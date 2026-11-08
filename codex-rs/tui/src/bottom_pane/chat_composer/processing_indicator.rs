//! Persistent blue Working/Idle activity lamp in the composer's existing bottom padding.
//!
//! Driven by the same admitted-turn/tool/startup lifecycle as task-running, not
//! by animation, a timer, or the existence of a process. This represents serving
//! a request, not a measurement of CPU use or proof that a remote worker is healthy.
use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::Span;

/// Preserve the persistent blue light without duplicating the status row's words.
pub(super) fn render_lamp(area: Rect, running: bool, buf: &mut Buffer) {
    if area.height < 3 || area.width < 3 {
        return;
    }
    for x in area.x + 1..area.right() - 1 {
        buf[(x, area.bottom() - 1)].reset();
    }
    let style = Style::default().fg(Color::Blue);
    let style = if running { style.add_modifier(Modifier::BOLD) } else { style };
    buf.set_span(area.x + 1, area.bottom() - 1,
        &Span::styled(if running { "●" } else { "○" }, style), area.width - 2);
}

pub(super) fn render(
    area: Rect,
    running: bool,
    task: &str,
    progress: Option<(usize, usize)>,
    buf: &mut Buffer,
) {
    // Keep input usable in a clipped/embedded composer. Never overwrite its text.
    if area.height < 3 || area.width < 3 {
        return;
    }
    let text = if running {
        let suffix = format!(" — {}", progress_text(progress));
        let prefix = "● Working — ";
        let available = usize::from(area.width - 2)
            .saturating_sub(Span::raw(prefix).width() + Span::raw(&suffix).width());
        let mut short_task = String::new();
        for c in task.chars().filter(|c| !c.is_control()).take(48) {
            let mut candidate = short_task.clone();
            candidate.push(c);
            if Span::raw(&candidate).width() > available { break; }
            short_task = candidate;
        }
        if short_task.is_empty() {
            format!("● Working{suffix}")
        } else {
            format!("{prefix}{short_task}{suffix}")
        }
    } else {
        String::from("○ Idle")
    };
    // Clear the entire owned padding row when a shorter label replaces a long one.
    for x in area.x + 1..area.right() - 1 {
        buf[(x, area.bottom() - 1)].reset();
    }
    let style = if running {
        Style::default()
            .fg(Color::Blue)
            .add_modifier(Modifier::BOLD)
    } else {
        Style::default()
            .fg(Color::Blue)
            .remove_modifier(Modifier::BOLD)
    };
    buf.set_span(
        area.x + 1,
        area.bottom() - 1,
        &Span::styled(text, style),
        area.width - 2,
    );
}

fn progress_text(progress: Option<(usize, usize)>) -> String {
    match progress {
        Some((done, total)) if total > 0 && done <= total => format!(
            "{}% steps ({done}/{total})",
            (done as u128 * 100) / total as u128
        ),
        _ => String::from("est. 1%"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn compact_lamp_is_blue_without_duplicate_working_or_stale_text() {
        let area = Rect::new(0, 0, 80, 3);
        let mut buf = Buffer::empty(area);
        render(area, true, "Working", None, &mut buf);
        for running in [true, false, true] {
            render_lamp(area, running, &mut buf);
            let row = (0..80).map(|x| buf[(x, 2)].symbol()).collect::<String>();
            assert_eq!(row.trim(), if running { "●" } else { "○" });
            assert_eq!(buf[(1, 2)].fg, Color::Blue);
            assert_eq!(buf[(1, 2)].modifier.contains(Modifier::BOLD), running);
        }
    }
    #[test]
    fn compact_lamp_preserves_input_at_clipped_sizes() {
        for width in 0..32 {
            for height in 0..5 {
                let area = Rect::new(0, 0, width, height);
                let mut buf = Buffer::empty(area);
                if width > 0 && height > 1 { buf[(0, 1)].set_symbol(">"); }
                render_lamp(area, true, &mut buf);
                if width > 0 && height > 1 { assert_eq!(buf[(0, 1)].symbol(), ">"); }
            }
        }
    }
    #[test]
    fn composer_keeps_lamp_connected() {
        let source = include_str!("../chat_composer.rs");
        assert!(source.contains("processing_indicator::render_lamp(composer_rect, self.is_task_running || background_running, buf);"));
    }
    #[test]
    fn reported_counts_are_not_time_estimates() {
        assert_eq!(progress_text(Some((1, 4))), "25% steps (1/4)");
        assert_eq!(progress_text(Some((0, 0))), "est. 1%");
        assert_eq!(progress_text(Some((5, 4))), "est. 1%");
        assert_eq!(progress_text(None), "est. 1%");
    }
    #[test]
    fn task_and_count_render_then_clear_on_idle() {
        let area = Rect::new(0, 0, 90, 3);
        let mut buf = Buffer::empty(area);
        render(area, true, "Build", Some((1, 4)), &mut buf);
        let row = (0..90).map(|x| buf[(x, 2)].symbol()).collect::<String>();
        assert!(row.contains("Working — Build — 25% steps (1/4)"));
        render(area, false, "Build", Some((1, 4)), &mut buf);
        let row = (0..90).map(|x| buf[(x, 2)].symbol()).collect::<String>();
        assert!(row.contains("Idle"));
        assert!(!row.contains("Build"));
        assert!(!row.contains('%'));
    }
    #[test]
    fn long_task_keeps_percentage_visible_in_a_narrow_terminal() {
        let area = Rect::new(0, 0, 40, 3);
        let mut buf = Buffer::empty(area);
        render(area, true, "Compiling a very long 日本語 task name", Some((1, 4)), &mut buf);
        let row = (0..40).map(|x| buf[(x, 2)].symbol()).collect::<String>();
        assert!(row.contains("25% steps (1/4)"));
    }
    #[test]
    fn processing_lamp_stays_blue_and_clears_working_state_on_idle() {
        let area = Rect::new(0, 0, 30, 3);
        let mut buf = Buffer::empty(area);
        render(area, true, "Build", None, &mut buf);
        assert_eq!(buf[(1, 2)].symbol(), "●");
        assert_eq!(buf[(1, 2)].fg, Color::Blue);
        render(area, false, "Build", None, &mut buf);
        assert_eq!(buf[(1, 2)].symbol(), "○");
        assert_eq!(buf[(1, 2)].fg, Color::Blue);
        assert!(!buf[(1, 2)].modifier.contains(Modifier::BOLD));
    }
    #[test]
    fn processing_lamp_preserves_input_and_clipped_composers() {
        for width in 0..32 {
            for height in 0..5 {
                let area = Rect::new(0, 0, width, height);
                let mut buf = Buffer::empty(area);
                if width > 0 && height > 1 {
                    buf[(0, 1)].set_symbol(">");
                }
                render(area, true, "Build", None, &mut buf);
                if width > 0 && height > 1 {
                    assert_eq!(buf[(0, 1)].symbol(), ">");
                }
            }
        }
    }
}
