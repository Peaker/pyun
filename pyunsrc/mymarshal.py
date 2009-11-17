"""A cross-Python-version marshaller
"""

import struct
from cStringIO import StringIO

class Error(Exception): pass

def dump(x, fo):
    if isinstance(x, type(None)):
        fo.write('N')
    elif isinstance(x, (tuple, list)):
        if isinstance(x, tuple):
            fmt = 't'
        else:
            fmt = 'l'
        fo.write(fmt + struct.pack('<L', len(x)))
        for item in x:
            dump(item, fo)
    elif isinstance(x, str):
        fo.write('s' + struct.pack('<L', len(x)))
        fo.write(x)
    elif isinstance(x, dict):
        fo.write('d')
        dump(x.items(), fo)
    elif isinstance(x, (int, long)) and -(1L<<31) <= x < (1L<<31):
        fo.write('I' + struct.pack('<l', x))
    elif isinstance(x, long):
        neg = x < 0
        if neg:
            x = -x
        hex_repr = hex(x)[2:-1]
        if len(hex_repr)%2 == 1:
            hex_repr = '0' + hex_repr
        data = hex_repr.decode('hex')
        fo.write('L' + struct.pack('<B', neg) + struct.pack('<L', len(data)) + data)
    elif isinstance(x, float):
        fo.write('F' + struct.pack('<d', x))
    else:
        raise Error("Cannot marshal object", x)

def load(fo):
    fmt = fo.read(1)
    if fmt == 'N':
        return None
    elif fmt in 'tl':
        if fmt == 't':
            seqtype = tuple
        else:
            seqtype = list
        length, = struct.unpack('<L', fo.read(4))
        return seqtype([load(fo)
                        for i in xrange(length)])
    elif fmt == 's':
        length, = struct.unpack('<L', fo.read(4))
        return fo.read(length)
    elif fmt == 'd':
        return dict(load(fo))
    elif fmt == 'I':
        value, = struct.unpack('<l', fo.read(4))
        return value
    elif fmt == 'L':
        neg, = struct.unpack('<B', fo.read(1))
        length, = struct.unpack('<L', fo.read(4))
        data = fo.read(length)
        value = int(data.encode('hex'), 16)
        if neg:
            value = -value
        return value
    elif fmt == 'F':
        value, = struct.unpack('<d', fo.read(8))
        return value
    else:
        raise Error('Unknown fmt', fmt)

def dumps(x):
    s = StringIO()
    dump(x, s)
    return s.getvalue().encode('zlib')

def loads(x):
    s = StringIO(x.decode('zlib'))
    return load(s)
