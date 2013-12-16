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

Dependencies
============
* Tornado_ >= version 3.1.
* YieldPoints_.

.. _Tornado: http://www.tornadoweb.org/
.. _YieldPoints: http://yieldpoints.rtfd.org/

Example
=======

.. literalinclude:: ../test/download_example.py

API
===

.. autoclass:: trickle.Trickle
    :members:

Changes
=======

See the :doc:`changelog`.

Testing
=======

Run ``python setup.py nosetests`` in the root directory.
