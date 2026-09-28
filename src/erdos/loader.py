"""Import a problem script (explore.py, verify.py) by file path."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType


def load_script(path: Path) -> ModuleType:
    path = Path(path).resolve()
    name = "erdos_script_" + re.sub(r"\W", "_", f"{path.parent.name}_{path.stem}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
