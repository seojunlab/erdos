import pytest

from erdos.checkpoint import CheckpointError, load_checkpoint, save_checkpoint


def test_missing_checkpoint_returns_none(tmp_path):
    assert load_checkpoint(tmp_path / "none.json") is None


def test_round_trip_with_big_ints_and_unicode(tmp_path):
    path = tmp_path / "checkpoints" / "run.json"
    state = {"next_n": 10**30 + 7, "note": "Erdős", "found": [3, 5]}
    save_checkpoint(path, state)
    assert load_checkpoint(path) == state


def test_overwrite_leaves_no_temp_files(tmp_path):
    path = tmp_path / "run.json"
    save_checkpoint(path, {"next_n": 1})
    save_checkpoint(path, {"next_n": 2})
    assert load_checkpoint(path) == {"next_n": 2}
    assert [p.name for p in tmp_path.iterdir()] == ["run.json"]


def test_corrupt_checkpoint_raises_clear_error(tmp_path):
    path = tmp_path / "run.json"
    path.write_text('{"next_n": 12', encoding="utf-8")
    with pytest.raises(CheckpointError, match="corrupt checkpoint"):
        load_checkpoint(path)


def test_non_object_checkpoint_is_rejected(tmp_path):
    path = tmp_path / "run.json"
    path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(CheckpointError, match="JSON object"):
        load_checkpoint(path)
