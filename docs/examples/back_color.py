'''
Create a QR Code with a specific QRCode make() function parameter: back_color.
Usage:
    python back_color.py [data] [back_color]
'''

import sys
import qrcode

assert len(sys.argv) == 3, 'Usage: python back_color.py [data] [back_color]'

DATA = sys.argv[1]

# string or tuple[int, int, int]
BACK_COL = sys.argv[2]
if '(' in BACK_COL and ')' in BACK_COL:
    BACK_COL = eval(BACK_COL)

qr = qrcode.QRCode()
qr.add_data(DATA)
qr.make(fit=True)
img = qr.make_image(back_color=BACK_COL)
img.save("example.png")
