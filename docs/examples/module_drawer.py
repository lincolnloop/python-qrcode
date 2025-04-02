'''
Create a QR Code with a specific QRCode make() function parameter: module_drawer.
Usage:
    python module_drawer.py [data] [module_drawer]
'''

import sys
import qrcode
import qrcode.image.svg
import qrcode.image.styledpil
import qrcode.image.styles.moduledrawers.svg

assert len(sys.argv) == 3, 'Usage: python module_drawer.py [data] [module_drawer]'

DATA = sys.argv[1]
MOD_DRAW, FACTORY = {
    'SvgSquareDrawer': (qrcode.image.styles.moduledrawers.svg.SvgSquareDrawer(), qrcode.image.svg.SvgFillImage),
    'SvgCircleDrawer': (qrcode.image.styles.moduledrawers.svg.SvgCircleDrawer(), qrcode.image.svg.SvgFillImage),
    'SvgPathSquareDrawer': (qrcode.image.styles.moduledrawers.svg.SvgPathSquareDrawer(), qrcode.image.svg.SvgPathFillImage),
    'SvgPathCircleDrawer': (qrcode.image.styles.moduledrawers.svg.SvgPathCircleDrawer(), qrcode.image.svg.SvgPathFillImage),
    'SquareModuleDrawer': (qrcode.image.styles.moduledrawers.SquareModuleDrawer(), qrcode.image.styledpil.StyledPilImage),
    'GappedSquareModuleDrawer': (qrcode.image.styles.moduledrawers.GappedSquareModuleDrawer(), qrcode.image.styledpil.StyledPilImage),
    'CircleModuleDrawer': (qrcode.image.styles.moduledrawers.CircleModuleDrawer(), qrcode.image.styledpil.StyledPilImage),
    'RoundedModuleDrawer': (qrcode.image.styles.moduledrawers.RoundedModuleDrawer(), qrcode.image.styledpil.StyledPilImage),
    'VerticalBarsDrawer': (qrcode.image.styles.moduledrawers.VerticalBarsDrawer(), qrcode.image.styledpil.StyledPilImage),
    'HorizontalBarsDrawer': (qrcode.image.styles.moduledrawers.HorizontalBarsDrawer(), qrcode.image.styledpil.StyledPilImage),
}[sys.argv[2]]

qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_H, image_factory=FACTORY)
qr.add_data(DATA)
qr.make(fit=True)
img = qr.make_image(module_drawer=MOD_DRAW)
ext = "svg" if "Svg" in sys.argv[2] else "png"
img.save(f"example.{ext}")
