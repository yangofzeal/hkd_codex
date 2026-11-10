import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class Builder(unittest.TestCase):
    def test_questions_persist_without_creating_extra_bars(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            root = base / 'view'
            root.mkdir()
            logs = base / 'old-mac-codex-logs'
            logs.mkdir()
            rows = [[n, 25, 'SAVED', 'fixture'] for n in ('Spindrop plugin', 'RenderDon', 'AUSA commercial · 30s')]
            record = {'timestamp': '2026-11-10T18:00:00Z', 'type': 'event_msg',
                      'payload': {'item': {'type': 'CommandExecution', 'aggregated_output': json.dumps(rows)}}}
            (logs / 'fixture.jsonl').write_text(json.dumps(record) + '\n')
            questions = root / 'pending-questions.json'
            questions.write_text(json.dumps([{'id': 'q1', 'text': 'Which <window>?',
                'status': 'pending', 'dependent_task': 'Research'}]))
            env = dict(os.environ, HKD_PROGRESS_ROOT=str(root))
            def run():
                return subprocess.run([sys.executable, str(Path(__file__).with_name('build_dashboard.py'))], env=env, capture_output=True)
            self.assertEqual(run().returncode, 0)
            page = (root / 'index.html').read_text()
            self.assertEqual(page.count('<progress '), 3)
            self.assertIn('Which &lt;window&gt;?', page)
            stamp = (root / 'status.json').stat().st_mtime_ns
            self.assertIn(b'unchanged', run().stdout)
            self.assertEqual(stamp, (root / 'status.json').stat().st_mtime_ns)
            questions.write_text('invalid JSON')
            self.assertNotEqual(run().returncode, 0)
            self.assertEqual(stamp, (root / 'status.json').stat().st_mtime_ns)
            questions.write_text('[]')
            self.assertEqual(run().returncode, 0)
            self.assertNotIn('Pending questions', (root / 'index.html').read_text())


if __name__ == '__main__':
    unittest.main()
