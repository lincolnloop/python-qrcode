import qrcode.image.base
from fpdf import FPDF


class PdfImage(qrcode.image.base.BaseImage):
    """
    Creates a PDF file with a QR-code

    Dependencies
        fpdf

    Simple usage
        factory = qrcode.image.pdf.PdfImage
        img = qrcode.make(mytext, image_factory=factory)
        img.save(output_file_path)

    Asvanced usage
        qr = QRCode()
        qr.add_data(mytext)
        img = qr.make_image(image_factory=factory, size=20, fill_color=(255, 0, 100), \
               background_color=(100, 100, 255), position=(100, 150), format=(148.5, 200))
        img.save(output_file_path)

    Kwargs
        size - the width and the height of the qrcode image, including the border. If not specified, the size computed by qrcode is used
        fill_color and background_color - RGB values ​​of the respective colors, black and none by default
        position - tuple with left and top offsets of a qrcode image on the page  in mm
        format - page size from the list (a3, a4, a5, letter, legal) or dimensions (width, height) in mm
    """

    kind = "PDF"
    allowed_kinds = ("PDF",)

    _position = (0, 0)
    _fill_color = (0, 0, 0)
    _size = 0
    _format = False


    def __init__(self, border, modules_count, box_size, *args, **kwargs):
        super().__init__(border, modules_count, box_size, *args, **kwargs)


    def drawrect(self, row, col):
        x, y = self.pixel_box(row, col)[0]
        self._pdf.rect(self._position[0] + x / self._cell_ratio, self._position[1] + y / self._cell_ratio,
                       self.box_size / self._cell_ratio, self.box_size / self._cell_ratio, 'F')


    def save(self, stream, kind=None):
        self.check_kind(kind=kind)
        self._pdf.output(stream)


    def new_image(self, **kwargs):
        self._position = kwargs.get("position", self._position)
        self._fill_color = kwargs.get("fill_color", self._fill_color)
        size = kwargs.get("size", self._size)
        if not size:
            size = self.pixel_size / 10
        self._cell_ratio = self.pixel_size / size

        format = kwargs.get("format", self._format)
        if not format:
            format = (self._position[0] + size, self._position[1] + size)

        self._pdf = FPDF(format=format)
        self._pdf.add_page()
        fill_color = kwargs.get("fill_color", self._fill_color)
        background_color = kwargs.get("background_color", None)
        if background_color:
            self._pdf.set_fill_color(*background_color)
            self._pdf.rect(self._position[0], self._position[1], size, size, 'F')
        self._pdf.set_fill_color(*fill_color)
        return self._pdf
