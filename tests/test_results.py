import subprocess

import pytest

from erdos.results import git_info, read_result, write_result


def test_round_trip_keeps_params_columns_and_rows(tmp_path):
    out = tmp_path / "results" / "run.csv"
    write_result(out, ["n", "value"], [(1, 2), (3, "Erdős")], {"range": "1..3", "algorithm": "brute force"}, script="explore.py")
    params, columns, rows = read_result(out)
    assert params["range"] == "1..3"
    assert params["algorithm"] == "brute force"
    assert params["script"] == "explore.py"
    assert {"created", "script", "commit", "dirty", "python", "erdos_version"} <= params.keys()
    assert columns == ["n", "value"]
    assert rows == [["1", "2"], ["3", "Erdős"]]


def test_file_uses_lf_line_endings(tmp_path):
    out = tmp_path / "run.csv"
    write_result(out, ["n"], [(1,)], {}, script="explore.py")
    assert b"\r\n" not in out.read_bytes()


def test_outside_git_repo_records_unknown(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    assert git_info(tmp_path) == ("unknown", "unknown")


def test_inside_git_repo_records_commit_and_dirty(tmp_path):
    git = ["git", "-c", "user.name=test", "-c", "user.email=test@example.org"]
    subprocess.run([*git, "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    subprocess.run([*git, "add", "a.txt"], cwd=tmp_path, check=True)
    subprocess.run([*git, "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert git_info(tmp_path) == (head, "false")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    assert git_info(tmp_path) == (head, "false")  # untracked files (e.g. fresh results) are not "dirty"
    (tmp_path / "a.txt").write_text("changed", encoding="utf-8")
    assert git_info(tmp_path) == (head, "true")


@pytest.mark.parametrize("params", [{"created": "x"}, {"bad:key": "x"}, {"range": "1\n2"}, {"": "x"}])
def test_bad_params_are_rejected(tmp_path, params):
    with pytest.raises(ValueError):
        write_result(tmp_path / "r.csv", ["n"], [], params, script="explore.py")
    assert not (tmp_path / "r.csv").exists()


def test_row_length_must_match_columns(tmp_path):
    with pytest.raises(ValueError, match="row 0"):
        write_result(tmp_path / "r.csv", ["n", "m"], [(1,)], {}, script="explore.py")
    assert not (tmp_path / "r.csv").exists()


def test_fields_with_newlines_and_carriage_returns_round_trip(tmp_path):
    out = tmp_path / "run.csv"
    rows = [["x\ny", "p\rq"], ["m\r\nn", "1"]]
    write_result(out, ["a", "b"], rows, {}, script="explore.py")
    assert read_result(out)[2] == rows


def test_non_ascii_file_names_do_not_crash_git_info(tmp_path):
    git = ["git", "-c", "user.name=test", "-c", "user.email=test@example.org"]
    subprocess.run([*git, "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "core.quotepath", "false"], cwd=tmp_path, check=True)
    name = tmp_path / "에르되시-Erdős.txt"
    name.write_text("a", encoding="utf-8")
    subprocess.run([*git, "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run([*git, "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    name.write_text("changed", encoding="utf-8")
    commit, dirty = git_info(tmp_path)
    assert len(commit) == 40 and dirty == "true"


@pytest.mark.parametrize("script", ["", "a\nb", "dir/explore.py"])
def test_script_must_be_a_plain_file_name(tmp_path, script):
    with pytest.raises(ValueError):
        write_result(tmp_path / "r.csv", ["n"], [], {}, script=script)
