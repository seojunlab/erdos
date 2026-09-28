"""Small-case tests for Erdős Problem #1072.

Both programs are checked against OEIS b-files saved in tests/data/
(downloaded from oeis.org on 2026-09-28; OEIS data are CC BY-SA 4.0):

- b073944.txt  A073944: f(prime(n)) for n = 1..10000 (b-file by J. E. Schoenfield, first 2000 by T. D. Noe)
- b154554.txt  A154554: primes with f(p) = p - 1, first 1000 terms (b-file by T. D. Noe)
- b115092.txt  A115092: number of m with prime(n) | m! + 1, n = 1..2000
"""

from pathlib import Path

import numpy as np
import pytest

from erdos.loader import load_script
from erdos.results import read_result

HERE = Path(__file__).resolve().parent
FOLDER = HERE.parent
explore = load_script(FOLDER / "explore.py")
verify = load_script(FOLDER / "verify.py")


def _bfile(name: str) -> dict[int, int]:
    out = {}
    for line in (HERE / "data" / name).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        n, value = line.split()
        out[int(n)] = int(value)
    return out


A073944 = _bfile("b073944.txt")
A154554 = _bfile("b154554.txt")
A115092 = _bfile("b115092.txt")
PRIMES_10000 = explore.primes_upto(104729)  # the 10000th prime is 104729


def test_sieves_agree_and_have_right_length():
    assert len(PRIMES_10000) == 10000 and PRIMES_10000[-1] == 104729
    assert np.array_equal(PRIMES_10000, verify.primes_upto(104729))


def test_tiny_cases_by_hand():
    # 1!+1 = 2, 2!+1 = 3, 3!+1 = 7, 4!+1 = 25, 5!+1 = 121 = 11^2
    primes = np.array([2, 3, 5, 7, 11], dtype=np.int64)
    expected = [1, 2, 4, 3, 5]
    assert list(explore.f_values(primes)) == expected
    assert list(verify.f_values(primes)) == expected


@pytest.mark.parametrize("module", [explore, verify], ids=["explore", "verify"])
def test_f_matches_A073944(module):
    f = module.f_values(PRIMES_10000)
    expected = np.array([A073944[n] for n in range(1, 10001)], dtype=np.int64)
    bad = np.nonzero(f != expected)[0]
    assert bad.size == 0, f"first mismatch at n={bad[0] + 1}, p={PRIMES_10000[bad[0]]}"


@pytest.mark.parametrize("module", [explore, verify], ids=["explore", "verify"])
def test_full_primes_match_A154554(module):
    primes = module.primes_upto(25349)
    f = module.f_values(primes)
    found = primes[f == primes - 1]
    assert list(found) == [A154554[n] for n in range(1, 1001)]


def test_solution_counts_match_A115092():
    primes = PRIMES_10000[:2000]
    counts = verify.solution_counts(primes)
    assert list(counts) == [A115092[n] for n in range(1, 2001)]


def test_block_summary_end_to_end(tmp_path):
    """Run both programs on a small range and check the summary files agree."""
    limit, block = 30000, 10000
    explore.run(limit, block, tmp_path, threads=1, max_minutes=5, per_prime_limit=25349)
    verify.run(limit, block, tmp_path, threads=1, max_minutes=5)
    p_e, cols_e, rows_e = read_result(tmp_path / "results" / "explore_blocks.csv")
    p_v, cols_v, rows_v = read_result(tmp_path / "results" / "verify_blocks.csv")
    assert p_e["script"] == "explore.py" and p_v["script"] == "verify.py"
    assert p_e["completed_upto"] == p_v["completed_upto"] == str(limit)
    assert cols_e == cols_v and rows_e == rows_v and len(rows_e) == 3
    assert verify.compare(tmp_path / "results") == (limit, [])
    # A154554 has exactly 1000 terms up to 25349; the per-prime file covers that range
    _, cols, rows = read_result(tmp_path / "results" / "explore_f_values.csv")
    assert cols == ["p", "f"]
    assert sum(1 for p, f in rows if int(f) == int(p) - 1) == 1000
    # first block (0, 10000] holds pi(10^4) = 1229 primes
    assert int(rows_e[0][cols_e.index("primes")]) == 1229
    # the mod-4 split partitions the primes 5 <= p <= 30000 (pi(30000) = 3245)
    _, cols, rows = read_result(tmp_path / "results" / "explore_mod4.csv")
    assert sum(int(r[cols.index("count")]) for r in rows) == 3245 - 2
    assert all(int(r[3]) == 0 for r in rows if r[0] == "1 mod 4" and r[2] == "f = h")


def test_refined_model_values():
    import math

    assert explore.refined_model(0.1) == pytest.approx(1 - math.exp(-0.1))
    assert explore.refined_model("full") == pytest.approx(0.75 * math.exp(-0.75))
    assert explore.refined_model(0.5) == pytest.approx(1 - 0.75 * math.exp(-0.5))


def test_explore_resumes_from_checkpoint(tmp_path):
    explore.run(20000, 10000, tmp_path, threads=1, max_minutes=5, per_prime_limit=1000, stop_after_blocks=1)
    params, _, rows = read_result(tmp_path / "results" / "explore_blocks.csv")
    assert params["completed_upto"] == "10000" and len(rows) == 1
    explore.run(20000, 10000, tmp_path, threads=1, max_minutes=5, per_prime_limit=1000)
    params, _, rows = read_result(tmp_path / "results" / "explore_blocks.csv")
    assert params["completed_upto"] == "20000" and len(rows) == 2
