#!/usr/bin/python
import qrcode
from qrcode.image.svg import SvgForPlotters

box_size = 10
border = 4

qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=box_size, border=border)
qr.add_data(b"Engrave this code on steel, let it rust and then only use sandpaper to clean the surface before applying a transparent protective coating.")

img_1 = qr.make_image(image_factory=SvgForPlotters, stroke_width=.02)
img_1.save('out.svg')
