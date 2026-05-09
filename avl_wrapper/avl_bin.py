"""Locate the AVL binary, verify it, and drive it via stdin command script."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="avl-wrapper",
        description="Python wrapper for AVL (Athena Vortex Lattice)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    verify_p = sub.add_parser("verify", help="Check that the AVL binary is installed and works")
    verify_p.add_argument("--binary", type=Path, default=None, help="Path to AVL binary")

    run_p = sub.add_parser("run", help="Feed a pre-built AVL command file to the AVL binary")
    run_p.add_argument("command_file", type=Path, help="AVL command script to execute")
    run_p.add_argument("--binary", type=Path, default=None, help="Path to AVL binary")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "verify":
        try:
            binary = verify(args.binary)
            print(f"AVL binary OK: {binary}")
            return 0
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    if args.command == "run":
        result = run_file(args.command_file, binary=args.binary)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        return result.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
