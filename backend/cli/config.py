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


def check_first_run() -> bool:
    import os
    from rich.console import Console
    from rich.panel import Panel
    console = Console()

    missing = []
    if not os.environ.get("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.environ.get("VOYAGE_API_KEY"):
        missing.append("VOYAGE_API_KEY")

    if not missing:
        return True

    console.print()
    console.print(Panel(
        """[bold white]Welcome to Nimbus.[/bold white]

Two API keys are required to get started.

[bold #c4a96a]export ANTHROPIC_API_KEY=sk-ant-...[/bold #c4a96a]
  [dim]Get yours → https://console.anthropic.com[/dim]

[bold #c4a96a]export VOYAGE_API_KEY=pa-...[/bold #c4a96a]
  [dim]Get yours → https://dash.voyageai.com[/dim]

Then run [bold]nimbus[/bold] again in your project directory.""",
        title="[dim]setup required[/dim]",
        border_style="dim",
        padding=(1, 2),
    ))
    console.print()
    return False
