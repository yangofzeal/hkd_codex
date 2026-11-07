"""Bounded evidence reads through the inspected user-supplied HKD Thread Paid.

This maps independent file reads, not hosted model inference, to paid HKD code.
No content, file-read result, or model judgment is cached.

>>> load_sources([]) == {}
True
"""
from importlib.machinery import SourceFileLoader
from importlib import util
from collections import OrderedDict
from pathlib import Path

VENDOR = Path(__file__).resolve().parents[1] / 'vendor' / 'hkd_thread_paid.py'


def load_module(name, path):
    """Use modern import APIs on 3.11, with the 3.4-compatible fallback."""
    if hasattr(util, 'module_from_spec'):
        spec = util.spec_from_file_location(name, str(path))
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return SourceFileLoader(name, str(path)).load_module()


_thread = load_module('hkd_thread_paid', VENDOR)
LIMIT = 200000


def load_sources(paths):
    if len(paths) > 16:
        raise ValueError('At most 16 evidence files per review')

    def read(index):
        with Path(paths[index]).open('rb') as stream:
            data = stream.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ValueError('Input exceeds 200 KB per file')
        return data.decode('utf-8')

    values = _thread.map_active(len(paths), range(len(paths)), read,
                                workers=min(4, max(1, len(paths))))
    if sum(len(text.encode('utf-8')) for text in values) > LIMIT:
        raise ValueError('Combined evidence exceeds 200 KB')
    return OrderedDict(('source_{}'.format(i), text) for i, text in enumerate(values, 1))
