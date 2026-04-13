"""System management CLI commands for AstrBot."""

import json
from dataclasses import dataclass
from typing import Annotated

import tyro

from .system_utils import (
    start_astrbot,
    stop_astrbot,
    restart_astrbot,
    get_astrbot_status,
    get_astrbot_logs,
    get_astrbot_info,
    init_astrbot,
    upgrade_astrbot,
    is_astrbot_running,
)


@dataclass
class Init:
    """Initialize AstrBot environment.

    Run astrbot init to generate configuration files and install dependencies.
    """

    def run(self) -> None:
        """Execute the init command."""
        print("\n🔧 Initializing AstrBot environment...")
        result = init_astrbot()

        if result.get("success"):
            print("✅ AstrBot initialized successfully")
            if result.get("output"):
                print(result["output"])
        else:
            print(f"❌ Initialization failed: {result.get('error', 'Unknown error')}")


@dataclass
class Upgrade:
    """Upgrade AstrBot installation.

    Pull latest changes from git and update dependencies.
    """

    def run(self) -> None:
        """Execute the upgrade command."""
        print("\n⬆️  Upgrading AstrBot...")
        result = upgrade_astrbot()

        if result.get("success"):
            print("✅ AstrBot upgraded successfully")
            if result.get("output"):
                print(result["output"])
        else:
            print(f"❌ Upgrade failed: {result.get('error', 'Unknown error')}")


@dataclass
class Start:
    """Start AstrBot service.

    Start AstrBot using PM2 process manager.
    """

    def run(self) -> None:
        """Execute the start command."""
        print("\n🚀 Starting AstrBot...")
        result = start_astrbot()

        if result.get("success"):
            print("✅ AstrBot started successfully")
            print("   Check status with: astrbot-cli system status")
            print("   View logs with: astrbot-cli system logs")
        else:
            print(f"❌ Failed to start: {result.get('error', 'Unknown error')}")


@dataclass
class Stop:
    """Stop AstrBot service.

    Stop the running AstrBot process.
    """

    def run(self) -> None:
        """Execute the stop command."""
        print("\n🛑 Stopping AstrBot...")
        result = stop_astrbot()

        if result.get("success"):
            print("✅ AstrBot stopped")
        else:
            print(f"❌ Failed to stop: {result.get('error', 'Unknown error')}")


@dataclass
class Restart:
    """Restart AstrBot service.

    Restart the running AstrBot process.
    """

    def run(self) -> None:
        """Execute the restart command."""
        print("\n🔄 Restarting AstrBot...")
        result = restart_astrbot()

        if result.get("success"):
            print("✅ AstrBot restarted successfully")
        else:
            print(f"❌ Failed to restart: {result.get('error', 'Unknown error')}")


@dataclass
class Status:
    """Show AstrBot service status.

    Display running status, PID, uptime, memory and CPU usage.
    """

    def run(self) -> None:
        """Execute the status command."""
        status = get_astrbot_status()

        print("\n📊 AstrBot Status")
        print("-" * 50)

        # Installation status
        installed = status.get("installed", False)
        print(f"Installed: {'✅ Yes' if installed else '❌ No'}")

        if status.get("path"):
            print(f"Path: {status['path']}")

        # Running status
        running = status.get("running", False)
        print(f"Running: {'✅ Yes' if running else '❌ No'}")

        if running:
            if status.get("pid"):
                print(f"PID: {status['pid']}")
            if status.get("status"):
                print(f"Status: {status['status']}")
            if status.get("uptime"):
                import time
                uptime_sec = (time.time() * 1000 - status["uptime"]) / 1000
                if uptime_sec < 60:
                    print(f"Uptime: {int(uptime_sec)}s")
                elif uptime_sec < 3600:
                    print(f"Uptime: {int(uptime_sec / 60)}m")
                else:
                    print(f"Uptime: {int(uptime_sec / 3600)}h {int((uptime_sec % 3600) / 60)}m")
            if status.get("memory"):
                mem_mb = status["memory"] / (1024 * 1024)
                print(f"Memory: {mem_mb:.1f} MB")
            if status.get("cpu") is not None:
                print(f"CPU: {status['cpu']:.1f}%")

        if not installed:
            print("\n💡 Run 'astrbot-cli quick-start' to install AstrBot")


@dataclass
class Logs:
    """Show AstrBot logs.

    Display recent log entries from AstrBot.
    """

    lines: Annotated[int, tyro.conf.Positional] = 50  # Number of lines to show
    follow: bool = False  # Follow log output (stream new entries)

    def run(self) -> None:
        """Execute the logs command."""
        result = get_astrbot_logs(lines=self.lines, follow=self.follow)

        if result.get("success"):
            print(f"\n📜 AstrBot Logs (last {self.lines} lines)")
            print("-" * 50)
            print(result.get("logs", ""))
        else:
            print(f"❌ Failed to get logs: {result.get('error', 'Unknown error')}")


@dataclass
class Info:
    """Show AstrBot information.

    Display version, installation path, Python environment, and dependencies.
    """

    def run(self) -> None:
        """Execute the info command."""
        info = get_astrbot_info()

        print("\nℹ️  AstrBot Information")
        print("-" * 50)

        # Installation info
        installed = info.get("installed", False)
        print(f"Installed: {'✅ Yes' if installed else '❌ No'}")

        if info.get("path"):
            print(f"Installation Path: {info['path']}")

        if info.get("version"):
            print(f"Version: {info['version']}")

        if info.get("python_version"):
            print(f"Python Version: {info['python_version']}")

        if info.get("venv_path"):
            print(f"Virtual Environment: {info['venv_path']}")

        dashboard_built = info.get("dashboard_built", False)
        print(f"Dashboard Built: {'✅ Yes' if dashboard_built else '❌ No'}")

        # Dependencies
        deps = info.get("dependencies", {})
        if deps:
            print("\nDependencies:")
            for dep, available in deps.items():
                status = "✅" if available else "❌"
                print(f"  {status} {dep}")

        if not installed:
            print("\n💡 Run 'astrbot-cli quick-start' to install AstrBot")


# Alias for backward compatibility
Version = Info