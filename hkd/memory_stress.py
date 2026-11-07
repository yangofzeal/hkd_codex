"""Measure bounded reviewer retention and real CLI RSS; not whole-Codex memory.

Deterministic allocation stress uses a fixture reviewer, not model inference.
The actual CLI stage performs one live model request and 100,000 saved reviews.
"""
import doctest
import gc
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import tracemalloc

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'personal_reliability'))
import check
from reuse import ReviewSession


def rss(pid):
    return int(subprocess.check_output(['/bin/ps', '-o', 'rss=', '-p', str(pid)]).strip()) * 1024


def local_stress():
    def reviewer(*args):
        return {'findings': []}, {'fixture_reviewer': True}
    session = ReviewSession(reviewer, check.validate, 'memory-stress')
    tracemalloc.start()
    samples = []
    for i in range(22000):
        # Distinct requests force eviction; large inputs test byte as well as count limits.
        size = 1000 if i % 2 else 64000
        result = session.review('Fixture {} {}'.format(i, 'x' * size), {'s': 'Explicit test evidence.'})
        del result
        if (i + 1) % 2000 == 0:
            gc.collect()
            current, peak = tracemalloc.get_traced_memory()
            snapshot = tracemalloc.take_snapshot().filter_traces([
                tracemalloc.Filter(True, str(ROOT / 'personal_reliability/reuse.py')),
                tracemalloc.Filter(True, str(ROOT / 'personal_reliability/check.py'))])
            hkd_retained = sum(item.size for item in snapshot.statistics('filename'))
            del snapshot
            assert len(session.entries) <= 8
            assert session.bytes <= 1048576
            assert session.bytes == sum(len(k) + len(v[1]) for k, v in session.entries.items())
            samples.append({'requests': i + 1, 'python_retained_bytes': current,
                            'python_peak_bytes': peak, 'rss_bytes': rss(os.getpid()),
                            'hkd_module_retained_bytes': hkd_retained,
                            # Copy the integer in the harness, rather than retain
                            # the cache's obsolete accounting object in samples.
                            'entries': len(session.entries), 'serialized_cache_bytes': int(str(session.bytes)),
                            'threads': threading.active_count()})
    session.clear()
    gc.collect()
    after_clear = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    return {'fixture_reviewer': True, 'requests': 22000, 'warmup_requests': 2000,
            'samples': samples, 'python_bytes_after_clear': after_clear,
            'post_warmup_retained_delta_bytes': samples[-1]['python_retained_bytes'] - samples[0]['python_retained_bytes'],
            'note': 'Sample records also consume a small bounded amount of retained Python memory.'}


def cli_stress():
    request = json.dumps({'text': (ROOT / 'personal_reliability/smoke_text.txt').read_text(),
                         'evidence': [str(ROOT / 'personal_reliability/smoke_evidence.txt')]}) + '\n'
    samples = []
    times = []
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen([sys.executable, str(ROOT / 'personal_reliability/check.py'), '--session'],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=errors, universal_newlines=True)
        try:
            start = time.perf_counter()
            process.stdin.write(request); process.stdin.flush()
            first = json.loads(process.stdout.readline())
            fresh = time.perf_counter() - start
            assert first['runtime']['fresh_model_call']
            keys = ['original', 'annotated', 'findings', 'source_sha256', 'status',
                    'truth_certified', 'semantic_completeness_verified']
            for i in range(100000):
                start = time.perf_counter()
                process.stdin.write(request); process.stdin.flush()
                result = json.loads(process.stdout.readline())
                times.append(time.perf_counter() - start)
                assert result['runtime']['mode'] == 'reused_saved_review'
                assert all(result[k] == first[k] for k in keys)
                if (i + 1) % 10000 == 0:
                    samples.append({'saved_requests': i + 1, 'child_rss_bytes': rss(process.pid)})
            process.stdin.close()
            assert process.wait(timeout=5) == 0
        finally:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait()
            process.stdin.close(); process.stdout.close()
    return {'live_model_calls': 1, 'saved_requests': 100000, 'fresh_seconds': fresh,
            'saved_mean_seconds': statistics.mean(times), 'saved_median_seconds': statistics.median(times),
            'saved_p95_seconds': sorted(times)[94999], 'saved_max_seconds': max(times),
            'samples': samples, 'child_rss_delta_bytes': samples[-1]['child_rss_bytes'] - samples[0]['child_rss_bytes'],
            'content_equal': True, 'clean_child_exit': True}


def main():
    started = time.perf_counter()
    result = {'scope': 'HKD Python reviewer allocation stress and actual JSONL session; not whole Codex or ChatGPT',
              'local': local_stress(), 'cli': cli_stress(),
              'elapsed_seconds': time.perf_counter() - started,
              'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                                ['personal_reliability/check.py', 'personal_reliability/reuse.py', 'memory_stress.py']},
              'limits': 'Finite tests cannot prove absence of all leaks. RSS includes allocator/runtime memory. No model-context compaction setting changed. No iTerm2-equivalence claim.'}
    (ROOT / 'memory_stress.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'local_retained_delta_bytes': result['local']['post_warmup_retained_delta_bytes'],
                      'cli_rss_delta_bytes': result['cli']['child_rss_delta_bytes'],
                      'elapsed_seconds': result['elapsed_seconds']}))


if __name__ == '__main__':
    assert doctest.testmod().failed == 0
    main()
