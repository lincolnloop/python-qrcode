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


def main(args=sys.argv[1:]):
    parser = optparse.OptionParser(usage=__doc__.strip())
    parser.add_option(
        "--factory", help="Full python path to the image factory class to "
        "create the image with. You can use the following shortcuts to the "
        "built-in image factory classes: {0}.".format(
            ", ".join(sorted(default_factories.keys()))))
    parser.add_option(
        "--optimize", type=int, help="Optimize the data by looking for chunks "
        "of at least this many characters that could use a more efficient "
        "encoding method. Use 0 to turn off chunk optimization.")
    parser.add_option(
        "--error-correction", type='choice', choices=error_correction.keys(),
        default='M',
        help="The error correction level to use. Choices are L (7%), "
        "M (15%, default), Q (25%), and H (30%).")
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
    else:
        data = sys.stdin.read()
    if opts.optimize is None:
        qr.add_data(data)
    else:
        qr.add_data(data, optimize=opts.optimize)

    if image_factory is None and os.isatty(sys.stdout.fileno()):
        qr.print_ascii(tty=True)
        return

    img = qr.make_image(image_factory=image_factory)

    sys.stdout.flush()
    if sys.version_info[0] >= 3:
        buff = sys.stdout.buffer
    else:
        if sys.platform == 'win32':
            import msvcrt
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        buff = sys.stdout

    img.save(buff)


if __name__ == "__main__":
    main()
