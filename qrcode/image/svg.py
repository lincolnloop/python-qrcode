import decimal, enum
from decimal import Decimal
from typing import List, Optional, Type, Union, overload

from typing_extensions import Literal

import qrcode.image.base
from qrcode.compat.etree import ET
from qrcode.image.styles.moduledrawers import svg as svg_drawers
from qrcode.image.styles.moduledrawers.base import QRModuleDrawer


class SvgFragmentImage(qrcode.image.base.BaseImageWithDrawer):
    """
    SVG image builder

    Creates a QR-code image as a SVG document fragment.
    """

    _SVG_namespace = "http://www.w3.org/2000/svg"
    kind = "SVG"
    allowed_kinds = ("SVG",)
    default_drawer_class: Type[QRModuleDrawer] = svg_drawers.SvgSquareDrawer

    def __init__(self, *args, **kwargs):
        ET.register_namespace("svg", self._SVG_namespace)
        super().__init__(*args, **kwargs)
        # Save the unit size, for example the default box_size of 10 is '1mm'.
        self.unit_size = self.units(self.box_size)

    @overload
    def units(self, pixels: Union[int, Decimal], text: Literal[False]) -> Decimal:
        ...

    @overload
    def units(self, pixels: Union[int, Decimal], text: Literal[True] = True) -> str:
        ...

    def units(self, pixels, text=True):
        """
        A box_size of 10 (default) equals 1mm.
        """
        units = Decimal(pixels) / 10
        if not text:
            return units
        units = units.quantize(Decimal("0.001"))
        context = decimal.Context(traps=[decimal.Inexact])
        try:
            for d in (Decimal("0.01"), Decimal("0.1"), Decimal("0")):
                units = units.quantize(d, context=context)
        except decimal.Inexact:
            pass
        return f"{units}mm"

    def save(self, stream, kind=None):
        self.check_kind(kind=kind)
        self._write(stream)

    def to_string(self, **kwargs):
        return ET.tostring(self._img, **kwargs)

    def new_image(self, **kwargs):
        return self._svg(**kwargs)

    def _svg(self, tag=None, version="1.1", **kwargs):
        if tag is None:
            tag = ET.QName(self._SVG_namespace, "svg")
        dimension = self.units(self.pixel_size)
        return ET.Element(
            tag,  # type: ignore
            width=dimension,
            height=dimension,
            version=version,
            **kwargs,
        )

    def _write(self, stream):
        ET.ElementTree(self._img).write(stream, xml_declaration=False)


class SvgImage(SvgFragmentImage):
    """
    Standalone SVG image builder

    Creates a QR-code image as a standalone SVG document.
    """

    background: Optional[str] = None
    drawer_aliases: qrcode.image.base.DrawerAliases = {
        "circle": (svg_drawers.SvgCircleDrawer, {}),
        "gapped-circle": (svg_drawers.SvgCircleDrawer, {"size_ratio": Decimal(0.8)}),
        "gapped-square": (svg_drawers.SvgSquareDrawer, {"size_ratio": Decimal(0.8)}),
    }

    def _svg(self, tag="svg", **kwargs):
        svg = super()._svg(tag=tag, **kwargs)
        svg.set("xmlns", self._SVG_namespace)
        if self.background:
            svg.append(
                ET.Element(
                    "rect",
                    fill=self.background,
                    x="0",
                    y="0",
                    width="100%",
                    height="100%",
                )
            )
        return svg

    def _write(self, stream):
        ET.ElementTree(self._img).write(stream, encoding="UTF-8", xml_declaration=True)


class SvgPathImage(SvgImage):
    """
    SVG image builder with one single <path> element (removes white spaces
    between individual QR points).
    """

    QR_PATH_STYLE = {
        "fill": "#000000",
        "fill-opacity": "1",
        "fill-rule": "nonzero",
        "stroke": "none",
    }

    needs_processing = True
    path: Optional[ET.Element] = None
    default_drawer_class: Type[QRModuleDrawer] = svg_drawers.SvgPathSquareDrawer
    drawer_aliases = {
        "circle": (svg_drawers.SvgPathCircleDrawer, {}),
        "gapped-circle": (
            svg_drawers.SvgPathCircleDrawer,
            {"size_ratio": Decimal(0.8)},
        ),
        "gapped-square": (
            svg_drawers.SvgPathSquareDrawer,
            {"size_ratio": Decimal(0.8)},
        ),
    }

    def __init__(self, *args, **kwargs):
        self._subpaths: List[str] = []
        super().__init__(*args, **kwargs)

    def _svg(self, viewBox=None, **kwargs):
        if viewBox is None:
            dimension = self.units(self.pixel_size, text=False)
            viewBox = "0 0 {d} {d}".format(d=dimension)
        return super()._svg(viewBox=viewBox, **kwargs)

    def process(self):
        # Store the path just in case someone wants to use it again or in some
        # unique way.
        self.path = ET.Element(
            ET.QName("path"),  # type: ignore
            d="".join(self._subpaths),
            id="qr-path",
            **self.QR_PATH_STYLE,
        )
        self._subpaths = []
        self._img.append(self.path)


class SvgCompressedImage(SvgImage):
    """
    SVG image builder with goal of smallest possible output, at least among
    algorithms with predictable fast run time.
    """

    needs_processing = True
    path: Optional[ET.Element] = None
    default_drawer_class: Type[QRModuleDrawer] = svg_drawers.SvgCompressedDrawer

    def __init__(self, *args, **kwargs):
        self._points = []
        super().__init__(*args, **kwargs)

    def _svg(self, viewBox=None, **kwargs):
        if viewBox is None:
            dimension = self.units(self.pixel_size, text=False)
            # Save characters by moving real pixels to start at 0,0 with a negative
            # offset for the border, with more real pixels having lower digit counts.
            viewBox = "-{b} -{b} {d} {d}".format(d=dimension, b=self.border)
        return super()._svg(viewBox=viewBox, **kwargs)

    def _generate_subpaths(self):
        """
        Yield a series of paths which walk the grid, drawing squares on,
        and also drawing reverse transparency holes, to complete the SVG.
        """
        # what we should make, juxtaposed against what we currently have
        goal = [ [0]*(self.width+2) for i in range(self.width+2) ]
        curr = [ [0]*(self.width+2) for i in range(self.width+2) ]
        for point in self._points:
            # The +1 -1 allows the path walk logic to not worry about image edges.
            goal[point[0]-self.border+1][point[1]-self.border+1] = 1

        def abs_or_delta(cmds, curr_1, last_1, curr_2=None, last_2=None):
            ''' Use whichever is shorter: the absolute command, or delta command.'''
            def opt_join(a, b):
                if b == None:
                    return '%d'%a
                return '%d'%a+('' if b < 0 else ' ')+'%d'%b
            return min([
                cmds[0]+opt_join(curr_1-last_1, curr_2-last_2 if curr_2 != None else None),
                # The +1 -1 allows the path walk logic to not worry about image edges.
                cmds[1]+opt_join(curr_1-1     , curr_2-1      if curr_2 != None else None)
            ], key=len)

        class WD(enum.IntEnum):
            North = 1
            South = 2
            East = 3
            West = 4

        class PathChain():
            __slots__ = ['cmds','next']
            def __init__(self):
                self.cmds = ''
                self.next = None
            def create_next(self):
                self.next = PathChain()
                return self.next

        # Old cursor position allows optimizing with "m" sometimes instead of "M".
        # The +1 -1 allows the path walk logic to not worry about image edges.
        old_cursor = (1,1)
        fullpath_head = fullpath_tail = None
        fullpath_splice_points = {}

        # Go over the grid, creating the paths. This ordering seems to work fairly
        # well, although it's not necessarily optimal. Unfortunately optimal is a
        # traveling salesman problem, and it's not obvious whether there's any
        # significantly better possible ordering in general.
        for search_y in range(self.width+2):
         for search_x in range(self.width+2):
            if goal[search_x][search_y] == curr[search_x][search_y]:
                continue

            # Note, the 'm' here is starting from the old cursor spot, which (as per SVG
            # spec) is not the close path spot. We could test for both, trying a 'z' to
            # to save characters for the next 'm'. However, the mathematically first
            # opportunity would be a convert of 'm1 100' to 'm1 9', so would require a
            # straight line of 91 pairs of identical pixels. I believe the QR spec allows
            # for that, but it is essentially impossible by chance.
            (start_x, start_y) = (search_x, search_y)
            subpath_head = subpath_tail = PathChain()
            subpath_head.cmds = abs_or_delta('mM', start_x, old_cursor[0], start_y, old_cursor[1])
            path_flips = {}
            do_splice = False # The point where we are doing a splice, to save on 'M's.
            subpath_splice_points = {}
            paint_on = goal[start_x][start_y]
            path_dir = WD.East if paint_on else WD.South
            (curr_x, curr_y) = (last_x, last_y) = (start_x, start_y)

            def should_switch_to_splicing():
                nonlocal do_splice, start_x, start_y, subpath_head, subpath_tail
                if not do_splice and (curr_x, curr_y) in fullpath_splice_points:
                    subpath_head = subpath_tail = PathChain()
                    path_flips.clear()
                    subpath_splice_points.clear()
                    do_splice |= True
                    (start_x, start_y) = (curr_x, curr_y)
                    return True
                return False

            def add_to_splice_points():
                nonlocal subpath_tail
                if (curr_x, curr_y) in subpath_splice_points:
                    # we hit a splice point a second time, so topology dictates it's done
                    subpath_splice_points.pop((curr_x, curr_y))
                else:
                    subpath_splice_points[curr_x, curr_y] = subpath_tail
                    subpath_tail = subpath_tail.create_next()

            # Immediately check for a need to splice in, right from the starting point.
            should_switch_to_splicing()

            while True:
                match path_dir:
                    case WD.East:
                        while goal[curr_x][curr_y] and not goal[curr_x  ][curr_y-1]:
                            if curr_x not in path_flips:
                                path_flips[curr_x] = []
                            path_flips[curr_x].append(curr_y)
                            curr_x += 1
                        assert curr_x != last_x
                        path_dir = WD.North if goal[curr_x][curr_y-1] else WD.South
                        if do_splice or (curr_x, curr_y) != (start_x, start_y):
                            subpath_tail.cmds += abs_or_delta('hH', curr_x, last_x)

                        # only a left turn with a hole coming up on the right is spliceable
                        if path_dir == WD.North and not goal[curr_x][curr_y]:
                            add_to_splice_points()

                        if (curr_x, curr_y) == (start_x, start_y):
                            break # subpath is done
                        if should_switch_to_splicing():
                            continue

                    case WD.West:
                        while not goal[curr_x-1][curr_y] and goal[curr_x-1][curr_y-1]:
                            curr_x -= 1
                            if curr_x not in path_flips:
                                path_flips[curr_x] = []
                            path_flips[curr_x].append(curr_y)
                        assert curr_x != last_x
                        path_dir = WD.South if goal[curr_x-1][curr_y] else WD.North
                        if do_splice or (curr_x, curr_y) != (start_x, start_y):
                            subpath_tail.cmds += abs_or_delta('hH', curr_x, last_x)

                        # only a left turn with a hole coming up on the right is spliceable
                        if path_dir == WD.South and not goal[curr_x-1][curr_y-1]:
                            add_to_splice_points()

                        if (curr_x, curr_y) == (start_x, start_y):
                            break # subpath is done
                        if should_switch_to_splicing():
                            continue

                    case WD.North:
                        while goal[curr_x][curr_y-1] and not goal[curr_x-1][curr_y-1]:
                            curr_y -= 1
                        assert curr_y != last_y
                        path_dir = WD.West if goal[curr_x-1][curr_y-1] else WD.East
                        if do_splice or (curr_x, curr_y) != (start_x, start_y):
                            subpath_tail.cmds += abs_or_delta('vV', curr_y, last_y)

                        # only a left turn with a hole coming up on the right is spliceable
                        if path_dir == WD.West and not goal[curr_x][curr_y-1]:
                            add_to_splice_points()

                        if (curr_x, curr_y) == (start_x, start_y):
                            break # subpath is done
                        if should_switch_to_splicing():
                            continue

                    case WD.South:
                        while not goal[curr_x][curr_y] and goal[curr_x-1][curr_y]:
                            curr_y += 1
                        assert curr_y != last_y
                        path_dir = WD.East if goal[curr_x][curr_y] else WD.West
                        if do_splice or (curr_x, curr_y) != (start_x, start_y):
                            subpath_tail.cmds += abs_or_delta('vV', curr_y, last_y)

                        # only a left turn with a hole coming up on the right is spliceable
                        if path_dir == WD.East and not goal[curr_x-1][curr_y]:
                            add_to_splice_points()

                        if (curr_x, curr_y) == (start_x, start_y):
                            break # subpath is done
                        if should_switch_to_splicing():
                            continue

                    case _: raise
                assert (last_x, last_y) != (curr_x, curr_y), goal
                (last_x, last_y) = (curr_x, curr_y)

            if do_splice:
                subpath_tail.next = fullpath_splice_points[start_x, start_y].next
                fullpath_splice_points[start_x, start_y].next = subpath_head
            else:
                if not fullpath_head:
                    fullpath_head = subpath_head
                else:
                    fullpath_tail.next = subpath_head
                fullpath_tail = subpath_tail
                old_cursor = (last_x, last_y)

            for k,v in subpath_splice_points.items():
                if k in fullpath_splice_points:
                    # we hit a splice point a second time, so topology dictates it's done
                    fullpath_splice_points.pop(k)
                else:
                    # merge new splice point
                    fullpath_splice_points[k] = v

            # Note that only one dimension (which was arbitrary chosen here as
            # horizontal) needs to be evaluated to determine all of the pixel flips.
            for x,ys in path_flips.items():
                ys = sorted(ys, reverse=True)
                while len(ys) > 1:
                    for y in range(ys.pop(),ys.pop()):
                        curr[x][y] = paint_on
        assert fullpath_splice_points == {}, fullpath_splice_points
        while fullpath_head:
            yield fullpath_head.cmds
            fullpath_head = fullpath_head.next

    def process(self):
        # Store the path just in case someone wants to use it again or in some
        # unique way.
        self.path = ET.Element(
            ET.QName("path"),  # type: ignore
            d=''.join(self._generate_subpaths()),
            fill="#000",
        )
        self._img.append(self.path)


class SvgFillImage(SvgImage):
    """
    An SvgImage that fills the background to white.
    """

    background = "white"


class SvgPathFillImage(SvgPathImage):
    """
    An SvgPathImage that fills the background to white.
    """

    background = "white"
