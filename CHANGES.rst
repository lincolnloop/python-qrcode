==========
Change log
==========

7.4 (unreleased)
================

- Restructure the factory drawers, allowing different shapes in SVG image
  factories as well.

- Add a ``--factory-drawer`` option to the ``qr`` console script.

- Optimize the output for the ``SVGPathImage`` factory (more than 30% reduction
  in file sizes).


7.3.1 (1 October 2021)
======================

- Improvements for embeded image.


7.3 (19 August 2021)
====================

- Skip color mask if QR is black and white


7.2 (19 July 2021)
==================

- Add Styled PIL image factory, allowing different color masks and shapes in QR codes

- Small performance inprovement

- Add check for border size parameter


7.1 (1 July 2021)
=================

- Add --ascii parameter to command line interface allowing to output ascii when stdout is piped

- Add --output parameter to command line interface to specify output file

- Accept RGB tuples in fill_color and back_color

- Add to_string method to SVG images

- Replace inline styles with SVG attributes to avoid CSP issues

- Add Python3.10 to supported versions


7.0 (29 June 2021)
==================

- Drop Python < 3.6 support.


6.1 (14 January 2019)
=====================

- Fix short chunks of data not being optimized to the correct mode.

- Tests fixed for Python 3


6.0 (23 March 2018)
===================

- Fix optimize length being ignored in ``QRCode.add_data``.

- Better calculation of the best mask pattern and related optimizations. Big
  thanks to cryptogun!


5.3 (18 May 2016)
=================

* Fix incomplete block table for QR version 15. Thanks Rodrigo Queiro for the
  report and Jacob Welsh for the investigation and fix.

* Avoid unnecessary dependency for non MS platforms, thanks to Noah Vesely.

* Make ``BaseImage.get_image()`` actually work.


5.2 (25 Jan 2016)
=================

* Add ``--error-correction`` option to qr script.

* Fix script piping to stdout in Python 3 and reading non-UTF-8 characters in
  Python 3.

* Fix script piping in Windows.

* Add some useful behind-the-curtain methods for tinkerers.

* Fix terminal output when using Python 2.6

* Fix terminal output to display correctly on MS command line.

5.2.1
-----

* Small fix to terminal output in Python 3 (and fix tests)

5.2.2
-----

* Revert some terminal changes from 5.2 that broke Python 3's real life tty
  code generation and introduce a better way from Jacob Welsh.


5.1 (22 Oct 2014)
=================

* Make ``qr`` script work in Windows. Thanks Ionel Cristian Mărieș

* Fixed print_ascii function in Python 3.

* Out-of-bounds code version numbers are handled more consistently with a
  ValueError.

* Much better test coverage (now only officially supporting Python 2.6+)


5.0 (17 Jun 2014)
=================

* Speed optimizations.

* Change the output when using the ``qr`` script to use ASCII rather than
  just colors, better using the terminal real estate.

* Fix a bug in passing bytecode data directly when in Python 3.

* Substation speed optimizations to best-fit algorithm (thanks Jacob Welsh!).

* Introduce a ``print_ascii`` method and use it as the default for the ``qr``
  script rather than ``print_tty``.

5.0.1
-----

* Update version numbers correctly.


4.0 (4 Sep 2013)
================

* Made qrcode work on Python 2.4 - Thanks tcely.
  Note: officially, qrcode only supports 2.5+.

* Support pure-python PNG generation (via pymaging) for Python 2.6+ -- thanks
  Adam Wisniewski!

* SVG image generation now supports alternate sizing (the default box size of
  10 == 1mm per rectangle).

* SVG path image generation allows cleaner SVG output by combining all QR rects
  into a single path. Thank you, Viktor Stískala.

* Added some extra simple SVG factories that fill the background white.

4.0.1
-----

* Fix the pymaging backend not able to save the image to a buffer. Thanks ilj!

4.0.2
-----

* Fix incorrect regex causing a comma to be considered part of the alphanumeric
  set.

* Switch to using setuptools for setup.py.

4.0.3
-----

* Fix bad QR code generation due to the regex comma fix in version 4.0.2.

4.0.4
-----

* Bad version number for previous hotfix release.


3.1 (12 Aug 2013)
=================

* Important fixes for incorrect matches of the alpha-numeric encoding mode.
  Previously, the pattern would match if a single line was alpha-numeric only
  (even if others wern't). Also, the two characters ``{`` and ``}`` had snuck
  in as valid characters. Thanks to Eran Tromer for the report and fix.

* Optimized chunking -- if the parts of the data stream can be encoded more
  efficiently, the data will be split into chunks of the most efficient modes.

3.1.1
-----

* Update change log to contain version 3.1 changes. :P

* Give the ``qr`` script an ``--optimize`` argument to control the chunk
  optimization setting.


3.0 (25 Jun 2013)
=================

* Python 3 support.

* Add QRCode.get_matrix, an easy way to get the matrix array of a QR code
  including the border. Thanks Hugh Rawlinson.

* Add in a workaround so that Python 2.6 users can use SVG generation (they
  must install ``lxml``).

* Some initial tests! And tox support (``pip install tox``) for testing across
  Python platforms.


2.7 (5 Mar 2013)
================

* Fix incorrect termination padding.


2.6 (2 Apr 2013)
================

* Fix the first four columns incorrectly shifted by one. Thanks to Josep
  Gómez-Suay for the report and fix.

* Fix strings within 4 bits of the QR version limit being incorrectly
  terminated. Thanks to zhjie231 for the report.


2.5 (12 Mar 2013)
=================

* The PilImage wrapper is more transparent - you can use any methods or
  attributes available to the underlying PIL Image instance.

* Fixed the first column of the QR Code coming up empty! Thanks to BecoKo.

2.5.1
-----

* Fix installation error on Windows.


2.4 (23 Apr 2012)
=================

* Use a pluggable backend system for generating images, thanks to Branko Čibej!
  Comes with PIL and SVG backends built in.

2.4.1
-----

* Fix a packaging issue

2.4.2
-----

* Added a ``show`` method to the PIL image wrapper so the ``run_example``
  function actually works.


2.3 (29 Jan 2012)
=================

* When adding data, auto-select the more efficient encoding methods for numbers
  and alphanumeric data (KANJI still not supported).

2.3.1
-----

* Encode unicode to utf-8 bytestrings when adding data to a QRCode.


2.2 (18 Jan 2012)
=================

* Fixed tty output to work on both white and black backgrounds.

* Added `border` parameter to allow customizing of the number of boxes used to
  create the border of the QR code


2.1 (17 Jan 2012)
=================

* Added a ``qr`` script which can be used to output a qr code to the tty using
  background colors, or to a file via a pipe.
