=============================
Pure python QR Code generator
=============================

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

For more info check `Advanced Usage <docs/advanced_usage.rst>`_.

Features
========
* Generate QR Code as either PNG, SVG or SVG Fragment.
* Convert the SVG image into strings using the ``to_string()`` method.
* Style image, by customizing colors, shapes and embedding images.

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

More examples in `Advanced Usage <docs/advanced_usage.rst>`_.
