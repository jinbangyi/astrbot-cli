"""Bot management CLI commands for AstrBot."""

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import tyro

from .bots_utils import (
    get_available_bots,
    get_bot_config,
    get_bot_config_schema,
    set_bot_config,
    list_bot_configs,
    add_bot_config,
    update_bot_config,
    delete_bot_config,
)


@dataclass
class List:
    """List bot configurations.

    Show configured bots. Use --available to see all supported bot types.
    """

    available: bool = False  # Show all available bot types

    def run(self) -> None:
        """Execute the list command."""
        if self.available:
            bots = get_available_bots()
            print("\nAvailable Bot Types:")
            print("-" * 60)
            for bot in bots:
                print(f"  {bot['name']:<20} {bot['desc']}")
        else:
            configs = list_bot_configs()
            if configs:
                print("\nConfigured Bots:")
                print("-" * 80)
                print(f"{'ID':<20} {'Type':<15} {'Enabled':<10} {'Description':<30}")
                print("-" * 80)
                for config in configs:
                    enabled = "Yes" if config.get("enable", False) else "No"
                    desc = config.get("desc", "")[:28]
                    print(f"{config.get('id', ''):<20} {config.get('type', ''):<15} {enabled:<10} {desc}")
            else:
                print("No bots configured. Use 'bots add' to add one.")


@dataclass
class Add:
    """Add a new bot configuration.

    Create a new bot configuration with the specified type.
    """

    type: Annotated[str, tyro.conf.Positional]  # Bot type (e.g., telegram, discord, aiocqhttp)
    id: str | None = None  # Bot instance ID (defaults to type name)
    enable: bool = True  # Enable the bot immediately

    def run(self) -> None:
        """Execute the add command."""
        try:
            bot_id = self.id or self.type
            config = add_bot_config(self.type, bot_id, self.enable)
            print(f"\nBot '{bot_id}' added successfully!")
            print(f"  Type: {self.type}")
            print(f"  Enabled: {self.enable}")
            print(f"\nConfigure with: astrbot-cli bots config {bot_id}")
        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class Remove:
    """Remove a bot configuration.

    Delete a bot configuration by its ID.
    """

    id: Annotated[str, tyro.conf.Positional]  # Bot instance ID to remove

    def run(self) -> None:
        """Execute the remove command."""
        try:
            delete_bot_config(self.id)
            print(f"Bot '{self.id}' has been removed")
        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class Enable:
    """Enable a bot.

    Enable a disabled bot by its ID.
    """

    id: Annotated[str, tyro.conf.Positional]  # Bot instance ID to enable

    def run(self) -> None:
        """Execute the enable command."""
        try:
            update_bot_config(self.id, {"enable": True})
            print(f"Bot '{self.id}' has been enabled")
        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class Disable:
    """Disable a bot.

    Disable an enabled bot by its ID.
    """

    id: Annotated[str, tyro.conf.Positional]  # Bot instance ID to disable

    def run(self) -> None:
        """Execute the disable command."""
        try:
            update_bot_config(self.id, {"enable": False})
            print(f"Bot '{self.id}' has been disabled")
        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class Config:
    """Configure a bot.

    View or edit bot configuration.
    """

    id: Annotated[str, tyro.conf.Positional]  # Bot instance ID
    edit: bool = False  # Open config in editor
    set: str | None = None  # Set a config value (format: key=value)
    get: str | None = None  # Get a config value

    def run(self) -> None:
        """Execute the config command."""
        config = get_bot_config(self.id)
        if config is None:
            print(f"Error: Bot '{self.id}' not found")
            return

        schema = get_bot_config_schema(config.get("type", ""))

        if self.get:
            keys = self.get.split(".")
            value = config
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break
            if value is not None:
                if isinstance(value, dict | list):
                    print(json.dumps(value, indent=2))
                else:
                    print(value)
            else:
                print(f"Config key '{self.get}' not found")

        elif self.set:
            if "=" not in self.set:
                print("Error: --set requires format 'key=value'")
                return

            key, value = self.set.split("=", 1)
            keys = key.split(".")

            current = config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]

            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = value

            current[keys[-1]] = parsed
            set_bot_config(self.id, config)
            print(f"Set {key} = {parsed}")

        elif self.edit:
            config_path = Path.home() / ".config" / "astrbot" / "bots" / f"{self.id}_config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)

            if not config_path.exists():
                config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

            editor = os.environ.get("EDITOR", "nano")
            subprocess.run([editor, str(config_path)])

            try:
                new_config = json.loads(config_path.read_text(encoding="utf-8"))
                set_bot_config(self.id, new_config)
                print("Configuration saved")
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in config file: {e}")

        else:
            print(f"\nConfiguration for '{self.id}':")
            print(f"  Type: {config.get('type', 'unknown')}")
            print(f"  Enabled: {config.get('enable', False)}")

            if schema:
                print("\nSchema available. Configurable options:")
                for key, info in schema.items():
                    if key in ["type", "id", "enable"]:
                        continue
                    default = info.get("default", "required")
                    desc = info.get("description", "")
                    print(f"  {key}: {desc}")
                    print(f"    Default: {default}")
                    print()

            print("Current configuration:")
            display_config = config.copy()
            for key in ["token", "key", "secret", "password", "access_token"]:
                if key in display_config:
                    display_config[key] = "***"
            print(json.dumps(display_config, indent=2, ensure_ascii=False))


@dataclass
class Info:
    """Show detailed information about a bot.

    Display bot configuration and status.
    """

    id: Annotated[str, tyro.conf.Positional]  # Bot instance ID

    def run(self) -> None:
        """Execute the info command."""
        config = get_bot_config(self.id)
        if config is None:
            print(f"Error: Bot '{self.id}' not found")
            return

        print(f"\n{'=' * 50}")
        print(f"Bot: {self.id}")
        print(f"{'=' * 50}")
        print(f"Type: {config.get('type', 'unknown')}")
        print(f"Enabled: {config.get('enable', False)}")

        other_keys = [k for k in config.keys() if k not in ["id", "type", "enable", "desc"]]
        if other_keys:
            print(f"\nConfiguration:")
            for key in other_keys:
                if key in ["token", "key", "secret", "password", "access_token"]:
                    print(f"  {key}: ***")
                else:
                    value = config[key]
                    if isinstance(value, dict | list):
                        print(f"  {key}: {json.dumps(value)}")
                    else:
                        print(f"  {key}: {value}")
