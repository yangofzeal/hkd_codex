//! Session-scoped heartbeat for explicitly registered background work.
//! Stale, malformed and terminal records never imply activity.
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

fn path() -> Option<PathBuf> {
    let node = std::env::var("CODEX_TASK_NODE").ok()?;
    if node.is_empty() || node.len() > 64 || !node.bytes().all(|c| c.is_ascii_alphanumeric() || b"_-".contains(&c)) { return None; }
    let home = std::env::var_os("CODEX_HOME").map(PathBuf::from)
        .or_else(|| std::env::var_os("HOME").map(|h| PathBuf::from(h).join(".codex")))?;
    Some(home.join("session-status").join(node).join("background-activity.txt"))
}
fn running(text: &str, now: u64) -> bool {
    if text.len() > 1024 { return false; }
    let mut rows = text.lines();
    if rows.next() != Some("v1") || rows.next() != Some("running") { return false; }
    let Some(stamp) = rows.next().and_then(|s| s.parse::<u64>().ok()) else { return false; };
    now.checked_sub(stamp).is_some_and(|age| age < 45)
        && rows.next().is_some_and(|s| !s.trim().is_empty())
}
pub(crate) fn monitored() -> bool { path().is_some_and(|p| p.is_file()) }
pub(crate) fn active() -> bool {
    use std::io::Read;
    let Some(p) = path() else { return false; };
    let Ok(file) = std::fs::File::open(p) else { return false; };
    let mut text = String::new();
    if file.take(1025).read_to_string(&mut text).is_err() { return false; }
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs();
    running(&text, now)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn heartbeat_lifecycle() {
        assert!(running("v1\nrunning\n100\nCompile Codex\n", 144));
        for state in ["done", "blocked", "failed", "paused", "idle"] {
            assert!(!running(&format!("v1\n{state}\n100\nCompile Codex\n"), 101));
        }
        assert!(!running("v1\nrunning\n100\nCompile Codex\n", 145));
        assert!(!running("v1\nrunning\n100\nCompile Codex\n", 99));
        assert!(!running("v1\nrunning\n100\n\n", 101));
        assert!(!running("broken", 101));
        assert!(!running(&"x".repeat(1025), 101));
    }
}
