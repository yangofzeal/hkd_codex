//! Exact UTF-8 bounds for a character-limit predicate.
//!
//! A Unicode scalar takes 1..=4 bytes in a valid Rust `str`. Thus byte length
//! <= limit proves acceptance, and byte length > 4*limit proves rejection.
//! Only the ambiguous interval needs the original scalar count. Saturating multiply
//! preserves the proof when the caller supplies a limit near usize::MAX.
//! This is a local exact specialization, not an application of fixed-gap PFT
//! factoring and not a model-inference acceleration claim.

pub(crate) fn exceeds_char_limit(value: &str, limit: usize) -> bool {
    let bytes = value.len();
    if bytes <= limit {
        return false;
    }
    if bytes > limit.saturating_mul(4) {
        return true;
    }
    // Keep Rust's optimized full count for this bounded ambiguous interval.
    // A scalar-by-scalar nth(limit) regressed on small Unicode inputs in testing.
    value.chars().count() > limit
}

#[cfg(test)]
mod tests {
    use super::exceeds_char_limit;

    #[test]
    fn boundaries_match_reference() {
        for text in ["", "a", "é", "中", "🦀", "e\u{301}", "aé中🦀", "\0\n\r"] {
            for limit in [0, 1, 2, 3, 4, 5, 8, usize::MAX / 4, usize::MAX] {
                assert_eq!(
                    exceeds_char_limit(text, limit),
                    text.chars().count() > limit
                );
            }
        }
    }

    #[test]
    fn generated_unicode_matches_reference() {
        let mut state = 0x2026_1107_u64;
        let mut comparisons = 0;
        for length in 0usize..300 {
            let mut text = String::new();
            for _ in 0..length {
                state ^= state << 13;
                state ^= state >> 7;
                state ^= state << 17;
                let scalar = (state % 0x110000) as u32;
                text.push(char::from_u32(scalar).unwrap_or('x'));
            }
            for limit in [
                0,
                length / 2,
                length.saturating_sub(1),
                length,
                length + 1,
                usize::MAX,
            ] {
                assert_eq!(
                    exceeds_char_limit(&text, limit),
                    text.chars().count() > limit
                );
                comparisons += 1;
            }
        }
        assert_eq!(comparisons, 1800);
    }

    #[test]
    fn large_inputs_match_reference() {
        for unit in ["a", "é", "中", "🦀", "aé中🦀"] {
            let text = unit.repeat(100_000);
            for limit in [0, 64, 1024, 100_000, 400_000, usize::MAX] {
                assert_eq!(
                    exceeds_char_limit(&text, limit),
                    text.chars().count() > limit
                );
            }
        }
    }
}
