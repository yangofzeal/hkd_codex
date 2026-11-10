#!/usr/bin/env python3
"""Extract saved progress evidence without executing anything from the logs."""
import glob
import html
import json
import os
import sys
import hashlib
from pathlib import Path

ROOT = Path(os.environ.get('HKD_PROGRESS_ROOT', Path(__file__).resolve().parent)).resolve()
files = sorted(glob.glob(str(ROOT.parent / 'old-mac-codex-logs/*.jsonl')))
fingerprint = {p: [os.stat(p).st_size, os.stat(p).st_mtime_ns] for p in files}
fingerprint['renderer_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
extra_path = ROOT / 'additional-tasks.json'
extra_raw = extra_path.read_text() if extra_path.exists() else '[]'
fingerprint['additional_tasks_sha256'] = hashlib.sha256(extra_raw.encode()).hexdigest()
cache = ROOT / 'input-cache.json'
try:
    if json.loads(cache.read_text()) == fingerprint and all((ROOT / p).exists() for p in ('status.json', 'index.html', 'widgets.json')):
        print('Evidence unchanged; reusing saved progress.')
        sys.exit(0)
except (OSError, ValueError):
    pass
rows = None
observed = None
source = None
for filename in files:
    with open(filename) as stream:
        for line in stream:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            payload = record.get('payload', {})
            item = payload.get('item', {})
            if record.get('type') != 'event_msg' or item.get('type') != 'CommandExecution':
                continue
            output = item.get('aggregated_output', '')
            decoder = json.JSONDecoder()
            for index, char in enumerate(output):
                if char != '[':
                    continue
                try:
                    candidate, _ = decoder.raw_decode(output[index:])
                except ValueError:
                    continue
                if not isinstance(candidate, list):
                    continue
                selected = [r for r in candidate if isinstance(r, list) and len(r) == 4
                            and r[0] in ('Spindrop plugin', 'RenderDon', 'AUSA commercial · 30s')]
                if len(selected) != 3:
                    continue
                stamp = record.get('timestamp', '')
                if observed is None or stamp > observed:
                    rows, observed, source = selected, stamp, filename
if rows is None:
    raise SystemExit('No complete three-project snapshot found; existing dashboard preserved.')
state = {'observed_at': observed, 'source': source, 'live': False,
         'tasks': [{'name': r[0], 'percent': r[1], 'basis': 'saved estimate',
                    'status': r[2], 'detail': r[3]} for r in rows]}
extra_tasks = json.loads(extra_raw)
if not isinstance(extra_tasks, list):
    raise SystemExit('Additional tasks must be a list; existing dashboard preserved.')
for task in extra_tasks:
    if not isinstance(task, dict) or not all(isinstance(task.get(k), str) for k in ('name', 'status', 'detail', 'basis')):
        raise SystemExit('Invalid additional task; existing dashboard preserved.')
    if not isinstance(task.get('percent'), (int, float)) or not 0 <= task['percent'] <= 100:
        raise SystemExit('Invalid additional task percentage; existing dashboard preserved.')
state['tasks'].extend(extra_tasks)
if len({t['name'] for t in state['tasks']}) != len(state['tasks']) or len(state['tasks']) > 8:
    raise SystemExit('Duplicate or excessive tasks; existing dashboard preserved.')
widgets = {'version': 1, 'placement': 'above', 'widgets': [
    {'id': 'project-progress-' + str(i), 'type': 'text', 'label': task['name'],
     'gradient_progress': True, 'percent': int(task['percent']), 'estimated': True,
     'state': 'snapshot', 'detail': task['status'] + ' · not live',
     'text': str(task['percent']) + '% estimated · saved ' + observed + ' · not live'}
    for i, task in enumerate(state['tasks'])]}
cards = []
for task in state['tasks']:
    value = float(task['percent'])
    if not 0 <= value <= 100:
        raise SystemExit('Invalid progress value; existing dashboard preserved.')
    name, status, detail = (html.escape(task[k]) for k in ('name', 'status', 'detail'))
    cards.append(f'<section><div class="heading"><h2>{name}</h2><strong>{value:g}% <small>estimated</small></strong></div>'
                 f'<progress max="100" value="{value}" aria-label="{name} estimated progress">{value:g}%</progress>'
                 f'<h3>{status}</h3><p>{detail}</p></section>')
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30"><title>Project Progress</title>
<style>body{background:#10191a;color:#eaf5ee;font:16px system-ui;margin:0;padding:36px;max-width:960px;margin-inline:auto}
h1{font-size:30px;margin-bottom:8px}.note{color:#b9c8c2;line-height:1.5}section{background:#1c2929;border:1px solid #3c5050;border-radius:16px;padding:24px;margin:20px 0}
.heading{display:flex;justify-content:space-between;gap:16px;align-items:center}h2{font-size:22px}strong{font-size:25px;white-space:nowrap}small{font-size:13px;font-weight:400;color:#b9c8c2}
progress{width:100%;height:22px;accent-color:#8ee8b7}progress::-webkit-progress-bar{background:#354746;border-radius:9px}progress::-webkit-progress-value{background:#8ee8b7;border-radius:9px}
h3{font-size:13px;color:#8ee8b7;letter-spacing:.05em;margin-top:20px}p{line-height:1.5}footer{color:#b9c8c2;font-size:13px}@media(max-width:600px){body{padding:16px}.heading{display:block}}</style>
<h1>Project Progress</h1><p class="note">Saved evidence · Not a live worker connection<br>Observation: ''' + html.escape(observed) + '''</p>'''
page += '<main style="position:sticky;top:0;background:#10191a;padding:1px 0">' + ''.join(cards) + '</main>'
page += '<footer>One bar per task. Percentages are saved estimates, not measured overall completion. This page reloads every 30 seconds; values change only when newly imported evidence is processed. Whole-pipeline speed and exactness gains remain unverified.</footer></html>'
for name, content in [('status.json', json.dumps(state, indent=2)), ('index.html', page), ('widgets.json', json.dumps(widgets, indent=2)), ('input-cache.json', json.dumps(fingerprint, sort_keys=True))]:
    target = ROOT / name
    temp = target.with_suffix(target.suffix + '.tmp')
    temp.write_text(content)
    os.replace(temp, target)
print('Saved', len(state['tasks']), 'progress bars; imported evidence from', observed)
