'''
Create a QR Code with a specific QRCode class parameter: back_color.
Usage:
    python back_color.py [data] [back_color]
'''

import sys
import qrcode

assert len(sys.argv) == 3, 'Usage: python back_color.py [data] [back_color]'

DATA = sys.argv[1]

# string or tuple[int, int, int]
back_color = sys.argv[2]
if '(' in back_color and ')' in back_color:
    back_color = eval(back_color)

qr = qrcode.QRCode()
qr.add_data(DATA)
qr.make(fit=True)
img = qr.make_image(back_color=back_color)
img.save("example.png")
