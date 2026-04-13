"""Bot management utilities for AstrBot CLI."""

import json
from pathlib import Path
from typing import Any

from .path_config import get_cmd_config_path

# Known bot/platform types with their descriptions
KNOWN_BOTS = {
    "aiocqhttp": "QQ adapter via OneBot (go-cqhttp, Lagrange, etc.)",
    "telegram": "Telegram Bot API",
    "discord": "Discord Bot",
    "slack": "Slack Bot",
    "kook": "KOOK (开黑啦) Bot",
    "lark": "Lark/Feishu Bot",
    "dingtalk": "DingTalk Bot",
    "wecom": "WeChat Work (企业微信) Bot",
    "wecom_ai_bot": "WeChat Work AI Bot",
    "weixin_official_account": "WeChat Official Account (公众号)",
    "weixin_oc": "WeChat Official Account (旧版)",
    "mattermost": "Mattermost Bot",
    "misskey": "Misskey Bot",
    "matrix": "Matrix Bot",
    "qqofficial": "QQ Official API",
    "qqofficial_webhook": "QQ Official API (Webhook mode)",
    "satori": "Satori Protocol",
    "vocechat": "VoceChat Bot",
    "webchat": "Web Chat (built-in)",
    "line": "LINE Bot",
}


def get_config_path() -> Path:
    """Get the AstrBot config file path."""
    return get_cmd_config_path()


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
            return {"platform": [], "provider": [], "provider_settings": {}}
    return {"platform": [], "provider": [], "provider_settings": {}}


def save_config(config: dict) -> None:
    """Save AstrBot configuration.

    Args:
        config: Configuration dictionary to save

    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def get_available_bots() -> list[dict[str, str]]:
    """Get list of available bot types.

    Returns:
        List of bot info dicts with name and desc

    """
    bots = []
    for name, desc in KNOWN_BOTS.items():
        bots.append({"name": name, "desc": desc})
    return bots


def list_bot_configs() -> list[dict]:
    """List all configured bots.

    Returns:
        List of bot configuration dictionaries

    """
    config = load_config()
    return config.get("platform", [])


def get_bot_config(bot_id: str) -> dict | None:
    """Get a bot configuration by ID.

    Args:
        bot_id: Bot instance ID

    Returns:
        Bot configuration dict or None if not found

    """
    config = load_config()
    platforms = config.get("platform", [])
    for platform in platforms:
        if platform.get("id") == bot_id:
            return platform
    return None


def add_bot_config(bot_type: str, bot_id: str, enable: bool = True) -> dict:
    """Add a new bot configuration.

    Args:
        bot_type: Bot type (e.g., telegram, discord)
        bot_id: Bot instance ID
        enable: Whether to enable the bot

    Returns:
        The created bot configuration

    Raises:
        ValueError: If bot ID already exists or type is unknown

    """
    if bot_type not in KNOWN_BOTS:
        raise ValueError(f"Unknown bot type: {bot_type}. Available types: {', '.join(KNOWN_BOTS.keys())}")

    config = load_config()
    platforms = config.get("platform", [])

    # Check if ID already exists
    for platform in platforms:
        if platform.get("id") == bot_id:
            raise ValueError(f"Bot with ID '{bot_id}' already exists")

    # Create new bot config
    new_bot = {
        "id": bot_id,
        "type": bot_type,
        "enable": enable,
    }

    # Add type-specific default config
    type_defaults = get_bot_defaults(bot_type)
    new_bot.update(type_defaults)

    platforms.append(new_bot)
    config["platform"] = platforms
    save_config(config)

    return new_bot


def get_bot_defaults(bot_type: str) -> dict:
    """Get default configuration values for a bot type.

    Args:
        bot_type: Bot type

    Returns:
        Dictionary of default configuration values

    """
    defaults = {
        "telegram": {
            "token": "",
            "telegram_api_base_url": "https://api.telegram.org/bot",
            "telegram_file_base_url": "https://api.telegram.org/file/bot",
            "telegram_command_register": True,
            "telegram_command_auto_refresh": False,
            "telegram_command_register_interval": 300,
            "telegram_polling_restart_delay": 5.0,
        },
        "discord": {
            "discord_token": "",
            "discord_proxy": "",
            "discord_command_register": True,
            "discord_activity_name": "",
            "discord_allow_bot_messages": False,
        },
        "aiocqhttp": {
            "ws_reverse_host": "0.0.0.0",
            "ws_reverse_port": 6199,
            "ws_reverse_token": "",
        },
        "slack": {
            "bot_token": "",
            "app_token": "",
            "signing_secret": "",
            "slack_connection_mode": "socket",
            "unified_webhook_mode": True,
            "webhook_uuid": "",
            "slack_webhook_host": "0.0.0.0",
            "slack_webhook_port": 6197,
            "slack_webhook_path": "/astrbot-slack-webhook/callback",
        },
        "kook": {
            "kook_bot_token": "",
            "kook_reconnect_delay": 5,
            "kook_max_reconnect_delay": 300,
            "kook_max_retry_delay": 60,
            "kook_heartbeat_interval": 30,
            "kook_heartbeat_timeout": 60,
            "kook_max_heartbeat_failures": 3,
            "kook_max_consecutive_failures": 10,
        },
        "lark": {
            "lark_app_id": "",
            "lark_app_secret": "",
            "lark_bot_name": "",
            "lark_encrypt_key": "",
            "lark_verification_token": "",
            "unified_webhook_mode": True,
            "webhook_uuid": "",
            "port": 6193,
        },
        "dingtalk": {
            "dingtalk_client_id": "",
            "dingtalk_client_secret": "",
            "card_template_id": "",
        },
        "wecom": {
            "corpid": "",
            "secret": "",
            "token": "",
            "encoding_aes_key": "",
            "kf_name": "",
            "api_base_url": "https://qyapi.weixin.qq.com/cgi-bin/",
            "unified_webhook_mode": True,
            "webhook_uuid": "",
            "callback_server_host": "0.0.0.0",
            "port": 6195,
        },
        "wecom_ai_bot": {
            "wecom_ai_bot_connection_mode": "long_connection",
            "wecom_ai_bot_name": "",
            "wecomaibot_ws_bot_id": "",
            "wecomaibot_ws_secret": "",
            "wecomaibot_token": "",
            "wecomaibot_encoding_aes_key": "",
            "wecomaibot_init_respond_text": "",
            "wecomaibot_friend_message_welcome_text": "",
            "msg_push_webhook_url": "",
            "only_use_webhook_url_to_send": False,
            "wecomaibot_ws_url": "wss://openws.work.weixin.qq.com",
            "wecomaibot_heartbeat_interval": 30,
            "unified_webhook_mode": True,
            "webhook_uuid": "",
            "port": 6198,
        },
        "weixin_official_account": {
            "appid": "",
            "secret": "",
            "token": "",
            "encoding_aes_key": "",
            "api_base_url": "https://api.weixin.qq.com/cgi-bin/",
            "unified_webhook_mode": True,
            "webhook_uuid": "",
            "callback_server_host": "0.0.0.0",
            "port": 6194,
            "active_send_mode": False,
        },
        "mattermost": {
            "mattermost_url": "",
            "mattermost_token": "",
            "mattermost_team_name": "",
        },
        "misskey": {
            "misskey_instance_url": "https://misskey.example",
            "misskey_token": "",
            "misskey_default_visibility": "public",
            "misskey_local_only": False,
            "misskey_enable_chat": True,
            "misskey_allow_insecure_downloads": False,
            "misskey_download_timeout": 15,
            "misskey_download_chunk_size": 65536,
            "misskey_max_download_bytes": None,
            "misskey_enable_file_upload": True,
            "misskey_upload_concurrency": 3,
            "misskey_upload_folder": "",
        },
        "matrix": {
            "matrix_homeserver": "",
            "matrix_user_id": "",
            "matrix_access_token": "",
            "matrix_device_id": "",
        },
        "qqofficial": {
            "appid": "",
            "secret": "",
            "enable_group_c2c": True,
            "enable_guild_direct_message": True,
        },
        "qqofficial_webhook": {
            "appid": "",
            "secret": "",
            "is_sandbox": False,
            "unified_webhook_mode": True,
            "webhook_uuid": "",
            "callback_server_host": "0.0.0.0",
            "port": 6196,
        },
        "satori": {
            "satori_host": "localhost",
            "satori_port": 8080,
        },
        "vocechat": {
            "vocechat_webhook_url": "",
            "vocechat_api_url": "",
        },
        "webchat": {},
        "line": {
            "channel_access_token": "",
            "channel_secret": "",
            "unified_webhook_mode": True,
            "webhook_uuid": "",
            "line_webhook_host": "0.0.0.0",
            "line_webhook_port": 6192,
        },
        "weixin_oc": {
            "weixin_oc_base_url": "https://ilinkai.weixin.qq.com",
            "weixin_oc_bot_type": "3",
            "weixin_oc_qr_poll_interval": 3,
            "weixin_oc_long_poll_timeout_ms": 30000,
            "weixin_oc_api_timeout_ms": 30000,
            "weixin_oc_token": "",
        },
    }
    return defaults.get(bot_type, {})


def update_bot_config(bot_id: str, updates: dict) -> dict:
    """Update a bot configuration.

    Args:
        bot_id: Bot instance ID
        updates: Dictionary of fields to update

    Returns:
        Updated bot configuration

    Raises:
        ValueError: If bot not found

    """
    config = load_config()
    platforms = config.get("platform", [])

    for i, platform in enumerate(platforms):
        if platform.get("id") == bot_id:
            platforms[i].update(updates)
            config["platform"] = platforms
            save_config(config)
            return platforms[i]

    raise ValueError(f"Bot '{bot_id}' not found")


def set_bot_config(bot_id: str, new_config: dict) -> None:
    """Set the complete configuration for a bot.

    Args:
        bot_id: Bot instance ID
        new_config: New configuration dictionary

    Raises:
        ValueError: If bot not found

    """
    config = load_config()
    platforms = config.get("platform", [])

    for i, platform in enumerate(platforms):
        if platform.get("id") == bot_id:
            new_config["id"] = bot_id
            new_config["type"] = platform.get("type", new_config.get("type", ""))
            platforms[i] = new_config
            config["platform"] = platforms
            save_config(config)
            return

    raise ValueError(f"Bot '{bot_id}' not found")


def delete_bot_config(bot_id: str) -> None:
    """Delete a bot configuration.

    Args:
        bot_id: Bot instance ID

    Raises:
        ValueError: If bot not found

    """
    config = load_config()
    platforms = config.get("platform", [])

    for i, platform in enumerate(platforms):
        if platform.get("id") == bot_id:
            del platforms[i]
            config["platform"] = platforms
            save_config(config)
            return

    raise ValueError(f"Bot '{bot_id}' not found")


def get_bot_config_schema(bot_type: str) -> dict | None:
    """Get configuration schema for a bot type.

    Args:
        bot_type: Bot type

    Returns:
        Configuration schema dict or None if not available

    """
    schemas = {
        "telegram": {
            "token": {"type": "string", "description": "Telegram Bot Token", "required": True},
            "telegram_api_base_url": {"type": "string", "description": "Telegram API base URL", "default": "https://api.telegram.org/bot"},
        },
        "discord": {
            "discord_token": {"type": "string", "description": "Discord Bot Token", "required": True},
            "discord_proxy": {"type": "string", "description": "Proxy URL for Discord API", "default": ""},
        },
        "aiocqhttp": {
            "ws_reverse_host": {"type": "string", "description": "WebSocket reverse host", "default": "0.0.0.0"},
            "ws_reverse_port": {"type": "int", "description": "WebSocket reverse port", "default": 6199},
            "ws_reverse_token": {"type": "string", "description": "WebSocket reverse access token", "default": ""},
        },
    }
    return schemas.get(bot_type)
