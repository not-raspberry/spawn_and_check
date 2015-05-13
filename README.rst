spawn_and_check
===============

Provide some checks, spawn a process and poll it until all checks pass.
That way you'll know when the application really started working.

Example
-------

.. code:: Python

    from spawn_and_check import execute, check_http
    process = execute('run_some_service --port 8000', [check_http('http://127.0.0.1:8000')], timeout=10)
    # The process is ready at this point.
