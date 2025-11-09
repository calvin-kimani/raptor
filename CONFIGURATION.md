# Raptor Configuration Guide

This guide explains how to customize Raptor with your own templates and scripts.

## Configuration Files

Raptor uses two `raptor.toml` configuration files:

1. **Framework Configuration**: `~/.raptor/raptor.toml`
   - Global settings that apply to all projects
   - Your personal templates and scripts
   - Team-shared resources

2. **Project Configuration**: `<project>/raptor.toml`
   - Project-specific settings
   - Per-audit custom templates
   - Project-specific scripts

## Adding Custom Template Directories

### Framework-Level (Global)

Edit `~/.raptor/raptor.toml`:

```toml
[schemas]
# Default schema directories (don't modify these)
findings = "schemas/findings"
reports = "schemas/reports"

# Add your custom directories here
# Format: "type=path1:path2:path3" where type is findings/reports
additional_dirs = [
    "reports=~/my-custom-reports",
    "findings=~/my-custom-findings"
]
```

### Project-Level

Edit your project's `raptor.toml`:

```toml
[schemas]
# Project-specific custom schema directories
# Format: "type=path1:path2:path3" where type is findings/reports
additional_dirs = [
    "reports=./custom-templates",
    "findings=../shared-findings"
]
```

## Adding Custom Script Directories

### Framework-Level (Global)

Edit `~/.raptor/raptor.toml`:

```toml
[scripts]
# Default scripts directory (don't modify)
default_dir = "scripts"

# Add your custom directories here
additional_dirs = [
    "~/my-audit-scripts",
    "/path/to/team/scripts"
]
```

### Project-Level

Edit your project's `raptor.toml`:

```toml
[scripts]
# Project-specific custom script directories
additional_dirs = [
    "./scripts",
    "./tools"
]
```

## Managing Plugins

Raptor supports a plugin system for extending functionality. Plugins can be installed globally or per-project.

### Plugin Registry

Add plugins to your `raptor.toml`:

```toml
[plugins.plugin-name]
url = "https://raw.githubusercontent.com/user/repo/main/plugin/install.py"
version = ">=1.0.0"  # Optional version constraint
description = "Plugin description"
```

**Supported URL formats:**
- Remote: `https://raw.githubusercontent.com/...`
- Absolute local: `/absolute/path/to/plugin`
- Relative local: `../relative/path/to/plugin`
- File URL: `file:///path/to/plugin`

**Version constraints (optional):**
- `"1.0.0"` or `"@1.0.0"` - Exact version
- `">=1.0.0"` - Minimum version
- `">1.0.0"` - Greater than version
- `"<=2.0.0"` - Maximum version
- `"<2.0.0"` - Less than version

### Framework-Level Plugins (Global)

Edit `~/.raptor/raptor.toml`:

```toml
[plugins.solidity-parser]
url = "https://raw.githubusercontent.com/user/solidity-parser/main/install.py"
version = ">=1.0.0"
description = "Solidity parser plugin"

[plugins.graph-builder]
url = "/usr/local/raptor-plugins/graph-builder"
description = "Graph builder for contract analysis"
```

Install globally:
```bash
raptor plugins install solidity-parser --global
```

### Project-Level Plugins

Edit your project's `raptor.toml`:

```toml
[plugins.custom-analyzer]
url = "./plugins/custom-analyzer"
version = "1.0.0"
description = "Project-specific analyzer"
```

Install to project:
```bash
raptor plugins install custom-analyzer
```

### Multi-Version Support

Raptor allows multiple versions of the same plugin:

```bash
# Install version 1.0.0 (becomes active)
raptor plugins install solidity-parser

# Install version 1.1.0 (1.0.0 remains active)
raptor plugins install solidity-parser

# Switch active version
raptor plugins switch solidity-parser 1.1.0
```

Plugin directories:
- Project: `<project>/.plugins/plugin-name/version/`
- Global: `~/.raptor/bin/cli/plugins/plugin-name/version/`

### Plugin Lock File

The `.plugins.lock` file tracks installed plugins:

```json
{
  "version": "1",
  "plugins": {
    "solidity-parser": {
      "1.0.0": {
        "source": "explicit",
        "location": "project",
        "installed_by": null,
        "dependencies": [],
        "active": false
      },
      "1.1.0": {
        "source": "explicit",
        "location": "project",
        "installed_by": null,
        "dependencies": ["graph-builder>=1.0.0"],
        "active": true
      }
    }
  }
}
```

**Lock file fields:**
- `source`: "explicit" (user-installed) or "dependency" (auto-installed)
- `location`: "project" or "global"
- `installed_by`: Parent plugin if installed as dependency
- `dependencies`: List of required plugins with version constraints
- `active`: Whether this version is currently active

### Plugin Dependencies

Plugins can declare dependencies in their `install.py`:

```python
TOOL_INFO = {
    "name": "boundary-analyzer",
    "version": "1.0.0",
    "depends_on": ["solidity-parser>=1.0.0", "graph-builder>=1.0.0"],
}
```

Dependencies are automatically installed when you install the plugin.

## Path Resolution

Raptor resolves paths as follows:

- **Absolute paths** (starting with `/` or `~`): Used as-is
  ```toml
  additional_dirs = ["~/templates", "/usr/local/raptor-templates"]
  ```

- **Relative paths** in framework config: Relative to `~/.raptor/`
  ```toml
  additional_dirs = ["my-templates"]  # Resolves to ~/.raptor/my-templates
  ```

- **Relative paths** in project config: Relative to project root
  ```toml
  additional_dirs = ["./templates"]  # Resolves to <project>/templates
  ```

## Search Order

When Raptor looks for templates or scripts, it searches in this order:

1. **Project additional directories** (most specific)
2. **Framework additional directories** (your custom additions)
3. **Framework default directories** (built-in templates)

This means project-specific templates override framework templates.

## Example: Custom Report Format

Let's say you want to add a custom report format for "MyPlatform":

1. Create template directory:
   ```bash
   mkdir -p ~/my-templates/reports
   ```

2. Create template file:
   ```bash
   cat > ~/my-templates/reports/myplatform-report.yml << 'EOF'
   name: MyPlatform Finding
   description: Custom platform report template
   # ... your template content ...
   EOF
   ```

3. Register the directory in `~/.raptor/raptor.toml`:
   ```toml
   [schemas]
   additional_dirs = ["reports=~/my-templates/reports"]
   ```

4. Now you can use it:
   ```bash
   raptor report --format myplatform
   ```

## Example: Custom Audit Script

1. Create script directory:
   ```bash
   mkdir -p ~/my-audit-tools
   ```

2. Create your script:
   ```bash
   cat > ~/my-audit-tools/analyze-contract.sh << 'EOF'
   #!/bin/bash
   # Custom analysis script
   echo "Running custom analysis..."
   # Your custom logic here
   EOF
   chmod +x ~/my-audit-tools/analyze-contract.sh
   ```

3. Register in `~/.raptor/raptor.toml`:
   ```toml
   [scripts]
   additional_dirs = ["~/my-audit-tools"]
   ```

4. Access from any project:
   ```bash
   # Get raptor installation path from project config
   RAPTOR_ROOT=$(grep installation_path raptor.toml | cut -d'"' -f2)

   # Or use your scripts directly since they're in additional_dirs
   ~/my-audit-tools/analyze-contract.sh
   ```

## Sharing Templates with Your Team

For team collaboration:

1. Create a shared repository:
   ```bash
   git clone https://github.com/yourteam/audit-templates.git ~/team-templates
   ```

2. Each team member adds to their `~/.raptor/raptor.toml`:
   ```toml
   [schemas]
   additional_dirs = [
       "reports=~/team-templates/reports",
       "findings=~/team-templates/findings"
   ]
   ```

3. Update templates:
   ```bash
   cd ~/team-templates && git pull
   ```

## Project-Specific Templates

For one-off custom templates in a specific audit:

1. Create template directory in your project:
   ```bash
   mkdir -p custom-templates/reports
   ```

2. Add template file
3. Update project's `raptor.toml`:
   ```toml
   [schemas]
   additional_dirs = ["reports=./custom-templates/reports"]
   ```

4. These templates are only available in this project

## Best Practices

1. **Use framework config** for personal/team-wide templates
2. **Use project config** for audit-specific customizations
3. **Use absolute paths** for shared resources
4. **Use relative paths** for portable project templates
5. **Version control** your custom templates in a separate repo
6. **Document** custom templates for your team

## Troubleshooting

**Template not found?**
- Check path exists: `ls ~/my-templates`
- Verify path in raptor.toml: `cat ~/.raptor/raptor.toml`
- Check file name matches exactly

**Script not found?**
- Ensure script is executable: `chmod +x script.sh`
- Verify path in raptor.toml
- Use absolute path to test: `/full/path/to/script.sh`

**Changes not taking effect?**
- Raptor reads config on each run (no restart needed)
- Check for TOML syntax errors
- Ensure paths don't have typos
