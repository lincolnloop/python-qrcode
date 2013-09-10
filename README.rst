=============================
Pure python QR Code generator
=============================

This module uses image libraries, Python Imaging Library (PIL) by default, to
generate QR Codes.

It is recommended to use the pillow_ fork rather than PIL itself.

.. _pillow: https://pypi.python.org/pypi/Pillow


What is a QR Code?
==================

A Quick Response code is a two-dimensional pictographic code used for its fast
readability and comparatively large storage capacity. The code consists of
black modules arranged in a square pattern on a white background. The
information encoded can be made up of any kind of data (e.g., binary,
alphanumeric, or Kanji symbols)

Usage
=====

From the command line, use the installed ``qr`` script::

    qr "Some text" > test.png

Or in Python, use the ``make`` shortcut function::

    import qrcode
    img = qrcode.make('Some data here')

Advanced Usage
--------------

For more control, use the ``QRCode`` class. For example::

    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data('Some data')
    qr.make(fit=True)

    img = qr.make_image()

The ``version`` parameter is an integer from 1 to 40 that controls the size of
the QR Code (the smallest, version 1, is a 21x21 matrix).
Set to ``None`` and use the ``fit`` parameter when making the code to determine
this automatically.

The ``error_correction`` parameter controls the error correction used for the
QR Code. The following four constants are made available on the ``qrcode``
package:

``ERROR_CORRECT_L``
    About 7% or less errors can be corrected.
``ERROR_CORRECT_M`` (default)
    About 15% or less errors can be corrected.
``ERROR_CORRECT_Q``
    About 25% or less errors can be corrected.
``ERROR_CORRECT_H``.
    About 30% or less errors can be corrected.

The ``box_size`` parameter controls how many pixels each "box" of the QR code
is.

The ``border`` parameter controls how many boxes thick the border should be
(the default is 4, which is the minimum according to the specs).

Other image factories
=====================

You can encode as SVG, or use a new pure Python image processor to encode to
PNG images.

The Python examples below use the ``make`` shortcut. The same ``image_factory``
keyword argument is a valid option for the ``QRCode`` class for more advanced
usage.

SVG
---

On Python 2.6 must install lxml since the older xml.etree.ElementTree version
can not be used to create SVG images.

You can create the entire SVG or an SVG fragment. When building an entire SVG
image, you can use the factory that combines as a path (recommended, and
default for the script) or a factory that creates a simple set of rectangles.

From your command line::

    qr --factory=svg-path "Some text" > test.svg
    qr --factory=svg "Some text" > test.svg
    qr --factory=svg-fragment "Some text" > test.svg

Or in Python::

    import qrcode
    import qrcode.image.svg

    if method == 'basic':
        # Simple factory, just a set of rects.
        factory = qrcode.image.svg.SvgImage
    elif method == 'fragment':
        # Fragment factory (also just a set of rects)
        factory = qrcode.image.svg.SvgFragmentImage
    else:
        # Combined path factory, fixes white space that may occur when zooming
        factory = qrcode.image.svg.SvgPathImage

    img = qrcode.make('Some data here', image_factory=factory)

Two other related factories are available that work the same, but also fill the
background of the SVG with white::

    qrcode.image.svg.SvgFillImage
    qrcode.image.svg.SvgPathFillImage


Pure Python PNG
---------------

Install the following two packages::

    pip install git+git://github.com/ojii/pymaging.git#egg=pymaging
    pip install git+git://github.com/ojii/pymaging-png.git#egg=pymaging-png

From your command line::

    qr --factory=pymaging "Some text" > test.png

Or in Python::

    import qrcode
    from qrcode.image.pure import PymagingImage
    img = qrcode.make('Some data here', image_factory=PymagingImage)
