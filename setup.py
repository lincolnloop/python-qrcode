#!/usr/bin/env python
from __future__ import unicode_literals
import io
import os
from setuptools import setup, find_packages
import sys


def long_description():
    """
    Build the long description from a README file located in the same directory
    as this module.
    """
    base_path = os.path.dirname(os.path.realpath(__file__))
    content = []
    for name in ('README.rst', 'CHANGES.rst'):
        with io.open(os.path.join(base_path, name), encoding='utf-8') as f:
            content.append(f.read())
    return '\n\n'.join(content)


setup(
    name='qrcode',
    version='5.3.post',
    url='https://github.com/lincolnloop/python-qrcode',
    description='QR Code image generator',
    license='BSD',
    long_description=long_description(),
    author='Lincoln Loop',
    author_email='info@lincolnloop.com',
    platforms=['any'],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'qr = qrcode.console_scripts:main',
        ],
    },
    install_requires=['six'],
    extra_requires={
        ':sys_platform==win32': ['colorama'],
        ':sys_platform==cygwin': ['colorama']
    },
    data_files=[('share/man/man1', ['doc/qr.1'])],
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
