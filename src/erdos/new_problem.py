"""Create a new problem folder from problems/_template.

Usage: python -m erdos.new_problem 1234 short-name --title "Plain title"
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

from erdos.meta import load_meta

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TEMPLATE_FILES = ("README.md", "explore.py", "verify.py", "tests/test_problem.py")


def create_problem(problems_root: Path, number: int, name: str, title: str) -> Path:
    if not 1 <= number <= 9999:
        raise ValueError(f"problem number must be between 1 and 9999, got {number}")
    if not NAME_RE.match(name):
        raise ValueError(f"short name {name!r} must be lowercase words joined by '-'")
    if not title.strip():
        raise ValueError("title must not be empty")
    template = problems_root / "_template"
    if not template.is_dir():
        raise ValueError(f"template folder not found: {template}")
    prefix = f"{number:04d}-"
    existing = sorted(p.name for p in problems_root.glob(prefix + "*"))
    if existing:
        raise ValueError(f"problem {number} already exists: {existing[0]}")

    folder = problems_root / f"{prefix}{name}"
    try:
        for rel in TEMPLATE_FILES:
            text = (template / rel).read_text(encoding="utf-8").replace("{{NUMBER}}", str(number))
            if rel == "README.md":
                text = text.replace("{{TITLE}}", title)
            out = folder / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8", newline="\n")
        for sub in ("results", "figures"):
            (folder / sub).mkdir()
            (folder / sub / ".gitkeep").touch()
        meta = {
            "number": number,
            "title": title,
            "url": f"https://www.erdosproblems.com/{number}",
            "site_status": "open",
            "our_status": "surveying",
            "claims": [],
        }
        (folder / "meta.yaml").write_text(
            yaml.safe_dump(meta, allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n"
        )
        load_meta(folder)  # fail loudly if the generated file breaks our own rules
    except BaseException:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    return folder


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a new problem folder from the template")
    parser.add_argument("number", type=int, help="problem number on erdosproblems.com")
    parser.add_argument("name", help="short folder name, e.g. sum-free-sets")
    parser.add_argument("--title", required=True, help="plain-language title")
    args = parser.parse_args(argv)
    root = root or Path.cwd()
    try:
        folder = create_problem(root / "problems", args.number, args.name, args.title)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"created {folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
