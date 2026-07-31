#!/usr/bin/env python3
"""Post-process a sphinx-multiversion build: version switcher + landing redirect.

sphinx-multiversion (see ``.github/workflows/docs.yml``) builds one
subdirectory per matched git ref (e.g. ``v2.0.1/``, ``master/``) but does not
create either of the two things a versioned site actually needs at its root:

1. ``switcher.json`` — the version list the sphinx-book-theme (pydata)
   navbar dropdown fetches at runtime (``html_theme_options["switcher"]`` in
   ``docs/conf.py``).
2. ``index.html`` — GitHub Pages serves the output root directly, and
   sphinx-multiversion never writes anything there, so ``/`` 404s unless
   something redirects it to a real version.

Both are derived here from ``sphinx-multiversion --dump-metadata``'s JSON, so
they always reflect exactly the refs ``smv_tag_whitelist``/
``smv_branch_whitelist`` matched for this build - nothing is hardcoded.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def semver_key(name: str) -> tuple[int, int, int] | None:
    """Parse a ``vX.Y.Z`` tag name into a sortable tuple, else None."""
    if not name.startswith("v"):
        return None
    parts = name[1:].split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return None
    a, b, c = (int(p) for p in parts)
    return (a, b, c)


def build_switcher(metadata: dict[str, dict], base_url: str) -> tuple[list[dict], str]:
    """Return (switcher.json entries, name of the preferred/default ref)."""
    tags = sorted(
        (
            (name, key)
            for name, data in metadata.items()
            if data["source"] == "tags" and (key := semver_key(name))
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    other_refs = sorted(
        name for name, data in metadata.items() if data["source"] != "tags"
    )

    preferred = tags[0][0] if tags else (other_refs[0] if other_refs else None)
    if preferred is None:
        raise ValueError("no versions in metadata; nothing to build a switcher from")

    ordered_names = [name for name, _ in tags] + other_refs
    base_url = base_url.rstrip("/")

    entries = []
    for name in ordered_names:
        entry = {
            "name": f"{name} (latest)" if name == preferred else name,
            "version": name,
            "url": f"{base_url}/{name}/",
        }
        if name == preferred:
            entry["preferred"] = True
        entries.append(entry)
    return entries, preferred


def build_redirect_html(preferred: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>AVL Aerodynamic Tables docs</title>
<meta http-equiv="refresh" content="0; url=./{preferred}/">
<link rel="canonical" href="./{preferred}/index.html">
</head>
<body>
<p>Redirecting to the latest docs: <a href="./{preferred}/">{preferred}</a></p>
</body>
</html>
"""


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(
            f"usage: {argv[0]} <smv-metadata.json> <output-dir> <base-url>",
            file=sys.stderr,
        )
        return 1

    metadata_path, output_dir, base_url = argv[1:4]
    metadata = json.loads(Path(metadata_path).read_text())
    if not metadata:
        print("gen_switcher.py: empty metadata, nothing to do", file=sys.stderr)
        return 1

    entries, preferred = build_switcher(metadata, base_url)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "switcher.json").write_text(json.dumps(entries, indent=2) + "\n")
    (out / "index.html").write_text(build_redirect_html(preferred))

    names = ", ".join(entry["version"] for entry in entries)
    print(f"gen_switcher.py: wrote switcher.json [{names}]; index.html -> {preferred}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
