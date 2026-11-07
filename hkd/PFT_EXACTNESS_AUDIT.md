# PFT applicability, exact contracts and demonstrated limits

This is a mathematical/source audit of the HKD fork, not a proof that a language
model cannot hallucinate. The counterexamples below disprove that universal claim
for the current architecture. Narrower exact properties can be established.

## 1. What fixed-gap PFT proves

The author's locally supplied `PFT_Compressive_Sensing_verified_v2.tex` states the
restricted Fermat-search theorem. For distinct odd primes p < q, let

    A = (p+q)/2, d = (q-p)/2, N = pq = A²-d².
    K = A-ceil(sqrt(N))+1
      = floor(d²/(A+sqrt(A²-d²)))+1.

The only nontrivial factor pair occurs at A. Rationalizing A-sqrt(A²-d²) gives the
second expression. With d fixed, the denominator increases with A, so K cannot
increase. If d² < 2A-1, then (A-1)² < N < A² and K=1. This is an exact, conditional
search-count statement. K never reaches zero; the bit cost of arithmetic can grow.
The published 50-to-65-digit examples share d=1916192221400349 and have counts
298323 and 1. This does not imply monotone wall-clock or hardware-cycle reduction.

At fixed ratio q/p=r>1 instead, A-sqrt(N) is proportional to sqrt(N):

    A-sqrt(N) = ((sqrt(r)-1)² / (2sqrt(r))) * sqrt(N).

Thus input size alone does not imply easier factoring. Code length is not this
semiprime N; no mapping from arbitrary code/evidence to fixed-gap instances with
preserved semantic truth and cheaper reconstruction has been supplied.

## 2. Why thinning cannot certify arbitrary factual truth

Let O be everything the checker observes (text, evidence and model result), and
W be the world. Two worlds can have identical O but different truth values for
an unobserved fact. A deterministic checker receiving O returns the same result
in both worlds. It cannot certify that fact correctly in both unless it obtains
additional distinguishing evidence or abstains. A randomized checker has the
same output distribution on identical O, so randomization does not remove this
problem. Exact arithmetic does not supply missing information.

Likewise, if a thinning function T maps distinct relevant inputs x and y to the
same retained state but a required answer differs, any decoder of T(x)=T(y)
fails on at least one input. Exact thinning requires a restricted admissible
domain plus an injectivity/recovery certificate, or preservation of every
distinction required by the requested answer. Fixed-gap factoring does not
establish those conditions for arbitrary text or arbitrary programs.

Historical counterexample at commit `3c3e731ddd`: text says "All tests passed.",
evidence says "Two tests failed.", and the model returns `findings: []`.
The old validator returned `no_issues_flagged`. The empty array is schema-valid.
Therefore structural validation is not a proof of semantic completeness.
The report explicitly returns `truth_certified: false` and
`semantic_completeness_verified: false`. Those labels alone did not repair
detection. The subsequent known-type update now deterministically repairs this
specific omission for the grammar and single-source pairing declared in
`known_error_types.json`, independent of the model output. It routes detected
cases without a model call. Other syntax is explicitly out of scope; the rule
does not assert completeness over arbitrary natural-language omissions.

## 3. Exact contracts repaired separately

1. **Span uniqueness.** `str.count` ignored overlapping occurrences. `aaa`/`aa`
   passed despite starts 0 and 1. Find the first occurrence i, then search from
   i+1. No earlier occurrence exists by minimality of i, and no later occurrence
   exists iff that second search fails. This proves uniqueness, including overlap.
   The suite also checks 3,937 exhaustive small-alphabet text/claim pairs.
2. **Insufficient contradiction evidence.** An identical claim and quoted source
   previously passed with verdict `contradicted` and a fabricated reason. Such
   findings are now rejected. This does not solve arbitrary entailment: an
   unrelated exact quote or an invented explanation can still be proposed by a
   model. Provenance checks and semantic truth remain different properties.
3. **Exact reuse identity.** Canonical input bytes are dictionary keys; hash
   collision resolution uses byte equality. Reuse no longer assumes a SHA-256
   digest is injective. The key includes implementation identity, kind, full text
   and evidence contents. Both key bytes and serialized payload count toward the
   1 MiB limit; at most eight entries remain. Expired entries are removed on the
   next request. These bounds exclude Python object and allocator overhead.

These are deterministic HKD application integrity improvements. They are not a
new Factor 50 solver or proof of superiority over every state-of-the-art system.

## 4. Exact diff-work reuse versus public Codex tip

Public `openai/codex` main was checked at
`57a808a3920f05f2d4b9eab2d0493e1df136ae6b` on November 7, 2026. The baseline
context matcher is copied verbatim under `baselines/seek_sequence_tip.rs`.

The matcher formerly normalized the same immutable pattern line on each search
position. The patch computes that deterministic normal form once, lazily, and
reuses it. Earlier exact/whitespace passes, order, start/eof handling and match
results are unchanged. Induct on visited pattern indices: each cached value is
the same `normalise(pattern[j])` as the baseline. Thus every comparison and first
match is identical. Lazy creation avoids normalizing unvisited pattern suffixes.
The benchmark contains 24,000 generated baseline/candidate comparisons and the
eight original test instances across the two implementations.

For a one-line fuzzy/missing pattern searched at n positions, pattern
normalizations decrease from n to 1. Source-line normalization and search still
grow with n; total work is not decreasing with code size. This is exact reuse of
invariant work, not a general PFT inverse-size law. It improves performance while
preserving baseline matching semantics; it does not make fuzzy matching more
semantically exact. Full patch generation, disk writes and model inference are
outside this isolated context-matcher benchmark.

## 5. Prompt latency, memory and compaction

The real JSONL CLI benchmark includes input/output IPC, evidence-file rereading,
exact reuse identity, validation, serialization, flush and parsing. A saved review
is not a new model answer. Fresh model calls remain separately timed. Processing
arbitrary new L-byte inputs and returning R-byte outputs has unavoidable data
movement; a universal zero-latency guarantee is impossible. One microsecond is
not established for the complete path. No hardware cycle counter was measured.

The stress test measures current RSS and traced Python allocations, not just
peak RSS. Distinct-input eviction stress uses a labeled fixture reviewer; the
separate actual CLI stress uses one real model call followed by repeated saved
reviews. A finite plateau supports bounded retention for those workloads only.
It cannot establish absence of all memory leaks in the entire Codex application.

Model context capacity is distinct from process RSS. The public configuration
contains `model_context_window` and `model_auto_compact_token_limit`. Disabling
compaction does not increase model context capacity. Preserving arbitrary,
unbounded conversation information in a bounded state without loss is impossible;
external storage/retrieval can shift the storage requirement but adds work.
No compaction setting or installed Codex binary was changed here, and no claim
of matching iTerm2 memory or eliminating all restart conditions is made.

## Unresolved scope

False or stale sources, omitted findings, semantic misinterpretation and invented
model explanations remain possible. Native Rust checks preserve exact local
contracts; they do not certify real-world facts. Full workspace tests are blocked
by unavailable offline V8/Chromium submodules; focused tests compile the actual
changed Rust modules. The report must not say all hallucinations are gone.
