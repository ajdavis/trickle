===========
Trickle
===========

:Info: IOStream wrapper for use with Tornado coroutines.
:Author: A\. Jesse Jiryu Davis

Dependencies
============
Tornado_ >= version 3.1.
YieldPoints_.

.. _Tornado: http://www.tornadoweb.org/
.. _YieldPoints: http://yieldpoints.rtfd.org/

Example
=======

.. code-block:: python

@gen.coroutine
def communicate():


Testing
=======

Run ``python setup.py nosetests`` in the root directory.
