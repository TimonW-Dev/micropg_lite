import ssl,hashlib,socket,binascii,random
def raiseExceptionLostConnection():raise Exception("08003:Lost connection")
def h(k,m):p=k+b'\x00'*(64-len(k)%64);return hashlib.sha256(bytes(0x5c^b for b in p)+hashlib.sha256(bytes(0x36^b for b in p)+m).digest()).digest()
class Cursor:
 def __init__(s,c):s.connection=c;s._rows=[]
 def execute(s,q,a=()):
  if not s.connection or not bool(s.connection.sock):raiseExceptionLostConnection()
  s._rows=[]
  if a:q=q.replace('%','%%').replace('%%s','%s')%tuple(('NULL'if i is None else"'"+i.replace("'","''")+"'"if isinstance(i,str)else"'"+''.join(['\\%03o'%c for c in i])+"'"for i in a))
  s.connection.execute(q,s)
 def fetchall(s):r=s._rows;s._rows=[];return r
 def close(s):s.connection=None
class connect:
 def __init__(s,host,user,password,database,port=5432,use_ssl=False):
  s.user,s.password,s.database,s.host,s.port,s.use_ssl,s.encoding,s.autocommit,s._ready_for_query=user,password,database,host,port,use_ssl,'UTF8',False,b'I'
  s.sock=socket.socket()
  s.sock.connect(socket.getaddrinfo(s.host,s.port)[0][-1])
  if s.use_ssl:
   s._w((8).to_bytes(4,'big')+(80877103).to_bytes(4,'big'))
   if s._d(1)==b'S':s.sock=ssl.wrap_socket(s.sock)
   else:raiseExceptionLostConnection()
  v=b'\x00\x03\x00\x00user\x00'+s.user.encode('ascii')+b'\x00'
  if s.database:v+=b'database\x00'+s.database.encode('ascii')+b'\x00'
  v+=b'\x00'
  s._w((len(v)+4).to_bytes(4,'big')+v)
  s._m(None)
 def _s(s,m,d):s._w(b''.join([m,(len(d)+4).to_bytes(4,'big'),d,b'H\x00\x00\x00\x04']))
 def _m(s,o):
  while 1:
   try:c=ord(s._d(1))
   except:raiseExceptionLostConnection()
   d=s._d(int.from_bytes(s._d(4),'big')-4)
   if c==90:s._ready_for_query=d;break
   elif c==82:
    n=str(random.getrandbits(32))
    f=f'n,,n=,r={n}'.encode('utf-8')
    m=b'SCRAM-SHA-256\x00'+(len(f)).to_bytes(4,'big')+f
    s._w(b'p'+(len(m)+4).to_bytes(4,'big')+m)
    assert ord(s._d(1))==82
    d=s._d(int.from_bytes(s._d(4),'big')-4)
    assert int.from_bytes(d[:4],'big')==11
    v=dict(k.split('=',1)for k in d[4:].decode('utf-8').split(','))
    assert v['r'].startswith(n)
    w=s.password.encode('utf-8')
    i=int(v['i'])
    u=h(w,binascii.a2b_base64(v['s'])+b'\x00\x00\x00\x01')
    j=int.from_bytes(u,'big')
    for _ in range(i-1):u=h(w,u);j^=int.from_bytes(u,'big')
    k=h(j.to_bytes(32,'big'),b"Client Key")
    a=f"n=,r={n},r={v['r']},s={v['s']},i={v['i']},c=biws,r={v['r']}"
    p=binascii.b2a_base64(bytes(x^y for x,y in zip(k,h(hashlib.sha256(k).digest(),a.encode('utf-8'))))).rstrip(b'\n')
    l=f"c=biws,r={v['r']},p={p.decode('utf-8')}".encode('utf-8')
    s._w(b'p'+(len(l)+4).to_bytes(4,'big')+l)
    for _ in range(3):
     assert ord(s._d(1))==82
     d=s._d(int.from_bytes(s._d(4),'big')-4)
     if int.from_bytes(d[:4],'big')==0:break
   elif c==67 and o:
    m=d[:-1].decode('ascii')
    if m=='SHOW':o._rowcount=1
    else:
     p=m.split()
     if p and p[-1].isdigit():o._rowcount=int(p[-1])
   elif c==84 and o:
    t=int.from_bytes(d[:2],'big')
    o.description=[None]*t
    n=2
    for i in range(t):
     e=d.index(b'\x00',n)
     m=d[n:e]
     n=e+1
     try:m=m.decode(s.encoding)
     except:pass
     y=int.from_bytes(d[n+6:n+10],'big')
     if y==1043:z,p,q=int.from_bytes(d[n+12:n+16],'big')-4,-1,-1
     elif y==1700:z=int.from_bytes(d[n+10:n+12],'big');p=int.from_bytes(d[n+12:n+14],'big');q=p-int.from_bytes(d[n+14:n+16],'big')
     else:z,p,q=int.from_bytes(d[n+10:n+12],'big'),-1,-1
     o.description[i]=(m,y,None,z,p,q,None)
     n+=18
   elif c==68 and o:
    n,w=2,[]
    while n<len(d):
     if d[n:n+4]==b'\xff\xff\xff\xff':w.append(None);n+=4
     else:
      l=int.from_bytes(d[n:n+4],'big')
      cd=d[n+4:n+4+l]
      co=o.description[len(w)][1]
      ce=s.encoding
      dd=cd.decode(ce)if cd else None
      if co==16:dd=(dd=='t')
      elif co in(21,23,20,26):dd=int(dd)
      elif co in(700,701):dd=float(dd)
      w.append(dd)
      n+=l+4
    o._rows.append(tuple(w))
   elif c==69:raiseExceptionLostConnection()
   elif c==100:o.write(d)
   elif c==71:
    while 1:
     b=o.read(8192)
     if not b:break
     s._w(b'd'+(len(b)+4).to_bytes(4,'big')+b)
    s._w(b'c\x00\x00\x00\x04S\x00\x00\x00\x04')
 def _d(s,l):
  if not s.sock:raiseExceptionLostConnection()
  r=bytearray(l)
  p=0
  while p<l:
   c=s.sock.read(l-p)if hasattr(s.sock,"read")else s.sock.recv(l-p)
   if not c:raiseExceptionLostConnection()
   r[p:p+len(c)]=c
   p+=len(c)
  return bytes(r)
 def _w(s,b):
  if not s.sock:raiseExceptionLostConnection()
  p=0
  while p<len(b):p+=s.sock.write(b[p:])if hasattr(s.sock,"write")else s.sock.send(b[p:])
 def cursor(s):return Cursor(s)
 def execute(s,q,o=None):
  if s._ready_for_query!=b'T':s.begin()
  s._s(b'Q',q.encode(s.encoding)+b'\x00')
  s._m(o)
  if s.autocommit:s.commit()
 def begin(s):
  if s._ready_for_query==b'E':s._rollback()
  s._s(b'Q',b"BEGIN\x00")
  s._m(None)
 def commit(s):
  if s.sock:s._s(b'Q',b"COMMIT\x00");s._m(None);s.begin()
 def _rollback(s):
  if s.sock:s._s(b'Q',b"ROLLBACK\x00");s._m(None)
 def rollback(s):s._rollback();s.begin()
 def close(s):
  if s.sock:s._w(b'X\x00\x00\x00\x04');s.sock.close();s.sock=None
def create_database(host,user,password,database,port=5432,use_ssl=False):
 c=connect(host,user,password,None,port,use_ssl)
 c._s(b'Q','CREATE DATABASE {}'.format(database).encode('utf-8')+b'\x00')
 c._m(None)
 c.close()
def drop_database(host,user,password,database,port=5432,use_ssl=False):
 c=connect(host,user,password,None,port,use_ssl)
 c._s(b'Q','DROP DATABASE {}'.format(database).encode('utf-8')+b'\x00')
 c._m(None)
 c.close()
