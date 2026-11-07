"""Deterministic detectors with explicit, narrow input contracts.

>>> test_failure_guard('All tests passed.', {'s': 'Two tests failed.'})['status']
'detected'
>>> test_failure_guard('All tests passed.', {'s': '0 tests failed.'})['status']
'no_conflict_in_scope'
>>> test_failure_guard('Did all tests pass?', {'s': 'Two tests failed.'})['status']
'out_of_scope'
"""
import re

VERSION = 'known-types-v1'
FAILURES = re.compile(r'(0|[1-9][0-9]{0,8}|One|Two) tests? failed\.')


def test_failure_guard(text, sources):
    """Check one unqualified assertion against one supplied run outcome.

    This is relative to the caller-supplied evidence pairing, not certification
    that a source is truthful, fresh, or describes the intended real-world run.
    Other syntax, multiple sources, questions and quotations are out of scope.
    """
    result = {'category': 'missed_explicit_test_failure', 'version': VERSION,
              'status': 'out_of_scope'}
    if text.strip() != 'All tests passed.' or len(sources) != 1:
        return result
    source_id, evidence = next(iter(sources.items()))
    match = FAILURES.fullmatch(evidence.strip())
    if match is None:
        return result
    token = match.group(1)
    failed = {'One': 1, 'Two': 2}.get(token)
    if failed is None:
        failed = int(token)
    result['status'] = 'detected' if failed else 'no_conflict_in_scope'
    if failed:
        result['finding'] = {
            'claim': 'All tests passed.', 'verdict': 'contradicted',
            'source_id': source_id, 'evidence_quote': evidence.strip(),
            'reason': 'Deterministic check: the supplied run outcome records {} failed test(s).'.format(failed)}
    return result
