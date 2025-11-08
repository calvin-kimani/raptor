# Raptor

Raptor is a framework for auditing blockchain ecosystem (contracts, protocols e.t.c).

## Overview

Raptor provides structured approaches and tools for identifying security vulnerabilities in smart contracts and blockchain protocols. The framework helps auditors document findings consistently and generate reports for multiple audit platforms.

## Installation

### curl

```bash
# Install latest stable version (recommended)
curl -sSL https://raw.githubusercontent.com/calvin-kimani/raptor/main/install.sh | bash

# Install specific version
curl -sSL https://raw.githubusercontent.com/calvin-kimani/raptor/main/install.sh | bash -s -- v0.1.0
curl -sSL https://raw.githubusercontent.com/calvin-kimani/raptor/main/install.sh | bash -s -- 0.1.0
```

### clone

```bash
# Latest stable
git clone https://github.com/calvin-kimani/raptor.git /tmp/raptor-install
bash /tmp/raptor-install/install.sh
rm -rf /tmp/raptor-install

# Specific version
git clone https://github.com/calvin-kimani/raptor.git /tmp/raptor-install
bash /tmp/raptor-install/install.sh v0.1.5
rm -rf /tmp/raptor-install
```

Then restart your shell or run:
```bash
source ~/.bashrc  # or ~/.zshrc for zsh
```

Verify installation:
```bash
raptor --version
```

## Updating Raptor

### Update to latest version

```bash
# Update to latest stable version
raptor update

# Update to specific version
raptor update v0.2.5
raptor update 0.2.5
```

### Upgrade to major version

```bash
# Upgrade to latest major version
raptor upgrade

# Upgrade to specific major version
raptor upgrade v1.0.0
```

### Downgrade

```bash
# Downgrade to previous version
raptor downgrade v0.1.0
```

### List available versions

```bash
# List all available versions
raptor version --list

# Show current version
raptor version --current
raptor --version
```

## Features

- **JSON-based Findings**: Store findings as structured JSON following a defined schema
- **Multi-platform Reports**: Generate reports for Sherlock, Code4rena, and CodeHawks
- **Git Integration**: Clone target repositories directly during project initialization
- **Flexible Workflow**: Create findings and generate reports independently or together

## File Structure

```
raptor/
├── bin/                   # CLI executables and modules
│   ├── raptor            # Main Raptor CLI executable
│   └── cli/              # CLI module code
│       ├── __init__.py   # Version info
│       ├── config.py     # Configuration management
│       ├── finding.py    # Finding management
│       ├── git.py        # Git repository management
│       ├── init.py       # Project initialization
│       ├── report.py     # Report generation
│       ├── raptor.py     # Main CLI logic
│       └── update.py     # Version management
├── scripts/              # Custom user scripts directory
├── schemas/              # Report templates and finding schemas
│   ├── reports/
│   │   ├── sherlock-report.yml   # Sherlock format template
│   │   ├── code4rena-report.yml  # Code4rena format template
│   │   └── codehawks-report.yml  # CodeHawks format template
│   └── findings/
│       └── finding-schema.json   # JSON schema for findings
├── CONFIGURATION.md      # Configuration guide
├── CONTRIBUTING.md       # Contribution guidelines
├── install.sh            # Installation script
├── raptor.toml           # Framework configuration
└── README.md             # This file
```

## Report Templates

Raptor supports generating reports for multiple audit platforms:

- **Sherlock**: Community-driven audit contests
- **Code4rena**: Competitive audit platform
- **CodeHawks**: Cyfrin's audit platform

Each platform has specific formatting requirements. Raptor stores findings in a structured JSON format and transforms them into the appropriate markdown format for each platform.

**Template locations:**
- Framework templates: `~/.raptor/schemas/reports/`
- Project templates: `<project>/audits/reports/.templates/`
- Custom templates: Configurable via `raptor.toml`

See [CONFIGURATION.md](CONFIGURATION.md) for adding custom report formats.

## Usage

### CLI Tool

Raptor provides a command-line interface for managing audit projects:

```bash
# Initialize a new audit project
raptor init my-audit

# Force overwrite existing directory
raptor init my-audit --force

# Clone repositories during init (shallow by default)
raptor init --git-url https://github.com/user/repo.git

# Clone multiple repos with full commit history
raptor init --git-url URL1 URL2 --commit

# Add repositories to existing project (shallow by default)
raptor git add https://github.com/user/repo.git

# Add multiple repos with full history
raptor git add URL1 URL2 --commit

# List all repositories in src/
raptor git list

# Update all repositories
raptor git update

# Update specific repositories
raptor git update repo1 repo2

# Remove repositories
raptor git remove repo-name

# Create a new finding (stored as JSON)
raptor finding --new "Attacker will drain funds from stakers" --severity HIGH

# Create finding and immediately generate reports
raptor finding --new "Reentrancy in withdraw" --severity CRITICAL --report sherlock code4rena

# Generate reports for all findings (default: sherlock format)
raptor report

# Generate reports in specific formats
raptor report --format sherlock code4rena codehawks

# Generate report for specific finding
raptor report --format sherlock --finding HIGH-reentrancy-attack
```

**Key Features:**
- **JSON-based findings**: All findings are stored as JSON following a structured schema
- **Multiple report formats**: Generate reports for Sherlock, Code4rena, and CodeHawks platforms
- **Git integration**: Clone repositories with `--git-url` or manage them with `raptor git` commands
- **Shallow clones**: By default, repos are cloned with `--depth 1` for faster downloads
- **Flexible reporting**: Generate reports for all findings or specific ones

## Example Workflow

1. Initialize a new audit project with `raptor init my-audit`
2. Clone target contract repo with `raptor git add https://github.com/user/repo.git`
3. Analyze the code and identify vulnerabilities
4. Document findings using `raptor finding --new "Title" --severity HIGH`
5. Generate platform-specific reports with `raptor report --format sherlock code4rena`
6. Submit reports to the appropriate audit platform

## Configuration

See [CONFIGURATION.md](CONFIGURATION.md) for detailed configuration guide.

## Contributing

Please read our [Contributing Guide](CONTRIBUTING.md).

### Code of Conduct

Please be respectful and professional in all interactions. We're all here to learn and improve the project together.

## Future Enhancements

- Additional report platform templates
- Automated finding validation
- Integration with popular security tools
- Enhanced CLI features

## License

Licensed under either of [Apache License](./LICENSE-APACHE), Version 2.0 or [MIT License](./LICENSE-MIT) at your option.

Unless you explicitly state otherwise, any contribution intentionally submitted for inclusion in these crates by you, as defined in the Apache-2.0 license,
shall be dual licensed as above, without any additional terms or conditions.

## Disclaimer

This framework is for educational and authorized security testing purposes only. Always obtain proper authorization before conducting security audits.