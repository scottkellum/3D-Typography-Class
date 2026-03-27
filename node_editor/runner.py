import subprocess
from pathlib import Path

_procs: dict[str, subprocess.Popen] = {}

PROJECT_ROOT = Path(__file__).parent.parent
TARGET = PROJECT_ROOT / "cold-node.py"


def _kill(key: str) -> None:
    proc = _procs.pop(key, None)
    if proc and proc.poll() is None:
        proc.terminate()


def launch_coldtype(status_callback=None) -> None:
    _kill("coldtype")
    _kill("blender")
    proc = subprocess.Popen(
        ["uv", "run", "coldtype", str(TARGET)],
        cwd=str(PROJECT_ROOT),
    )
    _procs["coldtype"] = proc
    if status_callback:
        status_callback("ColdType running…")


def launch_blender(status_callback=None) -> None:
    _kill("blender")
    _kill("coldtype")
    proc = subprocess.Popen(
        ["uv", "run", "coldtype", str(TARGET), "-p", "b3dlo"],
        cwd=str(PROJECT_ROOT),
    )
    _procs["blender"] = proc
    if status_callback:
        status_callback("Blender running…")


def poll_status() -> str | None:
    """Check if any running process has exited. Returns a status string or None."""
    for key in list(_procs.keys()):
        proc = _procs[key]
        if proc.poll() is not None:
            code = proc.returncode
            del _procs[key]
            return f"{key.title()} exited (code {code})"
    if _procs:
        return None  # still running, no change
    return None


def cleanup_all() -> None:
    for key in list(_procs.keys()):
        _kill(key)
