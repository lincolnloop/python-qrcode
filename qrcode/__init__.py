from qrcode.main import QRCode
from qrcode.constants import *


def run_example(*args, **kwargs):
    qr = QRCode(*args, **kwargs)
    qr.addData("http://www.lincolnloop.com")
    qr.make()

    im = qr.makeImage()
    im.show()


if __name__ == '__main__':
    run_example()
