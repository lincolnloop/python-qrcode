'''
Create a QR Code with a specific QRCode class parameter: error_correction.
Usage:
    python error_correction.py [data] [error_correction]
'''

import sys
import qrcode

assert len(sys.argv) == 3, 'Usage: python error_correction.py [data] [error_correction]'

DATA = sys.argv[1]
ERR_COR = {
    'ERROR_CORRECT_L': qrcode.ERROR_CORRECT_L,
    'ERROR_CORRECT_M': qrcode.ERROR_CORRECT_M,
    'ERROR_CORRECT_Q': qrcode.ERROR_CORRECT_Q,
    'ERROR_CORRECT_H': qrcode.ERROR_CORRECT_H,
}[sys.argv[2]]

qr = qrcode.QRCode(error_correction=ERR_COR)
qr.add_data(DATA)
qr.make(fit=True)
img = qr.make_image()
img.save("example.png")
