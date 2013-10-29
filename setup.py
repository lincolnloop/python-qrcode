#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='qrcode',
    version='4.0.4',
    url='https://github.com/lincolnloop/python-qrcode',
    #download_url='',
    description='QR Code image generator',
    license='BSD',
    long_description=open('README.rst').read(),
    author='Lincoln Loop',
    author_email='info@lincolnloop.com',
    platforms=['any'],
    packages=find_packages(),
    scripts=[
        'scripts/qr',
    ],
    install_requires=['six'],
    data_files=[('share/man/man1', ['doc/qr.1'])],
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
