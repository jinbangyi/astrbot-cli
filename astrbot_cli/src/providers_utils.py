"""Provider management utilities for AstrBot CLI."""

import json
from pathlib import Path
from typing import Any

from .path_config import get_cmd_config_path

# Known provider types with their descriptions
KNOWN_PROVIDERS = {
    "openai": "OpenAI API (GPT-4, GPT-3.5, etc.)",
    "anthropic": "Anthropic Claude API",
    "deepseek": "DeepSeek API",
    "gemini": "Google Gemini API",
    "zhipu": "Zhipu AI (智谱)",
    "ollama": "Ollama (local models)",
    "groq": "Groq API",
    "xai": "xAI Grok API",
    "openrouter": "OpenRouter API",
    "dashscope": "Alibaba DashScope (通义千问)",
    "moonshot": "Moonshot AI (Kimi)",
    "yi": "01.AI (零一万物)",
    "baichuan": "Baichuan (百川)",
    "minimax": "MiniMax",
    "siliconflow": "SiliconFlow",
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


def get_available_providers() -> list[dict[str, str]]:
    """Get list of available provider types.

    Returns:
        List of provider info dicts with name and desc

    """
    providers = []
    for name, desc in KNOWN_PROVIDERS.items():
        providers.append({"name": name, "desc": desc})
    return providers


def list_provider_configs() -> list[dict]:
    """List all configured providers.

    Returns:
        List of provider configuration dictionaries

    """
    config = load_config()
    return config.get("provider", [])


def get_provider_config(provider_id: str) -> dict | None:
    """Get a provider configuration by ID.

    Args:
        provider_id: Provider instance ID

    Returns:
        Provider configuration dict or None if not found

    """
    config = load_config()
    providers = config.get("provider", [])
    for provider in providers:
        if provider.get("id") == provider_id:
            return provider
    return None


def add_provider_config(provider_type: str, provider_id: str, enable: bool = True) -> dict:
    """Add a new provider configuration.

    Args:
        provider_type: Provider type (e.g., openai, deepseek, ollama)
        provider_id: Provider instance ID
        enable: Whether to enable the provider

    Returns:
        The created provider configuration

    Raises:
        ValueError: If provider ID already exists or type is unknown

    """
    if provider_type not in KNOWN_PROVIDERS:
        raise ValueError(f"Unknown provider type: {provider_type}. Available types: {', '.join(KNOWN_PROVIDERS.keys())}")

    config = load_config()
    providers = config.get("provider", [])

    # Check if ID already exists
    for provider in providers:
        if provider.get("id") == provider_id:
            raise ValueError(f"Provider with ID '{provider_id}' already exists")

    # Create new provider config
    new_provider = {
        "id": provider_id,
        "provider": provider_type,
        "type": f"{provider_type}_chat_completion",
        "provider_type": "chat_completion",
        "enable": enable,
    }

    # Add type-specific default config
    type_defaults = get_provider_defaults(provider_type)
    new_provider.update(type_defaults)

    providers.append(new_provider)
    config["provider"] = providers
    save_config(config)

    return new_provider


def get_provider_defaults(provider_type: str) -> dict:
    """Get default configuration values for a provider type.

    Args:
        provider_type: Provider type

    Returns:
        Dictionary of default configuration values

    """
    defaults = {
        "openai": {
            "key": [],
            "api_base": "https://api.openai.com/v1",
            "timeout": 120,
            "proxy": "",
            "custom_headers": {},
        },
        "anthropic": {
            "key": [],
            "api_base": "https://api.anthropic.com",
            "timeout": 120,
            "proxy": "",
        },
        "deepseek": {
            "key": [],
            "api_base": "https://api.deepseek.com",
            "timeout": 120,
            "proxy": "",
        },
        "gemini": {
            "key": [],
            "api_base": "https://generativelanguage.googleapis.com",
            "timeout": 120,
            "proxy": "",
        },
        "zhipu": {
            "key": [],
            "api_base": "https://open.bigmodel.cn/api/paas/v4",
            "timeout": 120,
            "proxy": "",
        },
        "ollama": {
            "api_base": "http://localhost:11434",
            "timeout": 300,
            "key": [],
        },
        "groq": {
            "key": [],
            "api_base": "https://api.groq.com/openai/v1",
            "timeout": 120,
            "proxy": "",
        },
        "xai": {
            "key": [],
            "api_base": "https://api.x.ai/v1",
            "timeout": 120,
            "proxy": "",
        },
        "openrouter": {
            "key": [],
            "api_base": "https://openrouter.ai/api/v1",
            "timeout": 120,
            "proxy": "",
        },
        "dashscope": {
            "key": [],
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "timeout": 120,
            "proxy": "",
        },
        "moonshot": {
            "key": [],
            "api_base": "https://api.moonshot.cn/v1",
            "timeout": 120,
            "proxy": "",
        },
        "yi": {
            "key": [],
            "api_base": "https://api.lingyiwanwu.com/v1",
            "timeout": 120,
            "proxy": "",
        },
        "baichuan": {
            "key": [],
            "api_base": "https://api.baichuan-ai.com/v1",
            "timeout": 120,
            "proxy": "",
        },
        "minimax": {
            "key": [],
            "api_base": "https://api.minimax.chat/v1",
            "timeout": 120,
            "proxy": "",
        },
        "siliconflow": {
            "key": [],
            "api_base": "https://api.siliconflow.cn/v1",
            "timeout": 120,
            "proxy": "",
        },
    }
    return defaults.get(provider_type, {"key": [], "timeout": 120})


def update_provider_config(provider_id: str, updates: dict) -> dict:
    """Update a provider configuration.

    Args:
        provider_id: Provider instance ID
        updates: Dictionary of fields to update

    Returns:
        Updated provider configuration

    Raises:
        ValueError: If provider not found

    """
    config = load_config()
    providers = config.get("provider", [])

    for i, provider in enumerate(providers):
        if provider.get("id") == provider_id:
            providers[i].update(updates)
            config["provider"] = providers
            save_config(config)
            return providers[i]

    raise ValueError(f"Provider '{provider_id}' not found")


def set_provider_config(provider_id: str, new_config: dict) -> None:
    """Set the complete configuration for a provider.

    Args:
        provider_id: Provider instance ID
        new_config: New configuration dictionary

    Raises:
        ValueError: If provider not found

    """
    config = load_config()
    providers = config.get("provider", [])

    for i, provider in enumerate(providers):
        if provider.get("id") == provider_id:
            # Preserve required fields
            new_config["id"] = provider_id
            new_config["provider"] = provider.get("provider", new_config.get("provider", ""))
            new_config["type"] = provider.get("type", "")
            new_config["provider_type"] = provider.get("provider_type", "chat_completion")
            providers[i] = new_config
            config["provider"] = providers
            save_config(config)
            return

    raise ValueError(f"Provider '{provider_id}' not found")


def delete_provider_config(provider_id: str) -> None:
    """Delete a provider configuration.

    Args:
        provider_id: Provider instance ID

    Raises:
        ValueError: If provider not found

    """
    config = load_config()
    providers = config.get("provider", [])

    for i, provider in enumerate(providers):
        if provider.get("id") == provider_id:
            del providers[i]
            config["provider"] = providers
            save_config(config)
            return

    raise ValueError(f"Provider '{provider_id}' not found")


def get_provider_config_schema(provider_type: str) -> dict | None:
    """Get configuration schema for a provider type.

    Args:
        provider_type: Provider type

    Returns:
        Configuration schema dict or None if not available

    """
    schemas = {
        "openai": {
            "key": {
                "type": "list[string]",
                "description": "OpenAI API Key(s)",
                "required": True,
            },
            "api_base": {
                "type": "string",
                "description": "API base URL (for proxy)",
                "default": "https://api.openai.com/v1",
            },
            "timeout": {
                "type": "int",
                "description": "Request timeout in seconds",
                "default": 120,
            },
            "proxy": {
                "type": "string",
                "description": "Proxy URL",
                "default": "",
            },
        },
        "anthropic": {
            "key": {
                "type": "list[string]",
                "description": "Anthropic API Key(s)",
                "required": True,
            },
            "api_base": {
                "type": "string",
                "description": "API base URL",
                "default": "https://api.anthropic.com",
            },
            "timeout": {
                "type": "int",
                "description": "Request timeout in seconds",
                "default": 120,
            },
        },
        "deepseek": {
            "key": {
                "type": "list[string]",
                "description": "DeepSeek API Key(s)",
                "required": True,
            },
            "api_base": {
                "type": "string",
                "description": "API base URL",
                "default": "https://api.deepseek.com",
            },
            "timeout": {
                "type": "int",
                "description": "Request timeout in seconds",
                "default": 120,
            },
        },
        "ollama": {
            "api_base": {
                "type": "string",
                "description": "Ollama server URL",
                "default": "http://localhost:11434",
            },
            "timeout": {
                "type": "int",
                "description": "Request timeout in seconds",
                "default": 300,
            },
        },
    }
    return schemas.get(provider_type)
