#############################################################################
# The MIT License (MIT)
#
# Copyright (c) 2014-2019, 2021-2024 Hajime Nakagami
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
# PostgreSQL driver for micropython https://github.com/micropython/micropython
# micropg is a minipg (https://github.com/nakagami/minipg) subset.
# micropg_lite is a micropg (https://github.com/nakagami/micropg) subset.
##############################################################################
# -----------------------------------------------------------------------------
# http://www.postgresql.org/docs/9.6/static/protocol.html
# http://www.postgresql.org/docs/9.6/static/protocol-message-formats.html

# https://github.com/postgres/postgres/blob/master/src/include/catalog/pg_type.h
# -----------------------------------------------------------------------------

### Version 2.1.1

from hashlib import sha256
from random import getrandbits
import binascii
import socket


def hmac_sha256_digest(key, msg):
    pad_key = key + b'\x00' * (64 - (len(key) % 64))
    ik = bytes([0x36 ^ b for b in pad_key])
    ok = bytes([0x5c ^ b for b in pad_key])
    return sha256(ok + sha256(ik + msg).digest()).digest()


def pbkdf2_hmac_sha256(password_bytes, salt, iterations):
    _u1 = hmac_sha256_digest(password_bytes, salt + b'\x00\x00\x00\x01')
    _ui = int.from_bytes(_u1, 'big')
    for _ in range(iterations - 1):
        _u1 = hmac_sha256_digest(password_bytes, _u1)
        _ui ^= int.from_bytes(_u1, 'big')
    return _ui.to_bytes(32, 'big')


def _decode_column(data, oid, encoding):
    if data is None:
        return data
    data = data.decode(encoding)
    if oid == 16:
        return data == 't'
    return data


def _bytes_to_bint(b):
    return int.from_bytes(b, 'big')


def _bint_to_bytes(val):
    return val.to_bytes(4, 'big')


class Cursor(object):
    def __init__(self, connection):
        self.connection = connection
        self._rows = []
        self._rowcount = 0

    def execute(self, query, args=()):
        if not self.connection or not self.connection.is_connect():
            raise Exception(u"08003:Lost connection")
        self._rows.clear()
        self.args = args
        if args:
            query = query.replace(u'%', u'%%').replace(u'%%s', u'%s')
            query = query % tuple(self.connection.escape_parameter(arg).replace(u'%', u'%%') for arg in args)
            query = query.replace(u'%%', u'%')
        self.connection.execute(query, self)

    def fetchall(self):
        r = list(self._rows)
        self._rows.clear()
        return r
    
    def close(self):
        self.connection = None

    def rowcount(self):
        return self._rowcount

    def closed(self):
        return self.connection is None or not self.connection.is_connect()
      
      
class Connection(object):
    def __init__(self, user, password, database, host, port, timeout):
        self.user = user
        self.password = password
        self.database = database
        self.host = host
        self.port = port
        self.timeout = timeout
        self.encoders = {}
        self._open()

    def _send_data(self, message, data):
        length = len(data) + 4
        self._write(message + _bint_to_bytes(length) + data)

    def _send_message(self, message, data):
        length = len(data) + 4
        terminator = b'H\x00\x00\x00\x04'
        self._write(message + _bint_to_bytes(length) + data + terminator)

    def _process_messages(self, obj):
        errobj = None
        while True:
            try:
                code = ord(self._read(1))
            except Exception:
                break
            ln = _bytes_to_bint(self._read(4)) - 4
            data = self._read(ln)
            if code == 90:
                self._ready_for_query = data
                break
            elif code == 67:
                if not obj:
                    continue
                command = data[:-1].decode('ascii')
                if command == 'SHOW':
                    obj._rowcount = 1
                else:
                    for k in ('SELECT', 'UPDATE', 'DELETE', 'INSERT'):
                        if command.startswith(k):
                            obj._rowcount = int(command.split(' ')[-1])
                            break
            elif code == 82:
                auth_method = _bytes_to_bint(data[:4])
                if auth_method == 10:
                    assert b'SCRAM-SHA-256\x00\x00' in data
                    client_nonce = str(getrandbits(32))
                    first_message = 'n,,n=,r=' + client_nonce
                    self._send_data(b'p',
                                    b'SCRAM-SHA-256\x00' + _bint_to_bytes(len(first_message)) + first_message.encode(
                                        'utf-8'))
                    code = ord(self._read(1))
                    assert code == 82
                    ln = _bytes_to_bint(self._read(4)) - 4
                    data = self._read(ln)
                    assert _bytes_to_bint(data[:4]) == 11
                    server = {
                        kv[0]: kv[2:]
                        for kv in data[4:].decode('utf-8').split(',')
                    }
                    # r: server nonce
                    # s: server salt
                    # i: iteration count
                    assert server['r'][:len(client_nonce)] == client_nonce
                    # send client final message
                    salted_pass = pbkdf2_hmac_sha256(
                        self.password.encode('utf-8'),
                        binascii.a2b_base64(server['s']),
                        int(server['i']),
                    )
                    client_key = hmac_sha256_digest(salted_pass, b"Client Key")
                    client_first_message_bare = "n=,r=" + client_nonce
                    server_first_message = "r=%s,s=%s,i=%s" % (server['r'], server['s'], server['i'])
                    client_final_message_without_proof = "c=biws,r=" + server['r']
                    auth_msg = ','.join([
                        client_first_message_bare,
                        server_first_message,
                        client_final_message_without_proof
                    ])
                    client_sig = hmac_sha256_digest(
                        sha256(client_key).digest(),
                        auth_msg.encode('utf-8'),
                    )
                    proof = binascii.b2a_base64(
                        b"".join([bytes([x ^ y]) for x, y in zip(client_key, client_sig)])
                    ).rstrip(b'\n')
                    self._send_data(b'p', (client_final_message_without_proof + ",p=").encode('utf-8') + proof)
                    code = ord(self._read(1))
                    assert code == 82
                    ln = _bytes_to_bint(self._read(4)) - 4
                    data = self._read(ln)
                    assert _bytes_to_bint(data[:4]) == 12
                    code = ord(self._read(1))
                    assert code == 82
                    ln = _bytes_to_bint(self._read(4)) - 4
                    data = self._read(ln)
                    assert _bytes_to_bint(data[:4]) == 0
                else:
                    errobj = Exception("Authentication method %d not supported." % (auth_method,))
            elif code == 68:
                if not obj:
                    continue
                n = 2
                row = []
                while n < len(data):
                    if data[n:n + 4] == b'\xff\xff\xff\xff':
                        row.append(None)
                        n += 4
                    else:
                        ln = _bytes_to_bint(data[n:n + 4])
                        n += 4
                        row.append(data[n:n + ln])
                        n += ln
                for i in range(len(row)):
                    row[i] = _decode_column(row[i], obj.description[i][1], 'UTF8')
                obj._rows.append(tuple(row))
            elif code == 84:
                if not obj:
                    continue
                count = _bytes_to_bint(data[0:2])
                obj.description = [None] * count
                n = 2
                idx = 0
                for i in range(count):
                    name = data[n:data.find(b'\x00', n)]
                    n += len(name) + 1
                    try:
                        name = name.decode('UTF8')
                    except UnicodeDecodeError:
                        pass
                    type_code = _bytes_to_bint(data[n + 6:n + 10])
                    if type_code == 1043:
                        size = _bytes_to_bint(data[n + 12:n + 16]) - 4
                        precision = -1
                        scale = -1
                    elif type_code == 1700:
                        size = _bytes_to_bint(data[n + 10:n + 12])
                        precision = _bytes_to_bint(data[n + 12:n + 14])
                        scale = precision - _bytes_to_bint(data[n + 14:n + 16])
                    else:
                        size = _bytes_to_bint(data[n + 10:n + 12])
                        precision = -1
                        scale = -1
                    field = (name, type_code, None, size, precision, scale, None)
                    n += 18
                    obj.description[idx] = field
                    idx += 1
            else:
                pass
        return errobj

    def process_messages(self, obj):
        err = self._process_messages(obj)
        if err:
            raise err

    def _read(self, ln):
        if not self.sock:
            raise Exception(u"08003:Lost connection")
        r = b''
        while len(r) < ln:
            if hasattr(self.sock, "read"):
                b = self.sock.read(ln - len(r))
            else:
                b = self.sock.recv(ln - len(r))
            if not b:
                raise Exception(u"08003:Can't recv packets")
            r += b
        return r

    def _write(self, b):
        if not self.sock:
            raise Exception(u"08003:Lost connection")
        n = 0
        while (n < len(b)):
            if hasattr(self.sock, "write"):
                n += self.sock.write(b[n:])
            else:
                n += self.sock.send(b[n:])

    def _open(self):
        self.sock = socket.socket()
        self.sock.connect(socket.getaddrinfo(self.host, self.port)[0][-1])
        if self.timeout is not None:
            self.sock.settimeout(float(self.timeout))
        # protocol version 3.0
        v = b'\x00\x03\x00\x00'
        v += b'user\x00' + self.user.encode('ascii') + b'\x00'
        if self.database:
            v += b'database\x00' + self.database.encode('ascii') + b'\x00'
        v += b'\x00'
        self._write(_bint_to_bytes(len(v) + 4) + v)
        self.process_messages(None)

    def escape_parameter(self, v):
        return "'" + v.replace("'", "''") + "'"

    def is_connect(self):
        return bool(self.sock)

    def cursor(self):
        return Cursor(self)

    def _execute(self, query, obj):
        self._send_message(b'Q', query.encode('UTF8') + b'\x00')
        self.process_messages(obj)

    def execute(self, query, obj=None):
        self._execute(query, obj)

    def commit(self):
        if self.sock:
            self._send_message(b'Q', b"COMMIT\x00")
            self.process_messages(None)

    def close(self):
        if self.sock:
            # send Terminate
            self._write(b'X\x00\x00\x00\x04')
            self.sock.close()
            self.sock = None


def connect(host, user, password='', database=None, port=5432, timeout=None):
    return Connection(user, password, database, host, port, timeout)
