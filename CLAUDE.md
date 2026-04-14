# CLAUDE.md

## Project Overview

**AstrBot CLI** is a command-line tool designed to manage and interact with [AstrBot](https://github.com/AstrBotDevs/AstrBot) – an open‑source, agentic chatbot infrastructure that integrates multiple IM platforms, LLMs, plugins, and AI capabilities.

The CLI provides two complementary execution models:
- **Stateful workflows** – powered by [dagu](https://github.com/dagu-dev/dagu), enabling reliable, DAG‑based automation of complex tasks.
- **Stateless grouped actions** – direct, immediate operations for day‑to‑day management.

### Command Groups

| Group | Purpose |
|-------|---------|
| `bots` | Manage platform connections (e.g., QQ, Telegram, Discord) – each "bot" corresponds to a platform instance in AstrBot configuration. |
| `profiles` | Handle configuration profiles used by bots – includes LLM provider selection, persona assignment, plugin enablement, and other runtime settings. |
| `plugins` | Install, list, remove, and configure AstrBot plugins. |
| `providers` | Manage LLM / model service providers (OpenAI, DeepSeek, Ollama, etc.). |
| `personas` | Create, edit, and delete persona definitions that shape bot behavior and reply style. |
| `config` | Manipulate global or scoped configuration values – separate from platform‑specific settings for clarity. |
| `workflows` | Orchestrate stateful, multi‑step processes using dagu (start, stop, list, inspect workflows). |

### Key Design Goals

- **Intuitive & discoverable** – command structure mirrors AstrBot's core concepts.
- **Terminology alignment** – terms like `bots`, `providers`, `personas` match project documentation.
- **Separation of concerns** – `config` vs. `profiles` clearly distinguishes global settings from bot‑specific configurations.
- **Workflow as first‑class citizen** – stateful operations are not an afterthought; they are integrated seamlessly via dagu.

## Repository Structure

```
├── .agents/                                    # Custom agent configurations
│   └── skills/                                 # Agent-specific skills
├── .ai/summaries/                              # AI-generated summaries (date-based: YY-MM-DD/)
├── .claude/                                    # Claude Code configuration
│   ├── settings.json                           # Claude Code settings
│   └── skills/                                 # Claude Code skills
├── .devcontainer/                              # Development container runtime configuration
│   ├── .env.example                            # Example environment variables file
│   └── docker-compose.yaml                     # Docker Compose file for devcontainer
├── .venv/                                      # Python virtual environment
├── astrbot_cli/                                # Main source code package
│   ├── cli.py                                  # CLI entry point with Typer commands
│   ├── __init__.py                             # Package initialization
│   └── src/                                    # Source modules
|       ├── bots.py                             # Bot management commands
|       ├── bots_utils.py                       # Bot utilities
|       ├── config.py                           # Config commands
|       ├── config_utils.py                     # Config utilities
|       ├── personas.py                         # Persona commands
|       ├── personas_utils.py                   # Persona utilities (SQLite)
|       ├── profiles.py                         # Profile commands
|       ├── profiles_utils.py                   # Profile utilities (new profiles.json)
|       ├── providers.py                        # Provider commands
|       ├── providers_utils.py                  # Provider utilities
|       ├── workflows.py                        # Workflow commands
|       ├── workflows_utils.py                  # Dagu integration
|       ├── workflows/                          # Built-in workflow templates (shipped with CLI)
|       │   └── plugin-debug.yaml               # Plugin debug workflow
|       ├── plugin.py                           # Plugin commands
|       ├── plugin_utils.py                     # Plugin utilities
|       ├── quick_start.py                      # Quick start
|       ├── path_config.py                      # Path management
|       └── utils.py                            # General utilities
├── code-repo/                                  # Storage for cloned code repositories
│   └── github/                                 # Public GitHub repositories
│       ├── helloworld/                         # AstrBot example plugin repository
│       └── AstrBot/                            # AstrBot repository
├── data/                                       # Persistent data storage for the workspace
├── debug/                                      # Temporary debugging files ONLY
├── docs/                                       # Project documentation
│   ├── AI-external-context/                    # External system context for AI agents
│   ├── blogs/                                  # Blog posts and articles
│   ├── development/                            # Date-based development plans (YY-MM-DD/)
│   ├── requirements/                           # Requirements documentation
│   ├── rules/                                  # Repository rules and guidelines
│   │   └── project.md                          # Project rules and guidelines (this file)
│   ├── user-guide/                             # User guides and manuals
│   └── TODO.md                                 # Active TODO list (unfinished tasks only)
├── scripts/                                    # Repository scripts
├── .dockerignore                               # Docker ignore file
├── .env.example                                # Example environment variables file
├── .env.local                                  # Local environment variables file
├── .gitignore                                  # Git ignore file
├── .python-version                             # Python version specification
├── CLAUDE.md                                   # Project overview and guidelines for AI agents
├── Dockerfile                                  # Dockerfile for containerizing the application
├── LICENSE                                     # License file
├── pyproject.toml                              # Python project configuration
├── README.md                                   # Project README file
└── uv.lock                                     # Python dependency lock file
```

## Important Notes

1. **Follow the file organization rules** outlined in `docs/rules/project.md` for all new files and documentation.
2. **Always check `docs/development/`** for current plans before implementing
3. **Date-based file organization** for all new documentation
4. **TODO.md is for unfinished tasks only** - remove completed items
5. each py file should within 800 lines, if the file is too long, consider refactor it into multiple files and modules
