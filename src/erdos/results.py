"""Write and read result files that carry their own provenance."""

from __future__ import annotations

import csv
import io
import platform
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path

from erdos import __version__
from erdos._io import atomic_write_text

RESERVED = ("created", "commit", "dirty", "python", "erdos_version")


def git_info(cwd: Path) -> tuple[str, str]:
    """Return (commit, dirty) for the repository containing cwd, or ("unknown", "unknown")."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=cwd, capture_output=True, text=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return "unknown", "unknown"
    return commit, "true" if status.strip() else "false"


def write_result(
    path: Path,
    columns: Sequence[str],
    rows: Iterable[Sequence[object]],
    params: Mapping[str, object],
) -> None:
    for key, value in params.items():
        if key in RESERVED:
            raise ValueError(f"parameter '{key}' is reserved")
        if not key or any(ch in key for ch in ":\r\n") or any(ch in str(value) for ch in "\r\n"):
            raise ValueError(f"parameter {key!r} must be a single line with no ':' in the key")

    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(columns)
    for i, row in enumerate(rows):
        row = list(row)
        if len(row) != len(columns):
            raise ValueError(f"row {i} has {len(row)} values, expected {len(columns)}")
        writer.writerow(row)

    path.parent.mkdir(parents=True, exist_ok=True)
    commit, dirty = git_info(path.parent)
    header = {
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": commit,
        "dirty": dirty,
        "python": platform.python_version(),
        "erdos_version": __version__,
        **{key: str(value) for key, value in params.items()},
    }
    head = "".join(f"# {key}: {value}\n" for key, value in header.items())
    atomic_write_text(path, head + buf.getvalue())


def read_result(path: Path) -> tuple[dict[str, str], list[str], list[list[str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    params: dict[str, str] = {}
    body = 0
    while body < len(lines) and lines[body].startswith("# "):
        key, _, value = lines[body][2:].partition(": ")
        params[key] = value
        body += 1
    table = list(csv.reader(lines[body:]))
    if not table:
        raise ValueError(f"{path}: no column header")
    return params, table[0], table[1:]
