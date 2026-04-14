"""Provider management CLI commands for AstrBot."""

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import tyro

from .providers_utils import (
    get_available_providers,
    get_provider_config,
    get_provider_config_schema,
    get_provider_defaults,
    set_provider_config,
    list_provider_configs,
    add_provider_config,
    update_provider_config,
    delete_provider_config,
)


@dataclass
class List:
    """List provider configurations.

    Show configured providers. Use --available to see all supported provider types.
    """

    available: bool = False  # Show all available provider types

    def run(self) -> None:
        """Execute the list command."""
        if self.available:
            providers = get_available_providers()
            print("\nAvailable Provider Types:")
            print("-" * 60)
            for provider in providers:
                print(f"  {provider['name']:<15} {provider['desc']}")
        else:
            configs = list_provider_configs()
            if configs:
                print("\nConfigured Providers:")
                print("-" * 80)
                print(f"{'ID':<20} {'Type':<15} {'Enabled':<10} {'Model':<30}")
                print("-" * 80)
                for config in configs:
                    enabled = "Yes" if config.get("enable", False) else "No"
                    model = config.get("model", "")[:28] if config.get("model") else ""
                    print(f"{config.get('id', ''):<20} {config.get('provider', ''):<15} {enabled:<10} {model}")
            else:
                print("No providers configured. Use 'providers add' to add one.")


@dataclass
class Add:
    """Add a new provider configuration.

    Create a new provider configuration with the specified type.
    """

    type: Annotated[str, tyro.conf.Positional]  # Provider type (e.g., openai, deepseek, ollama)
    id: str | None = None  # Provider instance ID (defaults to type name)
    enable: bool = True  # Enable the provider immediately

    def run(self) -> None:
        """Execute the add command."""
        try:
            provider_id = self.id or self.type
            config = add_provider_config(self.type, provider_id, self.enable)
            print(f"\nProvider '{provider_id}' added successfully!")
            print(f"  Type: {self.type}")
            print(f"  Enabled: {self.enable}")
            print(f"\nConfigure with: astrbot-cli providers config {provider_id}")
        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class Remove:
    """Remove a provider configuration.

    Delete a provider configuration by its ID.
    """

    id: Annotated[str, tyro.conf.Positional]  # Provider instance ID to remove

    def run(self) -> None:
        """Execute the remove command."""
        try:
            delete_provider_config(self.id)
            print(f"Provider '{self.id}' has been removed")
        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class Enable:
    """Enable a provider.

    Enable a disabled provider by its ID.
    """

    id: Annotated[str, tyro.conf.Positional]  # Provider instance ID to enable

    def run(self) -> None:
        """Execute the enable command."""
        try:
            update_provider_config(self.id, {"enable": True})
            print(f"Provider '{self.id}' has been enabled")
        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class Disable:
    """Disable a provider.

    Disable an enabled provider by its ID.
    """

    id: Annotated[str, tyro.conf.Positional]  # Provider instance ID to disable

    def run(self) -> None:
        """Execute the disable command."""
        try:
            update_provider_config(self.id, {"enable": False})
            print(f"Provider '{self.id}' has been disabled")
        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class Config:
    """Configure a provider.

    View or edit provider configuration.
    """

    id: Annotated[str, tyro.conf.Positional]  # Provider instance ID
    edit: bool = False  # Open config in editor
    set: str | None = None  # Set a config value (format: key=value)
    get: str | None = None  # Get a config value

    def run(self) -> None:
        """Execute the config command."""
        config = get_provider_config(self.id)
        if config is None:
            print(f"Error: Provider '{self.id}' not found")
            return

        schema = get_provider_config_schema(config.get("provider", ""))

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

            # Validate key against provider defaults (valid fields for this provider type)
            provider_type = config.get("provider", "")
            valid_fields = get_provider_defaults(provider_type) or {}
            # Also allow id, provider, enable
            valid_fields["id"] = None
            valid_fields["provider"] = None
            valid_fields["enable"] = None

            # Check if top-level key is valid
            top_key = keys[0]
            if top_key not in valid_fields:
                print(f"Error: '{top_key}' is not a valid field for provider type '{provider_type}'")
                print(f"Valid fields: {', '.join(sorted(valid_fields.keys()))}")
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
            set_provider_config(self.id, config)
            print(f"Set {key} = {parsed}")

        elif self.edit:
            # Open in editor
            config_path = Path.home() / ".config" / "astrbot" / "providers" / f"{self.id}_config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)

            if not config_path.exists():
                config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

            editor = os.environ.get("EDITOR", "nano")
            subprocess.run([editor, str(config_path)])

            # Read back the edited config
            try:
                new_config = json.loads(config_path.read_text(encoding="utf-8"))
                set_provider_config(self.id, new_config)
                print("Configuration saved")
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in config file: {e}")

        else:
            # Display current config
            print(f"\nConfiguration for '{self.id}':")
            print(f"  Type: {config.get('provider', 'unknown')}")
            print(f"  Enabled: {config.get('enable', False)}")

            if schema:
                print("\nSchema available. Configurable options:")
                for key, info in schema.items():
                    if key in ["type", "id", "enable", "provider", "provider_type"]:
                        continue
                    default = info.get("default", "required")
                    desc = info.get("description", "")
                    print(f"  {key}: {desc}")
                    print(f"    Default: {default}")
                    print()

            print("Current configuration:")
            # Hide sensitive fields
            display_config = config.copy()
            for key in ["key", "token", "secret", "password", "access_token"]:
                if key in display_config:
                    display_config[key] = "***"
            print(json.dumps(display_config, indent=2, ensure_ascii=False))


@dataclass
class Info:
    """Show detailed information about a provider.

    Display provider configuration and status.
    """

    id: Annotated[str, tyro.conf.Positional]  # Provider instance ID

    def run(self) -> None:
        """Execute the info command."""
        config = get_provider_config(self.id)
        if config is None:
            print(f"Error: Provider '{self.id}' not found")
            return

        print(f"\n{'=' * 50}")
        print(f"Provider: {self.id}")
        print(f"{'=' * 50}")
        print(f"Type: {config.get('provider', 'unknown')}")
        print(f"Model Type: {config.get('provider_type', 'chat_completion')}")
        print(f"Enabled: {config.get('enable', False)}")

        # Show other config keys (hiding sensitive ones)
        other_keys = [k for k in config.keys() if k not in ["id", "provider", "type", "provider_type", "enable"]]
        if other_keys:
            print(f"\nConfiguration:")
            for key in other_keys:
                if key in ["key", "token", "secret", "password", "access_token"]:
                    print(f"  {key}: ***")
                else:
                    value = config[key]
                    if isinstance(value, dict | list):
                        print(f"  {key}: {json.dumps(value)}")
                    else:
                        print(f"  {key}: {value}")
