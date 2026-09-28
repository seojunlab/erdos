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

RESERVED = ("created", "script", "commit", "dirty", "python", "erdos_version")


def git_info(cwd: Path) -> tuple[str, str]:
    """Return (commit, dirty) for the repository containing cwd, or ("unknown", "unknown")."""
    try:
        commit = _git(["rev-parse", "HEAD"], cwd).strip()
        # Untracked files are ignored: a fresh results/ file must not mark the next run dirty.
        status = _git(["status", "--porcelain", "--untracked-files=no"], cwd)
    except (OSError, ValueError, subprocess.CalledProcessError):
        return "unknown", "unknown"
    return commit, "true" if status.strip() else "false"


def _git(args: list[str], cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, check=True,
        encoding="utf-8", errors="replace",
    ).stdout


def write_result(
    path: Path,
    columns: Sequence[str],
    rows: Iterable[Sequence[object]],
    params: Mapping[str, object],
    *,
    script: str,
) -> None:
    """Write a CSV result file headed by its provenance.

    `script` is the file name of the program that produced the data, such as
    "explore.py" or "verify.py"; meta.yaml checks it for verified claims.
    """
    if not script or script != Path(script).name or any(ch in script for ch in ":\r\n"):
        raise ValueError(f"script must be a plain file name like 'explore.py', got {script!r}")
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
        "script": script,
        "commit": commit,
        "dirty": dirty,
        "python": platform.python_version(),
        "erdos_version": __version__,
        **{key: str(value) for key, value in params.items()},
    }
    head = "".join(f"# {key}: {value}\n" for key, value in header.items())
    atomic_write_text(path, head + buf.getvalue())


def read_result(path: Path) -> tuple[dict[str, str], list[str], list[list[str]]]:
    with open(path, encoding="utf-8", newline="") as fh:
        text = fh.read()
    params: dict[str, str] = {}
    while text.startswith("# "):
        line, _, text = text.partition("\n")
        key, _, value = line[2:].partition(": ")
        params[key] = value
    table = list(csv.reader(io.StringIO(text, newline="")))
    if not table:
        raise ValueError(f"{path}: no column header")
    return params, table[0], table[1:]
