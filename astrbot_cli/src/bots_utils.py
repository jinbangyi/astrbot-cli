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
            # Use utf-8-sig to handle BOM if present
            return json.loads(config_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            # Return empty dict if JSON is invalid
            return {}
    # Return empty dict - preserves existing keys when saving
    return {}


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
            "token": {
                "type": "string",
                "description": "Telegram Bot Token (from @BotFather)",
                "required": True,
            },
            "telegram_api_base_url": {
                "type": "string",
                "description": "Telegram API base URL (for custom API endpoints)",
                "default": "https://api.telegram.org/bot",
            },
            "telegram_file_base_url": {
                "type": "string",
                "description": "Telegram File API base URL",
                "default": "https://api.telegram.org/file/bot",
            },
            "telegram_command_register": {
                "type": "bool",
                "description": "Register bot commands with Telegram",
                "default": True,
            },
            "telegram_command_auto_refresh": {
                "type": "bool",
                "description": "Auto-refresh command registration",
                "default": False,
            },
            "telegram_command_register_interval": {
                "type": "int",
                "description": "Command registration refresh interval (seconds)",
                "default": 300,
            },
            "telegram_polling_restart_delay": {
                "type": "float",
                "description": "Delay before restarting polling after failure (seconds)",
                "default": 5.0,
            },
        },
        "discord": {
            "discord_token": {
                "type": "string",
                "description": "Discord Bot Token (from Discord Developer Portal)",
                "required": True,
            },
            "discord_proxy": {
                "type": "string",
                "description": "Proxy URL for Discord API (optional)",
                "default": "",
            },
            "discord_command_register": {
                "type": "bool",
                "description": "Register slash commands with Discord",
                "default": True,
            },
            "discord_activity_name": {
                "type": "string",
                "description": "Bot activity status text",
                "default": "",
            },
            "discord_allow_bot_messages": {
                "type": "bool",
                "description": "Allow bot to respond to other bots",
                "default": False,
            },
        },
        "aiocqhttp": {
            "ws_reverse_host": {
                "type": "string",
                "description": "WebSocket reverse server host",
                "default": "0.0.0.0",
            },
            "ws_reverse_port": {
                "type": "int",
                "description": "WebSocket reverse server port",
                "default": 6199,
            },
            "ws_reverse_token": {
                "type": "string",
                "description": "WebSocket reverse access token (for authentication)",
                "default": "",
            },
        },
        "slack": {
            "bot_token": {
                "type": "string",
                "description": "Slack Bot User OAuth Token (xoxb-...)",
                "required": True,
            },
            "app_token": {
                "type": "string",
                "description": "Slack App-Level Token (xapp-...)",
                "required": True,
            },
            "signing_secret": {
                "type": "string",
                "description": "Slack Signing Secret",
                "default": "",
            },
            "slack_connection_mode": {
                "type": "string",
                "description": "Connection mode: 'socket' or 'webhook'",
                "default": "socket",
            },
            "unified_webhook_mode": {
                "type": "bool",
                "description": "Use unified webhook mode",
                "default": True,
            },
            "webhook_uuid": {
                "type": "string",
                "description": "Webhook UUID for unified mode",
                "default": "",
            },
            "slack_webhook_host": {
                "type": "string",
                "description": "Webhook server host",
                "default": "0.0.0.0",
            },
            "slack_webhook_port": {
                "type": "int",
                "description": "Webhook server port",
                "default": 6197,
            },
            "slack_webhook_path": {
                "type": "string",
                "description": "Webhook callback path",
                "default": "/astrbot-slack-webhook/callback",
            },
        },
        "kook": {
            "kook_bot_token": {
                "type": "string",
                "description": "KOOK Bot Token (from KOOK Developer Portal)",
                "required": True,
            },
            "kook_reconnect_delay": {
                "type": "int",
                "description": "Initial reconnect delay (seconds)",
                "default": 5,
            },
            "kook_max_reconnect_delay": {
                "type": "int",
                "description": "Maximum reconnect delay (seconds)",
                "default": 300,
            },
            "kook_max_retry_delay": {
                "type": "int",
                "description": "Maximum retry delay (seconds)",
                "default": 60,
            },
            "kook_heartbeat_interval": {
                "type": "int",
                "description": "Heartbeat interval (seconds)",
                "default": 30,
            },
            "kook_heartbeat_timeout": {
                "type": "int",
                "description": "Heartbeat timeout (seconds)",
                "default": 60,
            },
            "kook_max_heartbeat_failures": {
                "type": "int",
                "description": "Maximum consecutive heartbeat failures",
                "default": 3,
            },
            "kook_max_consecutive_failures": {
                "type": "int",
                "description": "Maximum consecutive failures before reconnect",
                "default": 10,
            },
        },
        "lark": {
            "lark_app_id": {
                "type": "string",
                "description": "Lark/Feishu App ID",
                "required": True,
            },
            "lark_app_secret": {
                "type": "string",
                "description": "Lark/Feishu App Secret",
                "required": True,
            },
            "lark_bot_name": {
                "type": "string",
                "description": "Bot display name",
                "default": "",
            },
            "lark_encrypt_key": {
                "type": "string",
                "description": "Encryption key for message encryption",
                "default": "",
            },
            "lark_verification_token": {
                "type": "string",
                "description": "Verification token for webhook",
                "default": "",
            },
            "unified_webhook_mode": {
                "type": "bool",
                "description": "Use unified webhook mode",
                "default": True,
            },
            "webhook_uuid": {
                "type": "string",
                "description": "Webhook UUID for unified mode",
                "default": "",
            },
            "port": {
                "type": "int",
                "description": "Webhook server port",
                "default": 6193,
            },
        },
        "dingtalk": {
            "dingtalk_client_id": {
                "type": "string",
                "description": "DingTalk Client ID (AppKey)",
                "required": True,
            },
            "dingtalk_client_secret": {
                "type": "string",
                "description": "DingTalk Client Secret (AppSecret)",
                "required": True,
            },
            "card_template_id": {
                "type": "string",
                "description": "Card template ID for rich messages",
                "default": "",
            },
        },
        "wecom": {
            "corpid": {
                "type": "string",
                "description": "WeChat Work Corp ID",
                "required": True,
            },
            "secret": {
                "type": "string",
                "description": "WeChat Work App Secret",
                "required": True,
            },
            "token": {
                "type": "string",
                "description": "Token for callback verification",
                "default": "",
            },
            "encoding_aes_key": {
                "type": "string",
                "description": "Encoding AES Key for message encryption",
                "default": "",
            },
            "kf_name": {
                "type": "string",
                "description": "Customer Service name (for customer service mode)",
                "default": "",
            },
            "api_base_url": {
                "type": "string",
                "description": "WeChat Work API base URL",
                "default": "https://qyapi.weixin.qq.com/cgi-bin/",
            },
            "unified_webhook_mode": {
                "type": "bool",
                "description": "Use unified webhook mode",
                "default": True,
            },
            "webhook_uuid": {
                "type": "string",
                "description": "Webhook UUID for unified mode",
                "default": "",
            },
            "callback_server_host": {
                "type": "string",
                "description": "Callback server host",
                "default": "0.0.0.0",
            },
            "port": {
                "type": "int",
                "description": "Callback server port",
                "default": 6195,
            },
        },
        "wecom_ai_bot": {
            "wecom_ai_bot_connection_mode": {
                "type": "string",
                "description": "Connection mode: 'long_connection' or 'webhook'",
                "default": "long_connection",
            },
            "wecom_ai_bot_name": {
                "type": "string",
                "description": "AI Bot name",
                "default": "",
            },
            "wecomaibot_ws_bot_id": {
                "type": "string",
                "description": "WebSocket Bot ID",
                "default": "",
            },
            "wecomaibot_ws_secret": {
                "type": "string",
                "description": "WebSocket Secret",
                "default": "",
            },
            "wecomaibot_token": {
                "type": "string",
                "description": "Token for callback",
                "default": "",
            },
            "wecomaibot_encoding_aes_key": {
                "type": "string",
                "description": "Encoding AES Key for message encryption",
                "default": "",
            },
            "wecomaibot_init_respond_text": {
                "type": "string",
                "description": "Initial response text",
                "default": "",
            },
            "wecomaibot_friend_message_welcome_text": {
                "type": "string",
                "description": "Welcome text for friend messages",
                "default": "",
            },
            "msg_push_webhook_url": {
                "type": "string",
                "description": "Message push webhook URL",
                "default": "",
            },
            "only_use_webhook_url_to_send": {
                "type": "bool",
                "description": "Only use webhook URL for sending messages",
                "default": False,
            },
            "wecomaibot_ws_url": {
                "type": "string",
                "description": "WebSocket URL",
                "default": "wss://openws.work.weixin.qq.com",
            },
            "wecomaibot_heartbeat_interval": {
                "type": "int",
                "description": "Heartbeat interval (seconds)",
                "default": 30,
            },
            "unified_webhook_mode": {
                "type": "bool",
                "description": "Use unified webhook mode",
                "default": True,
            },
            "webhook_uuid": {
                "type": "string",
                "description": "Webhook UUID for unified mode",
                "default": "",
            },
            "port": {
                "type": "int",
                "description": "Callback server port",
                "default": 6198,
            },
        },
        "weixin_official_account": {
            "appid": {
                "type": "string",
                "description": "WeChat Official Account AppID",
                "required": True,
            },
            "secret": {
                "type": "string",
                "description": "WeChat Official Account AppSecret",
                "required": True,
            },
            "token": {
                "type": "string",
                "description": "Token for callback verification",
                "default": "",
            },
            "encoding_aes_key": {
                "type": "string",
                "description": "Encoding AES Key for message encryption",
                "default": "",
            },
            "api_base_url": {
                "type": "string",
                "description": "WeChat API base URL",
                "default": "https://api.weixin.qq.com/cgi-bin/",
            },
            "unified_webhook_mode": {
                "type": "bool",
                "description": "Use unified webhook mode",
                "default": True,
            },
            "webhook_uuid": {
                "type": "string",
                "description": "Webhook UUID for unified mode",
                "default": "",
            },
            "callback_server_host": {
                "type": "string",
                "description": "Callback server host",
                "default": "0.0.0.0",
            },
            "port": {
                "type": "int",
                "description": "Callback server port",
                "default": 6194,
            },
            "active_send_mode": {
                "type": "bool",
                "description": "Enable active message sending mode",
                "default": False,
            },
        },
        "mattermost": {
            "mattermost_url": {
                "type": "string",
                "description": "Mattermost server URL",
                "required": True,
            },
            "mattermost_token": {
                "type": "string",
                "description": "Mattermost Bot Token",
                "required": True,
            },
            "mattermost_team_name": {
                "type": "string",
                "description": "Team name for the bot",
                "default": "",
            },
        },
        "misskey": {
            "misskey_instance_url": {
                "type": "string",
                "description": "Misskey instance URL",
                "default": "https://misskey.example",
            },
            "misskey_token": {
                "type": "string",
                "description": "Misskey API Token",
                "required": True,
            },
            "misskey_default_visibility": {
                "type": "string",
                "description": "Default note visibility: 'public', 'home', 'followers'",
                "default": "public",
            },
            "misskey_local_only": {
                "type": "bool",
                "description": "Post notes as local-only",
                "default": False,
            },
            "misskey_enable_chat": {
                "type": "bool",
                "description": "Enable chat functionality",
                "default": True,
            },
            "misskey_allow_insecure_downloads": {
                "type": "bool",
                "description": "Allow insecure HTTP downloads",
                "default": False,
            },
            "misskey_download_timeout": {
                "type": "int",
                "description": "Download timeout (seconds)",
                "default": 15,
            },
            "misskey_download_chunk_size": {
                "type": "int",
                "description": "Download chunk size (bytes)",
                "default": 65536,
            },
            "misskey_max_download_bytes": {
                "type": "int",
                "description": "Maximum download size (bytes), None for unlimited",
                "default": None,
            },
            "misskey_enable_file_upload": {
                "type": "bool",
                "description": "Enable file upload functionality",
                "default": True,
            },
            "misskey_upload_concurrency": {
                "type": "int",
                "description": "Number of concurrent uploads",
                "default": 3,
            },
            "misskey_upload_folder": {
                "type": "string",
                "description": "Upload folder name in Drive",
                "default": "",
            },
        },
        "matrix": {
            "matrix_homeserver": {
                "type": "string",
                "description": "Matrix homeserver URL",
                "required": True,
            },
            "matrix_user_id": {
                "type": "string",
                "description": "Matrix user ID (@user:server.com)",
                "required": True,
            },
            "matrix_access_token": {
                "type": "string",
                "description": "Matrix access token",
                "required": True,
            },
            "matrix_device_id": {
                "type": "string",
                "description": "Matrix device ID",
                "default": "",
            },
        },
        "qqofficial": {
            "appid": {
                "type": "string",
                "description": "QQ Official App ID",
                "required": True,
            },
            "secret": {
                "type": "string",
                "description": "QQ Official App Secret",
                "required": True,
            },
            "enable_group_c2c": {
                "type": "bool",
                "description": "Enable group C2C messages",
                "default": True,
            },
            "enable_guild_direct_message": {
                "type": "bool",
                "description": "Enable guild direct messages",
                "default": True,
            },
        },
        "qqofficial_webhook": {
            "appid": {
                "type": "string",
                "description": "QQ Official App ID",
                "required": True,
            },
            "secret": {
                "type": "string",
                "description": "QQ Official App Secret",
                "required": True,
            },
            "is_sandbox": {
                "type": "bool",
                "description": "Use sandbox environment",
                "default": False,
            },
            "unified_webhook_mode": {
                "type": "bool",
                "description": "Use unified webhook mode",
                "default": True,
            },
            "webhook_uuid": {
                "type": "string",
                "description": "Webhook UUID for unified mode",
                "default": "",
            },
            "callback_server_host": {
                "type": "string",
                "description": "Callback server host",
                "default": "0.0.0.0",
            },
            "port": {
                "type": "int",
                "description": "Callback server port",
                "default": 6196,
            },
        },
        "satori": {
            "satori_host": {
                "type": "string",
                "description": "Satori protocol host",
                "default": "localhost",
            },
            "satori_port": {
                "type": "int",
                "description": "Satori protocol port",
                "default": 8080,
            },
        },
        "vocechat": {
            "vocechat_webhook_url": {
                "type": "string",
                "description": "VoceChat webhook URL",
                "required": True,
            },
            "vocechat_api_url": {
                "type": "string",
                "description": "VoceChat API URL",
                "default": "",
            },
        },
        "webchat": {},
        "line": {
            "channel_access_token": {
                "type": "string",
                "description": "LINE Channel Access Token",
                "required": True,
            },
            "channel_secret": {
                "type": "string",
                "description": "LINE Channel Secret",
                "required": True,
            },
            "unified_webhook_mode": {
                "type": "bool",
                "description": "Use unified webhook mode",
                "default": True,
            },
            "webhook_uuid": {
                "type": "string",
                "description": "Webhook UUID for unified mode",
                "default": "",
            },
            "line_webhook_host": {
                "type": "string",
                "description": "Webhook server host",
                "default": "0.0.0.0",
            },
            "line_webhook_port": {
                "type": "int",
                "description": "Webhook server port",
                "default": 6192,
            },
        },
        "weixin_oc": {
            "weixin_oc_base_url": {
                "type": "string",
                "description": "WeChat OC base URL",
                "default": "https://ilinkai.weixin.qq.com",
            },
            "weixin_oc_bot_type": {
                "type": "string",
                "description": "Bot type identifier",
                "default": "3",
            },
            "weixin_oc_qr_poll_interval": {
                "type": "int",
                "description": "QR code polling interval (seconds)",
                "default": 3,
            },
            "weixin_oc_long_poll_timeout_ms": {
                "type": "int",
                "description": "Long poll timeout (milliseconds)",
                "default": 30000,
            },
            "weixin_oc_api_timeout_ms": {
                "type": "int",
                "description": "API timeout (milliseconds)",
                "default": 30000,
            },
            "weixin_oc_token": {
                "type": "string",
                "description": "WeChat OC token",
                "default": "",
            },
        },
    }
    return schemas.get(bot_type)
