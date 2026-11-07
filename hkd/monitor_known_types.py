"""Run the registered error-contract regressions; never infer global correctness."""
import argparse
import doctest
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'personal_reliability'))


def monitor(registry_path):
    registry = json.loads(Path(registry_path).read_text())
    categories = registry['categories']
    if not isinstance(categories, list) or not categories:
        raise ValueError('The known-type registry must contain at least one category')
    ids = [c['id'] for c in categories]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate category IDs')
    rows = []
    for category in categories:
        if not category.get('scope') or not category.get('tests'):
            raise ValueError('Every category requires explicit scope and regression tests')
        suite = unittest.defaultTestLoader.loadTestsFromNames(category['tests'])
        output = io.StringIO()
        result = unittest.TextTestRunner(stream=output, verbosity=0).run(suite)
        passed = result.wasSuccessful() and result.testsRun > 0 and not result.skipped and not result.expectedFailures
        rows.append({'id': category['id'], 'scope': category['scope'],
                     'status': 'passed' if passed and category['status'] == 'enforced' else 'open_or_failed',
                     'tests_run': result.testsRun, 'failures': len(result.failures),
                     'errors': len(result.errors), 'skipped': len(result.skipped),
                     'expected_failures': len(result.expectedFailures)})
        if not passed:
            print(output.getvalue(), file=sys.stderr)
    sources = {ROOT / 'personal_reliability' / name for name in
               ['check.py', 'reuse.py', 'known_types.py', 'hkd_runtime.py']}
    sources.update(ROOT / 'vendor' / name for name in ['hkd_alu.py', 'hkd_thread_paid.py'])
    sources.add(Path(__file__).resolve())
    for category in categories:
        for name in category['tests']:
            module = sys.modules.get(name.split('.')[0])
            path = getattr(module, '__file__', None)
            if path and ROOT in Path(path).resolve().parents:
                sources.add(Path(path).resolve())
    return {'scope': registry['scope'], 'categories': rows,
            'passed_categories': sum(r['status'] == 'passed' for r in rows),
            'total_categories': len(rows),
            'failing_categories': [r['id'] for r in rows if r['status'] != 'passed'],
            'registry_sha256': hashlib.sha256(Path(registry_path).read_bytes()).hexdigest(),
            'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(sources)},
            'limits': 'Zero failing registered regressions, not proof of zero errors outside each declared contract. This monitors repository tests, not live ChatGPT conversations.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', default=str(ROOT / 'known_error_types.json'))
    parser.add_argument('--output', default=str(ROOT / 'known_type_monitor.json'))
    args = parser.parse_args()
    report = monitor(args.registry)
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n')
    for row in report['categories']:
        print('{}: {} ({} tests)'.format(row['id'], row['status'], row['tests_run']))
    print('{}/{} categories pass; {} failing categories.'.format(
        report['passed_categories'], report['total_categories'], len(report['failing_categories'])))
    return int(bool(report['failing_categories']))


if __name__ == '__main__':
    assert doctest.testmod().failed == 0
    raise SystemExit(main())
