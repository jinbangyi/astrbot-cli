"""Workflow management CLI commands for AstrBot."""

import json
from dataclasses import dataclass
from typing import Annotated

import tyro

from .workflows_utils import (
    list_workflows,
    get_workflow_status,
    start_workflow,
    stop_workflow,
    get_workflow_logs,
    create_workflow,
)


@dataclass
class List:
    """List all workflows.

    Show all available workflow files.
    """

    def run(self) -> None:
        """Execute the list command."""
        workflows = list_workflows()

        if workflows:
            print("\nAvailable Workflows:")
            print("-" * 60)
            print(f"{'Name':<30} {'Status':<15}")
            print("-" * 60)

            for wf in workflows:
                status_info = get_workflow_status(wf["name"])
                status = status_info.get("status", "unknown") if status_info else "unknown"
                print(f"{wf['name']:<30} {status:<15}")
        else:
            print("No workflows found.")
            print("Create one with: astrbot-cli workflows create <name>")


@dataclass
class Start:
    """Start a workflow.

    Begin execution of a workflow by name.
    """

    name: Annotated[str, tyro.conf.Positional]  # Workflow name to start

    def run(self) -> None:
        """Execute the start command."""
        result = start_workflow(self.name)
        if result.get("success"):
            print(f"Workflow '{self.name}' started successfully")
            if result.get("output"):
                print(result["output"])
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")


@dataclass
class Stop:
    """Stop a workflow.

    Stop execution of a running workflow.
    """

    name: Annotated[str, tyro.conf.Positional]  # Workflow name to stop

    def run(self) -> None:
        """Execute the stop command."""
        result = stop_workflow(self.name)
        if result.get("success"):
            print(f"Workflow '{self.name}' stopped")
            if result.get("output"):
                print(result["output"])
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")


@dataclass
class Status:
    """Show workflow status.

    Display the current status of a workflow.
    """

    name: Annotated[str, tyro.conf.Positional]  # Workflow name

    def run(self) -> None:
        """Execute the status command."""
        status_info = get_workflow_status(self.name)
        if status_info:
            print(f"\nWorkflow: {self.name}")
            print(f"Status: {status_info.get('status', 'unknown')}")
            if status_info.get("output"):
                print(f"\nOutput:\n{status_info['output']}")
        else:
            print(f"Error: Could not get status for '{self.name}'")


@dataclass
class Logs:
    """Show workflow logs.

    Display recent logs from a workflow.
    """

    name: Annotated[str, tyro.conf.Positional]  # Workflow name
    lines: int = 50  # Number of lines to show

    def run(self) -> None:
        """Execute the logs command."""
        result = get_workflow_logs(self.name, self.lines)
        if result.get("success"):
            print(f"\nLogs for '{self.name}':")
            print("-" * 60)
            print(result.get("logs", ""))
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")


@dataclass
class Create:
    """Create a new workflow.

    Create a new workflow file with optional commands.
    """

    name: Annotated[str, tyro.conf.Positional]  # Workflow name
    description: str = ""  # Workflow description
    commands: str | None = None  # Comma-separated list of commands

    def run(self) -> None:
        """Execute the create command."""
        commands_list = [c.strip() for c in self.commands.split(",")] if self.commands else None
        result = create_workflow(self.name, self.description, commands_list)

        if result.get("success"):
            print(f"Workflow '{self.name}' created successfully!")
            print(f"  Path: {result.get('path')}")
            print(f"\nEdit with: astrbot-cli workflows edit {self.name}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
