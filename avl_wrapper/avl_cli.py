"""avl-wrapper CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from avl_wrapper.avl_bin import run_file, verify


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="avl-wrapper",
        description="Python wrapper for AVL (Athena Vortex Lattice)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("verify", help="Check that the AVL binary is installed and works")

    run_p = sub.add_parser(
        "run", help="Feed a pre-built AVL command file to the AVL binary"
    )
    run_p.add_argument("command_file", type=Path, help="AVL command script to execute")

    return p


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``avl-wrapper`` CLI.

    Subcommands:

    ``verify``
        Check that the AVL binary is installed and runnable.

    ``run <command_file>``
        Feed a pre-built AVL command script to the binary via stdin.

    Example
    -------
    .. code-block:: shell

        # Verify the AVL binary is installed and functional
        avl-wrapper verify

        # Feed a pre-built command script to the binary
        avl-wrapper run path/to/commands.txt
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "verify":
        try:
            binary = verify()
            print(f"AVL binary OK: {binary}")
            return 0
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    if args.command == "run":
        result = run_file(args.command_file)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        return result.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
