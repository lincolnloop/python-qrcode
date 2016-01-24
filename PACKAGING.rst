Packaging quick reminder
========================

Ensure version numbers in ``setup.py`` and ``doc/qr.1`` have been updated.

1. Check twine and wheel are up to date::

    pip install --upgrade twine wheel

2. Delete contents of ``dist/``::

    rm -r dist

3. Package it up::

    python setup.py sdist bdist_wheel

4. Sign it::

    gpg --detach-sign -a dist/*.gz
    gpg --detach-sign -a dist/*.whl

5. Upload it::

    twine upload dist/*
