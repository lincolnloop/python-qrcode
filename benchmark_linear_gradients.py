# Copyright (c) 2026 Strohutt
# SPDX-License-Identifier: BSD-3-Clause
"""Compare gradient QR-to-PNG performance against a Git revision.

Run from an editable checkout:
    python benchmark_linear_gradients.py --baseline-ref BASE_COMMIT
"""

# ruff: noqa: T201 -- This command prints benchmark results.

import argparse
import gc
import importlib.util
import io
import platform
import shutil
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import __version__ as pillow_version

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles import colormasks
from qrcode.image.styles.moduledrawers.pil import (
    RoundedModuleDrawer,
    SquareModuleDrawer,
)

PAYLOADS = {
    "url": "https://example.org/products/42",
    "vcard": (
        "BEGIN:VCARD\nVERSION:3.0\nN:Example;Alex;;;\nFN:Alex Example\n"
        "ORG:Example Company\nTITLE:Project Coordinator\n"
        "TEL;TYPE=WORK:+49-30-5550100\nEMAIL:alex@example.org\n"
        "URL:https://example.org\n"
        "ADR;TYPE=WORK:;;Example Street 1;Berlin;;10115;Germany\nEND:VCARD\n"
    ),
    "text_1kb": (
        "The visitor information desk is open from Monday to Friday. "
        "Please keep this ticket for entry and contact reception if you need assistance. "
    )
    * 8,
}
PAYLOADS["text_1kb"] = PAYLOADS["text_1kb"][:1024]


def render(mask_class, drawer_class, payload):
    qr = qrcode.QRCode(box_size=10)
    qr.add_data(payload)
    qr.make()
    image = qr.make_image(
        image_factory=StyledPilImage,
        color_mask=mask_class(),
        module_drawer=drawer_class(),
    )
    output = io.BytesIO()
    image.save(output)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-ref", required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    repo = Path(__file__).resolve().parent
    if Path(qrcode.__file__).resolve().parent != repo / "qrcode":
        parser.error("install this checkout with pip install -e '.[pil]' first")
    git = shutil.which("git")
    if git is None:
        parser.error("git is required to read the baseline revision")
    # Read a user-selected local revision without invoking a shell.
    source = subprocess.check_output(  # noqa: S603
        [git, "show", f"{args.baseline_ref}:qrcode/image/styles/colormasks.py"],
        cwd=repo,
    )
    print(f"Python {platform.python_version()}, Pillow {pillow_version}")
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "baseline_colormasks.py"
        path.write_bytes(source)
        spec = importlib.util.spec_from_file_location("baseline_colormasks", path)
        baseline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline)
        for name, payload in PAYLOADS.items():
            for mask_name in (
                "HorizontalGradiantColorMask",
                "VerticalGradiantColorMask",
            ):
                for drawer in (SquareModuleDrawer, RoundedModuleDrawer):
                    old_mask = getattr(baseline, mask_name)
                    new_mask = getattr(colormasks, mask_name)
                    expected = render(old_mask, drawer, payload)
                    assert render(new_mask, drawer, payload) == expected
                    times = [[], []]
                    for iteration in range(args.repeats):
                        order = (0, 1) if iteration % 2 == 0 else (1, 0)
                        for index in order:
                            gc.collect()
                            gc.disable()
                            try:
                                start = time.perf_counter()
                                output = render(
                                    (old_mask, new_mask)[index], drawer, payload
                                )
                                times[index].append(time.perf_counter() - start)
                            finally:
                                gc.enable()
                            assert output == expected
                    before, after = (statistics.median(samples) for samples in times)
                    print(
                        f"{name} {mask_name} {drawer.__name__}: "
                        f"{before:.4f}s -> {after:.4f}s ({before / after:.2f}x)"
                    )


if __name__ == "__main__":
    main()
