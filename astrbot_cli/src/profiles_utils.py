"""Profile management utilities for AstrBot CLI."""

import json
import uuid
from pathlib import Path
from typing import Any

from .path_config import get_astrbot_root

# Default profile structure
DEFAULT_PROFILE = {
    "id": "default",
    "name": "Default Profile",
    "provider_id": "",
    "persona_id": "default",
    "plugins": ["*"],  # "*" means all plugins
    "settings": {},
}


def get_profiles_path() -> Path:
    """Get the profiles configuration file path."""
    astrbot_root = get_astrbot_root()
    if astrbot_root:
        return astrbot_root / "data" / "profiles.json"
    return Path.cwd() / "data" / "profiles.json"


def load_profiles() -> dict:
    """Load profiles configuration.

    Returns:
        dict: Profiles configuration dictionary

    """
    profiles_path = get_profiles_path()
    if profiles_path.exists():
        try:
            return json.loads(profiles_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return create_default_profiles()
    return create_default_profiles()


def create_default_profiles() -> dict:
    """Create default profiles configuration.

    Returns:
        dict: Default profiles configuration

    """
    return {
        "profiles": [DEFAULT_PROFILE.copy()],
        "active_profile": "default",
    }


def save_profiles(profiles_data: dict) -> None:
    """Save profiles configuration.

    Args:
        profiles_data: Profiles configuration dictionary to save

    """
    profiles_path = get_profiles_path()
    profiles_path.parent.mkdir(parents=True, exist_ok=True)
    profiles_path.write_text(json.dumps(profiles_data, indent=2, ensure_ascii=False), encoding="utf-8")


def list_profiles() -> list[dict]:
    """List all profiles.

    Returns:
        List of profile dictionaries

    """
    data = load_profiles()
    return data.get("profiles", [])


def get_profile(profile_id: str) -> dict | None:
    """Get a profile by ID.

    Args:
        profile_id: Profile ID

    Returns:
        Profile dictionary or None if not found

    """
    profiles = list_profiles()
    for profile in profiles:
        if profile.get("id") == profile_id:
            return profile
    return None


def get_active_profile() -> dict | None:
    """Get the currently active profile.

    Returns:
        Active profile dictionary or None

    """
    data = load_profiles()
    active_id = data.get("active_profile", "default")
    return get_profile(active_id)


def create_profile(
    name: str,
    provider_id: str = "",
    persona_id: str = "default",
    plugins: list[str] | None = None,
    settings: dict | None = None,
) -> dict:
    """Create a new profile.

    Args:
        name: Profile name
        provider_id: Provider ID to use
        persona_id: Persona ID to use
        plugins: List of plugin names (or ["*"] for all)
        settings: Additional settings

    Returns:
        The created profile

    Raises:
        ValueError: If profile name already exists

    """
    data = load_profiles()
    profiles = data.get("profiles", [])

    # Generate a unique ID from name
    profile_id = name.lower().replace(" ", "_").replace("-", "_")
    if not profile_id:
        profile_id = str(uuid.uuid4())[:8]

    # Check if ID already exists
    for profile in profiles:
        if profile.get("id") == profile_id:
            raise ValueError(f"Profile with ID '{profile_id}' already exists")

    # Create new profile
    new_profile = {
        "id": profile_id,
        "name": name,
        "provider_id": provider_id,
        "persona_id": persona_id,
        "plugins": plugins or ["*"],
        "settings": settings or {},
    }

    profiles.append(new_profile)
    data["profiles"] = profiles
    save_profiles(data)

    return new_profile


def update_profile(profile_id: str, updates: dict) -> dict:
    """Update a profile.

    Args:
        profile_id: Profile ID
        updates: Dictionary of fields to update

    Returns:
        Updated profile

    Raises:
        ValueError: If profile not found

    """
    data = load_profiles()
    profiles = data.get("profiles", [])

    for i, profile in enumerate(profiles):
        if profile.get("id") == profile_id:
            profiles[i].update(updates)
            data["profiles"] = profiles
            save_profiles(data)
            return profiles[i]

    raise ValueError(f"Profile '{profile_id}' not found")


def delete_profile(profile_id: str) -> None:
    """Delete a profile.

    Args:
        profile_id: Profile ID

    Raises:
        ValueError: If profile not found or is the active profile

    """
    data = load_profiles()

    # Don't allow deleting the active profile
    if data.get("active_profile") == profile_id:
        raise ValueError(f"Cannot delete the active profile '{profile_id}'. Switch to another profile first.")

    profiles = data.get("profiles", [])

    for i, profile in enumerate(profiles):
        if profile.get("id") == profile_id:
            del profiles[i]
            data["profiles"] = profiles
            save_profiles(data)
            return

    raise ValueError(f"Profile '{profile_id}' not found")


def set_active_profile(profile_id: str) -> None:
    """Set the active profile.

    Args:
        profile_id: Profile ID to make active

    Raises:
        ValueError: If profile not found

    """
    profile = get_profile(profile_id)
    if profile is None:
        raise ValueError(f"Profile '{profile_id}' not found")

    data = load_profiles()
    data["active_profile"] = profile_id
    save_profiles(data)


def set_profile_provider(profile_id: str, provider_id: str) -> None:
    """Set the provider for a profile.

    Args:
        profile_id: Profile ID
        provider_id: Provider ID to use

    """
    update_profile(profile_id, {"provider_id": provider_id})


def set_profile_persona(profile_id: str, persona_id: str) -> None:
    """Set the persona for a profile.

    Args:
        profile_id: Profile ID
        persona_id: Persona ID to use

    """
    update_profile(profile_id, {"persona_id": persona_id})


def set_profile_plugins(profile_id: str, plugins: list[str]) -> None:
    """Set the plugins for a profile.

    Args:
        profile_id: Profile ID
        plugins: List of plugin names

    """
    update_profile(profile_id, {"plugins": plugins})


def add_plugin_to_profile(profile_id: str, plugin_name: str) -> None:
    """Add a plugin to a profile's plugin list.

    Args:
        profile_id: Profile ID
        plugin_name: Plugin name to add

    """
    profile = get_profile(profile_id)
    if profile is None:
        raise ValueError(f"Profile '{profile_id}' not found")

    plugins = profile.get("plugins", [])
    if plugin_name not in plugins:
        plugins.append(plugin_name)
        update_profile(profile_id, {"plugins": plugins})


def remove_plugin_from_profile(profile_id: str, plugin_name: str) -> None:
    """Remove a plugin from a profile's plugin list.

    Args:
        profile_id: Profile ID
        plugin_name: Plugin name to remove

    """
    profile = get_profile(profile_id)
    if profile is None:
        raise ValueError(f"Profile '{profile_id}' not found")

    plugins = profile.get("plugins", [])
    if plugin_name in plugins:
        plugins.remove(plugin_name)
        update_profile(profile_id, {"plugins": plugins})
