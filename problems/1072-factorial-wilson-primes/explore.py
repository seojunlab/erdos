"""Primary computation for Erdős Problem #1072.

For a prime p, f(p) is the least m >= 1 with p | m! + 1 (Wilson: f(p) <= p - 1).

Method ("half scan with the reflection identity"):
    For 0 <= k <= p - 1,  k! * (p - 1 - k)! = (-1)^(k+1)  (mod p).
    Hence m! = -1 (mod p)  <=>  k! = (-1)^k (mod p)  with k = p - 1 - m.
    So we only walk j = 1, ..., h = (p - 1)/2 computing j! mod p:
      * if some m <= h has m! = -1, the least such m is f(p) (stop there);
      * otherwise f(p) = p - 1 - k*, where k* is the largest k < h with
        k! = (-1)^k (k = 0 always qualifies, giving f(p) = p - 1).
    Each step is one modular multiplication done with a floating-point
    reciprocal quotient estimate plus one correction (valid for p < 2^31).
    Eight primes are advanced side by side in each thread so that the CPU can
    overlap their independent multiplication chains.

Usage:
    python explore.py --limit 10000000 --block 100000 --threads 1 --max-minutes 14
    python explore.py --figure            (redraw figures/ from results/)

Progress is checkpointed after every block into checkpoints/explore_state.json;
rerunning the same command resumes. Results are written into results/ every time
the run stops (finished or not), with the covered range in `completed_upto`.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import time
from pathlib import Path

import numpy as np
from numba import njit, prange, set_num_threads

from erdos.checkpoint import load_checkpoint, save_checkpoint
from erdos.results import read_result, write_result

FOLDER = Path(__file__).resolve().parent
LANES = 8
EPS = (0.001, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
BLOCK_COLUMNS = ["lo", "hi", "primes", "full"] + [f"lt_{e}" for e in EPS] + ["sha256_16"]
METHOD = "half scan j=1..(p-1)/2 with reflection k!(p-1-k)! = (-1)^(k+1); float-reciprocal modmul; 8 lanes"


# ---------------------------------------------------------------- primes

def primes_upto(n: int) -> np.ndarray:
    """All primes <= n, by a numpy sieve of Eratosthenes."""
    if n < 2:
        return np.zeros(0, dtype=np.int64)
    sieve = np.ones(n + 1, dtype=bool)
    sieve[:2] = False
    for q in range(2, math.isqrt(n) + 1):
        if sieve[q]:
            sieve[q * q :: q] = False
    return np.nonzero(sieve)[0].astype(np.int64)


# ---------------------------------------------------------------- kernel

@njit
def _half_scan_lanes(ps, order, out):
    """Compute f(p) for ps[order[i]] into out[order[i]], LANES primes at a time."""
    K = 8
    n = order.shape[0]
    P = np.zeros(K, np.int64)
    H = np.zeros(K, np.int64)
    R = np.ones(K, np.int64)
    J = np.ones(K, np.int64)
    LASTK = np.zeros(K, np.int64)
    INV = np.zeros(K, np.float64)
    IDX = np.full(K, -1, np.int64)
    nxt = 0
    active = 0
    for lane in range(K):
        while nxt < n:
            i = order[nxt]
            nxt += 1
            p = ps[i]
            if p < 5:  # h < 2: nothing to scan, answer is p - 1 (f(2)=1, f(3)=2)
                out[i] = p - 1
                continue
            P[lane] = p
            H[lane] = (p - 1) // 2
            INV[lane] = 1.0 / p
            R[lane] = 1
            J[lane] = 1
            LASTK[lane] = 0
            IDX[lane] = i
            active += 1
            break
    while active > 0:
        for lane in range(K):
            if IDX[lane] < 0:
                continue
            p = P[lane]
            j = J[lane]
            r = R[lane]
            q = np.int64(float(r) * float(j) * INV[lane])
            r = r * j - q * p
            if r < 0:
                r += p
            elif r >= p:
                r -= p
            R[lane] = r
            done = False
            if r == p - 1:
                out[IDX[lane]] = j  # least m <= h with m! = -1
                done = True
            else:
                if j < H[lane]:
                    target = 1 if (j & 1) == 0 else p - 1
                    if r == target:
                        LASTK[lane] = j
                if j >= H[lane]:
                    out[IDX[lane]] = p - 1 - LASTK[lane]
                    done = True
            if not done:
                J[lane] = j + 1
                continue
            # refill this lane
            IDX[lane] = -1
            active -= 1
            while nxt < n:
                i = order[nxt]
                nxt += 1
                p = ps[i]
                if p < 5:
                    out[i] = p - 1
                    continue
                P[lane] = p
                H[lane] = (p - 1) // 2
                INV[lane] = 1.0 / p
                R[lane] = 1
                J[lane] = 1
                LASTK[lane] = 0
                IDX[lane] = i
                active += 1
                break
    return out


@njit(parallel=True)
def _f_parallel(ps, threads):
    n = ps.shape[0]
    out = np.zeros(n, np.int64)
    for t in prange(threads):
        order = np.arange(t, n, threads)  # interleaved split balances the work
        _half_scan_lanes(ps, order, out)
    return out


def f_values(primes: np.ndarray, threads: int = 1) -> np.ndarray:
    """f(p) for each prime in `primes` (int64 array, every p < 2^31)."""
    ps = np.ascontiguousarray(primes, dtype=np.int64)
    if ps.size and ps.max() >= 2**31:
        raise ValueError("the float-reciprocal multiplication needs p < 2^31")
    threads = max(1, min(int(threads), max(1, ps.size)))
    set_num_threads(threads)
    return _f_parallel(ps, threads)


# ---------------------------------------------------------------- summaries

def block_row(lo: int, hi: int, primes: np.ndarray, f: np.ndarray) -> list:
    """Summary of primes in (lo, hi]: counts, cumulative f/p fractions, hash of f."""
    ratio = f / primes
    row = [lo, hi, int(primes.size), int(np.count_nonzero(f == primes - 1))]
    row += [int(np.count_nonzero(ratio < e)) for e in EPS]
    row.append(hashlib.sha256(f.astype("<i8").tobytes()).hexdigest()[:16])
    return row


def decade_points(limit: int) -> list[int]:
    xs, x = [], 1000
    while x <= limit:
        xs.append(x)
        x *= 10
    return xs


# ---------------------------------------------------------------- driver

def run(
    limit: int,
    block: int,
    root: Path = FOLDER,
    *,
    threads: int = 1,
    max_minutes: float = 14.0,
    per_prime_limit: int = 100000,
    stop_after_blocks: int | None = None,
    class_limit: int | None = None,
) -> int:
    """Compute blocks (k*block, (k+1)*block] up to `limit`, resuming from a checkpoint.

    Returns the upper end of the range completed so far.
    """
    if limit % block:
        raise ValueError("limit must be a multiple of block")
    if limit >= 2**31:
        raise ValueError("limit must be below 2^31")
    root = Path(root)
    ck_path = root / "checkpoints" / "explore_state.json"
    state = load_checkpoint(ck_path)
    if state is None or state.get("block") != block or state.get("method") != METHOD:
        state = {"block": block, "method": METHOD, "rows": [], "seconds": 0.0}
    rows = state["rows"]
    start = time.time()
    last_block_seconds = 0.0
    done_blocks = 0
    while True:
        lo = len(rows) * block
        hi = lo + block
        if hi > limit:
            break
        if stop_after_blocks is not None and done_blocks >= stop_after_blocks:
            break
        elapsed = time.time() - start
        # cost grows like hi^2 / log hi; stop if the next block would overrun
        predicted = last_block_seconds * (hi / max(lo, 1)) ** 2
        if done_blocks and elapsed + predicted > max_minutes * 60:
            break
        t0 = time.time()
        ps = primes_upto(hi)
        ps = ps[ps > lo]
        f = f_values(ps, threads)
        last_block_seconds = time.time() - t0
        rows.append(block_row(lo, hi, ps, f))
        state["seconds"] = float(state.get("seconds", 0.0)) + last_block_seconds
        save_checkpoint(ck_path, state)
        done_blocks += 1
        print(f"block ({lo}, {hi}] {last_block_seconds:.1f}s full={rows[-1][3]}/{rows[-1][2]}", flush=True)
    completed = len(rows) * block
    write_results(root, rows, block, completed, limit, threads, per_prime_limit, state["seconds"],
                  class_limit if class_limit is not None else 10 * per_prime_limit)
    return completed


def write_results(root, rows, block, completed, limit, threads, per_prime_limit, seconds, class_limit):
    res = root / "results"
    common = {
        "method": METHOD,
        "block": block,
        "requested_limit": limit,
        "completed_upto": completed,
        "threads": threads,
        "compute_seconds_total": round(seconds, 1),
    }
    write_result(
        res / "explore_blocks.csv", BLOCK_COLUMNS, rows,
        {**common, "range": f"primes p in (0, {completed}] in blocks (lo, hi]",
         "columns": "full = #p with f(p)=p-1; lt_e = #p with f(p)/p < e; sha256_16 = sha256 of f values as int64 LE"},
        script="explore.py",
    )
    # per-prime values for small p (recomputed; cheap)
    small_limit = min(per_prime_limit, completed)
    ps = primes_upto(small_limit)
    f = f_values(ps, threads)
    write_result(
        res / "explore_f_values.csv", ["p", "f"], zip(ps.tolist(), f.tolist()),
        {"method": METHOD, "range": f"all primes p <= {small_limit}"},
        script="explore.py",
    )
    # counts of f(p) = p - 1 at x = 10^3, 10^4, ...
    cum_primes = np.cumsum([r[2] for r in rows]) if rows else np.zeros(0)
    cum_full = np.cumsum([r[3] for r in rows]) if rows else np.zeros(0)
    table = []
    points = decade_points(completed)
    if completed and completed not in points:
        points.append(completed)
    for x in points:
        if x % block == 0:
            k = x // block - 1
            n_p, n_full = int(cum_primes[k]), int(cum_full[k])
        elif x <= small_limit:
            sel = ps <= x
            n_p, n_full = int(sel.sum()), int(np.count_nonzero(f[sel] == ps[sel] - 1))
        else:
            continue
        table.append([x, n_p, n_full, f"{n_full / n_p:.6f}", f"{math.exp(-1):.6f}", f"{refined_model('full'):.6f}"])
    write_result(
        res / "explore_counts.csv", ["x", "pi_x", "full_count", "ratio", "one_over_e", "refined_model"], table,
        {**common, "range": f"x = powers of 10 up to {completed}",
         "columns": "full_count = #{p <= x : f(p) = p - 1}; ratio = full_count / pi_x"},
        script="explore.py",
    )
    # distribution of f(p)/p by decade range
    dist = []
    edges = [0] + [x for x in decade_points(completed) if x % block == 0]
    if edges[-1] != completed:
        edges.append(completed)
    for a, b in zip(edges, edges[1:]):
        sel = [r for r in rows if a < r[1] <= b]
        if not sel:
            continue
        n_p = sum(r[2] for r in sel)
        for j, e in enumerate(EPS):
            n_lt = sum(r[4 + j] for r in sel)
            dist.append([a, b, n_p, e, n_lt, f"{n_lt / n_p:.6f}", f"{1 - math.exp(-e):.6f}",
                         f"{refined_model(e):.6f}"])
        n_full = sum(r[3] for r in sel)
        dist.append([a, b, n_p, "full", n_full, f"{n_full / n_p:.6f}", f"{math.exp(-1):.6f}",
                     f"{refined_model('full'):.6f}"])
    write_result(
        res / "explore_distribution.csv",
        ["lo", "hi", "primes", "eps", "count", "fraction", "naive_model", "refined_model"], dist,
        {**common, "range": f"primes in (lo, hi] up to {completed}",
         "columns": "count = #p in (lo,hi] with f(p)/p < eps (eps=full: f(p)=p-1); "
                    "naive_model = 1-exp(-eps) (full: 1/e); refined_model: see refined_model() in explore.py"},
        script="explore.py",
    )
    # split by p mod 4 and by where f(p) falls relative to h = (p-1)/2 (recomputed; moderate cost)
    class_limit = min(class_limit, completed)
    cps = primes_upto(class_limit)
    cps = cps[cps >= 5]
    cf = f_values(cps, threads)
    h = (cps - 1) // 2
    split = []
    for cls in (1, 3):
        s = cps % 4 == cls
        n = int(s.sum())
        cells = [
            ("f < h", np.count_nonzero(cf[s] < h[s]), 1 - math.exp(-0.5)),
            ("f = h", np.count_nonzero(cf[s] == h[s]), 0.0 if cls == 1 else 0.5 * math.exp(-0.5)),
            ("h < f < p-1", np.count_nonzero((cf[s] > h[s]) & (cf[s] < cps[s] - 1)),
             math.exp(-0.5) * (1 - math.exp(-0.25)) * (1 if cls == 1 else 0.5)),
            ("f = p-1", np.count_nonzero(cf[s] == cps[s] - 1), math.exp(-0.75) * (1 if cls == 1 else 0.5)),
        ]
        for name, cnt, model in cells:
            split.append([f"{cls} mod 4", n, name, int(cnt), f"{cnt / n:.6f}", f"{model:.6f}"])
    write_result(
        res / "explore_mod4.csv", ["p_class", "primes", "where_f", "count", "fraction", "refined_model"], split,
        {"method": METHOD, "range": f"primes 5 <= p <= {class_limit}",
         "columns": "h = (p-1)/2; refined_model = prediction of the refined heuristic (README)"},
        script="explore.py",
    )


def refined_model(eps) -> float:
    """Refined heuristic (Conjectured, see README) for the share of primes with f(p)/p < eps.

    Lower half m <= h: each m! hits -1 with chance about 1/p, so P(f > t p) = exp(-t) for t < 1/2.
    At m = h: for p = 3 mod 4, h! = +1 or -1, taken as -1 half the time; for p = 1 mod 4 never -1.
    Upper half m = p-1-k: m! = -1 iff k! = (-1)^k; for odd k that would be a lower-half hit, so only
    even k (half of them) can give a new hit, at rate 1/(2p) per unit of m.
    """
    survive_half = 0.75 * math.exp(-0.5)  # no hit at any m <= h
    if eps == "full":
        return survive_half * math.exp(-0.25)
    if eps < 0.5:
        return 1 - math.exp(-eps)
    return 1 - survive_half * math.exp(-(eps - 0.5) / 2)


WATERMARK = "github.com/seojunlab"


def make_figure(root: Path = FOLDER) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    params, cols, rows = read_result(root / "results" / "explore_blocks.csv")
    _, _, small = read_result(root / "results" / "explore_f_values.csv")
    xs, ys = [], []
    n_p = n_full = 0
    small_x = int(small[-1][0]) if small else 0
    first_hi = int(rows[0][1]) if rows else 0
    for p, f in small:  # fine resolution below the first block boundary
        p, f = int(p), int(f)
        n_p += 1
        n_full += f == p - 1
        if p > first_hi:
            break
        if p >= 100:
            xs.append(p)
            ys.append(n_full / n_p)
    n_p = n_full = 0
    for r in rows:
        n_p += int(r[2])
        n_full += int(r[3])
        xs.append(int(r[1]))
        ys.append(n_full / n_p)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(xs, ys, color="#2a6fbb", lw=1.4, label="#{p ≤ x : f(p) = p − 1} / π(x)")
    ax.axhline(math.exp(-1), color="#c0392b", ls="--", lw=1.2, label="1/e ≈ 0.3679 (naive model)")
    ax.axhline(refined_model("full"), color="#27864a", ls=":", lw=1.6,
               label=f"(3/4)·e^(−3/4) ≈ {refined_model('full'):.4f} (refined model)")
    ax.set_xscale("log")
    ax.set_xlabel("x")
    ax.set_ylabel("fraction of primes p ≤ x")
    ax.set_title(f"Erdős #1072: share of primes with f(p) = p − 1, x ≤ {params['completed_upto']}")
    ax.set_ylim(0.25, 0.5)
    ax.grid(alpha=0.3, which="both")
    ax.legend()
    fig.tight_layout()
    fig.text(0.99, 0.01, WATERMARK, ha="right", va="bottom", fontsize=8, color="#888888", alpha=0.8)
    out = root / "figures" / "ratio_vs_x.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=10_000_000)
    ap.add_argument("--block", type=int, default=100_000)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--max-minutes", type=float, default=14.0)
    ap.add_argument("--per-prime-limit", type=int, default=100_000)
    ap.add_argument("--figure", action="store_true", help="only redraw the figure")
    args = ap.parse_args()
    if args.figure:
        print(make_figure())
        return
    done = run(args.limit, args.block, FOLDER, threads=args.threads,
               max_minutes=args.max_minutes, per_prime_limit=args.per_prime_limit)
    print(f"completed up to {done}")
    make_figure()


if __name__ == "__main__":
    main()
