//! Actual tip Codex context matcher versus same-contract local specialization.
#[path = "baselines/seek_sequence_tip.rs"]
mod baseline;
#[path = "../codex-rs/apply-patch/src/seek_sequence.rs"]
mod candidate;
use std::hint::black_box;
use std::time::Instant;
type Matcher = fn(&[String], &[String], usize, bool) -> Option<usize>;

fn measure(f: Matcher, lines: &[String], pattern: &[String], n: usize) -> f64 {
    let start = Instant::now();
    for _ in 0..n {
        black_box(f(black_box(lines), black_box(pattern), 0, false));
    }
    start.elapsed().as_nanos() as f64 / n as f64
}

fn main() {
    println!("category,lines,baseline_mean_ns,candidate_mean_ns,speedup,baseline_p95_ns,candidate_p95_ns,baseline_max_ns,candidate_max_ns,baseline_pattern_normalizations,candidate_pattern_normalizations");
    for count in [64, 1024, 16384] {
        for category in ["exact_at_end", "unicode_at_end", "no_match", "long_pattern_miss"] {
            let mut lines: Vec<String> = (0..count).map(|i| format!("let unrelated_{i} = 0;")).collect();
            let pattern = vec!["let message = \"target\";".to_string();
                               if category == "long_pattern_miss" { count - 1 } else { 1 }];
            if category == "exact_at_end" { lines[count - 1] = pattern[0].clone(); }
            if category == "unicode_at_end" { lines[count - 1] = "let message = “target”;".to_string(); }
            assert_eq!(baseline::seek_sequence(&lines, &pattern, 0, false),
                       candidate::seek_sequence(&lines, &pattern, 0, false));
            let n = (2_000_000.0 / measure(baseline::seek_sequence, &lines, &pattern, 1).max(1.0))
                .clamp(1.0, 10000.0) as usize;
            let mut before = Vec::new();
            let mut after = Vec::new();
            for round in 0..21 {
                if round % 2 == 0 {
                    before.push(measure(baseline::seek_sequence, &lines, &pattern, n));
                    after.push(measure(candidate::seek_sequence, &lines, &pattern, n));
                } else {
                    after.push(measure(candidate::seek_sequence, &lines, &pattern, n));
                    before.push(measure(baseline::seek_sequence, &lines, &pattern, n));
                }
            }
            let b = before.iter().sum::<f64>() / before.len() as f64;
            let a = after.iter().sum::<f64>() / after.len() as f64;
            before.sort_by(f64::total_cmp); after.sort_by(f64::total_cmp);
            let (bn, an) = if category == "exact_at_end" { (0, 0) }
                else if category == "long_pattern_miss" { (2, 1) } else { (count, 1) };
            println!("{category},{count},{b:.3},{a:.3},{:.4},{:.3},{:.3},{:.3},{:.3},{bn},{an}",
                     b/a, before[19], after[19], before[20], after[20]);
        }
    }
}

#[cfg(test)]
mod differential {
    use super::*;
    #[test]
    fn same_results_across_generated_contexts() {
        let alphabet = ["", "a", "a ", " a", "“a”", "\"a\"", "—", "-", "\u{a0}"];
        let mut state = 20261107u64;
        for _ in 0..3000 {
            let mut next = || { state ^= state << 13; state ^= state >> 7; state ^= state << 17; state as usize };
            let lines: Vec<String> = (0..next()%12).map(|_| alphabet[next()%alphabet.len()].to_string()).collect();
            let pattern: Vec<String> = (0..next()%5).map(|_| alphabet[next()%alphabet.len()].to_string()).collect();
            for start in [0, lines.len()/2, lines.len(), lines.len()+1] {
                for eof in [false, true] {
                    assert_eq!(baseline::seek_sequence(&lines, &pattern, start, eof),
                               candidate::seek_sequence(&lines, &pattern, start, eof));
                }
            }
        }
    }
}
