"""
Configuration loading and management
"""

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for Python < 3.11
    except ImportError:
        # If neither available, provide basic TOML parsing
        tomllib = None

from pathlib import Path
from typing import Dict, List, Any


def get_raptor_root():
    """Get the Raptor framework root directory."""
    return Path(__file__).parent.parent.parent.absolute()


def load_toml(file_path: Path) -> Dict[str, Any]:
    """Load a TOML configuration file."""
    if not file_path.exists():
        return {}

    if tomllib is None:
        # Basic fallback: return empty config if TOML library not available
        print(f"Warning: TOML library not available. Install tomli or upgrade to Python 3.11+")
        return {}

    with open(file_path, 'rb') as f:
        return tomllib.load(f)


def load_config() -> Dict[str, Any]:
    """
    Load and merge Raptor configurations.

    Loads configurations in order:
    1. Framework raptor.toml (from installation)
    2. Project raptor.toml (from current directory)

    Returns merged configuration with project settings taking precedence.
    """
    config = {}

    # Load framework config
    framework_config_path = get_raptor_root() / "raptor.toml"
    if framework_config_path.exists():
        config = load_toml(framework_config_path)

    # Load project config
    project_config_path = Path.cwd() / "raptor.toml"
    if project_config_path.exists():
        project_config = load_toml(project_config_path)
        # Merge configs (project config takes precedence)
        config.update(project_config)

    return config


def get_schema_dirs(config: Dict[str, Any]) -> List[Path]:
    """
    Get all schema directories from configuration.

    Returns list of paths to search for schemas (findings/reports), in order:
    1. Project schema directories
    2. Framework additional schema directories
    3. Framework default schema directories

    Supports new format: "type=path1:path2" where type is reports/findings
    """
    dirs = []
    raptor_root = get_raptor_root()

    # Helper to parse additional_dirs entries
    def parse_schema_entry(entry: str, base_path: Path) -> List[tuple]:
        """Parse entry like 'reports=~/path1:~/path2' into (type, Path) tuples."""
        results = []
        if '=' in entry:
            # New format: "type=path1:path2"
            schema_type, paths_str = entry.split('=', 1)
            schema_type = schema_type.strip()
            for path_str in paths_str.split(':'):
                path_str = path_str.strip()
                if path_str:
                    path = Path(path_str).expanduser()
                    if not path.is_absolute():
                        path = base_path / path
                    if path.exists():
                        results.append((schema_type, path))
        else:
            # Legacy format: just a path (applies to all types)
            path = Path(entry).expanduser()
            if not path.is_absolute():
                path = base_path / path
            if path.exists():
                # Add for all schema types (reports, findings)
                for schema_type in ['reports', 'findings']:
                    results.append((schema_type, path))
        return results

    # Get project-specific schema directories
    if 'schemas' in config and 'additional_dirs' in config['schemas']:
        for entry in config['schemas']['additional_dirs']:
            for schema_type, path in parse_schema_entry(entry, Path.cwd()):
                dirs.append(path)

    # Get framework additional schema directories
    # Load framework config separately to get framework-specific settings
    framework_config = load_toml(raptor_root / "raptor.toml")
    if 'schemas' in framework_config and 'additional_dirs' in framework_config['schemas']:
        for entry in framework_config['schemas']['additional_dirs']:
            for schema_type, path in parse_schema_entry(entry, raptor_root):
                dirs.append(path)

    # Get framework default directories
    if 'schemas' in framework_config:
        for key in ['reports', 'findings']:
            if key in framework_config['schemas']:
                path = raptor_root / framework_config['schemas'][key]
                if path.exists():
                    dirs.append(path)

    return dirs


def get_script_dirs(config: Dict[str, Any]) -> List[Path]:
    """
    Get all script directories from configuration.

    Returns list of paths to search for scripts, in order:
    1. Project script directories
    2. Framework additional script directories
    3. Framework default script directory

    Supports new format: "type=path1:path2" where type identifies script category
    """
    dirs = []
    raptor_root = get_raptor_root()

    # Helper to parse additional_dirs entries
    def parse_script_entry(entry: str, base_path: Path) -> List[tuple]:
        """Parse entry like 'analysis=~/path1:~/path2' into (type, Path) tuples."""
        results = []
        if '=' in entry:
            # New format: "type=path1:path2"
            script_type, paths_str = entry.split('=', 1)
            script_type = script_type.strip()
            for path_str in paths_str.split(':'):
                path_str = path_str.strip()
                if path_str:
                    path = Path(path_str).expanduser()
                    if not path.is_absolute():
                        path = base_path / path
                    if path.exists():
                        results.append((script_type, path))
        else:
            # Legacy format: just a path (no specific type)
            path = Path(entry).expanduser()
            if not path.is_absolute():
                path = base_path / path
            if path.exists():
                results.append(('general', path))
        return results

    # Get project-specific script directories
    if 'scripts' in config and 'additional_dirs' in config['scripts']:
        for entry in config['scripts']['additional_dirs']:
            for script_type, path in parse_script_entry(entry, Path.cwd()):
                dirs.append(path)

    # Get framework additional script directories
    # Load framework config separately to get framework-specific settings
    framework_config = load_toml(raptor_root / "raptor.toml")
    if 'scripts' in framework_config and 'additional_dirs' in framework_config['scripts']:
        for entry in framework_config['scripts']['additional_dirs']:
            for script_type, path in parse_script_entry(entry, raptor_root):
                dirs.append(path)

    # Get framework default directory
    if 'scripts' in framework_config and 'default_dir' in framework_config['scripts']:
        path = raptor_root / framework_config['scripts']['default_dir']
        if path.exists():
            dirs.append(path)

    return dirs


def find_template(template_name: str, template_type: str = "reports") -> Path:
    """
    Find a template file by searching all configured schema directories.

    Args:
        template_name: Name of template file (e.g., "sherlock-report.yml")
        template_type: Type of template ("reports", "findings")

    Returns:
        Path to template file, or None if not found
    """
    config = load_config()
    schema_dirs = get_schema_dirs(config)

    for dir_path in schema_dirs:
        # Check if this directory contains the template type as a subdirectory
        if (dir_path / template_type).exists():
            template_path = dir_path / template_type / template_name
            if template_path.exists():
                return template_path

        # Check if this directory IS the template type directory
        if template_type in str(dir_path) or dir_path.name == template_type:
            template_path = dir_path / template_name
            if template_path.exists():
                return template_path

        # Also check direct path in directory
        template_path = dir_path / template_name
        if template_path.exists():
            return template_path

    return None


def find_script(script_name: str) -> Path:
    """
    Find a script file by searching all configured script directories.

    Args:
        script_name: Name of script file

    Returns:
        Path to script file, or None if not found
    """
    config = load_config()
    script_dirs = get_script_dirs(config)

    for dir_path in script_dirs:
        script_path = dir_path / script_name
        if script_path.exists():
            return script_path

    return None
