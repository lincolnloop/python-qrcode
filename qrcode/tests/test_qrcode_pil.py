import io
from unittest.mock import patch

import pytest

import qrcode
import qrcode.util
from qrcode.tests.consts import BLACK, RED, UNICODE_TEXT, WHITE

Image = pytest.importorskip("PIL.Image", reason="PIL is not installed")

if Image:
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles import colormasks, moduledrawers


def test_render_pil():
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image()
    img.save(io.BytesIO())
    assert isinstance(img.get_image(), Image.Image)


@pytest.mark.parametrize("back_color", ["TransParent", "red", (255, 195, 235)])
def test_render_pil_background(back_color):
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(back_color="TransParent")
    img.save(io.BytesIO())


def test_render_pil_with_rgb_color_tuples():
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(back_color=(255, 195, 235), fill_color=(55, 95, 35))
    img.save(io.BytesIO())


def test_render_with_pattern():
    qr = qrcode.QRCode(mask_pattern=3)
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image()
    img.save(io.BytesIO())


def test_render_styled_Image():
    qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=StyledPilImage)
    img.save(io.BytesIO())


def test_render_styled_with_embedded_image():
    embedded_img = Image.new("RGB", (10, 10), color="red")
    qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_H)
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=StyledPilImage, embedded_image=embedded_img)
    img.save(io.BytesIO())


def test_render_styled_with_embedded_image_path(tmp_path):
    tmpfile = str(tmp_path / "test.png")
    embedded_img = Image.new("RGB", (10, 10), color="red")
    embedded_img.save(tmpfile)
    qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_H)
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=StyledPilImage, embedded_image_path=tmpfile)
    img.save(io.BytesIO())


@pytest.mark.parametrize(
    "drawer",
    [
        moduledrawers.pil.CircleModuleDrawer,
        moduledrawers.pil.GappedCircleModuleDrawer,
        moduledrawers.pil.GappedSquareModuleDrawer,
        moduledrawers.pil.HorizontalBarsDrawer,
        moduledrawers.pil.RoundedModuleDrawer,
        moduledrawers.pil.SquareModuleDrawer,
        moduledrawers.pil.VerticalBarsDrawer,
    ],
)
def test_render_styled_with_drawer(drawer):
    qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=drawer(),
    )
    img.save(io.BytesIO())


@pytest.mark.parametrize(
    "mask",
    [
        colormasks.SolidFillColorMask(),
        colormasks.SolidFillColorMask(back_color=WHITE, front_color=RED),
        colormasks.SolidFillColorMask(back_color=(255, 0, 255, 255), front_color=RED),
        colormasks.RadialGradiantColorMask(
            back_color=WHITE, center_color=BLACK, edge_color=RED
        ),
        colormasks.SquareGradiantColorMask(
            back_color=WHITE, center_color=BLACK, edge_color=RED
        ),
        colormasks.HorizontalGradiantColorMask(
            back_color=WHITE, left_color=RED, right_color=BLACK
        ),
        colormasks.VerticalGradiantColorMask(
            back_color=WHITE, top_color=RED, bottom_color=BLACK
        ),
        colormasks.ImageColorMask(
            back_color=WHITE, color_mask_image=Image.new("RGB", (10, 10), color="red")
        ),
    ],
)
def test_render_styled_with_mask(mask):
    qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=StyledPilImage, color_mask=mask)
    img.save(io.BytesIO())


def test_embedded_image_and_error_correction(tmp_path):
    "If an embedded image is specified, error correction must be the highest so the QR code is readable"
    tmpfile = str(tmp_path / "test.png")
    embedded_img = Image.new("RGB", (10, 10), color="red")
    embedded_img.save(tmpfile)

    qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_L)
    qr.add_data(UNICODE_TEXT)
    with pytest.raises(ValueError):
        qr.make_image(embedded_image_path=tmpfile)
    with pytest.raises(ValueError):
        qr.make_image(embedded_image=embedded_img)

    qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_M)
    qr.add_data(UNICODE_TEXT)
    with pytest.raises(ValueError):
        qr.make_image(embedded_image_path=tmpfile)
    with pytest.raises(ValueError):
        qr.make_image(embedded_image=embedded_img)

    qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_Q)
    qr.add_data(UNICODE_TEXT)
    with pytest.raises(ValueError):
        qr.make_image(embedded_image_path=tmpfile)
    with pytest.raises(ValueError):
        qr.make_image(embedded_image=embedded_img)

    # The only accepted correction level when an embedded image is provided
    qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_H)
    qr.add_data(UNICODE_TEXT)
    qr.make_image(embedded_image_path=tmpfile)
    qr.make_image(embedded_image=embedded_img)


def test_shortcut():
    qrcode.make("image")


@pytest.mark.parametrize(
    "mask_class",
    [
        colormasks.HorizontalGradiantColorMask,
        colormasks.VerticalGradiantColorMask,
    ],
)
@pytest.mark.parametrize("mode", ["RGB", "RGBA"])
@pytest.mark.parametrize("use_cache", [False, True])
def test_linear_gradient_mask_repeated_colors(mask_class, mode, use_cache):
    back = (240, 230, 220) if mode == "RGB" else (240, 230, 220, 0)
    paint = (0, 0, 0) if mode == "RGB" else (240, 230, 220, 255)
    front = (20, 40, 60) if mode == "RGB" else (20, 40, 60, 160)
    end = (60, 20, 40) if mode == "RGB" else (60, 20, 40, 240)
    mask = mask_class(back, front, end)
    mask.paint_color = paint
    image = Image.new(mode, (60, 80), back)
    pixels = image.load()
    colors = [mask.interp_color(back, paint, norm) for norm in (0.25, 0.5, 1)]
    for x in range(image.width):
        for y in range(image.height):
            pixels[x, y] = colors[(x + y) % len(colors)]
    expected = image.copy()
    colormasks.QRColorMask.apply_mask(mask, expected)

    with patch.object(mask, "extrap_color", wraps=mask.extrap_color) as extrapolate:
        mask.apply_mask(image, use_cache=use_cache)

    assert image.tobytes() == expected.tobytes()
    assert extrapolate.call_count <= max(image.size) * len(colors)


@pytest.mark.parametrize(
    "mask_class",
    [
        colormasks.HorizontalGradiantColorMask,
        colormasks.VerticalGradiantColorMask,
    ],
)
@pytest.mark.parametrize("transparent", [False, True])
@pytest.mark.parametrize(
    "drawer_class",
    [moduledrawers.pil.SquareModuleDrawer, moduledrawers.pil.RoundedModuleDrawer],
)
def test_linear_gradient_mask_rendering(mask_class, transparent, drawer_class):
    back = (245, 235, 225, 0) if transparent else (245, 235, 225)
    front = (20, 40, 60, 160) if transparent else (20, 40, 60)
    end = (60, 20, 40, 240) if transparent else (60, 20, 40)
    mask = mask_class(back, front, end)
    for data, box_size in (("https://example.org/", 3), (UNICODE_TEXT, 5)):
        qr = qrcode.QRCode(box_size=box_size)
        qr.add_data(data)
        actual = qr.make_image(
            image_factory=StyledPilImage,
            color_mask=mask,
            module_drawer=drawer_class(),
        )
        with patch.object(mask_class, "apply_mask", colormasks.QRColorMask.apply_mask):
            expected = qr.make_image(
                image_factory=StyledPilImage,
                color_mask=mask,
                module_drawer=drawer_class(),
            )
        assert actual.get_image().mode == expected.get_image().mode
        assert actual.get_image().tobytes() == expected.get_image().tobytes()
        mask.back_color = (
            tuple(channel - 10 for channel in mask.back_color[:3]) + mask.back_color[3:]
        )


@pytest.mark.parametrize(
    "mask_class",
    [
        colormasks.HorizontalGradiantColorMask,
        colormasks.VerticalGradiantColorMask,
    ],
)
def test_linear_gradient_mask_custom_subclass(mask_class):
    class CustomGradient(mask_class):
        def get_fg_pixel(self, image, x, y):
            return (x, y, 100)

        def get_bg_pixel(self, image, x, y):
            return (255 - x, 255 - y, 255)

    mask = CustomGradient()
    mask.paint_color = (0, 0, 0)
    image = Image.new("RGB", (12, 18), (127, 127, 127))
    expected = image.copy()
    colormasks.QRColorMask.apply_mask(mask, expected)
    mask.apply_mask(image)
    assert image.tobytes() == expected.tobytes()
