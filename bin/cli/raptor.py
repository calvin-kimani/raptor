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
  
  raptor install --list                  List all available plugins
  
  raptor install plugin-name             Install a plugin
  
  raptor install --status plugin-name             Show installation status for a plugin
  
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

    # Install command
    install_parser = subparsers.add_parser('install', help='Install plugins and tools')
    install_parser.add_argument('tool', nargs='?', help='Tool to install (e.g., ai)')
    install_parser.add_argument('--list', '-l', action='store_true',
                               help='List all available tools')
    install_parser.add_argument('--status', '-s', metavar='TOOL',
                               help='Show installation status for a tool')

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
    elif args.command == 'install':
        if args.list:
            plugins.list_tools()
            return 0
        elif args.status:
            plugins.show_status(args.status)
            return 0
        elif args.tool:
            return 0 if plugins.install_tool(args.tool) else 1
        else:
            install_parser.print_help()
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
