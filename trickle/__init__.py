import socket

from tornado import gen, ioloop
from tornado.iostream import IOStream
from yieldpoints import WaitAny, Cancel


__all__ = ['Trickle']


closed = object()
success = object()


# TODO: All IOStream methods: readuntil, etc.
class Trickle(object):
    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], IOStream):
            if len(args) > 1 or kwargs:
                raise TypeError('Too many arguments to Trickle()')

            self.stream = args[0]
        else:
            self.stream = IOStream(*args, **kwargs)

    @gen.coroutine
    def connect(self, *args, **kwargs):
        # TODO: error handling, timeouts.
        yield gen.Task(self.stream.connect, *args, **kwargs)

    @gen.coroutine
    def read_bytes(self, num_bytes, timeout=None):
        # This code inspired by Roey Berman: https://github.com/bergundy
        stream = self.stream
        stream.set_close_callback(callback=(yield gen.Callback(closed)))
        ioloop_timeout = None
        if timeout:
            def on_timeout():
                stream.close((socket.timeout, socket.timeout(), None))

            ioloop_timeout = ioloop.IOLoop.current().add_timeout(
                timeout, callback=on_timeout)

        stream.read_bytes(
            num_bytes,
            callback=(yield gen.Callback(success)))

        key, result = yield WaitAny((closed, success))

        if ioloop_timeout is not None:
            ioloop.IOLoop.current().remove_timeout(ioloop_timeout)

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

    @gen.coroutine
    def write(self, data):
        # TODO: error handling.
        yield gen.Task(self.stream.write, data)

    def closed(self):
        return self.stream.closed()
