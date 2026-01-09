Testing
=======

This project uses `uv <https://github.com/astral-sh/uv>`_ for dependency management and running tests.
It also uses `just <https://github.com/casey/just>`_ as a command runner for convenience.

Setup
-----

1.  Install ``uv`` (see `installation instructions <https://github.com/astral-sh/uv?tab=readme-ov-file#installation>`_).
2.  Install ``just`` (see `installation instructions <https://github.com/casey/just?tab=readme-ov-file#installation>`_).

Running Tests
-------------

To run the full test suite (all Python versions and variants)::

    just test

To run a quick test on your current environment (fastest)::

    just test quick

To run tests for a specific Python version::

    just test 3.12

To run tests for a specific Python version and variant (pil, png, none)::

    just test 3.12 pil

Linting
-------

To run all checks (formatting, linting, and tests)::

    just check