Testing
=======

First, install tox into your virtualenv::

    pip install --upgrade tox

To run all tests, you'll need to install multiple Python interpreters. On a
modern Ubuntu distribution you can use ``add-apt-repository
ppa:deadsnakes/ppa``.

Depending on if you can install the wheels directly for your OS, you may need
the libraries to build PIL, too. Here's the Ubuntu commands::

    sudo apt-get install build-essential python-dev python3-dev
    sudo apt-get install libjpeg8-dev zlib1g-dev

Finally, just run ``tox``!
If you want, you can test against a specific version like this: ``tox -e py36``
