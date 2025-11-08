"""
Git repository management functionality
"""

import subprocess
import shutil
from pathlib import Path


def _run_git_command(command, cwd=None):
    """Run a git command and return the result."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stderr
    except FileNotFoundError:
        return 1, "Error: git is not installed. Please install git first."


def add_repos(repo_urls, shallow=True):
    """Add one or more git repositories to the src directory."""
    project_path = Path.cwd()

    # Check if we're in a Raptor project
    if not (project_path / "raptor.toml").exists():
        print("Error: Not in a Raptor project. Run 'raptor init' first.")
        return 1

    src_dir = project_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total = len(repo_urls)

    for repo_url in repo_urls:
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        target_dir = src_dir / repo_name

        # Check if repo already exists
        if target_dir.exists():
            print(f"⚠ {repo_name} already exists in src/, skipping...")
            continue

        print(f"Cloning {repo_name}...")

        # Build git clone command
        git_cmd = ["git", "clone"]
        if shallow:
            git_cmd.extend(["--depth", "1"])
        git_cmd.extend([repo_url, str(target_dir)])

        returncode, output = _run_git_command(git_cmd)

        if returncode == 0:
            print(f"✓ {repo_name} cloned to src/{repo_name}")
            success_count += 1
        else:
            print(f"✗ Failed to clone {repo_name}: {output}")

    print(f"\n{success_count}/{total} repositories cloned successfully")
    return 0 if success_count > 0 else 1


def remove_repos(repo_names):
    """Remove one or more repositories from the src directory."""
    project_path = Path.cwd()

    # Check if we're in a Raptor project
    if not (project_path / "raptor.toml").exists():
        print("Error: Not in a Raptor project. Run 'raptor init' first.")
        return 1

    src_dir = project_path / "src"
    if not src_dir.exists():
        print("Error: No src/ directory found.")
        return 1

    success_count = 0
    total = len(repo_names)

    for repo_name in repo_names:
        # Clean repo name (remove .git suffix if present)
        repo_name = repo_name.replace('.git', '')
        target_dir = src_dir / repo_name

        if not target_dir.exists():
            print(f"⚠ {repo_name} not found in src/, skipping...")
            continue

        # Confirm deletion
        response = input(f"Remove {repo_name}? (y/n): ")
        if response.lower() != 'y':
            print(f"Skipped {repo_name}")
            continue

        try:
            shutil.rmtree(target_dir)
            print(f"✓ {repo_name} removed from src/")
            success_count += 1
        except Exception as e:
            print(f"✗ Failed to remove {repo_name}: {e}")

    print(f"\n{success_count}/{total} repositories removed successfully")
    return 0 if success_count > 0 else 1


def update_repos(repo_names=None):
    """Update one or more repositories (or all if none specified)."""
    project_path = Path.cwd()

    # Check if we're in a Raptor project
    if not (project_path / "raptor.toml").exists():
        print("Error: Not in a Raptor project. Run 'raptor init' first.")
        return 1

    src_dir = project_path / "src"
    if not src_dir.exists():
        print("Error: No src/ directory found.")
        return 1

    # Get list of repos to update
    if repo_names:
        # Update specific repos
        repos_to_update = []
        for name in repo_names:
            name = name.replace('.git', '')
            repo_dir = src_dir / name
            if repo_dir.exists() and (repo_dir / ".git").exists():
                repos_to_update.append(repo_dir)
            else:
                print(f"⚠ {name} is not a git repository, skipping...")
    else:
        # Update all git repos in src/
        repos_to_update = [d for d in src_dir.iterdir()
                          if d.is_dir() and (d / ".git").exists()]

    if not repos_to_update:
        print("No git repositories found to update.")
        return 1

    success_count = 0
    total = len(repos_to_update)

    for repo_dir in repos_to_update:
        repo_name = repo_dir.name
        print(f"Updating {repo_name}...")

        # Try to pull latest changes
        returncode, output = _run_git_command(["git", "pull"], cwd=str(repo_dir))

        if returncode == 0:
            print(f"✓ {repo_name} updated")
            success_count += 1
        else:
            print(f"✗ Failed to update {repo_name}: {output}")

    print(f"\n{success_count}/{total} repositories updated successfully")
    return 0 if success_count > 0 else 1


def list_repos():
    """List all repositories in the src directory."""
    project_path = Path.cwd()

    # Check if we're in a Raptor project
    if not (project_path / "raptor.toml").exists():
        print("Error: Not in a Raptor project. Run 'raptor init' first.")
        return 1

    src_dir = project_path / "src"
    if not src_dir.exists():
        print("No src/ directory found.")
        return 1

    # Find all git repos
    git_repos = [d for d in src_dir.iterdir()
                 if d.is_dir() and (d / ".git").exists()]

    # Find all non-git directories
    other_dirs = [d for d in src_dir.iterdir()
                  if d.is_dir() and not (d / ".git").exists()]

    if not git_repos and not other_dirs:
        print("No repositories or directories in src/")
        return 0

    if git_repos:
        print("\nGit Repositories:")
        for repo in sorted(git_repos):
            # Get current branch
            returncode, branch = _run_git_command(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(repo)
            )
            branch = branch.strip() if returncode == 0 else "unknown"
            print(f"  • {repo.name} (branch: {branch})")

    if other_dirs:
        print("\nOther Directories:")
        for dir in sorted(other_dirs):
            print(f"  • {dir.name}")

    return 0
