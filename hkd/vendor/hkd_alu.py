# -*- coding: utf-8 -*-
# HKD OBFUSCATE v4 - portable source payload, no marshal/code-object dependency.
# Protection is import-time only; protected functions have no per-call wrapper.
def _hkd_v4_bootstrap(_g):
    import binascii as _hb
    import hashlib as _hh
    import struct as _hs
    import zlib as _hz

    _b = (
        _hb.unhexlify('45d281d0e2b4f3d635dc0c13d1f0865106dacbdbda9e735fe768013f4017ec077ce826a10d28580ac79003605ae885d7055acf6e60ed992a581d7e5d635730796704995d3836b1ffcca77f1314e8727b7d3b2299aff4c0ec0e07cae72f67e4d48ffaa70ec3ccb0aa58f377276e75a89bced5eff3e4e6b6d1301c7d291bbb321c'),
        _hb.unhexlify('cbef1a27c9fd86cf0836103f7f2657fc78d3a36e82679913620cd70764a553c9c0b07af8449e0fcf605c2e7c99943448d93ad09dda2ec88eed4b841b0377de2880b84f5900898e36567d27a2a4ebb60ee040b48d83d314df0fcd3d803a25997e5309296feb31841f388868c367c0624544a634473232c139e439757b248cf966'),
        _hb.unhexlify('64273d553e324af8a0dda65464742aa5f1324a3299879eb44f93ef60704cf3fafa3c8b588d94735be2747d211bd14411f064f377585c5b5cfe89bd20bc22ae0508462ff211cb5d12c86a81b592ea29fd06c4b7e6e28b4967ef4ce19d0e5c49f9b81dc46f552b99f0293712ebd64e19c8def16ca77e52bc4017dd1bc8599fd497'),
        _hb.unhexlify('1aa7804e107ff26231c66ad9089270318f5fda7ba2f4faceecda2dba6054bd100899ba199f8c30690f4f6c171252c51f9197cb451d06cb1526107a74e962e21c94942626f5ba17e4bedd246c9f99023397687339f7a78440d1923e16da0f0b3fd2601ffc3b0237075bda76c311ca1e50ef0159298342568db79307ae268979f4'),
        _hb.unhexlify('aa726d65728adfb76732356944fb8e3146898c1f0acce52e4d3cb5606587f4f293987bb94953ba24de998799b54b90ba469fafe6975414d5f4eee3c02203fb269bd008bb6c16f87e4e0b82b26ca942468e790ebbcba9530ba6d2dcbd5928f6fa0ff420eb2d02da900109038e9429417867d6e4ea3e574e7ea58ebcf72b796266'),
        _hb.unhexlify('b754246ac733a5eb2411dea9e7ee5ff2fc1a85ce971914ca7ee0610121f09f6ddb72d778bdabc178d6bd0deef632e033301902f666495ebd'),
        _hb.unhexlify('b0e0fe6b2d524523161181910cef06e2d3479861c3c2ab80206685055e1ee5f1f5ef596df9a9a3be7b58348c4b0cbb1d19cd98c1888d524ac8f7aa6b56e48b8beacc150606f74e441319364616005d5803e3080341b8822ee6d8f97154a1ac6d48a1ce8cca8840a2ef330bd0b5a9ff6039e3b4e84d64048b134d634e45c8c769'),
        _hb.unhexlify('85de17a12eb6cd12f76dabcffb407b3d51e293859ca00aeb3dc2ce467d1d7488140d8eded244af129db7b408232a6e371d5713166f1163175d477bc8430e9c65747d648dccae9922d5d855f092a5f0e9d18405a6678d6faf8034ec921e21b0b655b435c2ab0782f4cc5c0290e0e5e8ec0008760060164ab06a834bdaef235de9'),
        _hb.unhexlify('8b35650d1b92f3abcbce632511056751eeff7f10d181487200ec43a5887f247ff10d1b493d15972f52279845a73e3ad7150b24b35f53933e1b5c62feaf3465698dd6287f6c72303f0abdc5e143b9abc1040a5ffe9c8c8b257ce86aa54e8356f8ad525554162b7f3052a9dff4729f46108512dc38ff7dbf6c30b8d9dd441ede29'),
        _hb.unhexlify('4d452408b118a7840667c660c5fb7fc02ed72f65acf967584a8911af727cbdd4226dfa4652aed646417e9f213a6093e02d88af251235db400e9a53051f0a8856e50b88fa727f9ef2a86ea084f0b6989241d03dd4a28ef1b9076ceb3b4c21083b842c9f0749e8a1c695e1a5cade4b7019f0c7940253b43b22c4f16bebd9b8a0b1'),
        _hb.unhexlify('9f5c046afd2d5f59c8ed6e8fa524bdbc9f684bcf9dc50d7b5aa028a4804355df25878f9786003724b067302ed84a58678b7616d2224ae9de169d2812cf55759817156fb04e238216b3e803e4a071231d26f7b5e91b702dd62f13c177ed933a52bf5d6b6e1f31b39e2be833153c92ce29498bd0ac012a217f41bed8a9b4cac1ea'),
        _hb.unhexlify('8b515be5db140fb82c10f75ce1b2b06961696d20febbbf1e265ebfaace4ed7b1e8737c571f9db89f96df2fe72f51c29bdda800e29e3f073e1097288399d4c36c43b1ea376857e260606af6e13096b9fa6e787c162e40eed74ae379ae1e0bc38e3c3ea201e2d1ed72ff366c0627dfcefbc30fab9904d02d55d3b63a59544a4667'),
        _hb.unhexlify('760ea37f3c7366eec984b952af973e3a548b5dce33fb8b1cbcc8c292b13d844d8d012c3e3a5f878c862b7e080c2c19ce7161fa6b08491806efa1ac58858c6b0a2f27fe1e7e38077cb982b3de16476b0855a74284a8240177337bc6e4a4ad7ffeae02b037da9deb10d7c3ce34d1f27fc059cf662196bb9f2a0d1d7df5a1767769'),
        _hb.unhexlify('9bdc3e851986a1f22902d012addbd96bdd2e7677482eaf84f2834c08c3c4c7735a894e8ad9657a4b67e6c7c4fa85ca65533d6fa57b6f22b9f95663250f6e5c508c60b3ae3f6518bae3103316df8c4a3f3e221103b56c5e5227a2ef7e73e2b0991bd20dc4c0030dd1a51782424e54a8dc7c176577a02a7b4ed6a07748b4f639ed'),
    )
    _inv = (4, 13, 11, 12, 1, 3, 7, 8, 10, 2, 9, 0, 6, 5)
    _leaves = (
        _hb.unhexlify('a38c44f08843c00e6e5f66f71bbc6a73e36887658f7b349188b6e85b8f6e03c3'),
        _hb.unhexlify('ab1d25c88a059f59087a25ef6d9fa4551c34b4fe17efcc9fc6aaf1ff6290157f'),
        _hb.unhexlify('b841b239d965fb0c4a1688f0fea0da541f7455ca31cd3a31481e63d472718da8'),
        _hb.unhexlify('c46e03fc9ba3c007e41e8115a151e9c49e08d631e03c8ef659e41895fb063e08'),
        _hb.unhexlify('835c0e4fc326e37f99d773cf0399a4633d9cd3e398032b84d9059ab9d54efd3f'),
        _hb.unhexlify('556d196e9d64aa7c27f52a71e9d4afe60a12135ccf7d176614a632c66b6a7125'),
        _hb.unhexlify('fb61c75c48a708f6d890a8944f58aef8cc0ff1fd71543ed5c9ff7a162ad96ff5'),
        _hb.unhexlify('036e2501b0751d05977559e27d56e23c73cda6cccaf234c458b6b350f53de29a'),
        _hb.unhexlify('e6ef91655606d8c0d7676f643846f16519fc301381697ed38232f849cff0f265'),
        _hb.unhexlify('ee906260dac4cecb40f4fe2138a01d464c720e55ea15403b6c1199adcd46bce2'),
        _hb.unhexlify('4b73fffbb97082a6d6aa8d0928816d4612da89505546e6235954ff93ba685162'),
        _hb.unhexlify('35d8740e21c87aea7c89b0dfde92dc3bc2471195de078a6931352fdf8bcc6d62'),
        _hb.unhexlify('c3a7bd4eba5ef47082021e25017349192978516055bab0471509a6c4eab585fc'),
        _hb.unhexlify('338816e9e4df146dce9a9a6dfdf3de6a8b0b10e1a3d3127c6919ece8b19febb4'),
    )
    _root = _hb.unhexlify('eb736a6003fea8b2468b3948263383d66b41d70bc760e0bc20829ac04a7fdf26')
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
