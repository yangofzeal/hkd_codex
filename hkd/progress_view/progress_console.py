"""Independent task display; survives resets of a separate Codex session."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

def main():
    root = Path(os.environ.get('HKD_PROGRESS_ROOT', Path(__file__).resolve().parent)).resolve()
    previous = None
    try:
        while True:
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('build_dashboard.py'))], capture_output=True, text=True)
            try:
                state = json.loads((root / 'status.json').read_text())
                lines = ['PROJECT PROGRESS · saved snapshot, not live', state['observed_at'], '']
                for task in state['tasks']:
                    pct = float(task['percent'])
                    filled = int(pct / 5)
                    lines.append(f"{task['name']:<26} [{'█' * filled}{'░' * (20-filled)}] {pct:g}% estimated")
                    lines.append('  ' + task['status'])
                    lines.append('  ' + task['detail'])
                    lines.append('')
                lines.extend([
                    'CURRENT LOCAL BLOCKERS',
                    'Stock source: ' + ('present; inspection pending' if (root.parent / 'trade_new').is_dir() else 'awaiting transfer to Downloads/trade_new'),
                    'Native Codex bars: source prepared; compilation and installation not verified.',
                    'Worker progress: saved evidence only; no live worker connection.',
                    'Imported logs are checked every 30 seconds; Ctrl-C closes this display.',
                ])
                if result.returncode:
                    lines.append('Refresh failed; retaining saved evidence.')
                display = '\n'.join(lines)
                if display != previous:
                    print(('\033[2J\033[H' if sys.stdout.isatty() else '') + display, flush=True)
                    previous = display
            except (OSError, ValueError, KeyError):
                print('Progress evidence unavailable; retrying in 30 seconds.', flush=True)
            time.sleep(30)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
