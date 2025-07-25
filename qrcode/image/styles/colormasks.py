import math

from PIL import Image


class QRColorMask:
    """
    QRColorMask is used to color in the QRCode.

    By the time apply_mask is called, the QRModuleDrawer of the StyledPilImage
    will have drawn all of the modules on the canvas (the color of these
    modules will be mostly black, although antialiasing may result in
    gradients) In the base class, apply_mask is implemented such that the
    background color will remain, but the foreground pixels will be replaced by
    a color determined by a call to get_fg_pixel. There is additional
    calculation done to preserve the gradient artifacts of antialiasing.

    All QRColorMask objects should be careful about RGB vs RGBA color spaces.

    For examples of what these look like, see doc/color_masks.png
    """

    back_color = (255, 255, 255)
    has_transparency = False
    paint_color = back_color

    def initialize(self, styledPilImage, image):
        self.paint_color = styledPilImage.paint_color

    def apply_mask(self, image, use_cache=False):
        width, height = image.size
        pixels = image.load()
        fg_color_cache = {} if use_cache else None
        for x in range(width):
            for y in range(height):
                current_color = pixels[x, y]
                if current_color == self.back_color:
                    continue
                if use_cache and current_color in fg_color_cache:
                    pixels[x, y] = fg_color_cache[current_color]
                    continue
                norm = self.extrap_color(
                    self.back_color, self.paint_color, current_color
                )
                if norm is not None:
                    new_color = self.interp_color(
                        self.get_bg_pixel(image, x, y),
                        self.get_fg_pixel(image, x, y),
                        norm,
                    )
                    pixels[x, y] = new_color

                    if use_cache:
                        fg_color_cache[current_color] = new_color
                else:
                    pixels[x, y] = self.get_bg_pixel(image, x, y)

    def get_fg_pixel(self, image, x, y):
        raise NotImplementedError("QRModuleDrawer.paint_fg_pixel")

    def get_bg_pixel(self, image, x, y):
        return self.back_color

    # The following functions are helpful for color calculation:

    # interpolate a number between two numbers
    def interp_num(self, n1, n2, norm):
        return int(n2 * norm + n1 * (1 - norm))

    # interpolate a color between two colorrs
    def interp_color(self, col1, col2, norm):
        return tuple(self.interp_num(col1[i], col2[i], norm) for i in range(len(col1)))

    # find the interpolation coefficient between two numbers
    def extrap_num(self, n1, n2, interped_num):
        if n2 == n1:
            return None
        return (interped_num - n1) / (n2 - n1)

    # find the interpolation coefficient between two numbers
    def extrap_color(self, col1, col2, interped_color):
        normed = []
        for c1, c2, ci in zip(col1, col2, interped_color):
            extrap = self.extrap_num(c1, c2, ci)
            if extrap is not None:
                normed.append(extrap)
        if not normed:
            return None
        return sum(normed) / len(normed)


class SolidFillColorMask(QRColorMask):
    """
    Just fills in the background with one color and the foreground with another
    """

    def __init__(self, back_color=(255, 255, 255), front_color=(0, 0, 0)):
        self.back_color = back_color
        self.front_color = front_color
        self.has_transparency = len(self.back_color) == 4

    def apply_mask(self, image):
        if self.back_color == (255, 255, 255) and self.front_color == (0, 0, 0):
            # Optimization: the image is already drawn by QRModuleDrawer in
            # black and white, so if these are also our mask colors we don't
            # need to do anything. This is much faster than actually applying a
            # mask.
            pass
        else:
            # There's probably a way to use PIL.ImageMath instead of doing
            # the individual pixel comparisons that the base class uses, which
            # would be a lot faster. (In fact doing this would probably remove
            # the need for the B&W optimization above.)
            QRColorMask.apply_mask(self, image, use_cache=True)

    def get_fg_pixel(self, image, x, y):
        return self.front_color


class RadialGradiantColorMask(QRColorMask):
    """
    Fills in the foreground with a radial gradient from the center to the edge
    """

    def __init__(
        self, back_color=(255, 255, 255), center_color=(0, 0, 0), edge_color=(0, 0, 255)
    ):
        self.back_color = back_color
        self.center_color = center_color
        self.edge_color = edge_color
        self.has_transparency = len(self.back_color) == 4

    def get_fg_pixel(self, image, x, y):
        width, _ = image.size
        normedDistanceToCenter = math.sqrt(
            (x - width / 2) ** 2 + (y - width / 2) ** 2
        ) / (math.sqrt(2) * width / 2)
        return self.interp_color(
            self.center_color, self.edge_color, normedDistanceToCenter
        )


class SquareGradiantColorMask(QRColorMask):
    """
    Fills in the foreground with a square gradient from the center to the edge
    """

    def __init__(
        self, back_color=(255, 255, 255), center_color=(0, 0, 0), edge_color=(0, 0, 255)
    ):
        self.back_color = back_color
        self.center_color = center_color
        self.edge_color = edge_color
        self.has_transparency = len(self.back_color) == 4

    def get_fg_pixel(self, image, x, y):
        width, _ = image.size
        normedDistanceToCenter = max(abs(x - width / 2), abs(y - width / 2)) / (
            width / 2
        )
        return self.interp_color(
            self.center_color, self.edge_color, normedDistanceToCenter
        )


class HorizontalGradiantColorMask(QRColorMask):
    """
    Fills in the foreground with a gradient sweeping from the left to the right
    """

    def __init__(
        self, back_color=(255, 255, 255), left_color=(0, 0, 0), right_color=(0, 0, 255)
    ):
        self.back_color = back_color
        self.left_color = left_color
        self.right_color = right_color
        self.has_transparency = len(self.back_color) == 4

    def get_fg_pixel(self, image, x, y):
        width, _ = image.size
        return self.interp_color(self.left_color, self.right_color, x / width)


class VerticalGradiantColorMask(QRColorMask):
    """
    Fills in the forefround with a gradient sweeping from the top to the bottom
    """

    def __init__(
        self, back_color=(255, 255, 255), top_color=(0, 0, 0), bottom_color=(0, 0, 255)
    ):
        self.back_color = back_color
        self.top_color = top_color
        self.bottom_color = bottom_color
        self.has_transparency = len(self.back_color) == 4

    def get_fg_pixel(self, image, x, y):
        width, _ = image.size
        return self.interp_color(self.top_color, self.bottom_color, y / width)


class ImageColorMask(QRColorMask):
    """
    Fills in the foreground with pixels from another image, either passed by
    path or passed by image object.
    """

    def __init__(
        self, back_color=(255, 255, 255), color_mask_path=None, color_mask_image=None
    ):
        self.back_color = back_color
        if color_mask_image:
            self.color_img = color_mask_image
        else:
            self.color_img = Image.open(color_mask_path)

        self.has_transparency = len(self.back_color) == 4

    def initialize(self, styledPilImage, image):
        self.paint_color = styledPilImage.paint_color
        self.color_img = self.color_img.resize(image.size)

    def get_fg_pixel(self, image, x, y):
        width, _ = image.size
        return self.color_img.getpixel((x, y))
