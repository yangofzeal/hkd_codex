# Personal text checker

For explicit process-local review reuse:

```sh
python3.11 hkd/personal_reliability/check.py --session
python3.11 hkd/personal_reliability/check.py --clipboard-session --evidence evidence.txt
```

Session mode accepts one JSON object per line, with `text`, optional `evidence`
file paths, `kind` and Boolean `fresh`. Clipboard mode reads only when you run it
and press Enter; it does not monitor your clipboard. Saved reviews expire after
60 seconds, are bounded to eight entries and 1 MiB, and are erased on exit.
Identical text/evidence/kind may reuse a revalidated saved assessment, explicitly
labeled as reused. Set `fresh` to true for a new model call. Reuse does not refresh
world facts, guarantee truth or accelerate fresh model inference. See
[`../reuse_benchmark.json`](../reuse_benchmark.json) for measured boundaries.

Review copied ChatGPT text with your signed-in Codex CLI:

```sh
python3 hkd/personal_reliability/check.py response.txt --evidence evidence.txt
python3 hkd/personal_reliability/check.py prompt.txt --kind prompt --evidence evidence.txt
```

A separate local copied-text launcher is installed on the author’s Mac; it is
not part of the upstream application or an automatic ChatGPT interception hook.
Without source files, factual statements may remain unverified.

The selected text and explicit evidence files are sent to OpenAI through your
existing Codex login. The wrapper does not upload your workspace or read chat
history. It disables inherited user configuration, project instructions, shell,
plugins, apps, web search and multi-agent tools for the reviewer. Temporary process
logs and model output are removed after the call; OpenAI's account data handling
still applies. CLI `--ephemeral` avoids persisting a normal local Codex session.

The report preserves original text and marks problematic spans. Exact source
quotes appear beside the findings. This is a review aid, not an invisible edit to
hosted ChatGPT. It does not automatically act on any prompt or suppress material
uncertainty. The model's semantic judgments may be wrong; quote matching proves
only that the text occurs in the supplied source, not that the source is true or
that it entails the judgment. No flags means no issues flagged, not certified truth.

## Codex response-stream adapter

```sh
# Review a recorded single-turn stream produced by codex exec --json:
python3 hkd/personal_reliability/check.py events.jsonl --codex-jsonl --evidence evidence.txt
```

Only the last completed agent message is reviewed. Tool output is not treated as
trusted proof. Failed/truncated/multiple-turn streams release no reviewed answer.
The adapter supports the event types inspected at public Codex main commit
`57a808a3920f05f2d4b9eab2d0493e1df136ae6b`. The installed runtime tested is
`codex-cli 0.167.0`; this is not a claim that it is built from that main commit.

## Validation

```sh
python3 hkd/personal_reliability/check.py --self-test
python3.10 -m unittest discover -s hkd/personal_reliability -v
```

`smoke_result.json` records an actual signed-in model review of explicitly
synthetic test material. It is not a human-incident benchmark, exhaustive
hallucination evaluation, or an HKD/PFT mathematical result. No hosted model or
installed Codex binary has been modified.
