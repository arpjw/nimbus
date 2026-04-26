import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

SESSIONS_DIR = Path.home() / ".nimbus" / "sessions"


@dataclass
class SessionEvent:
    timestamp: float
    event_type: str
    data: dict = field(default_factory=dict)


@dataclass
class Session:
    id: str
    repo_name: str
    task: str
    started_at: float
    events: list[SessionEvent] = field(default_factory=list)
    completed_at: Optional[float] = None
    pr_url: Optional[str] = None


class SessionRecorder:
    def __init__(self, repo_name: str, task: str):
        self.session = Session(
            id=f"{int(time.time())}",
            repo_name=repo_name,
            task=task,
            started_at=time.time()
        )

    def record(self, event_type: str, data: dict = {}):
        self.session.events.append(SessionEvent(
            timestamp=time.time(),
            event_type=event_type,
            data=data
        ))

    def save(self, pr_url: str = None) -> str:
        self.session.completed_at = time.time()
        self.session.pr_url = pr_url
        repo_dir = SESSIONS_DIR / self.session.repo_name.replace("/", "_")
        repo_dir.mkdir(parents=True, exist_ok=True)
        path = repo_dir / f"{self.session.id}.json"
        path.write_text(json.dumps(asdict(self.session), indent=2))
        return str(path)

    @staticmethod
    def load_latest(repo_name: str) -> Optional[dict]:
        repo_dir = SESSIONS_DIR / repo_name.replace("/", "_")
        if not repo_dir.exists():
            return None
        sessions = sorted(repo_dir.glob("*.json"), key=lambda p: p.stem, reverse=True)
        if not sessions:
            return None
        return json.loads(sessions[0].read_text())

    @staticmethod
    def list_sessions(repo_name: str) -> list[dict]:
        repo_dir = SESSIONS_DIR / repo_name.replace("/", "_")
        if not repo_dir.exists():
            return []
        sessions = sorted(repo_dir.glob("*.json"), key=lambda p: p.stem, reverse=True)
        results = []
        for s in sessions[:10]:
            data = json.loads(s.read_text())
            results.append({
                "id": data["id"],
                "task": data["task"],
                "started_at": data["started_at"],
                "pr_url": data.get("pr_url")
            })
        return results
