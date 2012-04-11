class BaseImage(object):
    def __init__(self, border, width, box_size):
        self.kind = None
        self.border = border
        self.width = width
        self.box_size = box_size

    def drawrect(self, row, col):
        raise NotImplementedError("BaseImage.drawrect")

    def save(self, stream, kind=None):
        raise NotImplementedError("BaseImage.save")
