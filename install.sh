#!/usr/bin/env bash
# Raptor Installation Script

set -e

RAPTOR_DIR="$HOME/.raptor"
RAPTOR_REPO="https://github.com/calvin-kimani/raptor.git"
VERSION="${1:-latest-stable}"  # Default to latest-stable if no version specified

echo "Installing Raptor..."

# Check dependencies
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed."
    exit 1
fi

# Handle existing installation
if [ -d "$RAPTOR_DIR" ]; then
    read -p "Raptor already installed. Overwrite? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$RAPTOR_DIR.backup" 2>/dev/null || true
        mv "$RAPTOR_DIR" "$RAPTOR_DIR.backup"
        echo "Previous installation backed up to $RAPTOR_DIR.backup"
    else
        exit 0
    fi
fi

# Clone repository
echo "Cloning Raptor repository..."
git clone "$RAPTOR_REPO" "$RAPTOR_DIR"

# Checkout specific version if requested
cd "$RAPTOR_DIR"

if [ "$VERSION" != "latest-stable" ] && [ "$VERSION" != "latest" ]; then
    # Specific version requested
    echo "Checking out version $VERSION..."

    # Ensure version has 'v' prefix if it looks like a version number
    if [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        VERSION="v$VERSION"
    fi

    # Fetch all tags
    git fetch --tags --quiet

    # Checkout the specified version
    if git checkout "$VERSION" 2>/dev/null; then
        echo "✓ Checked out version $VERSION"
    else
        echo "Error: Version '$VERSION' not found."
        echo "Available versions:"
        git tag -l | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | tail -10
        rm -rf "$RAPTOR_DIR"
        exit 1
    fi
elif [ "$VERSION" = "latest-stable" ]; then
    # Find latest stable tag (no suffix like -beta, -rc)
    LATEST_TAG=$(git tag -l | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1)

    if [ -n "$LATEST_TAG" ]; then
        echo "Checking out latest stable version: $LATEST_TAG..."
        git checkout "$LATEST_TAG"
        echo "✓ Checked out $LATEST_TAG"
    else
        echo "Warning: No stable tags found, using main branch"
    fi
fi

cd - > /dev/null

# Make binaries executable
chmod +x "$RAPTOR_DIR/bin/raptor"

# Update raptor.toml with actual installation path
if [ -f "$RAPTOR_DIR/raptor.toml" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|installation_path = \"/home/user/.raptor\"|installation_path = \"$RAPTOR_DIR\"|" "$RAPTOR_DIR/raptor.toml"
    else
        # Linux
        sed -i "s|installation_path = \"/home/user/.raptor\"|installation_path = \"$RAPTOR_DIR\"|" "$RAPTOR_DIR/raptor.toml"
    fi
fi

# Add to PATH (only if not already present)
SHELL_CONFIG=""
case "$(basename "$SHELL")" in
    bash) SHELL_CONFIG="$HOME/.bashrc" ;;
    zsh) SHELL_CONFIG="$HOME/.zshrc" ;;
    fish) SHELL_CONFIG="$HOME/.config/fish/config.fish" ;;
    *) SHELL_CONFIG="$HOME/.profile" ;;
esac

if [ "$(basename "$SHELL")" = "fish" ]; then
    PATH_LINE="set -gx PATH \$HOME/.raptor/bin \$PATH"
else
    PATH_LINE="export PATH=\"\$HOME/.raptor/bin:\$PATH\""
fi

if ! grep -q "raptor/bin" "$SHELL_CONFIG" 2>/dev/null; then
    echo "" >> "$SHELL_CONFIG"
    echo "# Raptor Framework" >> "$SHELL_CONFIG"
    echo "$PATH_LINE" >> "$SHELL_CONFIG"
    echo "Added Raptor to PATH in $SHELL_CONFIG"
fi

echo ""
echo "✓ Raptor installed successfully!"
echo ""
echo "To use Raptor:"
echo "  source $SHELL_CONFIG"
echo "  raptor --version"
echo ""
echo "To update Raptor in the future:"
echo "  raptor update"
echo ""
