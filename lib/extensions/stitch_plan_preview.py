# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from tempfile import TemporaryDirectory
from base64 import b64encode
from typing import Optional, Tuple
import sys

from inkex import errormsg, Boolean, BoundingBox, Image, BaseElement
from inkex.command import take_snapshot

from ..marker import set_marker
from ..stitch_plan import stitch_groups_to_stitch_plan
from ..svg import render_stitch_plan
from ..svg.tags import (INKSCAPE_GROUPMODE, INKSTITCH_ATTRIBS,
                        SODIPODI_INSENSITIVE, SVG_GROUP_TAG, SVG_PATH_TAG, XLINK_HREF)
from .base import InkstitchExtension
from .stitch_plan_preview_undo import reset_stitch_plan


class StitchPlanPreview(InkstitchExtension):
    def __init__(self, *args, **kwargs):
        InkstitchExtension.__init__(self, *args, **kwargs)
        self.arg_parser.add_argument("-s", "--move-to-side", type=Boolean, default=True, dest="move_to_side")
        self.arg_parser.add_argument("-v", "--layer-visibility", type=str, default="unchanged", dest="layer_visibility")
        self.arg_parser.add_argument("-n", "--needle-points", type=Boolean, default=False, dest="needle_points")
        self.arg_parser.add_argument("-i", "--insensitive", type=Boolean, default=False, dest="insensitive")
        self.arg_parser.add_argument("-c", "--visual-commands", type=Boolean, default="symbols", dest="visual_commands")
        self.arg_parser.add_argument("-o", "--overwrite", type=Boolean, default=True, dest="overwrite")
        self.arg_parser.add_argument("-m", "--render-mode", type=str, default="simple", dest="mode")

    def effect(self):
        realistic, raster_mult = self.parse_mode()

        # delete old stitch plan
        self.remove_old()

        # create new stitch plan
        if not self.get_elements():
            return

        svg = self.document.getroot()
        visual_commands = self.options.visual_commands
        self.metadata = self.get_inkstitch_metadata()
        collapse_len = self.metadata['collapse_len_mm']
        min_stitch_len = self.metadata['min_stitch_len_mm']
        stitch_groups = self.elements_to_stitch_groups(self.elements)
        stitch_plan = stitch_groups_to_stitch_plan(stitch_groups, collapse_len=collapse_len, min_stitch_len=min_stitch_len)

        layer = render_stitch_plan(svg, stitch_plan, realistic, visual_commands)
        layer = self.rasterize(svg, layer, raster_mult)

        # update layer visibility (unchanged, hidden, lower opacity)
        groups = self.document.getroot().findall(SVG_GROUP_TAG)
        self.set_invisible_layers_attribute(groups, layer)
        self.set_visibility(groups, layer)

        self.set_sensitivity(layer)
        self.translate(svg, layer)
        self.set_needle_points(layer)

    def parse_mode(self) -> Tuple[bool, Optional[int]]:
        """
        Parse the "mode" option and return a tuple of a bool indicating if realistic rendering should be used,
        and an optional int indicating the resolution multiplier to use for rasterization, or None if rasterization should not be used.
        """
        realistic = False
        raster_mult: Optional[int] = None
        render_mode = self.options.mode
        if render_mode == "simple":
            pass
        elif render_mode.startswith("realistic-"):
            realistic = True
            raster_option = render_mode.split('-')[1]
            if raster_option != "vector":
                try:
                    raster_mult = int(raster_option)
                except ValueError:
                    errormsg(f"Invalid raster mode {raster_option}")
                    sys.exit(1)
        else:
            errormsg(f"Invalid render mode {render_mode}")
            sys.exit(1)

        return (realistic, raster_mult)

    def remove_old(self):
        svg = self.document.getroot()
        if self.options.overwrite:
            reset_stitch_plan(svg)
        else:
            reset_stitch_plan(svg, False)
            layer = svg.find(".//*[@id='__inkstitch_stitch_plan__']")
            if layer is not None:
                layer.set('id', svg.get_unique_id('inkstitch_stitch_plan_'))

    def rasterize(self, svg, layer: BaseElement, raster_mult: Optional[int]) -> BaseElement:
        if raster_mult is None:
            # Don't rasterize if there's no reason to.
            return layer
        else:
            with TemporaryDirectory() as tempdir:
                bbox: BoundingBox = layer.bounding_box()
                rasterized_file = take_snapshot(svg, tempdir, dpi=96*raster_mult,
                                                export_id=layer.get_id(), export_id_only=True)
                with open(rasterized_file, "rb") as f:
                    image = Image(attrib={
                        XLINK_HREF: f"data:image/png;base64,{b64encode(f.read()).decode()}",
                        "x": str(bbox.left),
                        "y": str(bbox.top),
                        "height": str(bbox.height),
                        "width":  str(bbox.width),
                    })
                    layer.replace_with(image)
                    return image

    def set_invisible_layers_attribute(self, groups, layer):
        invisible_layers = []
        for g in groups:
            if g.get(INKSCAPE_GROUPMODE) == "layer" and 'display' in g.style and g.style['display'] == 'none':
                invisible_layers.append(g.get_id())
        layer.set(INKSTITCH_ATTRIBS['invisible_layers'], ",".join(invisible_layers))
        layer.set(INKSTITCH_ATTRIBS['layer_visibility'], self.options.layer_visibility)

    def set_visibility(self, groups, layer):
        if self.options.layer_visibility == "hidden":
            self.hide_all_layers()
            layer.style['display'] = "inline"
        elif self.options.layer_visibility == "lower_opacity":
            for g in groups:
                style = g.specified_style()
                # check groupmode and exclude stitch_plan layer
                # exclude objects which are not displayed at all or already have opacity < 0.4
                if (g.get(INKSCAPE_GROUPMODE) == "layer" and not g == layer and
                        float(style.get('opacity', 1)) > 0.4 and not style.get('display', 'inline') == 'none'):
                    g.style['opacity'] = 0.4

    def set_sensitivity(self, layer):
        if self.options.insensitive is True:
            layer.set(SODIPODI_INSENSITIVE, True)
        else:
            layer.pop(SODIPODI_INSENSITIVE)

    def translate(self, svg, layer):
        if self.options.move_to_side:
            # translate stitch plan to the right side of the canvas
            translate = svg.get('viewBox', '0 0 800 0').split(' ')[2]
            layer.transform = layer.transform.add_translate(translate)

    def set_needle_points(self, layer):
        if self.options.needle_points:
            for element in layer.iterdescendants(SVG_PATH_TAG):
                set_marker(element, 'start', 'needle-point')
                set_marker(element, 'mid', 'needle-point')
                set_marker(element, 'end', 'needle-point')
