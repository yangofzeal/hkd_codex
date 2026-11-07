"""Measure fresh model review separately from explicitly labeled snapshot reuse.

Runs one real model call on the existing synthetic smoke fixture, then 31
same-input saved-review requests. The ratio is NOT model inference speedup.
Evidence file reading and validation are included in each measured request.
"""
import doctest
import hashlib
import json
from pathlib import Path
import platform
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'personal_reliability'))
import check


def main():
    session = check.new_session()
    text = (ROOT / 'personal_reliability/smoke_text.txt').read_text()
    evidence = [str(ROOT / 'personal_reliability/smoke_evidence.txt')]
    start = time.perf_counter()
    first = session.review(text, check.load_sources(evidence))
    fresh = time.perf_counter() - start
    timings = []
    for _ in range(31):
        start = time.perf_counter()
        reused = session.review(text, check.load_sources(evidence))
        timings.append(time.perf_counter() - start)
        assert reused['runtime']['fresh_model_call'] is False
        for key in ('original', 'annotated', 'findings', 'source_sha256', 'status'):
            assert reused[key] == first[key], key
    session.clear()
    result = {
        'scope': 'One fresh synthetic review versus 31 identical saved-review requests; not fresh-inference acceleration',
        'python': platform.python_version(), 'platform': platform.platform(),
        'fresh_requests': 1, 'saved_requests': len(timings),
        'fresh_seconds': fresh, 'saved_median_seconds': statistics.median(timings),
        'saved_p95_seconds': sorted(timings)[29], 'saved_samples_seconds': timings,
        'content_equal': True, 'fresh_runtime': first['runtime'],
        'fresh_findings': len(first['findings']),
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [ROOT / 'personal_reliability/check.py',
                                    ROOT / 'personal_reliability/reuse.py',
                                    Path(__file__)]},
        'limits': ['Single fresh-call sample; no inference-speedup conclusion.',
                   'Reused judgments may be wrong; identical evidence is not proof of current world state.',
                   'In-process latency excludes initial interpreter startup and user-interface latency.']}
    (ROOT / 'reuse_benchmark.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['fresh_seconds', 'saved_median_seconds',
                                           'saved_p95_seconds', 'content_equal']}))


if __name__ == '__main__':
    assert doctest.testmod().failed == 0
    main()
