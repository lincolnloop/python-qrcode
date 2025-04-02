'''
Create a QR Code with a specific QRCode class parameter: image_factory.
Usage:
    python image_factory.py [data] [image_factory]
'''

import sys
import qrcode
import qrcode.image.svg
import qrcode.image.pure
import qrcode.image.styledpil

assert len(sys.argv) == 3, 'Usage: python image_factory.py [data] [image_factory]'

DATA = sys.argv[1]
IMG_FAC = {
    'SvgImage': qrcode.image.svg.SvgImage,
    'SvgFragmentImage': qrcode.image.svg.SvgFragmentImage,
    'SvgPathImage': qrcode.image.svg.SvgPathImage,
    'SvgFillImage': qrcode.image.svg.SvgFillImage,
    'SvgPathFillImage': qrcode.image.svg.SvgPathFillImage,
    'PyPNGImage': qrcode.image.pure.PyPNGImage,
    'StyledPilImag': qrcode.image.styledpil.StyledPilImage
}[sys.argv[2]]

qr = qrcode.QRCode(image_factory=IMG_FAC)
qr.add_data(DATA)
qr.make(fit=True)
img = qr.make_image()
ext = "svg" if "Svg" in sys.argv[2] else "png"
img.save(f"example.{ext}")
