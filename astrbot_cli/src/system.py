"""System management CLI commands for AstrBot."""

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
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
from .utils import (
    DEPENDENCIES,
    REPO_URL,
    check_all_dependencies,
    clone_repo,
    is_pm2_running,
    prompt_confirm,
    run_command,
)
from .path_config import (
    set_astrbot_path,
    set_api_key,
    get_astrbot_path,
    load_cli_config,
    print_current_path,
    validate_astrbot_path,
)

PM2_PROCESS_NAME = "astrbot"


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
            print("\n💡 Run 'astrbot-cli system quick-start' to install AstrBot")


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
            print("\n💡 Run 'astrbot-cli system quick-start' to install AstrBot")


# Alias for backward compatibility
Version = Info


@dataclass
class QuickStart:
    """Quick start AstrBot from source code.

    This command will:
    1. Check required dependencies (python3, uv, node, pnpm, pm2)
    2. Clone AstrBot repository to the specified path
    3. Setup Python environment with uv
    4. Build the dashboard
    5. Start AstrBot with PM2
    """
    force: bool = False  # Force reinstall even if directory exists
    skip_deps: bool = False  # Skip dependency checking
    path: Path | None = None  # Custom installation path

    def run(self) -> None:
        """Execute the quick start command."""
        print("\n🚀 Quick Start AstrBot from Source")
        print("=" * 50)

        # Determine working directory
        if self.path:
            working_dir = self.path.resolve()
        else:
            # Check if there's a saved path, otherwise use default
            config = load_cli_config()
            if config.astrbot_path:
                working_dir = Path(config.astrbot_path)
                print(f"\n📁 Using saved path: {working_dir}")
            else:
                # Default path
                working_dir = Path.cwd() / "data" / "astrbot"

        # Step 1: Check dependencies
        if not self.skip_deps:
            print("\n📋 Checking dependencies...")
            deps_status = check_all_dependencies()
            missing = [dep for dep, ok in deps_status.items() if not ok]

            if missing:
                self._print_missing_deps(missing)
                if not prompt_confirm("\nContinue anyway?", default=False):
                    print("\n❌ Aborted. Please install missing dependencies.")
                    sys.exit(1)
            else:
                print("✅ All dependencies present")
        else:
            print("\n⏭️  Skipping dependency check")

        # Step 2: Setup working directory
        print(f"\n📁 Working directory: {working_dir}")

        if working_dir.exists():
            if self.force:
                print("🗑️  Removing existing directory...")
                shutil.rmtree(working_dir)
            elif not (working_dir / "main.py").exists():
                pass  # Directory exists but empty, continue
            else:
                print("⚠️  Directory already exists. Use --force to reinstall.")
                if not prompt_confirm("Continue anyway?", default=False):
                    sys.exit(1)

        working_dir.mkdir(parents=True, exist_ok=True)

        # Step 3: Clone repository
        if not (working_dir / "main.py").exists():
            print(f"\n📥 Cloning AstrBot from {REPO_URL}...")
            clone_repo(REPO_URL, working_dir)
            print("✅ Repository cloned successfully")
        else:
            print("\n✅ Repository already exists, skipping clone")

        # Step 4: Setup Python environment
        self._setup_python_env(working_dir)

        # Step 5: Build dashboard
        self._build_dashboard(working_dir)

        # Step 6: Start with PM2
        self._start_with_pm2(working_dir)

        # Save the path to config so other commands can find it
        set_astrbot_path(working_dir)
        print(f"\n💾 Saved AstrBot path to config: {working_dir}")

        # Done!
        print("\n" + "=" * 50)
        print("✨ AstrBot is now running!")
        print("\nNext steps:")
        print("  1. Access the dashboard (check PM2 logs for URL)")
        print("  2. Configure your bot settings")
        print("  3. Connect to your chat platform")
        print("=" * 50 + "\n")

    def _print_missing_deps(self, missing: list[str]) -> None:
        """Print missing dependencies with installation hints."""
        print("\n❌ Missing dependencies:")
        for dep in missing:
            print(f"   - {dep}")

        print("\n💡 Installation commands:")
        for dep in missing:
            print(f"   {DEPENDENCIES[dep]}")

    def _setup_python_env(self, working_dir: Path) -> None:
        """Setup Python virtual environment with uv."""
        print("\n🐍 Setting up Python environment...")
        run_command(["uv", "venv"], cwd=working_dir)
        run_command(["uv", "sync"], cwd=working_dir)
        print("✅ Python environment setup complete")

    def _build_dashboard(self, working_dir: Path) -> None:
        """Build the dashboard with pnpm."""
        print("\n🎨 Building dashboard...")
        dashboard_dir = working_dir / "dashboard"
        run_command(["pnpm", "install"], cwd=dashboard_dir)
        run_command(["pnpm", "run", "build"], cwd=dashboard_dir)
        print("✅ Dashboard build complete")

    def _start_with_pm2(self, working_dir: Path) -> None:
        """Start AstrBot with PM2."""
        print("\n🚀 Starting AstrBot with PM2...")

        if is_pm2_running(PM2_PROCESS_NAME):
            if prompt_confirm("AstrBot is already running. Restart?", default=False):
                subprocess.run(["pm2", "delete", PM2_PROCESS_NAME], check=False)
            else:
                print("⏭️  Skipping start. Use 'pm2 restart astrbot' to restart.")
                return

        # Use the venv Python interpreter
        venv_python = working_dir / ".venv" / "bin" / "python"

        cmd = [
            "pm2",
            "start",
            str(venv_python),
            "--name",
            PM2_PROCESS_NAME,
            "--",
            "main.py",
            "--webui-dir",
            "dashboard/dist",
        ]
        run_command(cmd, cwd=working_dir, check=False)
        print("✅ AstrBot started with PM2")
        print("\n📊 Check status with: pm2 status")
        print("📜 View logs with: pm2 logs astrbot")


@dataclass
class Path:
    """Show or set the AstrBot installation path and API key.

    The API key is used for AstrBot OpenAPI authentication.
    It is stored in ~/.config/astrbot-cli/config.yaml and used as
    a fallback when commands don't have an explicit --api-key option.
    """
    set: Path | None = None  # Set a new AstrBot path
    force: bool = False  # Force set even if AstrBot not installed at path
    api_key: str | None = None  # Set the default API key for AstrBot OpenAPI

    def run(self) -> None:
        """Execute the path command."""
        if self.set:
            if self.force or (self.set / "main.py").exists():
                set_astrbot_path(self.set)
                print(f"✅ AstrBot path set to: {self.set}")
            else:
                print(f"❌ AstrBot not found at: {self.set}")
                print("   Use --force to set this path anyway.")
                sys.exit(1)
        elif self.api_key:
            set_api_key(self.api_key)
            print(f"✅ API key saved to ~/.config/astrbot-cli/config.yaml")
        else:
            print_current_path()