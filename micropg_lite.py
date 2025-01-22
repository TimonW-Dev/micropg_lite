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

### Version 3.1.0

import ssl, hashlib, socket, binascii, random

# -----------------------------------------------------------------------------

def raiseExceptionLostConnection():
    raise Exception("08003:Lost connection")

def hmac_sha256_digest(key, msg):
    pad_key = key + b'\x00' * (64 - len(key) % 64)
    return hashlib.sha256(bytes(0x5c ^ b for b in pad_key) + hashlib.sha256(bytes(0x36 ^ b for b in pad_key) + msg).digest()).digest()

class Cursor:
    def __init__(self, connection):
        self.connection = connection
        
    def execute(self, q, a=()):
        if not self.connection or not bool(self.connection.sock): raiseExceptionLostConnection()
        self._rows = []
        if a: q = q.replace('%', '%%').replace('%%s', '%s') % tuple(('NULL' if i is None else "'" + i.replace("'", "''") + "'" if isinstance(i, str) else "'" + ''.join(['\\%03o' % c for c in i]) + "'" for i in a))
        self.connection.execute(q, self)

    def fetchall(self):
        rows = self._rows
        self._rows = []
        return rows

    def close(self):
        self.connection = None

class connect:
    def __init__(self, host, user, password, database, port=5432, use_ssl=False):
        self.user = user
        self.password = password
        self.database = database
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.encoding = 'UTF8'
        self.autocommit = False
        self._ready_for_query = b'I'
        
        # Inlined _open() function
        self.sock = socket.socket()
        self.sock.connect(socket.getaddrinfo(self.host, self.port)[0][-1])
        if self.use_ssl:
            self._write((8).to_bytes(4, 'big') + (80877103).to_bytes(4, 'big'))
            if self._read(1) == b'S': self.sock = ssl.wrap_socket(self.sock)
            else: raiseExceptionLostConnection()
        v = b'\x00\x03\x00\x00user\x00' + self.user.encode('ascii') + b'\x00'
        if self.database: v += b'database\x00' + self.database.encode('ascii') + b'\x00'
        v += b'\x00'
        self._write((len(v) + 4).to_bytes(4, 'big') + v)
        self._process_messages(None)

    def _send_message(self, message, data):
        self._write(b''.join([message, (len(data) + 4).to_bytes(4, 'big'), data, b'H\x00\x00\x00\x04']))

    def _process_messages(self, obj):
        while True:
            try: code = ord(self._read(1))
            except: raiseExceptionLostConnection()
            data = self._read(int.from_bytes(self._read(4), 'big') - 4)
            if code == 90: self._ready_for_query = data; break
            elif code == 82:
                nonce = str(random.getrandbits(32))
                first = f'n,,n=,r={nonce}'.encode('utf-8')
                msg = b'SCRAM-SHA-256\x00' + (len(first)).to_bytes(4, 'big') + first
                self._write(b'p' + (len(msg) + 4).to_bytes(4, 'big') + msg)
                assert ord(self._read(1)) == 82
                data = self._read(int.from_bytes(self._read(4), 'big') - 4)
                assert int.from_bytes(data[:4], 'big') == 11
                server = dict(kv.split('=', 1) for kv in data[4:].decode('utf-8').split(','))
                assert server['r'].startswith(nonce)
                pw_bytes = self.password.encode('utf-8')
                iters = int(server['i'])
                u1 = hmac_sha256_digest(pw_bytes, binascii.a2b_base64(server['s']) + b'\x00\x00\x00\x01')
                ui = int.from_bytes(u1, 'big')
                for _ in range(iters - 1):
                    u1 = hmac_sha256_digest(pw_bytes, u1)
                    ui ^= int.from_bytes(u1, 'big') 
                client_key = hmac_sha256_digest(ui.to_bytes(32, 'big'), b"Client Key")
                auth_msg = f"n=,r={nonce},r={server['r']},s={server['s']},i={server['i']},c=biws,r={server['r']}"
                proof = binascii.b2a_base64(bytes(x ^ y for x, y in zip(client_key, hmac_sha256_digest(hashlib.sha256(client_key).digest(), auth_msg.encode('utf-8'))))).rstrip(b'\n')
                final = f"c=biws,r={server['r']},p={proof.decode('utf-8')}".encode('utf-8')
                self._write(b'p' + (len(final) + 4).to_bytes(4, 'big') + final)
                for _ in range(3):
                    assert ord(self._read(1)) == 82
                    data = self._read(int.from_bytes(self._read(4), 'big') - 4)
                    if int.from_bytes(data[:4], 'big') == 0: break
            elif code == 67 and obj:
                cmd = data[:-1].decode('ascii')
                if cmd == 'SHOW':
                    obj._rowcount = 1
                else:
                    parts = cmd.split()
                    if parts and parts[-1].isdigit(): obj._rowcount = int(parts[-1])
            elif code == 84 and obj:
                count = int.from_bytes(data[:2], 'big')
                obj.description = [None] * count
                n = 2
                for i in range(count):
                    name_end = data.index(b'\x00', n)
                    name = data[n:name_end]
                    n = name_end + 1
                    try: name = name.decode(self.encoding)
                    except: pass
                    type_code = int.from_bytes(data[n+6:n+10], 'big')
                    if type_code == 1043: size, precision, scale = int.from_bytes(data[n+12:n+16], 'big') - 4, -1, -1
                    elif type_code == 1700:
                        size = int.from_bytes(data[n+10:n+12], 'big')
                        precision = int.from_bytes(data[n+12:n+14], 'big')
                        scale = precision - int.from_bytes(data[n+14:n+16], 'big')
                    else: size, precision, scale = int.from_bytes(data[n+10:n+12], 'big'), -1, -1
                    obj.description[i] = (name, type_code, None, size, precision, scale, None)
                    n += 18
            elif code == 68 and obj:
                n, row = 2, []
                while n < len(data):
                    if data[n:n+4] == b'\xff\xff\xff\xff': row.append(None); n += 4
                    else:
                        ln = int.from_bytes(data[n:n+4], 'big')
                        col_data = data[n+4:n+4+ln]
                        col_oid = obj.description[len(row)][1]
                        col_encoding = self.encoding
                        decoded_data = col_data.decode(col_encoding) if col_data else None
                        if col_oid == 16: decoded_data = (decoded_data == 't')
                        elif col_oid in (21, 23, 20, 26): decoded_data = int(decoded_data)
                        elif col_oid in (700, 701): decoded_data = float(decoded_data)
                        row.append(decoded_data)
                        n += ln + 4
                obj._rows.append(tuple(row))
            elif code == 69: raiseExceptionLostConnection()
            elif code == 100: obj.write(data)
            elif code == 71:
                while True:
                    buf = obj.read(8192)
                    if not buf: break
                    self._write(b'd' + (len(buf) + 4).to_bytes(4, 'big') + buf)
                self._write(b'c\x00\x00\x00\x04S\x00\x00\x00\x04')
                
    def _read(self, ln):
        if not self.sock: raiseExceptionLostConnection()
        r = bytearray(ln)
        pos = 0
        while pos < ln:
            chunk = self.sock.read(ln - pos) if hasattr(self.sock, "read") else self.sock.recv(ln - pos)
            if not chunk: raiseExceptionLostConnection()
            r[pos:pos+len(chunk)] = chunk
            pos += len(chunk)
        return bytes(r)

    def _write(self, b):
        if not self.sock:
            raiseExceptionLostConnection()
        pos = 0
        while pos < len(b):
            pos += self.sock.write(b[pos:]) if hasattr(self.sock, "write") else self.sock.send(b[pos:])

    def cursor(self):
        return Cursor(self)

    def execute(self, query, obj=None):
        if self._ready_for_query != b'T':
            self.begin()
        self._send_message(b'Q', query.encode(self.encoding) + b'\x00')
        self._process_messages(obj)
        if self.autocommit:
            self.commit()

    def begin(self):
        if self._ready_for_query == b'E':
            self._rollback()
        self._send_message(b'Q', b"BEGIN\x00")
        self._process_messages(None)

    def commit(self):
        if self.sock:
            self._send_message(b'Q', b"COMMIT\x00")
            self._process_messages(None)
            self.begin()

    def _rollback(self):
        if self.sock:
            self._send_message(b'Q', b"ROLLBACK\x00")
            self._process_messages(None)

    def rollback(self):
        self._rollback()
        self.begin()

    def close(self):
        if self.sock:
            self._write(b'X\x00\x00\x00\x04')
            self.sock.close()
            self.sock = None

def create_database(host, user, password, database, port=5432, use_ssl=False):
    conn = connect(host, user, password, None, port, use_ssl)
    conn._send_message(b'Q', 'CREATE DATABASE {}'.format(database).encode('utf-8') + b'\x00')
    conn.close()

def drop_database(host, user, password, database, port=5432, use_ssl=False):
    conn = connect(host, user, password, None, port, use_ssl)
    conn._send_message(b'Q', 'DROP DATABASE {}'.format(database).encode('utf-8') + b'\x00')
    conn.close()