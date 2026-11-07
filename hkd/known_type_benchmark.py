"""Matched known-error fixture: previous model path versus deterministic detection.

Uses one real baseline model call. Warm candidate requests force fresh evaluation,
so their latency is not saved-review reuse. Measures the full local JSONL path.
"""
import doctest
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
BASELINE = '3c3e731dddbd17c7c9555b5ec2a23c4cbb53fa1f'


def run(script, source, repeated):
    env = dict(os.environ)
    env['PYTHONPATH'] = str(ROOT / 'personal_reliability')
    request = json.dumps({'text': 'All tests passed.', 'evidence': [str(source)], 'fresh': True}) + '\n'
    started = time.perf_counter()
    with tempfile.TemporaryFile() as errors:
        proc = subprocess.Popen([sys.executable, str(script), '--session'], env=env,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=errors, universal_newlines=True)
        try:
            proc.stdin.write(request); proc.stdin.flush()
            first = json.loads(proc.stdout.readline())
            cold = time.perf_counter() - started
            times = []
            for _ in range(repeated):
                started = time.perf_counter()
                proc.stdin.write(request); proc.stdin.flush()
                result = json.loads(proc.stdout.readline())
                times.append(time.perf_counter() - started)
                assert result['runtime']['mode'] == 'deterministic_known_type'
                assert not result['runtime']['fresh_model_call']
                assert result['findings'] == first['findings']
            proc.stdin.close()
            assert proc.wait(timeout=5) == 0
        finally:
            if proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait()
            proc.stdin.close(); proc.stdout.close()
    return first, cold, times


def main():
    with tempfile.TemporaryDirectory(prefix='hkd-known-type-benchmark-') as directory:
        source = Path(directory) / 'evidence.txt'
        source.write_text('Two tests failed.')
        old = Path(directory) / 'baseline_check.py'
        old.write_bytes(subprocess.check_output(['git', 'show', BASELINE + ':hkd/personal_reliability/check.py'], cwd=ROOT))
        baseline, before, _ = run(old, source, 0)
        candidate, after, times = run(ROOT / 'personal_reliability/check.py', source, 1000)
        assert any(f['claim'] == 'All tests passed.' for f in candidate['findings'])
        result = {'scope': 'Single declared known-error fixture, before/after complete local CLI path; not general inference speedup',
                  'baseline_commit': BASELINE, 'baseline_script_sha256': hashlib.sha256(old.read_bytes()).hexdigest(),
                  'cold_baseline_seconds': before, 'cold_candidate_seconds': after,
                  'cold_speedup': before / after, 'cold_samples_each': 1,
                  'baseline_expected_claim_detected': any('All tests passed.' in f['claim'] for f in baseline['findings']),
                  'candidate_expected_claim_detected': True,
                  'warm_forced_fresh_count': len(times), 'warm_mean_seconds': statistics.mean(times),
                  'warm_median_seconds': statistics.median(times), 'warm_p95_seconds': sorted(times)[949],
                  'warm_max_seconds': max(times), 'warm_samples_seconds': times,
                  'candidate_model_calls': 0, 'baseline_model_calls': 1,
                  'candidate_runtime': candidate['runtime'],
                  'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in [ROOT / 'personal_reliability/check.py', ROOT / 'personal_reliability/known_types.py',
                                             ROOT / 'personal_reliability/reuse.py', Path(__file__)]},
                  'limits': 'No new language-model generation on candidate path. Guarantee is limited to the registered source-pairing/grammar contract. Cold ratio uses one sample each.'}
    (ROOT / 'known_type_benchmark.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k in ['cold_baseline_seconds', 'cold_candidate_seconds', 'cold_speedup', 'warm_mean_seconds', 'warm_p95_seconds', 'warm_max_seconds']}))


if __name__ == '__main__':
    assert doctest.testmod().failed == 0
    main()
