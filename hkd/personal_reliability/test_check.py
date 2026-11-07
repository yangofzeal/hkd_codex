import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
import tempfile

import check
import hkd_runtime


class PaidRuntimeTests(unittest.TestCase):
    def test_alu_reporting_contract(self):
        module = hkd_runtime.load_module('hkd_alu', hkd_runtime.VENDOR.parent / 'hkd_alu.py')
        reporter = module.HKDALU(1, 2.0, stream=io.StringIO())
        result = reporter.complete('fixture', 2.0, 1.0, 'a\nb', logical_items=4)
        self.assertEqual(result.speedup, 2.0)
        self.assertEqual(result.overall_contribution_percent, 50.0)
        self.assertEqual(result.throughput_items_per_second, 4.0)
        self.assertEqual(reporter.summary()[0]['result'], 'a b')
        with self.assertRaises(AttributeError):
            result.speedup = 100000

    def test_paid_edition(self):
        self.assertEqual(hkd_runtime._thread.EDITION, 'PAID')

    def test_source_order_and_updates(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder) / str(i) for i in range(4)]
            for i, path in enumerate(paths):
                with path.open('w') as stream:
                    stream.write(str(i))
            self.assertEqual(list(hkd_runtime.load_sources(paths).values()), ['0', '1', '2', '3'])
            with paths[0].open('w') as stream:
                stream.write('changed')
            self.assertEqual(hkd_runtime.load_sources(paths)['source_1'], 'changed')

    def test_missing_source_fails(self):
        with self.assertRaises(OSError):
            hkd_runtime.load_sources(['/missing-hkd-test-fixture'])

    def test_input_count_is_bounded(self):
        with self.assertRaises(ValueError):
            hkd_runtime.load_sources(['not-read'] * 17)


class IntegrityTests(unittest.TestCase):
    def finding(self, **overrides):
        result = dict(claim='All tests passed.', verdict='contradicted',
                      source_id='source_1', evidence_quote='2 tests failed.',
                      reason='The supplied run records failures.')
        result.update(overrides)
        return result

    def verify(self, finding=None, text='All tests passed.'):
        return check.validate(text, {'source_1': 'Run A: 2 tests failed.'},
                              {'findings': [finding or self.finding()]})

    def test_preserves_original(self):
        result = self.verify()
        self.assertEqual(result['original'], 'All tests passed.')
        self.assertIn('[review 1: contradicted]', result['annotated'])

    def test_invented_quote(self):
        with self.assertRaises(ValueError):
            self.verify(self.finding(evidence_quote='20 tests failed.'))

    def test_invented_source(self):
        with self.assertRaises(ValueError):
            self.verify(self.finding(source_id='invented'))

    def test_invented_claim(self):
        with self.assertRaises(ValueError):
            self.verify(self.finding(claim='Payment completed.'))

    def test_repeated_span(self):
        with self.assertRaises(ValueError):
            self.verify(text='All tests passed. All tests passed.')

    def test_overlap(self):
        with self.assertRaises(ValueError):
            check.validate('All tests passed.', {'source_1': '2 tests failed.'},
                           {'findings': [self.finding(), self.finding(claim='tests passed')]})

    def test_unknown_has_no_fake_citation(self):
        with self.assertRaises(ValueError):
            self.verify(self.finding(verdict='unverified'))

    def test_unknown_label(self):
        result = self.verify(self.finding(verdict='unverified', source_id='', evidence_quote=''))
        self.assertIn('unverified', result['annotated'])

    def test_clean_is_not_verified(self):
        result = check.validate('Hello.', {}, {'findings': []})
        self.assertEqual(result['status'], 'no_issues_flagged')
        self.assertIn('does not mean verified', result['limits'])

    def test_empty_quote(self):
        with self.assertRaises(ValueError):
            self.verify(self.finding(evidence_quote=''))

    def test_unknown_verdict(self):
        with self.assertRaises(ValueError):
            self.verify(self.finding(verdict='true'))

    def test_extra_rewrite_field(self):
        with self.assertRaises(ValueError):
            self.verify(self.finding(replacement='Everything is perfect.'))

    def test_changed_source_invalidates_quote(self):
        with self.assertRaises(ValueError):
            check.validate('All tests passed.', {'source_1': 'No run recorded.'},
                           {'findings': [self.finding()]})

    def test_multiple_edits_preserve_offsets(self):
        findings = [self.finding(claim=x, verdict='unverified', source_id='', evidence_quote='')
                    for x in ['A passed.', 'B passed.']]
        r = check.validate('A passed. B passed.', {}, {'findings': findings})
        self.assertEqual(r['annotated'], 'A passed. [review 1: unverified] B passed. [review 2: unverified]')


class StreamTests(unittest.TestCase):
    def stream(self, events):
        return io.StringIO(''.join(json.dumps(e) + '\n' for e in events))

    def events(self):
        return [{'type': 'thread.started', 'thread_id': 'fixture'},
                {'type': 'turn.started'},
                {'type': 'item.completed', 'item': {'id': 'item_0', 'type': 'agent_message', 'text': 'First'}},
                {'type': 'item.completed', 'item': {'id': 'item_1', 'type': 'command_execution', 'aggregated_output': 'UNTRUSTED TEXT'}},
                {'type': 'item.completed', 'item': {'id': 'item_2', 'type': 'agent_message', 'text': 'Final'}},
                {'type': 'turn.completed', 'usage': {}}]

    def test_final_only(self):
        self.assertEqual(check.codex_text(self.stream(self.events())), 'Final')

    def test_truncated(self):
        with self.assertRaises(ValueError):
            check.codex_text(self.stream(self.events()[:-1]))

    def test_failed(self):
        with self.assertRaises(ValueError):
            check.codex_text(self.stream(self.events()[:-1] + [{'type': 'turn.failed'}]))

    def test_extra_turn(self):
        with self.assertRaises(ValueError):
            check.codex_text(self.stream(self.events() + self.events()))

    def test_invalid_json(self):
        with self.assertRaises(ValueError):
            check.codex_text(io.StringIO('not json\n'))

    def test_completion_without_start(self):
        with self.assertRaises(ValueError):
            check.codex_text(self.stream([{'type': 'turn.completed'}]))

    def test_missing_message(self):
        with self.assertRaises(ValueError):
            check.codex_text(self.stream([{'type': 'turn.started'}, {'type': 'turn.completed'}]))

    def test_error_after_message(self):
        with self.assertRaises(ValueError):
            check.codex_text(self.stream(self.events()[:-1] + [{'type': 'error'}]))

    def test_cli_invalid_does_not_release_text(self):
        r = subprocess.Popen([sys.executable, str(Path(check.__file__)), '--codex-jsonl'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             universal_newlines=True)
        stdout, stderr = r.communicate('not json')
        self.assertEqual(r.returncode, 2)
        self.assertEqual(stdout, '')

    def test_cli_valid_offline_review(self):
        with tempfile.TemporaryDirectory() as folder:
            review = Path(folder) / 'review.json'
            with review.open('w') as stream:
                json.dump({'findings': []}, stream)
            r = subprocess.Popen([sys.executable, str(Path(check.__file__)),
                                  '--review-json', str(review), '--json'],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = r.communicate('A question?')
            self.assertEqual(r.returncode, 0, stderr)
            self.assertEqual(json.loads(stdout)['original'], 'A question?')


if __name__ == '__main__':
    unittest.main()
