"""Regressions for independently reproduced integrity counterexamples."""
import doctest
import itertools
import unittest
import check


class SpanCornerCases(unittest.TestCase):
    def test_overlapping_claim_is_ambiguous(self):
        for text, claim in [('aaa', 'aa'), ('ababa', 'aba'), ('ééé', 'éé')]:
            with self.assertRaises(ValueError):
                check.exact_span(text, claim)

    def test_exhaustive_small_alphabet(self):
        # Independent oracle enumerates every possible starting position.
        words = [''.join(bits) for size in range(7)
                 for bits in itertools.product('ab', repeat=size)]
        claims = [''.join(bits) for size in range(5)
                  for bits in itertools.product('ab', repeat=size)]
        for text in words:
            for claim in claims:
                starts = [i for i in range(len(text)) if claim and text.startswith(claim, i)]
                if len(starts) == 1:
                    self.assertEqual(check.exact_span(text, claim),
                                     (starts[0], starts[0] + len(claim)))
                else:
                    with self.assertRaises(ValueError):
                        check.exact_span(text, claim)


if __name__ == '__main__':
    assert doctest.testmod().failed == 0
    unittest.main()
