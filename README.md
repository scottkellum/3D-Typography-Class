# 3D Typography in Blender

- https://www.blender.org/
- https://docs.astral.sh/uv/getting-started/installation/

- `uvx b3denv`

- Discord: https://discord.gg/a5FtJCMj



# Coldtype-Blender bridge

- Find the desired Blender version:
    - `uvx b3denv python --version`
- Create a project with that version:
    - `uv init --python 3.XX`
- Add Coldtype:
    - `uv add "coldtype[viewer]"`
- Verify Coldtype installation:
    - `uv run coldtype demoblender`
- Try a Blender-enabled Coldtype file:
    - `uv run coldtype demoblender -p b3dlo`
- Warning:
    - Scale is 1/100 of Blender (unlike using ST2)