"""Exact bounded specializations; no universal complexity or latency guarantee.

>>> exact_range_sum(sum, range, 10)
45
>>> exact_range_sum(sum, range, 10, -1, -2)
30
>>> exact_range_sum(sum, range, 0)
0
>>> exact_range_sum(sum, range, 3, 3)
0
>>> exact_range_sum(sum, range, -4, 5, 3)
-3
>>> exact_range_sum(lambda x: list(x), range, 3)
[0, 1, 2]
>>> exact_range_sum(sum, lambda n: [2] * n, 3)
6
>>> exact_range_sum(sum, range, 3, 8, -1)
0
>>> exact_range_sum(sum, range, True)
0
>>> exact_range_sum(sum, range, 0, 3, 0)
Traceback (most recent call last):
...
ValueError: range() arg 3 must not be zero
"""
import collections
import functools
import threading
_SUM, _RANGE = sum, range

def exact_range_sum(sum_function, range_function, *args):
    if sum_function is not _SUM or range_function is not _RANGE:
        return sum_function(range_function(*args))
    r = _RANGE(*args)  # Preserve validation and __index__ evaluation exactly once.
    a, b, step = r.start, r.stop, r.step
    n = max(0, (b-a-1)//step+1) if step > 0 else max(0, (a-b-1)//(-step)+1)
    return n * (2*a + (n-1)*step) // 2

def immutable(value):
    return type(value) in (int, bool, str, bytes, type(None)) or (type(value) is tuple and all(immutable(x) for x in value))

def memoize_exact(maxsize=256):
    """Bounded exact-key reuse for explicitly selected, statically checked functions."""
    if type(maxsize) is not int or not 1 <= maxsize <= 4096:
        raise ValueError('cache capacity must be 1..4096')
    def decorate(fn):
        cache=collections.OrderedDict();lock=threading.RLock();hits=misses=0
        @functools.wraps(fn)
        def call(*args, **kwargs):
            nonlocal hits,misses
            values=(args,tuple(sorted(kwargs.items())))
            if not immutable(values):return fn(*args,**kwargs)
            # Type-tag scalar keys: bool/int equality must not merge distinct inputs.
            def key(v):return (type(v).__name__,tuple(key(x) for x in v) if type(v) is tuple else v)
            identity=key(values)
            with lock:
                if identity in cache:
                    hits+=1;cache.move_to_end(identity);return cache[identity]
            result=fn(*args,**kwargs)
            if immutable(result):
                with lock:
                    misses+=1;cache[identity]=result;cache.move_to_end(identity)
                    while len(cache)>maxsize:cache.popitem(last=False)
            return result
        def info():
            with lock:return dict(hits=hits,misses=misses,size=len(cache),capacity=maxsize)
        call.pft_cache_info=info
        return call
    return decorate
