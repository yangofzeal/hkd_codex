//! Compact activity bar for tasks whose total work is not reported.
//! Estimated percentages are explicit heuristics, never measured completion.

/// Uncalibrated task-duration priors; the estimate never certifies completion.
pub(super) fn estimated_percent(task: &str, seconds: u64) -> u8 {
    let prior = match task {
        "Build" => 600_u128,
        "Tests" => 180,
        "Benchmark" | "HKD benchmark" => 300,
        _ => 120,
    };
    let seconds = u128::from(seconds);
    ((100 * seconds / (seconds + prior)).clamp(1, 95)) as u8
}

pub(super) fn label(header: &str, details: Option<&str>) -> &'static str {
    let text = format!("{header} {}", details.unwrap_or_default()).to_ascii_lowercase();
    if text.contains("benchmark") || text.contains("speedup") {
        if text.contains("hkd") {
            "HKD benchmark"
        } else {
            "Benchmark"
        }
    } else if text.contains("test") || text.contains("pytest") || text.contains("doctest") {
        "Tests"
    } else if text.contains("build") || text.contains("compil") || text.contains("cargo check") {
        "Build"
    } else {
        "Working"
    }
}

pub(super) fn line(label: &str, millis: u128, width: usize, animate: bool) -> Option<String> {
    if millis < 5_000 || width < 24 {
        return None;
    }
    let secs = millis / 1000;
    let suffix = format!(" {:02}:{:02} elapsed", secs / 60, secs % 60);
    let cells = width.saturating_sub(label.len() + suffix.len() + 3).min(12);
    if cells < 3 {
        return None;
    }
    let mut bar = vec!['·'; cells];
    if animate {
        let cycle = 2 * (cells - 1);
        let tick = (millis / 200 % cycle as u128) as usize;
        let position = if tick < cells { tick } else { cycle - tick };
        bar[position] = '━';
    } else {
        bar.fill('─');
    }
    Some(format!(
        "{label} [{}]{suffix}",
        bar.into_iter().collect::<String>()
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn estimates_are_bounded_monotonic_and_never_claim_completion() {
        for task in ["Build", "Tests", "Benchmark", "HKD benchmark", "Working"] {
            let mut previous = 0;
            for seconds in [0, 1, 60, 120, 600, 3600, u64::MAX] {
                let value = estimated_percent(task, seconds);
                assert!((1..=95).contains(&value));
                assert!(value >= previous);
                previous = value;
            }
        }
        assert_eq!(estimated_percent("Build", 600), 50);
        assert_eq!(estimated_percent("Tests", 180), 50);
        assert_eq!(estimated_percent("Working", 120), 50);
    }

    #[test]
    fn only_long_tasks_and_readable_widths_show_the_bar() {
        assert!(line("Build", 4999, 80, true).is_none());
        assert!(line("Build", 5000, 20, true).is_none());
        assert!(
            line("Build", 5000, 80, true)
                .unwrap()
                .contains("00:05 elapsed")
        );
    }

    #[test]
    fn animation_is_bounded_and_reduced_motion_is_static() {
        for width in 0..100 {
            for tick in 25..70 {
                if let Some(row) = line("HKD benchmark", tick * 200, width, true) {
                    assert!(row.chars().count() <= width);
                    assert_eq!(row.chars().filter(|c| *c == '━').count(), 1);
                    assert!(!row.contains('%'));
                }
            }
        }
        assert_eq!(
            line("Tests", 5000, 80, false),
            line("Tests", 5200, 80, false)
        );
        assert_ne!(line("Tests", 5000, 80, true), line("Tests", 5200, 80, true));
    }

    #[test]
    fn task_names_come_from_the_active_status() {
        assert_eq!(label("Running", Some("cargo build --release")), "Build");
        assert_eq!(label("Running", Some("python -m unittest")), "Tests");
        assert_eq!(label("HKD speedup", None), "HKD benchmark");
        assert_eq!(label("Thinking", None), "Working");
    }
}

/// The sole bottom activity row; the moving marker is activity, not completion.
pub(super) fn compact_line(millis: u128, animate: bool) -> String {
    let seconds = millis / 1000;
    let mut cells = ['·'; 12];
    if animate {
        let tick = (millis / 200 % 22) as usize;
        cells[if tick < 12 { tick } else { 22 - tick }] = '━';
    } else {
        cells.fill('─');
    }
    format!("Working [{}] {}:{:02} elapsed", cells.iter().collect::<String>(), seconds / 60, seconds % 60)
}

#[cfg(test)]
mod compact_tests {
    use super::compact_line;
    #[test]
    fn exact_requested_format_and_single_row() {
        assert_eq!(compact_line(42_000, false), "Working [────────────] 0:42 elapsed");
        for millis in [0, 42_000, 60_000, 3_600_000, u128::MAX] {
            let row = compact_line(millis, true);
            assert_eq!(row.lines().count(), 1);
            assert_eq!(row.matches("Working").count(), 1);
            assert_eq!(row.matches('━').count(), 1);
            assert!(!row.contains("unknown"));
        }
    }
}


/// PFT-inspired state factoring: reduce reported step states once per update.
/// Rendering uses only this sufficient summary; it does not rescan process rows.
/// A step counts as complete only when its reported units are complete.
pub(super) fn sequence_counts(counts: impl IntoIterator<Item = Option<(u64, u64)>>) -> Option<(u64, u64)> {
    let mut done = 0;
    let mut total = 0;
    for count in counts {
        total += 1;
        if count.is_some_and(|(n, d)| d > 0 && n == d) { done += 1; }
    }
    (total > 0).then_some((done, total))
}

/// Exact completed-step progress, not an elapsed-time estimate.
pub(super) fn sequence_line(counts: Option<(u64, u64)>) -> Option<String> {
    let (done, total) = counts?;
    if total == 0 || done > total { return None; }
    let pct = (u128::from(done) * 100 / u128::from(total)) as usize;
    let filled = pct * 12 / 100;
    Some(format!("Progress [{}{}] {done}/{total} steps · {pct}%", "━".repeat(filled), "·".repeat(12-filled)))
}

#[cfg(test)]
mod fixed_sequence_tests {
    use super::*;
    #[test]
    fn measured_steps_are_not_invented_from_activity() {
        let counts = sequence_counts([Some((1,1)), Some((1,1)), None, Some((0,1)), Some((0,1))]);
        assert_eq!(counts, Some((2,5)));
        assert_eq!(sequence_line(counts).unwrap(), "Progress [━━━━········] 2/5 steps · 40%");
        assert_eq!(sequence_counts([]), None);
        assert_eq!(sequence_counts([Some((2,1)),Some((0,0))]), Some((0,2)));
        assert!(sequence_line(Some((2,1))).is_none());
    }
    #[test]
    fn factored_projection_matches_full_step_count() {
        for total in 1..=256_u64 {
            for done in [0,total/2,total] {
                let reported=(0..total).map(|i|if i<done {Some((1,1))} else {None});
                let summary=sequence_counts(reported);
                assert_eq!(summary,Some((done,total)));
                assert!(sequence_line(summary).unwrap().contains(&format!("{done}/{total} steps")));
            }
        }
        assert!(sequence_line(Some((u64::MAX,u64::MAX))).unwrap().ends_with("100%"));
    }
}
