#############################################################################
# The MIT License (MIT)
#
# Copyright (c) 2014-2019, 2021-2024 Hajime Nakagami (micropg)
# Copyright (c) 2023-2025 TimonW-Dev, BetaFloof, MikeRoth93 (micropg_lite based on micropg)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
##############################################################################
# PostgreSQL driver for micropython https://github.com/micropython/micropython but it's more lightweight and made for ESP8266
# It's a micropg (https://github.com/nakagami/micropg) subset.
# micropg (https://github.com/nakagami/micropg) a minipg (https://github.com/nakagami/minipg) subset.
##############################################################################

### Version 4.0.0

import socket

# ssl, hashlib, binascii and random are imported lazily where they are needed to save RAM.
# -----------------------------------------------------------------------------

def _lost():
    raise Exception("08003:Lost connection")

# HMAC-SHA256. With n > 1 it chains n rounds and XORs them (PBKDF2-HMAC-SHA256, one block),
# so the key pads are only calculated once.
def hmac_sha256_digest(key, msg, n=1):
    import hashlib
    h = hashlib.sha256
    if len(key) > 64: key = h(key).digest()
    k = int.from_bytes(key + bytes(64 - len(key)), 'big')
    r = int.from_bytes(b'\x01' * 64, 'big')
    i = (k ^ 0x36 * r).to_bytes(64, 'big')
    o = (k ^ 0x5c * r).to_bytes(64, 'big')
    u = h(o + h(i + msg).digest()).digest()
    x = int.from_bytes(u, 'big')
    for _ in range(n - 1):
        u = h(o + h(i + u).digest()).digest()
        x ^= int.from_bytes(u, 'big')
    return x.to_bytes(32, 'big')

class Cursor:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, q, a=()):
        c = self.connection
        if not (c and c.sock): _lost()
        self._rows = []
        if a:
            p = []
            for i in a:
                p.append('NULL' if i is None else "'" + i.replace("'", "''") + "'" if isinstance(i, str) else "'" + '\\%03o' * len(i) % tuple(i) + "'")
            q = q.replace('%', '%%').replace('%%s', '%s') % tuple(p)
        c.execute(q, self)

    def fetchall(self):
        rows = self._rows
        self._rows = []
        return rows

    def close(self):
        self.connection = None

class connect:
    def __init__(self, host, user, password, database, port=5432, use_ssl=False):
        self.encoding = 'utf-8'
        self.autocommit = False
        s = self.sock = socket.socket()
        s.connect(socket.getaddrinfo(host, port)[0][-1])
        if use_ssl:
            self._write(b'\x00\x00\x00\x08\x04\xd2\x16\x2f')  # SSLRequest
            if self._read(1) != b'S': _lost()
            import ssl
            self.sock = ssl.wrap_socket(s)
        v = b'\x00\x03\x00\x00user\x00' + user.encode('ascii') + b'\x00'
        if database: v += b'database\x00' + database.encode('ascii') + b'\x00'
        v += b'\x00'
        self._write((len(v) + 4).to_bytes(4, 'big') + v)
        self._p(None, password)

    # Sends a simple query (plus Flush). q is the already encoded query without the trailing NUL.
    def _q(self, q):
        self._write(b''.join((b'Q', (len(q) + 5).to_bytes(4, 'big'), q, b'\x00H\x00\x00\x00\x04')))

    # Reads and handles server messages until ReadyForQuery. o: cursor/file object, w: password (login only).
    def _p(self, o, w=None):
        while True:
            try: h = self._read(5)
            except: _lost()
            c = h[0]
            d = self._read(int.from_bytes(h[1:], 'big') - 4)
            if c == 68 and o:
                ds = o.description
                e = self.encoding
                r = [None] * len(ds)
                n = 2
                i = 0
                while n < len(d):
                    if d[n] == 255: n += 4
                    else:
                        l = int.from_bytes(d[n:n + 4], 'big')
                        n += 4
                        v = d[n:n + l]
                        v = v.decode(e) if v else None
                        t = ds[i][1]
                        if t == 16: v = (v == 't')
                        elif t in (21, 23, 20, 26): v = int(v)
                        elif t in (700, 701): v = float(v)
                        r[i] = v
                        n += l
                    i += 1
                o._rows.append(tuple(r))
            elif c == 90:
                self._s = d[0]
                break
            elif c == 82:
                t = d[3]
                assert t == 0 or 9 < t < 13
                if t == 10:
                    import random
                    nonce = str(random.getrandbits(32))
                    f = ('n,,n=,r=' + nonce).encode()
                    m = b'SCRAM-SHA-256\x00' + len(f).to_bytes(4, 'big') + f
                    self._write(b'p' + (len(m) + 4).to_bytes(4, 'big') + m)
                elif t == 11:
                    import binascii, hashlib
                    m = d[4:].decode()
                    v = {}
                    for x in m.split(','): v[x[0]] = x[2:]
                    r = v['r']
                    ck = hmac_sha256_digest(hmac_sha256_digest(w.encode(), binascii.a2b_base64(v['s']) + b'\x00\x00\x00\x01', int(v['i'])), b'Client Key')
                    sig = hmac_sha256_digest(hashlib.sha256(ck).digest(), f'n=,r={nonce},{m},c=biws,r={r}'.encode())
                    proof = binascii.b2a_base64((int.from_bytes(ck, 'big') ^ int.from_bytes(sig, 'big')).to_bytes(32, 'big')).rstrip(b'\n')
                    f = f'c=biws,r={r},p='.encode() + proof
                    self._write(b'p' + (len(f) + 4).to_bytes(4, 'big') + f)
            elif c == 67 and o:
                p = d[:-1].decode('ascii').split()
                if p and p[-1].isdigit(): o._rowcount = int(p[-1])
            elif c == 84 and o:
                k = int.from_bytes(d[:2], 'big')
                ds = o.description = [None] * k
                n = 2
                for i in range(k):
                    j = d.index(b'\x00', n)
                    name = d[n:j]
                    n = j + 1
                    try: name = name.decode(self.encoding)
                    except: pass
                    ds[i] = (name, int.from_bytes(d[n + 6:n + 10], 'big'), None, int.from_bytes(d[n + 10:n + 12], 'big'), -1, -1, None)
                    n += 18
            elif c == 69: _lost()
            elif c == 100: o.write(d)
            elif c == 71:
                b = o.read(8192)
                while b:
                    self._write(b'd' + (len(b) + 4).to_bytes(4, 'big'))
                    self._write(b)
                    b = o.read(8192)
                self._write(b'c\x00\x00\x00\x04S\x00\x00\x00\x04')

    def _read(self, n):
        s = self.sock
        if not s: _lost()
        r = b''
        while len(r) < n:
            c = s.read(n - len(r)) if hasattr(s, 'read') else s.recv(n - len(r))
            if not c: _lost()
            r = r + c if r else c
        return r

    def _write(self, b):
        s = self.sock
        if not s: _lost()
        w = s.write if hasattr(s, 'write') else s.send
        m = memoryview(b)
        p = 0
        while p < len(b): p += w(m[p:])

    def cursor(self):
        return Cursor(self)

    def execute(self, query, obj=None):
        if self._s != 84: self.begin()
        self._q(query.encode(self.encoding))
        self._p(obj)
        if self.autocommit: self.commit()

    def begin(self):
        if self._s == 69:
            self._q(b'ROLLBACK')
            self._p(None)
        self._q(b'BEGIN')
        self._p(None)

    def commit(self):
        if self.sock:
            self._q(b'COMMIT')
            self._p(None)
            self.begin()

    def rollback(self):
        if self.sock:
            self._q(b'ROLLBACK')
            self._p(None)
        self.begin()

    def close(self):
        if self.sock:
            self._write(b'X\x00\x00\x00\x04')
            self.sock.close()
            self.sock = None

def create_database(host, user, password, database, port=5432, use_ssl=False):
    c = connect(host, user, password, None, port, use_ssl)
    c._q('CREATE DATABASE {}'.format(database).encode())
    c.close()

def drop_database(host, user, password, database, port=5432, use_ssl=False):
    c = connect(host, user, password, None, port, use_ssl)
    c._q('DROP DATABASE {}'.format(database).encode())
    c.close()