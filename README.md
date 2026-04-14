# AstrBot CLI

A command-line tool for managing [AstrBot](https://github.com/AstrBotDevs/AstrBot) – an open‑source, agentic chatbot infrastructure that integrates multiple IM platforms, LLMs, plugins, and AI capabilities.

The CLI provides two complementary execution models:
- **Stateful workflows** – powered by [dagu](https://github.com/dagu-dev/dagu), enabling reliable, DAG‑based automation of complex tasks.
- **Stateless grouped actions** – direct, immediate operations for day‑to‑day management.

## Features

- **Quick Start** – One-command installation and startup
- **Bot Management** – Configure platform connections (Telegram, Discord, QQ, Slack, etc.)
- **Provider Management** – Set up LLM providers (OpenAI, DeepSeek, Ollama, Gemini, etc.)
- **Profile System** – Link providers, personas, and plugins together
- **Plugin Management** – Install, configure, and manage plugins
- **Persona Management** – Create custom bot behaviors and response styles
- **Workflow Integration** – Stateful automation via dagu
- **System Management** – Start, stop, restart, and monitor AstrBot service

## Installation

```bash
# Clone the repository
git clone https://github.com/MinaraAgent/astrbot-cli.git
cd astrbot-cli

# Install dependencies with uv
uv sync
```

## Quick Start

```bash
# Install and start AstrBot at default location
astrbot-cli system quick-start

# Or specify a custom path
astrbot-cli system quick-start --path ~/my-astrbot

# Force reinstall
astrbot-cli system quick-start --force
```

## Command Reference

### System Commands

Manage the AstrBot service itself using PM2.

| Command | Description |
|---------|-------------|
| `astrbot-cli system init` | Initialize AstrBot environment |
| `astrbot-cli system upgrade` | Upgrade AstrBot installation |
| `astrbot-cli system start` | Start AstrBot service |
| `astrbot-cli system stop` | Stop AstrBot service |
| `astrbot-cli system restart` | Restart AstrBot service |
| `astrbot-cli system status` | Show service status (PID, uptime, memory, CPU) |
| `astrbot-cli system logs [lines]` | View service logs (`--follow` for streaming) |
| `astrbot-cli system info` | Show version, path, Python environment |
| `astrbot-cli system version` | Alias for `info` |
| `astrbot-cli system path` | Show current AstrBot installation path |
| `astrbot-cli system path --set <path>` | Set AstrBot path manually |
| `astrbot-cli system path --set <path> --force` | Force set path (even if AstrBot not installed there yet) |
| `astrbot-cli system quick-start` | Quick start AstrBot (uses saved/default path) |
| `astrbot-cli system quick-start --path <path>` | Start at specific path |
| `astrbot-cli system quick-start --force` | Force reinstall |

### Bot Commands

Manage platform connections (each "bot" is a platform instance).

| Command | Description |
|---------|-------------|
| `astrbot-cli bots list` | List configured bots |
| `astrbot-cli bots list --available` | List available bot types |
| `astrbot-cli bots add <type>` | Add a new bot |
| `astrbot-cli bots remove <id>` | Remove a bot |
| `astrbot-cli bots enable <id>` | Enable a bot |
| `astrbot-cli bots disable <id>` | Disable a bot |
| `astrbot-cli bots config <id>` | Configure a bot |
| `astrbot-cli bots info <id>` | Show bot info |
| `astrbot-cli bots send <bot_id> <message> --umo <target>` | Send a message through a bot (supports `--image`, `--video`, `--file` options) |
| `astrbot-cli bots messages --list` | List available chat sessions |
| `astrbot-cli bots messages <session_id>` | Get recent messages from a session |
| `astrbot-cli bots fetch discord --channel <id>` | Fetch messages directly from Discord API |

**Getting Messages:**

The `messages` command allows you to retrieve message history from chat sessions.

```bash
# List available chat sessions
astrbot-cli bots messages --list --api-key "your-api-key"

# Get messages from a specific session
astrbot-cli bots messages <session_id> --api-key "your-api-key"

# Limit the number of messages
astrbot-cli bots messages <session_id> --limit 50 --api-key "your-api-key"

# Output in JSON format
astrbot-cli bots messages <session_id> --json-output --api-key "your-api-key"

# Filter by platform
astrbot-cli bots messages --list --platform-id telegram --api-key "your-api-key"
```

**Fetching Messages from External Platforms:**

The `fetch` command retrieves messages directly from platform APIs, bypassing AstrBot's internal storage.

```bash
# Fetch from Discord channel using bot token directly
astrbot-cli bots fetch discord --channel 123456789012345678 --token "BOT_TOKEN"

# Fetch using bot config (reads token from saved config)
astrbot-cli bots fetch discord --channel 123456789012345678 --bot-id my-discord-bot

# Limit messages and output JSON
astrbot-cli bots fetch discord --channel 123456789012345678 --bot-id my-discord-bot --limit 100 --json-output

# Fetch messages before/after a specific message ID (Discord pagination)
astrbot-cli bots fetch discord --channel 123456789012345678 --bot-id my-discord-bot --after 123456789012345677
```

**Discord Requirements:**
- Bot token with 'Read Messages' and 'Read Message History' permissions
- Enable Developer Mode in Discord to copy channel IDs

**Telegram Limitations:**
- Telegram Bot API does NOT support message history
- Use AstrBot's session storage instead: `astrbot-cli bots messages --list`
- For direct history, you would need a MTProto userbot (not supported by CLI)

**Sending Messages:**

The `send` command allows you to send messages through a configured bot to channels, groups, or users. It supports text, images, videos, and files.

```bash
# Send text to a Discord channel
astrbot-cli bots send discord "Hello World!" --umo "discord:GroupMessage:1114061876221988936" --api-key "your-api-key"

# Send to a Telegram group
astrbot-cli bots send telegram "Hello World!" --umo "telegram:GroupMessage:-1001234567890" --api-key "your-api-key"

# Send to a Telegram user (private message)
astrbot-cli bots send telegram "Hello!" --umo "telegram:FriendMessage:123456" --api-key "your-api-key"

# Send an image
astrbot-cli bots send telegram "" --umo "telegram:FriendMessage:123456" --image /path/to/image.png --api-key "your-api-key"

# Send a video
astrbot-cli bots send telegram "Check out this video!" --umo "telegram:FriendMessage:123456" --video /path/to/video.mp4 --api-key "your-api-key"

# Send a file
astrbot-cli bots send telegram "Here's the document" --umo "telegram:FriendMessage:123456" --file /path/to/document.pdf --api-key "your-api-key"

# Send multiple media types together
astrbot-cli bots send telegram "See attached files" --umo "telegram:GroupMessage:-1001234567890" --image photo.jpg --video clip.mp4 --file report.pdf --api-key "your-api-key"
```

**UMO (Unified Message Origin) Format:**

The `--umo` parameter specifies the target and follows this format:
```
platform_id:MessageType:session_id
```

| Part | Description | Example |
|------|-------------|---------|
| `platform_id` | Bot instance ID (from bots list) | `discord`, `telegram` |
| `MessageType` | Message type | `GroupMessage`, `FriendMessage` |
| `session_id` | Channel/Group ID or User ID | `1114061876221988936`, `-1001234567890`, `123456` |

**Getting the API Key:**

1. Open AstrBot dashboard at `http://localhost:6185`
2. Go to Settings → API Keys
3. Create or copy an existing API key

**Available bot types:**

| Type | Description |
|------|-------------|
| `aiocqhttp` | QQ adapter via OneBot (go-cqhttp, Lagrange, etc.) |
| `telegram` | Telegram Bot API |
| `discord` | Discord Bot |
| `slack` | Slack Bot |
| `kook` | KOOK (开黑啦) Bot |
| `lark` | Lark/Feishu Bot |
| `dingtalk` | DingTalk Bot |
| `wecom` | WeChat Work (企业微信) Bot |
| `wecom_ai_bot` | WeChat Work AI Bot |
| `weixin_official_account` | WeChat Official Account (公众号) |
| `weixin_oc` | WeChat Official Account (旧版) |
| `mattermost` | Mattermost Bot |
| `misskey` | Misskey Bot |
| `matrix` | Matrix Bot |
| `qqofficial` | QQ Official API |
| `qqofficial_webhook` | QQ Official API (Webhook mode) |
| `satori` | Satori Protocol |
| `vocechat` | VoceChat Bot |
| `webchat` | Web Chat (built-in) |
| `line` | LINE Bot |

### Provider Commands

Manage LLM / model service providers.

| Command | Description |
|---------|-------------|
| `astrbot-cli providers list` | List configured providers |
| `astrbot-cli providers list --available` | List available provider types |
| `astrbot-cli providers add <type>` | Add a new provider |
| `astrbot-cli providers remove <id>` | Remove a provider |
| `astrbot-cli providers enable <id>` | Enable a provider |
| `astrbot-cli providers disable <id>` | Disable a provider |
| `astrbot-cli providers config <id>` | Configure a provider |
| `astrbot-cli providers info <id>` | Show provider info |

**Available provider types:**

| Type | Description |
|------|-------------|
| `openai` | OpenAI API (GPT-4, GPT-3.5, etc.) |
| `anthropic` | Anthropic Claude API |
| `deepseek` | DeepSeek API |
| `gemini` | Google Gemini API |
| `zhipu` | Zhipu AI (智谱) |
| `ollama` | Ollama (local models) |
| `groq` | Groq API |
| `xai` | xAI Grok API |
| `openrouter` | OpenRouter API |
| `dashscope` | Alibaba DashScope (通义千问) |
| `moonshot` | Moonshot AI (Kimi) |
| `yi` | 01.AI (零一万物) |
| `baichuan` | Baichuan (百川) |
| `minimax` | MiniMax |
| `siliconflow` | SiliconFlow |

### Profile Commands

Manage configuration profiles that link providers, personas, and plugins.

| Command | Description |
|---------|-------------|
| `astrbot-cli profiles list` | List all profiles |
| `astrbot-cli profiles create <name>` | Create a new profile |
| `astrbot-cli profiles delete <id>` | Delete a profile |
| `astrbot-cli profiles show` | Show active profile details |
| `astrbot-cli profiles show --id <id>` | Show specific profile details |
| `astrbot-cli profiles set <id> --provider X` | Set profile provider |
| `astrbot-cli profiles set <id> --persona X` | Set profile persona |
| `astrbot-cli profiles set <id> --plugins X,Y` | Set profile plugins |
| `astrbot-cli profiles use <id>` | Set active profile |

### Persona Commands

Manage persona definitions that shape bot behavior.

| Command | Description |
|---------|-------------|
| `astrbot-cli personas list` | List all personas |
| `astrbot-cli personas create <id> <prompt>` | Create a persona |
| `astrbot-cli personas edit <id> --prompt X` | Edit persona prompt |
| `astrbot-cli personas delete <id>` | Delete a persona |
| `astrbot-cli personas show <id>` | Show persona details |

### Plugin Commands

Manage AstrBot plugins.

| Command | Description |
|---------|-------------|
| `astrbot-cli plugins list` | List installed plugins |
| `astrbot-cli plugins list --all` | List all available plugins |
| `astrbot-cli plugins install --name <name>` | Install a plugin (name, URL, or local path) |
| `astrbot-cli plugins uninstall --name <name>` | Uninstall a plugin |
| `astrbot-cli plugins update --name <name>` | Update a specific plugin |
| `astrbot-cli plugins update` | Update all plugins |
| `astrbot-cli plugins search --query <query>` | Search for plugins |
| `astrbot-cli plugins config --name <name>` | Configure a plugin |
| `astrbot-cli plugins info --name <name>` | Show plugin info |

### Config Commands

Manage global configuration settings.

| Command | Description |
|---------|-------------|
| `astrbot-cli config show` | Show current settings |
| `astrbot-cli config show --defaults` | Show default settings |
| `astrbot-cli config get <key>` | Get a setting value |
| `astrbot-cli config set <key> <value>` | Set a setting value |
| `astrbot-cli config edit` | Edit settings in editor |
| `astrbot-cli config reset --confirm` | Reset to defaults |
| `astrbot-cli config schema` | Show settings schema |

### Workflow Commands

Manage stateful workflows via dagu integration.

| Command | Description |
|---------|-------------|
| `astrbot-cli workflows list` | List all workflows |
| `astrbot-cli workflows start <name>` | Start a workflow |
| `astrbot-cli workflows stop <name>` | Stop a workflow |
| `astrbot-cli workflows status <name>` | Show workflow status |
| `astrbot-cli workflows logs <name>` | Show workflow logs |
| `astrbot-cli workflows create <name>` | Create a new workflow |

**Built-in workflows:**

| Workflow | Description |
|----------|-------------|
| `plugin-debug` | Debug workflow for AstrBot plugins - sets up environment, installs plugin, configures optional settings |

**Plugin Debug Workflow Usage:**

```bash
# Basic usage
astrbot-cli workflows start plugin-debug --params PLUGIN_NAME=my-plugin

# With all optional parameters
astrbot-cli workflows start plugin-debug --params PLUGIN_NAME=my-plugin PLUGIN_REPO=https://github.com/user/repo PLUGIN_CONFIG='{"key": "value"}' BOT_TYPE=telegram BOT_CONFIG='{"token": "xxx"}' PERSONA_ID=default PERSONA_PROMPT='You are a helpful assistant' PROFILE_PROVIDER=openai
```

## Configuration Files

| File | Purpose |
|------|---------|
| `data/cmd_config.json` | Bots, providers, global config |
| `data/profiles.json` | Profile definitions |
| `data/data_v4.db` | SQLite database (personas) |
| `data/workflows/` | Workflow YAML files |
| `~/.astrbot-cli/config.json` | CLI settings (AstrBot path) |

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) – Python package manager

## Development

```bash
# Run CLI in development
uv run astrbot-cli --help

# Run CLI with specific command
uv run astrbot-cli system info
```

## Examples

```bash
# Start AstrBot at default location
astrbot-cli system quick-start

# Start AstrBot at custom location
astrbot-cli system quick-start --path ~/my-astrbot

# Show where AstrBot is installed
astrbot-cli system path

# Add Telegram bot
astrbot-cli bots add telegram

# Add OpenAI provider
astrbot-cli providers add openai

# Create a new profile
astrbot-cli profiles create my-profile

# Create a persona
astrbot-cli personas create friendly "You are a friendly and helpful assistant."

# Show configuration
astrbot-cli config show

# List all workflows
astrbot-cli workflows list

# Start the plugin debug workflow
astrbot-cli workflows start plugin-debug --params PLUGIN_NAME=astrbot_plugin_example
```

## License

MIT License
