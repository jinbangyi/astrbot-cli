"""Configuration management CLI commands for AstrBot."""

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import tyro

from .config_utils import (
    get_settings,
    update_settings,
    reset_settings,
    get_settings_schema,
    get_setting,
    set_setting,
    load_config,
    save_config,
)


@dataclass
class Show:
    """Show current configuration.

    Display all configuration settings. Use --defaults to see default values.
    """

    defaults: bool = False  # Show default values instead of current

    def run(self) -> None:
        """Execute the show command."""
        if self.defaults:
            from .config_utils import DEFAULT_CONFIG

            print("\nDefault Configuration:")
            print("-" * 60)
            print(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False))
        else:
            settings = get_settings()
            print("\nCurrent Configuration:")
            print("-" * 60)
            print(json.dumps(settings, indent=2, ensure_ascii=False))


@dataclass
class Get:
    """Get a configuration value.

    Retrieve a specific configuration value by key.
    """

    key: Annotated[str, tyro.conf.Positional]  # Configuration key (supports dot notation)

    def run(self) -> None:
        """Execute the get command."""
        value = get_setting(self.key)
        if value is not None:
            if isinstance(value, dict | list):
                print(json.dumps(value, indent=2))
            else:
                print(value)
        else:
            print(f"Configuration key '{self.key}' not found")


@dataclass
class Set:
    """Set a configuration value.

    Update a specific configuration value.
    """

    key: Annotated[str, tyro.conf.Positional]  # Configuration key (supports dot notation)
    value: Annotated[str, tyro.conf.Positional]  # Configuration value (JSON format)

    def run(self) -> None:
        """Execute the set command."""
        try:
            parsed_value = json.loads(self.value)
        except json.JSONDecodeError:
            parsed_value = self.value

        set_setting(self.key, parsed_value)
        print(f"Set {self.key} = {parsed_value}")


@dataclass
class Edit:
    """Edit configuration in editor.

    Open the configuration file in your default editor.
    """

    def run(self) -> None:
        """Execute the edit command."""
        from .config_utils import get_config_path

        config_path = get_config_path()
        if not config_path.exists():
            from .config_utils import DEFAULT_CONFIG

            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps({"platform_settings": DEFAULT_CONFIG}, indent=2), encoding="utf-8")

        editor = os.environ.get("EDITOR", "nano")
        subprocess.run([editor, str(config_path)])

        # Read back and validate
        try:
            new_config = json.loads(config_path.read_text(encoding="utf-8"))
            print("Configuration saved successfully")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in config file: {e}")


@dataclass
class Reset:
    """Reset configuration to defaults.

    Restore all settings to their default values.
    """

    confirm: bool = False  # Confirm the reset operation

    def run(self) -> None:
        """Execute the reset command."""
        if not self.confirm:
            print("Warning: This will reset all settings to defaults.")
            print("Use --confirm to proceed.")
            return

        reset_settings()
        print("Configuration has been reset to defaults")


@dataclass
class Schema:
    """Show configuration schema.

    Display the schema with descriptions for all settings.
    """

    def run(self) -> None:
        """Execute the schema command."""
        schema = get_settings_schema()
        print("\nConfiguration Schema:")
        print("-" * 60)

        def print_schema(schema: dict, indent: int = 0):
            for key, info in schema.items():
                prefix = "  " * indent
                type_str = info.get("type", "unknown")
                desc = info.get("description", "")

                print(f"{prefix}{key}:")
                print(f"{prefix}  Type: {type_str}")
                if desc:
                    print(f"{prefix}  Description: {desc}")

                if "options" in info:
                    print(f"{prefix}  Options: {', '.join(info['options'])}")

                if "fields" in info:
                    print(f"{prefix}  Fields:")
                    print_schema(info["fields"], indent + 2)

                print()

        print_schema(schema)
