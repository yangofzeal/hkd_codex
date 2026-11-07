# -*- coding: utf-8 -*-
# HKD OBFUSCATE v4 - portable source payload, no marshal/code-object dependency.
# Protection is import-time only; protected functions have no per-call wrapper.
def _hkd_v4_bootstrap(_g):
    import binascii as _hb
    import hashlib as _hh
    import struct as _hs
    import zlib as _hz

    _b = (
        _hb.unhexlify('aa72556b748ad8c77b331561049a86371da5606d7727c37a8dfb7354c350bb4344fa190150b642bae1fd9c47e047e0b68ab6090ab2f6b1be067f32dc7e21e014e65d7ab931829e71e9ef5c7bb0376b3e924876ab2adb104d4ce4c866e259ec6ac0f21b454cf135b332810f67f6facfb99ea87007796242780a77793a8a4488c9'),
        _hb.unhexlify('fd894b458e882c5a31320f792ef9baffa3ed23a6ad4ba03fd84c117c746063f33a439589de9b001a6520660c5051bac95650a4cb462ae6a405a15ef723c19b92a6de6dde1cc54a77aa95b5030953f223c708010974e75701776087f1f50bb361ea405bd7915a17e46f'),
        _hb.unhexlify('8c855da44310bdb865e1cd52240488c04e5e3e62cff122b0149a3a79a7c319ca3edb4107ea3fb8eea352ad30642599aa960e905d95f0d3528c063a03faf7b9bd05ae8b1643fecc58c3db51772c88ca82cf0772b0a822acc48a8bda8b7fd7e30332c496c2bcd629a7bfb9525fe0eeb0bb69ba1b843df3515aae6adb00320beae3'),
        _hb.unhexlify('bc4b7bb16b995f3c54bcf87e73060fcd9d15edc33b4ac2bd25fbaf9e3a1c61fa5434cd1169025cda16ffd53a89dda53f58c2b2d3ddc71300947af426eb2d5201fce189bb939f69ea76adbf8dad979c5335cca6df762a46d198121ba05a16a959fc9ca202d1e5d06f2b236e4a299d4899194e151af0658e55b90028dd389bfe70'),
        _hb.unhexlify('f2fe6a37f99187b34650d74d4a95c71ef28373b80e9d08b889d191ec53231332a1a4bacead1016fef2104342d2add2d439acec6e58a90b7fab36b396cb4ce0581b3973111346c373c0c765241757bbf46982216c57ee9ddebb84218fa50ccff1f99279b08c149c2a9242c2513ccd03be916bee2ec46fc93b5554346f68c34391'),
        _hb.unhexlify('7f5fa7abc025ce8fefe3e059e8c9aae934e910ada76d5eba958c543c4549872603b9be57e02ae64f7ba9e5c62d07fa1f01d5e56d55f9806a900a06df9f138a23a30972fac37f926b35e2ec8ff259631837935b2739445c8bd2649592b9632fa15233195056ab5eea2fb0431aa9e78e9f6f1c3e4b9ca3ea4d2eedb69cb9e66ea1'),
        _hb.unhexlify('4a7d56fd10a242be14beb1cbef003dd74ed7a84da56a7a82f4c2b206314b0862cce55bf92434689f488de617fbe2771a5c245533bcf98b7b194a8704a524d47446e3b9db0c1b6faed02df2884e231ce54780eb7f013ad47d9ed09e3a807bbce14629abd602df82b3e3ca1ba81d4a7408b5f156940e969007daa9a484652264bc'),
        _hb.unhexlify('9669f332a0ba3fa727276b64a8c6e444039fb9242aac7f0f4ec1ff0806e0111f9bf53e6184c3f14de99742d1c462c28331d444be325d368310f32a29504cbc8b159c6e0e3db7ef1ae081de3d249f7edc7b027e8c6444e94fff7244c5efea718b289eda7d01a2a2b4aa6534e9fb79e79e39e6248544323bd236bd81bf13aaaace'),
    )
    _inv = (0, 2, 5, 3, 4, 7, 6, 1)
    _leaves = (
        _hb.unhexlify('028e1f2d0b889e12c6f4c9906ab34cbd953f6a11c647718c57b33dafb0f20643'),
        _hb.unhexlify('15a85a3852c5684e59f470f97d02d8130b164ddd9f5f1ec12f57219f0dde3a1b'),
        _hb.unhexlify('bd8674e5cec9d7ef2f34161ffad43a3179c1353be2154812774f5ec2850e93dd'),
        _hb.unhexlify('a2684234bfdf23a57b969787b1060a3eed25b21d71d334cd200f385293e14191'),
        _hb.unhexlify('c6ab191b46669b082da1a80843552b058597b8fe0ab27d298e925aa6062767dc'),
        _hb.unhexlify('988c5a96e52ca1afe5a64b5c7a000ad8510ebe47ab10a644c6fcbfb2b87eb24f'),
        _hb.unhexlify('70739f18d8169fb4b5a570d9c52ce69254a4ca6b7f0d534e0f1e6e245b202615'),
        _hb.unhexlify('d0dd3d19610a9e3f41861618f630e7f56fb99065c95d57b2bb2491705185cb91'),
    )
    _root = _hb.unhexlify('06565e58640f0a6a8ee1d07023077baee848ac83f8e75a156edb8de656e67c1e')
    _share1 = _hb.unhexlify('55eda5f163d89abc0fa9ee2f50360fb8a1798cbdee89b7724aa601d666ef165c')
    _share2 = _hb.unhexlify('9f79c9c5af812421529d38fa0edc11dc26853438e917cd18eb1ba098b56c4e3b')

    def _u32(_n):
        return _hs.pack('>I', _n)


    def _xor(_a, _c):
        _o = bytearray(len(_a))
        _i = 0
        while _i < len(_a):
            _o[_i] = _a[_i] ^ _c[_i]
            _i += 1
        return bytes(_o)

    def _ks(_key, _index, _length):
        _o = bytearray()
        _counter = 0
        _seed = _key + _u32(_index)
        while len(_o) < _length:
            _o.extend(_hh.sha256(_seed + _u32(_counter)).digest())
            _counter += 1
        return bytes(_o[:_length])

    def _merkle(_values):
        if not _values:
            return _hh.sha256(b'').digest()
        _level = list(_values)
        while len(_level) > 1:
            if len(_level) & 1:
                _level.append(_level[-1])
            _next = []
            _i = 0
            while _i < len(_level):
                _next.append(_hh.sha256(_level[_i] + _level[_i + 1]).digest())
                _i += 2
            _level = _next
        return _level[0]

    _key = _xor(_share1, _share2)
    _parts = []
    _verify = []
    _i = 0
    while _i < len(_inv):
        _masked = _b[_inv[_i]]
        _raw = _xor(_masked, _ks(_key, _i, len(_masked)))
        _parts.append(_raw)
        _verify.append(_hh.sha256(_u32(_i) + _raw).digest())
        _i += 1

    if tuple(_verify) != _leaves or _merkle(_verify) != _root:
        raise ImportError('HKD protected payload integrity verification failed')

    try:
        _source = _hz.decompress(b''.join(_parts)).decode('utf-8')
    except Exception as _exc:
        raise ImportError('HKD protected payload reconstruction failed: %s' % (_exc,))

    _filename = _g.get('__file__') or '<HKD-obfuscated>'
    _code = compile(_source, _filename, 'exec', 0, True, 0)

    # Discard the plaintext string before running user code.  CPython may reclaim
    # it immediately; no plaintext source is retained as a module global.
    del _source

    # Return the compiled payload.  Keep exec out of this function: older
    # CPython parsers reject an exec statement in a function that also contains
    # nested functions/free variables.  Execution happens at module scope below.
    return _code

_hkd_v4_code = _hkd_v4_bootstrap(globals())
del _hkd_v4_bootstrap

# Exact module semantics: execute in the real module globals.
exec(_hkd_v4_code, globals(), globals())
del _hkd_v4_code
