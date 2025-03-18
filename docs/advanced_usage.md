# Advanced Usage
Using the [`QRCode`](../qrcode/main.py#L77) class.
```python
class QRCode(
    version: Any | None = None,
    error_correction: int = ERROR_CORRECT_M,
    box_size: int = 10,
    border: int = 4,
    image_factory: Any | None = None,
    mask_pattern: Any | None = None
)
```

## Parameters of `QRCode`

### `version`
Any integer from 1 to 40. It controlls the size of QR Code. Set to `None` and use the `fit` parameter when making the code to determine this automatically.
|version|size|max content length|
|:-:|:-:|:-:|
|`1`|21x21|4 ASCII chars|
|`2`|25x25|9 ASCII chars|
|`3`|29x29|17 ASCII chars|
|`4`|33x33|50 ASCII chars|
|`10`|57x57|174 ASCII chars|
|`25`|117x117|1269 ASCII chars|
|`40`|177x177|1852 ASCII chars|

[Check out the example code here](./examples/version.py)

![](./examples/version.png)


### `error_correction`
Controls how much errors can be corrected during scanning of the QR Code.
|value|percentage of errors corrected|
|:-:|:-:|
|`ERROR_CORRECT_L`|7%|
|`ERROR_CORRECT_M`|15%|
|`ERROR_CORRECT_Q`|25%|
|`ERROR_CORRECT_H`|30%|

[Check out the example code here](./examples/error_correction.py)

![](./examples/error_correction.png)


### `box_size`
Controls how many pixels each "box" of the QR code is.


### `border`
Controls how many boxes thick the border should be. The default is 4, which is the minimum according to the specs.


### `image_factory`
You can encode as SVG, or use a new pure Python image processor to encode to PNG images.

To apply styles to the QRCode, use the StyledPilImage or one of the standard SVG image factories. These accept an optional `module_drawer` parameter.

To apply color mask to the QRCode, use the StyledPilImage. It accepts an optional `color_mask` and `embeded_image_path`.

|value|usage|edit style|edit color mask|
|:-:|:-|:-:|:-:|
|`SvgImage`|Simple factory, just a set of rects|&check;||
|`SvgFragmentImage`|Fragment factory (also just a set of rects)|&check;||
|`SvgPathImage`|Combined path factory, fixes white space that may occur when zooming|&check;||
|`SvgFillImage`|Similar to `SvgImage`, but also fill the background with white|&check;||
|`SvgPathFillImage`|Similar to `SvgPathImage`, but also fill the background with white|&check;||
|`PyPNGImage`|PNG encoder that uses pypng|||
|`StyledPilImag`|PNG encoder that uses Pillow|&check;|&check;|

[Check out the example code here](./examples/image_factory.py)

![](./examples/image_factory.png)
