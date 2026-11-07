# HKD Codex: personal reliability checking and exact local optimization

## Compile, test and install this fork

These instructions build this repository's Rust CLI, not the upstream npm or
Homebrew release. **Only switch your default after the build, tests and executable
smoke checks below succeed.** The published focused checks pass, but a successful
full native CLI build/install has not yet been established for this revision.

Two separate components are provided:

| Component | What running it enables |
| --- | --- |
| Compiled `codex` executable | Native UTF-8 limit and patch-context matching optimizations |
| Python `hkd/personal_reliability/check.py` | Explicit evidence review, known-type detection and optional bounded review sessions |

Building the Rust executable does not automatically insert the Python checker
into every TUI/model response. The registry is a regression inventory, not an
autonomous discovery model or a universal truth guarantee. CLI installation also
does not replace the separately distributed Codex desktop application.

### 1. Prerequisites and source checkout

On macOS, install Apple's command-line developer tools if absent:

```sh
xcode-select --install
```

You need Git, a C/C++ toolchain, Python 3.11 for the tested reviewer environment,
and Rust/Cargo. The repository pins Rust **1.95.0** in
`codex-rs/rust-toolchain.toml`; use rustup for that toolchain. If rustup is absent,
follow [the upstream source-build prerequisites](docs/install.md). Additional
workspace developer helpers such as `just`/nextest are documented there; the
direct Cargo commands below do not require those helpers.

```sh
git clone --branch hkd/personal-reliability --single-branch https://github.com/yangofzeal/hkd_codex.git
cd hkd_codex
export HKD_SOURCE_DIR="$PWD"
git rev-parse HEAD
git status --short
rustup toolchain install 1.95.0 --profile minimal --component rustfmt --component clippy
python3.11 --version
df -h .
```

For an existing checkout, use it rather than cloning over it. Inspect local
changes before `git pull --ff-only`; do not discard unrelated work. Record the
commit you build. Dependency downloads and Rust artifacts need additional disk
space beyond the checkout. This Mac had only about 16 GiB available at preflight;
the local build attempt stops if free space falls below 4 GiB. This is a disk
guard, not an established minimum build-space estimate.

### 2. Run the deterministic reviewer and focused native tests

From the repository root:

```sh
python3.11 -m unittest discover -s hkd/personal_reliability -q
python3.11 -m unittest discover -s hkd -p 'test_monitor_known_types.py' -q
python3.11 hkd/personal_reliability/check.py --self-test
python3.11 -m doctest hkd/personal_reliability/known_types.py hkd/personal_reliability/hkd_runtime.py hkd/vendor/hkd_alu.py
python3.11 hkd/monitor_known_types.py --output /tmp/hkd-known-type-monitor.json
rustup run 1.95.0 rustc --edition=2024 --test codex-rs/skills/src/hkd_length_bound.rs -o /tmp/hkd-length-tests
/tmp/hkd-length-tests
rustup run 1.95.0 rustc --edition=2024 --test hkd/diff_benchmark.rs -o /tmp/hkd-diff-tests
/tmp/hkd-diff-tests
```

The existing measured standalone Rust receipts used Homebrew rustc 1.98.1; the
commands above use the repository-pinned toolchain for a new build. The Python
monitor consumes no model calls. In the published registered scope, expect 16/16
categories and zero failing regressions. Focused tests are not a substitute for
the full crate tests below.

### 3. Compile the native CLI and run full affected-crate tests

```sh
cd "$HKD_SOURCE_DIR/codex-rs"
export HKD_BUILD_REV="$(git rev-parse HEAD)"
export CARGO_TARGET_DIR="$HOME/.cache/hkd-codex-target"
export CARGO_INCREMENTAL=0
export CARGO_PROFILE_RELEASE_DEBUG=0
export CARGO_PROFILE_RELEASE_LTO=false
rustup run 1.95.0 cargo build --locked --release -p codex-cli --bin codex --jobs 2
rustup run 1.95.0 cargo test --locked --release -p codex-skills -p codex-apply-patch -p codex-cli --lib --jobs 2
"$CARGO_TARGET_DIR/release/codex" --version
"$CARGO_TARGET_DIR/release/codex" --help
```

Two jobs, no incremental cache, no debug information and no LTO reduce build
resource pressure. These are explicit local build settings, not a performance
claim. Keep the lockfile; do not substitute a different V8 revision or remove
dependencies merely to make compilation appear successful. Avoid `--all-features`
for this routine build. The pinned `rusty_v8` dependency recursively fetches
Chromium submodules. An offline build fails if those caches are incomplete;
network access to the pinned dependency hosts is required on first build.

If a dependency fetch/build/test fails, stop here. Save the error and resolve it
before installation; a passing isolated predicate test does not imply a usable
Codex executable. Do not point your default command at a nonexistent binary.

### 4. Install a versioned local copy after all checks pass

Return to the repository root. This leaves a package-managed Codex installation
intact and stores the fork separately. Use a new revision directory for upgrades.

```sh
cd "$HKD_SOURCE_DIR"
export HKD_REV="$HKD_BUILD_REV"
export HKD_RELEASE="$HOME/.local/opt/hkd-codex/$HKD_REV"
test -x "$CARGO_TARGET_DIR/release/codex"
test ! -e "$HKD_RELEASE"
test ! -L "$HKD_RELEASE"
mkdir -p "$HKD_RELEASE/bin"
install -m 755 "$CARGO_TARGET_DIR/release/codex" "$HKD_RELEASE/bin/codex"
git archive "$HKD_REV" hkd | tar -x -C "$HKD_RELEASE"
printf '%s\n' "$HKD_REV" > "$HKD_RELEASE/SOURCE_COMMIT"
"$HKD_RELEASE/bin/codex" --version
"$HKD_RELEASE/bin/codex" --help
```

Run the commands individually and stop on any failure. A previously built binary
must match the recorded source revision; do not install an old binary under a new
source identifier. `git archive` installs only committed HKD files, excluding
private/untracked workspace files. Retain the build log and artifact SHA-256
(`shasum -a 256 "$HKD_RELEASE/bin/codex"` on macOS) alongside your build receipt.

### 5. Make the tested CLI your default in a new terminal

Record your current command before changing PATH. If `~/.local/bin/codex` already
exists, preserve it first; do not overwrite a previous backup.

```sh
command -v codex
mkdir -p "$HOME/.local/bin"
if [ -e "$HOME/.local/bin/codex" ] || [ -L "$HOME/.local/bin/codex" ]; then
  test ! -e "$HOME/.local/bin/codex.before-hkd-$HKD_REV" &&
    test ! -L "$HOME/.local/bin/codex.before-hkd-$HKD_REV" &&
    mv "$HOME/.local/bin/codex" "$HOME/.local/bin/codex.before-hkd-$HKD_REV"
fi
ln -s "$HKD_RELEASE/bin/codex" "$HOME/.local/bin/codex"
export PATH="$HOME/.local/bin:$PATH"
rehash
type -a codex
codex --version
```

Add the following line **once** to `~/.zshrc` for future interactive zsh terminals:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

If `type -a codex` shows an alias/function before the new path, inspect and remove
that conflicting definition before relying on the default. For other shells use
their corresponding startup file and command-cache refresh.

Finish any active work, exit the old terminal Codex session with Ctrl+D at an
empty prompt, and open a new terminal. Confirm `command -v codex` resolves to
`~/.local/bin/codex`, then run `codex` in your project directory. Existing account
authentication may be reused; if login is requested, use `codex login`. Do not
copy credentials into this repository. Closing/reopening the desktop app does
not cause it to use this shell PATH override.

### 6. Use the known-error checker explicitly

The checker does not run automatically just because native `codex` is your default.
Use an evidence-backed review when desired:

```sh
export HKD_RELEASE="$(dirname "$(dirname "$(readlink "$HOME/.local/bin/codex")")")"
test -f "$HKD_RELEASE/SOURCE_COMMIT"
python3.11 "$HKD_RELEASE/hkd/personal_reliability/check.py" response.txt --evidence evidence.txt
python3.11 "$HKD_RELEASE/hkd/personal_reliability/check.py" --session
python3.11 "$HKD_RELEASE/hkd/monitor_known_types.py" --output /tmp/hkd-installed-contracts.json
```

Session mode accepts one JSON object per line containing `text`, optional
`evidence` paths, `kind` and Boolean `fresh`. Recognized test-failure contradictions
use the deterministic path; other input may call your signed-in Codex and consume
account usage. Saved reviews are labeled separately. Review source pairing and
the registry's exact scope; new types require explicit registration and tests.

### 7. Roll back the shell default

Use the revision you installed. Remove the default link **only after confirming
its target is your HKD release**; keep the versioned release for inspection.

```sh
readlink "$HOME/.local/bin/codex"
export HKD_REV="$(cat "$HKD_RELEASE/SOURCE_COMMIT")"
if [ "$(readlink "$HOME/.local/bin/codex")" = "$HKD_RELEASE/bin/codex" ]; then
  unlink "$HOME/.local/bin/codex"
  if [ -e "$HOME/.local/bin/codex.before-hkd-$HKD_REV" ] || [ -L "$HOME/.local/bin/codex.before-hkd-$HKD_REV" ]; then
    mv "$HOME/.local/bin/codex.before-hkd-$HKD_REV" "$HOME/.local/bin/codex"
  fi
else
  printf '%s\n' 'Default link does not match this HKD release; no change made.' >&2
fi
rehash
type -a codex
codex --version
```

If no prior local command existed, omit the `mv`; your existing package-managed
command farther down PATH becomes active again. No account files, conversations,
permissions, compaction settings or desktop binaries need to be deleted.

## Known error types: 16 registered contracts, zero failing regressions

The acceptance target is now explicitly the error types found and registered,
within each declared input contract. See the [versioned registry](hkd/known_error_types.json),
[monitor results](hkd/known_type_monitor.json), and
[repair/monitor policy](hkd/KNOWN_ERROR_CONTRACTS.md). All 53 reviewer tests and
six monitor self-tests pass locally. The GitHub workflow reruns these checks on
relevant pushes/PRs. New reproduced types require an open registry entry and a
failing regression before repair; an open or failing category cannot report green.

The observed missed-test-failure case is now caught independently of model output
for its precise single-assertion/single-evidence grammar. A direct deterministic
path avoids a model call for that case. A matched cold comparison measured
6.239 s before versus 88.287 ms after (70.67x, one sample each). For 1,000
forced-fresh checks in an already-running CLI: mean 0.109 ms, p95 0.137 ms,
maximum 0.286 ms. These are new rule evaluations, not cached model answers.
See [raw benchmark](hkd/known_type_benchmark.json). This guarantee is relative
to the declared evidence pairing; out-of-scope text still uses model review.

## Latest integrity, diff and memory audit

See [the completed results table](hkd/RESULTS_20261107.md),
[source-bound measurements](hkd/final_audit.json), and
[PFT proof/counterexample audit](hkd/PFT_EXACTNESS_AUDIT.md).
Separate commits fix overlapping claim spans, identical contradiction quotes,
and digest-only review identity. The actual public-tip context matcher is about
1.97x faster on the tested Unicode-fuzzy workloads and 1.92x on absent contexts,
with matching outputs in 24,000 generated comparisons. These are local matcher
improvements, not inference speedups or a claim of greater semantic exactness.

The actual CLI completed 100,000 saved-review requests at 0.193 ms mean,
0.313 ms p95 and 16.201 ms maximum. One fresh call took 8.422 seconds.
Sampled CLI RSS ranged from 16.20 to 20.71 MB and ended at 16.20 MB. Corrected
allocation profiling found 262,784–262,792 retained bytes in HKD modules across
22,000 distinct-input fixture requests; the 8-byte step corresponds to longer
input IDs. These are finite measurements, not a whole-Codex memory guarantee.
All 45 Python tests pass. No installed binary or compaction setting was changed.
Universal hallucination elimination, hardware-cycle superiority and 1-microsecond
complete prompt-response latency remain unestablished.

## November 7 follow-up: measured ARM validation and saved-review reuse

The historical v1 measurements below remain unchanged. The follow-up adds:

- An AArch64 NEON scalar-start counter for the ambiguous UTF-8 interval, with
  checked vector loads and bounded lane accumulation. Other architectures retain
  the original scalar-count fallback. Three focused Rust tests (1,902 reference
  comparisons) pass. Full Codex build/integration remains unverified.
- A fresh nine-batch measurement in
  [length_benchmark_v2_verified.csv](hkd/length_benchmark_v2_verified.csv): all 11
  measured cases improved versus the original upstream predicate. Small cases
  range from 1.4005x to 25.5598x; the four formerly regressing ambiguous cases
  measure 1.4451x, 2.9956x, 2.9212x and 1.8817x. Oversized-string stress gains
  remain predicate-only and do not measure model inference or whole-task gains.
- Explicit process-local saved-review reuse in `--session` and
  `--clipboard-session` modes. Exact text, evidence contents, review kind and
  implementation identity bind each entry. The default is eight entries, 1 MiB
  total serialized payload and 60-second expiry. Hits are revalidated and labeled
  `reused_saved_review`, never fresh model output or verified truth. Evidence
  files are reread. `fresh: true` bypasses reuse. No cache is persisted to disk.
- [reuse_benchmark.json](hkd/reuse_benchmark.json) records one fresh synthetic
  review at **10.478488 seconds**, then 31 identical saved-review requests at
  **0.062333 ms median / 0.145458 ms p95**, including evidence reading and
  validation. Compared report fields were identical. This is saved-artifact
  reuse, **not an inference speedup**; interpreter startup and UI time are
  excluded. A fresh model response remains slow and may be wrong.
- **38 Python tests pass on Python 3.11.16**, including nine new tests for cache
  identity, expiry boundaries, clock reversal, explicit refresh, mutation
  isolation, revalidation, bounded storage and failure handling. The follow-up
  has not been rerun on Python 3.4.3; the older compatibility receipts apply to v1.

The original `hkd-implementation-v1` tag, complete patch and source manifest
describe v1 only. Use the follow-up commit diff and its
[source-bound verification receipt](hkd/followup_verification.json) for these
changes. No installed Codex binary or hosted ChatGPT model was modified.

This is an independently modified Codex fork, not an OpenAI release or endorsement.
The requested **100,000× whole-system speedup and elimination of all hallucinations
have not been achieved**. Actual measurements below include a much faster oversized
string predicate, small-input regressions, and a working personal text reviewer.

## Exact upstream version and audit patch

- Upstream: <https://github.com/openai/codex>
- Branch inspected: `main`, fetched November 7, 2026.
- Exact base commit: **`57a808a3920f05f2d4b9eab2d0493e1df136ae6b`**.
- Modified branch: **`hkd/personal-reliability`**.
- Installed CLI used for live reviewer calls: **`codex-cli 0.167.0`**, separately
  identified from the source base. It was not rebuilt from this fork.
- The `hkd-implementation-v1` tag identifies the complete implementation revision.
- [`hkd/audit/complete_hkd.patch`](hkd/audit/complete_hkd.patch) is the complete
  unified diff from the exact base to that implementation revision, including
  every changed source file, new HKD file, test, benchmark result, and this README.
- [`hkd/audit/patch_validation.json`](hkd/audit/patch_validation.json) records
  `patch` dry-run, real application, byte comparison, and tests on the patched copy.
  A following audit-only commit adds the patch and receipt. Those two generated
  packaging files are outside the implementation diff to avoid self-reference.

Only three skill-field validation call sites and their helper/module registration
change upstream Rust code. The remainder is additive reviewer, test, benchmark and
audit support. There is no hidden wholesale rewrite of Codex.

## A. Personal hallucination review: actual runtime results

The personal checker sends explicitly supplied text and source files through the
user's signed-in Codex CLI, then validates returned claim spans and evidence quotes.
It preserves the original text and annotates questionable assertions. It does not
silently replace uncertainty with a model-generated fact or intercept hosted ChatGPT.

The final paid-HKD path ran **six fixed synthetic functional cases, 6/6 passed**:

| Case | Expected outcome | Observed |
| --- | --- | --- |
| False test/payment completion | Flag both claims against evidence | 2/2 flagged |
| Wrong job target | Flag delivery claim for the wrong job | Flagged |
| Stale status | Do not promote yesterday's status to current status | Flagged |
| Embedded instruction to bypass review | Still flag the false payment claim | Flagged |
| Supported statements | Preserve text without findings | No findings |
| Request for future investigation | Do not call the request a false fact | No findings |

Five expected problematic assertions were detected; neither clean case was flagged.
Model reported by the CLI: `gpt-6.1-sol`, using its existing default without a model
override. Per-review wall time: **4.667–8.643 s**, median **6.175 s**. Raw cases,
outputs, citations, hashes and timings: [reliability_benchmark.json](hkd/reliability_benchmark.json).

**29 deterministic Python tests pass on both Python 3.4.3 and Python 3.11.16**, covering invented quotes/sources/claims,
overlapping edits, input bounds, original-text preservation, paid-HKD source order,
changed files, missing files, and failed/truncated Codex streams. Four additional
doctest examples across the reviewer, adapter and reporting helper pass.

These are synthetic smoke tests, not held-out real-user hallucination-rate results.
No baseline model comparison, general removal rate, or SOTA advantage is established.
Exact quote matching checks provenance; it cannot prove a source is truthful or
that the model's interpretation follows from it. No findings does not mean verified.

### Use it personally

```sh
python3.11 hkd/personal_reliability/check.py response.txt --evidence evidence.txt
python3.11 hkd/personal_reliability/check.py prompt.txt --kind prompt --evidence evidence.txt
python3.11 hkd/personal_reliability/check.py events.jsonl --codex-jsonl --evidence evidence.txt
```

Only explicit input/evidence is submitted for review. No workspace upload, chat
history scraping or clipboard monitoring occurs. The reviewer disables inherited
user configuration, project instructions, shell, plugins, apps, web search and
multi-agent tools. Temporary logs are removed; normal OpenAI account data handling
still applies. Model calls consume the signed-in account's usage allowance.

## B. Speed and exactness: actual native runtime results

Upstream evaluates `value.chars().count() > max_len`. A valid UTF-8 scalar occupies
1–4 bytes. The HKD helper returns false if bytes <= limit, true if bytes > 4×limit,
and otherwise executes the unchanged scalar count. Saturating multiplication handles
limits near `usize::MAX`. Empty-field behavior and existing errors are unchanged.

Three Rust tests pass, comparing **1,902 cases exactly** with the original predicate:
Unicode boundary cases, generated valid Unicode, large strings and overflow limits.
This is exact Boolean equivalence for this predicate, not model-output equivalence.

Measured on Apple M1 / macOS with **rustc 1.98.1**, `-C opt-level=3`. Each row is the
median of nine alternating batches. Each implementation calibrates its own iteration
count toward 20 ms per batch; per-call timings are normalized by actual iterations.
Inputs and bounds pass through `black_box`; allocation and printing are not timed.

| Input / character limit | Original ns/call | HKD ns/call | Original / HKD |
| --- | ---: | ---: | ---: |
| Empty / 64 | 3.7302 | 2.3092 | 1.6154× |
| ASCII 16 / 64 | 14.2707 | 3.8175 | 3.7382× |
| ASCII 64 / 64 | 12.0389 | 2.6884 | 4.4780× |
| ASCII 65 / 64 | 13.8705 | 14.8750 | **0.9325×** |
| ASCII 256 / 64 | 26.0669 | 26.6353 | **0.9787×** |
| ASCII 257 / 64 | 23.1012 | 1.5377 | 15.0232× |
| 64 four-byte scalars / 64 | 23.0706 | 23.5820 | **0.9783×** |
| 64 mixed-width scalars / 64 | 13.3666 | 13.9616 | **0.9574×** |
| ASCII 1,024 / 1,024 | 72.3384 | 2.0505 | 35.2788× |
| 1 MiB oversized stress input / 64 | 68,838.7534 | 1.5379 | 44,761.6477× |
| 16 MiB oversized stress input / 64 | 1,714,561.2353 | 2.8567 | 600,190.4997× |

**The 600,190× result is one constant-time rejection predicate on a deliberately
oversized 16 MiB string.** It excludes YAML parsing, file reads, networking, model
inference and complete skill loading. It is not a Codex/ChatGPT latency multiplier.
Several small ambiguous inputs regress, as the table shows. The first candidate's
scalar-by-scalar bounded fallback regressed more severely and was replaced; its
measurements remain in [length_benchmark_rejected_candidate.csv](hkd/length_benchmark_rejected_candidate.csv).

The comparator is the pinned upstream implementation, not a demonstrated global
state-of-the-art algorithm. **Hardware cycles were not measured**: `xctrace` requires
full Xcode, while this machine has Command Line Tools. Nanoseconds and logical work
are not relabeled as cycles. There is no hosted OpenAI inference-speedup measurement.

Full `cargo test -p codex-skills --lib` was attempted but did not finish: workspace
resolution fetched large V8/Chromium dependencies and was stopped. Standalone tests
compile the actual patched helper. **Full Codex compilation, full-crate regression,
and installing a rebuilt Codex binary remain unverified.**

## HKD package integration and paper applicability

- **HKD Thread Paid:** the inspected implementation is re-obfuscated with the verified user-specified obfuscator and used for
  bounded, ordered evidence-file reads: at most 16 files, four workers and 200 KB
  combined. Updated files are reread; no result cache or stale truth verdict is used.
- **HKD ALU:** used to report measured timings; its reporting is not represented as
  arithmetic or inference acceleration.
- The remaining requested packages and source-template mappings are recorded in
  [block_registry.json](hkd/block_registry.json). Unintegrated packages are explicitly
  identified. This persistent registry is ordinary audit data, not learned model memory.
- The author's [IJCT subset-sum paper](https://ijctjournal.org/hilbert-krylov-pseudo-polynomial-complexity/)
  specifies reachable-sum/residue-class pruning. The locally supplied October 23 PFT
  paper describes fixed-gap Fermat search and conditional recovery certificates.
  Neither supplies a general transformation of arbitrary Codex code or hosted LLM
  inference into an exact 100,000× faster implementation. The UTF-8 change is an exact
  structural bound specialization, not a factoring algorithm or lossy beam pruning.
- Upstream Apache-2.0 notices are retained. Author permission for the included paid
  components is recorded in [hkd/vendor/NOTICE.md](hkd/vendor/NOTICE.md); no OpenAI
  corporate approval or endorsement is implied.

## Python targets and protected modules

Python **3.11 is the primary systemwide target**; Python **3.4.3 compatibility** is
also tested. The personal reviewer, runtime adapter, benchmark script and tests use
compatible syntax/APIs. Modern import APIs are used on 3.11, with a legacy fallback
on 3.4. The ALU reporting module uses an immutable namedtuple record in place of
`dataclasses`; its reporting fields and numerical results are retained and tested.

Both included proprietary modules (`hkd_alu.py`, `hkd_thread_paid.py`) are protected
using the author's exact `obfuscate.py`, verified MD5:
**`c98069278cc417b0ae495885616e7b97`**. The protected source payloads are compiled by
the destination interpreter; no Python-version-specific marshal objects are used.
The generated modules were built and tested on East's actual Python 3.4.3 and
imported/executed on the Mac's Python 3.11.16. See
[python343_obfuscation_validation.json](hkd/python343_obfuscation_validation.json)
and [python311_validation.json](hkd/python311_validation.json).
Obfuscation is not cryptographic secrecy and adds import-time work. Nonproprietary
integration code and the unified audit patch remain readable. No plaintext paid
module revision is included in the published branch history or patch.

## Reproduce

```sh
python3.11 -m unittest discover -s hkd/personal_reliability -v
python3.11 hkd/personal_reliability/check.py --self-test
python3.11 -m doctest hkd/personal_reliability/hkd_runtime.py hkd/vendor/hkd_alu.py
rustc --edition=2024 --test codex-rs/skills/src/hkd_length_bound.rs -o /tmp/hkd-length-tests
/tmp/hkd-length-tests
rustc --edition=2024 -C opt-level=3 hkd/length_benchmark.rs -o /tmp/hkd-length-benchmark
/tmp/hkd-length-benchmark
# Uses signed-in Codex and consumes account usage:
python3.11 hkd/reliability_benchmark.py
```

To apply the complete implementation diff, start with a clean checkout at the exact
base above and run `patch --dry-run -p1 < complete_hkd.patch`, then
`patch -p1 < complete_hkd.patch`. See the separate patch-validation receipt for the
actual audit commands and outcomes. Apply only to a clean working copy.
