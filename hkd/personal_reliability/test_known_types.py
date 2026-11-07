"""Known-type detection is tested independently of any model response."""
import doctest
import unittest
import check
from unittest.mock import patch
from known_types import test_failure_guard


class KnownTypeTests(unittest.TestCase):
    def test_known_type_bypasses_model(self):
        with patch.object(check.subprocess, 'Popen', side_effect=AssertionError('Model must not run')):
            session = check.new_session()
            result = session.review('All tests passed.', {'s': 'Two tests failed.'}, fresh=True)
            self.assertFalse(result['runtime']['fresh_model_call'])
            self.assertEqual(result['runtime']['mode'], 'deterministic_known_type')
            self.assertEqual(result['known_type_checks'][0]['status'], 'detected')

    def test_out_of_scope_does_not_bypass_model(self):
        with patch.object(check.subprocess, 'Popen', side_effect=RuntimeError('model path reached')):
            with self.assertRaisesRegex(RuntimeError, 'model path reached'):
                check.review_with_codex('Arbitrary prose.', {'s': 'Two tests failed.'}, 'response')

    def test_model_omission_is_repaired(self):
        result = check.validate('All tests passed.', {'s': 'Two tests failed.'}, {'findings': []})
        self.assertEqual(result['status'], 'needs_review')
        self.assertEqual(result['findings'][0]['verdict'], 'contradicted')
        self.assertEqual(result['known_type_checks'][0]['status'], 'detected')
        self.assertFalse(result['semantic_completeness_verified'])

    def test_numeric_failures_are_detected(self):
        for number in list(range(1, 10001)) + [999999999]:
            self.assertEqual(test_failure_guard('All tests passed.',
                             {'s': '{} tests failed.'.format(number)})['status'], 'detected')

    def test_zero_failures_is_not_a_contradiction(self):
        result = check.validate('All tests passed.', {'s': '0 tests failed.'}, {'findings': []})
        self.assertEqual(result['findings'], [])
        self.assertEqual(result['known_type_checks'][0]['status'], 'no_conflict_in_scope')

    def test_scope_does_not_expand_silently(self):
        cases = [('"All tests passed."', {'s': 'Two tests failed.'}),
                 ('Did all tests pass?', {'s': 'Two tests failed.'}),
                 ('All tests passed.', {'s': 'Yesterday two tests failed.'}),
                 ('All tests passed.', {'s': 'Run B: Two tests failed.'}),
                 ('All tests passed.', {'s': 'Two tests failed.', 't': 'No failures.'}),
                 ('All tests passed.', {'s': '-1 tests failed.'}),
                 ('All tests passed.', {'s': '1000000000 tests failed.'})]
        for text, sources in cases:
            self.assertEqual(test_failure_guard(text, sources)['status'], 'out_of_scope')

    def test_supported_evidence_quote_and_offsets(self):
        result = check.validate('  All tests passed.\n', {'s': ' One test failed.\n'}, {'findings': []})
        finding = result['findings'][0]
        self.assertEqual(result['original'][finding['start']:finding['end']], finding['claim'])
        self.assertEqual(finding['evidence_quote'], 'One test failed.')

    def test_reuse_rechecks_known_detector(self):
        from reuse import ReviewSession
        session = ReviewSession(lambda *args: ({'findings': []}, {}), check.validate, 'fixture')
        a = session.review('All tests passed.', {'s': 'Two tests failed.'})
        b = session.review('All tests passed.', {'s': 'Two tests failed.'})
        self.assertEqual(a['findings'], b['findings'])
        self.assertEqual(b['known_type_checks'][0]['status'], 'detected')


if __name__ == '__main__':
    assert doctest.testmod().failed == 0
    unittest.main()
