# Needed on case-insensitive filesystems
from __future__ import absolute_import

# Try to import PIL in either of the two ways it can be installed.
try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    import Image
    import ImageDraw

import qrcode.image.base


class PilImage(qrcode.image.base.BaseImage):
    """
    PIL image builder, default format is PNG.
    """
    kind = "PNG"

    def new_image(self, **kwargs):
        back_color = kwargs.get("back_color", "white")
        fill_color = kwargs.get("fill_color", "black")

        if fill_color.lower() != "black" or back_color.lower() != "white":
            if back_color.lower() == "transparent":
                mode = "RGBA"
                back_color = None
            else:
                mode = "RGB"
        else:
            mode = "1"
            # L mode (1 mode) color = (r*299 + g*587 + b*114)//1000
            if fill_color.lower() == "black": fill_color = 0
            if back_color.lower() == "white": back_color = 255

        img = Image.new(mode, (self.pixel_size, self.pixel_size), back_color)
        self.fill_color = fill_color
        self._idr = ImageDraw.Draw(img)
        return img

    def drawrect(self, row, col):
        box = self.pixel_box(row, col)
        self._idr.rectangle(box, fill=self.fill_color)

    def drawdiamond(self, row, col, version):
        """Draws a diamond instead of square in the qrcode
        
        Arguments:
            row {index} -- [Row index]
            col {index} -- [Collum index]
        """
        def _isPositionIndicator(version, row, col):
            """checks if the coordinate is the so called position indicator, these have to be a solid line

            Arguments:
                version {int} -- version number
                row {int} -- row
                col {int} -- collum
        
            Returns:
                bool -- wether its a position indicator
            """
            size = 21 + version*4
            if row <= 6: 
                if col < 7:
                    return True
            if row >= (size - 11):
                if col < 7: 
                    return True
            if row < 7:
                if col > (size - 12):
                    return True


        x = (col+self.border) * self.box_size
        y = (row+self.border) * self.box_size
        diamondSize = int(self.box_size/3) 
        boxSize = int(self.box_size/2)
        if _isPositionIndicator(version, row, col):
            self._idr.rectangle((x-boxSize, y-boxSize, x+boxSize, y+boxSize), fill=self.fill_color)

        else:
            self._idr.polygon([x-diamondSize, y, x, y+diamondSize, x+diamondSize, y, x, y-diamondSize], fill=self.fill_color)

    def save(self, stream, format=None, **kwargs):
        kind = kwargs.pop("kind", self.kind)
        if format is None:
            format = kind
        self._img.save(stream, format=format, **kwargs)

    def __getattr__(self, name):
        return getattr(self._img, name)
