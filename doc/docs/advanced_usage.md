For more control, use the `QRCode` class. For example:

``` {.python}
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
```

The `version` parameter is an integer from 1 to 40 that controls the
size of the QR Code (the smallest, version 1, is a 21x21 matrix). Set to
`None` and use the `fit` parameter when making the code to determine
this automatically.

`fill_color` and `back_color` can change the background and the painting
color of the QR, when using the default image factory.

The `error_correction` parameter controls the error correction used for
the QR Code. The following four constants are made available on the
`qrcode` package:

`ERROR_CORRECT_L`

About 7% or less errors can be corrected.

`ERROR_CORRECT_M` (default)

About 15% or less errors can be corrected.

`ERROR_CORRECT_Q`

About 25% or less errors can be corrected.

`ERROR_CORRECT_H`.

About 30% or less errors can be corrected.

The `box_size` parameter controls how many pixels each \"box\" of the QR
code is.

The `border` parameter controls how many boxes thick the border should
be (the default is 4, which is the minimum according to the specs).

