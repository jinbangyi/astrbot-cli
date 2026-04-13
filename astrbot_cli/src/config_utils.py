"""Configuration management utilities for AstrBot CLI."""

import json
from pathlib import Path
from typing import Any

from .path_config import get_cmd_config_path, get_astrbot_root

# Default configuration settings
DEFAULT_CONFIG = {
    "unique_session": False,
    "rate_limit": {
        "time": 60,
        "count": 30,
        "strategy": "stall",
    },
    "reply_prefix": "",
    "forward_threshold": 1500,
    "enable_id_white_list": True,
    "id_whitelist": [],
    "id_whitelist_log": True,
    "wl_ignore_admin_on_group": True,
    "wl_ignore_admin_on_friend": True,
    "reply_with_mention": False,
    "reply_with_quote": False,
    "path_mapping": [],
    "segmented_reply": {
        "enable": False,
        "only_llm_result": True,
        "interval_method": "random",
        "interval": "1.5,3.5",
        "log_base": 2.6,
        "words_count_threshold": 150,
        "split_mode": "regex",
        "regex": ".*?[。？！~…]+|.+$",
        "split_words": ["。", "？", "！", "~", "…"],
        "content_cleanup_rule": "",
    },
    "no_permission_reply": True,
    "empty_mention_waiting": True,
    "empty_mention_waiting_need_reply": True,
    "friend_message_needs_wake_prefix": False,
    "ignore_bot_self_message": False,
    "ignore_at_all": False,
}

# Configuration schema with descriptions
CONFIG_SCHEMA = {
    "unique_session": {
        "type": "bool",
        "description": "Enable unique session mode (one conversation per user)",
    },
    "rate_limit": {
        "type": "object",
        "description": "Rate limiting settings",
        "fields": {
            "time": {"type": "int", "description": "Time window in seconds"},
            "count": {"type": "int", "description": "Max requests in time window"},
            "strategy": {"type": "string", "options": ["stall", "discard"], "description": "Strategy when limit reached"},
        },
    },
    "reply_prefix": {
        "type": "string",
        "description": "Prefix to add to all bot replies",
    },
    "forward_threshold": {
        "type": "int",
        "description": "Character threshold for message forwarding",
    },
    "enable_id_white_list": {
        "type": "bool",
        "description": "Enable ID whitelist for access control",
    },
    "id_whitelist": {
        "type": "list",
        "description": "List of user/group IDs allowed to use the bot",
    },
    "reply_with_mention": {
        "type": "bool",
        "description": "Mention user when replying",
    },
    "reply_with_quote": {
        "type": "bool",
        "description": "Quote original message when replying",
    },
    "segmented_reply": {
        "type": "object",
        "description": "Segmented/streaming reply settings",
        "fields": {
            "enable": {"type": "bool", "description": "Enable segmented replies"},
            "interval_method": {"type": "string", "options": ["random", "fixed"], "description": "Interval calculation method"},
        },
    },
}


def get_config_path() -> Path:
    """Get the AstrBot config file path."""
    return get_cmd_config_path()


def get_shared_preferences_path() -> Path:
    """Get the shared preferences file path."""
    astrbot_root = get_astrbot_root()
    if astrbot_root:
        return astrbot_root / "data" / "shared_preferences.json"
    return Path.cwd() / "data" / "shared_preferences.json"


def load_config() -> dict:
    """Load AstrBot configuration.

    Returns:
        dict: Configuration dictionary

    """
    config_path = get_config_path()
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"platform": [], "provider": [], "provider_settings": {}, "platform_settings": DEFAULT_CONFIG.copy()}
    return {"platform": [], "provider": [], "provider_settings": {}, "platform_settings": DEFAULT_CONFIG.copy()}


def save_config(config: dict) -> None:
    """Save AstrBot configuration.

    Args:
        config: Configuration dictionary to save

    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def get_settings() -> dict:
    """Get all settings (platform_settings from config).

    Returns:
        dict: Settings dictionary merged with defaults

    """
    config = load_config()
    settings = config.get("platform_settings", {})
    result = DEFAULT_CONFIG.copy()
    result.update(settings)
    return result


def update_settings(updates: dict) -> dict:
    """Update settings.

    Args:
        updates: Dictionary of settings to update

    Returns:
        Updated settings dictionary

    """
    config = load_config()
    current = config.get("platform_settings", DEFAULT_CONFIG.copy())

    def deep_merge(base: dict, update: dict) -> dict:
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    updated = deep_merge(current, updates)
    config["platform_settings"] = updated
    save_config(config)
    return updated


def reset_settings() -> dict:
    """Reset settings to defaults.

    Returns:
        Default settings dictionary

    """
    config = load_config()
    config["platform_settings"] = DEFAULT_CONFIG.copy()
    save_config(config)
    return config["platform_settings"]


def get_settings_schema() -> dict:
    """Get settings schema with descriptions.

    Returns:
        Settings schema dictionary

    """
    return CONFIG_SCHEMA


def get_setting(key: str) -> Any:
    """Get a specific setting value.

    Args:
        key: Setting key (supports dot notation for nested keys)

    Returns:
        Setting value or None if not found

    """
    settings = get_settings()
    keys = key.split(".")
    value = settings
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return None
    return value


def set_setting(key: str, value: Any) -> None:
    """Set a specific setting value.

    Args:
        key: Setting key (supports dot notation for nested keys)
        value: Value to set

    """
    keys = key.split(".")

    if len(keys) == 1:
        update_settings({key: value})
    else:
        # Build nested dict update
        updates = {}
        current = updates
        for k in keys[:-1]:
            current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        update_settings(updates)


def load_shared_preferences() -> dict:
    """Load shared preferences.

    Returns:
        dict: Shared preferences dictionary

    """
    prefs_path = get_shared_preferences_path()
    if prefs_path.exists():
        try:
            return json.loads(prefs_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_shared_preferences(prefs: dict) -> None:
    """Save shared preferences.

    Args:
        prefs: Shared preferences dictionary to save

    """
    prefs_path = get_shared_preferences_path()
    prefs_path.parent.mkdir(parents=True, exist_ok=True)
    prefs_path.write_text(json.dumps(prefs, indent=2, ensure_ascii=False), encoding="utf-8")
