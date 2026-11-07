"""Regressions for independently reproduced integrity counterexamples."""
import doctest
import itertools
import unittest
import check


class SemanticBoundaryCases(unittest.TestCase):
    def test_identical_quote_does_not_prove_contradiction(self):
        for quote in ['All tests passed.', ' All tests passed. ']:
            finding = dict(claim='All tests passed.', verdict='contradicted',
                           source_id='s', evidence_quote=quote,
                           reason='Two tests failed.')
            with self.assertRaisesRegex(ValueError, 'identical quote'):
                check.validate('All tests passed.', {'s': quote}, {'findings': [finding]})

    def test_empty_findings_never_certify_truth_or_coverage(self):
        result = check.validate('All tests passed.', {'s': 'Two tests failed.'},
                                {'findings': []})
        self.assertFalse(result['truth_certified'])
        self.assertFalse(result['semantic_completeness_verified'])
        self.assertEqual(result['status'], 'no_issues_flagged')

    def test_genuine_contradiction_retains_model_assessment_boundary(self):
        finding = dict(claim='All tests passed.', verdict='contradicted',
                       source_id='s', evidence_quote='Two tests failed.',
                       reason='The run records failed tests.')
        result = check.validate('All tests passed.', {'s': 'Two tests failed.'},
                                {'findings': [finding]})
        self.assertEqual(result['status'], 'needs_review')
        self.assertFalse(result['truth_certified'])


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
