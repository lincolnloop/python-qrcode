from __future__ import annotations

"""CLI edge-case tests for ``qrcode.console_scripts``.

These tests cover scenarios not already exercised by the basic test suite:
factory shortcuts, error-correction levels, stdin with image output, optimise
values > 0, and option combinations.
"""

import io
import sys
from unittest import mock

import pytest

from qrcode.console_scripts import main

# ---------------------------------------------------------------------------
# Factory shortcut tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "shortcut",
    ["pil", "png", "svg", "svg-fragment", "svg-path"],
)
def test_factory_shortcuts(shortcut: str, tmp_path: pytest.TempPathFactory) -> None:
    """Each built-in factory shortcut should resolve without error."""
    out = tmp_path / f"out_{shortcut}.png"
    main(["testtext", "--factory", shortcut, "--output", str(out)])
    assert out.exists()


# ---------------------------------------------------------------------------
# Error-correction level tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "level",
    ["L", "M", "Q", "H"],
)
def test_error_correction_levels(level: str, tmp_path: pytest.TempPathFactory) -> None:
    """All four error-correction levels are accepted by the CLI."""
    out = tmp_path / f"ec_{level}.png"
    main(["testtext", "--error-correction", level, "--output", str(out)])
    assert out.exists()


# ---------------------------------------------------------------------------
# Optimise value > 0
# ---------------------------------------------------------------------------


def test_optimize_positive(tmp_path: pytest.TempPathFactory) -> None:
    """``--optimize=N`` with N > 0 should work (chunk optimisation threshold)."""
    out = tmp_path / "opt5.png"
    main(["testtext", "--optimize", "5", "--output", str(out)])
    assert out.exists()


# ---------------------------------------------------------------------------
# Stdin combined with image output (not ASCII)
# ---------------------------------------------------------------------------


def test_stdin_image_output(tmp_path: pytest.TempPathFactory) -> None:
    """Reading data from stdin and writing an image to a file."""
    out = tmp_path / "stdin_img.png"
    with mock.patch("sys.stdin") as fake_stdin:
        fake_stdin.buffer.read.return_value = b"from-stdin"
        main(["--output", str(out)])
    assert out.exists()


# ---------------------------------------------------------------------------
# ASCII flag explicit (force ASCII even when stdout is a pipe)
# ---------------------------------------------------------------------------


def test_ascii_flag_explicit(capsys: pytest.CaptureFixture[str]) -> None:
    """``--ascii`` forces terminal output even when stdout is not a tty."""

    class FakeStdout(io.StringIO):
        def fileno(self) -> int:
            return 1  # stdout file descriptor

    real_stdout = sys.stdout
    try:
        sys.stdout = FakeStdout()
        with mock.patch("os.isatty", return_value=False):
            main(["testtext", "--ascii"])
        output_text = sys.stdout.getvalue()
    finally:
        sys.stdout = real_stdout

    # ASCII QR code output uses CP437 block characters: █ ▀ ▄ ▌ etc.
    cp437_chars = ("\u2588", "\u2580", "\u2584", "\u258c")  # █ ▀ ▄ ▌
    assert any(c in output_text for c in cp437_chars) and len(output_text) > 100


# ---------------------------------------------------------------------------
# Combination: factory + error-correction + optimize
# ---------------------------------------------------------------------------


def test_option_combination(tmp_path: pytest.TempPathFactory) -> None:
    """Multiple options together should work without conflict."""
    out = tmp_path / "combo.png"
    main(
        [
            "https://example.com/long-url-for-testing",
            "--factory",
            "pil",
            "--error-correction",
            "H",
            "--optimize",
            "0",
            "--output",
            str(out),
        ]
    )
    assert out.exists()


# ---------------------------------------------------------------------------
# Invalid error-correction level
# ---------------------------------------------------------------------------


def test_invalid_error_correction(capsys: pytest.CaptureFixture[str]) -> None:
    """An unrecognised error-correction value should cause a clean exit."""
    with pytest.raises(SystemExit):
        main(["testtext", "--error-correction", "X"])


# ---------------------------------------------------------------------------
# Stdin binary data (non-UTF-8 bytes)
# ---------------------------------------------------------------------------


def test_stdin_binary_data(tmp_path: pytest.TempPathFactory) -> None:
    """Binary/non-UTF-8 stdin should be handled without decode errors."""
    out = tmp_path / "binary.png"
    with mock.patch("sys.stdin") as fake_stdin:
        # Bytes that are not valid UTF-8
        fake_stdin.buffer.read.return_value = b"\x80\x81\xff\xfe"
        main(["--output", str(out)])
    assert out.exists()


# ---------------------------------------------------------------------------
# Empty string input (edge case — should auto-select version 1)
# ---------------------------------------------------------------------------


def test_empty_string_input(tmp_path: pytest.TempPathFactory) -> None:
    """Minimal data (single character) should produce a valid QR code."""
    out = tmp_path / "empty.png"
    main(["x", "--output", str(out)])
    assert out.exists()


# ---------------------------------------------------------------------------
# --qr-version option
# ---------------------------------------------------------------------------


def test_qr_version(tmp_path: pytest.TempPathFactory) -> None:
    """``--qr-version=N`` forces a specific QR code version."""
    out = tmp_path / "v10.png"
    main(["testtext", "--qr-version", "10", "--output", str(out)])
    assert out.exists()


# ---------------------------------------------------------------------------
# --box-size option
# ---------------------------------------------------------------------------


def test_box_size(tmp_path: pytest.TempPathFactory) -> None:
    """``--box-size=N`` controls module pixel size."""
    out = tmp_path / "bs20.png"
    main(["testtext", "--box-size", "20", "--output", str(out)])
    assert out.exists()


# ---------------------------------------------------------------------------
# --border option
# ---------------------------------------------------------------------------


def test_border(tmp_path: pytest.TempPathFactory) -> None:
    """``--border=N`` controls quiet zone width."""
    out = tmp_path / "br8.png"
    main(["testtext", "--border", "8", "--output", str(out)])
    assert out.exists()
