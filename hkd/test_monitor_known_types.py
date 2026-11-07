"""The registry monitor must fail closed for missing, duplicate or open rules."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import monitor_known_types


class MonitorTests(unittest.TestCase):
    def test_empty_registry_cannot_be_green(self):
        with self.assertRaises(ValueError):
            self.run_registry([])

    def run_registry(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'registry.json'
            path.write_text(json.dumps({'scope': 'fixture', 'categories': rows}))
            with contextlib.redirect_stderr(io.StringIO()):
                return monitor_known_types.monitor(path)

    def row(self, **overrides):
        row = {'id': 'fixture', 'scope': 'one declared test', 'status': 'enforced',
               'tests': ['test_check.IntegrityTests.test_preserves_original']}
        row.update(overrides)
        return row

    def test_passing_declared_contract(self):
        self.assertEqual(self.run_registry([self.row()])['failing_categories'], [])

    def test_open_contract_cannot_be_green(self):
        self.assertEqual(self.run_registry([self.row(status='open')])['failing_categories'], ['fixture'])

    def test_missing_test_cannot_be_green(self):
        self.assertEqual(self.run_registry([self.row(tests=['no_such_hkd_test'])])['failing_categories'], ['fixture'])

    def test_duplicate_category_is_rejected(self):
        with self.assertRaises(ValueError):
            self.run_registry([self.row(), self.row()])

    def test_missing_scope_is_rejected(self):
        with self.assertRaises(ValueError):
            self.run_registry([self.row(scope='')])


if __name__ == '__main__':
    unittest.main()
