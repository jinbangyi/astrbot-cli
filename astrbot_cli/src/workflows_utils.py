"""Workflow management utilities for AstrBot CLI."""

import json
import subprocess
from pathlib import Path
from typing import Any

from .path_config import get_astrbot_root


def get_workflows_path() -> Path:
    """Get the workflows directory path."""
    astrbot_root = get_astrbot_root()
    if astrbot_root:
        return astrbot_root / "data" / "workflows"
    return Path.cwd() / "data" / "workflows"


def get_dagu_bin() -> str:
    """Get dagu binary path."""
    return "dagu"


def list_workflows() -> list[dict]:
    """List all workflow files.

    Returns:
        List of workflow info dictionaries

    """
    workflows_path = get_workflows_path()
    workflows = []

    if workflows_path.exists():
        for file in workflows_path.glob("*.yaml"):
            workflows.append({
                "name": file.stem,
                "path": str(file),
                "exists": True,
            })

    return workflows


def get_workflow_status(name: str) -> dict | None:
    """Get workflow running status.

    Args:
        name: Workflow name

    Returns:
        Status dict or None if not found

    """
    try:
        result = subprocess.run(
            [get_dagu_bin(), "status", name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return {"name": name, "status": "running", "output": result.stdout}
        return {"name": name, "status": "stopped", "output": result.stderr}
    except subprocess.TimeoutExpired:
        return {"name": name, "status": "timeout", "output": "Command timed out"}
    except FileNotFoundError:
        return {"name": name, "status": "error", "output": "dagu not found"}


def start_workflow(name: str) -> dict:
    """Start a workflow.

    Args:
        name: Workflow name

    Returns:
        Result dict with status

    """
    workflows_path = get_workflows_path()
    workflow_file = workflows_path / f"{name}.yaml"

    if not workflow_file.exists():
        return {"success": False, "error": f"Workflow '{name}' not found"}

    try:
        result = subprocess.run(
            [get_dagu_bin(), "start", str(workflow_file)],
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
        return {"success": False, "error": "dagu not found. Please install dagu first."}


def stop_workflow(name: str) -> dict:
    """Stop a workflow.

    Args:
        name: Workflow name

    Returns:
        Result dict with status

    """
    try:
        result = subprocess.run(
            [get_dagu_bin(), "stop", name],
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
        return {"success": False, "error": "dagu not found. Please install dagu first."}


def get_workflow_logs(name: str, lines: int = 50) -> dict:
    """Get workflow logs.

    Args:
        name: Workflow name
        lines: Number of lines to retrieve

    Returns:
        Result dict with logs

    """
    try:
        result = subprocess.run(
            [get_dagu_bin(), "logs", name, "--tail", str(lines)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {"success": True, "logs": result.stdout}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "dagu not found"}


def create_workflow(name: str, description: str = "", commands: list[str] | None = None) -> dict:
    """Create a new workflow file.

    Args:
        name: Workflow name
        description: Workflow description
        commands: List of commands to execute

    Returns:
        Created workflow info

    """
    workflows_path = get_workflows_path()
    workflows_path.mkdir(parents=True, exist_ok=True)

    workflow_file = workflows_path / f"{name}.yaml"

    if workflow_file.exists():
        return {"success": False, "error": f"Workflow '{name}' already exists"}

    workflow_content = {
        "name": name,
        "description": description or f"AstrBot workflow: {name}",
        "steps": [],
    }

    if commands:
        for i, cmd in enumerate(commands, 1):
            workflow_content["steps"].append({
                "name": f"step-{i}",
                "command": cmd,
            })
    else:
        workflow_content["steps"].append({
            "name": "step-1",
            "command": "echo 'Hello from AstrBot workflow'",
        })

    workflow_file.write_text(
        f"""# AstrBot Workflow: {name}
# Edit this file to customize your workflow

name: {workflow_content['name']}
description: {workflow_content['description']}

steps:
""",
        encoding="utf-8",
    )

    for step in workflow_content["steps"]:
        workflow_file.write_text(
            f"""  - name: {step['name']}
    command: {step['command']}
""",
            encoding="utf-8",
            append=True,
        )

    return {
        "success": True,
        "name": name,
        "path": str(workflow_file),
    }
