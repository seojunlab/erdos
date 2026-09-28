from pathlib import Path

import pytest

from erdos.meta import MetaError, load_meta

VALID = """\
number: 12
title: "Erdős sums: a test"
url: https://www.erdosproblems.com/12
site_status: open
our_status: exploring
claims:
  - label: known
    statement: Holds for small n.
    source: https://example.org/paper
"""

VERIFIED = VALID + """\
  - label: verified
    statement: No counterexample below 10^6.
    range: "n <= 10^6"
    evidence: [results/explore.csv, results/verify.csv]
"""


def make(tmp_path: Path, text: str, name: str = "0012-test-problem") -> Path:
    folder = tmp_path / name
    folder.mkdir()
    (folder / "meta.yaml").write_text(text, encoding="utf-8")
    return folder


def test_loads_valid_meta_with_unicode_title(tmp_path):
    meta = load_meta(make(tmp_path, VALID))
    assert meta.number == 12
    assert meta.title == "Erdős sums: a test"
    assert meta.count("known") == 1


def test_missing_field_names_file_and_field(tmp_path):
    folder = make(tmp_path, VALID.replace("our_status: exploring\n", ""))
    with pytest.raises(MetaError, match=r"meta\.yaml: missing field 'our_status'"):
        load_meta(folder)


def test_unknown_label_is_rejected(tmp_path):
    folder = make(tmp_path, VALID.replace("label: known", "label: proven"))
    with pytest.raises(MetaError, match=r"claims\[0\].*'proven'"):
        load_meta(folder)


def test_known_claim_needs_source(tmp_path):
    folder = make(tmp_path, VALID.replace("    source: https://example.org/paper\n", ""))
    with pytest.raises(MetaError, match="needs a 'source'"):
        load_meta(folder)


def test_verified_claim_needs_existing_evidence_files(tmp_path):
    folder = make(tmp_path, VERIFIED)
    _evidence(folder, "explore.csv", "explore.py")
    with pytest.raises(MetaError, match="evidence file 'results/verify.csv' does not exist"):
        load_meta(folder)
    _evidence(folder, "verify.csv", "verify.py")
    assert load_meta(folder).count("verified") == 1


def test_verified_claim_with_one_evidence_file_is_rejected(tmp_path):
    text = VERIFIED.replace("[results/explore.csv, results/verify.csv]", "[results/explore.csv]")
    with pytest.raises(MetaError, match="at least two distinct evidence files"):
        load_meta(make(tmp_path, text))


def test_observed_claim_needs_range(tmp_path):
    text = VALID + "  - label: observed\n    statement: Looks true.\n"
    with pytest.raises(MetaError, match="needs a 'range'"):
        load_meta(make(tmp_path, text))


def test_folder_number_must_match(tmp_path):
    folder = make(tmp_path, VALID, name="0013-test-problem")
    with pytest.raises(MetaError, match="does not match number 12"):
        load_meta(folder)


def test_invalid_yaml_is_reported(tmp_path):
    with pytest.raises(MetaError, match="invalid YAML"):
        load_meta(make(tmp_path, "number: [unclosed\n"))


def test_boolean_is_not_a_number(tmp_path):
    folder = make(tmp_path, VALID.replace("number: 12", "number: true"))
    with pytest.raises(MetaError, match="'number' must be int"):
        load_meta(folder)


def test_missing_file_is_reported(tmp_path):
    folder = tmp_path / "0012-empty"
    folder.mkdir()
    with pytest.raises(MetaError, match="file not found"):
        load_meta(folder)


# --- review fixes ---------------------------------------------------------------

from erdos.results import write_result  # noqa: E402


def _evidence(folder, name, script):
    write_result(folder / "results" / name, ["n"], [(1,)], {"range": "n <= 10"}, script=script)


def test_verified_needs_explore_and_verify_result_files(tmp_path):
    folder = make(tmp_path, VERIFIED)
    _evidence(folder, "explore.csv", "explore.py")
    _evidence(folder, "verify.csv", "explore.py")  # both made by the same script
    with pytest.raises(MetaError, match="explore.py and verify.py"):
        load_meta(folder)
    _evidence(folder, "verify.csv", "verify.py")
    assert load_meta(folder).count("verified") == 1


def test_verified_evidence_must_be_distinct_files(tmp_path):
    text = VERIFIED.replace("[results/explore.csv, results/verify.csv]", "[results/explore.csv, ./results/explore.csv]")
    folder = make(tmp_path, text)
    _evidence(folder, "explore.csv", "explore.py")
    with pytest.raises(MetaError, match="at least two distinct evidence files"):
        load_meta(folder)


@pytest.mark.parametrize("bad", ["meta.yaml", "../0001-other/results/x.csv"])
def test_verified_evidence_must_live_in_results(tmp_path, bad):
    text = VERIFIED.replace("[results/explore.csv, results/verify.csv]", f"[results/explore.csv, {bad}]")
    folder = make(tmp_path, text)
    _evidence(folder, "explore.csv", "explore.py")
    other = tmp_path / "0001-other"
    write_result(other / "results" / "x.csv", ["n"], [(1,)], {}, script="verify.py")
    with pytest.raises(MetaError, match="must be inside results/"):
        load_meta(folder)


def test_verified_evidence_must_be_a_result_file(tmp_path):
    folder = make(tmp_path, VERIFIED)
    _evidence(folder, "explore.csv", "explore.py")
    (folder / "results" / "verify.csv").write_text("n\n1\n", encoding="utf-8")
    with pytest.raises(MetaError, match="not a result file"):
        load_meta(folder)


def test_unknown_top_level_key_is_rejected(tmp_path):
    folder = make(tmp_path, VALID.replace("claims:", "claim:"))
    with pytest.raises(MetaError, match="unknown field 'claim'"):
        load_meta(folder)


def test_unknown_claim_key_is_rejected(tmp_path):
    folder = make(tmp_path, VALID.replace("source:", "sorce: x\n    source:"))
    with pytest.raises(MetaError, match=r"claims\[0\].*unknown field 'sorce'"):
        load_meta(folder)


@pytest.mark.parametrize("value", ["{}", '""'])
def test_claims_must_be_a_list(tmp_path, value):
    text = VALID.split("claims:")[0] + f"claims: {value}\n"
    with pytest.raises(MetaError, match="'claims' must be a list"):
        load_meta(make(tmp_path, text))


def test_non_utf8_meta_names_the_file(tmp_path):
    folder = make(tmp_path, VALID)
    (folder / "meta.yaml").write_bytes(VALID.encode("cp949", errors="replace").replace(b"12", b"12") + b"\xff\xfe")
    with pytest.raises(MetaError, match=r"meta\.yaml: not valid UTF-8"):
        load_meta(folder)
