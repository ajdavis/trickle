import re
import socket
from cStringIO import StringIO

from tornado.concurrent import Future
from tornado.netutil import Resolver
from tornado.tcpserver import TCPServer
from tornado.testing import AsyncTestCase, gen_test, bind_unused_port

from trickle import Trickle


class TestTCPServer(TCPServer):
    def __init__(self, *args, **kwargs):
        super(TestTCPServer, self).__init__(*args, **kwargs)
        self.test_stream = Future()

    def handle_stream(self, stream, address):
        self.test_stream.set_result(stream)


class TrickleTest(AsyncTestCase):
    def setUp(self):
        super(TrickleTest, self).setUp()
        sock, port = bind_unused_port()
        self.port = port
        self.server = TestTCPServer(self.io_loop)
        self.server.add_socket(sock)
        self.resolver = Resolver()

    @gen_test
    def test_basic(self):
        client_trickle = Trickle(
            socket.socket(socket.AF_INET),
            io_loop=self.io_loop)

        addr_info = yield self.resolver.resolve(
            'localhost', self.port, socket.AF_INET)

        sock_addr = addr_info[0][1]
        yield client_trickle.connect(sock_addr)

        # Wait for server to handle connection.
        server_stream = yield self.server.test_stream
        server_trickle = Trickle(server_stream)
        data = b'a' * 10
        yield server_trickle.write(data)
        self.assertEqual(data, (yield client_trickle.read(10)))

    @gen_test
    def test_read_timeout(self):
        client_trickle = Trickle(
            socket.socket(socket.AF_INET),
            io_loop=self.io_loop)

        addr_info = yield self.resolver.resolve(
            'localhost', self.port, socket.AF_INET)

        sock_addr = addr_info[0][1]
        yield client_trickle.connect(sock_addr)

        try:
            yield client_trickle.read(10, timeout=0.01)
        except socket.timeout:
            pass
        else:
            self.fail('socket.timeout not raised')

    @gen_test
    def test_xkcd(self):
        # TODO: connect to a local HTTP server instead.
        addr_info = yield self.resolver.resolve('xkcd.com', 80, socket.AF_INET)
        sock_addr = addr_info[0][1]
        trick = Trickle(
            socket.socket(socket.AF_INET),
            io_loop=self.io_loop)

        yield trick.connect(sock_addr)
        yield trick.write(b'GET / HTTP/1.1\r\nHost: xkcd.com\r\n\r\n')
        headers = b''

        # TODO: readuntil.
        while (
                not headers.endswith(b'\r\n\r\n')
                and not trick.closed()):
            c = yield trick.read(1)
            headers += c

        match = re.search(br'Content-Length: (\d+)\r\n', headers)
        content_length = int(match.group(1))
        yield trick.read(content_length)
