# Research rules

These rules apply to every change in this repository.

- Every claim in a problem README or `meta.yaml` gets exactly one label: verified, observed, conjectured, or known.
- A verified claim needs `explore.py` and `verify.py`, using different algorithms, agreeing over the stated range. Both result files are listed under `evidence` in `meta.yaml`.
- Cite only sources that were opened and read. Never cite from memory.
- Read and write every text file as UTF-8 (`encoding="utf-8"`), so non-ASCII names such as "Erdős" survive on every platform.
- Write result files with `erdos.results.write_result` and checkpoints with `erdos.checkpoint.save_checkpoint`.
- Nothing from this repository is submitted to the OEIS.
- Before every commit, run `uv run pytest` and `uv run python -m erdos.status --check`.
