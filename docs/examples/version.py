'''
Create a QR Code with a specific QRCode class parameter: version.
Usage:
    python version.py [data] [version]
'''

import sys
import qrcode
import qrcode.image.styles

assert len(sys.argv) == 3, 'Usage: python version.py [data] [version]'

DATA = sys.argv[1]
VERSION = sys.argv[2]
try: VERSION = int(VERSION)
except ValueError: VERSION = None

qr = qrcode.QRCode(version=VERSION)
qr.add_data(DATA)
if VERSION is None:
    qr.make(fit=True)
img = qr.make_image()
img.save("example.png")
