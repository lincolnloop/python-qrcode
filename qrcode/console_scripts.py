#!/usr/bin/env python
"""
qr - Convert stdin (or the first argument) to a QR Code.

When stdout is a tty the QR Code is printed to the terminal and when stdout is
a pipe to a file an image is written. The default image format is PNG.
"""
import sys
import optparse
import os
import qrcode
# The next block is added to get the terminal to display properly on MS platforms
if sys.platform.startswith(('win', 'cygwin')):  # pragma: no cover
    import colorama
    colorama.init()
    # Allows ANSI codes to work with sys.stdout.buffer.write
    # https://stackoverflow.com/a/64222858/10720231
    os.system("color")

default_factories = {
    'pil': 'qrcode.image.pil.PilImage',
    'pymaging': 'qrcode.image.pure.PymagingImage',
    'svg': 'qrcode.image.svg.SvgImage',
    'svg-fragment': 'qrcode.image.svg.SvgFragmentImage',
    'svg-path': 'qrcode.image.svg.SvgPathImage',
}

error_correction = {
    'L': qrcode.ERROR_CORRECT_L,
    'M': qrcode.ERROR_CORRECT_M,
    'Q': qrcode.ERROR_CORRECT_Q,
    'H': qrcode.ERROR_CORRECT_H,
}


class CustomOptionParser(optparse.OptionParser):
    """
    A subclass of optparse.OptionParser to make the epilog format right

    https://stackoverflow.com/a/5961280/10720231
    """
    def format_epilog(self, formatter):
        return self.epilog

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    from pkg_resources import get_distribution
    version = get_distribution('qrcode').version
    parser = CustomOptionParser(usage=__doc__.strip(), version=version, epilog="\n"
        "ANSI colors\n"
        "Black  : 0 (\x1b[30m#\x1b[0m)- Bright black  :  8 (\x1b[30;1m#\x1b[0m)\n"
        "Red    : 1 (\x1b[31m#\x1b[0m)- Bright red    :  9 (\x1b[31;1m#\x1b[0m)\n"
        "Green  : 2 (\x1b[32m#\x1b[0m)- Bright green  : 10 (\x1b[32;1m#\x1b[0m)\n"
        "Yellow : 3 (\x1b[33m#\x1b[0m)- Bright yellow : 11 (\x1b[33;1m#\x1b[0m)\n"
        "Blue   : 4 (\x1b[34m#\x1b[0m)- Bright blue   : 12 (\x1b[34;1m#\x1b[0m)\n"
        "Magenta: 5 (\x1b[35m#\x1b[0m)- Bright magenta: 13 (\x1b[35;1m#\x1b[0m)\n"
        "Cyan   : 6 (\x1b[36m#\x1b[0m)- Bright cyan   : 14 (\x1b[36;1m#\x1b[0m)\n"
        "White  : 7 (\x1b[37m#\x1b[0m)- Bright white  : 15 (\x1b[37;1m#\x1b[0m)")
    parser.add_option(
        "--factory", help="Full python path to the image factory class to "
        "create the image with. You can use the following shortcuts to the "
        "built-in image factory classes: {}.".format(
            ", ".join(sorted(default_factories.keys()))))
    parser.add_option(
        "--optimize", type=int, help="Optimize the data by looking for chunks "
        "of at least this many characters that could use a more efficient "
        "encoding method. Use 0 to turn off chunk optimization.")
    parser.add_option(
        "--error-correction", type='choice',
        choices=sorted(error_correction.keys()), default='M',
        help="The error correction level to use. Choices are L (7%), "
        "M (15%, default), Q (25%), and H (30%).")
    parser.add_option(
        "--ascii", "-a", help="Print as ascii even if stdout is piped.", action="store_true")
    parser.add_option(
        "--invert", "-i", help="Invert colorscheme. (text only)", action="store_true")
    parser.add_option(
        "--tty", "-t", help="Use a black and white colorscheme. (text only)", action="store_true")
    parser.add_option(
        "--raw", "-r", help="Don't convert from cp437 to unicdoe (useful for chaining)", action="store_true")
    parser.add_option(
        "--border", type=int, default=4, help="Width of QR code border (text only)")
    parser.add_option(
        "--fg", type=int, default=None, help="ANSI color for forground (text only)")
    parser.add_option(
        "--bg", type=int, default=None, help="ANSI color for forground (text only)")
    parser.add_option(
        "--output",
        help="The output file. If not specified, the image is sent to "
        "the standard output.")

    opts, args = parser.parse_args(args)

    qr = qrcode.QRCode(
        error_correction=error_correction[opts.error_correction])

    if opts.factory:
        module = default_factories.get(opts.factory, opts.factory)
        if '.' not in module:
            parser.error("The image factory is not a full python path")
        module, name = module.rsplit('.', 1)
        imp = __import__(module, {}, [], [name])
        image_factory = getattr(imp, name)
    else:
        image_factory = None

    if args:
        data = args[0]
        data = data.encode(errors="surrogateescape")
    else:
        # Use sys.stdin.buffer if available (Python 3) avoiding
        # UnicodeDecodeErrors.
        stdin_buffer = getattr(sys.stdin, 'buffer', sys.stdin)
        data = stdin_buffer.read()
    if opts.optimize is None:
        qr.add_data(data)
    else:
        qr.add_data(data, optimize=opts.optimize)

    if opts.output:
        img = qr.make_image(image_factory=image_factory)
        with open(opts.output, "wb") as out:
            img.save(out)
    else:
        if image_factory is None and (os.isatty(sys.stdout.fileno()) or opts.ascii):
            qr.print_ascii(tty=opts.tty, invert=opts.invert, border=opts.border, raw=opts.raw, fg=opts.fg, bg=opts.bg)
            return

        img = qr.make_image(image_factory=image_factory)

        sys.stdout.flush()
        # Use sys.stdout.buffer if available (Python 3), avoiding
        # UnicodeDecodeErrors.
        stdout_buffer = getattr(sys.stdout, 'buffer', None)
        if not stdout_buffer:
            if sys.platform == 'win32':  # pragma: no cover
                import msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            stdout_buffer = sys.stdout

        img.save(stdout_buffer)


if __name__ == "__main__":
    main()
