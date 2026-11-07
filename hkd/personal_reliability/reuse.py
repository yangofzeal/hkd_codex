"""Bounded process-local reuse of explicitly identified review snapshots.

This reuses a saved model assessment; it is NOT a new model generation, a
fresh observation of the world, or proof a stochastic model would repeat it.
Exact text/evidence/kind/implementation keys and revalidation protect integrity.
Nothing is persisted to disk. This implements the video paper's reuse principle
only for saved artifacts and deterministic validation, not for hidden LLM states.
"""
from collections import OrderedDict
import json
import math
import threading
import time


class ReviewSession:
    def __init__(self, reviewer, validator, identity, ttl=60, max_entries=8,
                 max_bytes=1048576, clock=time.monotonic):
        if not math.isfinite(ttl) or ttl < 0 or max_entries < 1 or max_bytes < 1:
            raise ValueError('Invalid reuse limits')
        self.reviewer = reviewer
        self.validator = validator
        self.identity = identity
        self.ttl = ttl
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self.clock = clock
        self.entries = OrderedDict()
        self.bytes = 0
        self.lock = threading.RLock()

    def clear(self):
        with self.lock:
            self.entries.clear()
            self.bytes = 0

    def _drop(self, key):
        row = self.entries.pop(key, None)
        if row is not None:
            self.bytes -= len(key) + len(row[1])

    def review(self, text, sources, kind='response', fresh=False):
        if kind not in ('prompt', 'response') or not isinstance(text, str) or not text.strip():
            raise ValueError('Invalid review input')
        if not isinstance(sources, dict) or not all(isinstance(k, str) and isinstance(v, str)
                                                  for k, v in sources.items()):
            raise ValueError('Sources must map IDs to text')
        if len(text.encode('utf-8')) > 200000 or sum(len(v.encode('utf-8')) for v in sources.values()) > 200000:
            raise ValueError('Review input exceeds size limits')
        start = time.perf_counter()
        material = json.dumps([self.identity, kind, text, sources], sort_keys=True,
                              separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        # A digest alone is not a mathematical identity proof. Python dicts use
        # byte equality after hashing, so even hash collisions cannot reuse a
        # review for different canonical input bytes. Account for these bytes.
        key = material
        with self.lock:
            now = self.clock()
            # Purge expired entries even when requests use different keys.
            for old_key, (created, payload) in list(self.entries.items()):
                if now < created or now - created >= self.ttl:
                    self._drop(old_key)
            if fresh:
                self._drop(key)
            row = self.entries.get(key)
            if row is not None:
                created, payload = row
                saved = json.loads(payload.decode('utf-8'))
                report = self.validator(text, sources, saved['review'])
                self.entries.move_to_end(key)
                report['runtime'] = {'mode': 'reused_saved_review',
                                     'fresh_model_call': False,
                                     'snapshot_age_seconds': now - created,
                                     'origin_runtime': saved['runtime'],
                                     'request_wall_seconds': time.perf_counter() - start}
                return report
            review, runtime = self.reviewer(text, sources, kind)
            report = self.validator(text, sources, review)
            payload = json.dumps({'review': review, 'runtime': runtime},
                                 ensure_ascii=False).encode('utf-8')
            entry_bytes = len(key) + len(payload)
            if self.ttl > 0 and entry_bytes <= self.max_bytes:
                while self.entries and (len(self.entries) >= self.max_entries or
                                        self.bytes + entry_bytes > self.max_bytes):
                    self._drop(next(iter(self.entries)))
                self.entries[key] = (self.clock(), payload)
                self.bytes += entry_bytes
            report['runtime'] = {'mode': 'fresh_review', 'fresh_model_call': True,
                                 'origin_runtime': runtime,
                                 'request_wall_seconds': time.perf_counter() - start}
            return report
