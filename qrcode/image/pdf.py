from decimal import Decimal
import qrcode.image.base


pdf_template = """%PDF-1.1
%\xc2\xa5\xc2\xb1\xc3\xab

1 0 obj
  << /Type /Catalog
     /Pages 2 0 R
  >>
endobj

2 0 obj
  << /Type /Pages
     /Kids [3 0 R]
     /Count 1
     /MediaBox [0 0 {pagesize} {pagesize}]
  >>
endobj

3 0 obj
  <<  /Type /Page
      /Parent 2 0 R
      /Resources
       << /Font
           << /F1
               << /Type /Font
                  /Subtype /Type1
                  /BaseFont /Times-Roman
               >>
           >>
       >>
      /Contents 4 0 R
  >>
endobj

4 0 obj
  << /Length 55 >>
stream
  0.0 0.0 0.0 rg
{rectangles}
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000018 00000 n 
0000000077 00000 n 
0000000178 00000 n 
0000000457 00000 n 
trailer
  <<  /Root 1 0 R
      /Size 5
  >>
startxref
565
%%EOF
"""


class PdfImage(qrcode.image.base.BaseImage):
    """
    PDF image builder

    Creates a QR-code image as a PDF document.
    """

    kind = "PDF"
    allowed_kinds = ("PDF",)

    def __init__(self, *args, **kwargs):
        super(PdfImage, self).__init__(*args, **kwargs)
        self.unit_size = self.units(self.box_size)
        self._rects = []

    def drawrect(self, row, col):
        x, y = self.pixel_box(row, col)[0]
        self._rects.append('  {x} {y} {w} {w} re f'.format(
            x=x, y=y, w=self.box_size
        ))

    def units(self, size):
        """
        A box_size of 10 (default) equals 10pt = 3.577777mm.
        
        A PDF point (pt) is defined as 1/72 inches,
        or 25.4/72 mm
        """
        return size

    def save(self, stream, kind=None):
        self.check_kind(kind=kind)
        pdf_data = pdf_template.format(
            pagesize=self.pagesize, rectangles="\n".join(self._rects),
        ).encode('utf-8')
        stream.write(pdf_data)

    def new_image(self, **kwargs):
        self.pagesize = self.units(self.pixel_size)
        return self


