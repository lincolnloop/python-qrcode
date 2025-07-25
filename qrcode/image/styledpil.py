from __future__ import annotations

import warnings
from typing import overload

import deprecation
from PIL import Image

import qrcode.image.base
from qrcode.image.styles.colormasks import QRColorMask, SolidFillColorMask
from qrcode.image.styles.moduledrawers.pil import SquareModuleDrawer


class StyledPilImage(qrcode.image.base.BaseImageWithDrawer):
    """
    Styled PIL image builder, default format is PNG.

    This differs from the PilImage in that there is a module_drawer, a
    color_mask, and an optional image

    The module_drawer should extend the QRModuleDrawer class and implement the
    drawrect_context(self, box, active, context), and probably also the
    initialize function. This will draw an individual "module" or square on
    the QR code.

    The color_mask will extend the QRColorMask class and will at very least
    implement the get_fg_pixel(image, x, y) function, calculating a color to
    put on the image at the pixel location (x,y) (more advanced functionality
    can be gotten by instead overriding other functions defined in the
    QRColorMask class)

    The Image can be specified either by path or with a Pillow Image, and if it
    is there will be placed in the middle of the QR code. No effort is done to
    ensure that the QR code is still legible after the image has been placed
    there; Q or H level error correction levels are recommended to maintain
    data integrity A resampling filter can be specified (defaulting to
    PIL.Image.Resampling.LANCZOS) for resizing; see PIL.Image.resize() for possible
    options for this parameter.
    The image size can be controlled by `embedded_image_ratio` which is a ratio
    between 0 and 1 that's set in relation to the overall width of the QR code.
    """

    kind = "PNG"

    needs_processing = True
    color_mask: QRColorMask
    default_drawer_class = SquareModuleDrawer

    def __init__(self, *args, **kwargs):
        self.color_mask = kwargs.get("color_mask", SolidFillColorMask())

        if kwargs.get("embeded_image_path") or kwargs.get("embeded_image"):
            warnings.warn(
                "The 'embeded_*' parameters are deprecated. Use 'embedded_image_path' "
                "or 'embedded_image' instead. The 'embeded_*' parameters will be "
                "removed in v9.0.",
                category=DeprecationWarning,
                stacklevel=2,
            )

        # allow embeded_ parameters with typos for backwards compatibility
        embedded_image_path = kwargs.get(
            "embedded_image_path", kwargs.get("embeded_image_path")
        )
        self.embedded_image = kwargs.get("embedded_image", kwargs.get("embeded_image"))
        self.embedded_image_ratio = kwargs.get(
            "embedded_image_ratio", kwargs.get("embeded_image_ratio", 0.25)
        )
        self.embedded_image_resample = kwargs.get(
            "embedded_image_resample",
            kwargs.get("embeded_image_resample", Image.Resampling.LANCZOS),
        )
        if not self.embedded_image and embedded_image_path:
            self.embedded_image = Image.open(embedded_image_path)

        # the paint_color is the color the module drawer will use to draw upon
        # a canvas During the color mask process, pixels that are paint_color
        # are replaced by a newly-calculated color
        self.paint_color = tuple(0 for i in self.color_mask.back_color)
        if self.color_mask.has_transparency:
            self.paint_color = (*self.color_mask.back_color[:3], 255)

        super().__init__(*args, **kwargs)

    @overload
    def drawrect(self, row, col):
        """
        Not used.
        """

    def new_image(self, **kwargs):
        mode = (
            "RGBA"
            if (
                self.color_mask.has_transparency
                or (self.embedded_image and "A" in self.embedded_image.getbands())
            )
            else "RGB"
        )
        # This is the background color. Should be white or whiteish
        back_color = self.color_mask.back_color

        return Image.new(mode, (self.pixel_size, self.pixel_size), back_color)

    def init_new_image(self):
        self.color_mask.initialize(self, self._img)
        super().init_new_image()

    def process(self):
        self.color_mask.apply_mask(self._img)
        if self.embedded_image:
            self.draw_embedded_image()

    @deprecation.deprecated(
        deprecated_in="9.0",
        removed_in="8.3",
        current_version="8.2",
        details="Use draw_embedded_image() instead",
    )
    def draw_embeded_image(self):
        return self.draw_embedded_image()

    def draw_embedded_image(self):
        if not self.embedded_image:
            return
        total_width, _ = self._img.size
        total_width = int(total_width)
        logo_width_ish = int(total_width * self.embedded_image_ratio)
        logo_offset = (
            int((int(total_width / 2) - int(logo_width_ish / 2)) / self.box_size)
            * self.box_size
        )  # round the offset to the nearest module
        logo_position = (logo_offset, logo_offset)
        logo_width = total_width - logo_offset * 2
        region = self.embedded_image
        region = region.resize((logo_width, logo_width), self.embedded_image_resample)
        if "A" in region.getbands():
            self._img.alpha_composite(region, logo_position)
        else:
            self._img.paste(region, logo_position)

    def save(self, stream, format=None, **kwargs):
        if format is None:
            format = kwargs.get("kind", self.kind)
        kwargs.pop("kind", None)
        self._img.save(stream, format=format, **kwargs)

    def __getattr__(self, name):
        return getattr(self._img, name)
