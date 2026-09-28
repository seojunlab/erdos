"""Save and resume long computations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from erdos._io import atomic_write_text


class CheckpointError(ValueError):
    """A checkpoint file exists but cannot be used."""


def save_checkpoint(path: Path, state: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def load_checkpoint(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    try:
        state = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CheckpointError(
            f"{path}: corrupt checkpoint ({exc}); delete it to restart from zero"
        ) from None
    if not isinstance(state, dict):
        raise CheckpointError(f"{path}: checkpoint must be a JSON object")
    return state
