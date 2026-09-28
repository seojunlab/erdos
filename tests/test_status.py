from erdos.status import main


def read_status(root):
    return (root / "STATUS.md").read_text(encoding="utf-8")


def test_no_problems_writes_placeholder(tmp_path):
    assert main([], root=tmp_path) == 0
    assert "No problems attempted yet." in read_status(tmp_path)


def test_problems_are_sorted_and_counted(tmp_path, write_problem):
    write_problem(tmp_path / "problems", 20, "later")
    write_problem(
        tmp_path / "problems", 3, "earlier",
        claims="  - label: conjectured\n    statement: Probably true.\n",
    )
    assert main([], root=tmp_path) == 0
    text = read_status(tmp_path)
    assert text.index("| 3 |") < text.index("| 20 |")
    assert "| 3 | [A test problem](problems/0003-earlier/) | open | exploring | 0 | 0 | 1 |" in text


def test_template_and_hidden_folders_are_skipped(tmp_path):
    (tmp_path / "problems" / "_template").mkdir(parents=True)
    (tmp_path / "problems" / ".cache").mkdir()
    assert main([], root=tmp_path) == 0
    assert "No problems attempted yet." in read_status(tmp_path)


def test_markdown_characters_in_title_are_escaped(tmp_path, write_problem):
    write_problem(tmp_path / "problems", 5, "pipes", title="a | [b]")
    assert main([], root=tmp_path) == 0
    assert "[a \| \[b\]](problems/0005-pipes/)" in read_status(tmp_path)


def test_invalid_meta_fails_with_folder_name(tmp_path, write_problem, capsys):
    folder = write_problem(tmp_path / "problems", 7, "broken")
    (folder / "meta.yaml").write_text("number: 7\n", encoding="utf-8")
    assert main([], root=tmp_path) == 1
    assert "0007-broken" in capsys.readouterr().err
    assert not (tmp_path / "STATUS.md").exists()


def test_duplicate_numbers_fail(tmp_path, write_problem, capsys):
    write_problem(tmp_path / "problems", 9, "one")
    write_problem(tmp_path / "problems", 9, "two")
    assert main([], root=tmp_path) == 1
    assert "appears in both" in capsys.readouterr().err


def test_check_mode(tmp_path, write_problem):
    write_problem(tmp_path / "problems", 1, "first")
    assert main(["--check"], root=tmp_path) == 1  # STATUS.md missing
    assert main([], root=tmp_path) == 0
    assert main(["--check"], root=tmp_path) == 0  # fresh
    status = tmp_path / "STATUS.md"
    status.write_bytes(status.read_bytes().replace(b"\n", b"\r\n"))
    assert main(["--check"], root=tmp_path) == 0  # CRLF checkout still counts as fresh
    write_problem(tmp_path / "problems", 2, "second")
    assert main(["--check"], root=tmp_path) == 1  # stale
