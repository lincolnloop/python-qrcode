from __future__ import annotations

from html import escape
from itertools import groupby
from pathlib import Path

from qrcode.image.base import BaseImage


class HtmlImage(BaseImage):
    """
    HTML image builder.

    Renders the QR code as an HTML fragment, so it can be embedded in a
    document (or an email) without referencing an external image.

    The markup is a table of cells: each row of the QR code becomes a ``<tr>``
    and runs of same-coloured modules are merged into a single ``<td>`` using
    ``colspan``. Only inline styles and legacy table attributes are used, since
    that is the subset of HTML that email clients render reliably.
    """

    kind = "HTML"
    allowed_kinds = ("HTML",)
    needs_drawrect = False

    def new_image(
        self,
        fill_color="#000000",
        back_color="#ffffff",
        alt="QR Code",
        attrib=None,
    ):
        self.fill_color = fill_color
        self.back_color = back_color
        self.alt = alt
        self.attrib = attrib or {}
        return self._html()

    def drawrect(self, row, col):
        """
        Not used.
        """

    def to_string(self):
        """
        Return the QR code as an HTML fragment.
        """
        return self._img

    def save(self, stream, kind=None):
        self.check_kind(kind=kind)
        html = self.to_string()
        if isinstance(stream, (str, Path)):
            Path(stream).write_text(html, encoding="utf-8")
            return
        try:
            stream.write(html.encode("utf-8"))
        except TypeError:
            # A text stream was given rather than a binary one.
            stream.write(html)

    def rows_iter(self):
        """
        Yield each row of modules, including the border (quiet zone).
        """
        width = self.width + self.border * 2
        blank_row = [False] * width
        x_border = [False] * self.border
        for _ in range(self.border):
            yield blank_row
        for module_row in self.modules:
            yield x_border + [bool(module) for module in module_row] + x_border
        for _ in range(self.border):
            yield blank_row

    def merged_rows_iter(self):
        """
        Yield ``(row, count)`` pairs, collapsing identical adjacent rows.

        Identical rows render the same as a single, taller row, which keeps the
        border from adding a ``<tr>`` per module.
        """
        for row, group in groupby(self.rows_iter()):
            yield row, len(list(group))

    def _table_attrs(self):
        attrs = {
            "role": "img",
            "aria-label": self.alt,
            # Legacy attributes, for email clients that ignore the styles.
            "cellpadding": "0",
            "cellspacing": "0",
            "border": "0",
            "style": (
                "border-collapse:collapse;border-spacing:0;table-layout:fixed;"
                f"width:{self.pixel_size}px;height:{self.pixel_size}px;"
                f"background-color:{self.back_color};font-size:0;line-height:0"
            ),
        }
        attrs.update(self.attrib)
        return "".join(
            f' {name}="{escape(str(value), quote=True)}"'
            for name, value in attrs.items()
        )

    def _html(self):
        parts = [f"<table{self._table_attrs()}>"]
        for row, row_count in self.merged_rows_iter():
            parts.append(f'<tr style="height:{row_count * self.box_size}px">')
            for dark, group in groupby(row):
                col_count = len(list(group))
                colspan = f' colspan="{col_count}"' if col_count > 1 else ""
                style = f"width:{col_count * self.box_size}px"
                if dark:
                    style += f";background-color:{self.fill_color}"
                parts.append(f'<td{colspan} style="{style}"></td>')
            parts.append("</tr>\n")
        parts.append("</table>")
        return "".join(parts)
