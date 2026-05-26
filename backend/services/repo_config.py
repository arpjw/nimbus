from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_log = logging.getLogger(__name__)

try:
    import toml
except ImportError:
    toml = None  # type: ignore[assignment]


@dataclass
class MCPServerConfig:
    name: str
    url: str
    auth_env: Optional[str] = None


@dataclass
class RepoConfig:
    allowed_agents: list[str] = field(default_factory=list)
    denied_paths: list[str] = field(default_factory=list)
    require_human_approval: bool = True
    required_checks: list[str] = field(default_factory=list)
    block_on_severity: str = "high"
    planner_model: Optional[str] = None
    implementer_model: Optional[str] = None
    protected_branches: list[str] = field(default_factory=list)
    mcp_servers: list[MCPServerConfig] = field(default_factory=list)


def load_repo_config(workspace: Path) -> RepoConfig:
    config_path = workspace / ".nimbus.toml"
    if not config_path.exists() or toml is None:
        return RepoConfig()
    try:
        data = toml.loads(config_path.read_text())
        tasks = data.get("tasks", {})
        review = data.get("review", {})
        models = data.get("models", {})
        branches = data.get("branches", {})
        mcp_raw = data.get("mcp", {}).get("servers", [])
        mcp_servers = [
            MCPServerConfig(
                name=s.get("name", ""),
                url=s.get("url", ""),
                auth_env=s.get("auth_env"),
            )
            for s in mcp_raw
            if s.get("url")
        ]
        return RepoConfig(
            allowed_agents=tasks.get("allowed_agents", []),
            denied_paths=tasks.get("denied_paths", []),
            require_human_approval=tasks.get("require_human_approval", True),
            required_checks=review.get("required_checks", []),
            block_on_severity=review.get("block_on_severity", "high"),
            planner_model=models.get("planner"),
            implementer_model=models.get("implementer"),
            protected_branches=branches.get("protected", []),
            mcp_servers=mcp_servers,
        )
    except Exception as exc:
        _log.warning("Failed to load .nimbus.toml: %s", exc)
        return RepoConfig()


def check_protected_branch(repo_config: RepoConfig, branch_name: str) -> None:
    from fastapi import HTTPException
    for pattern in repo_config.protected_branches:
        if fnmatch.fnmatch(branch_name, pattern) or branch_name == pattern:
            raise HTTPException(
                status_code=403,
                detail=f"Branch '{branch_name}' is protected by .nimbus.toml",
            )


def filter_denied_paths(repo_config: RepoConfig, changes: list) -> list:
    if not repo_config.denied_paths:
        return changes
    allowed = []
    for change in changes:
        path = getattr(change, "path", change.get("path", "")) if not hasattr(change, "path") else change.path
        denied = any(fnmatch.fnmatch(path, pattern) for pattern in repo_config.denied_paths)
        if not denied:
            allowed.append(change)
    return allowed
