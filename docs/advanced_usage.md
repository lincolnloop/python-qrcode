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

### version
An integer from 1 to 40, that controlls the size of QR Code. Set to `None` and use the `fit` parameter when making the code to determine this automatically.
|version|size|max content length|
|:-:|:-:|:-:|
|1|21x21|4 ASCII chars|
|2|25x25|9 ASCII chars|
|3|29x29|17 ASCII chars|
|4|33x33|50 ASCII chars|
|10|57x57|174 ASCII chars|
|25|117x117|1269 ASCII chars|
|40|177x177|1852 ASCII chars|

![](./examples/version.png)

[Check out the example code here](./examples/version.py)

### error_correction
Controls how much errors can be corrected during scanning of the QR Code.
|value|percentage of errors corrected|
|:-:|:-:|
|ERROR_CORRECT_L|7%|
|ERROR_CORRECT_M|15%|
|ERROR_CORRECT_Q|25%|
|ERROR_CORRECT_H|30%|

![](./examples/error_correction.png)

[Check out the example code here](./examples/error_correction.py)