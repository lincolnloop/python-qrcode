You can encode as SVG, or use a new pure Python image processor to
encode to PNG images.

The Python examples below use the `make` shortcut. The same
`image_factory` keyword argument is a valid option for the `QRCode`
class for more advanced usage.

## SVG

You can create the entire SVG or an SVG fragment. When building an
entire SVG image, you can use the factory that combines as a path
(recommended, and default for the script) or a factory that creates a
simple set of rectangles.

From your command line:
```bash
$ qr --factory=svg-path "Some text" > test.svg
$ qr --factory=svg "Some text" > test.svg
$ qr --factory=svg-fragment "Some text" > test.svg
```
Or in Python:

```python
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
```

Two other related factories are available that work the same, but also
fill the background of the SVG with white:

```python
qrcode.image.svg.SvgFillImage
qrcode.image.svg.SvgPathFillImage
```

## Pure Python PNG

Install the following two packages:

```bash
$ pip install git+git://github.com/ojii/pymaging.git#egg=pymaging
$ pip install git+git://github.com/ojii/pymaging-png.git#egg=pymaging-png
```
From your command line:
```bash
$ qr --factory=pymaging "Some text" > test.png
```
Or in Python:

```python
import qrcode
from qrcode.image.pure import PymagingImage
img = qrcode.make('Some data here', image_factory=PymagingImage)
```
