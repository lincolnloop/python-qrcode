# Needed on case-insensitive filesystems
from __future__ import absolute_import

from qrcode.image.tty import TTYImage
import os

class ASCIIImage(TTYImage):
    def __init__(self, *args, **kwargs):
        super(ASCIIImage, self).__init__(*args, **kwargs)
        if 'foreground' in kwargs:
            self.foreground = kwargs['foreground']
        else:
            self.foreground = False

    def output_border(self, stream, BACKGROUND_COLOR):
        for i in xrange(self.border):
            stream.write('\x1b[' + BACKGROUND_COLOR + (self.false_character * ((self.border * 2) + self.width)))
            stream.write(os.linesep)

    def save(self, stream, format=None, **kwargs):
        if not stream.isatty():
            raise OSError("Not a tty")

        import sys
        if sys.version_info < (2, 7):
            # On Python versions 2.6 and earlier, stdout tries to encode
            # strings using ASCII rather than stdout.encoding, so use this
            # workaround.
            import codecs
            out = codecs.getwriter(sys.stdout.encoding)(sys.stdout)
        else:
            out = sys.stdout

        BACKGROUND_COLOR = '48;2;255;255;255m'
        self.output_border(stream, BACKGROUND_COLOR)
        for line in self.data:
            stream.write('\x1b[' + BACKGROUND_COLOR + (self.false_character * self.border))
            for pixel in line:
                if None == pixel:
                    stream.write('\x1b[' + BACKGROUND_COLOR + self.false_character)
                else:
                    if self.foreground:
                        stream.write("\x1b[38;2;%d;%d;%d;" % (pixel) + BACKGROUND_COLOR + self.character)
                    else:
                        stream.write("\x1b[38;2;255;255;255;48;2;%d;%d;%dm" % (pixel) + self.character)
            stream.write('\x1b[' + BACKGROUND_COLOR + (self.false_character * self.border))
            stream.write(os.linesep)
        stream.write('\x1b[0m')
        self.output_border(stream, BACKGROUND_COLOR)

