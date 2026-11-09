//! One [speech] button reads the latest response from the start on every click.
use crate::render::renderable::Renderable;
use crate::tui::FrameRequester;
use ratatui::{buffer::Buffer, layout::Rect, text::Line, widgets::Widget};
use std::process::Stdio;
use std::sync::{Mutex, OnceLock};
use std::time::Duration;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};

#[derive(Default)]
struct State {
    male: bool,
    reply: bool,
    area: Rect,
    status: String,
    task: Option<tokio::task::JoinHandle<()>>,
    generation: u64,
}
fn state() -> &'static Mutex<State> {
    static STATE: OnceLock<Mutex<State>> = OnceLock::new();
    STATE.get_or_init(|| {
        let mut s = State::default();
        if let Some(home) = crate::runtime_widgets::config_home() {
            if let Ok(bytes) = std::fs::read(home.join("hkd-speech.json")) {
                if bytes.len() <= 4096 {
                    if let Ok(v) = serde_json::from_slice::<serde_json::Value>(&bytes) {
                        s.male = v["voice"] == "male";
                        s.reply = v["source"] == "reply";
                    }
                }
            }
        }
        Mutex::new(s)
    })
}
pub(crate) fn enabled() -> bool {
    std::env::var_os("CODEX_SPEECH_SCRIPT").is_some()
}
pub(crate) enum Action {
    None,
    Speak(bool),
    Changed,
}
pub(crate) fn click(x: u16, y: u16) -> Action {
    let Ok(mut s) = state().lock() else {
        return Action::None;
    };
    if !s.area.contains((x, y).into()) {
        return Action::None;
    }
    if x.saturating_sub(s.area.x) < 8 { Action::Speak(true) } else { Action::None }
}
fn publish(id: u64, status: String, frame: &FrameRequester) {
    if let Ok(mut s) = state().lock() {
        if s.generation == id {
            s.status = status;
            frame.schedule_frame();
        }
    }
}
pub(crate) fn speak(text: String, frame: FrameRequester) {
    let Ok(mut s) = state().lock() else {
        return;
    };
    if s.task.as_ref().is_some_and(|t| !t.is_finished()) {
        if let Some(task) = s.task.take() {
            task.abort();
        }
        s.generation = s.generation.wrapping_add(1);
        // A new click restarts the latest response instead of acting as Stop.
        s.status = "Restarting from beginning…".into();
    }
    if text.trim().is_empty() || text.chars().count() > 8000 || text.len() > 32768 {
        s.status = "No response yet, or response exceeds 8000 characters".into();
        frame.schedule_frame();
        return;
    }
    let Some(script) = std::env::var_os("CODEX_SPEECH_SCRIPT") else {
        return;
    };
    let Some(python) = std::env::var_os("CODEX_SPEECH_PYTHON") else {
        s.status = "Speech Python is not configured".into();
        return;
    };
    s.generation = s.generation.wrapping_add(1);
    let id = s.generation;
    let voice = if s.male { "male" } else { "female" };
    s.status = "Generating local speech…".into();
    frame.schedule_frame();
    s.task = Some(tokio::spawn(async move {
        let run = async {
            let file = tempfile::Builder::new().suffix(".wav").tempfile()?;
            let mut child = tokio::process::Command::new(python)
                .arg(script)
                .args(["--voice", voice, "--output"])
                .arg(file.path())
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::null())
                .kill_on_drop(true)
                .spawn()?;
            if let Some(mut stdin) = child.stdin.take() {
                stdin.write_all(text.as_bytes()).await?;
            }
            let stdout = child
                .stdout
                .take()
                .ok_or_else(|| std::io::Error::other("Speech output missing"))?;
            let mut lines = BufReader::new(stdout).lines();
            while let Some(line) = lines.next_line().await? {
                if let Ok(v) = serde_json::from_str::<serde_json::Value>(&line) {
                    if let (Some(done), Some(total)) = (v["done"].as_u64(), v["total"].as_u64()) {
                        if total > 0 && done <= total {
                            publish(id, format!("Generating {done}/{total} chunks"), &frame);
                        }
                    }
                }
            }
            if !child.wait().await?.success() {
                return Err(std::io::Error::other("Speech generation failed"));
            }
            publish(id, "Speaking latest response · click speech to restart".into(), &frame);
            let status = tokio::process::Command::new("/usr/bin/afplay")
                .arg(file.path())
                .kill_on_drop(true)
                .status()
                .await?;
            if !status.success() {
                return Err(std::io::Error::other("Audio playback failed"));
            }
            Ok::<(), std::io::Error>(())
        };
        let status = match tokio::time::timeout(Duration::from_secs(600), run).await {
            Ok(Ok(())) => "Ready · local Kokoro".to_string(),
            Ok(Err(e)) => format!("Speech unavailable: {e}"),
            Err(_) => "Speech timed out".into(),
        };
        publish(id, status, &frame);
    }));
}
pub(crate) struct Dock;
impl Renderable for Dock {
    fn desired_height(&self, width: u16) -> u16 {
        u16::from(enabled() && width >= 8)
    }
    fn render(&self, area: Rect, buf: &mut Buffer) {
        let Ok(mut s) = state().lock() else {
            return;
        };
        s.area = area;
        if area.is_empty() {
            return;
        }
        Widget::render(Line::raw(format!("[speech] {}", s.status)), area, buf);
    }
}


#[cfg(test)]
mod speech_button_tests {
    use super::*;
    static TEST_LOCK: Mutex<()> = Mutex::new(());
    #[test]
    fn single_button_always_selects_reply() {
        let _test_guard=TEST_LOCK.lock().unwrap();
        let mut s=state().lock().unwrap();
        s.area=Rect::new(2,3,100,1);s.reply=false;drop(s);
        assert!(matches!(click(2,3),Action::Speak(true)));
        assert!(matches!(click(9,3),Action::Speak(true)));
        assert!(matches!(click(10,3),Action::None));
        assert!(matches!(click(2,4),Action::None));
    }
    #[test]
    fn one_speech_label_without_source_toggles() {
        let _test_guard=TEST_LOCK.lock().unwrap();
        let area=Rect::new(0,0,100,1);let mut buf=Buffer::empty(area);Dock.render(area,&mut buf);
        let text=buf.content.iter().map(|c|c.symbol()).collect::<String>();
        assert!(text.starts_with("[speech]"));
        assert!(!text.contains("[Prompt]") && !text.contains("[Reply]"));
    }
}
