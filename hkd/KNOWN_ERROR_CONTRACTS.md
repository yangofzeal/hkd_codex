# Known error contracts: repair, regress, monitor

The acceptance target is the types we have explicitly registered, within each
declared input contract. It is not a claim about all possible language-model
errors. `known_error_types.json` is the versioned inventory; each row includes
a stable category ID, exact scope, regression tests and enforcement status.

Run `python3 hkd/monitor_known_types.py`. The output names every category and
fails if a category is open, missing its test/scope, skipped, expected-failing,
or actually failing. A passing run means zero failing registered regressions.
`known_type_monitor.json` binds the result to registry and implementation hashes.
The GitHub workflow reruns the deterministic suites and monitor on relevant
pushes and pull requests. It consumes no model calls and does not monitor the
contents of hosted ChatGPT conversations.

## Newly repaired omission and direct response path

The registered `missed_explicit_test_failure` rule covers exactly one unqualified
assertion `All tests passed.` (outer whitespace allowed), paired by the caller
with exactly one supplied source of the form `N test(s) failed.`. N is 0 through
999999999 without leading zeroes, or the words One/Two. Positive counts produce
a deterministic contradiction finding, even if a model returned no findings.
Zero counts mean no conflict under this rule, not proof that every test ran or
passed. Quotations, questions, named/mismatched runs, multiple sources and other
prose are out of scope, and still use the evidence-assisted review path.

The direct path returns its deterministic finding without calling a model.
It reports `mode=deterministic_known_type`, `fresh_model_call=false` and a rule
version. This is distinct from saved-review reuse. Unit tests forbid a subprocess
call on the known path and confirm the model path remains for out-of-scope text.

For the positive-count contract, detection follows directly: the assertion says
there are no failed tests; paired evidence supplies integer f>0; the detector
checks f>0 and unconditionally supplies the review finding. This is sound and
complete for that contradiction predicate relative to the declared evidence
pairing. It does not certify the source's truth, freshness or real-world run ID.

## Adding the next discovered category

1. Preserve the counterexample and identify whether it was a live failure or a
   constructed validator fixture. Do not publish private source/user text.
2. Add a new stable registry ID with precise input scope, a failing regression,
   and `status=open`. Do not silently merge a new error into a passing category.
3. Repair the detector or execution path; add adverse and out-of-scope controls.
4. Mark it enforced only when the regression passes. Rerun the monitor, relevant
   suites and benchmarks, then update source-bound receipts and reports.

Unknown categories are not automatically claimed detected. A newly identified
type is added by this review-and-regression process. Existing passing categories
cannot be relabeled as a universal PFT truth guarantee.
