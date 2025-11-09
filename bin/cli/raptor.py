"""
Raptor CLI - Main entry point
"""

import sys
import argparse
from . import __version__
from .init import init_project
from .finding import new_finding
from .report import generate_report
from . import git as git_module
from . import update as update_module
from . import plugin_manager as plugins


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Raptor - Smart Contract Audit Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  raptor init my-audit                   Initialize new audit project

  raptor init my-audit --force           Force overwrite existing directory

  raptor init --git-url https://github.com/user/repo.git
                                         Clone repo to src/ (shallow clone by default)
  
  raptor init --git-url URL1 URL2 --commit
                                         Clone multiple repos with full commit history
  
  raptor git add https://github.com/user/repo.git
                                         Add repository to existing project (shallow)
  
  raptor git add URL1 URL2 --commit      Add multiple repos with full history

  raptor git remove repo-name            Remove repository from src/

  raptor git update                      Update all repositories

  raptor git update repo1 repo2          Update specific repositories

  raptor git list                        List all repositories

  raptor finding --new "Attacker will drain funds" --severity HIGH
                                         Create a new finding
  raptor finding --new "Reentrancy" --severity CRITICAL --report sherlock code4rena
                                         Create finding and generate reports
  
  raptor report --format sherlock code4rena
                                         Generate reports for all findings
  
  raptor report --format codehawks --finding HIGH-reentrancy-attack
                                         Generate report for specific finding
  
  raptor update                          Update to latest stable version
  
  raptor update v0.2.5                   Update to specific version
  
  raptor upgrade                         Upgrade to latest major version
  
  raptor upgrade v1.0.0                  Upgrade to specific major version
  
  raptor downgrade v0.1.0                Downgrade to previous version
  
  raptor version --list                  List all available versions

  raptor version --current               Show current version

  raptor plugins --list                  List all available plugins
  raptor plugins -l                      (shorthand)

  raptor plugins install                 Install all plugins from raptor.toml
  raptor plugins -i                      (shorthand)

  raptor plugins install plugin1 plugin2 Install specific plugins
  raptor plugins -i plugin1 plugin2      (shorthand)

  raptor plugins install --global        Install all plugins globally
  raptor plugins -i -g                   (shorthand)

  raptor plugins status plugin-name      Show installation status for a plugin

  raptor --version                       Show version
"""
    )

    parser.add_argument('--version', action='version', version=f'Raptor {__version__}')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize a new Raptor audit project')
    init_parser.add_argument('project_name', nargs='?', help='Project name (optional)')
    init_parser.add_argument('-f', '--force', action='store_true',
                            help='Force overwrite existing directory')
    init_parser.add_argument('--git-url', '--gu', nargs='+', dest='git_urls',
                            help='Clone one or more git repositories into src/')
    init_parser.add_argument('--commit', action='store_true',
                            help='Clone with full commit history (default: shallow clone)')

    # Git command
    git_parser = subparsers.add_parser('git', help='Manage git repositories')
    git_subparsers = git_parser.add_subparsers(dest='git_command', help='Git operations')

    # Git add
    git_add = git_subparsers.add_parser('add', help='Add repositories to src/')
    git_add.add_argument('repos', nargs='+', help='Repository URL(s) to clone')
    git_add.add_argument('--commit', action='store_true',
                        help='Clone with full commit history (default: shallow clone)')

    # Git remove
    git_remove = git_subparsers.add_parser('remove', help='Remove repositories from src/')
    git_remove.add_argument('repos', nargs='+', help='Repository name(s) to remove')

    # Git update
    git_update = git_subparsers.add_parser('update', help='Update repositories')
    git_update.add_argument('repos', nargs='*', help='Repository name(s) to update (default: all)')

    # Git list
    _git_list = git_subparsers.add_parser('list', help='List all repositories in src/')

    # Finding command
    finding_parser = subparsers.add_parser('finding', help='Manage findings')
    finding_parser.add_argument('--new', dest='title', help='Create new finding with title')
    finding_parser.add_argument('--severity', '-s',
                               choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
                               default='MEDIUM',
                               help='Severity level (default: MEDIUM)')
    finding_parser.add_argument('--report', '-r', nargs='+', dest='report_formats',
                               choices=['sherlock', 'code4rena', 'codehawks'],
                               help='Generate reports in specified formats')

    # Report command
    report_parser = subparsers.add_parser('report', help='Generate reports from findings')
    report_parser.add_argument('--format', '-f', nargs='+', dest='formats',
                              choices=['sherlock', 'code4rena', 'codehawks'],
                              help='Report formats (default: sherlock)')
    report_parser.add_argument('--finding', nargs='+', dest='findings',
                              help='Specific findings (titles, filenames, or indexes)')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update Raptor to a newer version')
    update_parser.add_argument('version', nargs='?', help='Target version (default: latest stable)')

    # Upgrade command
    upgrade_parser = subparsers.add_parser('upgrade', help='Upgrade Raptor to a new major version')
    upgrade_parser.add_argument('version', nargs='?', help='Target version (default: latest)')

    # Downgrade command
    downgrade_parser = subparsers.add_parser('downgrade', help='Downgrade Raptor to a previous version')
    downgrade_parser.add_argument('version', help='Target version to downgrade to')

    # Version command
    version_parser = subparsers.add_parser('version', help='Show or manage versions')
    version_group = version_parser.add_mutually_exclusive_group()
    version_group.add_argument('--list', '-l', action='store_true',
                              help='List all available versions')
    version_group.add_argument('--current', '-c', action='store_true',
                              help='Show current version')

    # Plugins command
    plugins_parser = subparsers.add_parser('plugins', help='Manage plugins')
    plugins_subparsers = plugins_parser.add_subparsers(dest='plugins_command', help='Plugin operations')

    # Plugins list
    plugins_list = plugins_subparsers.add_parser('list', help='List all available plugins')

    # Plugins install
    plugins_install = plugins_subparsers.add_parser('install', help='Install plugins')
    plugins_install.add_argument('plugins', nargs='*', help='Plugin name(s) to install (default: install all from raptor.toml)')
    plugins_install.add_argument('--global', '-g', dest='global_install', action='store_true',
                                help='Install globally to raptor installation instead of project plugins')

    # Plugins status
    plugins_status = plugins_subparsers.add_parser('status', help='Show plugin installation status')
    plugins_status.add_argument('plugin', help='Plugin name')

    # Shorthand flags for plugins command
    plugins_parser.add_argument('--list', '-l', action='store_true',
                               help='List all available plugins (shorthand for: plugins list)')
    plugins_parser.add_argument('--install', '-i', nargs='*', dest='install_plugins',
                               help='Install plugins (shorthand for: plugins install)')
    plugins_parser.add_argument('--global', '-g', dest='global_install', action='store_true',
                               help='Install globally (use with --install)')

    # Register plugin commands
    plugin_handlers = plugins.register_tool_commands(subparsers)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == 'init':
        shallow = not args.commit  # If --commit is not set, use shallow clone
        return init_project(args.project_name, force=args.force,
                          git_urls=args.git_urls, shallow=shallow)
    elif args.command == 'git':
        if not args.git_command:
            git_parser.print_help()
            return 1

        if args.git_command == 'add':
            shallow = not args.commit
            return git_module.add_repos(args.repos, shallow=shallow)
        elif args.git_command == 'remove':
            return git_module.remove_repos(args.repos)
        elif args.git_command == 'update':
            return git_module.update_repos(args.repos if args.repos else None)
        elif args.git_command == 'list':
            return git_module.list_repos()
    elif args.command == 'finding':
        if not args.title:
            print("Error: --new is required for finding command")
            finding_parser.print_help()
            return 1
        return new_finding(args.title, args.severity, report_formats=args.report_formats)
    elif args.command == 'report':
        return generate_report(formats=args.formats, findings=args.findings)
    elif args.command == 'update':
        return update_module.update_raptor(args.version)
    elif args.command == 'upgrade':
        return update_module.upgrade_raptor(args.version)
    elif args.command == 'downgrade':
        return update_module.downgrade_raptor(args.version)
    elif args.command == 'version':
        if args.list:
            return update_module.list_versions()
        elif args.current:
            current = update_module.get_current_version()
            print(f"Raptor version: {current}")
            return 0
        else:
            # Default: show current version
            current = update_module.get_current_version()
            print(f"Raptor version: {current}")
            return 0
    elif args.command == 'plugins':
        global_install = getattr(args, 'global_install', False)

        # Handle shorthand flags
        if args.list:
            plugins.list_tools()
            return 0
        elif hasattr(args, 'install_plugins') and args.install_plugins is not None:
            # --install/-i flag used
            if len(args.install_plugins) == 0:
                # No plugins specified, install all
                return 0 if plugins.install_all_tools(global_install) else 1
            else:
                # Install specific plugins
                success = True
                for plugin_name in args.install_plugins:
                    if not plugins.install_tool(plugin_name, global_install):
                        success = False
                return 0 if success else 1

        # Handle subcommands
        if not args.plugins_command:
            plugins_parser.print_help()
            return 1

        if args.plugins_command == 'list':
            plugins.list_tools()
            return 0
        elif args.plugins_command == 'install':
            if not args.plugins or len(args.plugins) == 0:
                # No plugins specified, install all from raptor.toml
                return 0 if plugins.install_all_tools(global_install) else 1
            else:
                # Install specific plugins
                success = True
                for plugin_name in args.plugins:
                    if not plugins.install_tool(plugin_name, global_install):
                        success = False
                return 0 if success else 1
        elif args.plugins_command == 'status':
            plugins.show_status(args.plugin)
            return 0
    elif args.command in plugin_handlers:
        # Handle plugin commands
        handler = plugin_handlers[args.command]
        if callable(handler):
            return handler(args)
        else:
            print(f"Error: Invalid handler for command '{args.command}'")
            return 1
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
