"""
Plugin lock file management for tracking installed plugins and dependencies.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class PluginLock:
    """Manages the .plugins.lock file for tracking installed plugins."""

    def __init__(self, project_dir: Path = None):
        """
        Initialize plugin lock manager.

        Args:
            project_dir: Project directory (default: current directory)
        """
        self.project_dir = project_dir or Path.cwd()
        self.lock_file = self.project_dir / ".plugins.lock"
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load lock file or create default structure."""
        if self.lock_file.exists():
            try:
                with open(self.lock_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load .plugins.lock: {e}")
                return self._default_structure()
        return self._default_structure()

    def _default_structure(self) -> Dict[str, Any]:
        """Return default lock file structure."""
        return {
            "version": "1",
            "plugins": {}
        }

    def _save(self):
        """Save lock file to disk."""
        with open(self.lock_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def is_installed(self, plugin_name: str, version: Optional[str] = None) -> bool:
        """
        Check if plugin is already installed.

        Args:
            plugin_name: Name of the plugin
            version: Specific version to check (optional, checks any version)

        Returns:
            True if plugin is installed
        """
        if plugin_name not in self.data["plugins"]:
            return False

        if version is None:
            # Check if any version is installed
            return len(self.data["plugins"][plugin_name]) > 0
        else:
            # Check if specific version is installed
            return version in self.data["plugins"][plugin_name]

    def get_plugin(self, plugin_name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get plugin information from lock file.

        Args:
            plugin_name: Name of the plugin
            version: Specific version (optional, returns active/latest version)

        Returns:
            Plugin info or None
        """
        if plugin_name not in self.data["plugins"]:
            return None

        versions = self.data["plugins"][plugin_name]
        if not versions:
            return None

        if version:
            return versions.get(version)
        else:
            # Return the active version or the latest installed
            for v, info in versions.items():
                if info.get('active', False):
                    return info
            # If no active, return first one
            return next(iter(versions.values()))

    def get_installed_versions(self, plugin_name: str) -> List[str]:
        """
        Get all installed versions of a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            List of installed version strings
        """
        if plugin_name not in self.data["plugins"]:
            return []
        return list(self.data["plugins"][plugin_name].keys())

    def add_plugin(
        self,
        plugin_name: str,
        version: str,
        source: str,
        location: str,
        installed_by: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        active: bool = True
    ):
        """
        Add or update plugin in lock file.

        Args:
            plugin_name: Name of the plugin
            version: Plugin version
            source: Where plugin came from ("local", "global", "dependency")
            location: Installation location ("project" or "global")
            installed_by: Parent plugin if this was installed as dependency
            dependencies: List of plugin dependencies
            active: Whether this version is the active one
        """
        if plugin_name not in self.data["plugins"]:
            self.data["plugins"][plugin_name] = {}

        # If setting this version as active, deactivate others
        if active:
            for v in self.data["plugins"][plugin_name].values():
                v['active'] = False

        self.data["plugins"][plugin_name][version] = {
            "source": source,
            "location": location,
            "installed_by": installed_by,
            "dependencies": dependencies or [],
            "active": active
        }
        self._save()

    def remove_plugin(self, plugin_name: str, version: Optional[str] = None):
        """
        Remove plugin from lock file.

        Args:
            plugin_name: Name of the plugin
            version: Specific version to remove (optional, removes all)
        """
        if plugin_name not in self.data["plugins"]:
            return

        if version:
            # Remove specific version
            if version in self.data["plugins"][plugin_name]:
                del self.data["plugins"][plugin_name][version]
                # If no versions left, remove plugin entry
                if not self.data["plugins"][plugin_name]:
                    del self.data["plugins"][plugin_name]
        else:
            # Remove all versions
            del self.data["plugins"][plugin_name]

        self._save()

    def set_active_version(self, plugin_name: str, version: str):
        """
        Set a specific version as the active one.

        Args:
            plugin_name: Name of the plugin
            version: Version to activate
        """
        if plugin_name not in self.data["plugins"]:
            return

        if version not in self.data["plugins"][plugin_name]:
            return

        # Deactivate all versions
        for v in self.data["plugins"][plugin_name].values():
            v['active'] = False

        # Activate specified version
        self.data["plugins"][plugin_name][version]['active'] = True
        self._save()

    def get_active_version(self, plugin_name: str) -> Optional[str]:
        """
        Get the active version of a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Active version string or None
        """
        if plugin_name not in self.data["plugins"]:
            return None

        for version, info in self.data["plugins"][plugin_name].items():
            if info.get('active', False):
                return version

        # If no active, return first one
        versions = list(self.data["plugins"][plugin_name].keys())
        return versions[0] if versions else None

    def get_dependents(self, plugin_name: str) -> List[str]:
        """
        Get list of plugins that depend on this plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            List of plugin names that depend on this plugin
        """
        dependents = []
        for name, versions in self.data["plugins"].items():
            for version, info in versions.items():
                deps = info.get("dependencies", [])
                # Check if plugin_name is in dependencies (with or without version spec)
                for dep in deps:
                    dep_name = dep.split('>=')[0].split('>')[0].split('<=')[0].split('<')[0].split('==')[0].split('@')[0]
                    if dep_name == plugin_name:
                        dependents.append(f"{name}@{version}")
                        break
        return dependents

    def is_dependency(self, plugin_name: str, version: Optional[str] = None) -> bool:
        """
        Check if plugin was installed as a dependency.

        Args:
            plugin_name: Name of the plugin
            version: Specific version (optional)

        Returns:
            True if installed as dependency
        """
        plugin_info = self.get_plugin(plugin_name, version)
        if not plugin_info:
            return False
        return plugin_info.get("installed_by") is not None

    def get_all_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Get all installed plugins."""
        return self.data["plugins"]
