import shutil
from pathlib import Path

import pytest

from erdos.meta import load_meta
from erdos.new_problem import create_problem, main

TEMPLATE = Path(__file__).resolve().parents[1] / "problems" / "_template"


@pytest.fixture
def problems_root(tmp_path):
    root = tmp_path / "problems"
    shutil.copytree(TEMPLATE, root / "_template")
    return root


def test_creates_a_valid_problem_folder(problems_root):
    folder = create_problem(problems_root, 42, "sum-free-sets", "Sum-free sets")
    assert folder.name == "0042-sum-free-sets"
    for rel in ("README.md", "explore.py", "verify.py", "tests/test_problem.py",
                "results/.gitkeep", "figures/.gitkeep"):
        assert (folder / rel).is_file(), rel
    meta = load_meta(folder)
    assert (meta.number, meta.our_status, meta.claims) == (42, "surveying", ())
    assert "# Erdős Problem #42: Sum-free sets" in (folder / "README.md").read_text(encoding="utf-8")


def test_tricky_title_survives(problems_root):
    title = 'Sums: "quoted" | and """triple"""'
    folder = create_problem(problems_root, 7, "tricky", title)
    assert load_meta(folder).title == title
    for name in ("explore.py", "verify.py"):
        compile((folder / name).read_text(encoding="utf-8"), name, "exec")


@pytest.mark.parametrize(
    "number,name,title",
    [(0, "ok", "T"), (10000, "ok", "T"), (5, "Bad_Name", "T"), (5, "ok", "   ")],
)
def test_bad_input_is_rejected_and_nothing_is_created(problems_root, number, name, title):
    with pytest.raises(ValueError):
        create_problem(problems_root, number, name, title)
    assert [p.name for p in problems_root.iterdir()] == ["_template"]


def test_duplicate_number_is_rejected(problems_root):
    create_problem(problems_root, 3, "first", "First")
    with pytest.raises(ValueError, match="already exists: 0003-first"):
        create_problem(problems_root, 3, "second", "Second")


def test_missing_template_is_reported(tmp_path):
    (tmp_path / "problems").mkdir()
    with pytest.raises(ValueError, match="template folder not found"):
        create_problem(tmp_path / "problems", 1, "x", "X")


def test_cli(problems_root, capsys):
    root = problems_root.parent
    assert main(["11", "good-name", "--title", "Good"], root=root) == 0
    assert (problems_root / "0011-good-name" / "meta.yaml").is_file()
    assert main(["12", "Bad_Name", "--title", "Bad"], root=root) == 1
    assert "error:" in capsys.readouterr().err
