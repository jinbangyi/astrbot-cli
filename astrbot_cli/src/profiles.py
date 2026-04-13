"""Profile management CLI commands for AstrBot."""

import json
from dataclasses import dataclass
from typing import Annotated

import tyro

from .profiles_utils import (
    list_profiles,
    get_profile,
    get_active_profile,
    create_profile,
    update_profile,
    delete_profile,
    set_active_profile,
    set_profile_provider,
    set_profile_persona,
    set_profile_plugins,
)
from .providers_utils import list_provider_configs
from .personas_utils import list_personas


@dataclass
class List:
    """List all profiles.

    Show all configured profiles with their provider and persona assignments.
    """

    def run(self) -> None:
        """Execute the list command."""
        profiles = list_profiles()
        active = get_active_profile()

        if profiles:
            print("\nConfigured Profiles:")
            print("-" * 80)
            print(f"{'ID':<20} {'Name':<20} {'Provider':<15} {'Persona':<15} {'Active':<8}")
            print("-" * 80)

            for profile in profiles:
                is_active = "Yes" if active and profile.get("id") == active.get("id") else ""
                provider = profile.get("provider_id", "")[:13] or "-"
                persona = profile.get("persona_id", "")[:13] or "-"
                print(
                    f"{profile.get('id', ''):<20} {profile.get('name', ''):<20} {provider:<15} {persona:<15} {is_active:<8}"
                )
        else:
            print("No profiles configured.")


@dataclass
class Create:
    """Create a new profile.

    Create a profile with optional provider, persona, and plugin assignments.
    """

    name: Annotated[str, tyro.conf.Positional]  # Profile name
    provider: str | None = None  # Provider ID to use
    persona: str = "default"  # Persona ID to use (default: default)
    plugins: str | None = None  # Comma-separated plugin names, or "*" for all

    def run(self) -> None:
        """Execute the create command."""
        try:
            plugin_list = ["*"] if self.plugins is None else [p.strip() for p in self.plugins.split(",")]
            profile = create_profile(
                name=self.name,
                provider_id=self.provider or "",
                persona_id=self.persona,
                plugins=plugin_list,
            )
            print(f"\nProfile '{profile['id']}' created successfully!")
            print(f"  Name: {profile['name']}")
            if self.provider:
                print(f"  Provider: {self.provider}")
            print(f"  Persona: {self.persona}")
            print(f"  Plugins: {', '.join(plugin_list)}")
            print(f"\nSet as active: astrbot-cli profiles use {profile['id']}")
        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class Delete:
    """Delete a profile.

    Remove a profile by its ID.
    """

    id: Annotated[str, tyro.conf.Positional]  # Profile ID to delete

    def run(self) -> None:
        """Execute the delete command."""
        try:
            delete_profile(self.id)
            print(f"Profile '{self.id}' has been deleted")
        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class Show:
    """Show profile details.

    Display detailed information about a profile.
    """

    id: str | None = None  # Profile ID (default: active profile)

    def run(self) -> None:
        """Execute the show command."""
        profile = get_profile(self.id) if self.id else get_active_profile()

        if profile is None:
            if self.id:
                print(f"Error: Profile '{self.id}' not found")
            else:
                print("No active profile set")
            return

        print(f"\n{'=' * 50}")
        print(f"Profile: {profile.get('name', profile.get('id', 'unknown'))}")
        print(f"{'=' * 50}")
        print(f"ID: {profile.get('id')}")
        print(f"Provider: {profile.get('provider_id') or 'Not set'}")
        print(f"Persona: {profile.get('persona_id', 'default')}")
        print(f"Plugins: {', '.join(profile.get('plugins', ['*']))}")

        settings = profile.get("settings", {})
        if settings:
            print(f"\nSettings:")
            print(json.dumps(settings, indent=2))


@dataclass
class Set:
    """Set profile settings.

    Configure provider, persona, or plugins for a profile.
    """

    id: Annotated[str, tyro.conf.Positional]  # Profile ID
    provider: str | None = None  # Set provider ID
    persona: str | None = None  # Set persona ID
    add_plugin: str | None = None  # Add a plugin
    remove_plugin: str | None = None  # Remove a plugin
    plugins: str | None = None  # Set all plugins (comma-separated)

    def run(self) -> None:
        """Execute the set command."""
        try:
            if self.provider:
                set_profile_provider(self.id, self.provider)
                print(f"Set provider to '{self.provider}' for profile '{self.id}'")

            if self.persona:
                set_profile_persona(self.id, self.persona)
                print(f"Set persona to '{self.persona}' for profile '{self.id}'")

            if self.plugins:
                plugin_list = [p.strip() for p in self.plugins.split(",")]
                set_profile_plugins(self.id, plugin_list)
                print(f"Set plugins to: {', '.join(plugin_list)}")

            from .profiles_utils import add_plugin_to_profile, remove_plugin_from_profile

            if self.add_plugin:
                add_plugin_to_profile(self.id, self.add_plugin)
                print(f"Added plugin '{self.add_plugin}' to profile '{self.id}'")

            if self.remove_plugin:
                remove_plugin_from_profile(self.id, self.remove_plugin)
                print(f"Removed plugin '{self.remove_plugin}' from profile '{self.id}'")

            if not any([self.provider, self.persona, self.plugins, self.add_plugin, self.remove_plugin]):
                print("No settings specified. Use --provider, --persona, --plugins, --add-plugin, or --remove-plugin")

        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class Use:
    """Set active profile.

    Switch to using a different profile.
    """

    id: Annotated[str, tyro.conf.Positional]  # Profile ID to activate

    def run(self) -> None:
        """Execute the use command."""
        try:
            set_active_profile(self.id)
            print(f"Switched to profile '{self.id}'")
        except ValueError as e:
            print(f"Error: {e}")
