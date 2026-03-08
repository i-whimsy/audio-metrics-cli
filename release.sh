#!/bin/bash
# Release script for audio-metrics-cli

set -e

echo "🚀 Building audio-metrics-cli for PyPI release..."

# Check if version is set
VERSION=$(grep '^version' pyproject.toml | head -1 | cut -d'"' -f2)
echo "📦 Version: $VERSION"

# Install build tools
echo "📥 Installing build tools..."
pip install build twine --quiet

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info

# Build package
echo "🔨 Building package..."
python -m build

# Show built files
echo "📦 Built files:"
ls -lh dist/

# Ask for confirmation
echo ""
read -p "Upload to PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 Uploading to PyPI..."
    twine upload dist/*
    echo "✅ Release complete!"
    echo ""
    echo "🔗 PyPI page: https://pypi.org/project/audio-metrics-cli/$VERSION/"
    echo "🔗 GitHub releases: https://github.com/i-whimsy/audio-metrics-cli/releases"
else
    echo "❌ Upload cancelled"
    echo "💡 Files are ready in dist/ directory"
fi
