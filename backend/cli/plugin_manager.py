import importlib
import importlib.metadata
import subprocess
import sys
import tomllib
from pathlib import Path


PLUGINS_CONFIG_PATH = Path.home() / ".nimbus" / "plugins.toml"


def _load_plugins_config() -> dict:
    if not PLUGINS_CONFIG_PATH.exists():
        return {"plugins": {}}
    try:
        with open(PLUGINS_CONFIG_PATH, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {"plugins": {}}


def _save_plugins_config(config: dict):
    PLUGINS_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        import tomli_w
        with open(PLUGINS_CONFIG_PATH, "wb") as f:
            tomli_w.dump(config, f)
    except ImportError:
        lines = ["[plugins]\n"]
        for name, info in config.get("plugins", {}).items():
            lines.append(f"[plugins.{name}]\n")
            for k, v in info.items():
                lines.append(f'{k} = "{v}"\n')
        PLUGINS_CONFIG_PATH.write_text("".join(lines))


def discover_plugins() -> dict[str, type]:
    plugins: dict[str, type] = {}
    try:
        eps = importlib.metadata.entry_points(group="nimbus.plugins")
        for ep in eps:
            try:
                plugin_class = ep.load()
                plugins[ep.name] = plugin_class
            except Exception as e:
                print(f"Warning: failed to load plugin {ep.name}: {e}")
    except Exception:
        pass
    return plugins


def get_installed_plugins() -> dict:
    return _load_plugins_config().get("plugins", {})


_VERIFIED_PREFIX = "nimbus-plugin-"


def is_verified_plugin(package_name: str) -> bool:
    base = package_name.split("==")[0].split("@")[0].strip().lower()
    return base.startswith(_VERIFIED_PREFIX)


def install_plugin(package_name: str, allow_untrusted: bool = False) -> bool:
    if not is_verified_plugin(package_name) and not allow_untrusted:
        raise ValueError(
            f"'{package_name}' is not a verified Nimbus plugin. "
            f"Verified plugins start with '{_VERIFIED_PREFIX}'. "
            "Pass --allow-untrusted to install anyway."
        )
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", package_name, "--break-system-packages"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        config = _load_plugins_config()
        config.setdefault("plugins", {})[package_name] = {
            "package": package_name,
            "verified": is_verified_plugin(package_name),
            "installed_at": __import__("datetime").datetime.utcnow().isoformat(),
        }
        _save_plugins_config(config)
        return True
    return False


def uninstall_plugin(package_name: str) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", package_name, "-y"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        config = _load_plugins_config()
        config.get("plugins", {}).pop(package_name, None)
        _save_plugins_config(config)
        return True
    return False


def list_plugins() -> list[dict]:
    discovered = discover_plugins()
    installed = get_installed_plugins()

    result = []
    for name, plugin_class in discovered.items():
        commands = []
        for attr_name in dir(plugin_class):
            attr = getattr(plugin_class, attr_name, None)
            if callable(attr) and getattr(attr, "_is_nimbus_command", False):
                commands.append({
                    "name": attr_name,
                    "doc": attr.__doc__ or "",
                })
        result.append({
            "name": name,
            "class": plugin_class.__name__,
            "commands": commands,
            "installed": name in installed or any(name in pkg for pkg in installed.keys()),
        })
    return result


class NimbusPlugin:
    name: str = "unnamed"

    def get_commands(self) -> dict[str, callable]:
        commands: dict[str, callable] = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name, None)
            if callable(attr) and getattr(attr, "_is_nimbus_command", False):
                commands[attr_name] = attr
        return commands


def command():
    def decorator(fn):
        fn._is_nimbus_command = True
        return fn
    return decorator
