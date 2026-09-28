from pathlib import Path

import pytest


def _write_problem(
    problems_root: Path, number: int, name: str, title: str = "A test problem", claims: str = ""
) -> Path:
    folder = problems_root / f"{number:04d}-{name}"
    folder.mkdir(parents=True)
    meta = (
        f"number: {number}\n"
        f'title: "{title}"\n'
        f"url: https://www.erdosproblems.com/{number}\n"
        "site_status: open\n"
        "our_status: exploring\n"
    )
    if claims:
        meta += "claims:\n" + claims
    (folder / "meta.yaml").write_text(meta, encoding="utf-8")
    return folder


@pytest.fixture
def write_problem():
    return _write_problem
