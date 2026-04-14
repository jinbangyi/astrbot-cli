"""Path configuration management for AstrBot CLI.

This module manages the AstrBot installation path, allowing users to:
1. Install AstrBot to any directory (via --path option)
2. Use CLI commands from any directory (reads saved path)
3. Check and manage multiple installations
4. Configure default API key for AstrBot API authentication
"""

import json
from pathlib import Path
from dataclasses import dataclass

import yaml


# Default installation path
DEFAULT_INSTALL_PATH = Path.cwd() / "data" / "astrbot"

# CLI config file location (stores the AstrBot path)
# Using user's home directory for global config
CLI_CONFIG_DIR = Path.home() / ".config" / "astrbot-cli"
CLI_CONFIG_FILE = CLI_CONFIG_DIR / "config.yaml"


@dataclass
class CLIConfig:
    """CLI configuration stored in ~/.config/astrbot-cli/config.yaml"""

    astrbot_path: str | None = None  # Path to AstrBot installation
    api_key: str | None = None  # Default API key for AstrBot API authentication

    def to_dict(self) -> dict:
        return {"astrbot_path": self.astrbot_path, "api_key": self.api_key}

    @classmethod
    def from_dict(cls, data: dict) -> "CLIConfig":
        return cls(
            astrbot_path=data.get("astrbot_path"),
            api_key=data.get("api_key")
        )


def ensure_config_dir() -> None:
    """Ensure the CLI config directory exists."""
    CLI_CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_cli_config() -> CLIConfig:
    """Load CLI configuration from file.

    Returns:
        CLIConfig: The loaded configuration, or empty config if file doesn't exist
    """
    if not CLI_CONFIG_FILE.exists():
        return CLIConfig()

    try:
        content = CLI_CONFIG_FILE.read_text(encoding="utf-8")
        # Support both YAML and JSON for backward compatibility
        if CLI_CONFIG_FILE.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(content) or {}
        else:
            data = json.loads(content)
        return CLIConfig.from_dict(data)
    except (json.JSONDecodeError, yaml.YAMLError, KeyError):
        return CLIConfig()


def save_cli_config(config: CLIConfig) -> None:
    """Save CLI configuration to file.

    Args:
        config: The configuration to save
    """
    ensure_config_dir()
    # Use YAML format for better readability
    CLI_CONFIG_FILE.write_text(
        yaml.dump(config.to_dict(), default_flow_style=False, allow_unicode=True),
        encoding="utf-8"
    )


def set_astrbot_path(path: Path) -> None:
    """Set the AstrBot installation path.

    Args:
        path: Path to the AstrBot installation directory
    """
    config = load_cli_config()
    config.astrbot_path = str(path.resolve())
    save_cli_config(config)


def get_astrbot_path() -> Path:
    """Get the AstrBot installation path.

    Priority order:
    1. Saved path in CLI config
    2. Default path (cwd/data/astrbot)

    Returns:
        Path: The AstrBot installation directory
    """
    config = load_cli_config()

    if config.astrbot_path:
        path = Path(config.astrbot_path)
        if path.exists():
            return path

    return DEFAULT_INSTALL_PATH


def get_astrbot_root() -> Path:
    """Get the AstrBot root directory (alias for get_astrbot_path).

    This function is used by other modules for compatibility.

    Returns:
        Path: The AstrBot installation directory
    """
    return get_astrbot_path()


def get_plugins_dir() -> Path:
    """Get the plugins directory path."""
    return get_astrbot_path() / "data" / "plugins"


def get_config_dir() -> Path:
    """Get the config directory path."""
    return get_astrbot_path() / "data" / "config"


def get_cmd_config_path() -> Path:
    """Get the AstrBot command config file path."""
    return get_astrbot_path() / "data" / "cmd_config.json"


def is_astrbot_installed() -> bool:
    """Check if AstrBot is installed at the configured path.

    Returns:
        bool: True if AstrBot is installed, False otherwise
    """
    astrbot_path = get_astrbot_path()
    return (astrbot_path / "main.py").exists()


def validate_astrbot_path(path: Path | None = None) -> Path:
    """Validate and return the AstrBot path.

    Args:
        path: Optional explicit path to validate. If None, uses saved/default path.

    Returns:
        Path: The validated AstrBot path

    Raises:
        ValueError: If AstrBot is not installed at the path
    """
    if path is None:
        path = get_astrbot_path()

    if not (path / "main.py").exists():
        config = load_cli_config()
        if config.astrbot_path:
            raise ValueError(
                f"AstrBot not found at saved path: {path}\n"
                f"Run 'astrbot-cli quick-start' to install AstrBot, or use --path option."
            )
        else:
            raise ValueError(
                f"AstrBot not found at default path: {path}\n"
                f"Run 'astrbot-cli quick-start' to install AstrBot.\n"
                f"You can also specify a path with --path option."
            )

    return path


def print_current_path() -> None:
    """Print the current AstrBot path configuration."""
    config = load_cli_config()

    # Use saved path if available, otherwise use default
    if config.astrbot_path:
        astrbot_path = Path(config.astrbot_path)
        print(f"AstrBot path: {astrbot_path}")
        print(f"  (saved in config)")
    else:
        astrbot_path = DEFAULT_INSTALL_PATH
        print(f"AstrBot path: {astrbot_path}")
        print("  (using default path, not saved in config)")

    if astrbot_path.exists():
        if (astrbot_path / "main.py").exists():
            print("  Status: Installed ✓")
        else:
            print("  Status: Directory exists but AstrBot not installed")
    else:
        print("  Status: Directory does not exist")

    # Show API key status
    if config.api_key:
        print(f"\nAPI Key: configured ✓")
    else:
        print(f"\nAPI Key: not configured")


def get_default_api_key() -> str | None:
    """Get the default API key from CLI config.

    Returns:
        str | None: The API key if configured, None otherwise
    """
    config = load_cli_config()
    return config.api_key


def set_api_key(api_key: str) -> None:
    """Set the default API key in CLI config.

    Args:
        api_key: The API key to save
    """
    config = load_cli_config()
    config.api_key = api_key
    save_cli_config(config)


def resolve_api_key(provided_key: str | None) -> str | None:
    """Resolve the API key to use, with fallback to config.

    Priority:
    1. Explicitly provided key
    2. Key from CLI config

    Args:
        provided_key: API key passed to the command

    Returns:
        str | None: The resolved API key, or None if not available
    """
    if provided_key:
        return provided_key
    return get_default_api_key()
