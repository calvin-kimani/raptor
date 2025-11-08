"""
Plugin/Tool discovery and management system.

Downloads install.py files from remote URLs and lets them handle plugin installation.
"""

from pathlib import Path
from typing import Dict, Optional, Any
import importlib.util
import sys
import urllib.request

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python
    except ImportError:
        import toml as tomllib  # Fallback to toml package


def load_plugins_registry() -> Dict[str, str]:
    """
    Load plugin registry from raptor.toml.

    Returns:
        Dict mapping plugin name to install.py URL
    """
    # Find raptor.toml (in project root or raptor installation)
    toml_paths = [
        Path.cwd() / "raptor.toml",  # Current project
        Path(__file__).parent.parent.parent / "raptor.toml",  # Raptor installation
        Path.home() / ".raptor" / "raptor.toml",  # User config
    ]

    config_file = None
    for toml_path in toml_paths:
        if toml_path.exists():
            config_file = toml_path
            break

    if not config_file:
        return {}

    # Read TOML file
    try:
        with open(config_file, 'rb' if hasattr(tomllib, 'load') else 'r') as f:
            if hasattr(tomllib, 'load'):
                config = tomllib.load(f)
            else:
                config = tomllib.load(f)
    except Exception as e:
        print(f"Warning: Could not read raptor.toml: {e}")
        return {}

    # Extract plugins section
    plugins = {}
    if 'plugins' in config:
        for plugin_name, plugin_config in config['plugins'].items():
            if isinstance(plugin_config, dict):
                url = plugin_config.get('url', '')
                if url:
                    plugins[plugin_name] = url

    return plugins


def _fetch_install_py(plugin_name: str, url: str) -> Optional[Path]:
    """
    Download install.py from a URL.

    Args:
        plugin_name: Name of the plugin
        url: Direct URL to the install.py file

    Returns:
        Path to the downloaded install.py, or None if download failed
    """
    plugins_dir = Path(__file__).parent / "plugins"
    plugin_dir = plugins_dir / plugin_name
    install_file = plugin_dir / "install.py"

    # If already downloaded, return existing path
    if install_file.exists():
        return install_file

    # Create plugin directory
    plugin_dir.mkdir(parents=True, exist_ok=True)

    try:
        print(f"Downloading plugin '{plugin_name}' from {url}...")

        # Download the install.py file
        with urllib.request.urlopen(url) as response:
            install_content = response.read()

        # Save to file
        with open(install_file, 'wb') as f:
            f.write(install_content)

        print(f"✓ Plugin '{plugin_name}' downloaded successfully")
        return install_file

    except Exception as e:
        print(f"Error downloading plugin '{plugin_name}': {e}")
        # Clean up failed download
        if install_file.exists():
            install_file.unlink()
        if plugin_dir.exists() and not any(plugin_dir.iterdir()):
            plugin_dir.rmdir()
        return None


def discover_tools() -> Dict[str, Any]:
    """
    Discover all available tools from raptor.toml and local plugins.

    Returns:
        Dict mapping tool name to tool module
    """
    tools = {}

    # First, check for local plugins (for development)
    plugins_dir = Path(__file__).parent / "plugins"
    if plugins_dir.exists():
        for plugin_path in plugins_dir.iterdir():
            if plugin_path.is_dir() and not plugin_path.name.startswith('_'):
                install_file = plugin_path / "install.py"
                if install_file.exists():
                    plugin_name = plugin_path.name
                    module_name = f"cli.plugins.{plugin_name}.install"

                    try:
                        spec = importlib.util.spec_from_file_location(module_name, install_file)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[module_name] = module
                            spec.loader.exec_module(module)

                            if hasattr(module, 'TOOL_INFO'):
                                tools[module.TOOL_INFO['name']] = module
                    except Exception as e:
                        print(f"Warning: Could not load local plugin '{plugin_name}': {e}")

    # Then, check for remote plugins in raptor.toml
    registry = load_plugins_registry()
    for plugin_name, url in registry.items():
        # Skip if already loaded locally
        if any(mod.TOOL_INFO.get('name') == plugin_name for mod in tools.values()):
            continue

        # Download install.py
        install_file = _fetch_install_py(plugin_name, url)

        if not install_file:
            continue

        # Import the install module
        module_name = f"cli.plugins.{plugin_name}.install"

        try:
            spec = importlib.util.spec_from_file_location(module_name, install_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                if hasattr(module, 'TOOL_INFO'):
                    tools[module.TOOL_INFO['name']] = module
                else:
                    print(f"Warning: Plugin '{plugin_name}' missing TOOL_INFO")

        except Exception as e:
            print(f"Warning: Could not load plugin '{plugin_name}': {e}")

    return tools


def list_tools() -> None:
    """List all available tools."""
    tools = discover_tools()

    if not tools:
        print("No tools available")
        return

    print("\nAvailable tools:\n")

    for tool_name, module in tools.items():
        info = module.TOOL_INFO
        print(f"  {tool_name:15s} - {info['description']}")

        # Check installation status
        if hasattr(module, 'check'):
            statuses = module.check()
            installed_count = sum(1 for installed in statuses.values() if installed)
            total_count = len(statuses)

            if installed_count == total_count:
                print(f"  {'':15s}   ✓ Installed")
            elif installed_count > 0:
                print(f"  {'':15s}   ⚠ Partially installed ({installed_count}/{total_count})")
            else:
                print(f"  {'':15s}   ✗ Not installed")

        print()


def install_tool(tool_name: str) -> bool:
    """
    Install a specific tool.

    Args:
        tool_name: Name of the tool to install

    Returns:
        True if installation succeeded
    """
    tools = discover_tools()

    if tool_name not in tools:
        print(f"Error: Unknown tool '{tool_name}'")
        print(f"\nAvailable tools: {', '.join(tools.keys())}")
        return False

    module = tools[tool_name]

    if not hasattr(module, 'install'):
        print(f"Error: Tool '{tool_name}' does not have an install() function")
        return False

    return module.install()


def check_tool(tool_name: str) -> bool:
    """
    Check if a tool is installed.

    Args:
        tool_name: Name of the tool

    Returns:
        True if tool is fully installed
    """
    tools = discover_tools()

    if tool_name not in tools:
        return False

    module = tools[tool_name]

    if hasattr(module, 'check'):
        statuses = module.check()
        # Check if all required dependencies are installed
        return all(statuses.values())

    return False


def show_status(tool_name: str) -> None:
    """
    Show installation status for a tool.

    Args:
        tool_name: Name of the tool
    """
    tools = discover_tools()

    if tool_name not in tools:
        print(f"Error: Unknown tool '{tool_name}'")
        return

    module = tools[tool_name]

    if hasattr(module, 'status'):
        module.status()
    else:
        info = module.TOOL_INFO
        print(f"\n{tool_name} - {info['description']}")
        print("Status information not available")


def register_tool_commands(subparsers) -> Dict[str, Any]:
    """
    Register CLI commands from all installed tools.

    Args:
        subparsers: argparse subparsers object

    Returns:
        Dict mapping command names to handler modules
    """
    tools = discover_tools()
    command_handlers = {}

    for tool_name, module in tools.items():
        if hasattr(module, 'register_commands'):
            try:
                handlers = module.register_commands(subparsers)
                if handlers:
                    command_handlers.update(handlers)
            except Exception as e:
                print(f"Warning: Could not register commands for '{tool_name}': {e}")

    return command_handlers
