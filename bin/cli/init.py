"""
Project initialization functionality
"""

import shutil
from pathlib import Path
from . import git as git_module


def get_raptor_root():
    """Get the Raptor framework root directory."""
    return Path(__file__).parent.parent.parent.absolute()


def init_project(project_name=None, force=False, git_urls=None, shallow=True):
    """Initialize a new Raptor audit project or clone repos to existing project."""

    # Check if we're in an existing Raptor project
    existing_project = (Path.cwd() / "raptor.toml").exists()

    # If only git_urls provided in an existing project, just clone the repos
    if git_urls and existing_project and not project_name:
        print("Adding repositories to existing Raptor project...")
        return git_module.add_repos(git_urls, shallow=shallow)

    # Otherwise, proceed with full initialization
    if project_name:
        project_path = Path.cwd() / project_name
        if project_path.exists():
            if force:
                print(f"Removing existing directory '{project_name}'...")
                shutil.rmtree(project_path)
            else:
                print(f"Error: Directory '{project_name}' already exists. Use --force to overwrite.")
                return 1
        project_path.mkdir(parents=True, exist_ok=True)
    else:
        project_path = Path.cwd()
        if list(project_path.iterdir()) and not force and not existing_project:
            response = input("Current directory is not empty. Continue? (y/n): ")
            if response.lower() != 'y':
                return 1

    print(f"Initializing Raptor audit project in {project_path}...")

    # Create directory structure
    dirs = [
        "src",                              # Contract source code to audit
        "audits",                           # Audit reports and findings
        "audits/findings",                  # Individual findings
        "audits/findings/.templates",       # Finding templates (hidden)
        "audits/reports",                   # Final reports
        "audits/reports/.templates",        # Report templates (hidden)
        "test",                             # PoC exploits and tests
        "notes",                            # Audit notes
    ]

    for dir_name in dirs:
        (project_path / dir_name).mkdir(parents=True, exist_ok=True)

    # Create raptor.toml config
    raptor_root = get_raptor_root()
    config = """[project]
name = "{project_name}"
version = "0.1.0"

[raptor]
# Location of Raptor framework installation
installation_path = "{raptor_path}"

[audit]
target = "src/"

[output]
findings_dir = "audits/findings"
reports_dir = "audits/reports"

[templates]
# Template locations (hidden from main directory)
findings_templates = "audits/findings/.templates"
reports_templates = "audits/reports/.templates"
schema = "audits/findings/.templates/finding-schema.json"

# Project-specific custom template directories
# Add additional directories here for project-specific templates
additional_dirs = [
    # "./custom-templates",
    # "/path/to/project/templates"
]

[scripts]
# Project-specific custom script directories
# Add additional directories here for project-specific scripts
additional_dirs = [
    # "./scripts",
    # "/path/to/project/scripts"
]

[test]
framework = "foundry"  # foundry, hardhat, or custom
""".format(
        project_name=project_name or project_path.name,
        raptor_path=str(raptor_root)
    )

    with open(project_path / "raptor.toml", "w") as f:
        f.write(config)

    # Create README template
    readme = """# {project_name} Audit

Raptor audit project for {project_name}.

## Structure

- `src/` - Contract source code under audit
- `audits/findings/` - Individual vulnerability findings (JSON format)
- `audits/reports/` - Generated audit reports (Markdown)
- `test/` - Proof of concept exploits
- `notes/` - Audit notes and analysis

## Usage

```bash
# Create a new finding
raptor finding --new "Attacker will drain funds" --severity HIGH

# Generate reports for all findings
raptor report

# Generate reports in specific formats
raptor report --format sherlock code4rena

# Review findings
ls audits/findings/
```

## Report Formats

This project supports generating reports for:
- Sherlock
- Code4rena
- CodeHawks
""".format(project_name=project_name or project_path.name)

    with open(project_path / "README.md", "w") as f:
        f.write(readme)

    # Create .gitignore
    gitignore = """# Raptor
notes/*.tmp
*.log

# Foundry
cache/
out/
broadcast/

# IDE
.vscode/
.idea/
*.swp
"""
    with open(project_path / ".gitignore", "w") as f:
        f.write(gitignore)

    # Copy templates to .templates directories (hidden from main view)
    raptor_root = get_raptor_root()

    # Copy finding schema to findings/.templates
    schema_src = raptor_root / "templates/schemas/finding-schema.json"
    if schema_src.exists():
        shutil.copy(schema_src, project_path / "audits/findings/.templates/finding-schema.json")

    # Copy report templates to reports/.templates
    templates_dir = raptor_root / "templates/reports"
    for template in ["sherlock-report.yml", "code4rena-report.yml", "codehawks-report.yml"]:
        template_src = templates_dir / template
        if template_src.exists():
            shutil.copy(template_src, project_path / "audits/reports/.templates" / template)

    # Create sample finding template (markdown format for reference)
    finding_template = """# [SEVERITY] {Actor} will {Impact} {Affected Party}

## Summary
**{Root cause} will cause [a/an] {impact} for {affected party} as {actor} will {attack path}**

Example: The missing check in `stake.sol` will cause a complete loss of funds for stakers as an attacker will frontrun their transactions

## Root Cause

### Code Issue
In `{contract}:{line}` the {root cause}

Example:
- In `stake.sol:551` there is a missing check on transfer function
- In `lp.sol:12` the fee calculation does division before multiplication which will revert the transaction on `lp.sol:18`

### Design Issue
The choice to {design choice} is a mistake as {root cause}

Example:
- The choice to use Uniswap as an oracle is a mistake as the price can be manipulated
- The choice to depend on Protocol X for admin calls is a mistake as it will cause any call to revert

## Internal Pre-conditions
1. {Role} needs to {action} to set {variable} to be [at least / at most / exactly / other than] {value}
2. {variable} to go from {value} to {value} [within {time}]

Example:
- Admin needs to call `setFee()` to set `fee` to be exactly `1 ETH`
- Number of ETH in the `stake.sol` contract to be at least `500 ETH`

## External Pre-conditions
1. {External protocol condition}

Example:
- ETH oracle needs to go from `4000` to `5000` within 2 minutes
- Gas price needs to be exactly `100 wei`

## Attack Path
1. {Role} calls {function} {extra context}
2. ...

Example:
1. The owner calls `decrease()` and sets `mintFee` to 0.03 ETH
2. The user calls `mint()` and uses an outdated version as he calls with 0.05 ETH as `msg.value` to pay the 0.03 ETH `mintFee`

## Impact
The {affected party} suffers an approximate loss of {value}. [The attacker gains {gain} or loses {loss}]

Example:
- The stakers suffer a 50% loss during staking. The attacker gains this 50% from stakers.
- The protocol suffers a `0.0006` ETH minting fee. The attacker loses their portion of the fee and doesn't gain anything (griefing).
- The users suffer an approximate loss of 0.01% due to precision loss.

## Proof of Concept
```solidity
// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity >=0.8.0;

import "forge-std/Test.sol";
// PoC code here
```

## Tool Used
Raptor Framework

## Mitigation
Recommended fixes to address the vulnerability.
"""
    with open(project_path / "audits/findings/.templates/TEMPLATE.md", "w") as f:
        f.write(finding_template)

    # Clone git repositories if provided (after project structure is created)
    if git_urls:
        import os
        original_cwd = Path.cwd()
        try:
            # Change to project directory to clone repos
            os.chdir(project_path)
            result = git_module.add_repos(git_urls, shallow=shallow)
            if result != 0:
                print("Warning: Some repositories failed to clone.")
        finally:
            # Change back to original directory
            os.chdir(original_cwd)

    print("✓ Project initialized successfully")
    print(f"\nNext steps:")
    if project_name:
        print(f"  cd {project_name}")
    if git_urls:
        print(f"  # Contracts cloned to src/")
    else:
        print(f"  # Add contracts to src/")
    print(f"  raptor finding --new \"Attacker will drain funds\" --severity HIGH")
    print(f"\nTemplates stored in:")
    print(f"  audits/findings/.templates/ - Finding templates and schema")
    print(f"  audits/reports/.templates/ - Report format templates")

    return 0
