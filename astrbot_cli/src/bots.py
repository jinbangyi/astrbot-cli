"""Bot management CLI commands for AstrBot."""

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import httpx
import tyro

from .bots_utils import (
    get_available_bots,
    get_bot_config,
    get_bot_config_schema,
    get_bot_defaults,
    set_bot_config,
    list_bot_configs,
    add_bot_config,
    update_bot_config,
    delete_bot_config,
)
from .system_utils import is_astrbot_running, get_astrbot_status
from .path_config import resolve_api_key


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
    schema: bool = False  # Show config schema for this bot type

    def run(self) -> None:
        """Execute the config command."""
        config = get_bot_config(self.id)
        if config is None:
            print(f"Error: Bot '{self.id}' not found")
            return

        bot_schema = get_bot_config_schema(config.get("type", ""))

        if self.schema:
            bot_type = config.get("type", "unknown")
            print(f"\nConfiguration Schema for '{bot_type}':")
            print("=" * 70)

            if not bot_schema:
                print(f"No schema available for bot type '{bot_type}'")
                print("\nAvailable fields (from defaults):")
                defaults = get_bot_defaults(bot_type)
                for key, value in defaults.items():
                    value_type = type(value).__name__
                    print(f"  {key}:")
                    print(f"    Type: {value_type}")
                    print(f"    Default: {value if value else '(empty)'}")
                return

            # Required fields first
            required_fields = {k: v for k, v in bot_schema.items() if v.get("required")}
            optional_fields = {k: v for k, v in bot_schema.items() if not v.get("required")}

            if required_fields:
                print("\nRequired Fields:")
                print("-" * 70)
                for key, info in required_fields.items():
                    self._print_schema_field(key, info)

            if optional_fields:
                print("\nOptional Fields:")
                print("-" * 70)
                for key, info in optional_fields.items():
                    self._print_schema_field(key, info)

            return

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

            # Validate key against bot defaults (valid fields for this bot type)
            bot_type = config.get("type", "")
            valid_fields = get_bot_defaults(bot_type) or {}
            # Also allow id, type, enable
            valid_fields["id"] = None
            valid_fields["type"] = None
            valid_fields["enable"] = None

            # Check if top-level key is valid
            top_key = keys[0]
            if top_key not in valid_fields:
                print(f"Error: '{top_key}' is not a valid field for bot type '{bot_type}'")
                print(f"Valid fields: {', '.join(sorted(valid_fields.keys()))}")
                return

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

    def _print_schema_field(self, key: str, info: dict) -> None:
        """Print a single schema field with formatting."""
        field_type = info.get("type", "any")
        description = info.get("description", "")
        default = info.get("default")
        required = info.get("required", False)

        print(f"\n  {key}:")
        print(f"    Type: {field_type}")
        if description:
            print(f"    Description: {description}")
        if required:
            print(f"    Required: Yes")
        else:
            print(f"    Required: No")
            if default is not None:
                print(f"    Default: {default}")


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


def _upload_file_via_api(file_path: str, api_key: str | None = None) -> dict:
    """Upload a file to AstrBot and get an attachment_id.

    Args:
        file_path: Path to the file to upload
        api_key: Optional API key for authentication

    Returns:
        Result dict with attachment_id on success or error on failure
    """
    from pathlib import Path

    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    port = os.environ.get("ASTRBOT_PORT", "6185")
    base_url = f"http://localhost:{port}"
    url = f"{base_url}/api/v1/file"

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path_obj.name, f)}
            with httpx.Client(timeout=60) as client:
                resp = client.post(url, files=files, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "ok":
                        return {"success": True, "attachment_id": data.get("data", {}).get("attachment_id")}
                    return {"success": False, "error": data.get("message", "Unknown error")}
                elif resp.status_code == 401:
                    return {"success": False, "error": "Authentication failed. Check your API key."}
                else:
                    return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except httpx.ConnectError:
        return {"success": False, "error": f"Connection failed. Is AstrBot running on port {port}?"}
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timed out"}
    except Exception as e:
        return {"success": False, "error": f"Upload failed: {e}"}


def _send_message_via_api(
    bot_id: str,
    umo: str,
    message_parts: list[dict],
    api_key: str | None = None
) -> dict:
    """Send a message through AstrBot OpenAPI.

    Args:
        bot_id: Bot instance ID
        umo: Unified message origin (target). Format: platform_id:MessageType:session_id
        message_parts: List of message part dicts, each with "type" and content fields
        api_key: Optional API key for authentication

    Returns:
        Result dict with success status
    """
    # Determine API base URL
    status = get_astrbot_status()
    if not status.get("running"):
        return {"success": False, "error": "AstrBot is not running. Start it first with 'astrbot-cli system start'"}

    # Default port is 6185 or from environment
    port = os.environ.get("ASTRBOT_PORT", "6185")
    base_url = f"http://localhost:{port}"

    url = f"{base_url}/api/v1/im/message"

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Message payload format: list of message parts
    # Each part is an object with "type" and content fields
    # For plain text: [{"type": "plain", "text": "message content"}]
    # For image: [{"type": "image", "attachment_id": "..."}]
    # For video: [{"type": "video", "attachment_id": "..."}]
    # For file: [{"type": "file", "attachment_id": "..."}]
    payload = {
        "umo": umo,
        "message": message_parts
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "ok":
                    return {"success": True}
                return {"success": False, "error": data.get("message", "Unknown error")}
            elif resp.status_code == 401:
                return {"success": False, "error": "Authentication failed. Check your API key."}
            elif resp.status_code == 404:
                return {"success": False, "error": f"Bot '{bot_id}' not found or not running"}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except httpx.ConnectError:
        return {"success": False, "error": f"Connection failed. Is AstrBot running on port {port}?"}
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timed out"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {e}"}


@dataclass
class Send:
    """Send a message through a bot.

    Send a message to a channel/group/user via AstrBot's OpenAPI.
    Supports text, images, videos, and files.

    API key priority:
    1. --api-key option (if provided)
    2. Default API key from ~/.config/astrbot-cli/config.yaml

    Examples:
        Send text: astrbot-cli bots send mybot "Hello" --umo "telegram:FriendMessage:123456"
        Send image: astrbot-cli bots send mybot "" --umo "..." --image /path/to/image.png
        Send multiple: astrbot-cli bots send mybot "Check this" --umo "..." --image photo.jpg --video clip.mp4
        With API key: astrbot-cli bots send mybot "Hello" --umo "..." --api-key YOUR_KEY
    """

    bot_id: Annotated[str, tyro.conf.Positional]  # Bot instance ID
    message: Annotated[str, tyro.conf.Positional]  # Text message content (can be empty if sending media)
    umo: str | None = None  # Unified Message Origin (target). Format: platform_id:MessageType:session_id
    api_key: str | None = None  # API key for authentication (optional if no auth required)
    image: str | None = None  # Path to image file to send
    video: str | None = None  # Path to video file to send
    file: str | None = None  # Path to file to send

    def run(self) -> None:
        """Execute the send command."""
        from pathlib import Path

        # Resolve API key (use provided or fallback to config)
        api_key = resolve_api_key(self.api_key)

        # Check if bot exists
        config = get_bot_config(self.bot_id)
        if config is None:
            print(f"Error: Bot '{self.bot_id}' not found")
            return

        # Check if AstrBot is running
        if not is_astrbot_running():
            print("Error: AstrBot is not running. Start it first with 'astrbot-cli system start'")
            return

        # Validate UMO
        if not self.umo:
            print("Error: --umo is required.")
            print("Format: platform_id:MessageType:session_id")
            print("Example: discord:GroupMessage:1114061876221988936")
            print("         telegram:GroupMessage:-1001234567890")
            print("         telegram:FriendMessage:123456")
            return

        # Validate that at least one content type is provided
        has_text = bool(self.message and self.message.strip())
        has_image = bool(self.image)
        has_video = bool(self.video)
        has_file = bool(self.file)

        if not (has_text or has_image or has_video or has_file):
            print("Error: No message content provided.")
            print("Provide either a text message, --image, --video, or --file option.")
            return

        # Build message parts
        message_parts = []

        # Add text part first
        if has_text:
            message_parts.append({"type": "plain", "text": self.message})

        # Process media files
        media_files = []
        if has_image:
            media_files.append(("image", self.image))
        if has_video:
            media_files.append(("video", self.video))
        if has_file:
            media_files.append(("file", self.file))

        # Upload and add media parts
        for media_type, media_path in media_files:
            path = Path(media_path)
            if not path.exists():
                print(f"Error: {media_type} file not found: {media_path}")
                return

            print(f"Uploading {media_type}: {path.name}...")
            upload_result = _upload_file_via_api(media_path, api_key)

            if not upload_result.get("success"):
                print(f"Error: Failed to upload {media_type}: {upload_result.get('error', 'Unknown error')}")
                return

            attachment_id = upload_result.get("attachment_id")
            if not attachment_id:
                print(f"Error: No attachment_id returned for {media_type}")
                return

            part = {"type": media_type, "attachment_id": attachment_id}
            if media_type == "file":
                part["filename"] = path.name
            message_parts.append(part)

        # Send message
        result = _send_message_via_api(self.bot_id, self.umo, message_parts, api_key)

        if result.get("success"):
            content_summary = []
            if has_text:
                content_summary.append("text")
            if has_image:
                content_summary.append("image")
            if has_video:
                content_summary.append("video")
            if has_file:
                content_summary.append("file")
            print(f"Message ({', '.join(content_summary)}) sent successfully via bot '{self.bot_id}'")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")


def _get_messages_via_api(
    session_id: str,
    platform_id: str = "webchat",
    page: int = 1,
    page_size: int = 50,
    api_key: str | None = None
) -> dict:
    """Get message history from AstrBot API.

    Args:
        session_id: Session ID to get messages for
        platform_id: Platform ID (default: webchat)
        page: Page number (default: 1)
        page_size: Number of messages per page (default: 50)
        api_key: Optional API key for authentication

    Returns:
        Result dict with messages on success or error on failure
    """
    status = get_astrbot_status()
    if not status.get("running"):
        return {"success": False, "error": "AstrBot is not running. Start it first with 'astrbot-cli system start'"}

    port = os.environ.get("ASTRBOT_PORT", "6185")
    base_url = f"http://localhost:{port}"

    # Use the chat/get_session endpoint to get message history
    url = f"{base_url}/api/chat/get_session"
    params = {"session_id": session_id}

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "ok":
                    return {"success": True, "data": data.get("data", {})}
                return {"success": False, "error": data.get("message", "Unknown error")}
            elif resp.status_code == 401:
                return {"success": False, "error": "Authentication failed. Check your API key."}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except httpx.ConnectError:
        return {"success": False, "error": f"Connection failed. Is AstrBot running on port {port}?"}
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timed out"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {e}"}


def _get_sessions_via_api(
    username: str = "guest",
    platform_id: str | None = None,
    api_key: str | None = None
) -> dict:
    """Get chat sessions from AstrBot API.

    Args:
        username: Username to get sessions for
        platform_id: Optional platform ID filter
        api_key: Optional API key for authentication

    Returns:
        Result dict with sessions on success or error on failure
    """
    status = get_astrbot_status()
    if not status.get("running"):
        return {"success": False, "error": "AstrBot is not running. Start it first with 'astrbot-cli system start'"}

    port = os.environ.get("ASTRBOT_PORT", "6185")
    base_url = f"http://localhost:{port}"

    url = f"{base_url}/api/v1/chat/sessions"
    params = {"username": username}
    if platform_id:
        params["platform_id"] = platform_id

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "ok":
                    return {"success": True, "data": data.get("data", [])}
                return {"success": False, "error": data.get("message", "Unknown error")}
            elif resp.status_code == 401:
                return {"success": False, "error": "Authentication failed. Check your API key."}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except httpx.ConnectError:
        return {"success": False, "error": f"Connection failed. Is AstrBot running on port {port}?"}
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timed out"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {e}"}


def _format_message_content(content: dict) -> str:
    """Format message content for display.

    Args:
        content: Message content dict with 'type' and 'message' fields

    Returns:
        Formatted string representation
    """
    msg_type = content.get("type", "unknown")
    message_parts = content.get("message", [])

    if not message_parts:
        return ""

    text_parts = []
    for part in message_parts:
        if isinstance(part, dict):
            part_type = part.get("type", "")
            if part_type == "plain":
                text_parts.append(part.get("text", ""))
            elif part_type == "image":
                text_parts.append("[IMAGE]")
            elif part_type == "video":
                text_parts.append("[VIDEO]")
            elif part_type == "file":
                text_parts.append(f"[FILE: {part.get('filename', 'unknown')}]")
            elif part_type == "record":
                text_parts.append("[AUDIO]")
        elif isinstance(part, str):
            text_parts.append(part)

    return " ".join(text_parts)


@dataclass
class Messages:
    """Get recent messages from a session.

    Retrieve message history from AstrBot's internal storage.
    Note: This returns messages that were received/sent through the bot,
    not directly from external platforms like Discord/Telegram.

    For direct platform message fetching, the bot needs read permissions
    and AstrBot would need to support channel history API.

    API key priority:
    1. --api-key option (if provided)
    2. Default API key from ~/.config/astrbot-cli/config.yaml

    Use --list to see available sessions first.

    Examples:
        List sessions: astrbot-cli bots messages --list
        Get messages: astrbot-cli bots messages <session_id>
        With limit:   astrbot-cli bots messages <session_id> --limit 20
        With API key: astrbot-cli bots messages <session_id> --api-key YOUR_KEY
    """

    session_id: Annotated[str | None, tyro.conf.Positional] = None  # Session ID to get messages from
    list: bool = False  # List available sessions
    limit: int = 20  # Maximum number of messages to display
    username: str = "guest"  # Username for session lookup
    platform_id: str | None = None  # Filter by platform ID
    api_key: str | None = None  # API key for authentication
    json_output: bool = False  # Output in JSON format

    def run(self) -> None:
        """Execute the messages command."""
        # Resolve API key (use provided or fallback to config)
        api_key = resolve_api_key(self.api_key)

        # Check if AstrBot is running
        if not is_astrbot_running():
            print("Error: AstrBot is not running. Start it first with 'astrbot-cli system start'")
            return

        # List sessions mode
        if self.list:
            result = _get_sessions_via_api(
                username=self.username,
                platform_id=self.platform_id,
                api_key=api_key
            )

            if not result.get("success"):
                print(f"Error: {result.get('error', 'Unknown error')}")
                return

            data = result.get("data", {})
            # Handle both dict response with 'sessions' key and direct list
            if isinstance(data, dict):
                sessions = data.get("sessions", [])
            elif isinstance(data, list):
                sessions = data
            else:
                sessions = []

            if not sessions:
                print("No sessions found.")
                return

            if self.json_output:
                print(json.dumps(sessions, indent=2, ensure_ascii=False))
            else:
                print(f"\nSessions for '{self.username}':")
                print("-" * 100)
                print(f"{'Session ID':<40} {'Platform':<15} {'Display Name':<30} {'Updated':<20}")
                print("-" * 100)
                for session in sessions:
                    if not isinstance(session, dict):
                        continue
                    sid = session.get("session_id", "")[:38]
                    platform = session.get("platform_id", "")
                    display_name = session.get("display_name", "")[:28] or "-"
                    updated = session.get("updated_at", "")[:19]
                    print(f"{sid:<40} {platform:<15} {display_name:<30} {updated:<20}")
            return

        # Get messages mode
        if not self.session_id:
            print("Error: session_id is required.")
            print("Use --list to see available sessions first.")
            print("Usage: astrbot-cli bots messages <session_id>")
            return

        result = _get_messages_via_api(
            session_id=self.session_id,
            platform_id=self.platform_id or "webchat",
            api_key=api_key
        )

        if not result.get("success"):
            print(f"Error: {result.get('error', 'Unknown error')}")
            return

        data = result.get("data", {})
        history = data.get("history", [])
        is_running = data.get("is_running", False)

        if not history:
            print(f"No messages found for session '{self.session_id}'")
            return

        # Limit the number of messages
        if self.limit > 0:
            history = history[-self.limit:]

        if self.json_output:
            print(json.dumps(history, indent=2, ensure_ascii=False))
        else:
            print(f"\nMessages for session '{self.session_id}'")
            if is_running:
                print("(Session is currently running)")
            print("=" * 80)

            for msg in history:
                content = msg.get("content", {})
                msg_type = content.get("type", "unknown")
                sender_id = msg.get("sender_id", "unknown")
                sender_name = msg.get("sender_name", sender_id)
                created_at = msg.get("created_at", "")

                # Format timestamp
                if created_at:
                    try:
                        # Parse ISO format and display in local format
                        ts = created_at[:19].replace("T", " ")
                    except Exception:
                        ts = created_at[:19]
                else:
                    ts = "unknown"

                # Format message content
                text = _format_message_content(content)
                if len(text) > 200:
                    text = text[:197] + "..."

                # Display message
                type_indicator = "🤖" if msg_type == "bot" else "👤"
                print(f"\n[{ts}] {type_indicator} {sender_name}")
                print(f"  {text}")

            print("\n" + "=" * 80)
            print(f"Total: {len(history)} message(s)")


def _fetch_discord_messages(
    token: str,
    channel_id: str,
    limit: int = 50,
    before: str | None = None,
    after: str | None = None,
) -> dict:
    """Fetch messages directly from Discord API.

    Args:
        token: Discord bot token
        channel_id: Discord channel ID to fetch messages from
        limit: Number of messages to fetch (max 100)
        before: Get messages before this message ID
        after: Get messages after this message ID

    Returns:
        Result dict with messages on success or error on failure
    """
    if limit > 100:
        limit = 100

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    params = {"limit": limit}
    if before:
        params["before"] = before
    if after:
        params["after"] = after

    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                messages = resp.json()
                return {"success": True, "messages": messages}
            elif resp.status_code == 401:
                return {"success": False, "error": "Invalid bot token"}
            elif resp.status_code == 403:
                return {"success": False, "error": "Bot lacks permission to read this channel"}
            elif resp.status_code == 404:
                return {"success": False, "error": "Channel not found"}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except httpx.ConnectError:
        return {"success": False, "error": "Connection failed to Discord API"}
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timed out"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {e}"}


def _fetch_telegram_messages(
    token: str,
    chat_id: str,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Fetch messages directly from Telegram Bot API.

    Args:
        token: Telegram bot token
        chat_id: Telegram chat/channel/group ID (can be negative for groups)
        limit: Number of messages to fetch
        offset: Offset for pagination

    Returns:
        Result dict with messages on success or error on failure
    """
    url = f"https://api.telegram.org/bot{token}/getChatHistory"
    # Note: getChatHistory may not be available on all bots
    # Alternative: use getChat to get info, then rely on updates

    # Try getChat first to validate
    chat_url = f"https://api.telegram.org/bot{token}/getChat"
    params = {"chat_id": chat_id}

    headers = {}

    try:
        with httpx.Client(timeout=30) as client:
            # First verify chat access
            chat_resp = client.get(chat_url, params=params)
            if chat_resp.status_code != 200:
                data = chat_resp.json()
                if data.get("error_code") == 401:
                    return {"success": False, "error": "Invalid bot token"}
                elif data.get("error_code") == 400:
                    return {"success": False, "error": f"Chat not accessible: {data.get('description', 'Unknown error')}"}
                return {"success": False, "error": f"HTTP {chat_resp.status_code}: {chat_resp.text}"}

            # Telegram Bot API doesn't have a direct message history endpoint
            # We need to use getChatAdministrators, getChatMember, etc.
            # For message history, we'd need MTProto (userbot) not Bot API
            return {
                "success": False,
                "error": "Telegram Bot API does not support message history. Use AstrBot's session history instead, or use a userbot.",
                "chat_info": chat_resp.json().get("result", {})
            }
    except httpx.ConnectError:
        return {"success": False, "error": "Connection failed to Telegram API"}
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timed out"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {e}"}


def _format_discord_message(msg: dict) -> str:
    """Format a Discord message for display.

    Args:
        msg: Discord message object from API

    Returns:
        Formatted string representation
    """
    author = msg.get("author", {})
    username = author.get("username", "unknown")
    content = msg.get("content", "")
    timestamp = msg.get("timestamp", "")[:19].replace("T", " ") if msg.get("timestamp") else "unknown"

    # Handle attachments
    attachments = msg.get("attachments", [])
    attachment_text = ""
    if attachments:
        attachment_text = " [ATTACHMENTS: " + ", ".join(a.get("filename", "file") for a in attachments) + "]"

    # Handle embeds
    embeds = msg.get("embeds", [])
    embed_text = ""
    if embeds:
        embed_text = f" [EMBEDS: {len(embeds)}]"

    # Handle stickers
    stickers = msg.get("sticker_items", [])
    sticker_text = ""
    if stickers:
        sticker_text = " [STICKER]"

    full_content = content + attachment_text + embed_text + sticker_text
    if len(full_content) > 200:
        full_content = full_content[:197] + "..."

    return f"[{timestamp}] {username}: {full_content}"


@dataclass
class FetchMessages:
    """Fetch messages directly from external platforms.

    This command bypasses AstrBot's internal storage and fetches messages
    directly from platform APIs (Discord, Telegram).

    Requirements:
    - Discord: Bot token with 'Read Messages' permission in the channel
    - Telegram: Bot API doesn't support message history (use sessions instead)

    Examples:
        Discord:  astrbot-cli bots fetch discord --token BOT_TOKEN --channel 123456789
        With limit: astrbot-cli bots fetch discord --token BOT_TOKEN --channel 123456789 --limit 100
        JSON:    astrbot-cli bots fetch discord --token BOT_TOKEN --channel 123456789 --json-output
    """

    platform: Annotated[str, tyro.conf.Positional] = "discord"  # Platform name (discord, telegram)
    channel: str | None = None  # Channel/Chat ID to fetch messages from
    token: str | None = None  # Bot token (reads from bot config if not provided)
    bot_id: str | None = None  # Bot instance ID (to read token from config)
    limit: int = 50  # Number of messages to fetch
    before: str | None = None  # Fetch messages before this message ID (Discord only)
    after: str | None = None  # Fetch messages after this message ID (Discord only)
    json_output: bool = False  # Output in JSON format

    def run(self) -> None:
        """Execute the fetch command."""
        # Validate platform
        platform = self.platform.lower()
        if platform not in ("discord", "telegram"):
            print(f"Error: Unsupported platform '{self.platform}'")
            print("Supported platforms: discord, telegram")
            return

        # Get token from bot config if bot_id is provided
        token = self.token
        if not token and self.bot_id:
            config = get_bot_config(self.bot_id)
            if config:
                # Check platform-specific token field names
                bot_type = config.get("type", "").lower()
                token_fields = {
                    "discord": ["discord_token", "token"],
                    "telegram": ["token"],
                    "slack": ["bot_token", "token"],
                    "kook": ["kook_bot_token", "token"],
                    "lark": ["lark_app_secret", "token"],
                    "dingtalk": ["dingtalk_client_secret", "secret"],
                    "wecom": ["secret", "token"],
                    "mattermost": ["mattermost_token", "token"],
                    "misskey": ["misskey_token", "token"],
                    "matrix": ["matrix_access_token", "access_token", "token"],
                    "line": ["channel_access_token", "token"],
                }
                # Try platform-specific fields first, then generic ones
                fields_to_try = token_fields.get(bot_type, []) + ["token", "access_token", "api_token", "bot_token"]
                for field in fields_to_try:
                    if config.get(field):
                        token = config.get(field)
                        break
                if not token:
                    print(f"Error: No token found in bot '{self.bot_id}' config")
                    print(f"  Bot type: {bot_type}")
                    print(f"  Checked fields: {', '.join(fields_to_try)}")
                    return
            else:
                print(f"Error: Bot '{self.bot_id}' not found")
                return

        if not token:
            print("Error: Bot token is required.")
            print("Provide --token or --bot-id to read from config.")
            return

        # Get channel/chat ID
        channel_id = self.channel
        if not channel_id:
            print("Error: --channel is required.")
            print("For Discord: Use the channel ID (enable Developer Mode in Discord to copy)")
            print("For Telegram: Use the chat/group ID")
            return

        # Fetch messages based on platform
        if platform == "discord":
            result = _fetch_discord_messages(
                token=token,
                channel_id=channel_id,
                limit=self.limit,
                before=self.before,
                after=self.after,
            )
        elif platform == "telegram":
            result = _fetch_telegram_messages(
                token=token,
                chat_id=channel_id,
                limit=self.limit,
            )
        else:
            print(f"Error: Platform '{platform}' not implemented")
            return

        # Handle result
        if not result.get("success"):
            print(f"Error: {result.get('error', 'Unknown error')}")
            if result.get("chat_info"):
                print(f"\nChat info: {json.dumps(result.get('chat_info'), indent=2)}")
            return

        messages = result.get("messages", [])

        if not messages:
            print("No messages found.")
            return

        if self.json_output:
            print(json.dumps(messages, indent=2, ensure_ascii=False))
        else:
            print(f"\nMessages from {platform} channel '{channel_id}':")
            print("=" * 80)

            if platform == "discord":
                for msg in messages:
                    print(_format_discord_message(msg))
            elif platform == "telegram":
                # Telegram doesn't support message history via Bot API
                print("Telegram Bot API does not support message history.")
                print("Use AstrBot's session storage instead: astrbot-cli bots messages --list")

            print("=" * 80)
            print(f"Total: {len(messages)} message(s)")
