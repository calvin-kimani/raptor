# Contributing Guide

Thank you for your interest in contributing to this project! This guide will help you understand our workflow and make your first contribution.

## Getting Started

### Prerequisites

- Git installed on your system
- A GitHub account
- Basic familiarity with command line operations

### Setting Up Your Development Environment

1. **Fork the repository** on GitHub by clicking the "Fork" button
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/calvin-kimani/raptor.git
   cd raptor
   ```
3. **Add the original repository as upstream**:
   ```bash
   git remote add upstream https://github.com/calvin-kimani/raptor.git
   ```
4. **Verify your remotes**:
   ```bash
   git remote -v
   ```

## Making Changes

### 1. Create a Feature Branch

Always create a new branch for your changes. Never work directly on the main branch.

```bash
# Update your local main branch first
git checkout main
git pull upstream main

# Create and switch to a new feature branch
git checkout -b feature/your-feature-name
```

### 2. Branch Naming Convention

Use descriptive branch names that follow this pattern: `type/brief-description`

#### Branch Types and When to Use Them:

**`feature/`** - For new functionality or enhancements
- Adding a new component, page, or capability
- Implementing a new API endpoint
- Adding user-facing features
- Examples: `feature/add-user-authentication`, `feature/shopping-cart`

**`bugfix/` or `fix/`** - For fixing existing bugs or issues
- Resolving broken functionality
- Fixing errors or unexpected behavior
- Addressing reported issues
- Examples: `bugfix/fix-login-validation`, `fix/memory-leak-in-cache`

**`hotfix/`** - For urgent fixes that need immediate deployment
- Critical security vulnerabilities
- Production-breaking bugs
- Emergency patches
- Examples: `hotfix/security-patch`, `hotfix/payment-gateway-error`

**`docs/`** - For documentation-only changes
- Updating README files
- Adding code comments
- Writing guides or tutorials
- API documentation updates
- Examples: `docs/update-readme`, `docs/api-documentation`

**`refactor/`** - For code improvements without changing functionality
- Code cleanup and optimization
- Restructuring without adding features
- Performance improvements
- Removing dead code
- Examples: `refactor/improve-error-handling`, `refactor/database-queries`

**`test/`** - For adding or updating tests
- Writing new test cases
- Improving test coverage
- Fixing broken tests
- Examples: `test/add-user-service-tests`, `test/integration-tests`

**`chore/`** - For maintenance tasks and tooling
- Updating dependencies
- Configuration changes
- Build script modifications
- Setting up CI/CD
- Examples: `chore/update-dependencies`, `chore/setup-eslint`

**`style/`** - For formatting and style changes only
- Code formatting fixes
- Linting rule updates
- CSS/styling adjustments (no functional changes)
- Examples: `style/fix-indentation`, `style/update-button-colors`

### 3. Make Your Changes

- Write clear, concise code
- Follow the existing code style and conventions
- Add tests for new functionality
- Update documentation as needed

### 4. Commit Your Changes

Write clear, meaningful commit messages following this format:

```bash
git add .
git commit -m "type: brief description

Optional longer description explaining the change in more detail.

Closes #123"
```

#### Commit Message Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting changes (no code changes)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

#### Example Commit Messages:
```
feat: add user profile page

Add a new user profile page with edit functionality
and avatar upload support.

Closes #45
```

```
fix: resolve login form validation issue

Fix validation logic that was preventing users with
special characters in their email from logging in.

Fixes #78
```

## Submitting Changes

### 1. Push Your Branch

```bash
git push origin feature/your-feature-name
```

### 2. Create a Pull Request

1. Go to your fork on GitHub
2. Click "Compare & pull request"
3. Fill out the pull request template with:
   - Clear title describing the change
   - Detailed description of what was changed and why
   - Reference to any related issues
   - Screenshots (if applicable)

### 3. Pull Request Checklist

Before submitting, ensure:
- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated (if needed)
- [ ] Commit messages are clear and descriptive
- [ ] No merge conflicts with main branch

## Code Review Process

1. **Automated Checks**: Your PR will run through automated tests and linting
2. **Peer Review**: Team members will review your code and provide feedback
3. **Address Feedback**: Make requested changes by pushing new commits to your branch
4. **Approval**: Once approved, a maintainer will merge your PR

### Responding to Review Comments

- Address all feedback promptly and professionally
- Ask questions if feedback is unclear
- Make changes in new commits (don't amend existing commits during review)
- Respond to comments to let reviewers know you've addressed them

## Keeping Your Branch Updated

If your PR becomes outdated due to changes in the main branch:

```bash
# Switch to main and update
git checkout main
git pull upstream main

# Switch back to your feature branch
git checkout feature/your-feature-name

# Rebase your changes onto the latest main
git rebase main

# Force push your updated branch (only do this on your own branches)
git push --force-with-lease origin feature/your-feature-name
```

## Common Git Commands

### Useful Commands for Contributors

```bash
# Check status of your working directory
git status

# See what changes you've made
git diff

# View commit history
git log --oneline

# Undo changes to a file
git checkout -- filename

# Undo last commit (keeping changes)
git reset --soft HEAD~1

# Stash changes temporarily
git stash
git stash pop

# See all branches
git branch -a
```

## Best Practices

### Code Quality
- Write self-documenting code with clear variable and function names
- Keep functions small and focused on a single responsibility
- Remove commented-out code and console.log statements
- Ensure your code is properly formatted

### Testing
- Write tests for new features and bug fixes
- Ensure all existing tests still pass
- Aim for good test coverage of critical functionality

### Documentation
- Update README.md if you're adding new features
- Add inline comments for complex logic
- Update API documentation for new endpoints

### Communication
- Use clear, professional language in issues and PRs
- Be responsive to feedback and questions
- Ask for help when you need it

## Troubleshooting

### Common Issues

**Merge Conflicts**
```bash
# Pull latest changes
git pull upstream main

# Resolve conflicts in your editor
# Then add and commit
git add .
git commit -m "resolve merge conflicts"
```

**Accidentally Committed to Main**
```bash
# Create a new branch with your changes
git checkout -b feature/your-feature-name

# Reset main to match upstream
git checkout main
git reset --hard upstream/main
```

**Need to Change Your Last Commit**
```bash
# If you haven't pushed yet - amend your last commit
git commit --amend -m "new commit message"

# If you already pushed - add a new commit instead
git add .
git commit -m "fix: add missing validation logic"
git push origin your-branch-name
```

**Forgot to Add Files or Made an Incomplete Commit**
```bash
# If you haven't pushed yet - add the missing files and amend
git add forgotten-file.js
git commit --amend --no-edit  # Keeps the same commit message

# If you already pushed - make a follow-up commit
git add forgotten-file.js
git commit -m "add missing file for previous feature"
git push origin your-branch-name
```

**Realized You Need to Do Something Before Your Changes**
```bash
# Option 1: Add a preparatory commit before your changes
git add preparatory-changes.js
git commit -m "refactor: prepare codebase for new feature"

# Then continue with your original work
git add your-feature.js
git commit -m "feat: implement new feature"
git push origin your-branch-name

# Option 2: If you need to completely reorder commits (advanced)
# Use interactive rebase to reorder commits
git rebase -i HEAD~2  # Adjust number based on how many commits to reorder
```

## What to Do When You Realize You Made a Mistake

### After Pushing: The Safe Approach

Once you've pushed commits to GitHub, **avoid using `--force` or `--amend`** as this can cause issues for reviewers and CI systems. Instead, use these approaches:

**Missing Files or Incomplete Implementation**
```bash
# Add the missing pieces with a new commit
git add missing-file.js
git commit -m "add missing validation logic"
git push origin your-branch-name
```

**Need to Fix Something in a Previous Commit**
```bash
# Make the fix in a new commit
git add fixed-file.js
git commit -m "fix: correct typo in user validation"
git push origin your-branch-name
```

**Realized You Need Prerequisites First**
```bash
# Add the prerequisite work as a new commit
git add setup-file.js
git commit -m "refactor: add helper functions for new feature"
git push origin your-branch-name

# Your original commits stay as they are - this is fine!
# The PR will show the logical progression of changes
```

### Before Pushing: You Have More Options

If you haven't pushed your commits yet, you have more flexibility:

**Amend Your Last Commit**
```bash
# Add forgotten files to your last commit
git add forgotten-file.js
git commit --amend --no-edit

# Or change the commit message
git commit --amend -m "feat: implement user validation with proper error handling"
```

**Reorder Commits with Interactive Rebase**
```bash
# Reorder, edit, or combine your last few commits
git rebase -i HEAD~3  # For the last 3 commits

# This opens an editor where you can:
# - Reorder commits by moving lines
# - Edit commit messages
# - Squash commits together
# - Split commits apart
```

### Best Practices for Handling Mistakes

1. **Don't Panic**: Mistakes are normal and fixable
2. **Communicate**: If you realize you made an error after creating a PR, leave a comment explaining what you're fixing
3. **Keep It Simple**: Additional commits are often clearer than complex Git operations
4. **Learn Gradually**: Start with simple fixes before attempting advanced Git operations

## Getting Help

- If you've made multiple mistakes and aren't sure how to fix them
- If you need to completely restart your branch
- If you're unsure whether your fix approach is appropriate
- If your branch has become too messy and needs cleanup

Remember: **Additional commits in a PR are perfectly acceptable**. Reviewers can see the progression of your work, and many projects prefer this transparency over heavily edited Git history.

- Check existing issues and documentation first
- Create a new issue for bugs or feature requests
- Ask questions in our community channels
- Tag maintainers in your PR if you need attention

## Code of Conduct

Please be respectful and professional in all interactions. We're all here to learn and improve the project together.

---

Thank you for contributing! Your efforts help make this project better for everyone.