# 3D Typography in Blender

- https://www.blender.org/
- https://docs.astral.sh/uv/getting-started/installation/

## Install

```bash
./install.sh
```

Requires [Homebrew](https://brew.sh). The script installs `uv` (if missing), system graphics dependencies, and syncs the Python environment.

## Node Editor

A visual node editor for composing ColdType scripts. Changes to the graph auto-save `cold-node.py`, which ColdType and Blender reload live.

```bash
uv run python node_editor.py
```

- **Right-click** the canvas to add nodes (Text, Font Style, Layout, Extrude, Output)
- Connect nodes by dragging between ports
- **Launch ColdType** / **Launch Blender** buttons in the toolbar start live preview
- Your node graph is saved automatically and restored on next open

## Run manually

Launch the ColdType 2D preview:
```bash
uv run coldtype ./cold-node.py
```

Launch with Blender (3D):
```bash
uv run coldtype ./cold-node.py -p b3dlo
```

## Setup

- Discord: https://discord.gg/a5FtJCMj

# Coldtype-Blender bridge

- Find the desired Blender version:
  - `BLENDER_PATH="/Applications/Blender.app" uvx b3denv@latest python --version`
- Create a project with that version:
  - `uv init --python 3.13` (for Blender 5.1)
- Add Coldtype:
  - `uv add "coldtype[viewer]"`
- Verify Coldtype installation:
  - `uv run coldtype --version`
- Try a demo:
  - `uv run coldtype demoblender`
- Try a Blender-enabled Coldtype file:
  - `uv run coldtype demoblender -p b3dlo`
- Run a custom ColdType script in Blender:
  - `uv run coldtype ./my-file.py -p b3dlo`
- Warning:
  - Scale is 1/100 of Blender (unlike using ST2)

## Troubleshooting

### Python Version Mismatch

If you get a `ModuleNotFoundError` (e.g., `No module named 'uharfbuzz._harfbuzz'`), your virtual environment's Python version may not match Blender's. To fix:

1. Check Blender's Python version:
   - `BLENDER_PATH="/Applications/Blender.app" uvx b3denv@latest python --version`
2. Update `pyproject.toml` to match (e.g., `requires-python = ">=3.13"`)
3. Pin the Python version:
   - `uv python pin 3.13`
4. Remove old virtual environment:
   - `rm -rf .venv`
5. Recreate environment with correct Python version:
   - `uv sync`
6. Verify:
   - `uv run python --version`
