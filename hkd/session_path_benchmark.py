"""Measure the real JSONL CLI path, including IPC and output serialization."""
import doctest
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def main():
    request = {'text': (ROOT / 'personal_reliability/smoke_text.txt').read_text(),
               'evidence': [str(ROOT / 'personal_reliability/smoke_evidence.txt')]}
    encoded = json.dumps(request) + '\n'
    start = time.perf_counter()
    process = subprocess.Popen([sys.executable, str(ROOT / 'personal_reliability/check.py'), '--session'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, universal_newlines=True)
    try:
        process.stdin.write(encoded)
        process.stdin.flush()
        first = json.loads(process.stdout.readline())
        fresh = time.perf_counter() - start
        assert first['runtime']['fresh_model_call']
        samples = []
        for _ in range(31):
            start = time.perf_counter()
            process.stdin.write(encoded)
            process.stdin.flush()
            report = json.loads(process.stdout.readline())
            samples.append(time.perf_counter() - start)
            assert report['runtime']['mode'] == 'reused_saved_review'
            for key in ('original', 'annotated', 'findings', 'source_sha256', 'status',
                        'truth_certified', 'semantic_completeness_verified'):
                assert report[key] == first[key]
        process.stdin.close()
        assert process.wait(timeout=5) == 0
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
    result = {'scope': 'Actual child CLI session: request IPC, evidence reads, exact-key lookup, validation, JSON serialization, flush and response parsing',
              'fresh_requests': 1, 'saved_requests': 31, 'fresh_with_startup_seconds': fresh,
              'saved_mean_seconds': statistics.mean(samples),
              'saved_median_seconds': statistics.median(samples),
              'saved_p95_seconds': sorted(samples)[29], 'saved_max_seconds': max(samples),
              'saved_samples_seconds': samples, 'content_equal': True,
              'fresh_runtime': first['runtime'], 'truth_certified': False,
              'hardware_cycles_measured': False,
              'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                                ['personal_reliability/check.py', 'personal_reliability/reuse.py',
                                 'personal_reliability/hkd_runtime.py', 'vendor/hkd_thread_paid.py',
                                 'session_path_benchmark.py']},
              'limits': 'Saved artifact reuse, not new model inference; no ChatGPT UI/network ingress included; single fresh sample is not a latency distribution.'}
    (ROOT / 'session_path_benchmark.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k.startswith('saved_') and k != 'saved_samples_seconds'}))


if __name__ == '__main__':
    assert doctest.testmod().failed == 0
    main()
