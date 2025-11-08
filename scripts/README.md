# Custom Scripts Directory

This directory is for your custom audit scripts and utilities.

## Purpose

Place your custom tools, automation scripts, or helper utilities here. These scripts can be referenced from any Raptor project via the `raptor.toml` configuration.

## Examples

- Custom static analysis scripts
- Automated test runners
- Report formatters
- Integration with other security tools

## Usage

1. Add your scripts to this directory
2. Make them executable: `chmod +x script_name.sh`
3. Reference them in your project's workflow

## Accessing from Projects

Each Raptor project's `raptor.toml` contains:
```toml
[raptor]
installation_path = "/path/to/.raptor"
```

This allows you to access these scripts from any project:
```bash
$RAPTOR_ROOT/scripts/your-script.sh
```
