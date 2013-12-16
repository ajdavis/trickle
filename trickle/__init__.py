import socket

from tornado import gen, ioloop
from tornado.gen import Wait
from tornado.iostream import IOStream
from yieldpoints import WaitAny, Cancel


__all__ = ['Trickle']


closed = object()
success = object()


def trickle_method(method_name, timeout):
    @gen.coroutine
    def wrapped(self, *args, **kwargs):
        # This code inspired by Roey Berman: https://github.com/bergundy
        stream = self.stream
        stream.set_close_callback(callback=(yield gen.Callback(closed)))
        ioloop_timeout = None
        if timeout:
            def on_timeout():
                stream.close((socket.timeout, socket.timeout(), None))

            ioloop_timeout = stream.io_loop.add_timeout(
                timeout, callback=on_timeout)

        method = getattr(stream, method_name)
        kwargs['callback'] = yield gen.Callback(success)
        method(*args, **kwargs)

        key, result = yield WaitAny((closed, success))

        if ioloop_timeout is not None:
            stream.io_loop.remove_timeout(ioloop_timeout)

        stream.set_close_callback(None)
        if key is success:
            yield Cancel(closed)
            raise gen.Return(result)
        elif key is closed:
            yield Cancel(success)
            if stream.error:
                raise stream.error
            return
        else:
            assert False, 'Unexpected return from WaitAny'

    return wrapped


class Trickle(object):
    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], IOStream):
            if len(args) > 1 or kwargs:
                raise TypeError('Too many arguments to Trickle()')

            self.stream = args[0]
        else:
            self.stream = IOStream(*args, **kwargs)

    def connect(self, address, server_hostname=None, timeout=None):
        method = trickle_method('connect', timeout)
        return method(self, address, server_hostname=server_hostname)

    def read_until(self, delimiter, timeout=None):
        return trickle_method('read_until', timeout)(self, delimiter)

    def read_until_regex(self, regex, timeout=None):
        return trickle_method('read_until_regex', timeout)(self, regex)

    # TODO: note no streaming_callback.
    def read_bytes(self, num_bytes, timeout=None):
        return trickle_method('read_bytes', timeout)(self, num_bytes)

    # TODO: note no streaming_callback.
    @gen.coroutine
    def read_until_close(self, timeout=None):
        stream = self.stream
        ioloop_timeout = None

        if timeout:
            def on_timeout():
                stream.close((socket.timeout, socket.timeout(), None))

            ioloop_timeout = stream.io_loop.add_timeout(
                timeout, callback=on_timeout)

        stream.read_until_close(callback=(yield gen.Callback(closed)))
        result = yield Wait(closed)

        if ioloop_timeout is not None:
            stream.io_loop.remove_timeout(ioloop_timeout)

        if stream.error:
            raise stream.error

        raise gen.Return(result)

    def write(self, data, timeout=None, **kwargs):
        return trickle_method('write', timeout)(self, data, **kwargs)

    def closed(self):
        return self.stream.closed()
