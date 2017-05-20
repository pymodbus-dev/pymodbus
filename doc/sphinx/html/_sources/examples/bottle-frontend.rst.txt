==================================================
Bottle Web Frontend Example
==================================================

--------------------------------------------------
Summary
--------------------------------------------------

This is a simple example of adding a live REST api
on top of a running pymodbus server. This uses the
bottle microframework to achieve this.

The example can be hosted under twisted as well as
the bottle internal server and can furthermore be
run behind gunicorn, cherrypi, etc wsgi containers.

--------------------------------------------------
Main Program
--------------------------------------------------

.. literalinclude:: ../../../examples/gui/web/frontend.py

