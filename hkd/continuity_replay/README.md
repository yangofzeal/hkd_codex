# Recent-prompt continuity replay

Incident: the assistant ended the Finch–Machine task with an unfinished-deliverable report, after the user asked it to continue. The source instruction now explicitly forbids voluntary idling when an authorized next action exists, including during the first 20 seconds after an actual prompt. It does not wait out that window or permit stopping afterward.

`replay.rs` tests a deterministic decision contract with simulated prompt ages. It rejects end-turn decisions with unfinished work and a ready authorized action. Pause, approval/security boundaries, verified completion, and a genuine all-paths blocker are tested separately. The ready-action state is an explicit fixture assumption; this harness does not infer it from prose. Transcript timestamps were not available.

This is not model inference replay, a scheduling hook, or proof that the installed Codex or this hosted session would behave differently. The production integration is prompt assembly in `render_model_instructions`; native build/install and behavioral model evaluation remain separate.

Run from repository root:

```sh
rustc --edition 2024 --test codex-rs/prompts/src/task_continuity.rs -o /tmp/codex-continuity-tests
/tmp/codex-continuity-tests
rustc --edition 2024 hkd/continuity_replay/replay.rs -o /tmp/codex-continuity-replay
/tmp/codex-continuity-replay
```
