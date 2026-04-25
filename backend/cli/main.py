import argparse
import asyncio
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from colorama import Fore, Style, init

from cli.client import NimbusClient
from cli.git import get_git_remote

init(autoreset=True)

_PHASE_COLOR = {
    "queued": Fore.WHITE,
    "cloning": Fore.CYAN,
    "indexing": Fore.CYAN,
    "planning": Fore.YELLOW,
    "awaiting_approval": Fore.YELLOW,
    "awaiting_diff_approval": Fore.YELLOW,
    "implementing": Fore.BLUE,
    "verifying": Fore.MAGENTA,
    "fixing": Fore.YELLOW,
    "reviewing": Fore.BLUE,
    "pr_creation": Fore.CYAN,
    "cleanup": Fore.CYAN,
    "done": Fore.GREEN,
    "failed": Fore.RED,
}

_TERMINAL_PHASES = {"done", "failed"}


def _print_plan_table(changes: list[dict]) -> None:
    if not changes:
        return
    headers = ("ACTION", "FILE", "DESCRIPTION")
    rows = [
        (c.get("action", "").upper(), c.get("path", ""), c.get("description", ""))
        for c in changes
    ]
    col_widths = [
        max(len(headers[i]), max((len(r[i]) for r in rows), default=0))
        for i in range(3)
    ]
    col_widths[2] = min(col_widths[2], 60)

    sep = "  ".join("-" * w for w in col_widths)
    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(Style.BRIGHT + header_line + Style.RESET_ALL)
    print(sep)
    for row in rows:
        desc = row[2][:60]
        print("  ".join(cell.ljust(w) for cell, w in zip((row[0], row[1], desc), col_widths)))


def _print_diff(diff: str) -> None:
    print(Style.DIM + "-" * 60 + Style.RESET_ALL)
    for line in diff.splitlines():
        if line.startswith("@@"):
            print(Fore.CYAN + line + Style.RESET_ALL)
        elif line.startswith("+") and not line.startswith("+++"):
            print(Fore.GREEN + line + Style.RESET_ALL)
        elif line.startswith("-") and not line.startswith("---"):
            print(Fore.RED + line + Style.RESET_ALL)
        else:
            print(line)
    print(Style.DIM + "-" * 60 + Style.RESET_ALL)


def _fmt_event(event: dict) -> str:
    phase = event.get("phase", "")
    message = event.get("message", "")
    ts_raw = event.get("ts", "")

    try:
        ts = datetime.fromisoformat(ts_raw).astimezone(timezone.utc).strftime("%H:%M:%S")
    except Exception:
        ts = (ts_raw[:8] if ts_raw else "        ")

    color = _PHASE_COLOR.get(phase, Fore.WHITE)
    ts_str = Style.DIM + ts + Style.RESET_ALL
    phase_str = color + Style.BRIGHT + f"{phase:<14}" + Style.RESET_ALL
    return f"  {ts_str}  {phase_str}  {message}"


_VERDICT_COLOR = {
    "APPROVE": Fore.GREEN,
    "REQUEST_CHANGES": Fore.RED,
    "NEEDS_DISCUSSION": Fore.YELLOW,
}


async def _test(args: argparse.Namespace) -> int:
    api_key = args.api_key or os.environ.get("NIMBUS_API_KEY")
    client = NimbusClient(args.backend, api_key=api_key)

    repo_id = args.repo_id
    if not repo_id:
        try:
            remote_url, repo_slug = get_git_remote()
            repo_name = repo_slug.split("/")[-1] if "/" in repo_slug else repo_slug
            lookup_client = NimbusClient(args.backend, api_key=api_key)
            async with __import__("httpx").AsyncClient() as http:
                resp = await http.get(f"{args.backend}/workspaces/")
                resp.raise_for_status()
                workspaces = resp.json()
            workspace_id = None
            for ws in workspaces:
                if ws["name"] == repo_name:
                    workspace_id = ws["id"]
                    break
            if workspace_id:
                async with __import__("httpx").AsyncClient() as http:
                    resp = await http.get(f"{args.backend}/workspaces/{workspace_id}/repos")
                    resp.raise_for_status()
                    repos = resp.json()
                for repo in repos:
                    if repo["url"] == remote_url:
                        repo_id = repo["id"]
                        break
        except Exception as exc:
            print(Fore.RED + f"Could not auto-detect repo-id: {exc}", file=sys.stderr)
            print(Fore.RED + "Pass --repo-id explicitly.", file=sys.stderr)
            return 1

    if not repo_id:
        print(Fore.RED + "Could not resolve repo-id. Pass --repo-id explicitly.", file=sys.stderr)
        return 1

    print(f"Generating tests for {args.file_path} ...")
    try:
        result = await client.generate_tests_pr(repo_id, args.file_path)
    except Exception as exc:
        print(Fore.RED + f"Error: {exc}", file=sys.stderr)
        return 1

    content: str = result["content"]
    test_file_path: str = result["test_file_path"]

    print()
    for line in content.splitlines():
        if re.match(r"^(def test_|async def test_|it\(|test\(|func Test)", line):
            print(Fore.GREEN + Style.BRIGHT + line + Style.RESET_ALL)
        else:
            print(line)
    print()

    if args.write:
        out_path = Path.cwd() / test_file_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content)
        print(Fore.GREEN + f"Written to {out_path}")
    else:
        print(Style.DIM + f"(use --write to save to {test_file_path})" + Style.RESET_ALL)

    return 0


async def _review(args: argparse.Namespace) -> int:
    api_key = args.api_key or os.environ.get("NIMBUS_API_KEY")
    client = NimbusClient(args.backend, api_key=api_key)
    print(f"Reviewing {args.pr_url} ...")
    try:
        result = await client.review_pr(args.pr_url, post=args.post)
    except Exception as exc:
        print(Fore.RED + f"Error: {exc}", file=sys.stderr)
        return 1

    review: str = result["review"]
    verdict: str = result["verdict"]
    color = _VERDICT_COLOR.get(verdict, Fore.WHITE)

    print()
    for line in review.splitlines():
        if "**Verdict**:" in line:
            print(color + Style.BRIGHT + line + Style.RESET_ALL)
        else:
            print(line)
    print()

    if args.post:
        print(Fore.CYAN + "Review posted to PR.")

    return 0


async def _issue(args: argparse.Namespace) -> int:
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)", args.issue_url.rstrip("/"))
    if not match:
        print(Fore.RED + "Invalid GitHub issue URL. Expected: https://github.com/owner/repo/issues/NUMBER", file=sys.stderr)
        return 1

    owner, repo_name, issue_number_str = match.group(1), match.group(2), match.group(3)
    issue_number = int(issue_number_str)
    repo_full_name = f"{owner}/{repo_name}"
    repo_url = f"https://github.com/{repo_full_name}"

    token = args.token or os.environ.get("NIMBUS_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers: dict = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        async with httpx.AsyncClient() as http:
            resp = await http.get(f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}", headers=headers)
            resp.raise_for_status()
            issue_data = resp.json()
    except Exception as exc:
        print(Fore.RED + f"Failed to fetch issue: {exc}", file=sys.stderr)
        return 1

    title: str = issue_data.get("title", "")
    body: str = issue_data.get("body") or ""
    description = f"{title}\n\n{body}".strip()

    api_key = args.api_key or os.environ.get("NIMBUS_API_KEY")
    client = NimbusClient(args.backend, api_key=api_key)

    try:
        workspace = await client.get_or_create_workspace(repo_name)
        print(f"workspace  {workspace['name']}  ({workspace['id'][:8]}...)")

        repo = await client.get_or_create_repo(workspace["id"], repo_url, repo_name)
        print(f"repo       {repo['name']}  ({repo['id'][:8]}...)")

        task = await client.create_task(
            workspace["id"],
            repo["id"],
            description,
            issue_number=issue_number,
            repo_full_name=repo_full_name,
        )
        desc_preview = task["description"][:60]
        print(f"task       {task['id'][:8]}...  {desc_preview}")

    except Exception as exc:
        print(Fore.RED + f"Error communicating with backend: {exc}", file=sys.stderr)
        return 1

    if not args.yes:
        print()
        try:
            answer = input("Start execution? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return 0
        if answer != "y":
            print("Aborted.")
            return 0

    print()
    try:
        async for event in client.stream_task(task["id"]):
            print(_fmt_event(event))
            phase = event.get("phase", "")
            if phase == "awaiting_approval":
                changes = event.get("data", {}).get("changes", [])
                print()
                _print_plan_table(changes)
                print()
                if args.yes:
                    try:
                        await client.approve_task(task["id"])
                    except Exception as exc:
                        print(Fore.RED + f"Failed to approve: {exc}", file=sys.stderr)
                        return 1
                else:
                    n = len(changes)
                    try:
                        answer = input(f"Proceed with {n} change{'s' if n != 1 else ''}? [y/N] ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        print("\nAborted.")
                        try:
                            await client.reject_task(task["id"])
                        except Exception:
                            pass
                        return 1
                    if answer == "y":
                        try:
                            await client.approve_task(task["id"])
                        except Exception as exc:
                            print(Fore.RED + f"Failed to approve: {exc}", file=sys.stderr)
                            return 1
                    else:
                        try:
                            await client.reject_task(task["id"])
                        except Exception:
                            pass
                        return 1
            elif phase == "awaiting_diff_approval":
                diff = event.get("data", {}).get("diff", "")
                print()
                _print_diff(diff)
                print()
                if args.yes:
                    try:
                        await client.approve_diff(task["id"])
                    except Exception as exc:
                        print(Fore.RED + f"Failed to approve diff: {exc}", file=sys.stderr)
                        return 1
                else:
                    try:
                        answer = input("Open PR with these changes? [y/N] ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        print("\nAborted.")
                        try:
                            await client.reject_diff(task["id"])
                        except Exception:
                            pass
                        return 1
                    if answer == "y":
                        try:
                            await client.approve_diff(task["id"])
                        except Exception as exc:
                            print(Fore.RED + f"Failed to approve diff: {exc}", file=sys.stderr)
                            return 1
                    else:
                        try:
                            await client.reject_diff(task["id"])
                        except Exception:
                            pass
                        return 1
            elif phase == "done":
                pr_url = event.get("data", {}).get("pr_url")
                print()
                if pr_url:
                    print(Fore.GREEN + Style.BRIGHT + f"PR: {pr_url}")
                else:
                    print(Fore.GREEN + Style.BRIGHT + "Done.")
                return 0
            elif phase == "failed":
                print()
                print(Fore.RED + Style.BRIGHT + f"Failed: {event.get('message', 'unknown error')}")
                return 1
    except Exception as exc:
        print(Fore.RED + f"\nConnection error: {exc}", file=sys.stderr)
        return 1

    return 0


async def _run(args: argparse.Namespace) -> int:
    remote_url, repo_slug = get_git_remote()
    repo_name = repo_slug.split("/")[-1] if "/" in repo_slug else repo_slug

    api_key = args.api_key or os.environ.get("NIMBUS_API_KEY")
    client = NimbusClient(args.backend, api_key=api_key)

    try:
        workspace = await client.get_or_create_workspace(repo_name)
        print(f"workspace  {workspace['name']}  ({workspace['id'][:8]}...)")

        repo = await client.get_or_create_repo(workspace["id"], remote_url, repo_name)
        print(f"repo       {repo['name']}  ({repo['id'][:8]}...)")

        task = await client.create_task(workspace["id"], repo["id"], args.task)
        desc_preview = task["description"][:60]
        print(f"task       {task['id'][:8]}...  {desc_preview}")

    except Exception as exc:
        print(Fore.RED + f"Error communicating with backend: {exc}", file=sys.stderr)
        return 1

    if not args.yes:
        print()
        try:
            answer = input("Start execution? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return 0
        if answer != "y":
            print("Aborted.")
            return 0

    print()
    try:
        async for event in client.stream_task(task["id"]):
            print(_fmt_event(event))
            phase = event.get("phase", "")
            if phase == "awaiting_approval":
                changes = event.get("data", {}).get("changes", [])
                print()
                _print_plan_table(changes)
                print()
                if args.yes:
                    try:
                        await client.approve_task(task["id"])
                    except Exception as exc:
                        print(Fore.RED + f"Failed to approve: {exc}", file=sys.stderr)
                        return 1
                else:
                    n = len(changes)
                    try:
                        answer = input(f"Proceed with {n} change{'s' if n != 1 else ''}? [y/N] ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        print("\nAborted.")
                        try:
                            await client.reject_task(task["id"])
                        except Exception:
                            pass
                        return 1
                    if answer == "y":
                        try:
                            await client.approve_task(task["id"])
                        except Exception as exc:
                            print(Fore.RED + f"Failed to approve: {exc}", file=sys.stderr)
                            return 1
                    else:
                        try:
                            await client.reject_task(task["id"])
                        except Exception:
                            pass
                        return 1
            elif phase == "awaiting_diff_approval":
                diff = event.get("data", {}).get("diff", "")
                print()
                _print_diff(diff)
                print()
                if args.yes:
                    try:
                        await client.approve_diff(task["id"])
                    except Exception as exc:
                        print(Fore.RED + f"Failed to approve diff: {exc}", file=sys.stderr)
                        return 1
                else:
                    try:
                        answer = input("Open PR with these changes? [y/N] ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        print("\nAborted.")
                        try:
                            await client.reject_diff(task["id"])
                        except Exception:
                            pass
                        return 1
                    if answer == "y":
                        try:
                            await client.approve_diff(task["id"])
                        except Exception as exc:
                            print(Fore.RED + f"Failed to approve diff: {exc}", file=sys.stderr)
                            return 1
                    else:
                        try:
                            await client.reject_diff(task["id"])
                        except Exception:
                            pass
                        return 1
            elif phase == "done":
                pr_url = event.get("data", {}).get("pr_url")
                print()
                if pr_url:
                    print(Fore.GREEN + Style.BRIGHT + f"PR: {pr_url}")
                else:
                    print(Fore.GREEN + Style.BRIGHT + "Done.")
                return 0
            elif phase == "failed":
                print()
                print(Fore.RED + Style.BRIGHT + f"Failed: {event.get('message', 'unknown error')}")
                return 1
    except Exception as exc:
        print(Fore.RED + f"\nConnection error: {exc}", file=sys.stderr)
        return 1

    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="nimbus",
        description="Nimbus autonomous SWE agent CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Submit a task to the Nimbus agent")
    run_p.add_argument("task", metavar="TASK", help='Task description, e.g. "fix the login bug"')
    run_p.add_argument(
        "--backend",
        default="http://localhost:8000",
        metavar="URL",
        help="Nimbus backend URL (default: http://localhost:8000)",
    )
    run_p.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )
    run_p.add_argument(
        "--api-key",
        default=None,
        metavar="KEY",
        help="Nimbus API key (defaults to NIMBUS_API_KEY env var)",
    )

    review_p = sub.add_parser("review", help="Review a GitHub PR diff")
    review_p.add_argument("pr_url", metavar="PR_URL", help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/1")
    review_p.add_argument(
        "--backend",
        default="http://localhost:8000",
        metavar="URL",
        help="Nimbus backend URL (default: http://localhost:8000)",
    )
    review_p.add_argument(
        "--post",
        action="store_true",
        help="Post the review as a comment on the PR",
    )
    review_p.add_argument(
        "--api-key",
        default=None,
        metavar="KEY",
        help="Nimbus API key (defaults to NIMBUS_API_KEY env var)",
    )

    issue_p = sub.add_parser("issue", help="Run Nimbus on a GitHub issue")
    issue_p.add_argument("issue_url", metavar="ISSUE_URL", help="GitHub issue URL, e.g. https://github.com/owner/repo/issues/1")
    issue_p.add_argument(
        "--backend",
        default="http://localhost:8000",
        metavar="URL",
        help="Nimbus backend URL (default: http://localhost:8000)",
    )
    issue_p.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompts",
    )
    issue_p.add_argument(
        "--token",
        default=None,
        metavar="TOKEN",
        help="GitHub token (defaults to NIMBUS_GITHUB_TOKEN or GITHUB_TOKEN env var)",
    )
    issue_p.add_argument(
        "--api-key",
        default=None,
        metavar="KEY",
        help="Nimbus API key (defaults to NIMBUS_API_KEY env var)",
    )

    test_p = sub.add_parser("test", help="Generate a test suite for a source file")
    test_p.add_argument("file_path", metavar="FILE_PATH", help="Relative path to the source file, e.g. services/auth.py")
    test_p.add_argument(
        "--repo-id",
        default=None,
        metavar="ID",
        help="Repo ID (auto-detected from git remote if omitted)",
    )
    test_p.add_argument(
        "--backend",
        default="http://localhost:8000",
        metavar="URL",
        help="Nimbus backend URL (default: http://localhost:8000)",
    )
    test_p.add_argument(
        "--write",
        action="store_true",
        help="Write the generated tests to disk",
    )
    test_p.add_argument(
        "--api-key",
        default=None,
        metavar="KEY",
        help="Nimbus API key (defaults to NIMBUS_API_KEY env var)",
    )

    args = parser.parse_args()
    if args.command == "review":
        sys.exit(asyncio.run(_review(args)))
    if args.command == "issue":
        sys.exit(asyncio.run(_issue(args)))
    if args.command == "test":
        sys.exit(asyncio.run(_test(args)))
    sys.exit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
