"""Quick start command for AstrBot from source."""

import shutil
import subprocess
import sys
from pathlib import Path

import tyro

from .utils import (
    DEPENDENCIES,
    REPO_URL,
    check_all_dependencies,
    clone_repo,
    is_pm2_running,
    prompt_confirm,
    run_command,
)

WORKING_DIR = Path.cwd() / "data" / "astrbot"
PM2_PROCESS_NAME = "astrbot"


def print_header() -> None:
    """Print header."""
    print("\n🚀 Quick Start AstrBot from Source")
    print("=" * 50)


def print_missing_deps(missing: list[str]) -> None:
    """Print missing dependencies with installation hints."""
    print("\n❌ Missing dependencies:")
    for dep in missing:
        print(f"   - {dep}")

    print("\n💡 Installation commands:")
    for dep in missing:
        print(f"   {DEPENDENCIES[dep]}")


def setup_python_env(working_dir: Path) -> None:
    """Setup Python virtual environment with uv."""
    print("\n🐍 Setting up Python environment...")
    run_command(["uv", "venv"], cwd=working_dir)
    run_command(["uv", "sync"], cwd=working_dir)
    print("✅ Python environment setup complete")


def build_dashboard(working_dir: Path) -> None:
    """Build the dashboard with pnpm."""
    print("\n🎨 Building dashboard...")
    dashboard_dir = working_dir / "dashboard"
    run_command(["pnpm", "install"], cwd=dashboard_dir)
    run_command(["pnpm", "run", "build"], cwd=dashboard_dir)
    print("✅ Dashboard build complete")


def start_with_pm2(working_dir: Path) -> None:
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


def main(
    force: bool = False,
    skip_deps: bool = False,
) -> None:
    """Quick start AstrBot from source code.

    This command will:
    1. Check required dependencies (python3, uv, node, pnpm, pm2)
    2. Clone AstrBot repository to data/astrbot/
    3. Setup Python environment with uv
    4. Build the dashboard
    5. Start AstrBot with PM2

    Args:
        force: Force reinstall even if directory exists.
        skip_deps: Skip dependency checking.
    """
    print_header()

    # Step 1: Check dependencies
    if not skip_deps:
        print("\n📋 Checking dependencies...")
        deps_status = check_all_dependencies()
        missing = [dep for dep, ok in deps_status.items() if not ok]

        if missing:
            print_missing_deps(missing)
            if not prompt_confirm("\nContinue anyway?", default=False):
                print("\n❌ Aborted. Please install missing dependencies.")
                sys.exit(1)
        else:
            print("✅ All dependencies present")
    else:
        print("\n⏭️  Skipping dependency check")

    # Step 2: Setup working directory
    print(f"\n📁 Working directory: {WORKING_DIR}")

    if WORKING_DIR.exists():
        if force:
            print("🗑️  Removing existing directory...")
            shutil.rmtree(WORKING_DIR)
        elif not (WORKING_DIR / "main.py").exists():
            pass  # Directory exists but empty, continue
        else:
            print("⚠️  Directory already exists. Use --force to reinstall.")
            if not prompt_confirm("Continue anyway?", default=False):
                sys.exit(1)

    WORKING_DIR.mkdir(parents=True, exist_ok=True)

    # Step 3: Clone repository
    if not (WORKING_DIR / "main.py").exists():
        print(f"\n📥 Cloning AstrBot from {REPO_URL}...")
        clone_repo(REPO_URL, WORKING_DIR)
        print("✅ Repository cloned successfully")
    else:
        print("\n✅ Repository already exists, skipping clone")

    # Step 4: Setup Python environment
    setup_python_env(WORKING_DIR)

    # Step 5: Build dashboard
    build_dashboard(WORKING_DIR)

    # Step 6: Start with PM2
    start_with_pm2(WORKING_DIR)

    # Done!
    print("\n" + "=" * 50)
    print("✨ AstrBot is now running!")
    print("\nNext steps:")
    print("  1. Access the dashboard (check PM2 logs for URL)")
    print("  2. Configure your bot settings")
    print("  3. Connect to your chat platform")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    tyro.cli(main)
