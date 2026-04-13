"""System management utilities for AstrBot CLI."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from .path_config import get_astrbot_root, get_astrbot_path
from .utils import run_command, run_command_capture, check_all_dependencies, DEPENDENCIES

PM2_PROCESS_NAME = "astrbot"


def get_pm2_process_info() -> dict | None:
    """Get PM2 process info for AstrBot.

    Returns:
        Process info dict or None if not running
    """
    result = subprocess.run(
        ["pm2", "jlist"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    try:
        processes = json.loads(result.stdout)
        for p in processes:
            if p.get("name") == PM2_PROCESS_NAME:
                return p
        return None
    except json.JSONDecodeError:
        return None


def is_astrbot_running() -> bool:
    """Check if AstrBot is running via PM2."""
    return get_pm2_process_info() is not None


def start_astrbot() -> dict:
    """Start AstrBot with PM2.

    Returns:
        Result dict with success status
    """
    astrbot_root = get_astrbot_root()
    if not astrbot_root:
        return {"success": False, "error": "AstrBot path not set. Run 'astrbot-cli quick-start' first."}

    if not (astrbot_root / "main.py").exists():
        return {"success": False, "error": f"AstrBot not found at {astrbot_root}"}

    if is_astrbot_running():
        return {"success": False, "error": "AstrBot is already running. Use 'restart' to restart."}

    venv_python = astrbot_root / ".venv" / "bin" / "python"

    # Check if venv exists
    if not venv_python.exists():
        # Try system python as fallback
        venv_python = Path(sys.executable)

    try:
        result = subprocess.run(
            [
                "pm2", "start",
                str(venv_python),
                "--name", PM2_PROCESS_NAME,
                "--", "main.py",
                "--webui-dir", "dashboard/dist",
            ],
            cwd=astrbot_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        return {"success": False, "error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "pm2 not found. Install with: npm install -g pm2"}


def stop_astrbot() -> dict:
    """Stop AstrBot via PM2.

    Returns:
        Result dict with success status
    """
    if not is_astrbot_running():
        return {"success": False, "error": "AstrBot is not running"}

    try:
        result = subprocess.run(
            ["pm2", "stop", PM2_PROCESS_NAME],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        return {"success": False, "error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "pm2 not found"}


def restart_astrbot() -> dict:
    """Restart AstrBot via PM2.

    Returns:
        Result dict with success status
    """
    if not is_astrbot_running():
        # Not running, try to start
        return start_astrbot()

    try:
        result = subprocess.run(
            ["pm2", "restart", PM2_PROCESS_NAME],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        return {"success": False, "error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "pm2 not found"}


def get_astrbot_status() -> dict:
    """Get AstrBot running status.

    Returns:
        Status dict with process info
    """
    process_info = get_pm2_process_info()
    astrbot_root = get_astrbot_root()

    status = {
        "installed": astrbot_root is not None and (astrbot_root / "main.py").exists() if astrbot_root else False,
        "path": str(astrbot_root) if astrbot_root else None,
        "running": False,
        "pid": None,
        "uptime": None,
        "memory": None,
        "cpu": None,
        "status": None,
    }

    if process_info:
        status["running"] = True
        status["pid"] = process_info.get("pid")
        status["uptime"] = process_info.get("pm2_env", {}).get("pm_uptime")
        status["memory"] = process_info.get("monit", {}).get("memory")
        status["cpu"] = process_info.get("monit", {}).get("cpu")
        status["status"] = process_info.get("pm2_env", {}).get("status")

    return status


def get_astrbot_logs(lines: int = 50, follow: bool = False) -> dict:
    """Get AstrBot logs from PM2.

    Args:
        lines: Number of lines to show
        follow: Whether to follow log output

    Returns:
        Result dict with logs
    """
    if not is_astrbot_running():
        return {"success": False, "error": "AstrBot is not running"}

    try:
        cmd = ["pm2", "logs", PM2_PROCESS_NAME, "--lines", str(lines), "--nostream"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {"success": True, "logs": result.stdout}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "pm2 not found"}


def get_astrbot_info() -> dict:
    """Get AstrBot installation info.

    Returns:
        Info dict with version, path, etc.
    """
    astrbot_root = get_astrbot_root()

    info = {
        "installed": False,
        "path": None,
        "version": None,
        "python_version": None,
        "venv_path": None,
        "dashboard_built": False,
        "dependencies": {},
    }

    if not astrbot_root:
        return info

    info["path"] = str(astrbot_root)
    info["installed"] = (astrbot_root / "main.py").exists()

    if not info["installed"]:
        return info

    # Check for version info in main.py or package
    # Try to read version from pyproject.toml if it exists
    pyproject_path = astrbot_root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            import re
            content = pyproject_path.read_text(encoding="utf-8")
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                info["version"] = match.group(1)
        except Exception:
            pass

    # Check Python version
    info["python_version"] = sys.version.split()[0]

    # Check venv
    venv_path = astrbot_root / ".venv"
    info["venv_path"] = str(venv_path) if venv_path.exists() else None

    # Check dashboard build
    dashboard_dist = astrbot_root / "dashboard" / "dist"
    info["dashboard_built"] = dashboard_dist.exists() and any(dashboard_dist.iterdir()) if dashboard_dist.exists() else False

    # Check dependencies
    deps_status = check_all_dependencies()
    info["dependencies"] = deps_status

    return info


def init_astrbot() -> dict:
    """Initialize AstrBot environment.

    Returns:
        Result dict with status
    """
    astrbot_root = get_astrbot_root()

    if not astrbot_root:
        return {"success": False, "error": "AstrBot path not set. Run 'astrbot-cli quick-start' first."}

    if not (astrbot_root / "main.py").exists():
        return {"success": False, "error": f"AstrBot not found at {astrbot_root}"}

    # Run astrbot init command
    venv_python = astrbot_root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = Path(sys.executable)

    try:
        result = subprocess.run(
            [str(venv_python), "main.py", "init"],
            cwd=astrbot_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        return {"success": False, "error": result.stderr or result.stdout}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def upgrade_astrbot() -> dict:
    """Upgrade AstrBot installation.

    Returns:
        Result dict with status
    """
    astrbot_root = get_astrbot_root()

    if not astrbot_root:
        return {"success": False, "error": "AstrBot path not set. Run 'astrbot-cli quick-start' first."}

    if not (astrbot_root / "main.py").exists():
        return {"success": False, "error": f"AstrBot not found at {astrbot_root}"}

    # Git pull to update
    try:
        result = subprocess.run(
            ["git", "pull"],
            cwd=astrbot_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return {"success": False, "error": f"Git pull failed: {result.stderr}"}

        output = result.stdout

        # Update dependencies
        venv_python = astrbot_root / ".venv" / "bin" / "python"
        if venv_python.exists():
            sync_result = subprocess.run(
                ["uv", "sync"],
                cwd=astrbot_root,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if sync_result.returncode == 0:
                output += "\nDependencies updated."
            else:
                output += f"\nWarning: Dependency update had issues: {sync_result.stderr}"

        return {"success": True, "output": output}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "git not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}
