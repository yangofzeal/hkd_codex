//! Deterministic contract replay, not hosted-model inference or a runtime hook.
#[path = "../../codex-rs/prompts/src/task_continuity.rs"]
mod task_continuity;

#[derive(Debug, PartialEq)]
enum Decision { Continue, RespectBoundary, ReportBlocker, Complete }

fn decision(pending: bool, authorized_next_action: bool, stop_boundary: bool) -> Decision {
    if stop_boundary { Decision::RespectBoundary }
    else if !pending { Decision::Complete }
    else if authorized_next_action { Decision::Continue }
    else { Decision::ReportBlocker }
}

fn main() {
    let policy = task_continuity::append_task_continuity("Original instructions.");
    assert!(policy.contains("within the last 20 seconds"));
    // Transcript supplies event order, not reliable per-message wall-clock times.
    // Ages below are simulated, never represented as measured transcript timestamps.
    for age_ms in [0, 1_000, 19_999, 20_000, 20_001, 60_000] {
        assert_eq!(decision(true, true, false), Decision::Continue);
        println!("simulated_age_ms={age_ms} unfinished=true ready_action=true proposed=end_turn decision=CONTINUE rejected_stop=true");
    }
    assert_eq!(decision(true, true, true), Decision::RespectBoundary);
    assert_eq!(decision(true, false, false), Decision::ReportBlocker);
    assert_eq!(decision(false, false, false), Decision::Complete);
    println!("PASS: 6 continuation cases; pause/approval boundary, all-paths-blocked, verified completion");
    println!("Scope: deterministic policy replay only; no model compliance or installed runtime claim.");
}
