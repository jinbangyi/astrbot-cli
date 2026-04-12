"""Utility functions for quick start astrbot command."""

import json
import shutil
import subprocess
from pathlib import Path

# Required dependencies with installation hints
DEPENDENCIES: dict[str, str] = {
    "python3": "apt-get install python3",
    "uv": "pip install uv",
    "node": "apt-get install nodejs",
    "pnpm": "npm install -g pnpm",
    "pm2": "npm install -g pm2",
}

REPO_URL = "https://github.com/AstrBotDevs/AstrBot.git"


def check_dependency(dep_name: str) -> bool:
    """Check if a dependency is available in PATH."""
    return shutil.which(dep_name) is not None


def check_all_dependencies() -> dict[str, bool]:
    """Check all required dependencies."""
    return {dep: check_dependency(dep) for dep in DEPENDENCIES}


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a shell command."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        text=True,
    )


def run_command_capture(
    cmd: list[str],
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run a command and capture output."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def clone_repo(repo_url: str, dest_dir: Path) -> None:
    """Clone a git repository."""
    subprocess.run(
        ["git", "clone", repo_url, str(dest_dir)],
        check=True,
    )


def is_pm2_running(name: str = "astrbot") -> bool:
    """Check if a process is running in PM2."""
    result = subprocess.run(
        ["pm2", "jlist"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    try:
        processes = json.loads(result.stdout)
        return any(p.get("name") == name for p in processes)
    except json.JSONDecodeError:
        return False


def prompt_confirm(message: str, default: bool = False) -> bool:
    """Prompt user for confirmation."""
    suffix = " [Y/n]: " if default else " [y/N]: "
    response = input(message + suffix).strip().lower()
    if not response:
        return default
    return response in ("y", "yes")
