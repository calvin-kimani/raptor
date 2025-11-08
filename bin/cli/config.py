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


def get_template_dirs(config: Dict[str, Any]) -> List[Path]:
    """
    Get all template directories from configuration.

    Returns list of paths to search for templates, in order:
    1. Project template directories
    2. Framework additional template directories
    3. Framework default template directories
    """
    dirs = []
    raptor_root = get_raptor_root()

    # Get project-specific template directories
    if 'templates' in config and 'additional_dirs' in config['templates']:
        for dir_path in config['templates']['additional_dirs']:
            path = Path(dir_path).expanduser()
            if not path.is_absolute():
                # Relative to project root
                path = Path.cwd() / path
            if path.exists():
                dirs.append(path)

    # Get framework additional template directories
    # Load framework config separately to get framework-specific settings
    framework_config = load_toml(raptor_root / "raptor.toml")
    if 'templates' in framework_config and 'additional_dirs' in framework_config['templates']:
        for dir_path in framework_config['templates']['additional_dirs']:
            path = Path(dir_path).expanduser()
            if not path.is_absolute():
                # Relative to raptor installation
                path = raptor_root / path
            if path.exists():
                dirs.append(path)

    # Get framework default directories
    if 'templates' in framework_config:
        for key in ['reports', 'schemas', 'findings']:
            if key in framework_config['templates']:
                path = raptor_root / framework_config['templates'][key]
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
    """
    dirs = []
    raptor_root = get_raptor_root()

    # Get project-specific script directories
    if 'scripts' in config and 'additional_dirs' in config['scripts']:
        for dir_path in config['scripts']['additional_dirs']:
            path = Path(dir_path).expanduser()
            if not path.is_absolute():
                # Relative to project root
                path = Path.cwd() / path
            if path.exists():
                dirs.append(path)

    # Get framework additional script directories
    # Load framework config separately to get framework-specific settings
    framework_config = load_toml(raptor_root / "raptor.toml")
    if 'scripts' in framework_config and 'additional_dirs' in framework_config['scripts']:
        for dir_path in framework_config['scripts']['additional_dirs']:
            path = Path(dir_path).expanduser()
            if not path.is_absolute():
                # Relative to raptor installation
                path = raptor_root / path
            if path.exists():
                dirs.append(path)

    # Get framework default directory
    if 'scripts' in framework_config and 'default_dir' in framework_config['scripts']:
        path = raptor_root / framework_config['scripts']['default_dir']
        if path.exists():
            dirs.append(path)

    return dirs


def find_template(template_name: str, template_type: str = "reports") -> Path:
    """
    Find a template file by searching all configured template directories.

    Args:
        template_name: Name of template file (e.g., "sherlock-report.yml")
        template_type: Type of template ("reports", "schemas", "findings")

    Returns:
        Path to template file, or None if not found
    """
    config = load_config()
    template_dirs = get_template_dirs(config)

    for dir_path in template_dirs:
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
