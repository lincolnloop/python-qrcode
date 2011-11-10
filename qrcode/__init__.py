from qrcode.main import QRCode
from qrcode.constants import *


def run_example():
    qr = QRCode()
    qr.addData("http://www.lincolnloop.com")
    qr.make()

    im = qr.makeImage()
    im.show()


if __name__ == '__main__':
    run_example()
