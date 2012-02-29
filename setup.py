#!/usr/bin/env python
from distutils.core import setup

setup(
    name='qrcode',
    version='2.3',
    url='https://github.com/lincolnloop/python-qrcode',
    #download_url='',
    description='QR Code image generator',
    license='BSD',
    long_description=open('README.rst').read(),
    author='Lincoln Loop',
    author_email='info@lincolnloop.com',
    platforms=['any'],
    packages=[
        'qrcode',
    ],
    scripts=[
        'scripts/qr',
    ],
    package_data={'': ['LICENSE']},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
