"""Independent second computation for Erdős Problem #1072.

Method ("plain forward scan"): for each prime p multiply r = m! mod p for
m = 1, 2, ..., p - 2 using exact integer remainder (r * m % p), and stop at the
first m with r = p - 1. If none is found, f(p) = p - 1 (Wilson's theorem).

This differs from explore.py in three ways: it walks the whole range 1..p-2
instead of half of it, it never uses the reflection identity, and it reduces
with the exact integer remainder instead of a floating-point quotient estimate.
The prime sieve and the block summaries (integer comparisons f * den < num * p
instead of floating f / p < eps) are also written separately.

Usage:
    python verify.py --limit 10000000 --block 100000 --threads 1 --max-minutes 14
    python verify.py --compare          (compare results/ of both programs)
"""

from __future__ import annotations

import argparse
import hashlib
import time
from fractions import Fraction
from pathlib import Path

import numpy as np
from numba import njit, prange, set_num_threads

from erdos.checkpoint import load_checkpoint, save_checkpoint
from erdos.results import read_result, write_result

FOLDER = Path(__file__).resolve().parent
EPS = ("0.001", "0.01", "0.02", "0.05", "0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9")
COLUMNS = ["lo", "hi", "primes", "full"] + [f"lt_{e}" for e in EPS] + ["sha256_16"]
METHOD = "forward scan m=1..p-2 with exact integer remainder, stop at first m! = -1; 8 lanes"


@njit
def _sieve(n):
    # Note: an earlier variant that counted primes inside the marking loop
    # crashed (access violation) under this numba version; this form is fine.
    composite = np.zeros(n + 1, np.uint8)
    i = 2
    while i * i <= n:
        if composite[i] == 0:
            for j in range(i * i, n + 1, i):
                composite[j] = 1
        i += 1
    count = 0
    for i in range(2, n + 1):
        if composite[i] == 0:
            count += 1
    out = np.empty(count, np.int64)
    k = 0
    for i in range(2, n + 1):
        if composite[i] == 0:
            out[k] = i
            k += 1
    return out


def primes_upto(n: int) -> np.ndarray:
    if n < 2:
        return np.zeros(0, dtype=np.int64)
    return _sieve(n)


@njit
def _forward_lanes(ps, lo_idx, hi_idx, step, out):
    """f(p) for ps[lo_idx::step] by the forward scan, 8 primes side by side."""
    K = 8
    P = np.zeros(K, np.int64)
    R = np.ones(K, np.int64)
    M = np.ones(K, np.int64)
    IDX = np.full(K, -1, np.int64)
    nxt = lo_idx
    active = 0
    for lane in range(K):
        if nxt < hi_idx:
            P[lane] = ps[nxt]
            R[lane] = 1
            M[lane] = 1
            IDX[lane] = nxt
            nxt += step
            active += 1
    while active > 0:
        for lane in range(K):
            i = IDX[lane]
            if i < 0:
                continue
            p = P[lane]
            m = M[lane]
            finished = False
            if m > p - 2:
                out[i] = p - 1  # no earlier hit: Wilson gives (p-1)! = -1
                finished = True
            else:
                r = R[lane] * m % p
                R[lane] = r
                if r == p - 1:
                    out[i] = m
                    finished = True
                else:
                    M[lane] = m + 1
            if finished:
                if nxt < hi_idx:
                    P[lane] = ps[nxt]
                    R[lane] = 1
                    M[lane] = 1
                    IDX[lane] = nxt
                    nxt += step
                else:
                    IDX[lane] = -1
                    active -= 1
    return out


@njit(parallel=True)
def _f_parallel(ps, threads):
    n = ps.shape[0]
    out = np.zeros(n, np.int64)
    for t in prange(threads):
        _forward_lanes(ps, np.int64(t), np.int64(n), np.int64(threads), out)
    return out


def f_values(primes: np.ndarray, threads: int = 1) -> np.ndarray:
    ps = np.ascontiguousarray(primes, dtype=np.int64)
    if ps.size and ps.max() >= 2**31:
        raise ValueError("r * m must fit in 63 bits: need p < 2^31")
    threads = max(1, min(int(threads), max(1, ps.size)))
    set_num_threads(threads)
    return _f_parallel(ps, threads)


@njit(parallel=True)
def _counts(ps):
    out = np.zeros(ps.shape[0], np.int64)
    for i in prange(ps.shape[0]):
        p = ps[i]
        r = 1
        c = 0
        for m in range(1, p):
            r = r * m % p
            if r == p - 1:
                c += 1
        out[i] = c
    return out


def solution_counts(primes: np.ndarray) -> np.ndarray:
    """Number of m in 1..p-1 with p | m! + 1 (OEIS A115092)."""
    return _counts(np.ascontiguousarray(primes, dtype=np.int64))


def summarize(lo: int, hi: int, ps: np.ndarray, f: np.ndarray) -> list:
    row = [lo, hi, len(ps), sum(1 for p, v in zip(ps.tolist(), f.tolist()) if v == p - 1)]
    fp = list(zip(f.tolist(), ps.tolist()))
    for e in EPS:
        frac = Fraction(e)
        num, den = frac.numerator, frac.denominator
        row.append(sum(1 for v, p in fp if v * den < num * p))
    row.append(hashlib.sha256(np.asarray(f, dtype="<i8").tobytes()).hexdigest()[:16])
    return row


def run(limit: int, block: int, root: Path = FOLDER, *, threads: int = 1,
        max_minutes: float = 14.0, stop_after_blocks: int | None = None) -> int:
    if limit % block:
        raise ValueError("limit must be a multiple of block")
    root = Path(root)
    ck = root / "checkpoints" / "verify_state.json"
    state = load_checkpoint(ck)
    if state is None or state.get("block") != block or state.get("method") != METHOD:
        state = {"block": block, "method": METHOD, "rows": [], "seconds": 0.0}
    rows = state["rows"]
    start = time.time()
    last = 0.0
    done = 0
    while len(rows) * block < limit:
        lo = len(rows) * block
        hi = lo + block
        if stop_after_blocks is not None and done >= stop_after_blocks:
            break
        if done and (time.time() - start) + last * (hi / lo) ** 2 > max_minutes * 60:
            break
        t0 = time.time()
        ps = primes_upto(hi)
        ps = ps[ps > lo]
        f = f_values(ps, threads)
        last = time.time() - t0
        rows.append(summarize(lo, hi, ps, f))
        state["seconds"] = float(state.get("seconds", 0.0)) + last
        save_checkpoint(ck, state)
        done += 1
        print(f"block ({lo}, {hi}] {last:.1f}s full={rows[-1][3]}/{rows[-1][2]}", flush=True)
    completed = len(rows) * block
    common = {"method": METHOD, "block": block, "requested_limit": limit,
              "completed_upto": completed, "threads": threads,
              "compute_seconds_total": round(state["seconds"], 1)}
    write_result(
        root / "results" / "verify_blocks.csv", COLUMNS, rows,
        {**common, "range": f"primes p in (0, {completed}] in blocks (lo, hi]",
         "columns": "full = #p with f(p)=p-1; lt_e = #p with f(p)/p < e; sha256_16 = sha256 of f values as int64 LE"},
        script="verify.py",
    )
    counts = []
    cp = cf = 0
    x = 10
    for r in rows:
        cp += r[2]
        cf += r[3]
        while x <= r[1]:
            if x == r[1]:
                counts.append([x, cp, cf, f"{cf / cp:.6f}"])
            x *= 10
    write_result(
        root / "results" / "verify_counts.csv", ["x", "pi_x", "full_count", "ratio"], counts,
        {**common, "range": f"x = powers of 10 that are block ends, up to {completed}"},
        script="verify.py",
    )
    return completed


def compare(results_dir: Path = FOLDER / "results") -> tuple[int, list[int]]:
    """Return (common range, list of block `hi` values where the two programs disagree)."""
    pe, ce, re_ = read_result(Path(results_dir) / "explore_blocks.csv")
    pv, cv, rv = read_result(Path(results_dir) / "verify_blocks.csv")
    if ce != cv or pe["block"] != pv["block"]:
        raise ValueError("block files have different layouts")
    n = min(len(re_), len(rv))
    bad = [int(a[1]) for a, b in zip(re_[:n], rv[:n]) if a != b]
    upto = int(re_[n - 1][1]) if n else 0
    return upto, bad


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=10_000_000)
    ap.add_argument("--block", type=int, default=100_000)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--max-minutes", type=float, default=14.0)
    ap.add_argument("--compare", action="store_true")
    args = ap.parse_args()
    if not args.compare:
        print(f"completed up to {run(args.limit, args.block, FOLDER, threads=args.threads, max_minutes=args.max_minutes)}")
    upto, bad = compare()
    print(f"explore and verify block summaries compared over (0, {upto}]: "
          f"{'all agree' if not bad else 'DISAGREE at blocks ending ' + str(bad)}")


if __name__ == "__main__":
    main()
