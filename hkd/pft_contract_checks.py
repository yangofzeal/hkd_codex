"""Exact arithmetic checks of the restricted fixed-gap theorem, not LLM truth.

>>> count_to_pair(11, 13)
1
>>> count_to_pair(1009, 1327)
11
"""
import doctest
import hashlib
import json
import math
from pathlib import Path


def count_to_pair(p, q):
    n = p * q
    root = math.isqrt(n)
    return (p + q) // 2 - root - (root * root < n) + 1


def main():
    primes = [n for n in range(3, 600, 2)
              if all(n % d for d in range(3, math.isqrt(n) + 1, 2))]
    groups = {}
    pairs = 0
    for i, p in enumerate(primes):
        for q in primes[i + 1:]:
            a, d = (p + q) // 2, (q - p) // 2
            k = count_to_pair(p, q)
            if d * d < 2 * a - 1:
                assert k == 1
            groups.setdefault(d, []).append((a, k))
            pairs += 1
    for group in groups.values():
        group.sort()
        assert all(right[1] <= left[1] for left, right in zip(group, group[1:]))
    p, q = 6154055552798757774153103, 6154055556631142216953801
    a, d = 100005344163055407336319304256712, 1916192221400349
    counts = [count_to_pair(p, q), count_to_pair(a - d, a + d)]
    assert counts == [298323, 1]
    result = {'small_prime_pairs_checked': pairs, 'fixed_gap_groups': len(groups),
              'paper_example_counts_to_given_pair': counts,
              'magnitude_only_counterexample': {'143': 1, '1338943': 11},
              'hardware_cycles_measured': False,
              'universal_hallucination_theorem': False,
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'scope': 'Exact integer count identities and finite fixed-gap checks. No live factoring performance or semantic correctness claim.'}
    Path(__file__).with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    assert doctest.testmod().failed == 0
    main()
