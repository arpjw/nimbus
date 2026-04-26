import toml
from pathlib import Path

CONFIG_PATH = Path.home() / ".nimbus" / "config.toml"

DEFAULT_CONFIG = {
    "local": {
        "chroma_dir": str(Path.home() / ".nimbus" / "chroma"),
        "default_model_planner": "claude-opus-4-6",
        "default_model_implementer": "claude-sonnet-4-6",
        "editor": "",
        "sound": False,
        "auto_approve_confidence": 92,
    }
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(toml.dumps(DEFAULT_CONFIG))
    return toml.loads(CONFIG_PATH.read_text())
