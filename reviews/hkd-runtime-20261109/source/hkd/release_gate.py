"""Source-bound release launcher for the 20 registered error contracts.

This is an integrity/regression gate, not a universal truth detector.
>>> good_report({'total_categories':20,'passed_categories':20,'failing_categories':[]})
True
>>> good_report({'total_categories':18,'passed_categories':18,'failing_categories':[]})
False
>>> good_report({'total_categories':20,'passed_categories':19,'failing_categories':['x']})
False
>>> good_report({})
False
"""
import argparse
import doctest
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'hkd/release'
TARGET = Path.home() / '.cache/hkd-codex-target'


def good_report(report):
    return (report.get('total_categories') == 20 and report.get('passed_categories') == 20
            and report.get('failing_categories') == [])


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def sources():
    names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).decode().split('\0')
    paths = {name for name in names if name.startswith('codex-rs/') and '/target/' not in name
             and Path(name).suffix in {'.rs', '.toml', '.lock', '.md', '.txt', '.json', '.snap'}}
    paths.update(str(path.relative_to(ROOT)) for path in (ROOT / 'hkd').rglob('*.py')
                 if not any(part in {'release', 'build_validation_20261107', '__pycache__'} for part in path.parts))
    paths.update(str(path.relative_to(ROOT)) for path in (ROOT / 'hkd').rglob('*.rs'))
    paths.update(['hkd/features/Cargo.toml', 'hkd/features/Cargo.lock'])
    paths.update(['hkd/known_error_types.json', 'hkd/execution_repair/sling-source.json', 'hkd/execution_repair/host-source.json', 'AGENTS.md'])
    return {name: digest(ROOT / name) for name in sorted(paths) if (ROOT / name).is_file()}


def regress():
    from compaction_guard import require_source
    require_source()
    sys.path.insert(0, str(ROOT / 'hkd'))
    from monitor_known_types import monitor
    result = monitor(ROOT / 'hkd/known_error_types.json')
    if not good_report(result):
        raise RuntimeError('Release blocked: the 20 registered contracts did not all pass')
    return result


def compatible_host_sources(previous, current):
    """Only these CLI-only UI modules may differ for verified host reuse.

    >>> compatible_host_sources({'codex-rs/core/a.rs':'a'}, {'codex-rs/core/a.rs':'b'})
    False
    >>> compatible_host_sources({'codex-rs/Cargo.lock':'a'}, {})
    False
    >>> compatible_host_sources({'codex-rs/tui/src/anticipation.rs':'a'}, {'codex-rs/tui/src/anticipation.rs':'b'})
    True
    """
    excluded = {'codex-rs/tui/src/anticipation.rs', 'codex-rs/tui/src/task_progress.rs', 'codex-rs/tui/src/status_indicator_widget.rs', 'codex-rs/tui/src/prompt_speech.rs'}
    native = lambda values: {k: v for k, v in values.items()
                             if k.startswith('codex-rs/') and k not in excluded}
    return native(previous) == native(current)


def build(reuse_verified_host=False):
    RELEASE.mkdir(exist_ok=True)
    if shutil.disk_usage(TARGET).free < 4 * 2**30:
        raise RuntimeError('Build blocked: less than 4 GiB free; preserve running builds and caches')
    before = sources()
    host_cache = None
    if reuse_verified_host:
        from release_activation import read_receipt
        from execution_repair.host_guard import verify_host
        _, previous = read_receipt(RELEASE / 'receipt.json')
        if not compatible_host_sources(previous['sources'], before):
            raise RuntimeError('Host reuse blocked: native inputs beyond CLI preview changed')
        host_cache = verify_host(RELEASE / 'codex', previous['code_mode_host']['sha256'])
        host_cache['previous_receipt_sha256'] = digest(RELEASE / 'receipt.json')
    checks = regress()
    for command in [
        [sys.executable, '-m', 'doctest', 'hkd/compaction_guard.py'],
        [sys.executable, 'hkd/feature_checks.py'],
        [sys.executable, 'hkd/execution_repair/test_workers.py'],
        [sys.executable, '-m', 'doctest', 'hkd/execution_repair/host_guard.py', 'hkd/execution_repair/workers.py'],
        [sys.executable, 'hkd/anticipation.py', '--test'],
        [sys.executable, '-m', 'doctest', 'hkd/speech.py', 'hkd/build_dashboard.py'],
    ]:
        subprocess.run(command, cwd=ROOT, check=True)
    environment = dict(os.environ, CARGO_TARGET_DIR=str(TARGET))
    with (RELEASE / 'build.log').open('w') as log:
        subprocess.run(['cargo', 'build', '--locked', '--release', '-p', 'codex-cli', '--bin', 'codex', * ([] if reuse_verified_host else ['-p', 'codex-code-mode-host', '--bin', 'codex-code-mode-host']), '-p', 'codex-exec-server-cli', '--bin', 'codex-exec-server', '--jobs', '2', '--config', 'profile.release.package.codex-tui.opt-level=1', '--config', 'profile.release.package.codex-tui.codegen-units=32', '--config', 'profile.release.package.codex-tui.debug=0'],
                       cwd=ROOT / 'codex-rs', env=environment, stdout=log, stderr=subprocess.STDOUT, check=True)
    after = sources()
    if before != after:
        raise RuntimeError('Source changed during compilation; rerun the release gate')
    binary = RELEASE / 'codex'
    temporary = RELEASE / 'codex.new'
    shutil.copy2(TARGET / 'release/codex', temporary)
    temporary.replace(binary)
    # Use the host and exec server from this exact paired source build.
    for name in (['codex-exec-server'] if reuse_verified_host else ['codex-code-mode-host', 'codex-exec-server']):
        shutil.copy2(TARGET / 'release' / name, RELEASE / name)
    from execution_repair.host_guard import verify_host
    host = verify_host(binary, host_cache['sha256'] if host_cache else digest(TARGET / 'release/codex-code-mode-host'))
    host['origin'] = str(RELEASE / 'codex-code-mode-host') if host_cache else str(TARGET / 'release/codex-code-mode-host')
    host['built_from_this_source'] = not reuse_verified_host
    if host_cache:
        host['reused_from_verified_release'] = True
        host['previous_receipt_sha256'] = host_cache['previous_receipt_sha256']
        host['native_input_comparison'] = 'All recorded native source hashes unchanged except CLI-only preview/progress modules'
        host['reason'] = 'V8 build artifact URL returned HTTP 404; retained existing hash-verified host'
    test_environment = dict(os.environ, HKD_TEST_BINARY=str(binary),
                            HKD_TEST_RECEIPT=str(RELEASE / 'command-receipt.json'))
    with (RELEASE / 'command-tests.log').open('w') as test_log:
        subprocess.run([sys.executable, str(ROOT / 'hkd/execution_repair/test_commands.py')],
                       cwd=ROOT, env=test_environment, stdout=test_log,
                       stderr=subprocess.STDOUT, check=True)
    subprocess.run(['cargo', 'build', '--locked', '--offline', '--manifest-path',
                    str(ROOT / '.codex-cache/hkd-vt100/Cargo.toml')], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / 'hkd/execution_repair/test_native_activity.py')],
                   cwd=ROOT, env=test_environment, check=True)
    if after != sources():
        raise RuntimeError('Source changed during runtime validation; rerun the release gate')
    version = subprocess.check_output([str(binary), '--version'], text=True).strip()
    receipt = {'created_at': time.time(), 'version': version, 'sources': after,
               'binary_sha256': digest(binary), 'code_mode_host': host, 'registered_categories': checks['total_categories'],
               'passed_categories': checks['passed_categories'], 'command_tests': json.loads((RELEASE / 'command-receipt.json').read_text()),
               'scope': 'Registered contracts and actual command execution regressions; no universal truth guarantee'}
    (RELEASE / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('Built and sealed:', binary, version)


def verify():
    from release_activation import read_receipt
    _, receipt = read_receipt(RELEASE / 'receipt.json')
    from compaction_guard import require_receipt
    require_receipt(receipt)
    if receipt['sources'] != sources() or receipt['binary_sha256'] != digest(RELEASE / 'codex'):
        raise RuntimeError('Launch blocked: source or executable differs from the tested release')
    from execution_repair.host_guard import verify_host
    verify_host(RELEASE / 'codex', receipt['code_mode_host']['sha256'])
    checks = regress()
    print(f"{checks['passed_categories']}/{checks['total_categories']} registered contracts passed; release identity verified.", flush=True)


def launch(arguments):
    verify()
    environment = os.environ
    environment['CODEX_SPEECH_SCRIPT'] = str(ROOT / 'hkd/speech.py')
    environment['CODEX_SPEECH_PYTHON'] = str(Path.home() / '.cache/hkd-speech/venv/bin/python')
    environment['CODEX_ANTICIPATION_SCRIPT'] = str(ROOT / 'hkd/anticipation.py')
    environment['CODEX_ANTICIPATION_PYTHON'] = sys.executable
    launcher = ROOT / 'hkd/local_cluster/launch.py'
    # argparse consumes the outer separator. Supply a new one so Codex flags
    # reach Codex rather than being parsed as local-cluster launcher options.
    forwarded = arguments[1:] if arguments[:1] == ['--'] else arguments
    os.execv(sys.executable, [sys.executable, str(launcher), '--codex', str(RELEASE / 'codex'), '--'] + forwarded)


if __name__ == '__main__':
    if doctest.testmod().failed:
        raise SystemExit(1)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build', 'build-reusing-host', 'verify', 'install', 'launch'])
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.action in ('build', 'build-reusing-host'):
            build(reuse_verified_host=args.action == 'build-reusing-host')
        elif args.action == 'verify':
            verify()
        elif args.action == 'install':
            from release_activation import activate
            body = '#!/bin/sh\nset -eu\nexec '+str(ROOT / 'scripts/codex-hkd')+' "$@"\n'
            activate(Path.home() / '.local/bin/codex', RELEASE / 'receipt.json', body, verify)
            print('Validated custom launcher installed.')
        else:
            launch(args.arguments)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as error:
        print('Release gate:', error, file=sys.stderr)
        raise SystemExit(1)
