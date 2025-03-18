'''
Create a QR Code with a specific QRCode class parameter: fill_color.
Usage:
    python fill_color.py [data] [fill_color]
'''

import sys
import qrcode

assert len(sys.argv) == 3, 'Usage: python fill_color.py [data] [fill_color]'

DATA = sys.argv[1]

# string or tuple[int, int, int]
fill_color = sys.argv[2]
if '(' in fill_color and ')' in fill_color:
    fill_color = eval(fill_color)

qr = qrcode.QRCode()
qr.add_data(DATA)
qr.make(fit=True)
img = qr.make_image(fill_color=fill_color)
img.save("example.png")
