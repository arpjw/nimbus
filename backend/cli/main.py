import argparse
import asyncio
import sys
from datetime import datetime, timezone

from colorama import Fore, Style, init

from cli.client import NimbusClient
from cli.git import get_git_remote

init(autoreset=True)

_PHASE_COLOR = {
    "queued": Fore.WHITE,
    "cloning": Fore.CYAN,
    "indexing": Fore.CYAN,
    "planning": Fore.YELLOW,
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


async def _run(args: argparse.Namespace) -> int:
    remote_url, repo_slug = get_git_remote()
    repo_name = repo_slug.split("/")[-1] if "/" in repo_slug else repo_slug

    client = NimbusClient(args.backend)

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
            if phase == "done":
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

    args = parser.parse_args()
    sys.exit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
