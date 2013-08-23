Testing
=======

First, install tox into your virtualenv::

    pip install -U tox

To run all the qrcode tests, you'll need to install the older Python
interpreters. Here's how you'll do it on a modern Ubuntu distribution::

    sudo add-apt-repository ppa:fkrull/deadsnakes
    sudo apt-get update
    sudo apt-get install python2.4-dev python2.6-dev

Ensure you have the libraries to build PIL, too::

    sudo apt-get install build-essential python-dev python3-dev 
    sudo apt-get install libjpeg8-dev zlib1g-dev

Finally, just run ``tox``!
If you want, you can test against a specific version like this: ``tox -e py33``
