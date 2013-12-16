import socket

from tornado import gen, ioloop
from tornado.gen import Wait
from tornado.iostream import IOStream
from yieldpoints import WaitAny, Cancel


__all__ = ['Trickle']

version = '0.1'

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
    """A coroutine-friendly :class:`~tornado.iostream.IOStream` interface.

    Takes same parameters as ``IOStream``, or takes a single ``IOStream``
    as its only parameter.
    """
    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], IOStream):
            if len(args) > 1 or kwargs:
                raise TypeError('Too many arguments to Trickle()')

            self.stream = args[0]
        else:
            self.stream = IOStream(*args, **kwargs)

    def connect(self, address, server_hostname=None, timeout=None):
        """Connects the socket to a remote address without blocking.

        Like ``IOStream`` :meth:`~tornado.iostream.IOStream.connect`,
        but returns a :class:`~tornado.concurrent.Future` and takes
        no callback.
        """
        method = trickle_method('connect', timeout)
        return method(self, address, server_hostname=server_hostname)

    def read_until(self, delimiter, timeout=None):
        """Read up to the given delimiter..

        Like ``IOStream`` :meth:`~tornado.iostream.IOStream.read_until`,
        but returns a :class:`~tornado.concurrent.Future` and takes no
        callback.
        """
        return trickle_method('read_until', timeout)(self, delimiter)

    def read_until_regex(self, regex, timeout=None):
        """Read up to the given regex pattern.

        Like ``IOStream`` :meth:`~tornado.iostream.IOStream.read_until_regex`,
        but returns a :class:`~tornado.concurrent.Future` and takes no
        callback.
        """
        return trickle_method('read_until_regex', timeout)(self, regex)

    def read_bytes(self, num_bytes, timeout=None):
        """Read the given number of bytes.

        Like ``IOStream`` :meth:`~tornado.iostream.IOStream.read_bytes`,
        but returns a :class:`~tornado.concurrent.Future` and takes no
        callback or streaming_callback.
        """
        return trickle_method('read_bytes', timeout)(self, num_bytes)

    @gen.coroutine
    def read_until_close(self, timeout=None):
        """Read all remaining data from the socket.

        Like ``IOStream`` :meth:`~tornado.iostream.IOStream.read_until_close`,
        but returns a :class:`~tornado.concurrent.Future` and takes no
        callback or streaming_callback.
        """
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
        """Write the given data to this stream.

        Like ``IOStream`` :meth:`~tornado.iostream.IOStream.write`, but
        returns a :class:`~tornado.concurrent.Future` and takes no callback.

        yield the returned Future to wait for all data to be written to the
        stream.
        """
        return trickle_method('write', timeout)(self, data, **kwargs)

    def closed(self):
        """Returns true if the stream has been closed."""
        return self.stream.closed()
