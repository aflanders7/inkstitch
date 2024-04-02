# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from inkex import Path, errormsg
from shapely.geometry import LineString, MultiPolygon, Polygon

from ..i18n import _
from ..svg import PIXELS_PER_MM
from ..svg.tags import SVG_PATH_TAG
from ..utils.smoothing import smooth_path
from .base import InkstitchExtension


class Outline(InkstitchExtension):
    def __init__(self, *args, **kwargs):
        InkstitchExtension.__init__(self, *args, **kwargs)
        self.arg_parser.add_argument("-b", "--buffer", type=float, default=0.001, dest="buffer")
        self.arg_parser.add_argument("-s", "--smoothness", type=float, default=0.3, dest="smoothness")
        self.arg_parser.add_argument("-t", "--threshold", type=float, default=10.0, dest="threshold")

    def effect(self):
        if not self.svg.selection:
            errormsg(_("Please select one or more shapes to convert to their outline."))
            return

        self.threshold = self.options.threshold * PIXELS_PER_MM
        self.shape_buffer = max(self.options.buffer * PIXELS_PER_MM, 0.001)
        self.smoothness = self.options.smoothness * PIXELS_PER_MM

        for element in self.svg.selection:
            self.element_to_outline(element)

    def element_to_outline(self, element):
        if element.tag_name == 'g':
            for element in element.iterdescendants(SVG_PATH_TAG):
                self.element_to_outline(element)
            return

        d = ''
        transform = element.composed_transform()
        path = element.get_path().transform(transform).break_apart()
        for subpath in path:
            points = subpath.end_points
            shape = LineString(points).buffer(self.shape_buffer)

            interiors = []
            for interior in shape.interiors:
                if Polygon(interior).area < self.threshold:
                    continue
                interior_path = smooth_path(interior.coords, self.smoothness)
                if len(interior_path) > 2:
                    interiors.append(Polygon(interior_path))
            outline = MultiPolygon([Polygon(smooth_path(shape.exterior.coords, self.smoothness))] + interiors)

            for geom in outline.geoms:
                d += str(Path(geom.exterior.coords).transform(-transform))
        element.set('d', d)
