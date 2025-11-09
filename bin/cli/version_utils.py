"""
Version parsing and comparison utilities for plugin dependencies.
"""

import re
from typing import Tuple, Optional


class Version:
    """Simple semantic version parsing and comparison."""

    def __init__(self, version_string: str):
        """
        Parse a version string.

        Args:
            version_string: Version in format "major.minor.patch" or "major.minor"
        """
        self.original = version_string
        parts = version_string.split('.')

        try:
            self.major = int(parts[0]) if len(parts) > 0 else 0
            self.minor = int(parts[1]) if len(parts) > 1 else 0
            self.patch = int(parts[2]) if len(parts) > 2 else 0
        except (ValueError, IndexError):
            raise ValueError(f"Invalid version string: {version_string}")

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self):
        return f"Version('{self}')"

    def __eq__(self, other):
        if not isinstance(other, Version):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __lt__(self, other):
        if not isinstance(other, Version):
            raise TypeError(f"Cannot compare Version with {type(other)}")
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        if not isinstance(other, Version):
            raise TypeError(f"Cannot compare Version with {type(other)}")
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other):
        return self == other or self > other


def parse_dependency_spec(dep_spec: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Parse a dependency specification string.

    Supports formats:
    - "plugin-name" -> (plugin-name, None, None)
    - "plugin-name>=1.0.0" -> (plugin-name, ">=", "1.0.0")
    - "plugin-name@1.0.0" -> (plugin-name, "==", "1.0.0")
    - "plugin-name==1.0.0" -> (plugin-name, "==", "1.0.0")
    - "plugin-name>1.0.0" -> (plugin-name, ">", "1.0.0")
    - "plugin-name<2.0.0" -> (plugin-name, "<", "2.0.0")
    - "plugin-name<=2.0.0" -> (plugin-name, "<=", "2.0.0")

    Args:
        dep_spec: Dependency specification string

    Returns:
        Tuple of (plugin_name, operator, version)
    """
    # Pattern to match: name [operator] [version]
    pattern = r'^([a-zA-Z0-9_-]+)\s*(@|>=|>|<=|<|==)?\s*([0-9.]+)?$'
    match = re.match(pattern, dep_spec.strip())

    if not match:
        # No version specified
        return (dep_spec.strip(), None, None)

    name, operator, version = match.groups()

    # Convert @ to ==
    if operator == '@':
        operator = '=='

    return (name, operator, version)


def check_version_constraint(installed_version: str, operator: str, required_version: str) -> bool:
    """
    Check if an installed version satisfies a version constraint.

    Args:
        installed_version: Currently installed version
        operator: Comparison operator (==, >=, >, <=, <)
        required_version: Required version

    Returns:
        True if constraint is satisfied
    """
    try:
        installed = Version(installed_version)
        required = Version(required_version)
    except ValueError as e:
        print(f"Warning: Invalid version format: {e}")
        return True  # Be lenient with version checking

    if operator == '==':
        return installed == required
    elif operator == '>=':
        return installed >= required
    elif operator == '>':
        return installed > required
    elif operator == '<=':
        return installed <= required
    elif operator == '<':
        return installed < required
    else:
        print(f"Warning: Unknown operator '{operator}', skipping version check")
        return True


def format_dependency_spec(name: str, operator: Optional[str], version: Optional[str]) -> str:
    """
    Format a dependency specification for display.

    Args:
        name: Plugin name
        operator: Version operator
        version: Version string

    Returns:
        Formatted dependency string
    """
    if operator and version:
        return f"{name}{operator}{version}"
    return name
