import sys
from qrcode.main import *

outFile = 'smaple'
qr = QRCode(
        border=2,
        true_color=(82, 43, 188),
        image_factory='pil',
        extended_colors = {
            "padding":(125, 112, 14),
            "ec":(178, 44, 3),
            "timing":(0, 66, 150),
            "prob":(52, 20, 188),
            "type":(0, 51, 150)},
        image_factory_modifiers = {
            "character":"  ",
            "shape":"circle" })

qr.add_data("Red\n", (143, 0, 4))
qr.add_data("Green", (48, 107, 23))

qr.make()
img = qr.make_image()
img.save(outFile + '.png')

qr.set_image_factory('svg')
img = qr.make_image()
img.save(outFile + '.svg')

qr.set_image_factory('tty')
img = qr.make_image()
img.save(sys.stdout)

qr.set_image_factory('ascii')
img = qr.make_image()
sys.stdout.write('\n' * 3)
img.save(sys.stdout)
