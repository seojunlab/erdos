# erdos

Computer experiments on open problems of Paul Erdős, done together with an AI assistant.

The problems come from [erdosproblems.com](https://www.erdosproblems.com), which lists more than a thousand of them; about half are still open. Many can be probed by computer: search for a counterexample, extend the range where a statement has been checked, or collect data that sharpens a guess. This repository does that one problem at a time and writes up each result so a non-specialist can follow it.

## How this research is done

We do this research together with AI. AI can make mistakes that look convincing, so every result here follows these rules:

| Label | Meaning |
|---|---|
| **Verified** | Two independent programs, using different methods, agree over the stated range. Both output files are in the repository. |
| **Observed** | Seen in one computation, not yet checked by a second. |
| **Conjectured** | A pattern we believe but have not established. |
| **Known** | Already in the literature, with a link to the source. |

- Every citation points to a source that was opened and read, never recalled from memory.
- Every result file records the parameters, code version, and date that produced it.
- Failed attempts stay in the repository with a note on why they stopped.

If you spot an error, please [open an issue](https://github.com/seojunlab/erdos/issues).

Sequence data computed here is published in this repository only. We do not submit to the OEIS, whose [rules](https://oeis.org/wiki/Use_of_AI_for_OEIS_Submissions_is_Forbidden) restrict AI-assisted submissions.

## Status

See [STATUS.md](STATUS.md) for every problem attempted so far.

## Layout

```
src/erdos/        shared tools: meta.yaml checks, result files, checkpoints, status builder
problems/NNNN-*/  one folder per Erdős problem (NNNN is its number on erdosproblems.com)
  README.md       the problem in plain words, what is known, our results, attempts log
  meta.yaml       machine-readable status and labelled claims
  explore.py      primary computation
  verify.py       independent second computation
  results/        output data with provenance headers
  figures/        plots
  tests/          small cases checked against published values
```

## Running the code

Install [uv](https://docs.astral.sh/uv/), then:

```bash
uv sync
uv run pytest
uv run python -m erdos.new_problem 1234 short-name --title "Plain title"
uv run python -m erdos.status
```

## License

Code is under the [MIT License](LICENSE). Text, figures, and data are under [CC BY 4.0](LICENSE-CONTENT.md).
