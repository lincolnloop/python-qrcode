#!/usr/bin/env python
"""qr - Convert stdin (or the first argument) to a QR Code.

When stdout is a tty the QR Code is printed to the terminal and when stdout is
a pipe to a file an image is written. The default image format is PNG.
"""

from __future__ import annotations

import optparse
import os
import sys
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple, NoReturn

if TYPE_CHECKING:
    from collections.abc import Iterable

    from qrcode.image.base import BaseImage, DrawerAliases

import qrcode

# ---------------------------------------------------------------------------
# Environment setup (Windows colour support)
# ---------------------------------------------------------------------------

# The next block is added to get the terminal to display properly on MS platforms
if sys.platform.startswith(("win", "cygwin")):  # pragma: no cover
    import colorama

    colorama.init()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_FACTORIES: dict[str, str] = {
    "pil": "qrcode.image.pil.PilImage",
    "png": "qrcode.image.pure.PyPNGImage",
    "svg": "qrcode.image.svg.SvgImage",
    "svg-fragment": "qrcode.image.svg.SvgFragmentImage",
    "svg-path": "qrcode.image.svg.SvgPathImage",
    # Keeping for backwards compatibility:
    "pymaging": "qrcode.image.pure.PymagingImage",
}

ERROR_CORRECTION_MAP: dict[str, int] = {
    "L": qrcode.ERROR_CORRECT_L,
    "M": qrcode.ERROR_CORRECT_M,
    "Q": qrcode.ERROR_CORRECT_Q,
    "H": qrcode.ERROR_CORRECT_H,
}

__all__: list[str] = [
    "ParsedArgs",
    "get_drawer_help",
    "main",
]


# ---------------------------------------------------------------------------
# Parsed arguments container
# ---------------------------------------------------------------------------


class ParsedArgs(NamedTuple):
    """Container for CLI options parsed by ``_parse_args``."""

    factory: str | None
    factory_drawer: str | None
    optimize: int | None
    error_correction: str
    ascii_output: bool
    output_path: str | None
    data_arg: str | None
    box_size: int | None
    border: int | None
    version: int | None


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str]) -> ParsedArgs:
    """Parse command-line arguments into a :class:`ParsedArgs` named tuple.

    Args:
        argv: List of argument strings (typically ``sys.argv[1:]``).

    Returns:
        A :class:`ParsedArgs` instance with all recognised options populated.
    """
    version = metadata.version("qrcode")
    parser = optparse.OptionParser(usage=(__doc__ or "").strip(), version=version)

    def raise_error(msg: str) -> NoReturn:
        parser.error(msg)
        raise  # pragma: no cover  # noqa: PLE0704

    parser.add_option(
        "--factory",
        help="Full python path to the image factory class to "
        "create the image with. You can use the following shortcuts to the "
        f"built-in image factory classes: {commas(DEFAULT_FACTORIES)}.",
    )
    parser.add_option(
        "--factory-drawer",
        help=f"Use an alternate drawer. {get_drawer_help()}.",
    )
    parser.add_option(
        "--optimize",
        type=int,
        help="Optimize the data by looking for chunks "
        "of at least this many characters that could use a more efficient "
        "encoding method. Use 0 to turn off chunk optimization.",
    )
    parser.add_option(
        "--error-correction",
        type="choice",
        choices=sorted(ERROR_CORRECTION_MAP.keys()),
        default="M",
        help="The error correction level to use. Choices are L (7%), "
        "M (15%, default), Q (25%), and H (30%).",
    )
    parser.add_option(
        "--ascii", help="Print as ascii even if stdout is piped.", action="store_true"
    )
    parser.add_option(
        "--output",
        help="The output file. If not specified, the image is sent to "
        "the standard output.",
    )
    parser.add_option(
        "--box-size",
        type=int,
        help="Pixel size of each QR module (default: factory default).",
    )
    parser.add_option(
        "--border",
        type=int,
        help="Width of the quiet zone in modules (default: 4).",
    )
    parser.add_option(
        "--qr-version",
        type=int,
        help="QR code version (1–40). Auto-fit when omitted.",
    )

    opts, remaining = parser.parse_args(argv)

    return ParsedArgs(
        factory=opts.factory,
        factory_drawer=opts.factory_drawer,
        optimize=opts.optimize,
        error_correction=opts.error_correction,
        ascii_output=bool(opts.ascii),
        output_path=opts.output,
        data_arg=remaining[0] if remaining else None,
        box_size=opts.box_size,
        border=opts.border,
        version=opts.qr_version,
    )


# ---------------------------------------------------------------------------
# Factory resolution
# ---------------------------------------------------------------------------


def get_factory(module: str) -> type[BaseImage]:
    """Dynamically import an image factory class from a dotted path.

    Args:
        module: Full Python import path (e.g. ``"qrcode.image.pil.PilImage"``).

    Returns:
        The factory class (subclass of :class:`BaseImage`).

    Raises:
        ValueError: If *module* does not contain a dot.
    """
    if "." not in module:
        raise ValueError("The image factory is not a full python path")
    mod_name, cls_name = module.rsplit(".", 1)
    imp = __import__(mod_name, {}, {}, [cls_name])
    return getattr(imp, cls_name)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# QR code creation helper
# ---------------------------------------------------------------------------


def _create_qr(args: ParsedArgs) -> tuple[qrcode.QRCode, bytes]:
    """Create a :class:`~qrcode.main.QRCode` instance and read input data.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Tuple of ``(qr_code, raw_data_bytes)``. The QR code is configured with
        the requested factory and error correction level but has not yet had
        ``make()`` called on it.
    """
    # Resolve image factory
    if args.factory:
        module = DEFAULT_FACTORIES.get(args.factory, args.factory)
        try:
            image_factory = get_factory(module)
        except ValueError as e:
            raise SystemExit(str(e)) from e
    else:
        image_factory = None

    qr = qrcode.QRCode(
        version=args.version if args.version is not None else None,
        error_correction=ERROR_CORRECTION_MAP[args.error_correction],
        box_size=args.box_size if args.box_size is not None else 10,
        border=args.border if args.border is not None else 4,
        image_factory=image_factory,
    )

    # Read data from argument or stdin
    if args.data_arg:
        data = args.data_arg.encode(errors="surrogateescape")
    else:
        data = sys.stdin.buffer.read()

    return qr, data


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _resolve_drawer_kwargs(
    qr: qrcode.QRCode, drawer_alias: str | None
) -> dict[str, Any]:
    """Build keyword arguments for ``make_image`` based on the drawer alias.

    Args:
        qr: The QR code instance (already initialised with its factory).
        drawer_alias: String alias for the desired drawer, or ``None`` to use
            defaults.

    Returns:
        Dictionary suitable for unpacking into ``qr.make_image(**kwargs)``.

    Raises:
        SystemExit: If the selected factory has no drawer aliases or the alias
            is not recognised.
    """
    kwargs: dict[str, Any] = {}
    if not drawer_alias:
        return kwargs

    aliases: DrawerAliases | None = getattr(qr.image_factory, "drawer_aliases", None)
    if not aliases:
        print("The selected factory has no drawer aliases.", file=sys.stderr)
        raise SystemExit(1)
    if drawer_alias not in aliases:
        msg = f"{drawer_alias} factory drawer not found. Expected {commas(aliases)}"
        print(msg, file=sys.stderr)
        raise SystemExit(1)

    drawer_cls, drawer_kwargs = aliases[drawer_alias]
    kwargs["module_drawer"] = drawer_cls(**drawer_kwargs)
    return kwargs


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """CLI entry-point for the ``qr`` command."""
    if argv is None:
        argv = sys.argv[1:]

    args = _parse_args(argv)
    qr, data = _create_qr(args)

    # Add data with optional optimisation
    if args.optimize is not None:
        qr.add_data(data, optimize=args.optimize)
    else:
        qr.add_data(data)

    # --- Output path: file ---
    if args.output_path:
        img = qr.make_image()
        with Path(args.output_path).open("wb") as out:
            img.save(out)
        return

    # --- Output path: ASCII to terminal (only when no custom factory set) ---
    if qr.image_factory is None and (
        os.isatty(sys.stdout.fileno()) or args.ascii_output
    ):
        qr.print_ascii(tty=not args.ascii_output)
        return

    # --- Output path: image stream to stdout ---
    kwargs = _resolve_drawer_kwargs(qr, args.factory_drawer)
    img = qr.make_image(**kwargs)  # type: ignore[arg-type]

    sys.stdout.flush()
    img.save(sys.stdout.buffer)


# ---------------------------------------------------------------------------
# Utility functions (used in help text generation)
# ---------------------------------------------------------------------------


def get_drawer_help() -> str:
    """Build the ``--factory-drawer`` help string listing available drawers.

    Returns:
        Human-readable sentence describing which drawer aliases are available
        for each factory shortcut.
    """
    help_map: dict[str, set[str]] = {}

    for alias, module in DEFAULT_FACTORIES.items():
        try:
            image_cls = get_factory(module)
        except ImportError:  # pragma: no cover
            continue
        aliases: DrawerAliases | None = getattr(image_cls, "drawer_aliases", None)
        if not aliases:
            continue
        factories = help_map.setdefault(commas(aliases), set())
        factories.add(alias)

    return ". ".join(
        f"For {commas(factories, 'and')}, use: {alias_key}"
        for alias_key, factories in help_map.items()
    )


def commas(items: Iterable[str], joiner: str = "or") -> str:
    """Join an iterable of strings with commas and a final conjunction.

    Args:
        items: Strings to join.
        joiner: Final conjunction (``"or"``, ``"and"``, etc.).

    Returns:
        Formatted string, e.g. ``"a, b or c"``.
    """
    items_tuple = tuple(items)
    if not items_tuple:
        return ""
    if len(items_tuple) == 1:
        return items_tuple[0]
    return f"{', '.join(items_tuple[:-1])} {joiner} {items_tuple[-1]}"


if __name__ == "__main__":  # pragma: no cover
    main()
