//! Exact UTF-8 bounds for a character-limit predicate.
//!
//! A Unicode scalar takes 1..=4 bytes in a valid Rust `str`. Thus byte length
//! <= limit proves acceptance, and byte length > 4*limit proves rejection.
//! Only the ambiguous interval needs the original scalar count. The rejection bound is written as (bytes - 1) / 4 >= limit after proving
//! bytes > limit, so it never overflows even near usize::MAX.
//! This is a local exact specialization, not an application of fixed-gap PFT
//! factoring and not a model-inference acceleration claim.

pub(crate) fn exceeds_char_limit(value: &str, limit: usize) -> bool {
    let bytes = value.len();
    if bytes <= limit {
        return false;
    }
    if (bytes - 1) / 4 >= limit {
        return true;
    }
    // On valid UTF-8, every scalar has exactly one non-continuation byte.
    // Count these directly so LLVM can vectorize the remaining bounded work.
    bounded_count(value, limit)
}

#[cfg(all(target_arch = "aarch64", target_feature = "neon"))]
fn bounded_count(value: &str, limit: usize) -> bool {
    use std::arch::aarch64::*;
    let bytes = value.as_bytes();
    let mut offset = 0;
    let mut count = 0usize;
    // Valid UTF-8 has exactly one byte >= -64 (as i8) per scalar.
    // Each lane accumulates at most 16 ones before a widening horizontal sum.
    // Every vector load is within a fully checked 16-byte slice.
    unsafe {
        while bytes.len() - offset >= 16 {
            let blocks = ((bytes.len() - offset) / 16).min(16);
            let mut totals = vdupq_n_u8(0);
            for _ in 0..blocks {
                let vector = vreinterpretq_s8_u8(vld1q_u8(bytes.as_ptr().add(offset)));
                let starts = vcgeq_s8(vector, vdupq_n_s8(-64));
                totals = vaddq_u8(totals, vshrq_n_u8::<7>(starts));
                offset += 16;
            }
            count += vaddlvq_u8(totals) as usize;
            if count > limit {
                return true;
            }
        }
    }
    count + bytes[offset..].iter().filter(|byte| **byte & 0xc0 != 0x80).count() > limit
}

#[cfg(not(all(target_arch = "aarch64", target_feature = "neon")))]
fn bounded_count(value: &str, limit: usize) -> bool {
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
