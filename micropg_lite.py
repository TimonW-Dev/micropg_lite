#############################################################################
# The MIT License (MIT)
#
# Copyright (c) 2014-2019, 2021-2024 Hajime Nakagami (micropg)
# Copyright (c) 2023-2024 TimonW-Dev, BetaFloof (micropg_lite based on micropg)
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

import ssl
import hashlib
import socket
import binascii
import random

# -----------------------------------------------------------------------------

def hmac_sha256_digest(key, msg):
    pad_key = key + b'\x00' * (64 - len(key) % 64)
    return hashlib.sha256(bytes(0x5c ^ b for b in pad_key) + hashlib.sha256(bytes(0x36 ^ b for b in pad_key) + msg).digest()).digest()

def _bytes_to_bint(b):
    return int.from_bytes(b, 'big')

def _bint_to_bytes(val):
    return val.to_bytes(4, 'big')

class Cursor:
    def __init__(self, connection):
        self.connection = connection
        self.description = []
        self._rows = []
        self._rowcount = self.arraysize = 0

    def _check_connection(self):
        if not self.connection or not self.connection.is_connect():
            raise Exception("08003:Lost connection")

    def execute(self, query, args=()):
        self._check_connection()
        self.description, self._rows = [], []
        if args:
            query = query.replace('%', '%%').replace('%%s', '%s') % tuple(self.connection.escape_parameter(arg).replace('%', '%%') for arg in args)
            query = query.replace('%%', '%')
        self.connection.execute(query, self)

    def executemany(self, query, seq_of_params):
        self._rowcount = sum(self.execute(query, params)._rowcount for params in seq_of_params)

    def fetchall(self):
        rows = self._rows
        self._rows = []
        return rows

    def close(self):
        self.connection = None

class Connection:
    def __init__(self, user, password, database, host, port, timeout, use_ssl):
        self.user = user
        self.password = password
        self.database = database
        self.host = host
        self.port = port
        self.timeout = timeout
        self.use_ssl = use_ssl
        self.encoding = 'UTF8'
        self.autocommit = False
        self.server_version = ''
        self._ready_for_query = b'I'
        self._open()

    def __enter__(self):
        return self

    def __exit__(self, exc, value, traceback):
        self.close()

    def _send_message(self, message, data):
        self._write(b''.join([message, _bint_to_bytes(len(data) + 4), data, b'H\x00\x00\x00\x04']))

    def _process_messages(self, obj):
        while True:
            try:
                code = ord(self._read(1))
            except:
                raise Exception(u"08003:Lost connection")
            ln = _bytes_to_bint(self._read(4)) - 4
            data = self._read(ln)
            if code == 90:
                self._ready_for_query = data
                break
                
            elif code == 82:
                auth_method = _bytes_to_bint(data[:4])
                if auth_method == 0:
                    pass  # trust
                elif auth_method == 10:  # SASL
                    assert b'SCRAM-SHA-256\x00\x00' in data
                    printable = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/'
                    client_nonce = ''.join(printable[random.getrandbits(6)] for _ in range(24))
                    client_first = f'n,,n=,r={client_nonce}'.encode('utf-8')
                    scram_msg = b'SCRAM-SHA-256\x00' + _bint_to_bytes(len(client_first)) + client_first
                    self._write(b'p' + _bint_to_bytes(len(scram_msg) + 4) + scram_msg)

                    assert ord(self._read(1)) == 82
                    data = self._read(_bytes_to_bint(self._read(4)) - 4)
                    assert _bytes_to_bint(data[:4]) == 11  # SCRAM first

                    server = dict(kv.split('=', 1) for kv in data[4:].decode('utf-8').split(','))
                    assert server['r'].startswith(client_nonce)

                    # Inlined pbkdf2_hmac_sha256 logic
                    password_bytes = self.password.encode('utf-8')
                    salt = binascii.a2b_base64(server['s'])
                    iterations = int(server['i'])

                    u1 = hmac_sha256_digest(password_bytes, salt + b'\x00\x00\x00\x01')
                    ui = int.from_bytes(u1, 'big')
                    for _ in range(iterations - 1):
                        u1 = hmac_sha256_digest(password_bytes, u1)
                        ui ^= int.from_bytes(u1, 'big')
                    salt_pass = ui.to_bytes(32, 'big')

                    client_key = hmac_sha256_digest(salt_pass, b"Client Key")

                    auth_msg = f"n=,r={client_nonce},r={server['r']},s={server['s']},i={server['i']},c=biws,r={server['r']}"
                    proof = binascii.b2a_base64(bytes(x ^ y for x, y in zip(client_key, hmac_sha256_digest(hashlib.sha256(client_key).digest(), auth_msg.encode('utf-8'))))).rstrip(b'\n')
                    client_final = f"c=biws,r={server['r']},p={proof.decode('utf-8')}".encode('utf-8')
                    self._write(b'p' + _bint_to_bytes(len(client_final) + 4) + client_final)

                    assert ord(self._read(1)) == 82
                    data = self._read(_bytes_to_bint(self._read(4)) - 4)
                    assert _bytes_to_bint(data[:4]) == 12  # SCRAM final

                    assert ord(self._read(1)) == 82
                    data = self._read(_bytes_to_bint(self._read(4)) - 4)
                    assert _bytes_to_bint(data[:4]) == 0
                    
                else:
                    raise Exception(u"08003:Lost connection")
            
            elif code == 83:
                k, v, _ = data.split(b'\x00')
                if k == b'server_encoding':
                    self.encoding = v.decode('ascii')
                elif k == b'server_version':
                    ver = v.decode('ascii').split('(')[0].split('.')
                    self.server_version = int(ver[0]) * 10000
                    try:
                        self.server_version += int(ver[1]) * 100
                        if len(ver) > 2:
                            self.server_version += int(ver[2])
                    except (IndexError, ValueError):
                        pass
                elif k == b'TimeZone':
                    self.tz_name = v.decode('ascii')
            elif code == 67 and obj:
                cmd = data[:-1].decode('ascii')
                if cmd == 'SHOW':
                    obj._rowcount = 1
                else:
                    parts = cmd.split()
                    if parts and parts[-1].isdigit():
                        obj._rowcount = int(parts[-1])
            elif code == 84 and obj:
                count = _bytes_to_bint(data[:2])
                obj.description = [None] * count
                n = 2
                for i in range(count):
                    name_end = data.index(b'\x00', n)
                    name = data[n:name_end]
                    n = name_end + 1
                    try: name = name.decode(self.encoding)
                    except UnicodeDecodeError: pass
                    type_code = _bytes_to_bint(data[n+6:n+10])
                    if type_code == 1043:
                        size, precision, scale = _bytes_to_bint(data[n+12:n+16]) - 4, -1, -1
                    elif type_code == 1700:
                        size = _bytes_to_bint(data[n+10:n+12])
                        precision = _bytes_to_bint(data[n+12:n+14])
                        scale = precision - _bytes_to_bint(data[n+14:n+16])
                    else:
                        size, precision, scale = _bytes_to_bint(data[n+10:n+12]), -1, -1
                    obj.description[i] = (name, type_code, None, size, precision, scale, None)
                    n += 18
            elif code == 68 and obj:
                n, row = 2, []
                while n < len(data):
                    if data[n:n+4] == b'\xff\xff\xff\xff':
                        row.append(None)
                        n += 4
                    else:
                        ln = _bytes_to_bint(data[n:n+4])
                        col_data = data[n+4:n+4+ln]
                        col_oid = obj.description[len(row)][1]
                        col_encoding = self.encoding

                        # Inline _decode_column logic
                        if col_data is None:
                            decoded_data = None
                        else:
                            decoded_data = col_data.decode(col_encoding)
                            if col_oid == 16:
                                decoded_data = (decoded_data == 't')
                            elif col_oid in (21, 23, 20, 26):
                                decoded_data = int(decoded_data)
                            elif col_oid in (700, 701):
                                decoded_data = float(decoded_data)

                        row.append(decoded_data)
                        n += ln + 4
                obj._rows.append(tuple(row))
            elif code == 69:
                print(code)
                raise Exception("08003:Lost connection")
            elif code == 100:
                obj.write(data)
            elif code == 71:
                print(code)
                while True:
                    buf = obj.read(8192)
                    if not buf:
                        break
                    self._write(b'd' + _bint_to_bytes(len(buf) + 4) + buf)
                self._write(b'c\x00\x00\x00\x04S\x00\x00\x00\x04')

    def _read(self, ln):
        if not self.sock:
            raise Exception("08003:Lost connection")
        r = bytearray(ln)
        pos = 0
        while pos < ln:
            if hasattr(self.sock, "read"):
                chunk = self.sock.read(ln - pos)
            else:
                chunk = self.sock.recv(ln - pos)
            if not chunk:
                raise Exception("08003:Lost connection")
            r[pos:pos+len(chunk)] = chunk
            pos += len(chunk)
        return bytes(r)

    def _write(self, b):
        if not self.sock:
            raise Exception("08003:Lost connection")
        pos = 0
        while pos < len(b):
            if hasattr(self.sock, "write"):
                sent = self.sock.write(b[pos:])
            else:
                sent = self.sock.send(b[pos:])
            pos += sent

    def _open(self):
        self.sock = socket.socket()
        self.sock.connect(socket.getaddrinfo(self.host, self.port)[0][-1])
        if self.timeout is not None:
            self.sock.settimeout(float(self.timeout))
        if self.use_ssl:
            self._write(_bint_to_bytes(8) + _bint_to_bytes(80877103))
            if self._read(1) == b'S':
                self.sock = ssl.wrap_socket(self.sock)
            else:
                raise Exception("08003:Lost connection")
        v = b'\x00\x03\x00\x00user\x00' + self.user.encode('ascii') + b'\x00'
        if self.database:
            v += b'database\x00' + self.database.encode('ascii') + b'\x00'
        v += b'\x00'
        self._write(_bint_to_bytes(len(v) + 4) + v)
        self._process_messages(None)

    def escape_parameter(self, v):
        if v is None:
            return 'NULL'
        t = type(v)
        if t == str:
            return "'" + v.replace("'", "''") + "'"
        if t in (bytearray, bytes):
            return "'" + ''.join(['\\%03o' % c for c in v]) + "'::bytea"
        if t == bool:
            return 'TRUE' if v else 'FALSE'
        if t in (list, tuple):
            return 'ARRAY[' + ','.join([self.escape_parameter(e) for e in v]) + ']'
        return "'" + str(v) + "'"

    def is_connect(self):
        return bool(self.sock)

    def cursor(self):
        return Cursor(self)

    def execute(self, query, obj=None):
        if self._ready_for_query != b'T':
            self.begin()
        
        self._send_message(b'Q', query.encode(self.encoding) + b'\x00')
        self._process_messages(obj)
        
        if self.autocommit:
            self.commit()

    def set_autocommit(self, autocommit):
        self.autocommit = autocommit

    def _begin(self):
        self._send_message(b'Q', b"BEGIN\x00")
        self._process_messages(None)

    def begin(self):
        if self._ready_for_query == b'E':
            self._rollback()
        self._begin()

    def commit(self):
        if self.sock:
            self._send_message(b'Q', b"COMMIT\x00")
            self._process_messages(None)
            self._begin()

    def _rollback(self):
        if self.sock:
            self._send_message(b'Q', b"ROLLBACK\x00")
            self._process_messages(None)

    def rollback(self):
        self._rollback()
        self.begin()

    def close(self):
        if self.sock:
            # send Terminate
            self._write(b'X\x00\x00\x00\x04')
            self.sock.close()
            self.sock = None

def connect(host, user, password='', database=None, port=None, timeout=None, use_ssl=False):
    return Connection(user, password, database, host, port if port else 5432, timeout, use_ssl)

def create_database(database, host, user, password='', port=None, use_ssl=False):
    with connect(host, user, password, None, port, None, use_ssl) as conn:
        conn._rollback()
        conn._send_message(b'Q', 'CREATE DATABASE {}'.format(database).encode('utf-8') + b'\x00')
        conn._process_messages(None)

def drop_database(database, host, user, password='', port=None, use_ssl=False):
    with connect(host, user, password, None, port, None, use_ssl) as conn:
        conn._rollback()
        conn._send_message(b'Q', 'DROP DATABASE {}'.format(database).encode('utf-8') + b'\x00')
        conn._process_messages(None)