# Candidate problems for computer attack (survey of 2026-09-28)

This survey was done on 2026-09-28. Method: we downloaded the community database [`data/problems.yaml`](https://raw.githubusercontent.com/teorth/erdosproblems/main/data/problems.yaml) from [teorth/erdosproblems](https://github.com/teorth/erdosproblems) and listed every problem whose status is `open`, `falsifiable`, `decidable` or `verifiable` (589 open, 4 "open (Lean)", 25 falsifiable, 8 decidable and 7 verifiable out of 1,221 entries at the time of reading). We set aside every problem that appears anywhere on the [AI contributions wiki](https://github.com/teorth/erdosproblems/wiki/AI-contributions-to-Erd%C5%91s-problems) (405 problem numbers; the wiki says it is frozen with data as of 30 June 2026), except where the wiki entry is only a literature search. We then read the erdosproblems.com page and the forum thread (`/forum/thread/NNN`) of about 160 remaining problems, favouring those with OEIS links or a "falsifiable/decidable" status, opened the linked OEIS entries, and ran web searches for recent preprints and public repositories. Each problem was kept only if it is open on erdosproblems.com, a computer search can say something meaningful, existing computation is small or absent, and small cases have checkable values. Labels follow the repository rules: **Known** (in a cited source), **Observed** (something we computed or derived once while writing this survey, not independently checked), **Conjectured** (our belief or heuristic). Nothing here is **Verified** in the repository's sense. Caveat on activity: the forum is very active with AI-assisted computation in 2026, and a public repository, [erdos-frontier-atlas](https://github.com/techno-optimist/erdos-frontier-atlas), maps computational frontiers of many problems and is being updated daily; every pick must be re-checked against both before work starts.

## #475: Graham's rearrangement conjecture for small primes

- Link: https://www.erdosproblems.com/475
- Statement in plain words: Given a prime p and a set A of nonzero residues mod p, can the elements of A always be listed in an order such that all running (partial) sums are different? It is proved for all sufficiently large primes, but a complete check of small primes is not recorded anywhere we looked. Note: the problem page marks this problem "decidable" (resolved up to a finite check), not "open"; the large-prime threshold of Pham and Sauermann appears to be ineffective ([arXiv:2602.15797](https://arxiv.org/abs/2602.15797), abstract), so a small-prime census adds evidence but cannot by itself close the problem (Observed, checked 2026-09-28).
- Computational angle: For each small prime p, go through every subset A of the nonzero residues (up to multiplying A by a unit, which maps valid orderings to valid orderings; Observed) and find one valid ordering by backtracking. The cited results already cover |A| ≤ 20 and |A| ≥ p − 3, so every prime p ≤ 23 is already settled, and the first uncovered case is p = 29 with 21 ≤ |A| ≤ 25 (Observed: our deduction from the two cited results). A clean check of p = 29, 31, 37 (and perhaps 41) would be a new finite result; one set with no valid ordering would disprove the conjecture. Size: about 1.7 million sets for p = 29 and about 23 million for p = 31 before symmetry reduction (Observed: binomial sums).
- Existing computation: The problem page records proofs for |A| ≤ 12 and for p − 3 ≤ |A| ≤ p − 1 (Known, [problem page](https://www.erdosproblems.com/475)). Costa, Della Fiore, Fontana and Vena prove that every A with |A| ≤ 20 in any abelian group has a valid ordering (Known, [arXiv:2603.20961](https://arxiv.org/abs/2603.20961), abstract; we did not check whether that proof is computer-assisted, uncertain). Pham and Sauermann complete the proof for all sufficiently large p (Known, [arXiv:2602.15797](https://arxiv.org/abs/2602.15797)); we did not find whether their threshold is explicit (uncertain). No exhaustive small-prime census found on the page, the forum or the AI wiki.
- Test values for small cases: Every p ≤ 23 must pass completely, and |A| = p − 1 is Graham's own theorem (Known, [problem page](https://www.erdosproblems.com/475) and [arXiv:2603.20961](https://arxiv.org/abs/2603.20961)); p = 3, 5, 7 can be checked by hand.
- Recent activity: Forum posts of 23–24 February and 3 March 2026 add the Pham–Sauermann and Costa–Della Fiore references ([forum thread](https://www.erdosproblems.com/forum/thread/475)); a related August 2026 preprint extends the method to some composite moduli ([arXiv:2608.10015](https://arxiv.org/abs/2608.10015)). Not on the AI wiki.
- Effort estimate: small, because p ≤ 31 needs about 25 million easy orderings and p = 37 is still within reach of a single PC after symmetry reduction.

## #1072: Primes p for which p − 1 is the least m with p | m! + 1

- Link: https://www.erdosproblems.com/1072
- Statement in plain words: Let f(p) be the least m with m! + 1 divisible by p; Wilson's theorem gives f(p) ≤ p − 1. Are there infinitely many primes with f(p) = p − 1, and is f(p)/p → 0 for almost all p?
- Computational angle: For every prime p ≤ X compute m! mod p for m = 1, …, p − 2 and record the first m with m! ≡ −1; count primes with f(p) = p − 1 and tabulate f(p)/p. Cost is about X²/(2 log X) modular multiplications, roughly 3×10¹² for X = 10⁷ (Observed estimate). This cannot settle "infinitely many", but the page reports that Erdős, Hardy and Subbarao believed the count is o(x/log x) (Known, [problem page](https://www.erdosproblems.com/1072)), while a naive heuristic (each m! hits −1 with chance about 1/p) predicts a fixed fraction about 1/e (Conjectured). The OEIS b-file already lists 1,000 such primes among the 2,796 primes up to 25,349, a fraction of 0.358 against 1/e ≈ 0.368 (Observed). Data to 10⁸ would show whether the fraction drifts down.
- Existing computation: [A073944](https://oeis.org/A073944) (f(p) for the first 10,000 primes, b-file by Schoenfield and Noe) and [A154554](https://oeis.org/A154554) (primes with f(p) = p − 1, b-file of 1,000 terms up to 25,349, Noe 2009) (Known). Nothing further on the forum or the AI wiki.
- Test values for small cases: [A073944](https://oeis.org/A073944), [A154554](https://oeis.org/A154554) (starts 2, 3, 5, 13, 17, 31, 37, …) and [A115092](https://oeis.org/A115092) (number of m < p with p | m! + 1).
- Recent activity: One forum comment (30 January 2026) notes that f(p) = p − a forces p | (a − 1)! + (−1)^a and cites a paper giving f(p)/p ≤ 0.138 infinitely often ([forum thread](https://www.erdosproblems.com/forum/thread/1072)). Not on the AI wiki.
- Effort estimate: small, because the loop is one modular multiplication per step and parallelises perfectly over primes.

## #1100: Coprime consecutive divisors, the function g(k)

- Link: https://www.erdosproblems.com/1100
- Statement in plain words: τ⊥(n) counts the pairs of consecutive divisors of n that are coprime, and g(k) is the largest τ⊥(n) over squarefree n with exactly k prime factors. Determine how g(k) grows; Erdős and Simonovits showed (√2 + o(1))^k < g(k) < (2 − c)^k (Known, [problem page](https://www.erdosproblems.com/1100)).
- Computational angle: A forum post quotes the Erdős–Simonovits reduction: g(k) equals the maximum, over k positive reals with distinct subset sums, of the number of consecutive disjoint pairs when all subsets are sorted by sum (Known as a forum claim, [forum thread](https://www.erdosproblems.com/forum/thread/1100)). Exact g(k) for k up to about 7–9 can be computed by enumerating realisable subset-sum orders (each order is a linear-programming feasibility question) or, for lower bounds, by searching prime tuples. Exact values would be new data on the base of the exponential and would settle small-k guesses.
- Existing computation: none found. The forum contains a claimed formula g(k) = C(k,2) + 1, refuted there by the example 2310 with τ⊥ = 12 > 11; no table of g(k) and no OEIS sequence for it was found ([A325864](https://oeis.org/A325864) is related but different, as noted on the forum).
- Test values for small cases: τ⊥(2310) = 12 for k = 5 (Known, forum; Observed by our own recount of its 32 divisors); τ⊥(n) = ω(n) when each prime exceeds the product of the smaller ones (Known, forum remark); k ≤ 4 is a hand or brute-force check.
- Recent activity: Forum posts of 24–25 April and 30 July 2026 ([forum thread](https://www.erdosproblems.com/forum/thread/1100)); the atlas lists the growth base as a "value gap" ([gap map](https://github.com/techno-optimist/erdos-frontier-atlas/blob/main/atlas/gap_map.json)). Not on the AI wiki.
- Effort estimate: medium, because the number of realisable orders grows very fast with k and each needs an exact LP check.

## #131: Largest non-dividing subset of {1, …, N}

- Link: https://www.erdosproblems.com/131
- Statement in plain words: F(N) is the largest size of a set A ⊆ {1, …, N} in which no element divides a sum of distinct other elements. Estimate F(N); it is known that F(N) ≤ N^{1/4+o(1)} and F(N) > exp(c√log N) (Known, [problem page](https://www.erdosproblems.com/131)).
- Computational angle: Compute the thresholds T_k (least N admitting a non-dividing k-set) as far as possible; the growth of T_k is a direct numerical proxy for F(N) between the two known bounds. The next cell is T_11.
- Existing computation: [A068063](https://oeis.org/A068063) gives F(n) for n ≤ 100 (b-file by Sievers, October 2025); its definition ("sum of any nonempty subset of the other elements") appears to match the problem (Observed). A pull request merged in the atlas on 2026-09-28 reports T_9 = 107 and T_10 = 155 by exhaustive search, about 2.5×10⁹ nodes, with a second implementation for k ≤ 9 ([PR #165](https://github.com/techno-optimist/erdos-frontier-atlas/pull/165)); not independently checked by us (uncertain).
- Test values for small cases: [A068063](https://oeis.org/A068063) (for example a(65) = 8 with two explicit 8-sets), and T_1..T_8 = 1, 3, 7, 10, 21, 31, 43, 65 read off from it.
- Recent activity: The atlas PR above (merged today); no forum comments ([forum thread](https://www.erdosproblems.com/forum/thread/131)). Not on the AI wiki.
- Effort estimate: medium, because T_11 is the first cell beyond a search that already took about 10⁹ nodes, and someone else is actively on it.

## #663: Least prime not dividing (n+1)⋯(n+k)

- Link: https://www.erdosproblems.com/663
- Statement in plain words: q(n,k) is the least prime not dividing (n+1)(n+2)⋯(n+k). For fixed k ≥ 2, is q(n,k) < (1 + o(1)) log n for all large n?
- Computational angle: For k = 2, 3, 4 find, for each prime P, the smallest n with q(n,k) > P. Every prime below P must divide one of n+1, …, n+k, so this is a Chinese-remainder search over k^π(P) residue choices with pruning. The record table of q(n,k)/log n shows whether the ratio drifts toward 1 or stays above it. Data cannot prove the asymptotic statement.
- Existing computation: [A391668](https://oeis.org/A391668) tabulates q(n,k) for small n, k (Beregovsky, December 2025) (Known). No record search found on the page or forum. Related #457 is on the AI wiki; we did not check whether work there already produced such records (uncertain).
- Test values for small cases: [A391668](https://oeis.org/A391668); q(n,k) is trivial to compute directly for small n.
- Recent activity: Tao's heuristic in favour of "yes" (6 September 2025, [forum thread](https://www.erdosproblems.com/forum/thread/663)); A391668 created December 2025.
- Effort estimate: small, because the CRT search is simple and records for k = 2 need only modest primes.

## #304: Longest shortest Egyptian fraction for a/b

- Link: https://www.erdosproblems.com/304
- Statement in plain words: N(a,b) is the least number of distinct unit fractions summing to a/b, and N(b) is its maximum over a < b. Is N(b) ≪ log log b? (Known bounds: log log b ≪ N(b) ≪ √log b, [problem page](https://www.erdosproblems.com/304).)
- Computational angle: Compute N(b) for all b up to 10³–10⁴ and list record-setters; the positions of records (where N(b) first reaches 6, 7, 8) compared with log log b is the most direct evidence available.
- Existing computation: [A097849](https://oeis.org/A097849) (row maxima of [A097847](https://oeis.org/A097847)) has 105 terms and no b-file; [A330808](https://oeis.org/A330808) lists record values for the single fraction 1 − 1/n up to a(27539) = 8 (Known). Uncertain: A330808 states that its unit fractions need not be distinct, and we did not confirm whether A097847 requires distinct denominators as the problem does; this must be settled before using them as test values.
- Test values for small cases: [A097849](https://oeis.org/A097849) (1, 1, 2, 2, 3, 2, 3, …), subject to the distinctness caveat.
- Recent activity: One forum comment (6 February 2026) pointing to a paper of Yokota ([forum thread](https://www.erdosproblems.com/forum/thread/304)); A097849's name was corrected in May 2026; the atlas lists A097849(106) as a next cell ([gap map](https://github.com/techno-optimist/erdos-frontier-atlas/blob/main/atlas/gap_map.json)).
- Effort estimate: medium, because proving that no representation of length 5 or 6 exists requires a careful exhaustive search for each b.

## #1073: Composite u dividing n! + 1

- Link: https://www.erdosproblems.com/1073
- Statement in plain words: A(x) counts composite u < x that divide n! + 1 for some n. Is A(x) ≤ x^{o(1)}?
- Computational angle: Compute A(x) to 10⁹ or beyond and watch log A(x) / log x. Every prime factor of such u exceeds n, so u > n² and only n < √x matter (Observed, elementary). For each prime p < x one therefore needs m! mod p only for m < √x, about π(x)·√x ≈ 1.5×10¹² steps for x = 10⁹ (Observed estimate), plus prime squares and combinations.
- Existing computation: [A256519](https://oeis.org/A256519), b-file of 719 terms up to 99,795,337 (Greathouse, 2015) (Known). Nothing on the forum or the AI wiki.
- Test values for small cases: [A256519](https://oeis.org/A256519): 25, 121, 169, 437, 551, 667, …
- Recent activity: No forum comments ([forum thread](https://www.erdosproblems.com/forum/thread/1073)); the atlas lists it as "not gap shaped" ([gap map](https://github.com/techno-optimist/erdos-frontier-atlas/blob/main/atlas/gap_map.json)).
- Effort estimate: medium, because reaching 10⁹–10¹⁰ needs the √x reduction and a careful combination step, not a naive loop.

## #295: Fewest unit fractions with large denominators summing to 1

- Link: https://www.erdosproblems.com/295
- Statement in plain words: k(N) is the least k such that 1 is a sum of k distinct unit fractions with all denominators at least N. Is it true that k(N) − (e − 1)N → ∞? (Known: −c < k(N) − (e − 1)N ≪ N/log N, [problem page](https://www.erdosproblems.com/295).)
- Computational angle: Compute k(17), k(18), … and tabulate k(N) − (e − 1)N. At N = 16 the value 30 exceeds (e − 1)·16 ≈ 27.5 by about 2.5 (Observed); a steady rise would support the conjecture.
- Existing computation: [A192881](https://oeis.org/A192881) gives k(1..16) (terms 9–10 by Múgica 2017, terms 11–16 by Alekseyev, October 2025) (Known). The atlas records a trivial lower bound of 29 for k(17) ([gap map](https://github.com/techno-optimist/erdos-frontier-atlas/blob/main/atlas/gap_map.json)).
- Test values for small cases: [A192881](https://oeis.org/A192881): 1, 3, 5, 8, 10, 11, 13, 15, 17, 19, 21, 23, 25, 26, 28, 30.
- Recent activity: OEIS extension of October 2025; no forum comments ([forum thread](https://www.erdosproblems.com/forum/thread/295)).
- Effort estimate: large, because each new term needs an exhaustive search over representations with about 30 terms, and a few more terms say little about a limit.

## #167: Tuza's conjecture on small graphs

- Link: https://www.erdosproblems.com/167
- Statement in plain words: If a graph has at most k edge-disjoint triangles, can all its triangles be destroyed by removing at most 2k edges? K₄ and K₅ show 2k would be best possible.
- Computational angle: Check τ ≤ 2ν for all graphs up to 10 vertices (about 12 million) and, with pruning, 11 vertices, then run targeted searches (dense regular and vertex-transitive graphs). A counterexample settles the problem; a census gives a documented baseline. Since the conjecture is now proved for maximum degree at most 7 (Known, [arXiv:2608.06538](https://arxiv.org/abs/2608.06538)), a counterexample needs a vertex of degree at least 8 and so at least 9 vertices (Observed deduction). We expect no small counterexample (Conjectured).
- Existing computation: none found. The page, the [forum thread](https://www.erdosproblems.com/forum/thread/167) and the AI wiki (literature search only) show no census, and a web search found none; this is a negative search, so uncertain.
- Test values for small cases: K₄ (ν = 1, τ = 2) and K₅ (ν = 2, τ = 4) from the [problem page](https://www.erdosproblems.com/167); ν and τ of any small graph are easy to brute-force.
- Recent activity: Forum post of 12 October 2025 adding Haxell's bound; the AI wiki lists a literature-search entry of the same date; the maximum-degree-7 preprint above is from August 2026.
- Effort estimate: small for n ≤ 10 and medium for n = 11, but the chance of a genuinely new result is low.

## #742: Murty–Simon conjecture at order 25

- Link: https://www.erdosproblems.com/742
- Statement in plain words: A graph has diameter 2 and every edge deletion increases its diameter. Must it have at most n²/4 edges?
- Computational angle: Dailly, Foucaud and Hansberg report that Fan proved the conjecture for graphs of order at most 24 and 26, and Füredi for n above a tower-type n₀ (Known, [arXiv:1812.08420](https://arxiv.org/pdf/1812.08420), introduction). If read literally, order 25 is the smallest open case (uncertain: we did not open Fan's paper). A SAT or structured search for a diameter-2-critical graph on 25 vertices with more than 156 edges would either find a counterexample or, far harder, rule one out.
- Existing computation: The same paper reports its own computer search on all graphs of order up to 11 (for a strengthened conjecture) (Known, [arXiv:1812.08420](https://arxiv.org/pdf/1812.08420)); nothing on the forum or the AI wiki.
- Test values for small cases: Complete bipartite graphs attain n²/4; the same paper cites a complete list of diameter-2-critical graphs of order at most 7 and gives expanded 5-cycles as near-extremal examples ([arXiv:1812.08420](https://arxiv.org/pdf/1812.08420)).
- Recent activity: none in the last year; the only forum post is from 1 September 2025 ([forum thread](https://www.erdosproblems.com/forum/thread/742)).
- Effort estimate: large, because exhaustive work on 25-vertex graphs is far beyond direct enumeration and needs a strong reduction first.

## Recommended first three

1. **#475 (Graham's rearrangement conjecture for small primes): likely quick win.** The finite gap is concrete and small (first open case p = 29 with 21 ≤ |A| ≤ 25), test values come free from published theorems, and a complete check of p ≤ 31 or 37 is a new, citable finite statement.
2. **#1072 (primes with f(p) = p − 1): likely quick win.** The code is a few lines, the OEIS data give exact test values, and counts up to 10⁸ directly test a stated belief of Erdős, Hardy and Subbarao against a 1/e heuristic that the existing b-file already seems to favour.
3. **#1100 (the function g(k)): real chance of a new result.** No one has tabulated exact g(k), the forum shows active confusion about its size (a refuted quadratic formula against exponential bounds), and exact values for k up to about 8 would be new.

## Rejected

- #647 (τ(m) + m barrier): searched to 10²² with GPU, Lean-certified to 10⁸, many 2026 posts ([forum thread](https://www.erdosproblems.com/forum/thread/647)).
- #23 (triangle-free to bipartite): exact values to n = 23 in [A389646](https://oeis.org/A389646) and a(5n) = n² proved for n ≤ 40 by a computer-assisted preprint ([arXiv:2606.28041](https://arxiv.org/abs/2606.28041)).
- #617 (balanced colourings of K_{r²+1}): a public repository claims a machine-verified resolution of r = 5 in September 2026 ([repository](https://github.com/RamazanKara/erdos-617-r5-formal-verification)); r = 6 is far larger.
- #993 (unimodality for trees): all trees up to 32 vertices checked in 2026 ([forum thread](https://www.erdosproblems.com/forum/thread/993)).
- #583 (path decompositions): exhaustive to n = 11, n = 12 running as of 17 September 2026 ([forum thread](https://www.erdosproblems.com/forum/thread/583)).
- #628 (Erdős–Lovász Tihany): order-13 census completed in August 2026 ([forum thread](https://www.erdosproblems.com/forum/thread/628)).
- #743 (tree packing): checked for n = 12 in September 2026 ([forum thread](https://www.erdosproblems.com/forum/thread/743)).
- #375 (Grimm's conjecture): verified to 10¹² in August 2026 ([forum thread](https://www.erdosproblems.com/forum/thread/375)).
- #458 (lcm of 1..n and prime gaps): verified to 10²⁰ ([forum thread](https://www.erdosproblems.com/forum/thread/458)).
- #287 (unit fractions with gaps ≤ 2): finite bounds up to about 3.7×10⁶⁰ posted in 2026 ([forum thread](https://www.erdosproblems.com/forum/thread/287)).
- #97 (equidistant vertices of convex polygons): ruled out up to 10 vertices in September 2026, several active projects ([forum thread](https://www.erdosproblems.com/forum/thread/97)).
- #699 (gcd of binomial coefficients): active theoretical progress in 2026 ([forum thread](https://www.erdosproblems.com/forum/thread/699)).
- #128 (dense induced subgraphs force a triangle): computational search already posted July 2026 ([forum thread](https://www.erdosproblems.com/forum/thread/128)).
- #156 (small maximal Sidon sets): exhaustive small cases and new OEIS data in 2026 ([forum thread](https://www.erdosproblems.com/forum/thread/156)).
- #241 (B₃ sets): f(N) computed to N = 320 on the forum ([forum thread](https://www.erdosproblems.com/forum/thread/241)).
- #424 (Hofstadter's ab − 1 sequence): an August 2026 preprint claims positive lower density, which would answer the problem ([arXiv:2608.07910](https://arxiv.org/abs/2608.07910)).
- #1106 (prime factors of partition numbers): data to n = 10⁴ already show F(n) > n from n = 116, and going further needs factoring huge p(n) ([forum thread](https://www.erdosproblems.com/forum/thread/1106)).
- #1055 (Erdős–Selfridge prime classes): [A005113](https://oeis.org/A005113) was extended in May 2026, and the next term is at least 2·a(19) − 1 ≈ 1.3×10¹⁴ by a bound stated in the entry.
- #580 (trees in graphs with many high-degree vertices): SAT-certified for n ≤ 19 in a July 2026 preprint ([forum thread](https://www.erdosproblems.com/forum/thread/580)).
- #472 (Ulam's prime sequence): the question is about an infinite sequence; the forum already notes it runs for at least a million steps ([forum thread](https://www.erdosproblems.com/forum/thread/472)).
- #365 (consecutive powerful numbers): the first question is already answered on the page (Golomb, Walker), and the second is asymptotic ([problem page](https://www.erdosproblems.com/365)).
- #364 and #366 (consecutive powerful and 2-full/3-full numbers): OEIS searches already to 7.38×10²⁸ and 10²² respectively ([#364](https://www.erdosproblems.com/364), [#366](https://www.erdosproblems.com/366)).
- #556 (three-colour Ramsey numbers of cycles): values known only for tiny n ([A389335](https://oeis.org/A389335)), and each new value is a hard multi-colour Ramsey computation.
- #107 (happy ending problem): the next case f(7) is far beyond a single PC; SAT work already exists ([forum thread](https://www.erdosproblems.com/forum/thread/107)).
- #835 (colouring k-subsets / Johnson graphs): the remaining cases k = p − 1 start at J(20,10), too large to colour exactly ([problem page](https://www.erdosproblems.com/835)).
- #19 (Erdős–Faber–Lovász): reduced to finitely many cases, but the threshold from the large-n proof does not appear to be explicit, so a computer cannot finish it yet (our reading, uncertain) ([forum thread](https://www.erdosproblems.com/forum/thread/19)).
- #634 (triangles cut into n congruent triangles): n = 19 is open, but the search is continuous-geometric and existing work is extensive ([problem page](https://www.erdosproblems.com/634)); we did not open Beeson's slides, so the extent of prior search is uncertain.
