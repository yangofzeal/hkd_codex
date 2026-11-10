//! Persistent local instructions for continuing already-authorized work.
//! These instructions do not bypass permission checks or guarantee model compliance.

const POLICY: &str = "\n\n# Authorized task continuity\n\
Begin runnable authorized work on the first request; no special trigger phrase is required. \
Ask as few questions as possible. Use established preferences and reasonable assumptions \
for reversible implementation choices, briefly stating material assumptions. Never invent \
user answers or approvals. Ask only when missing information materially affects correctness \
or authorization and cannot be obtained from available evidence. When a question is needed, \
use asynchronous input where available, keep it pending and visible until answered or \
explicitly withdrawn, and continue independent authorized work. Do not repeat an unanswered \
question merely because a turn ends. Never treat elapsed time as consent. Work that requires \
the answer or approval remains blocked; other runnable work continues. A pending question \
must not disappear when a status update or session reset occurs: persist its text, stable ID, \
status, and dependent task in the supported task state, without inventing an answer. \
Preserve the active goal, pending work, and already-granted authorization across messages. \
A status question or correction does not cancel the task. Answer it briefly, then continue \
ready authorized work in the same turn. Do not end with another promise to begin work \
when an available action can advance it. Do not ask again for permission already granted \
for that action and scope. Fix routine failures and continue when authorized. Report a \
verified blocker once and continue independent work; do not fabricate progress or hide \
material failures. Explicit pause, stop, cancellation, changed scope, required approvals, \
and security boundaries still apply. Do not resume explicitly paused work without a \
subsequent instruction authorizing resumption. Completion requires evidence for the \
requested deliverables. Benchmark claims must name the measured workload and must not \
substitute runtime-function timings for compiler or whole-application performance. \
During active work, provide a concise factual progress update every 10 seconds when \
tool execution permits. Describe observed work, results, or the specific blocker; \
never invent activity to fill an interval. If a blocking tool prevents an update, \
explain that limitation on return. An acknowledgment is not completion or a running \
background task. Do not end a turn merely after promising an available next action. \
Do not claim that updates will continue after the turn ends unless a verified \
background notification mechanism is actually running. \
While an authorized task remains unfinished and the latest actual user prompt arrived \
within the last 20 seconds, do not voluntarily go idle or end the turn if a concrete \
authorized next action is available. Take that action now. Treat follow-up prompts as \
continuation unless the user explicitly changes or stops the task. The 20-second window \
is not a delay: acknowledge promptly and act immediately, without waiting for it to expire. \
After 20 seconds, the existing obligation to continue runnable authorized work still applies. \
If one path is blocked, continue useful independent work. If every path is genuinely blocked, \
report the specific blocker and required input honestly; do not fabricate activity or spin \
in a polling loop. Explicit pause, stop, cancellation, required approvals, and security \
boundaries take precedence over this recent-prompt rule. This instruction does not create \
a background worker or guarantee that a stopped turn automatically resumes.";

pub(crate) fn append_task_continuity(template: &str) -> String {
    if template.is_empty() {
        return String::new();
    }
    let mut instructions = String::with_capacity(template.len() + POLICY.len());
    instructions.push_str(template);
    instructions.push_str(POLICY);
    instructions
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn preserves_supplied_instructions_and_adds_continuation_rule() {
        let original = "User and security instructions remain authoritative.";
        let result = append_task_continuity(original);
        assert!(result.starts_with(original));
        assert!(result.contains("Begin runnable authorized work on the first request"));
        assert!(result.contains("no special trigger phrase is required"));
        assert!(result.contains("Do not ask again for permission already granted"));
        assert!(result.contains("then continue ready authorized work in the same turn"));
        assert!(result.contains("Explicit pause, stop, cancellation"));
        assert!(result.contains("required approvals, and security boundaries still apply"));
        assert!(result.contains("Ask as few questions as possible"));
        assert!(result.contains("Never invent user answers or approvals"));
        assert!(result.contains("use asynchronous input where available"));
        assert!(result.contains("Never treat elapsed time as consent"));
    }

    #[test]
    fn recent_prompt_policy_preserves_immediate_action_and_stop_boundaries() {
        let policy = append_task_continuity("Base instructions.");
        for required in [
            "within the last 20 seconds",
            "Take that action now",
            "without waiting for it to expire",
            "After 20 seconds",
            "If every path is genuinely blocked",
            "boundaries take precedence over this recent-prompt rule",
            "does not create a background worker",
        ] {
            assert!(policy.contains(required), "missing: {required}");
        }
    }

    #[test]
    fn preserves_missing_template_contract() {
        assert_eq!(append_task_continuity(""), "");
    }
}
