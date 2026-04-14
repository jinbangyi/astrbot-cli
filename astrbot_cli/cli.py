"""Main entry point for AstrBot CLI."""

import sys

import tyro

from .src.plugin import Install, Uninstall, Update, PluginList, Search, Config as PluginConfig, Info as PluginInfo
from .src.bots import List as BotList, Add as BotAdd, Remove as BotRemove, Enable as BotEnable, Disable as BotDisable, Config as BotConfig, Info as BotInfo, Send as BotSend, Messages as BotMessages, FetchMessages as BotFetchMessages
from .src.profiles import List as ProfileList, Create as ProfileCreate, Delete as ProfileDelete, Show as ProfileShow, Set as ProfileSet, Use as ProfileUse
from .src.providers import List as ProviderList, Add as ProviderAdd, Remove as ProviderRemove, Enable as ProviderEnable, Disable as ProviderDisable, Config as ProviderConfig, Info as ProviderInfo
from .src.personas import List as PersonaList, Create as PersonaCreate, Edit as PersonaEdit, Delete as PersonaDelete, Show as PersonaShow
from .src.config import Show as ConfigShow, Set as ConfigSet, Get as ConfigGet, Edit as ConfigEdit, Reset as ConfigReset, Schema as ConfigSchema
from .src.workflows import List as WorkflowList, Start as WorkflowStart, Stop as WorkflowStop, Status as WorkflowStatus, Logs as WorkflowLogs, Create as WorkflowCreate
from .src.system import (
    Init as SystemInit,
    Upgrade as SystemUpgrade,
    Start as SystemStart,
    Stop as SystemStop,
    Restart as SystemRestart,
    Status as SystemStatus,
    Logs as SystemLogs,
    Info as SystemInfo,
    Version as SystemVersion,
    QuickStart as SystemQuickStart,
    Path as SystemPath,
)


def print_help() -> None:
    """Print CLI help message."""
    print("""
AstrBot CLI - Command Line Interface for AstrBot

Usage:
    astrbot-cli <command> [options]

Commands:
    system            Manage AstrBot service (start/stop/restart/status/path/quick-start)
    bots              Manage AstrBot bots (platform connections)
    profiles          Manage configuration profiles
    plugins           Manage AstrBot plugins
    providers         Manage LLM providers
    personas          Manage personas
    config            Configure global settings
    workflows         Manage stateful workflows (dagu)

Configuration:
    Config file: ~/.config/astrbot-cli/config.yaml
    Set API key: astrbot-cli system path --api-key YOUR_KEY
    The API key is used as fallback for commands that need authentication.

System Commands:
    astrbot-cli system init                 Initialize AstrBot environment
    astrbot-cli system upgrade              Upgrade AstrBot installation
    astrbot-cli system start                Start AstrBot service
    astrbot-cli system stop                 Stop AstrBot service
    astrbot-cli system restart              Restart AstrBot service
    astrbot-cli system status               Show service status
    astrbot-cli system logs [lines]         View service logs
    astrbot-cli system info                 Show AstrBot information
    astrbot-cli system version              Show AstrBot version
    astrbot-cli system path                 Show current AstrBot path and API key status
    astrbot-cli system path --set <path>    Set AstrBot path manually
    astrbot-cli system path --api-key <key> Set default API key for AstrBot OpenAPI
    astrbot-cli system quick-start          Quick start AstrBot (uses saved/default path)
    astrbot-cli system quick-start --path /my/path    Start at specific path
    astrbot-cli system quick-start --force  Force reinstall

Bot Commands:
    astrbot-cli bots list              List configured bots
    astrbot-cli bots list --available  List available bot types
    astrbot-cli bots add <type>        Add a new bot
    astrbot-cli bots remove <id>       Remove a bot
    astrbot-cli bots enable <id>       Enable a bot
    astrbot-cli bots disable <id>      Disable a bot
    astrbot-cli bots config <id>       Configure a bot
    astrbot-cli bots info <id>         Show bot info
    astrbot-cli bots send <bot_id> <message> --umo <target>  Send a message
    astrbot-cli bots messages --list   List available chat sessions
    astrbot-cli bots messages <session_id>  Get recent messages from a session
    astrbot-cli bots fetch discord --channel <id>  Fetch messages directly from Discord

Profile Commands:
    astrbot-cli profiles list                    List all profiles
    astrbot-cli profiles create <name>           Create a new profile
    astrbot-cli profiles delete <id>             Delete a profile
    astrbot-cli profiles show [id]               Show profile details
    astrbot-cli profiles set <id> --provider X   Set profile provider
    astrbot-cli profiles use <id>                Set active profile

Plugin Commands:
    astrbot-cli plugins list              List installed plugins
    astrbot-cli plugins list --all        List all available plugins
    astrbot-cli plugins install <name>    Install a plugin (name, URL, or local path)
    astrbot-cli plugins uninstall <name>  Uninstall a plugin
    astrbot-cli plugins update [name]     Update plugin(s)
    astrbot-cli plugins search <query>    Search for plugins
    astrbot-cli plugins config <name>     Configure a plugin
    astrbot-cli plugins info <name>       Show plugin info

Provider Commands:
    astrbot-cli providers list              List configured providers
    astrbot-cli providers list --available  List available provider types
    astrbot-cli providers add <type>        Add a new provider
    astrbot-cli providers remove <id>       Remove a provider
    astrbot-cli providers enable <id>       Enable a provider
    astrbot-cli providers disable <id>      Disable a provider
    astrbot-cli providers config <id>       Configure a provider
    astrbot-cli providers info <id>         Show provider info

Persona Commands:
    astrbot-cli personas list              List all personas
    astrbot-cli personas create <id> <prompt>  Create a persona
    astrbot-cli personas edit <id> --prompt X  Edit persona prompt
    astrbot-cli personas delete <id>       Delete a persona
    astrbot-cli personas show <id>         Show persona details

Config Commands:
    astrbot-cli config show              Show current settings
    astrbot-cli config show --defaults   Show default settings
    astrbot-cli config get <key>         Get a setting value
    astrbot-cli config set <key> <value> Set a setting value
    astrbot-cli config edit              Edit settings in editor
    astrbot-cli config reset --confirm   Reset to defaults
    astrbot-cli config schema            Show settings schema

Workflow Commands:
    astrbot-cli workflows list              List all workflows
    astrbot-cli workflows start <name>      Start a workflow
    astrbot-cli workflows stop <name>       Stop a workflow
    astrbot-cli workflows status <name>     Show workflow status
    astrbot-cli workflows logs <name>       Show workflow logs
    astrbot-cli workflows create <name>     Create a new workflow

Examples:
    astrbot-cli system quick-start                        Start AstrBot at default location
    astrbot-cli system quick-start --path ~/my-astrbot    Start AstrBot at custom location
    astrbot-cli system path                               Show where AstrBot is installed
    astrbot-cli bots add telegram                         Add Telegram bot
    astrbot-cli providers add openai                      Add OpenAI provider
    astrbot-cli profiles create my-profile                Create a new profile
    astrbot-cli config show                               Show configuration
""")


def main() -> None:
    """AstrBot CLI main entry point."""
    if len(sys.argv) < 2:
        print_help()
        return

    subcommand = sys.argv[1]

    if subcommand in ["--help", "-h", "help"]:
        print_help()
        return

    # Bot subcommands
    if subcommand == "bots":
        if len(sys.argv) < 3:
            print("Usage: astrbot-cli bots <command>")
            print("Commands: list, add, remove, enable, disable, config, info, send, messages, fetch")
            return

        bot_cmd = sys.argv[2]
        cmd_args = sys.argv[3:]

        if bot_cmd == "list":
            args = tyro.cli(BotList, args=cmd_args)
            args.run()
        elif bot_cmd == "add":
            args = tyro.cli(BotAdd, args=cmd_args)
            args.run()
        elif bot_cmd == "remove":
            args = tyro.cli(BotRemove, args=cmd_args)
            args.run()
        elif bot_cmd == "enable":
            args = tyro.cli(BotEnable, args=cmd_args)
            args.run()
        elif bot_cmd == "disable":
            args = tyro.cli(BotDisable, args=cmd_args)
            args.run()
        elif bot_cmd == "config":
            args = tyro.cli(BotConfig, args=cmd_args)
            args.run()
        elif bot_cmd == "info":
            args = tyro.cli(BotInfo, args=cmd_args)
            args.run()
        elif bot_cmd == "send":
            args = tyro.cli(BotSend, args=cmd_args)
            args.run()
        elif bot_cmd == "messages":
            args = tyro.cli(BotMessages, args=cmd_args)
            args.run()
        elif bot_cmd == "fetch":
            args = tyro.cli(BotFetchMessages, args=cmd_args)
            args.run()
        else:
            print(f"Unknown bot command: {bot_cmd}")
            print("Commands: list, add, remove, enable, disable, config, info, send, messages, fetch")

    # Profile subcommands
    elif subcommand == "profiles":
        if len(sys.argv) < 3:
            print("Usage: astrbot-cli profiles <command>")
            print("Commands: list, create, delete, show, set, use")
            return

        profile_cmd = sys.argv[2]
        cmd_args = sys.argv[3:]

        if profile_cmd == "list":
            args = tyro.cli(ProfileList, args=cmd_args)
            args.run()
        elif profile_cmd == "create":
            args = tyro.cli(ProfileCreate, args=cmd_args)
            args.run()
        elif profile_cmd == "delete":
            args = tyro.cli(ProfileDelete, args=cmd_args)
            args.run()
        elif profile_cmd == "show":
            args = tyro.cli(ProfileShow, args=cmd_args)
            args.run()
        elif profile_cmd == "set":
            args = tyro.cli(ProfileSet, args=cmd_args)
            args.run()
        elif profile_cmd == "use":
            args = tyro.cli(ProfileUse, args=cmd_args)
            args.run()
        else:
            print(f"Unknown profile command: {profile_cmd}")
            print("Commands: list, create, delete, show, set, use")

    # Plugin subcommands
    elif subcommand == "plugins":
        if len(sys.argv) < 3:
            print("Usage: astrbot-cli plugins <command>")
            print("Commands: install, uninstall, update, list, search, config, info")
            return

        plugin_cmd = sys.argv[2]
        cmd_args = sys.argv[3:]

        if plugin_cmd == "install":
            args = tyro.cli(Install, args=cmd_args)
            args.run()
        elif plugin_cmd == "uninstall":
            args = tyro.cli(Uninstall, args=cmd_args)
            args.run()
        elif plugin_cmd == "update":
            args = tyro.cli(Update, args=cmd_args)
            args.run()
        elif plugin_cmd == "list":
            args = tyro.cli(PluginList, args=cmd_args)
            args.run()
        elif plugin_cmd == "search":
            args = tyro.cli(Search, args=cmd_args)
            args.run()
        elif plugin_cmd == "config":
            args = tyro.cli(PluginConfig, args=cmd_args)
            args.run()
        elif plugin_cmd == "info":
            args = tyro.cli(PluginInfo, args=cmd_args)
            args.run()
        else:
            print(f"Unknown plugin command: {plugin_cmd}")
            print("Commands: install, uninstall, update, list, search, config, info")

    # Provider subcommands
    elif subcommand == "providers":
        if len(sys.argv) < 3:
            print("Usage: astrbot-cli providers <command>")
            print("Commands: list, add, remove, enable, disable, config, info")
            return

        provider_cmd = sys.argv[2]
        cmd_args = sys.argv[3:]

        if provider_cmd == "list":
            args = tyro.cli(ProviderList, args=cmd_args)
            args.run()
        elif provider_cmd == "add":
            args = tyro.cli(ProviderAdd, args=cmd_args)
            args.run()
        elif provider_cmd == "remove":
            args = tyro.cli(ProviderRemove, args=cmd_args)
            args.run()
        elif provider_cmd == "enable":
            args = tyro.cli(ProviderEnable, args=cmd_args)
            args.run()
        elif provider_cmd == "disable":
            args = tyro.cli(ProviderDisable, args=cmd_args)
            args.run()
        elif provider_cmd == "config":
            args = tyro.cli(ProviderConfig, args=cmd_args)
            args.run()
        elif provider_cmd == "info":
            args = tyro.cli(ProviderInfo, args=cmd_args)
            args.run()
        else:
            print(f"Unknown provider command: {provider_cmd}")
            print("Commands: list, add, remove, enable, disable, config, info")

    # Persona subcommands
    elif subcommand == "personas":
        if len(sys.argv) < 3:
            print("Usage: astrbot-cli personas <command>")
            print("Commands: list, create, edit, delete, show")
            return

        persona_cmd = sys.argv[2]
        cmd_args = sys.argv[3:]

        if persona_cmd == "list":
            args = tyro.cli(PersonaList, args=cmd_args)
            args.run()
        elif persona_cmd == "create":
            args = tyro.cli(PersonaCreate, args=cmd_args)
            args.run()
        elif persona_cmd == "edit":
            args = tyro.cli(PersonaEdit, args=cmd_args)
            args.run()
        elif persona_cmd == "delete":
            args = tyro.cli(PersonaDelete, args=cmd_args)
            args.run()
        elif persona_cmd == "show":
            args = tyro.cli(PersonaShow, args=cmd_args)
            args.run()
        else:
            print(f"Unknown persona command: {persona_cmd}")
            print("Commands: list, create, edit, delete, show")

    # Config subcommands
    elif subcommand == "config":
        if len(sys.argv) < 3:
            print("Usage: astrbot-cli config <command>")
            print("Commands: show, get, set, edit, reset, schema")
            return

        config_cmd = sys.argv[2]
        cmd_args = sys.argv[3:]

        if config_cmd == "show":
            args = tyro.cli(ConfigShow, args=cmd_args)
            args.run()
        elif config_cmd == "get":
            args = tyro.cli(ConfigGet, args=cmd_args)
            args.run()
        elif config_cmd == "set":
            args = tyro.cli(ConfigSet, args=cmd_args)
            args.run()
        elif config_cmd == "edit":
            args = tyro.cli(ConfigEdit, args=cmd_args)
            args.run()
        elif config_cmd == "reset":
            args = tyro.cli(ConfigReset, args=cmd_args)
            args.run()
        elif config_cmd == "schema":
            args = tyro.cli(ConfigSchema, args=cmd_args)
            args.run()
        else:
            print(f"Unknown config command: {config_cmd}")
            print("Commands: show, get, set, edit, reset, schema")

    # Workflow subcommands
    elif subcommand == "workflows":
        if len(sys.argv) < 3:
            print("Usage: astrbot-cli workflows <command>")
            print("Commands: list, start, stop, status, logs, create")
            return

        workflow_cmd = sys.argv[2]
        cmd_args = sys.argv[3:]

        if workflow_cmd == "list":
            args = tyro.cli(WorkflowList, args=cmd_args)
            args.run()
        elif workflow_cmd == "start":
            args = tyro.cli(WorkflowStart, args=cmd_args)
            args.run()
        elif workflow_cmd == "stop":
            args = tyro.cli(WorkflowStop, args=cmd_args)
            args.run()
        elif workflow_cmd == "status":
            args = tyro.cli(WorkflowStatus, args=cmd_args)
            args.run()
        elif workflow_cmd == "logs":
            args = tyro.cli(WorkflowLogs, args=cmd_args)
            args.run()
        elif workflow_cmd == "create":
            args = tyro.cli(WorkflowCreate, args=cmd_args)
            args.run()
        else:
            print(f"Unknown workflow command: {workflow_cmd}")
            print("Commands: list, start, stop, status, logs, create")

    # System subcommands
    elif subcommand == "system":
        if len(sys.argv) < 3:
            print("Usage: astrbot-cli system <command>")
            print("Commands: init, upgrade, start, stop, restart, status, logs, info, version, path, quick-start")
            return

        system_cmd = sys.argv[2]
        cmd_args = sys.argv[3:]

        if system_cmd == "init":
            args = tyro.cli(SystemInit, args=cmd_args)
            args.run()
        elif system_cmd == "upgrade":
            args = tyro.cli(SystemUpgrade, args=cmd_args)
            args.run()
        elif system_cmd == "start":
            args = tyro.cli(SystemStart, args=cmd_args)
            args.run()
        elif system_cmd == "stop":
            args = tyro.cli(SystemStop, args=cmd_args)
            args.run()
        elif system_cmd == "restart":
            args = tyro.cli(SystemRestart, args=cmd_args)
            args.run()
        elif system_cmd == "status":
            args = tyro.cli(SystemStatus, args=cmd_args)
            args.run()
        elif system_cmd == "logs":
            args = tyro.cli(SystemLogs, args=cmd_args)
            args.run()
        elif system_cmd == "info":
            args = tyro.cli(SystemInfo, args=cmd_args)
            args.run()
        elif system_cmd == "version":
            args = tyro.cli(SystemVersion, args=cmd_args)
            args.run()
        elif system_cmd == "path":
            args = tyro.cli(SystemPath, args=cmd_args)
            args.run()
        elif system_cmd == "quick-start":
            args = tyro.cli(SystemQuickStart, args=cmd_args)
            args.run()
        else:
            print(f"Unknown system command: {system_cmd}")
            print("Commands: init, upgrade, start, stop, restart, status, logs, info, version, path, quick-start")

    else:
        print(f"Unknown command: {subcommand}")
        print("Commands: system, bots, profiles, plugins, providers, personas, config, workflows")


if __name__ == "__main__":
    main()
