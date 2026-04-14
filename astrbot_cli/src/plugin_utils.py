"""Plugin management utilities for AstrBot CLI."""

import json
import shutil
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import yaml

from .utils import run_command_capture
from .path_config import get_astrbot_root, get_plugins_dir, get_config_dir

# Constants
PLUGIN_REGISTRY_URL = "https://api.soulter.top/astrbot/plugins"
PLUGIN_REGISTRY_FALLBACK = "https://github.com/AstrBotDevs/AstrBot_Plugins_Collection/raw/refs/heads/main/plugin_cache_original.json"


class PluginStatus(str, Enum):
    """Plugin installation status."""

    INSTALLED = "installed"
    NEED_UPDATE = "needs-update"
    NOT_INSTALLED = "not-installed"
    NOT_PUBLISHED = "unpublished"


@dataclass
class PluginInfo:
    """Plugin information."""

    name: str
    desc: str
    version: str
    author: str
    repo: str
    status: PluginStatus
    local_path: Path | None = None

    def __str__(self) -> str:
        desc_display = self.desc[:30] + "..." if len(self.desc) > 30 else self.desc
        return f"{self.name:<20} {self.version:<10} {self.status.value:<12} {self.author:<15} {desc_display}"


def load_yaml_metadata(plugin_dir: Path) -> dict:
    """Load plugin metadata from metadata.yaml file.

    Args:
        plugin_dir: Plugin directory path

    Returns:
        dict: Dictionary containing metadata, or empty dict if loading fails

    """
    yaml_path = plugin_dir / "metadata.yaml"
    if yaml_path.exists():
        try:
            return yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            print(f"Failed to read {yaml_path}: {e}")
    return {}


def get_online_plugins() -> list[PluginInfo]:
    """Fetch online plugin list from registry.

    Returns:
        list[PluginInfo]: List of available plugins from online registry

    """
    plugins = []
    for url in [PLUGIN_REGISTRY_URL, PLUGIN_REGISTRY_FALLBACK]:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()

                for plugin_id, plugin_info in data.items():
                    plugins.append(
                        PluginInfo(
                            name=str(plugin_id),
                            desc=str(plugin_info.get("desc", "")),
                            version=str(plugin_info.get("version", "")),
                            author=str(plugin_info.get("author", "")),
                            repo=str(plugin_info.get("repo", "")),
                            status=PluginStatus.NOT_INSTALLED,
                        )
                    )
                break
        except Exception as e:
            print(f"Failed to fetch plugins from {url}: {e}")
            continue

    return plugins


def get_local_plugins(plugins_dir: Path) -> list[PluginInfo]:
    """Get list of locally installed plugins.

    Args:
        plugins_dir: Path to plugins directory

    Returns:
        list[PluginInfo]: List of installed plugins

    """
    plugins = []
    if not plugins_dir.exists():
        return plugins

    for plugin_dir in plugins_dir.glob("*"):
        if not plugin_dir.is_dir():
            continue

        metadata = load_yaml_metadata(plugin_dir)
        if not metadata:
            continue

        # Get required fields
        name = metadata.get("name", plugin_dir.name)
        desc = metadata.get("desc", metadata.get("description", ""))
        version = metadata.get("version", "0.0.0")
        author = metadata.get("author", "Unknown")
        repo = metadata.get("repo", "")

        plugins.append(
            PluginInfo(
                name=str(name),
                desc=str(desc),
                version=str(version),
                author=str(author),
                repo=str(repo),
                status=PluginStatus.INSTALLED,
                local_path=plugin_dir,
            )
        )

    return plugins


def compare_versions(v1: str, v2: str) -> int:
    """Compare two version strings.

    Returns:
        -1 if v1 < v2
        0 if v1 == v2
        1 if v1 > v2

    """
    try:
        parts1 = [int(p) for p in v1.lstrip("v").split(".")]
        parts2 = [int(p) for p in v2.lstrip("v").split(".")]

        # Pad with zeros to make equal length
        max_len = max(len(parts1), len(parts2))
        parts1.extend([0] * (max_len - len(parts1)))
        parts2.extend([0] * (max_len - len(parts2)))

        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            if p1 > p2:
                return 1
        return 0
    except (ValueError, AttributeError):
        return 0


def build_plugin_list() -> list[PluginInfo]:
    """Build complete plugin list with status.

    Returns:
        list[PluginInfo]: Combined list of local and online plugins with correct status

    """
    plugins_dir = get_plugins_dir()

    # Get local plugins first
    local_plugins = {p.name: p for p in get_local_plugins(plugins_dir)}

    # Get online plugins
    online_plugins = get_online_plugins()
    online_names = {p.name for p in online_plugins}

    result = []

    # Process local plugins
    for name, plugin in local_plugins.items():
        if name in online_names:
            # Find online version
            online_plugin = next(p for p in online_plugins if p.name == name)
            if compare_versions(plugin.version, online_plugin.version) < 0:
                plugin.status = PluginStatus.NEED_UPDATE
            else:
                plugin.status = PluginStatus.INSTALLED
        else:
            plugin.status = PluginStatus.NOT_PUBLISHED
        result.append(plugin)

    # Add uninstalled online plugins
    for online_plugin in online_plugins:
        if online_plugin.name not in local_plugins:
            result.append(online_plugin)

    return result


def download_plugin(repo_url: str, target_path: Path, proxy: str | None = None) -> None:
    """Download and extract plugin from GitHub repository.

    Args:
        repo_url: GitHub repository URL
        target_path: Target directory path
        proxy: Optional proxy server address

    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Parse repository info
        parts = repo_url.rstrip("/").split("/")
        author = parts[-2]
        repo = parts[-1].replace(".git", "")

        # Try to get the latest release
        release_url = f"https://api.github.com/repos/{author}/{repo}/releases"

        with httpx.Client(proxy=proxy, follow_redirects=True, timeout=30.0) as client:
            try:
                resp = client.get(release_url)
                resp.raise_for_status()
                releases = resp.json()

                if releases:
                    download_url = releases[0]["zipball_url"]
                else:
                    # No release, use default branch
                    print(f"Downloading {author}/{repo} from default branch...")
                    download_url = f"https://github.com/{author}/{repo}/archive/refs/heads/master.zip"
            except Exception:
                # Fallback to master branch
                download_url = f"https://github.com/{author}/{repo}/archive/refs/heads/master.zip"

            # Download
            resp = client.get(download_url)
            if resp.status_code == 404 and "master.zip" in download_url:
                alt_url = download_url.replace("master.zip", "main.zip")
                print("Branch 'master' not found, trying 'main' branch...")
                resp = client.get(alt_url)

            resp.raise_for_status()
            zip_content = BytesIO(resp.content)

        # Extract
        with ZipFile(zip_content) as z:
            z.extractall(temp_dir)
            namelist = z.namelist()
            root_dir = Path(namelist[0]).parts[0] if namelist else ""

        # Move to target
        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.move(temp_dir / root_dir, target_path)

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def find_plugin_by_name(name: str) -> PluginInfo | None:
    """Find a plugin by name in the online registry.

    Args:
        name: Plugin name

    Returns:
        PluginInfo if found, None otherwise

    """
    plugins = get_online_plugins()
    return next((p for p in plugins if p.name == name), None)


def install_plugin(name: str, proxy: str | None = None) -> PluginInfo:
    """Install a plugin by name, URL, or local path.

    Args:
        name: Plugin name, repository URL, or local path
        proxy: Optional proxy server address

    Returns:
        PluginInfo: Installed plugin info

    Raises:
        ValueError: If plugin not found or already installed

    """
    plugins_dir = get_plugins_dir()
    plugins_dir.mkdir(parents=True, exist_ok=True)

    # Check if it's a local path
    local_path = Path(name).expanduser().resolve()
    if local_path.exists() and local_path.is_dir():
        # Check for metadata.yaml to confirm it's a valid plugin
        metadata_path = local_path / "metadata.yaml"
        if not metadata_path.exists():
            raise ValueError(f"'{name}' is not a valid AstrBot plugin (missing metadata.yaml)")

        # Load metadata to get plugin name
        metadata = load_yaml_metadata(local_path)
        plugin_name = metadata.get("name", local_path.name)
        target_path = plugins_dir / plugin_name

        if target_path.exists():
            raise ValueError(f"Plugin directory '{plugin_name}' already exists")

        print(f"Installing plugin from local path: {local_path}...")

        # Copy the plugin directory
        shutil.copytree(local_path, target_path)

        return PluginInfo(
            name=str(plugin_name),
            desc=str(metadata.get("desc", "")),
            version=str(metadata.get("version", "0.0.0")),
            author=str(metadata.get("author", "Unknown")),
            repo=str(metadata.get("repo", "")),
            status=PluginStatus.INSTALLED,
            local_path=target_path,
        )

    # Check if it's a URL
    if name.startswith("http"):
        repo_url = name
        plugin_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        target_path = plugins_dir / plugin_name

        if target_path.exists():
            raise ValueError(f"Plugin directory '{plugin_name}' already exists")

        print(f"Installing plugin from {repo_url}...")
        download_plugin(repo_url, target_path, proxy)

    else:
        # Find in registry
        plugin = find_plugin_by_name(name)
        if not plugin:
            raise ValueError(f"Plugin '{name}' not found in registry")

        target_path = plugins_dir / name
        if target_path.exists():
            raise ValueError(f"Plugin '{name}' is already installed")

        print(f"Installing plugin {name}...")
        download_plugin(plugin.repo, target_path, proxy)

    # Load and return plugin info
    metadata = load_yaml_metadata(target_path)
    return PluginInfo(
        name=str(metadata.get("name", name)),
        desc=str(metadata.get("desc", "")),
        version=str(metadata.get("version", "0.0.0")),
        author=str(metadata.get("author", "Unknown")),
        repo=str(metadata.get("repo", "")),
        status=PluginStatus.INSTALLED,
        local_path=target_path,
    )


def uninstall_plugin(name: str) -> None:
    """Uninstall a plugin by name.

    Args:
        name: Plugin name

    Raises:
        ValueError: If plugin not installed

    """
    plugins_dir = get_plugins_dir()
    plugin_path = plugins_dir / name

    if not plugin_path.exists():
        raise ValueError(f"Plugin '{name}' is not installed")

    shutil.rmtree(plugin_path)
    print(f"Plugin '{name}' has been uninstalled")


def update_plugin(name: str | None = None, proxy: str | None = None) -> list[PluginInfo]:
    """Update one or all plugins.

    Args:
        name: Plugin name to update, or None to update all
        proxy: Optional proxy server address

    Returns:
        list[PluginInfo]: List of updated plugins

    Raises:
        ValueError: If specified plugin not found or doesn't need update

    """
    plugins = build_plugin_list()
    updated = []

    if name:
        # Update specific plugin
        plugin = next((p for p in plugins if p.name == name), None)
        if not plugin:
            raise ValueError(f"Plugin '{name}' not found")
        if plugin.status != PluginStatus.NEED_UPDATE:
            raise ValueError(f"Plugin '{name}' does not need updating")

        print(f"Updating plugin {name}...")
        if plugin.local_path:
            shutil.rmtree(plugin.local_path)
        download_plugin(plugin.repo, plugin.local_path or get_plugins_dir() / name, proxy)
        updated.append(plugin)

    else:
        # Update all plugins needing update
        need_update = [p for p in plugins if p.status == PluginStatus.NEED_UPDATE]

        if not need_update:
            print("No plugins need updating")
            return updated

        print(f"Found {len(need_update)} plugin(s) needing update")
        for plugin in need_update:
            print(f"Updating plugin {plugin.name}...")
            if plugin.local_path:
                shutil.rmtree(plugin.local_path)
            download_plugin(plugin.repo, plugin.local_path, proxy)
            updated.append(plugin)

    return updated


def get_plugin_config_path(name: str) -> Path:
    """Get the config file path for a plugin.

    Args:
        name: Plugin name

    Returns:
        Path to plugin config file

    """
    return get_config_dir() / f"{name}_config.json"


def get_plugin_config_schema_path(name: str) -> Path | None:
    """Get the config schema file path for a plugin.

    Args:
        name: Plugin name

    Returns:
        Path to plugin config schema file, or None if not found

    """
    plugins_dir = get_plugins_dir()
    plugin_dir = plugins_dir / name
    schema_path = plugin_dir / "_conf_schema.json"
    return schema_path if schema_path.exists() else None


def get_plugin_config(name: str) -> dict:
    """Get plugin configuration.

    Args:
        name: Plugin name

    Returns:
        Plugin configuration dict

    """
    config_path = get_plugin_config_path(name)
    if config_path.exists():
        try:
            # Use utf-8-sig to handle BOM (Byte Order Mark)
            return json.loads(config_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in config file {config_path}: {e}")
            return {}
    return {}


def set_plugin_config(name: str, config: dict) -> None:
    """Save plugin configuration.

    Args:
        name: Plugin name
        config: Configuration dict to save

    """
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = get_plugin_config_path(name)
    # Use utf-8 (without BOM) for consistency
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def get_plugin_config_schema(name: str) -> dict | None:
    """Get plugin configuration schema.

    Args:
        name: Plugin name

    Returns:
        Configuration schema dict, or None if not available

    """
    schema_path = get_plugin_config_schema_path(name)
    if schema_path:
        try:
            return json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def display_plugins(plugins: list[PluginInfo], title: str | None = None) -> None:
    """Display a list of plugins in a formatted table.

    Args:
        plugins: List of plugins to display
        title: Optional title to display

    """
    if title:
        print(f"\n{title}")
        print("-" * 80)

    if not plugins:
        print("No plugins found")
        return

    print(f"{'Name':<20} {'Version':<10} {'Status':<12} {'Author':<15} {'Description':<30}")
    print("-" * 87)

    for plugin in plugins:
        print(plugin)
