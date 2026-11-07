"""Snapshot reuse must preserve evidence identity and never claim fresh inference."""
import doctest
import unittest

import check
from reuse import ReviewSession


class ReuseTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.calls = 0
        def reviewer(text, sources, kind):
            self.calls += 1
            return {'findings': []}, {'fixture': True}
        self.reviewer = reviewer
        self.session = ReviewSession(reviewer, check.validate, 'test-v1',
                                     clock=lambda: self.now)

    def test_hit_preserves_content_and_labels_reuse(self):
        first = self.session.review('Statement.', {})
        second = self.session.review('Statement.', {})
        self.assertEqual(self.calls, 1)
        self.assertEqual(first['annotated'], second['annotated'])
        self.assertFalse(second['runtime']['fresh_model_call'])
        self.assertEqual(second['runtime']['mode'], 'reused_saved_review')
        self.assertEqual(second['status'], 'no_issues_flagged')

    def test_each_identity_change_invalidates(self):
        for text, sources, kind in [('A', {}, 'response'), ('B', {}, 'response'),
                                    ('B', {'s': 'evidence'}, 'response'),
                                    ('B', {'s': 'evidence'}, 'prompt')]:
            self.session.review(text, sources, kind)
        self.session.identity = 'test-v2'
        self.session.review('B', {'s': 'evidence'}, 'prompt')
        self.assertEqual(self.calls, 5)

    def test_exact_expiry_and_clock_reversal(self):
        self.session.review('A', {})
        self.now = 60
        self.session.review('A', {})
        self.now = 59
        self.session.review('A', {})
        self.assertEqual(self.calls, 3)

    def test_explicit_fresh(self):
        self.session.review('A', {})
        self.session.review('A', {}, fresh=True)
        self.assertEqual(self.calls, 2)

    def test_returned_value_cannot_poison_snapshot(self):
        first = self.session.review('A', {})
        first['original'] = 'poisoned'
        second = self.session.review('A', {})
        second['findings'].append({'invented': True})
        third = self.session.review('A', {})
        self.assertEqual(third['original'], 'A')
        self.assertEqual(third['findings'], [])

    def test_revalidation_rejects_corrupted_payload(self):
        self.session.review('A', {})
        key = next(iter(self.session.entries))
        self.session.entries[key] = (0, b'{"review":{"findings":[{}]},"runtime":{}}')
        with self.assertRaises(ValueError):
            self.session.review('A', {})

    def test_entry_and_byte_bounds(self):
        self.session.max_entries = 2
        for text in ['A', 'B', 'C']:
            self.session.review(text, {})
        self.assertEqual(len(self.session.entries), 2)
        self.session.review('A', {})
        self.assertEqual(self.calls, 4)
        self.assertLessEqual(self.session.bytes, self.session.max_bytes)
        self.session.clear()
        self.assertEqual(self.session.bytes, 0)
        self.session.max_bytes = 1
        self.session.review('A', {})
        self.assertEqual(len(self.session.entries), 0)

    def test_failure_is_not_cached(self):
        def fail(*args):
            raise RuntimeError('fixture failure')
        self.session.reviewer = fail
        with self.assertRaises(RuntimeError):
            self.session.review('A', {})
        self.assertEqual(self.session.entries, {})

    def test_disabled_cache_and_input_bounds(self):
        self.session.ttl = 0
        self.session.review('A', {})
        self.session.review('A', {})
        self.assertEqual(self.calls, 2)
        for text in ['', 'a' * 200001]:
            with self.assertRaises(ValueError):
                self.session.review(text, {})


if __name__ == '__main__':
    assert doctest.testmod().failed == 0
    unittest.main()
