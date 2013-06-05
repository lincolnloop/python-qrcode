#!/usr/bin/env python
from setuptools import setup

setup(
    name='qrcode',
    version='2.7',
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
        'qrcode.image',
    ],
    scripts=[
        'scripts/qr',
    ],
    data_files=[('share/man/man1', ['doc/qr.1'])],
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
    install_requires=[
        'pillow >= 2.0.0',
    ],
)
