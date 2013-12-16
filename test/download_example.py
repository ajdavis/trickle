import re
import socket

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.netutil import Resolver

from trickle import Trickle


resolver = Resolver()


@gen.coroutine
def download():
    sock = socket.socket(socket.AF_INET)
    trick = Trickle(sock)

    addr_info = yield resolver.resolve(
        'xkcd.com',
        80,
        socket.AF_INET)

    sock_addr = addr_info[0][1]

    yield trick.connect(sock_addr)
    yield trick.write(b'GET / HTTP/1.1\r\nHost: xkcd.com\r\n\r\n')

    headers = yield trick.read_until(b'\r\n\r\n')
    match = re.search(br'Content-Length: (\d+)\r\n', headers)
    content_length = int(match.group(1))

    body = yield trick.read_bytes(content_length)
    print body


IOLoop.current().run_sync(download)
