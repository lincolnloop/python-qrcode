import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from qrcode.constants import PIL_AVAILABLE


def test_module_help():
    """Test that the module can be executed with the help flag."""
    result = subprocess.run(
        [sys.executable, "-m", "qrcode", "-h"],
        capture_output=True,
        text=True,
        check=False,
    )

    # Check that the command executed successfully
    assert result.returncode == 0

    # Check that the help output contains expected information
    assert "qr - Convert stdin" in result.stdout
    assert "--output" in result.stdout
    assert "--factory" in result.stdout


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL is not installed")
def test_module_generate_qrcode():
    """Test that the module can generate a QR code image."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "qrcode.png"

        # Run the command to generate a QR code
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "qrcode",
                "--output",
                str(output_path),
                "https://github.com/lincolnloop/python-qrcode",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Check that the command executed successfully
        assert result.returncode == 0

        # Check that the output file was created
        assert output_path.exists()

        # Check that the file is not empty and is a valid image file
        assert output_path.stat().st_size > 0
