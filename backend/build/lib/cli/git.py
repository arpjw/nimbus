import re
import subprocess
from typing import Tuple


def get_git_remote() -> Tuple[str, str]:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        raise SystemExit("Error: no git remote 'origin' found. Are you in a git repository?")
    except FileNotFoundError:
        raise SystemExit("Error: git is not installed or not in PATH.")

    url = result.stdout.strip()
    if not url:
        raise SystemExit("Error: git remote 'origin' has no URL configured.")

    slug = _extract_slug(url)
    if not slug:
        raise SystemExit(f"Error: could not extract repo slug from remote URL: {url}")

    return url, slug


def _extract_slug(url: str) -> str:
    ssh = re.match(r"git@[^:]+:(.+?)(?:\.git)?$", url)
    if ssh:
        return ssh.group(1)
    https = re.match(r"https?://[^/]+/(.+?)(?:\.git)?$", url)
    if https:
        return https.group(1)
    return ""
