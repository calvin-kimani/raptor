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

    Expected format in raptor.toml:
    [plugins.plugin_name]
    url = "https://raw.githubusercontent.com/.../install.py"
    description = "Plugin description"

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
            if isinstance(plugin_config, dict) and 'url' in plugin_config:
                plugins[plugin_name] = plugin_config['url']

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
    Discover all available tools from multiple sources with priority order.

    Priority (highest to lowest):
    1. Project-specific plugins (<project>/.plugins/)
    2. Global plugins (<raptor-install>/bin/cli/plugins/)
    3. Remote plugins (from raptor.toml registry)

    Returns:
        Dict mapping tool name to tool module with source information
    """
    tools = {}

    # Priority 1: Project-specific plugins
    project_plugins_dir = Path.cwd() / ".plugins"
    if project_plugins_dir.exists():
        for plugin_path in project_plugins_dir.iterdir():
            if plugin_path.is_dir() and not plugin_path.name.startswith('_'):
                install_file = plugin_path / "install.py"
                if install_file.exists():
                    plugin_name = plugin_path.name
                    module_name = f"project.plugins.{plugin_name}.install"

                    try:
                        spec = importlib.util.spec_from_file_location(module_name, install_file)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[module_name] = module
                            spec.loader.exec_module(module)

                            if hasattr(module, 'TOOL_INFO'):
                                # Mark as project plugin
                                module._plugin_source = "project"
                                module._plugin_path = str(plugin_path)
                                tools[module.TOOL_INFO['name']] = module
                    except Exception as e:
                        print(f"Warning: Could not load project plugin '{plugin_name}': {e}")

    # Priority 2: Global plugins (raptor installation)
    global_plugins_dir = Path(__file__).parent / "plugins"
    if global_plugins_dir.exists():
        for plugin_path in global_plugins_dir.iterdir():
            if plugin_path.is_dir() and not plugin_path.name.startswith('_'):
                install_file = plugin_path / "install.py"
                if install_file.exists():
                    plugin_name = plugin_path.name

                    # Check if already loaded from project
                    if any(mod.TOOL_INFO.get('name') == plugin_name for mod in tools.values()
                           if hasattr(mod, 'TOOL_INFO')):
                        continue

                    module_name = f"cli.plugins.{plugin_name}.install"

                    try:
                        spec = importlib.util.spec_from_file_location(module_name, install_file)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[module_name] = module
                            spec.loader.exec_module(module)

                            if hasattr(module, 'TOOL_INFO'):
                                # Mark as global plugin
                                module._plugin_source = "global"
                                module._plugin_path = str(plugin_path)
                                tools[module.TOOL_INFO['name']] = module
                    except Exception as e:
                        print(f"Warning: Could not load global plugin '{plugin_name}': {e}")

    # Priority 3: Remote plugins from raptor.toml (don't auto-download, just show available)
    # These are shown in list but not automatically loaded - user must install them first

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
        source = getattr(module, '_plugin_source', 'unknown')

        # Show source indicator
        source_indicator = {
            'project': '[Project]',
            'global': '[Global]',
            'remote': '[Remote]',
        }.get(source, '')

        print(f"  {tool_name:20s} {source_indicator:10s} - {info['description']}")

        # Check installation status
        if hasattr(module, 'check'):
            statuses = module.check()
            installed_count = sum(1 for installed in statuses.values() if installed)
            total_count = len(statuses)

            if installed_count == total_count:
                print(f"  {'':20s} {'':10s}   ✓ Installed")
            elif installed_count > 0:
                print(f"  {'':20s} {'':10s}   ⚠ Partially installed ({installed_count}/{total_count})")
            else:
                print(f"  {'':20s} {'':10s}   ✗ Not installed")

        print()


def install_tool(tool_name: str, global_install: bool = False) -> bool:
    """
    Install a specific tool.

    Args:
        tool_name: Name of the tool to install
        global_install: If True, install to global plugins; if False, install to project plugins

    Returns:
        True if installation succeeded
    """
    # Determine installation directory
    if global_install:
        install_dir = Path(__file__).parent / "plugins" / tool_name
        location = "global"
    else:
        install_dir = Path.cwd() / ".plugins" / tool_name
        location = "project"

    # Check if plugin exists in raptor.toml
    registry = load_plugins_registry()

    if tool_name not in registry:
        print(f"Error: Unknown tool '{tool_name}'")
        print(f"\nAvailable tools in raptor.toml: {', '.join(registry.keys())}")
        return False

    # Get plugin URL from registry
    plugin_url = registry[tool_name]

    print(f"Installing '{tool_name}' to {location} plugins...")
    print(f"  Source: {plugin_url}")
    print(f"  Target: {install_dir}")

    # Create installation directory
    install_dir.mkdir(parents=True, exist_ok=True)

    try:
        import urllib.request
        import shutil

        # Download install.py
        install_file = install_dir / "install.py"

        # Check if URL is a local file path
        if plugin_url.startswith('file://'):
            # Remove file:// prefix
            local_path = Path(plugin_url[7:])
            if not local_path.exists():
                print(f"  ✗ Local file not found: {local_path}")
                return False

            # If it's a directory, look for install.py
            if local_path.is_dir():
                source_install = local_path / "install.py"
                if not source_install.exists():
                    print(f"  ✗ install.py not found in: {local_path}")
                    return False

                # Copy entire directory
                print(f"  Copying plugin directory...")
                if install_dir.exists():
                    shutil.rmtree(install_dir)
                shutil.copytree(local_path, install_dir)
                print(f"  ✓ Copied directory")
            else:
                # Copy single file
                shutil.copy2(local_path, install_file)
                print(f"  ✓ Copied install.py")

        elif plugin_url.startswith('/') or plugin_url.startswith('./') or plugin_url.startswith('../'):
            # Local file path (absolute or relative)
            local_path = Path(plugin_url).expanduser().resolve()

            if not local_path.exists():
                print(f"  ✗ Local file not found: {local_path}")
                return False

            # If it's a directory, copy entire directory
            if local_path.is_dir():
                source_install = local_path / "install.py"
                if not source_install.exists():
                    print(f"  ✗ install.py not found in: {local_path}")
                    return False

                print(f"  Copying plugin directory...")
                if install_dir.exists():
                    shutil.rmtree(install_dir)
                shutil.copytree(local_path, install_dir)
                print(f"  ✓ Copied directory")
            else:
                # Copy single file
                shutil.copy2(local_path, install_file)
                print(f"  ✓ Copied install.py")

        else:
            # Remote URL - download
            with urllib.request.urlopen(plugin_url) as response:
                content = response.read()

            with open(install_file, 'wb') as f:
                f.write(content)

            print(f"  ✓ Downloaded install.py")

        # Load the install module to run installation
        import importlib.util
        final_install_file = install_dir / "install.py"

        spec = importlib.util.spec_from_file_location(f"{tool_name}.install", final_install_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Run the install function
            if hasattr(module, 'install'):
                success = module.install(install_dir)
                if success:
                    print(f"\n✓ Successfully installed '{tool_name}' to {location} plugins")
                    return True
                else:
                    print(f"\n✗ Installation of '{tool_name}' failed")
                    return False
            else:
                print(f"  ✓ Plugin files copied (no install() function)")
                return True

    except Exception as e:
        print(f"\n✗ Error installing '{tool_name}': {e}")
        import traceback
        traceback.print_exc()
        # Clean up failed installation
        if install_dir.exists():
            shutil.rmtree(install_dir)
        return False


def install_all_tools(global_install: bool = False) -> bool:
    """
    Install all tools defined in raptor.toml.

    Args:
        global_install: If True, install to global plugins; if False, install to project plugins

    Returns:
        True if all installations succeeded
    """
    registry = load_plugins_registry()

    if not registry:
        print("No plugins defined in raptor.toml")
        print("\nAdd plugins to raptor.toml:")
        print("[plugins.plugin-name]")
        print('url = "https://... or /path/to/plugin"')
        print('description = "Plugin description"')
        return False

    print(f"Installing {len(registry)} plugin(s) from raptor.toml...\n")

    success_count = 0
    failed = []

    for tool_name in registry.keys():
        print(f"Installing '{tool_name}'...")
        if install_tool(tool_name, global_install):
            success_count += 1
        else:
            failed.append(tool_name)
        print()  # Blank line between installations

    # Summary
    print(f"\n{'='*60}")
    print(f"Installation Summary:")
    print(f"  ✓ Successful: {success_count}/{len(registry)}")
    if failed:
        print(f"  ✗ Failed: {', '.join(failed)}")
    print(f"{'='*60}")

    return len(failed) == 0


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
