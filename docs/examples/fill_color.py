'''
Create a QR Code with a specific QRCode make() function parameter: fill_color.
Usage:
    python fill_color.py [data] [fill_color]
'''

import sys
import qrcode

assert len(sys.argv) == 3, 'Usage: python fill_color.py [data] [fill_color]'

DATA = sys.argv[1]

# string or tuple[int, int, int]
FILL_COL = sys.argv[2]
if '(' in FILL_COL and ')' in FILL_COL:
    FILL_COL = eval(FILL_COL)

qr = qrcode.QRCode()
qr.add_data(DATA)
qr.make(fit=True)
img = qr.make_image(fill_color=FILL_COL)
img.save("example.png")
