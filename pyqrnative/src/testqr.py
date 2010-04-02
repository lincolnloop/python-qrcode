from PyQRNative import *

qr = QRCode(20, QRErrorCorrectLevel.L)
qr.addData("http://www.baconsalt.com")
qr.make()

im = qr.makeImage()

im.show()