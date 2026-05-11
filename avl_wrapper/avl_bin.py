"""Locate the AVL binary, verify it, and drive it via stdin command script."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def find_avl() -> Path:
    """Return the path to the AVL binary.

    Checks ~/bin/avl first (documented install location), then falls back to
    anything named avl* on PATH.
    """
    local = Path.home() / "bin" / "avl"
    if local.is_file() and local.stat().st_mode & 0o111:
        return local

    found = shutil.which("avl")
    if found:
        return Path(found)

    raise FileNotFoundError(
        "AVL binary not found. Install it to ~/bin/avl or ensure it is on PATH.\n"
        "See README.md for build instructions."
    )


def verify(binary: Path | None = None) -> Path:
    """Verify that the AVL binary launches successfully and return its path."""
    binary = binary or find_avl()
    result = subprocess.run(
        [str(binary)],
        input="quit\n",
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"AVL binary at {binary} exited with code {result.returncode}.\n"
            f"stderr: {result.stderr.strip()}"
        )
    return binary


def run(
    command_text: str,
    binary: Path | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    """Feed command_text to AVL via stdin and return the completed process.

    Set cwd to the directory containing the .avl file so that AVL's
    'LOAD <name>' resolves correctly.

    Example
    -------
    >>> from pathlib import Path
    >>> from avl_wrapper.avl_bin import find_avl, run
    >>> binary = find_avl()
    >>> result = run("LOAD bd\\nQuit\\n", cwd=Path("examples"))
    >>> result.returncode
    0
    """
    binary = binary or find_avl()
    return subprocess.run(
        [str(binary)],
        input=command_text,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def run_file(
    command_file: Path,
    binary: Path | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    """Read command_file and feed it to AVL via stdin."""
    return run(Path(command_file).read_text(), binary=binary, cwd=cwd)
