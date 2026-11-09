#!/usr/bin/env python3
"""Public, independent demonstrations of exact aggregation and sampling thinning.

This is not a translation, implementation, or validation of a private algorithm.
Only finite integer sums and a declared rational sampling grid are used. Python
3.9+ and the standard library suffice. No files or services are read by the demos.

>>> aggregate_binary([1, 1, 1]).counts
((0, 1), (1, 3), (2, 3), (3, 1))
>>> sampling_count(12, 4)
4
>>> sampling_count(12, 13)
1
>>> sampling_within_budget(12, 4, 3)
False
>>> sampling_within_budget(12, 5, 3)
True
"""

from dataclasses import dataclass
from fractions import Fraction
import argparse
import doctest
import json
import sys


def _integer(value, name, minimum=0):
    if type(value) is not int:
        raise TypeError(name + " must be a built-in integer (not bool)")
    if value < minimum:
        raise ValueError(name + " must be >= " + str(minimum))
    return value


@dataclass(frozen=True)
class Aggregation:
    """Immutable, sorted counts and one index witness per reachable sum.

    widths includes the initial singleton state. transitions counts two
    candidate contributions per old state; it is not CPU time or bit cost.
    """

    counts: tuple
    witnesses: tuple
    widths: tuple
    transitions: int
    histories: int


class StateLimitExceeded(RuntimeError):
    """Exact aggregation stopped; no approximate result is returned."""


def aggregate_binary(weights, *, max_states=100_000):
    """Count all binary selections, coalescing only identical partial sums.

    Zero weights and duplicates denote distinct selectable positions. Negative
    weights are excluded from this public model. Witnesses use input indices.
    A resource limit aborts rather than silently pruning reachable states.

    >>> aggregate_binary([]).counts
    ((0, 1),)
    >>> aggregate_binary([0, 0]).counts
    ((0, 4),)
    >>> aggregate_binary([2, 2]).witnesses
    ((0, ()), (2, (1,)), (4, (0, 1)))
    >>> try:
    ...     aggregate_binary([1, 2], max_states=2)
    ... except StateLimitExceeded as error:
    ...     print(str(error))
    exact state limit exceeded at layer 2
    """
    _integer(max_states, "max_states", 1)
    values = tuple(weights)
    for weight in values:
        _integer(weight, "weight")
    counts = {0: 1}
    witnesses = {0: ()}
    widths = [1]
    transitions = 0
    for index, weight in enumerate(values):
        next_counts = {}
        next_witnesses = {}
        # Input order and dictionary insertion order give deterministic witnesses.
        for total, multiplicity in counts.items():
            for chosen in (False, True):
                candidate = total + (weight if chosen else 0)
                transitions += 1
                if candidate not in next_counts:
                    if len(next_counts) >= max_states:
                        raise StateLimitExceeded(
                            "exact state limit exceeded at layer " + str(index + 1)
                        )
                    next_counts[candidate] = 0
                    next_witnesses[candidate] = (
                        witnesses[total] + (index,) if chosen else witnesses[total]
                    )
                next_counts[candidate] += multiplicity
        counts, witnesses = next_counts, next_witnesses
        widths.append(len(counts))
    return Aggregation(
        tuple(sorted(counts.items())), tuple(sorted(witnesses.items())),
        tuple(widths), transitions, 1 << len(values)
    )


def verify_witness(weights, target, indices):
    """Verify an indexed selection without running the aggregation algorithm.

    >>> verify_witness([2, 2, 5], 4, (0, 1))
    True
    >>> verify_witness([2, 2, 5], 4, (0, 0))
    False
    >>> verify_witness([2, 2, 5], 4, (True, 1))
    False
    """
    try:
        values = tuple(weights)
        chosen = tuple(indices)
        _integer(target, "target")
        for weight in values:
            _integer(weight, "weight")
        if any(type(i) is not int or i < 0 or i >= len(values) for i in chosen):
            return False
        if len(set(chosen)) != len(chosen):
            return False
        return sum(values[i] for i in chosen) == target
    except (TypeError, ValueError):
        return False


def sampling_count(budget, scale):
    """Count integer j >= 0 with scale*j <= budget, including j=0.

    This is an exact grid count, not a general optimization/search solver.
    >>> sampling_count(0, 9)
    1
    >>> sampling_count(17, 4)
    5
    >>> sampling_count(4, 0)
    Traceback (most recent call last):
    ...
    ValueError: scale must be >= 1
    """
    _integer(budget, "budget")
    _integer(scale, "scale", 1)
    return budget // scale + 1


def sampling_within_budget(budget, scale, max_samples):
    """Exact threshold: K <= k iff budget < k*scale, for k >= 1.

    >>> sampling_within_budget(0, 1, 0)
    False
    >>> sampling_within_budget(10, 11, 1)
    True
    """
    _integer(budget, "budget")
    _integer(scale, "scale", 1)
    _integer(max_samples, "max_samples")
    return budget < max_samples * scale


def integer_grid_maximum(coefficients, budget, scale, *, max_samples=100_000):
    """Maximize a polynomial over ONLY the declared finite integer grid.

    Coefficients are ascending-power integers. Exact values use Horner's rule.
    Ties choose the smallest index. This makes no continuous-domain guarantee.

    >>> integer_grid_maximum([0, 4, -1], 12, 3)
    (2, 4, 5)
    >>> integer_grid_maximum([0], 5, 2)
    (0, 0, 3)
    """
    values = tuple(coefficients)
    if not values or any(type(c) is not int for c in values):
        raise ValueError("coefficients must be a nonempty sequence of integers")
    _integer(max_samples, "max_samples", 1)
    count = sampling_count(budget, scale)
    if count > max_samples:
        raise StateLimitExceeded("exact sampling limit exceeded")
    best_index, best_value = 0, None
    for index in range(count):
        value = 0
        for coefficient in reversed(values):
            value = value * index + coefficient
        if best_value is None or value > best_value:
            best_index, best_value = index, value
    return best_index, best_value, count


def demo():
    """Return deterministic public examples, with no machine-speed claims."""
    aggregation = []
    for length in (4, 8, 12, 16):
        result = aggregate_binary([1] * length)
        aggregation.append({
            "length": length, "histories": result.histories,
            "final_states": len(result.counts), "transitions": result.transitions,
            "mass_verified": sum(c for _, c in result.counts) == result.histories,
        })
    thinning = []
    for scale in (1, 2, 3, 6, 12, 25):
        best_index, best_value, samples = integer_grid_maximum([0, 4, -1], 24, scale)
        thinning.append({
            "scale": scale, "interval_end": str(Fraction(24, scale)),
            "samples": samples, "best_index": best_index, "best_value": best_value,
        })
    return {
        "scope": "independent public aggregation and finite-grid demonstrations",
        "aggregation": aggregation, "thinning": thinning,
        "caution": "Different scales define different feasible grids; no universal speedup.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", nargs="?", help="Python source to specialize without executing it")
    parser.add_argument("-o", "--output", help="Output Python file (input is preserved)")
    parser.add_argument("--memoize", action="append", default=[], help="Opt in a supported pure function to bounded reuse")
    parser.add_argument("--cache-size", type=int, default=256)
    parser.add_argument("--self-test", action="store_true", help="run embedded examples only")
    args = parser.parse_args(argv)
    # Explicit testmod() on every CLI execution, as requested for this project.
    result = doctest.testmod(sys.modules[__name__])
    if result.failed:
        return 1
    if args.input:
        from pft_transform import convert
        output=args.output or str(__import__("pathlib").Path(args.input).with_suffix(".pft.py"))
        print(json.dumps(convert(args.input, output, args.memoize, args.cache_size), indent=2))
        return 0
    if args.self_test:
        print(json.dumps({"doctests": result.attempted, "failures": result.failed}))
    else:
        print(json.dumps(demo(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
