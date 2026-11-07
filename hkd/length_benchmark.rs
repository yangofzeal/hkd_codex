//! Standalone release-mode comparison of the actual upstream predicate and patch.
#[path = "../codex-rs/skills/src/hkd_length_bound.rs"]
mod hkd_length_bound;
use std::hint::black_box;
use std::time::Instant;

#[inline(never)]
fn baseline(value: &str, limit: usize) -> bool {
    value.chars().count() > limit
}
#[inline(never)]
fn candidate(value: &str, limit: usize) -> bool {
    hkd_length_bound::exceeds_char_limit(value, limit)
}
fn batch(f: fn(&str, usize) -> bool, s: &str, limit: usize, n: u64) -> f64 {
    let start = Instant::now();
    for _ in 0..n {
        black_box(f(black_box(s), black_box(limit)));
    }
    start.elapsed().as_nanos() as f64 / n as f64
}
fn iterations(f: fn(&str, usize) -> bool, s: &str, limit: usize) -> u64 {
    let ns = batch(f, s, limit, 100).max(0.1);
    (20_000_000.0 / ns).clamp(10.0, 10_000_000.0) as u64
}
fn main() {
    println!(
        "case,bytes,scalars,limit,baseline_ns,candidate_ns,speedup,baseline_iterations,candidate_iterations"
    );
    for (name, text, limit) in [
        ("empty", String::new(), 64),
        ("ascii16", "a".repeat(16), 64),
        ("ascii64", "a".repeat(64), 64),
        ("ascii65", "a".repeat(65), 64),
        ("ascii256", "a".repeat(256), 64),
        ("ascii257", "a".repeat(257), 64),
        ("unicode64", "🦀".repeat(64), 64),
        ("mixed64", "aé中🦀".repeat(16), 64),
        ("ascii1024", "a".repeat(1024), 1024),
        ("stress_1MiB", "a".repeat(1 << 20), 64),
        ("stress_16MiB", "🦀".repeat(1 << 22), 64),
    ] {
        assert_eq!(baseline(&text, limit), candidate(&text, limit));
        let n = iterations(baseline, &text, limit);
        let m = iterations(candidate, &text, limit);
        let mut before = Vec::new();
        let mut after = Vec::new();
        for round in 0..9 {
            if round % 2 == 0 {
                before.push(batch(baseline, &text, limit, n));
                after.push(batch(candidate, &text, limit, m));
            } else {
                after.push(batch(candidate, &text, limit, m));
                before.push(batch(baseline, &text, limit, n));
            }
        }
        before.sort_by(|a, b| a.total_cmp(b));
        after.sort_by(|a, b| a.total_cmp(b));
        println!(
            "{name},{},{},{limit},{:.4},{:.4},{:.4},{n},{m}",
            text.len(),
            text.chars().count(),
            before[4],
            after[4],
            before[4] / after[4]
        );
    }
}
