# Reviewed HKD runtime update bundle — November 9, 2026

This branch publishes the current tested change bundle without claiming a new installed release. Source snapshots retain their original repository paths under `source/`. They depend on the local native integration described by the existing release manifest; they are not a drop-in standalone distribution.

Implemented locally: indexed changed-job persistence; 250 ms local draft-preview debounce; one `[speech]` button selecting the latest reply and restarting on each click; exact fixed-sequence progress stacked below Working. The source snapshot and full native release validation remain distinct.

Validation: 18 worker lifecycle tests and four persistence/atomicity tests passed. Compiled preview lifecycle and speech-button tests passed; local speech generated 3.296 seconds of non-silent audio and afplay exited successfully. Progress projection tests passed. Full revised native release validation is pending. The source-host V8 download returned HTTP 404; the build retains a previously verified host only after checking recorded native inputs and transport.

`pft.py INPUT.py -o OUTPUT.py` parses without executing the input and specializes supported `sum(range(...))` expressions. `--memoize NAME` opts narrowly checked pure functions into bounded exact-key caching. Unsupported code is retained. Existing demos remain available with `--self-test`. The converter passed eight tests including 2,000 randomized range comparisons. This is not a general polynomial-time compiler.

`hkd_pft_handler.py --self-test` passes ten doctests. It provides a bounded transitions/async collector and indexed progress. The 1 ms value is a requested local acknowledgment target, not a universal guarantee or a model-reply SLA. Requires Python 3.10+ and transitions==0.9.3. Legacy behavior is available only through explicit `--legacy` delegation to the original local handler.

The local ladder measured deterministic integer-square replies through the async handler with an in-memory sink. It excludes model inference, network latency and durable I/O. Absolute latency did not decrease monotonically. Output equivalence passed; progress-index relative gains increased with retained history.

The diagram distinguishes installed upstream 0.167.0 comparisons, source-level reference algorithms, and prior-HKD worker comparisons. No same-version full-CLI SOTA comparison, hardware-cycle superiority, P=NP proof, Gemini advantage or token-saving measurement is established.

Existing paid packages remain in their supplied obfuscated form at `hkd/vendor/hkd_alu.py` and `hkd/vendor/hkd_thread_paid.py`. No additional plaintext paid implementation is included in this review bundle; the new converter is an independent exact-specialization utility. Obfuscated-only proposed employee licensing is USD 999/month per employee per agreed package, subject to purchaser agreement.

Open incident: response_continuity_silence_20261109. The user reported missed acknowledgments following interrupted turns. Root cause and a hosted-service fix are not established. No latency guarantee is claimed.
