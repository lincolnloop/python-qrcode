from dxfwrite import DXFEngine as dxf

import qrcode.image.base


class DxfImage(qrcode.image.base.BaseImage):
    """
    DXF image builder
    """
    kind = "DXF"
    allowed_kinds = ("DXF",)

    def new_image(self, **kwargs):
        img = dxf.drawing()
        img.header['$EXTMIN'] = (0, -self.pixel_size, 0)
        img.header['$EXTMAX'] = (self.pixel_size, 0, 0)
        box = dxf.block(name="box")
        box.add(dxf.rectangle((0, 0), self.box_size, self.box_size, color=None, bgcolor=0))
        img.blocks.add(box)
        return img

    def drawrect(self, row, col):
        self._img.add(dxf.insert("box", insert=((col + self.border) * self.box_size, (-1 - row - self.border) * self.box_size)))

    def save(self, stream, kind=None):
        self.check_kind(kind=kind)
        
        self._img.saveas(stream)
