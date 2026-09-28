from erdos.loader import load_script


def test_scripts_with_same_name_in_different_folders_do_not_collide(tmp_path):
    for folder, value in (("0001-a", 1), ("0002-b", 2)):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "explore.py").write_text(f"VALUE = {value}\n", encoding="utf-8")
    first = load_script(tmp_path / "0001-a" / "explore.py")
    second = load_script(tmp_path / "0002-b" / "explore.py")
    assert (first.VALUE, second.VALUE) == (1, 2)


def test_script_with_unicode_source_loads(tmp_path):
    (tmp_path / "0003-c").mkdir()
    path = tmp_path / "0003-c" / "verify.py"
    path.write_text('NAME = "Erdős"\n', encoding="utf-8")
    assert load_script(path).NAME == "Erdős"
