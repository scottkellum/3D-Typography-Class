#!/usr/bin/env bash
set -e

echo "=== ColdType Node Editor — Install ==="

# Check for Homebrew
if ! command -v brew &>/dev/null; then
    echo "ERROR: Homebrew is not installed."
    echo "Install it from https://brew.sh and re-run this script."
    exit 1
fi

# Check for uv
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    brew install uv
fi

echo "Installing system dependencies (cairo, harfbuzz, pkg-config)..."
brew install pkg-config cairo harfbuzz

echo "Syncing Python environment..."
uv sync

echo ""
echo "=== Done ==="
echo ""
echo "Run the node editor:"
echo "  uv run python node_editor.py"
echo ""
echo "Or launch ColdType directly:"
echo "  uv run coldtype ./cold-node.py"
echo ""
echo "Or launch with Blender:"
echo "  uv run coldtype ./cold-node.py -p b3dlo"
