from PyQRNative import *

qr = QRCode(10, QRErrorCorrectLevel.L)
qr.addData("http://www.baconsalt.com")
qr.make()

im = qr.makeImage()

im.show()