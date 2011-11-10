#!/usr/bin/env python
from distutils.core import setup

setup(
    name='qrcode',
    version='1.0',
    url='http://github.com/lincolnloop/qrcode',
    #download_url='',
    description='QR Code image generator',
    long_description=open('README.rst').read(),
    author='Lincoln Loop',
    author_email='info@lincolnloop.com',
    platforms=['any'],
    packages=[
        'qrcode',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
