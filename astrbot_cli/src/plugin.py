"""Plugin management CLI commands for AstrBot."""

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import tyro

from .plugin_utils import (
    PluginInfo,
    PluginStatus,
    build_plugin_list,
    display_plugins,
    get_plugin_config,
    get_plugin_config_schema,
    get_plugin_config_schema_path,
    install_plugin,
    set_plugin_config,
    uninstall_plugin,
    update_plugin,
)


@dataclass
class Install:
    """Install a plugin.

    Can install by:
    - Plugin name (from registry)
    - GitHub repository URL
    - Local path (e.g., ~/path/to/plugin or /absolute/path/to/plugin)
    """

    name: str  # Plugin name, GitHub repository URL, or local path
    proxy: str | None = None  # Proxy server for GitHub access

    def run(self) -> None:
        """Execute the install command."""
        try:
            plugin = install_plugin(self.name, self.proxy)
            print(f"\nPlugin '{plugin.name}' installed successfully!")
            print(f"  Version: {plugin.version}")
            print(f"  Author: {plugin.author}")
            print(f"  Description: {plugin.desc}")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Failed to install plugin: {e}")


@dataclass
class Uninstall:
    """Uninstall a plugin.

    Removes the plugin directory and its data.
    """

    name: str  # Plugin name to uninstall

    def run(self) -> None:
        """Execute the uninstall command."""
        try:
            uninstall_plugin(self.name)
        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class Update:
    """Update plugins.

    Update a specific plugin or all plugins that have updates available.
    """

    name: str | None = None  # Plugin name to update (omit to update all)
    proxy: str | None = None  # Proxy server for GitHub access

    def run(self) -> None:
        """Execute the update command."""
        try:
            updated = update_plugin(self.name, self.proxy)
            if updated:
                print(f"\nUpdated {len(updated)} plugin(s):")
                for plugin in updated:
                    print(f"  - {plugin.name} ({plugin.version})")
        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class PluginList:
    """List plugins.

    Show installed plugins and their status. Use --all to see available plugins.
    """

    all: bool = False  # Show all plugins including uninstalled ones

    def run(self) -> None:
        """Execute the list command."""
        plugins = build_plugin_list()

        # Categorize plugins
        unpublished = [p for p in plugins if p.status == PluginStatus.NOT_PUBLISHED]
        need_update = [p for p in plugins if p.status == PluginStatus.NEED_UPDATE]
        installed = [p for p in plugins if p.status == PluginStatus.INSTALLED]
        not_installed = [p for p in plugins if p.status == PluginStatus.NOT_INSTALLED]

        # Display by category
        if unpublished:
            display_plugins(unpublished, "Unpublished Plugins (local only)")

        if need_update:
            display_plugins(need_update, "Plugins Needing Update")

        if installed:
            display_plugins(installed, "Installed Plugins")

        if self.all and not_installed:
            display_plugins(not_installed, "Available Plugins")

        if not any([unpublished, need_update, installed]):
            print("No plugins installed. Use --all to see available plugins.")


@dataclass
class Search:
    """Search for plugins.

    Search plugins by name, description, or author.
    """

    query: str  # Search query

    def run(self) -> None:
        """Execute the search command."""
        plugins = build_plugin_list()
        query_lower = self.query.lower()

        matched = [
            p
            for p in plugins
            if query_lower in p.name.lower()
            or query_lower in p.desc.lower()
            or query_lower in p.author.lower()
        ]

        if matched:
            display_plugins(matched, f"Search results for '{self.query}'")
        else:
            print(f"No plugins matching '{self.query}' found")


@dataclass
class Config:
    """Configure a plugin.

    View or edit plugin configuration. Plugins define their config schema
    in _conf_schema.json file.
    """

    name: str  # Plugin name
    edit: bool = False  # Open config in editor
    set: str | None = None  # Set a config value (format: key=value)
    get: str | None = None  # Get a config value
    all: bool = False  # Show all config values including defaults

    def run(self) -> None:
        """Execute the config command."""
        # Check if plugin is installed
        plugins = build_plugin_list()
        plugin = next((p for p in plugins if p.name == self.name), None)

        if not plugin or not plugin.local_path:
            print(f"Error: Plugin '{self.name}' is not installed")
            return

        config = get_plugin_config(self.name)
        schema = get_plugin_config_schema(self.name)

        if self.get:
            # Get a specific config value
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
            # Set a config value
            if "=" not in self.set:
                print("Error: --set requires format 'key=value'")
                return

            key, value = self.set.split("=", 1)
            keys = key.split(".")

            # Validate key against plugin config schema if available
            if schema:
                # Extract top-level keys from schema
                valid_fields = set(schema.keys())
                top_key = keys[0]
                if top_key not in valid_fields:
                    print(f"Error: '{top_key}' is not a valid field for plugin '{self.name}'")
                    print(f"Valid fields: {', '.join(sorted(valid_fields))}")
                    return

            # Navigate to the right nested dict
            current = config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]

            # Try to parse value as JSON, otherwise treat as string
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = value

            current[keys[-1]] = parsed
            set_plugin_config(self.name, config)
            print(f"Set {key} = {parsed}")

        elif self.edit:
            # Open in editor
            config_path = Path.home() / ".config" / "astrbot" / "plugins" / f"{self.name}_config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)

            if not config_path.exists():
                config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

            editor = os.environ.get("EDITOR", "nano")
            subprocess.run([editor, str(config_path)])

            # Read back the edited config
            try:
                new_config = json.loads(config_path.read_text(encoding="utf-8"))
                set_plugin_config(self.name, new_config)
                print("Configuration saved")
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in config file: {e}")

        elif self.all:
            # Display all config values including defaults
            print(f"\nConfiguration for '{self.name}' (all values):")
            if schema:
                merged_config = {}
                for key, info in schema.items():
                    default = info.get("default")
                    desc = info.get("description", info.get("desc", ""))
                    hint = info.get("hint", "")
                    merged_config[key] = {
                        "value": config.get(key, default),
                        "default": default,
                        "description": desc,
                    }
                    if hint:
                        merged_config[key]["hint"] = hint
                print(json.dumps(merged_config, indent=2, ensure_ascii=False))
            elif config:
                print(json.dumps(config, indent=2, ensure_ascii=False))
            else:
                print("No configuration available")

        else:
            # Display current config
            print(f"\nConfiguration for '{self.name}':")
            if schema:
                print("\nSchema available. Configurable options:")
                for key, info in schema.items():
                    default = info.get("default", "required")
                    desc = info.get("description", info.get("desc", ""))
                    hint = info.get("hint", "")
                    print(f"  {key}: {desc}")
                    if hint:
                        print(f"    Hint: {hint}")
                    print(f"    Default: {default}")
                    print()

            if config:
                print("Current configuration:")
                print(json.dumps(config, indent=2, ensure_ascii=False))
            else:
                print("No configuration set (using defaults)")


@dataclass
class Info:
    """Show detailed information about a plugin.

    Display plugin metadata, configuration schema, and status.
    """

    name: str  # Plugin name

    def run(self) -> None:
        """Execute the info command."""
        plugins = build_plugin_list()
        plugin = next((p for p in plugins if p.name == self.name), None)

        if not plugin:
            print(f"Error: Plugin '{self.name}' not found")
            return

        print(f"\n{'=' * 50}")
        print(f"Plugin: {plugin.name}")
        print(f"{'=' * 50}")
        print(f"Version: {plugin.version}")
        print(f"Author: {plugin.author}")
        print(f"Status: {plugin.status.value}")
        print(f"Repository: {plugin.repo}")
        print(f"\nDescription:")
        print(f"  {plugin.desc}")

        if plugin.local_path:
            print(f"\nLocal path: {plugin.local_path}")

            # Check for config schema
            schema_path = get_plugin_config_schema_path(self.name)
            if schema_path:
                print(f"\nConfiguration schema available.")

            # Show current config
            config = get_plugin_config(self.name)
            if config:
                print(f"\nCurrent configuration:")
                print(json.dumps(config, indent=2, ensure_ascii=False))


# Union type for subcommands
Commands = Annotated[
    Install | Uninstall | Update | PluginList | Search | Config | Info,
    tyro.conf.subcommand(),
]


def run_plugin_command(cmd: Install | Uninstall | Update | PluginList | Search | Config | Info) -> None:
    """Run a plugin command based on its type.

    Args:
        cmd: The plugin command to execute

    """
    cmd.run()
