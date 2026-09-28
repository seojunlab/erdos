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
    (folder / "results").mkdir()
    (folder / "results" / "explore.csv").write_text("x", encoding="utf-8")
    with pytest.raises(MetaError, match="evidence file 'results/verify.csv' does not exist"):
        load_meta(folder)
    (folder / "results" / "verify.csv").write_text("x", encoding="utf-8")
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
