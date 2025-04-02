'''
Create a QR Code with a specific QRCode make() function parameter: embeded_image_path.
Usage:
    python embeded_image_path.py [data] [embeded_image_path]
'''

import sys
import qrcode
import qrcode.image.styledpil

assert len(sys.argv) == 3, 'Usage: python embeded_image_path.py [data] [embeded_image_path]'

DATA = sys.argv[1]
EM_IMG_PATH = sys.argv[2]
if EM_IMG_PATH == 'None':
    EM_IMG_PATH = None

qr = qrcode.QRCode(
    error_correction=qrcode.ERROR_CORRECT_H,
    image_factory=qrcode.image.styledpil.StyledPilImage
)
qr.add_data(DATA)
qr.make(fit=True)
img = qr.make_image(embeded_image_path=EM_IMG_PATH)
img.save(f"example.png")
