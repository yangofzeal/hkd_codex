# Prepared upstream performance report — not sent

## Maintainer/contact

The documented route is the [openai/codex issue tracker](https://github.com/openai/codex/issues).
At inspected public commit `57a808a3920f05f2d4b9eab2d0493e1df136ae6b`,
`docs/contributing.md` requests detailed issue reports and says external code PRs
are not accepted. `.github/CODEOWNERS` names `@openai/codex-core-agent-team` for
several core paths, but does not assign an owner specifically to `apply-patch`.
No maintainer email is published in those inspected files. Do not substitute
Sam Altman's address or invent a personal maintainer address.

**Email:** no verified public maintainer email available; use the issue tracker.

**Subject:** apply_patch repeatedly normalizes invariant Unicode context patterns;
lazy reuse reduces measured fuzzy-search time about 1.9x

## Body suitable for an issue or an existing maintainer email thread

Hello Codex maintainers,

I reproduced redundant allocation/computation in
`codex-rs/apply-patch/src/seek_sequence.rs` at public main commit
`57a808a3920f05f2d4b9eab2d0493e1df136ae6b`.

In the final Unicode-normalizing fallback, the loop calls `normalise(pat)` at
every candidate source position even though `pat` is unchanged for the search.
For a one-line pattern searched at n positions, this produces n equivalent
pattern strings and normalizations. It is temporary allocation churn; I have
not demonstrated a retained-memory leak or a semantic hallucination caused by it.

I tested a local change that lazily retains each reached pattern line's normal
form once within that search. Source-line normalization, strictness-pass order,
start/eof behavior and first-match selection remain unchanged. Lazy construction
avoids processing a large pattern suffix when its first line never matches.

On the recorded Apple Silicon/macOS test host, using rustc 1.98.1 and optimized
standalone builds of the actual two matcher implementations, 21 alternating
batches per input at 64/1,024/16,384 lines gave:

| Category | Ratio of mean baseline/candidate latency | Minimum per-size ratio |
| --- | ---: | ---: |
| Unicode-fuzzy context at end | 1.973x | 1.952x |
| No matching context | 1.924x | 1.921x |
| Long-pattern early mismatch | 1.262x | 1.235x |
| Exact context at end | 1.058x | 1.053x |

The near-1x exact-path difference is not claimed as a robust algorithmic gain.
These are per-context-matcher wall times, not whole-Codex or model inference
measurements. Hardware cycles were not measured.

The harness compares 24,000 generated baseline/candidate cases (including
whitespace, Unicode punctuation, empty/oversized patterns, start offsets and
EOF mode); nine focused tests pass, including both copies of the original tests.
Full Cargo tests/build were not completed in the recorded audit because the
environment lacked cached V8/Chromium dependencies; a new online build is being
attempted separately. No full-application or memory-leak resolution is claimed.

Reproduction in my fork:

```sh
git clone --branch hkd/personal-reliability https://github.com/yangofzeal/hkd_codex.git
cd hkd_codex
git checkout e2eedaa24f
rustc --edition=2024 --test hkd/diff_benchmark.rs -o /tmp/hkd-diff-tests
/tmp/hkd-diff-tests
rustc --edition=2024 -C opt-level=3 hkd/diff_benchmark.rs -o /tmp/hkd-diff-benchmark
/tmp/hkd-diff-benchmark
```

Implementation and audit links:

- [Reference change](https://github.com/yangofzeal/hkd_codex/commit/e2eedaa24f)
- [Raw per-size timings and observed maxima](https://github.com/yangofzeal/hkd_codex/blob/e2eedaa24f/hkd/diff_benchmark.csv)
- [Benchmark and differential tests](https://github.com/yangofzeal/hkd_codex/blob/e2eedaa24f/hkd/diff_benchmark.rs)
- [Unchanged public-tip baseline](https://github.com/yangofzeal/hkd_codex/blob/e2eedaa24f/hkd/baselines/seek_sequence_tip.rs)

I am providing the reproduction, measured scope and possible approach for your
review through the documented issue channel, rather than claiming an accepted
upstream fix or submitting an unsolicited code PR.

Best,
Michael Yang
