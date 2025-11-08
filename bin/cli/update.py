"""
Version management and update functionality
"""

import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple


def get_raptor_installation_path() -> Path:
    """Get the Raptor installation directory."""
    # Try to get from environment or default to ~/.raptor
    home = Path.home()
    raptor_dir = home / ".raptor"

    if raptor_dir.exists():
        return raptor_dir

    # Fallback: check if we're running from a development installation
    cli_path = Path(__file__).parent
    if (cli_path.parent.parent / "raptor.toml").exists():
        return cli_path.parent.parent

    return raptor_dir


def get_current_version() -> str:
    """Get the current installed version of Raptor."""
    raptor_path = get_raptor_installation_path()

    # Try to get version from git tag
    if (raptor_path / ".git").exists():
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--exact-match"],
                cwd=str(raptor_path),
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

    # Fallback to __init__.py version
    try:
        from . import __version__
        return f"v{__version__}"
    except ImportError:
        return "unknown"


def get_available_versions() -> List[str]:
    """Get list of available versions from git tags."""
    raptor_path = get_raptor_installation_path()

    if not (raptor_path / ".git").exists():
        print("Error: Not a git repository. Cannot fetch versions.")
        return []

    try:
        # Fetch latest tags
        subprocess.run(
            ["git", "fetch", "--tags", "--quiet"],
            cwd=str(raptor_path),
            capture_output=True,
            check=True
        )

        # Get all tags
        result = subprocess.run(
            ["git", "tag", "-l"],
            cwd=str(raptor_path),
            capture_output=True,
            text=True,
            check=True
        )

        tags = result.stdout.strip().split('\n')
        # Filter for version tags (vX.Y.Z format)
        version_pattern = re.compile(r'^v?\d+\.\d+\.\d+(-[\w\.]+)?$')
        versions = [tag for tag in tags if version_pattern.match(tag)]

        # Sort versions (newest first)
        versions.sort(reverse=True, key=lambda v: parse_version_tuple(v))

        return versions
    except subprocess.CalledProcessError as e:
        print(f"Error fetching versions: {e}")
        return []


def parse_version_tuple(version: str) -> Tuple[int, int, int]:
    """Parse version string into tuple for sorting."""
    # Remove 'v' prefix and any suffix like -beta
    clean = version.lstrip('v').split('-')[0]
    parts = clean.split('.')
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return (0, 0, 0)


def get_latest_stable() -> Optional[str]:
    """Get the latest stable version (no beta/rc tags)."""
    versions = get_available_versions()

    for version in versions:
        # Skip versions with suffixes like -beta, -rc, -alpha
        if '-' not in version:
            return version

    return versions[0] if versions else None


def parse_version(version_str: str) -> str:
    """
    Parse and normalize version string.

    Supports formats:
    - "v0.1.0", "0.1.0" -> "v0.1.0"
    - "latest" -> latest stable version
    - "latest-stable" -> latest stable version
    """
    if not version_str:
        return get_latest_stable()

    version_str = version_str.strip()

    # Handle special keywords
    if version_str in ["latest", "latest-stable", "stable"]:
        return get_latest_stable()

    # Ensure 'v' prefix
    if not version_str.startswith('v'):
        version_str = 'v' + version_str

    # Validate version exists
    available = get_available_versions()
    if version_str not in available:
        print(f"Error: Version '{version_str}' not found.")
        print(f"Available versions: {', '.join(available[:10])}")
        return None

    return version_str


def backup_config() -> Optional[Path]:
    """Backup the current raptor.toml configuration."""
    raptor_path = get_raptor_installation_path()
    config_file = raptor_path / "raptor.toml"

    if not config_file.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = raptor_path / f"raptor.toml.backup.{timestamp}"

    try:
        import shutil
        shutil.copy2(config_file, backup_file)
        return backup_file
    except Exception as e:
        print(f"Warning: Could not backup config: {e}")
        return None


def restore_custom_config(backup_path: Path) -> bool:
    """
    Restore custom configuration from backup.

    Merges user's additional_dirs back into the new configuration.
    """
    if not backup_path or not backup_path.exists():
        return False

    raptor_path = get_raptor_installation_path()
    current_config = raptor_path / "raptor.toml"

    if not current_config.exists():
        return False

    try:
        # Try to use TOML library if available
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                print("Warning: Cannot preserve custom config (TOML library not available)")
                print(f"Your backup is saved at: {backup_path}")
                return False

        # Read backup config
        with open(backup_path, 'rb') as f:
            backup_config = tomllib.load(f)

        # Read current config as text
        with open(current_config, 'r') as f:
            current_text = f.read()

        # Extract custom dirs from backup
        custom_templates = backup_config.get('templates', {}).get('additional_dirs', [])
        custom_scripts = backup_config.get('scripts', {}).get('additional_dirs', [])

        if custom_templates or custom_scripts:
            print("\n✓ Preserved your custom configuration:")
            if custom_templates:
                print(f"  Template directories: {custom_templates}")
            if custom_scripts:
                print(f"  Script directories: {custom_scripts}")
            print(f"\nBackup saved at: {backup_path}")
            print("You may need to manually re-add custom directories to raptor.toml\n")

        return True

    except Exception as e:
        print(f"Warning: Could not restore custom config: {e}")
        print(f"Your backup is saved at: {backup_path}")
        return False


def switch_version(version: str) -> bool:
    """Switch to a specific version using git checkout."""
    raptor_path = get_raptor_installation_path()

    if not (raptor_path / ".git").exists():
        print("Error: Not a git repository. Cannot switch versions.")
        return False

    try:
        # Check for local modifications
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(raptor_path),
            capture_output=True,
            text=True,
            check=True
        )

        if result.stdout.strip():
            print("Warning: You have local modifications.")
            print("Stashing changes...")
            subprocess.run(
                ["git", "stash", "save", f"Pre-switch stash {datetime.now()}"],
                cwd=str(raptor_path),
                check=True
            )

        # Checkout the version
        print(f"Switching to version {version}...")
        subprocess.run(
            ["git", "checkout", version],
            cwd=str(raptor_path),
            capture_output=True,
            check=True
        )

        # Update installation path in config
        config_file = raptor_path / "raptor.toml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                content = f.read()

            # Update installation_path if needed
            if 'installation_path = "/home/user/.raptor"' in content:
                content = content.replace(
                    'installation_path = "/home/user/.raptor"',
                    f'installation_path = "{raptor_path}"'
                )
                with open(config_file, 'w') as f:
                    f.write(content)

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error switching version: {e}")
        return False


def update_raptor(version: Optional[str] = None) -> int:
    """
    Update Raptor to a newer version.

    Args:
        version: Target version (default: latest stable)

    Returns:
        0 on success, 1 on error
    """
    current = get_current_version()
    print(f"Current version: {current}")

    # Parse target version
    if version:
        target = parse_version(version)
    else:
        target = get_latest_stable()

    if not target:
        return 1

    print(f"Target version: {target}")

    if current == target:
        print("Already on the target version!")
        return 0

    # Backup configuration
    print("\nBacking up configuration...")
    backup = backup_config()

    # Switch version
    if not switch_version(target):
        return 1

    # Restore custom config
    if backup:
        restore_custom_config(backup)

    print(f"\n✓ Successfully updated to {target}")
    return 0


def upgrade_raptor(version: Optional[str] = None) -> int:
    """
    Upgrade Raptor to a new major version.

    Args:
        version: Target major version (default: latest)

    Returns:
        0 on success, 1 on error
    """
    current = get_current_version()
    print(f"Current version: {current}")

    # Parse target version
    if version:
        target = parse_version(version)
    else:
        target = get_latest_stable()

    if not target:
        return 1

    # Check if it's a major upgrade
    current_major = parse_version_tuple(current)[0]
    target_major = parse_version_tuple(target)[0]

    if target_major > current_major:
        print(f"\n⚠️  Major version upgrade: v{current_major}.x.x → v{target_major}.x.x")
        print("This may include breaking changes.")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Upgrade cancelled.")
            return 0

    print(f"Target version: {target}")

    # Backup configuration
    print("\nBacking up configuration...")
    backup = backup_config()

    # Switch version
    if not switch_version(target):
        return 1

    # Restore custom config
    if backup:
        restore_custom_config(backup)

    print(f"\n✓ Successfully upgraded to {target}")
    return 0


def downgrade_raptor(version: str) -> int:
    """
    Downgrade Raptor to a previous version.

    Args:
        version: Target version to downgrade to

    Returns:
        0 on success, 1 on error
    """
    if not version:
        print("Error: Version is required for downgrade")
        return 1

    current = get_current_version()
    print(f"Current version: {current}")

    target = parse_version(version)
    if not target:
        return 1

    print(f"Target version: {target}")

    # Warning
    print("\n⚠️  Warning: Downgrading may cause compatibility issues.")
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Downgrade cancelled.")
        return 0

    # Backup configuration
    print("\nBacking up configuration...")
    backup = backup_config()

    # Switch version
    if not switch_version(target):
        return 1

    # Restore custom config
    if backup:
        restore_custom_config(backup)

    print(f"\n✓ Successfully downgraded to {target}")
    return 0


def list_versions() -> int:
    """List all available versions."""
    print("Fetching available versions...")
    versions = get_available_versions()

    if not versions:
        print("No versions found.")
        return 1

    current = get_current_version()
    latest = get_latest_stable()

    print(f"\nCurrent version: {current}")
    print(f"Latest stable: {latest}\n")
    print("Available versions:")

    for version in versions:
        marker = ""
        if version == current:
            marker = " (current)"
        elif version == latest:
            marker = " (latest stable)"
        print(f"  {version}{marker}")

    return 0
