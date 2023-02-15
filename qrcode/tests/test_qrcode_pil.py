import io
import os
import unittest

import pytest

import qrcode
import qrcode.util
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles import colormasks, moduledrawers
from qrcode.tests.consts import UNICODE_TEXT, RED, WHITE, BLACK

Image = pytest.importorskip("PIL.Image", reason="PIL is not installed")


class PILQRCodeTests(unittest.TestCase):

    def test_render_pil(self):
        qr = qrcode.QRCode()
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image()
        img.save(io.BytesIO())
        assert isinstance(img.get_image(), Image.Image)

    def test_render_pil_with_transparent_background(self):
        qr = qrcode.QRCode()
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image(back_color="TransParent")
        img.save(io.BytesIO())

    def test_render_pil_with_red_background(self):
        qr = qrcode.QRCode()
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image(back_color="red")
        img.save(io.BytesIO())

    def test_render_pil_with_rgb_color_tuples(self):
        qr = qrcode.QRCode()
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image(back_color=(255, 195, 235), fill_color=(55, 95, 35))
        img.save(io.BytesIO())

    def test_render_with_pattern(self):
        qr = qrcode.QRCode(mask_pattern=3)
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image()
        img.save(io.BytesIO())

    def test_render_styled_Image(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image(image_factory=StyledPilImage)
        img.save(io.BytesIO())

    def test_render_styled_with_embeded_image(self):
        embeded_img = Image.new("RGB", (10, 10), color="red")
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image(image_factory=StyledPilImage, embeded_image=embeded_img)
        img.save(io.BytesIO())

    def test_render_styled_with_embeded_image_path(self, tmp_path):
        tmpfile = os.path.join(str(tmp_path), "test.png")
        embeded_img = Image.new("RGB", (10, 10), color="red")
        embeded_img.save(tmpfile)
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image(image_factory=StyledPilImage, embeded_image_path=tmpfile)
        img.save(io.BytesIO())

    def test_render_styled_with_square_module_drawer(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=moduledrawers.SquareModuleDrawer(),
        )
        img.save(io.BytesIO())

    def test_render_styled_with_gapped_module_drawer(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=moduledrawers.GappedSquareModuleDrawer(),
        )
        img.save(io.BytesIO())

    def test_render_styled_with_circle_module_drawer(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=moduledrawers.CircleModuleDrawer(),
        )
        img.save(io.BytesIO())

    def test_render_styled_with_rounded_module_drawer(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=moduledrawers.RoundedModuleDrawer(),
        )
        img.save(io.BytesIO())

    def test_render_styled_with_vertical_bars_module_drawer(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=moduledrawers.VerticalBarsDrawer(),
        )
        img.save(io.BytesIO())

    def test_render_styled_with_horizontal_bars_module_drawer(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=moduledrawers.HorizontalBarsDrawer(),
        )
        img.save(io.BytesIO())

    def test_render_styled_with_default_solid_color_mask(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        mask = colormasks.SolidFillColorMask()
        img = qr.make_image(image_factory=StyledPilImage, color_mask=mask)
        img.save(io.BytesIO())

    def test_render_styled_with_solid_color_mask(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        mask = colormasks.SolidFillColorMask(back_color=WHITE, front_color=RED)
        img = qr.make_image(image_factory=StyledPilImage, color_mask=mask)
        img.save(io.BytesIO())

    def test_render_styled_with_color_mask_with_transparency(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        mask = colormasks.SolidFillColorMask(
            back_color=(255, 0, 255, 255), front_color=RED
        )
        img = qr.make_image(image_factory=StyledPilImage, color_mask=mask)
        img.save(io.BytesIO())
        assert img.mode == "RGBA"

    def test_render_styled_with_radial_gradient_color_mask(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        mask = colormasks.RadialGradiantColorMask(
            back_color=WHITE, center_color=BLACK, edge_color=RED
        )
        img = qr.make_image(image_factory=StyledPilImage, color_mask=mask)
        img.save(io.BytesIO())

    def test_render_styled_with_square_gradient_color_mask(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        mask = colormasks.SquareGradiantColorMask(
            back_color=WHITE, center_color=BLACK, edge_color=RED
        )
        img = qr.make_image(image_factory=StyledPilImage, color_mask=mask)
        img.save(io.BytesIO())

    def test_render_styled_with_horizontal_gradient_color_mask(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        mask = colormasks.HorizontalGradiantColorMask(
            back_color=WHITE, left_color=RED, right_color=BLACK
        )
        img = qr.make_image(image_factory=StyledPilImage, color_mask=mask)
        img.save(io.BytesIO())

    def test_render_styled_with_vertical_gradient_color_mask(self):
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        mask = colormasks.VerticalGradiantColorMask(
            back_color=WHITE, top_color=RED, bottom_color=BLACK
        )
        img = qr.make_image(image_factory=StyledPilImage, color_mask=mask)
        img.save(io.BytesIO())

    def test_render_styled_with_image_color_mask(self):
        img_mask = Image.new("RGB", (10, 10), color="red")
        qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
        qr.add_data(UNICODE_TEXT)
        mask = colormasks.ImageColorMask(back_color=WHITE, color_mask_image=img_mask)
        img = qr.make_image(image_factory=StyledPilImage, color_mask=mask)
        img.save(io.BytesIO())


class ShortcutTest(unittest.TestCase):

    def runTest(self):
        qrcode.make("image")
