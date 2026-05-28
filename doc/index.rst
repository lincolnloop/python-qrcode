python-qrcode — API Reference
==============================

Generate QR codes from the command line or with a simple Python library.

.. toctree::
   :maxdepth: 2
   :caption: Modules

   modules.rst


Quick Start
-----------

.. code-block:: python

   import qrcode

   img = qrcode.make("https://example.com")
   img.save("qr.png")


Image Factories
---------------

The library supports multiple output formats via image factory classes.

PIL (PNG/JPEG)
~~~~~~~~~~~~~~

.. autoclass:: qrcode.image.pil.PilImage
   :members:
   :undoc-members:
   :show-inheritance:

Styled PIL
~~~~~~~~~~

.. autoclass:: qrcode.image.styledpil.StyledPilImage
   :members:
   :undoc-members:
   :show-inheritance:

SVG Fragment
~~~~~~~~~~~~

.. autoclass:: qrcode.image.svg.SvgFragmentImage
   :members:
   :undoc-members:
   :show-inheritance:

SVG Standalone
~~~~~~~~~~~~~~

.. autoclass:: qrcode.image.svg.SvgImage
   :members:
   :undoc-members:
   :show-inheritance:

SVG Path
~~~~~~~~

.. autoclass:: qrcode.image.svg.SvgPathImage
   :members:
   :undoc-members:
   :show-inheritance:

PyPNG (pure Python)
~~~~~~~~~~~~~~~~~~~

.. autoclass:: qrcode.image.pure.PyPNGImage
   :members:
   :undoc-members:
   :show-inheritance:


Colour Masks
------------

.. automodule:: qrcode.image.styles.colormasks
   :members:
   :undoc-members:
   :show-inheritance:


Module Drawers
--------------

.. autoclass:: qrcode.image.styles.moduledrawers.base.QRModuleDrawer
   :members:
   :undoc-members:
   :show-inheritance:

PIL Drawers
~~~~~~~~~~~

.. automodule:: qrcode.image.styles.moduledrawers.pil
   :members:
   :undoc-members:
   :show-inheritance:

SVG Drawers
~~~~~~~~~~~

.. automodule:: qrcode.image.styles.moduledrawers.svg
   :members:
   :undoc-members:
   :show-inheritance:


Core API
--------

.. autoclass:: qrcode.main.QRCode
   :members:
   :undoc-members:
   :show-inheritance:

.. autofunction:: qrcode.make


Exceptions
----------

.. automodule:: qrcode.exceptions
   :members:
   :undoc-members:
   :show-inheritance:
