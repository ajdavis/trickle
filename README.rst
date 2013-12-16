===========
Trickle
===========

:Info: An IOStream wrapper for use with Tornado coroutines.
:Author: A\. Jesse Jiryu Davis

Purpose
=======
Tornado's IOStream API is central to Tornado, but it's designed to be used with
callbacks, instead of with coroutines and Futures. Trickle is a proof-of-concept
for a coroutine-friendly IOStream interface.

Documentation
=============
See the documentation on `ReadTheDocs <http://trickle.rtfd.org>`_.

Example
=======

.. literalinclude:: ../test/download_example.py

API
===

.. autoclass:: trickle.Trickle
    :members:

Testing
=======

Run ``python setup.py nosetests`` in the root directory.
