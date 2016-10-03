# Needed on case-insensitive filesystems
from __future__ import absolute_import

from qrcode.image.base import BaseImage

class TTYImage(BaseImage):
    def __init__(self, *args, **kwargs):
        super(TTYImage, self).__init__(*args, **kwargs)
        if 'character' in kwargs:
            self.character = kwargs['character']
        else:
            self.character = ' '
        if 'false_character' in kwargs:
            self.false_character = kwargs['false_character']
        else:
            self.false_character = ' ' * len(self.character)
        self.data = []
        for l in xrange(self.width):
            self.data.append([0]*self.width)

    def output_border(self, stream):
        for i in xrange(self.border):
            stream.write('\x1b[30;47m' + (self.false_character * (self.border * 2 + self.width)))
            stream.write('\n')

    def save(self, stream, format=None, **kwargs):
        if not stream.isatty():
            raise OSError("Not a tty")

        self.output_border(stream)
        for line in self.data:
            stream.write(self.false_character * self.border)
            for pixel in line:
                if None == pixel or (255, 255, 255) == pixel:
                    stream.write("\x1b[30;47m" + self.false_character)
                else:
                    stream.write("\x1b[0m" + self.character)
            stream.write('\x1b[30;47m' + (self.false_character * self.border))
            stream.write('\n')
        self.output_border(stream)
        stream.write('\x1b[0m')

    def drawrect(self, row, col, color):
        self.data[row][col] = color
