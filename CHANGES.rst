==========
Change log
==========

HEAD
====


Version 3.0
===========

* Python 3 support.

* Add QRCode.get_matrix, an easy way to get the matrix array of a QR code
  including the border. Thanks Hugh Rawlinson.

* Add in a workaround so that Python 2.6 users can use SVG generation (they
  must install ``lxml``).

* Some initial tests! And tox support (``pip install tox``) for testing across
  Python platforms.


Version 2.7
===========

* Fix incorrect termination padding.


Version 2.6
===========

* Fix the first four columns incorrectly shifted by one. Thanks to Josep
  Gómez-Suay for the report and fix.

* Fix strings within 4 bits of the QR version limit being incorrectly
  terminated. Thanks to zhjie231 for the report.


Version 2.5
===========

* The PilImage wrapper is more transparent - you can use any methods or
  attributes available to the underlying PIL Image instance.

* Fixed the first column of the QR Code coming up empty! Thanks to BecoKo.

Version 2.5.1
-------------

* Fix installation error on Windows.


Version 2.4
===========

* Use a pluggable backend system for generating images, thanks to Branko Čibej!
  Comes with PIL and SVG backends built in.

Version 2.4.1
-------------

* Fix a packaging issue

Version 2.4.2
-------------

* Added a ``show`` method to the PIL image wrapper so the ``run_example``
  function actually works.


Version 2.3
===========

* When adding data, auto-select the more efficient encoding methods for numbers
  and alphanumeric data (KANJI still not supported).

Version 2.3.1
-------------

* Encode unicode to utf-8 bytestrings when adding data to a QRCode.


Version 2.2
===========

* Fixed tty output to work on both white and black backgrounds.

* Added `border` parameter to allow customizing of the number of boxes used to
  create the border of the QR code


Version 2.1
===========

* Added a ``qr`` script which can be used to output a qr code to the tty using
  background colors, or to a file via a pipe.
