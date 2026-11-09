//! Local draft generation starts after a 250 ms typing pause.
//! Every edit updates the draft and cancels stale generation and display.
use crate::render::renderable::Renderable;
use crate::tui::FrameRequester;
use ratatui::{
    buffer::Buffer,
    layout::Rect,
    text::Line,
    widgets::{Paragraph, Widget, Wrap},
};
use std::process::Stdio;
use std::sync::{Mutex, OnceLock};
use std::time::{Duration, Instant};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};

const DRAFT_DEBOUNCE: Duration = Duration::from_millis(250);

#[derive(Default)]
struct State {
    draft: String,
    context: String,
    changed: Option<Instant>,
    generation: u64,
    task: Option<tokio::task::JoinHandle<()>>,
    preview: String,
    started: bool,
}
fn state() -> &'static Mutex<State> {
    static STATE: OnceLock<Mutex<State>> = OnceLock::new();
    STATE.get_or_init(|| Mutex::new(State::default()))
}
pub(crate) fn invalidate() {
    if let Ok(mut s) = state().lock() {
        if let Some(task) = s.task.take() {
            task.abort();
        }
        s.generation = s.generation.wrapping_add(1);
        s.draft.clear();
        s.context.clear();
        s.preview.clear();
        s.started = false;
        s.changed = None;
    }
}
fn publish(generation: u64, text: String, frame: &FrameRequester) {
    if let Ok(mut s) = state().lock() {
        if s.generation == generation && !s.draft.is_empty() {
            s.preview = text
                .chars()
                .filter(|c| !c.is_control() || *c == '\n')
                .take(1600)
                .collect();
            frame.schedule_frame();
        }
    }
}
pub(crate) fn observe(draft: &str, context: &str, frame: FrameRequester) {
    let Some(script) = std::env::var_os("CODEX_ANTICIPATION_SCRIPT") else {
        return;
    };
    let Ok(mut s) = state().lock() else {
        return;
    };
    let draft: String = draft.chars().take(4097).collect();
    let context: String = context.chars().take(8192).collect();
    if draft != s.draft || context != s.context {
        if let Some(task) = s.task.take() {
            task.abort();
        }
        s.generation = s.generation.wrapping_add(1);
        s.draft = draft.chars().take(4097).collect();
        s.context = context.chars().take(8192).collect();
        s.preview.clear();
        s.changed = Some(Instant::now());
        s.started = false;
    }
    if !(1..=4096).contains(&s.draft.trim().chars().count()) || s.started {
        return;
    }
    // Wait for a natural typing pause before starting model work.
    frame.schedule_frame_in(DRAFT_DEBOUNCE);
    s.started = true;
    let generation = s.generation;
    let request = serde_json::json!({"draft":s.draft,"context":s.context}).to_string();
    s.task = Some(tokio::spawn(async move {
        tokio::time::sleep(DRAFT_DEBOUNCE).await;
        let run = async {
            let python = std::env::var_os("CODEX_ANTICIPATION_PYTHON")
                .unwrap_or_else(|| "python3.11".into());
            let mut child = tokio::process::Command::new(python)
                .arg(script)
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::null())
                .kill_on_drop(true)
                .spawn()?;
            if let Some(mut stdin) = child.stdin.take() {
                stdin.write_all(request.as_bytes()).await?;
            }
            let stdout = child
                .stdout
                .take()
                .ok_or_else(|| std::io::Error::other("Preview output missing"))?;
            let mut lines = BufReader::new(stdout).lines();
            let mut any = false;
            while let Some(line) = lines.next_line().await? {
                if line.len() > 16384 {
                    return Err(std::io::Error::other("Preview too large"));
                }
                let value: serde_json::Value = serde_json::from_str(&line)?;
                if let Some(text) = value["text"].as_str() {
                    publish(generation, text.to_owned(), &frame);
                    any = true;
                }
            }
            if !child.wait().await?.success() || !any {
                return Err(std::io::Error::other("Local preview unavailable"));
            }
            Ok::<(), std::io::Error>(())
        };
        if !matches!(
            tokio::time::timeout(Duration::from_secs(30), run).await,
            Ok(Ok(()))
        ) {
            publish(
                generation,
                "Local draft preview unavailable. Enter still submits normally.".into(),
                &frame,
            );
        }
    }));
}
pub(crate) struct Dock;
impl Renderable for Dock {
    fn desired_height(&self, width: u16) -> u16 {
        if width < 30 {
            return 0;
        }
        state()
            .lock()
            .map(|s| {
                if preview_visible(&s.preview, s.changed.map(|at| at.elapsed())) {
                    4
                } else {
                    0
                }
            })
            .unwrap_or(0)
    }
    fn render(&self, area: Rect, buf: &mut Buffer) {
        if area.is_empty() {
            return;
        }
        let Ok(s) = state().lock() else {
            return;
        };
        if !preview_visible(&s.preview, s.changed.map(|at| at.elapsed())) {
            return;
        }
        let rows = vec![
            Line::raw("Draft preview · local Llama · unverified · not submitted"),
            Line::raw(s.preview.clone()),
        ];
        Widget::render(Paragraph::new(rows).wrap(Wrap { trim: true }), area, buf);
    }
}

fn preview_visible(text: &str, age: Option<Duration>) -> bool {
    !text.is_empty() && age.is_some_and(|age| age >= DRAFT_DEBOUNCE)
}

#[cfg(test)]
mod timing_tests {
    use super::*;
    #[test]
    fn preview_display_uses_short_typing_debounce() {
        assert!(!preview_visible(
            "partial",
            Some(Duration::from_millis(249))
        ));
        assert!(preview_visible("partial", Some(DRAFT_DEBOUNCE)));
        assert!(!preview_visible("", Some(Duration::from_secs(6))));
        assert!(!preview_visible("stale", None));
    }
}
