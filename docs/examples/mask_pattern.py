'''
Create a QR Code with a specific QRCode class parameter: mask_pattern.
Usage:
    python mask_pattern.py [data] [mask_pattern]
'''

import sys
import qrcode
import qrcode.image.svg
import qrcode.image.pure
import qrcode.image.styledpil

assert len(sys.argv) == 3, 'Usage: python mask_pattern.py [data] [mask_pattern]'

DATA = sys.argv[1]
MASK_PAT = int(sys.argv[2])

qr = qrcode.QRCode(mask_pattern=MASK_PAT)
qr.add_data(DATA)
qr.make(fit=True)
img = qr.make_image()
img.save(f"example.png")
