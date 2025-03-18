'''
Create a QR Code with a specific QRCode make() function parameter: color_mask.
Usage:
    python color_mask.py [data] [color_mask]
'''

import sys
import qrcode
import qrcode.image.styledpil
import qrcode.image.styles.colormasks

RED = (255, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

assert len(sys.argv) == 3, 'Usage: python color_mask.py [data] [color_mask]'

DATA = sys.argv[1]
COL_MASK = {
    'SolidFillColorMask': qrcode.image.styles.colormasks.SolidFillColorMask(back_color=WHITE, front_color=BLACK),
    'RadialGradiantColorMask': qrcode.image.styles.colormasks.RadialGradiantColorMask(back_color=WHITE, center_color=RED, edge_color=GREEN),
    'SquareGradiantColorMask': qrcode.image.styles.colormasks.SquareGradiantColorMask(back_color=WHITE, center_color=RED, edge_color=GREEN),
    'HorizontalGradiantColorMask': qrcode.image.styles.colormasks.HorizontalGradiantColorMask(back_color=WHITE, left_color=RED, right_color=GREEN),
    'VerticalGradiantColorMask': qrcode.image.styles.colormasks.VerticalGradiantColorMask(back_color=WHITE, top_color=RED, bottom_color=GREEN),
    'ImageColorMask': qrcode.image.styles.colormasks.ImageColorMask(color_mask_path='stars.png'),
}[sys.argv[2]]

qr = qrcode.QRCode(
    error_correction=qrcode.ERROR_CORRECT_H,
    image_factory=qrcode.image.styledpil.StyledPilImage
)
qr.add_data(DATA)
qr.make(fit=True)
img = qr.make_image(color_mask=COL_MASK)
img.save(f"example.png")
