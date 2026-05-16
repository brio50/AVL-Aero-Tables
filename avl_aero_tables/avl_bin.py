"""Locate the AVL binary, verify it, and drive it via stdin command script."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def find_avl() -> Path:
    """Return the path to the AVL binary.

    Checks ~/bin/avl first (documented install location), then falls back to
    anything named avl* on PATH.

    Example
    -------
    >>> from avl_aero_tables.avl_bin import find_avl
    >>> binary = find_avl()
    >>> binary.name
    'avl'
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
    """Verify that the AVL binary launches successfully and return its path.

    Example
    -------
    >>> from avl_aero_tables.avl_bin import verify
    >>> binary = verify()
    >>> binary.is_file()
    True
    """
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
    avl_file: str | None = None,
    run_file: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Feed command_text to AVL via stdin and return the completed process.

    avl_file and run_file are passed as positional CLI arguments to the AVL
    binary before stdin is read — matching AVL's documented CLI interface:
    ``avl [avl_file [run_file]]``.  Set cwd to the directory containing the
    .avl file so bare filenames resolve correctly.

    Example
    -------
    >>> from pathlib import Path
    >>> from avl_aero_tables.avl_bin import run
    >>> result = run("Quit\\n", avl_file="bd.avl", cwd=Path("examples/bd"))
    >>> result.returncode
    0
    """
    binary = binary or find_avl()
    args = [str(binary)]
    if avl_file is not None:
        args.append(avl_file)
    if run_file is not None:
        args.append(run_file)
    return subprocess.run(
        args,
        input=command_text,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def run_file(
    command_file: Path,
    binary: Path | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Read command_file and feed it to AVL via stdin.

    Example
    -------
    >>> import tempfile
    >>> from pathlib import Path
    >>> from avl_aero_tables.avl_bin import run_file
    >>> with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
    ...     _ = f.write("LOAD bd\\nQuit\\n")
    ...     cmd_path = Path(f.name)
    >>> result = run_file(cmd_path, cwd=Path("examples/bd"))
    >>> result.returncode
    0
    """
    return run(Path(command_file).read_text(), binary=binary, cwd=cwd)
