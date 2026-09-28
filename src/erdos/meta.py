"""Load and validate a problem folder's meta.yaml."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from erdos.results import read_result

LABELS = ("verified", "observed", "conjectured", "known")
SITE_STATUSES = ("open", "solved")
OUR_STATUSES = ("surveying", "exploring", "paused", "done")
TOP_KEYS = ("number", "title", "url", "site_status", "our_status", "claims")
CLAIM_KEYS = ("label", "statement", "range", "source", "evidence")
VERIFIED_SCRIPTS = ("explore.py", "verify.py")
FOLDER_RE = re.compile(r"^(\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*$")


class MetaError(ValueError):
    """A meta.yaml file is missing, malformed, or breaks a project rule."""


@dataclass(frozen=True)
class Claim:
    label: str
    statement: str
    range: str | None = None
    source: str | None = None
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProblemMeta:
    number: int
    title: str
    url: str
    site_status: str
    our_status: str
    claims: tuple[Claim, ...]
    folder: Path

    def count(self, label: str) -> int:
        return sum(1 for claim in self.claims if claim.label == label)


def load_meta(folder: Path) -> ProblemMeta:
    path = folder / "meta.yaml"
    where = str(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise MetaError(f"{where}: file not found") from None
    except UnicodeDecodeError:
        raise MetaError(f"{where}: not valid UTF-8; save the file as UTF-8") from None
    except OSError as exc:
        raise MetaError(f"{where}: cannot read: {exc}") from None
    except yaml.YAMLError as exc:
        raise MetaError(f"{where}: invalid YAML: {exc}") from None
    if not isinstance(raw, dict):
        raise MetaError(f"{where}: top level must be a mapping")
    _no_unknown_keys(raw, TOP_KEYS, where)

    number = _field(raw, "number", int, where)
    title = _field(raw, "title", str, where)
    url = _field(raw, "url", str, where)
    site_status = _choice(raw, "site_status", SITE_STATUSES, where)
    our_status = _choice(raw, "our_status", OUR_STATUSES, where)

    match = FOLDER_RE.match(folder.name)
    if not match:
        raise MetaError(f"{where}: folder name '{folder.name}' must look like '0001-short-name'")
    if int(match.group(1)) != number:
        raise MetaError(f"{where}: folder number {match.group(1)} does not match number {number}")

    raw_claims = raw.get("claims")
    if raw_claims is None:
        raw_claims = []
    if not isinstance(raw_claims, list):
        raise MetaError(f"{where}: field 'claims' must be a list")
    claims = tuple(_claim(item, i, folder, where) for i, item in enumerate(raw_claims))
    return ProblemMeta(number, title, url, site_status, our_status, claims, folder)


def _no_unknown_keys(raw: dict, allowed: tuple[str, ...], where: str) -> None:
    for key in raw:
        if key not in allowed:
            raise MetaError(f"{where}: unknown field '{key}', expected one of {', '.join(allowed)}")


def _field(raw: dict, key: str, typ: type, where: str):
    if key not in raw:
        raise MetaError(f"{where}: missing field '{key}'")
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, typ):
        raise MetaError(f"{where}: field '{key}' must be {typ.__name__}, got {value!r}")
    if typ is str and not value.strip():
        raise MetaError(f"{where}: field '{key}' must not be empty")
    return value


def _choice(raw: dict, key: str, allowed: tuple[str, ...], where: str) -> str:
    value = _field(raw, key, str, where)
    if value not in allowed:
        raise MetaError(f"{where}: field '{key}' is {value!r}, expected one of {', '.join(allowed)}")
    return value


def _claim(raw: object, index: int, folder: Path, where: str) -> Claim:
    at = f"{where}: claims[{index}]"
    if not isinstance(raw, dict):
        raise MetaError(f"{at} must be a mapping")
    _no_unknown_keys(raw, CLAIM_KEYS, at)
    label = _choice(raw, "label", LABELS, at)
    statement = _field(raw, "statement", str, at)
    rng = raw.get("range")
    source = raw.get("source")
    evidence = raw.get("evidence") or []
    if label in ("verified", "observed") and not (isinstance(rng, str) and rng.strip()):
        raise MetaError(f"{at}: a {label} claim needs a 'range'")
    if label == "known" and not (isinstance(source, str) and source.strip()):
        raise MetaError(f"{at}: a known claim needs a 'source'")
    if not isinstance(evidence, list) or not all(isinstance(e, str) for e in evidence):
        raise MetaError(f"{at}: 'evidence' must be a list of file paths")
    if label == "verified":
        _check_verified_evidence(evidence, folder, at)
    return Claim(label, statement, rng, source, tuple(evidence))


def _check_verified_evidence(evidence: list[str], folder: Path, at: str) -> None:
    """A verified claim rests on result files written by both explore.py and verify.py."""
    results_dir = (folder / "results").resolve()
    resolved: dict[Path, str] = {}
    for rel in evidence:
        path = (folder / rel).resolve()
        if not path.is_relative_to(results_dir):
            raise MetaError(f"{at}: evidence file '{rel}' must be inside results/")
        resolved.setdefault(path, rel)
    if len(resolved) < 2:
        raise MetaError(
            f"{at}: a verified claim needs at least two distinct evidence files (explore + verify)"
        )
    scripts = set()
    for path, rel in resolved.items():
        if not path.is_file():
            raise MetaError(f"{at}: evidence file '{rel}' does not exist")
        try:
            params, _, _ = read_result(path)
        except (OSError, UnicodeDecodeError, ValueError):
            params = {}
        if "script" not in params or "commit" not in params:
            raise MetaError(
                f"{at}: evidence file '{rel}' is not a result file (no provenance header); "
                "write it with erdos.results.write_result"
            )
        scripts.add(params["script"])
    if not set(VERIFIED_SCRIPTS) <= scripts:
        raise MetaError(
            f"{at}: a verified claim needs result files from both explore.py and verify.py, "
            f"found {', '.join(sorted(scripts))}"
        )
