=============================
Pure python QR Code generator
=============================

.. image:: https://img.shields.io/pypi/v/qrcode.svg
    :target: https://pypi.org/project/qrcode/
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/qrcode.svg
    :target: https://pypi.org/project/qrcode/
    :alt: Python versions

.. image:: https://github.com/lincolnloop/python-qrcode/actions/workflows/push.yml/badge.svg
    :target: https://github.com/lincolnloop/python-qrcode/actions
    :alt: Build status

.. image:: https://img.shields.io/pypi/l/qrcode.svg
    :target: https://opensource.org/licenses/BSD-3-Clause
    :alt: License

.. image:: https://codecov.io/gh/lincolnloop/python-qrcode/graph/badge.svg?token=PLACEHOLDER
    :target: https://codecov.io/gh/lincolnloop/python-qrcode
    :alt: Code coverage


Generate QR codes.

A standard install uses pypng_ to generate PNG files and can also render QR
codes directly to the console. A standard install is just::

    pip install qrcode

For more image functionality, install qrcode with the ``pil`` dependency so
that pillow_ is installed and can be used for generating images::

    pip install "qrcode[pil]"

.. _pypng: https://pypi.python.org/pypi/pypng
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

Or in Python, use the ``make`` shortcut function:

.. code:: python

    import qrcode
    img = qrcode.make('Some data here')
    type(img)  # qrcode.image.pil.PilImage
    img.save("some_file.png")

Advanced Usage
--------------

For more control, use the ``QRCode`` class. For example:

.. code:: python

    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data('Some data')
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

The ``version`` parameter is an integer from 1 to 40 that controls the size of
the QR Code (the smallest, version 1, is a 21x21 matrix).
Set to ``None`` and use the ``fit`` parameter when making the code to determine
this automatically.

``fill_color`` and ``back_color`` can change the background and the painting
color of the QR, when using the default image factory. Both parameters accept
RGB color tuples.

.. code:: python


    img = qr.make_image(back_color=(255, 195, 235), fill_color=(55, 95, 35))

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

You can create the entire SVG or an SVG fragment. When building an entire SVG
image, you can use the factory that combines as a path (recommended, and
default for the script) or a factory that creates a simple set of rectangles.

From your command line::

    qr --factory=svg-path "Some text" > test.svg
    qr --factory=svg "Some text" > test.svg
    qr --factory=svg-fragment "Some text" > test.svg

Or in Python:

.. code:: python


    import qrcode
    import qrcode.image.svg
    
    method = input("What method? (basic, fragment, path): ")
    
    if method == 'basic':
        # Simple factory, just a set of rects.
        factory = qrcode.image.svg.SvgImage
    elif method == 'fragment':
        # Fragment factory (no standalone header)
        factory = qrcode.image.svg.SvgFragmentImage
    else:
        # Combined path factory, fixes white space that may occur when zooming
        factory = qrcode.image.svg.SvgPathImage
    
    img = qrcode.make('Some data here', image_factory=factory)
    
    img.save('some_file.svg')

Two other related factories are available that work the same, but also fill the
background of the SVG with white::

    qrcode.image.svg.SvgFillImage
    qrcode.image.svg.SvgPathFillImage

The ``QRCode.make_image()`` method forwards additional keyword arguments to the
underlying ElementTree XML library. This helps to fine tune the root element of
the resulting SVG:

.. code:: python

    import qrcode
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage)
    qr.add_data('Some data')
    qr.make(fit=True)

    img = qr.make_image(attrib={'class': 'some-css-class'})

You can convert the SVG image into strings using the ``to_string()`` method.
Additional keyword arguments are forwarded to ElementTrees ``tostring()``:

.. code:: python

    img.to_string(encoding='unicode')


Pure Python PNG
---------------

If Pillow is not installed, the default image factory will be a pure Python PNG
encoder that uses `pypng`.

You can use the factory explicitly from your command line::

    qr --factory=png "Some text" > test.png

Or in Python:

.. code:: python

    import qrcode
    from qrcode.image.pure import PyPNGImage
    img = qrcode.make('Some data here', image_factory=PyPNGImage)


Styled Image
------------

Works only with versions_ >=7.2 (SVG styled images require 7.4).

.. _versions: https://github.com/lincolnloop/python-qrcode/blob/master/CHANGES.rst#72-19-july-2021

To apply styles to the QRCode, use the ``StyledPilImage`` or one of the
standard SVG_ image factories. These accept an optional ``module_drawer``
parameter to control the shape of the QR Code.

These QR Codes are not guaranteed to work with all readers, so do some
experimentation and set the error correction to high (especially if embedding
an image).

Other PIL module drawers:

    .. image:: doc/module_drawers.png

For SVGs, use ``SvgSquareDrawer``, ``SvgCircleDrawer``,
``SvgPathSquareDrawer``, or ``SvgPathCircleDrawer``.

These all accept a ``size_ratio`` argument which allows for "gapped" squares or
circles by reducing this less than the default of ``Decimal(1)``.


The ``StyledPilImage`` additionally accepts an optional ``color_mask``
parameter to change the colors of the QR Code, and an optional
``embedded_image_path`` to embed an image in the center of the code.

Other color masks:

    .. image:: doc/color_masks.png

Here is a code example to draw a QR code with rounded corners, radial gradient
and an embedded image:

.. code:: python

    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
    from qrcode.image.styles.colormasks import RadialGradiantColorMask

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data('https://example.com')
    qr.make(fit=True)

    # Combined: rounded modules + radial gradient + embedded logo
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=RadialGradiantColorMask(
            center_color=(255, 0, 0),
            edge_color=(0, 0, 255),
        ),
        embedded_image_path="/path/to/logo.png",
    )
    img.save("styled_qr.png")

**Available Module Drawers (PIL)**

The following drawers control the shape of individual QR modules:

- ``SquareModuleDrawer`` — default square blocks
- ``RoundedModuleDrawer`` — rounded corners for a softer look
- ``GappedCircleDrawer`` — circular modules with gaps between them
- ``VerticalBarsDrawer`` — vertical bar style (like a barcode)

All drawers accept a ``size_ratio`` parameter (default ``1.0``) to control the
module size relative to the available space. Values less than 1.0 create gaps
between modules.

**Available Color Masks**

Color masks control the foreground color of dark modules:

- ``SolidFillColorMask`` — single uniform color (default: black)
- ``RadialGradiantColorMask`` — radial gradient from center to edge
- ``HorizontalGradiantColorMask`` — left-to-right gradient
- ``VerticalGradiantColorMask`` — top-to-bottom gradient
- ``ImageColorMask`` — colors derived from a reference image

All color masks support an optional ``back_color`` parameter for the background.
Use ``(255, 255, 255, 0)`` (RGBA with alpha=0) for transparency.

**CLI Advanced Usage**

The command-line tool supports multiple output formats:

.. code:: bash

    # Basic PNG output
    qr "https://example.com" > qr.png

    # SVG path output (recommended for web)
    qr --factory=svg-path "https://example.com" > qr.svg

    # ASCII art to terminal
    qr --terminal "https://example.com"

    # ASCII art to file
    qr --ascii "https://example.com" > qr.txt

    # Custom output file (avoids PowerShell piping issues)
    qr --output=qr.png "https://example.com"

    # Using a specific module drawer with StyledPilImage
    qr --factory=styledpil --drawer=circle "https://example.com" > styled.svg


Custom Image Factory
====================

You can create your own image output format by subclassing
:class:`qrcode.image.base.BaseImage`. Three abstract methods must be
implemented:

1. ``new_image(**kwargs)`` — instantiate and return the underlying image object.
2. ``drawrect(row, col)`` — draw a single dark module at grid position *(row, col)*.
3. ``save(stream, kind=None)`` — write the finished image to *stream*.

Use :meth:`~qrcode.image.base.BaseImage.pixel_box` to convert module coordinates
to pixel coordinates. Override :meth:`~qrcode.image.base.BaseImage.process` for
post-processing (called before saving when ``needs_processing = True``).

Minimal example::

    from qrcode.image.base import BaseImage

    class MyFormat(BaseImage):
        kind = "MYFMT"

        def new_image(self, **kwargs):
            return []  # placeholder image object

        def drawrect(self, row, col):
            self._img.append((row, col))

        def save(self, stream, kind=None):
            for coord in self._img:
                stream.write(f"module {coord}\\n".encode())

    import qrcode
    img = qrcode.make("Hello!", image_factory=MyFormat)

Examples
========

Get the text content from `print_ascii`:

.. code:: python

    import io
    import qrcode
    qr = qrcode.QRCode()
    qr.add_data("Some text")
    f = io.StringIO()
    qr.print_ascii(out=f)
    f.seek(0)
    print(f.read())

The `add_data` method will append data to the current QR object. To add new data by replacing previous content in the same object, first use clear method:

.. code:: python

    import qrcode
    qr = qrcode.QRCode()
    qr.add_data('Some data')
    img = qr.make_image()
    qr.clear()
    qr.add_data('New data')
    other_img = qr.make_image()

Pipe ascii output to text file in command line::

    qr --ascii "Some data" > "test.txt"
    cat test.txt

Alternative to piping output to file to avoid PowerShell issues::

    # qr "Some data" > test.png
    qr --output=test.png "Some data"
