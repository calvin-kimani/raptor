"""
Plugin/Tool discovery and management system.

Fetches plugins from remote git repositories and manages their installation and CLI integration.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import importlib.util
import sys
import subprocess
import shutil


def load_plugins_registry() -> Dict[str, Tuple[str, str, str]]:
    """
    Load plugin registry from plugins.txt.

    Returns:
        Dict mapping plugin name to (git_url, branch, install_path) tuple
    """
    plugins_file = Path(__file__).parent / "plugins.txt"
    plugins = {}

    if not plugins_file.exists():
        return plugins

    with open(plugins_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse plugin:git_url:branch:install_path format
            parts = line.split(':', 3)
            if len(parts) == 4:
                name, git_url, branch, install_path = parts
                plugins[name.strip()] = (git_url.strip(), branch.strip(), install_path.strip())

    return plugins


def _fetch_plugin(plugin_name: str, git_url: str, branch: str, install_path: str) -> Optional[Path]:
    """
    Fetch a plugin from a remote git repository.

    Args:
        plugin_name: Name of the plugin
        git_url: Git repository URL
        branch: Branch to fetch from
        install_path: Path to install.py within the repo

    Returns:
        Path to the plugin directory, or None if fetch failed
    """
    plugins_dir = Path(__file__).parent / "plugins"
    plugin_dir = plugins_dir / plugin_name

    # If already fetched, return existing path
    if plugin_dir.exists():
        return plugin_dir

    # Create plugins directory if needed
    plugins_dir.mkdir(exist_ok=True)

    try:
        print(f"Fetching plugin '{plugin_name}' from {git_url} (branch: {branch})...")

        # Clone the repository with sparse checkout
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", branch, "--filter=blob:none", "--sparse", git_url, str(plugin_dir)],
            check=True,
            capture_output=True,
            text=True
        )

        # Set up sparse checkout for only the plugin directory
        plugin_base_path = Path(install_path).parent
        subprocess.run(
            ["git", "-C", str(plugin_dir), "sparse-checkout", "set", str(plugin_base_path)],
            check=True,
            capture_output=True,
            text=True
        )

        print(f"✓ Plugin '{plugin_name}' fetched successfully")
        return plugin_dir

    except subprocess.CalledProcessError as e:
        print(f"Error fetching plugin '{plugin_name}': {e.stderr if e.stderr else str(e)}")
        # Clean up failed clone
        if plugin_dir.exists():
            shutil.rmtree(plugin_dir)
        return None
    except Exception as e:
        print(f"Unexpected error fetching plugin '{plugin_name}': {e}")
        if plugin_dir.exists():
            shutil.rmtree(plugin_dir)
        return None


def discover_tools() -> Dict[str, Any]:
    """
    Discover all available tools from plugins.txt.

    Returns:
        Dict mapping tool name to tool module
    """
    tools = {}
    registry = load_plugins_registry()

    for plugin_name, (git_url, branch, install_path) in registry.items():
        # Fetch plugin if needed (but don't install dependencies)
        plugin_dir = _fetch_plugin(plugin_name, git_url, branch, install_path)

        if not plugin_dir:
            continue

        # Resolve the install.py path
        install_file = plugin_dir / install_path

        if not install_file.exists():
            print(f"Warning: Plugin '{plugin_name}' install file not found: {install_path}")
            continue

        # Import the install module
        module_name = f"cli.plugins.{plugin_name}.install"

        try:
            spec = importlib.util.spec_from_file_location(module_name, install_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # Add to sys.modules so relative imports work
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                # Get tool info
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
