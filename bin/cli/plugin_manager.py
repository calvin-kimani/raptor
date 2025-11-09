"""
Plugin/Tool discovery and management system.

Downloads install.py files from remote URLs and lets them handle plugin installation.
"""

from pathlib import Path
from typing import Dict, Optional, Any, List
import importlib.util
import sys
import urllib.request
import json

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python
    except ImportError:
        import toml as tomllib  # Fallback to toml package

from .plugin_lock import PluginLock
from .version_utils import parse_dependency_spec, check_version_constraint, format_dependency_spec


def load_plugins_registry() -> Dict[str, Dict[str, str]]:
    """
    Load plugin registry from raptor.toml.

    Expected format in raptor.toml:
    [plugins.plugin_name]
    url = "https://raw.githubusercontent.com/.../install.py"
    version = "1.0.0"  # Optional: can use ">=1.0.0", "@1.2.0", etc.
    description = "Plugin description"

    Returns:
        Dict mapping plugin name to plugin info (url, version, description)
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
                plugins[plugin_name] = {
                    'url': plugin_config['url'],
                    'version': plugin_config.get('version'),  # Optional
                    'description': plugin_config.get('description', '')
                }

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

    With multi-version support, only loads the active version of each plugin.

    Returns:
        Dict mapping tool name to tool module with source information
    """
    tools = {}
    lock = PluginLock()

    # Priority 1: Project-specific plugins
    project_plugins_dir = Path.cwd() / ".plugins"
    if project_plugins_dir.exists():
        for plugin_path in project_plugins_dir.iterdir():
            if plugin_path.is_dir() and not plugin_path.name.startswith('_'):
                plugin_name = plugin_path.name

                # Get active version from lock file
                active_version = lock.get_active_version(plugin_name)
                if not active_version:
                    # Fallback: try loading from plugin_path directly (legacy single-version)
                    install_file = plugin_path / "install.py"
                else:
                    # Load from version-specific directory
                    install_file = plugin_path / active_version / "install.py"

                if install_file.exists():
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
                                module._plugin_path = str(install_file.parent)
                                module._plugin_version = active_version or module.TOOL_INFO.get('version', '0.0.0')
                                tools[module.TOOL_INFO['name']] = module
                    except Exception as e:
                        print(f"Warning: Could not load project plugin '{plugin_name}': {e}")

    # Priority 2: Global plugins (raptor installation)
    global_plugins_dir = Path(__file__).parent / "plugins"
    if global_plugins_dir.exists():
        for plugin_path in global_plugins_dir.iterdir():
            if plugin_path.is_dir() and not plugin_path.name.startswith('_'):
                plugin_name = plugin_path.name

                # Check if already loaded from project
                if any(mod.TOOL_INFO.get('name') == plugin_name for mod in tools.values()
                       if hasattr(mod, 'TOOL_INFO')):
                    continue

                # Get active version from lock file
                active_version = lock.get_active_version(plugin_name)
                if not active_version:
                    # Fallback: try loading from plugin_path directly (legacy single-version)
                    install_file = plugin_path / "install.py"
                else:
                    # Load from version-specific directory
                    install_file = plugin_path / active_version / "install.py"

                if install_file.exists():
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
                                module._plugin_path = str(install_file.parent)
                                module._plugin_version = active_version or module.TOOL_INFO.get('version', '0.0.0')
                                tools[module.TOOL_INFO['name']] = module
                    except Exception as e:
                        print(f"Warning: Could not load global plugin '{plugin_name}': {e}")

    # Priority 3: Remote plugins from raptor.toml (don't auto-download, just show available)
    # These are shown in list but not automatically loaded - user must install them first

    return tools


def list_tools() -> None:
    """List all available tools with version information."""
    tools = discover_tools()
    lock = PluginLock()

    if not tools:
        print("No tools available")
        return

    print("\nAvailable tools:\n")

    for tool_name, module in tools.items():
        info = module.TOOL_INFO
        source = getattr(module, '_plugin_source', 'unknown')
        active_version = getattr(module, '_plugin_version', info.get('version', '0.0.0'))

        # Show source indicator
        source_indicator = {
            'project': '[Project]',
            'global': '[Global]',
            'remote': '[Remote]',
        }.get(source, '')

        # Get all installed versions
        installed_versions = lock.get_installed_versions(tool_name)
        version_display = f"v{active_version}"
        if len(installed_versions) > 1:
            version_display += f" ({len(installed_versions)} versions)"

        print(f"  {tool_name:20s} {source_indicator:10s} {version_display:15s} - {info['description']}")

        # Check installation status
        if hasattr(module, 'check'):
            statuses = module.check()
            installed_count = sum(1 for installed in statuses.values() if installed)
            total_count = len(statuses)

            if installed_count == total_count:
                print(f"  {'':20s} {'':10s} {'':15s}   ✓ Installed")
            elif installed_count > 0:
                print(f"  {'':20s} {'':10s} {'':15s}   ⚠ Partially installed ({installed_count}/{total_count})")
            else:
                print(f"  {'':20s} {'':10s} {'':15s}   ✗ Not installed")

        # Show all installed versions
        if len(installed_versions) > 1:
            active = lock.get_active_version(tool_name)
            versions_str = ", ".join([f"v{v}{'*' if v == active else ''}" for v in installed_versions])
            print(f"  {'':20s} {'':10s} {'':15s}   Versions: {versions_str}")

        print()


def install_tool(
    tool_name: str,
    global_install: bool = False,
    force: bool = False,
    installed_by: Optional[str] = None,
    _lock: Optional[PluginLock] = None,
    _url: Optional[str] = None
) -> bool:
    """
    Install a specific tool with dependency resolution.

    Supports multi-version installation: plugins are installed to version-specific
    directories (.plugins/plugin-name/version/).

    Args:
        tool_name: Name of the tool to install
        global_install: If True, install to global plugins; if False, install to project plugins
        force: If True, reinstall even if already installed
        installed_by: Parent plugin name if this is a dependency
        _lock: PluginLock instance (for internal use)
        _url: Optional URL to override registry lookup (for dependencies with URLs)

    Returns:
        True if installation succeeded
    """
    import urllib.request
    import shutil
    import tempfile

    # Initialize lock file manager
    if _lock is None:
        _lock = PluginLock()

    # Get plugin URL - either from parameter or registry
    if _url:
        # URL provided directly (from dependency spec)
        plugin_url = _url
        required_operator = None
        required_version = None
    else:
        # Check if plugin exists in raptor.toml
        registry = load_plugins_registry()

        if tool_name not in registry:
            print(f"Error: Unknown tool '{tool_name}'")
            print(f"\nAvailable tools in raptor.toml: {', '.join(registry.keys())}")
            return False

        # Get plugin info from registry
        plugin_info = registry[tool_name]
        plugin_url = plugin_info['url']
        required_version_spec = plugin_info.get('version')  # Optional version constraint

        # Parse version constraint if specified
        required_operator = None
        required_version = None
        if required_version_spec:
            _, required_operator, required_version, _ = parse_dependency_spec(f"{tool_name}{required_version_spec}")

    # Step 1: Download/copy plugin to temporary directory to get version from TOOL_INFO
    temp_dir = Path(tempfile.mkdtemp(prefix=f"raptor_plugin_{tool_name}_"))

    try:
        install_file = temp_dir / "install.py"

        # Download/copy to temporary location
        if plugin_url.startswith('file://'):
            # Remove file:// prefix
            local_path = Path(plugin_url[7:])
            if not local_path.exists():
                print(f"  ✗ Local file not found: {local_path}")
                shutil.rmtree(temp_dir)
                return False

            if local_path.is_dir():
                source_install = local_path / "install.py"
                if not source_install.exists():
                    print(f"  ✗ install.py not found in: {local_path}")
                    shutil.rmtree(temp_dir)
                    return False
                shutil.copytree(local_path, temp_dir, dirs_exist_ok=True)
            else:
                shutil.copy2(local_path, install_file)

        elif plugin_url.startswith('/') or plugin_url.startswith('./') or plugin_url.startswith('../'):
            # Local file path (absolute or relative)
            local_path = Path(plugin_url).expanduser().resolve()

            if not local_path.exists():
                print(f"  ✗ Local file not found: {local_path}")
                shutil.rmtree(temp_dir)
                return False

            if local_path.is_dir():
                source_install = local_path / "install.py"
                if not source_install.exists():
                    print(f"  ✗ install.py not found in: {local_path}")
                    shutil.rmtree(temp_dir)
                    return False
                shutil.copytree(local_path, temp_dir, dirs_exist_ok=True)
            else:
                shutil.copy2(local_path, install_file)

        else:
            # Remote URL - download
            with urllib.request.urlopen(plugin_url) as response:
                content = response.read()
            with open(install_file, 'wb') as f:
                f.write(content)

        # Step 2: Load install.py to get version from TOOL_INFO
        spec = importlib.util.spec_from_file_location(f"{tool_name}.install.temp", install_file)
        if not spec or not spec.loader:
            print(f"  ✗ Could not load install.py")
            shutil.rmtree(temp_dir)
            return False

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        tool_info = getattr(module, 'TOOL_INFO', {})
        plugin_version = tool_info.get('version', '0.0.0')
        dependencies = tool_info.get('depends_on', [])

        # Step 3: Check if this specific version is already installed
        if not force and _lock.is_installed(tool_name, plugin_version):
            installed_plugin = _lock.get_plugin(tool_name, plugin_version)

            # Check version constraint from raptor.toml
            if required_operator and required_version:
                if check_version_constraint(plugin_version, required_operator, required_version):
                    if not installed_by:
                        print(f"✓ '{tool_name}' v{plugin_version} is already installed (satisfies {required_operator}{required_version})")
                    shutil.rmtree(temp_dir)
                    return True
            else:
                if not installed_by:
                    print(f"✓ '{tool_name}' v{plugin_version} is already installed (use --force to reinstall)")
                shutil.rmtree(temp_dir)
                return True

        # Step 4: Determine version-specific installation directory
        location = "global" if global_install else "project"

        if global_install:
            base_dir = Path(__file__).parent / "plugins" / tool_name
        else:
            base_dir = Path.cwd() / ".plugins" / tool_name

        # Version-specific directory
        install_dir = base_dir / plugin_version

        if not installed_by:  # Only print for explicitly requested plugins
            print(f"Installing '{tool_name}' v{plugin_version} to {location} plugins...")
            print(f"  Source: {plugin_url}")
            print(f"  Target: {install_dir}")

        # Step 5: Copy plugin from temp to version-specific directory
        install_dir.parent.mkdir(parents=True, exist_ok=True)  # Create base plugin dir
        if install_dir.exists():
            shutil.rmtree(install_dir)
        shutil.copytree(temp_dir, install_dir)

        if not installed_by:
            print(f"  ✓ Copied plugin files")

        # Step 6: Auto-install dependencies first
        if dependencies and not installed_by:  # Only show message for explicit installs
            # Format dependencies for display
            dep_display = [format_dependency_spec(*parse_dependency_spec(d)) for d in dependencies]
            print(f"\n  Dependencies: {', '.join(dep_display)}")
            print(f"  Installing dependencies...")

        for dep_spec in dependencies:
            # Parse dependency specification (now returns 4-tuple with URL)
            dep_name, operator, dep_required_version, dep_url = parse_dependency_spec(dep_spec)

            # Check if dependency is already installed with compatible version
            if _lock.is_installed(dep_name) and not force:
                dep_info = _lock.get_plugin(dep_name)
                dep_installed_version = dep_info.get('version', '0.0.0')

                # Check version constraint
                if operator and dep_required_version:
                    if check_version_constraint(dep_installed_version, operator, dep_required_version):
                        if not installed_by:  # Only print for explicit installs
                            print(f"  ✓ Dependency '{dep_name}' already installed (v{dep_installed_version})")
                        continue
                    else:
                        if not installed_by:
                            print(f"  ⚠ Dependency '{dep_name}' version mismatch:")
                            print(f"    Installed: v{dep_installed_version}")
                            print(f"    Required: {operator}{dep_required_version}")
                            print(f"    Reinstalling...")
                else:
                    # No version constraint, already installed is fine
                    if not installed_by:
                        print(f"  ✓ Dependency '{dep_name}' already installed")
                    continue

            # Install or reinstall the dependency
            dep_success = install_tool(
                dep_name,
                global_install=global_install,
                force=True if (operator and dep_required_version and _lock.is_installed(dep_name)) else force,
                installed_by=tool_name,
                _lock=_lock,
                _url=dep_url  # Pass URL if provided in dependency spec
            )
            if not dep_success:
                print(f"  ✗ Failed to install dependency '{format_dependency_spec(dep_name, operator, dep_required_version, dep_url)}'")
                # Clean up failed installation
                if install_dir.exists():
                    shutil.rmtree(install_dir)
                shutil.rmtree(temp_dir)
                return False
            elif not installed_by:  # Only print for explicit installs
                version_suffix = f" (v{dep_required_version})" if dep_required_version else ""
                print(f"  ✓ Installed dependency '{dep_name}'{version_suffix}")

        # Step 6.5: Create dependency paths config file for this plugin
        dep_paths = {}
        for dep_spec in dependencies:
            dep_name, _, _, _ = parse_dependency_spec(dep_spec)
            # Get the installed dependency version and path
            dep_version = _lock.get_active_version(dep_name)
            if dep_version:
                dep_plugin_info = _lock.get_plugin(dep_name, dep_version)
                if dep_plugin_info:
                    dep_location = dep_plugin_info.get('location', 'project')

                    if dep_location == 'global':
                        dep_base = Path(__file__).parent / "plugins" / dep_name
                    else:
                        dep_base = Path.cwd() / ".plugins" / dep_name

                    dep_path = dep_base / dep_version
                    dep_paths[dep_name] = str(dep_path)

        # Write dependency paths to plugin directory
        if dep_paths:
            deps_config_file = install_dir / ".plugin_deps.json"
            with open(deps_config_file, 'w') as f:
                json.dump(dep_paths, f, indent=2)

        # Step 7: Run the install function
        if hasattr(module, 'install'):
            success = module.install(install_dir)
            if success:
                # Validate version constraint from raptor.toml
                if required_operator and required_version and not installed_by:
                    if not check_version_constraint(plugin_version, required_operator, required_version):
                        print(f"\n⚠ Warning: Installed version v{plugin_version} does not satisfy constraint {required_operator}{required_version}")
                        print(f"  The plugin may not work as expected")

                # Step 8: Update lock file - mark as active if this is the first/only version
                is_first_version = not _lock.is_installed(tool_name)
                source = "dependency" if installed_by else "explicit"
                _lock.add_plugin(
                    plugin_name=tool_name,
                    version=plugin_version,
                    source=source,
                    location=location,
                    installed_by=installed_by,
                    dependencies=dependencies,
                    active=is_first_version  # First version is automatically active
                )

                if not installed_by:  # Only print for explicit installs
                    active_msg = " (active)" if is_first_version else ""
                    print(f"\n✓ Successfully installed '{tool_name}' v{plugin_version}{active_msg} to {location} plugins")

                # Clean up temp directory
                shutil.rmtree(temp_dir)
                return True
            else:
                print(f"\n✗ Installation of '{tool_name}' failed")
                # Clean up both directories
                if install_dir.exists():
                    shutil.rmtree(install_dir)
                shutil.rmtree(temp_dir)
                return False
        else:
            # No install function, but plugin files copied
            is_first_version = not _lock.is_installed(tool_name)
            _lock.add_plugin(
                plugin_name=tool_name,
                version=plugin_version,
                source="dependency" if installed_by else "explicit",
                location=location,
                installed_by=installed_by,
                dependencies=dependencies,
                active=is_first_version
            )
            if not installed_by:
                print(f"  ✓ Plugin files copied (no install() function)")

            # Clean up temp directory
            shutil.rmtree(temp_dir)
            return True

    except Exception as e:
        print(f"\n✗ Error installing '{tool_name}': {e}")
        import traceback
        traceback.print_exc()
        # Clean up failed installation
        if install_dir.exists():
            shutil.rmtree(install_dir)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return False


def install_all_tools(global_install: bool = False, force: bool = False) -> bool:
    """
    Install all tools defined in raptor.toml.

    Args:
        global_install: If True, install to global plugins; if False, install to project plugins
        force: If True, reinstall even if already installed

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

    # Create shared lock instance
    lock = PluginLock()

    success_count = 0
    failed = []

    for tool_name in registry.keys():
        print(f"Installing '{tool_name}'...")
        if install_tool(tool_name, global_install, force=force, _lock=lock):
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


def switch_version(tool_name: str, version: str) -> bool:
    """
    Switch the active version of a plugin.

    Args:
        tool_name: Name of the plugin
        version: Version to activate

    Returns:
        True if switch succeeded
    """
    lock = PluginLock()

    # Check if plugin is installed
    if not lock.is_installed(tool_name):
        print(f"Error: Plugin '{tool_name}' is not installed")
        return False

    # Check if this specific version is installed
    if not lock.is_installed(tool_name, version):
        installed_versions = lock.get_installed_versions(tool_name)
        print(f"Error: Version '{version}' of '{tool_name}' is not installed")
        print(f"Installed versions: {', '.join(installed_versions)}")
        return False

    # Get current active version
    current_active = lock.get_active_version(tool_name)
    if current_active == version:
        print(f"✓ Version '{version}' is already the active version for '{tool_name}'")
        return True

    # Switch to new version
    lock.set_active_version(tool_name, version)
    print(f"✓ Switched '{tool_name}' from v{current_active} to v{version}")
    print(f"  Note: Restart any running processes to use the new version")
    return True


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
