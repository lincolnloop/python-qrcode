from __future__ import absolute_import
import os
import tempfile

import pygame
import qrcode.image.base


class PygameSurface(qrcode.image.base.BaseImage):

    kind = 'PNG'

    def new_image(self, **kwargs):
        back_color = pygame.Color(kwargs.get("back_color", "white"))
        fill_color = pygame.Color(kwargs.get("fill_color", "black"))
        self.fill_color = fill_color
        surface = pygame.Surface((self.pixel_size, self.pixel_size))
        surface.fill(back_color)
        return surface

    def drawrect(self, row, col):
        rect = pygame.Rect(self.pixel_box(row, col)[0], (self.box_size,self.box_size))
        self._img.fill(color=self.fill_color, rect=rect)

    def save(self, stream, format=None, **kwargs):
        if format is None:
            format = kwargs.pop("kind", self.kind)
        tmpfd, tmpname = tempfile.mkstemp(suffix='.'+kind)
        pygame.image.save(self._img, tmpname)
        tmpfp = os.fdopen(tmpfd)
        stream.write(tmpfp.read())
        tmpfp.close()
        os.remove(tmpname)
