# Authors: see git history
#
# Copyright (c) 2023 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

import time
from collections import defaultdict
from copy import copy
from itertools import chain

import inkex
from networkx import is_empty
from shapely import (LineString, MultiLineString, Point, dwithin,
                     minimum_bounding_radius, reverse)
from shapely.affinity import scale
from shapely.ops import linemerge, substring

from ..commands import add_commands
from ..elements import FillStitch
from ..stitches.auto_fill import (build_fill_stitch_graph, build_travel_graph,
                                  find_stitch_path, graph_make_valid,
                                  which_outline)
from ..svg import PIXELS_PER_MM, get_correction_transform
from ..utils import ensure_multi_line_string
from .pallet import Pallet
from .utils import sort_fills_and_strokes, stripes_to_shapes


class TartanSvgGroup:
    """Generates the tartan pattern for svg element tartans
    """

    def __init__(self, settings):
        self.rotate = settings['rotate']
        self.scale = settings['scale']
        self.offset_x = settings['offset_x'] * PIXELS_PER_MM
        self.offset_y = settings['offset_y'] * PIXELS_PER_MM
        self.output = settings['output']
        self.stitch_type = settings['stitch_type']
        self.row_spacing = settings['row_spacing']
        self.angle_warp = settings['angle_warp']
        self.angle_weft = settings['angle_weft']
        self.min_stripe_width = settings['min_stripe_width']
        self.bean_stitch_repeats = settings['bean_stitch_repeats']

        self.pallet = Pallet()
        self.pallet.update_from_code(settings['pallet'])
        self.symmetry = self.pallet.symmetry
        self.stripes = self.pallet.pallet_stripes
        self.warp, self.weft = self.stripes
        if self.pallet.get_pallet_width(self.scale, self.min_stripe_width) == 0:
            self.warp = []
        if self.pallet.get_pallet_width(self.scale, self.min_stripe_width, 1) == 0:
            self.weft = []
        if self.pallet.equal_warp_weft:
            self.weft = self.warp

    def __repr__(self):
        return f'TartanPattern({self.rotate}, {self.scale}, ({self.offset_x}, {self.offset_y}), {self.symmetry}, {self.warp}, {self.weft})'

    def generate(self, outline):
        parent_group = outline.getparent()
        if parent_group.get_id().startswith('inkstitch-tartan'):
            # remove everything but the tartan outline
            for child in parent_group.iterchildren():
                if child != outline:
                    parent_group.remove(child)
            group = parent_group
        else:
            group = inkex.Group()
            group.set('id', f'inkstitch-tartan-{int(time.time())}')
            parent_group.append(group)

        outline_shape = FillStitch(outline).shape
        transform = get_correction_transform(outline)
        dimensions, rotation_center = self._get_dimensions(outline_shape)

        warp = stripes_to_shapes(
            self.warp,
            dimensions,
            outline_shape,
            self.rotate,
            rotation_center,
            self.symmetry,
            self.scale,
            self.min_stripe_width
        )
        warp_routing_lines = self._get_routing_lines(warp, outline_shape)
        warp = self._route_shapes(warp_routing_lines, outline_shape, warp)
        warp = self._shapes_to_elements(warp, warp_routing_lines, transform)

        weft = stripes_to_shapes(
            self.weft,
            dimensions,
            outline_shape,
            self.rotate,
            rotation_center,
            self.symmetry,
            self.scale,
            self.min_stripe_width,
            True
        )
        weft_routing_lines = self._get_routing_lines(weft, outline_shape)
        weft = self._route_shapes(weft_routing_lines, outline_shape, weft, True)
        weft = self._shapes_to_elements(weft, weft_routing_lines, transform, True)

        fills, strokes = self._combine_shapes(warp, weft, outline_shape)
        fills, strokes = sort_fills_and_strokes(fills, strokes)

        for color, fill_elements in fills.items():
            for element in fill_elements:
                group.append(element)
                if self.stitch_type == "auto_fill":
                    self._add_command(element)
                else:
                    element.pop('inkstitch:start')
                    element.pop('inkstitch:end')

        for color, stroke_elements in strokes.items():
            for element in stroke_elements:
                group.append(element)

        # set outline invisible
        outline.style['display'] = 'none'
        group.append(outline)
        return group

    def _get_command_position(self, fill, point):
        dimensions, center = self._get_dimensions(fill.shape)
        line = LineString([center, (point[0], point[1])])
        fact = 20 / line.length
        line = scale(line, xfact=1+fact, yfact=1+fact, origin=center)
        pos = line.coords[-1]
        return Point(pos)

    def _add_command(self, element):
        if not element.style('fill'):
            return
        fill = FillStitch(element)
        start = element.get('inkstitch:start')
        end = element.get('inkstitch:end')
        if start:
            start = start[1:-1].split(',')
            add_commands(fill, ['fill_start'], self._get_command_position(fill, start))
            element.pop('inkstitch:start')
        if end:
            end = end[1:-1].split(',')
            add_commands(fill, ['fill_end'], self._get_command_position(fill, end))
            element.pop('inkstitch:end')

    def _route_shapes(self, routing_lines, outline_shape, shapes, weft=False):
        routed = defaultdict(list)
        for color, lines in routing_lines.items():
            routed_polygons = self._get_routed_shapes('polygon', shapes[color][0], lines[0], outline_shape, weft)
            routed_linestrings = self._get_routed_shapes('linestring', None, lines[1], outline_shape, weft)
            routed[color] = [routed_polygons, routed_linestrings]
        return routed

    def _get_routed_shapes(self, geometry_type, polygons, lines, outline_shape, weft):
        if not lines:
            return []

        if weft:
            starting_point = lines[-1].coords[-1]
            ending_point = lines[0].coords[0]
        else:
            starting_point = lines[0].coords[0]
            ending_point = lines[-1].coords[-1]

        segments = [list(line.coords) for line in lines if line.length > 5]

        fill_stitch_graph = build_fill_stitch_graph(outline_shape, segments, starting_point, ending_point)
        if is_empty(fill_stitch_graph):
            return []
        graph_make_valid(fill_stitch_graph)
        travel_graph = build_travel_graph(fill_stitch_graph, outline_shape, 0, False)
        path = find_stitch_path(fill_stitch_graph, travel_graph, starting_point, ending_point)
        return self._path_to_shapes(path, fill_stitch_graph, polygons, geometry_type, outline_shape)

    def _path_to_shapes(self, path, fill_stitch_graph, polygons, geometry_type, outline_shape):
        outline = MultiLineString()
        travel_linestring = LineString()
        routed_shapes = []
        for edge in path:
            start, end = edge
            if edge.is_segment():
                if not edge.key == 'segment':
                    # networkx fixed the shape for us, we do not really want to insert the element twice
                    continue
                if not travel_linestring.is_empty:
                    # insert edge run before segment
                    travel_linestring = self._get_shortest_travel(start, outline, travel_linestring)
                    if travel_linestring.geom_type == "LineString":
                        routed_shapes.append(travel_linestring)
                    travel_linestring = LineString()
                routed = self._route_edge_segment(edge, outline, geometry_type, fill_stitch_graph, polygons)
                routed_shapes.extend(routed)
            elif routed_shapes:
                # prepare edge run between segments
                if travel_linestring.is_empty:
                    outline_index = which_outline(outline_shape, start)
                    outline = ensure_multi_line_string(outline_shape.boundary).geoms[outline_index]
                    start_distance = outline.project(Point(start))
                    travel_linestring = self._get_travel(start, end, outline)
                else:
                    end_distance = outline.project(Point(end))
                    travel_linestring = substring(outline, start_distance, end_distance)
        return routed_shapes

    def _route_edge_segment(self, edge, outline, geometry_type, fill_stitch_graph, polygons):
        start, end = edge
        routed = []
        if geometry_type == 'polygon':
            polygon = self._find_polygon(polygons, Point(start))
            if polygon:
                routed.append({'shape': polygon, 'start': start, 'end': end})
        elif geometry_type == 'linestring':
            line = None
            try:
                line = fill_stitch_graph[start][end]['segment'].get('geometry')
            except KeyError:
                line = LineString([start, end])
            if line is not None:
                if start != tuple(line.coords[0]):
                    line = line.reverse()
                if line:
                    routed.append(line)
        return routed

    def _get_shortest_travel(self, start, outline, travel_linestring):
        if outline.length / 2 < travel_linestring.length:
            short_travel = outline.difference(travel_linestring)
            if short_travel.geom_type == "MultiLineString":
                short_travel = linemerge(short_travel)
            if short_travel.geom_type == "LineString":
                if Point(short_travel.coords[-1]).distance(Point(start)) > Point(short_travel.coords[0]).distance(Point(start)):
                    short_travel = reverse(short_travel)
                return short_travel
        return travel_linestring

    def _find_polygon(self, polygons, point):
        for polygon in polygons:
            if dwithin(point, polygon, 0.01):
                return polygon

    def _get_routing_lines(self, shapes, outline):
        routing_lines = defaultdict(list)
        for color, elements in shapes.items():
            routed = [[], []]
            for polygon in elements[0]:
                bounding_coords = polygon.minimum_rotated_rectangle.exterior.coords
                routing_line = LineString([bounding_coords[0], bounding_coords[2]])
                routing_line = ensure_multi_line_string(routing_line.intersection(polygon)).geoms
                routed[0].append(LineString([routing_line[0].coords[0], routing_line[-1].coords[-1]]))
            routed[1].extend(elements[1])
            routing_lines[color] = routed
        return routing_lines

    def _shapes_to_elements(self, shapes, routed_lines, transform, weft=False):
        shapes_copy = copy(shapes)
        for color, shape in shapes_copy.items():
            elements = [[], []]
            polygons, linestrings = shape
            for polygon in polygons:
                if isinstance(polygon, dict):
                    path_element = self._polygon_to_path(color, polygon['shape'], weft, transform, polygon['start'], polygon['end'])
                    if self.stitch_type == 'legacy_fill':
                        polygon_start = Point(polygon['start'])
                        path_element = self._adapt_legacy_fill_params(path_element, polygon_start)
                    elements[0].append(path_element)
                elif polygon.geom_type == "Polygon":
                    elements[0].append(self._polygon_to_path(color, polygon, weft, transform))
                else:
                    elements[0].append(self._linestring_to_path(color, polygon, transform, True))
            for line in linestrings:
                segment = line.difference(MultiLineString(routed_lines[color][1])).is_empty
                if segment:
                    linestring = self._linestring_to_path(color, line, transform)
                else:
                    linestring = self._linestring_to_path(color, line, transform, True)
                elements[1].append(linestring)
            shapes[color] = elements
        return shapes

    def _adapt_legacy_fill_params(self, path_element, start):
        # find best legacy fill param setting
        if not FillStitch(path_element).to_stitch_groups(None):
            return path_element
        blank = Point(FillStitch(path_element).to_stitch_groups(None)[0].stitches[0])
        path_element.set('inkstitch:reverse', True)
        reverse = Point(FillStitch(path_element).to_stitch_groups(None)[0].stitches[0])
        path_element.set('inkstitch:flip', True)
        reverse_flip = Point(FillStitch(path_element).to_stitch_groups(None)[0].stitches[0])
        path_element.pop('inkstitch:revers')
        flip = Point(FillStitch(path_element).to_stitch_groups(None)[0].stitches[0])
        start_positions = [blank.distance(start), reverse.distance(start), reverse_flip.distance(start), flip.distance(start)]
        best_setting = start_positions.index(min(start_positions))

        if best_setting == 0:
            path_element.set('inkstitch:reverse', False)
            path_element.set('inkstitch:flip', False)
        elif best_setting == 1:
            path_element.set('inkstitch:reverse', True)
            path_element.set('inkstitch:flip', False)
        elif best_setting == 2:
            path_element.set('inkstitch:reverse', True)
            path_element.set('inkstitch:flip', True)
        elif best_setting == 3:
            path_element.set('inkstitch:reverse', False)
            path_element.set('inkstitch:flip', True)
        return path_element

    def _combine_shapes(self, warp, weft, outline):
        # combine warp and weft elements into color groups
        # separated into polygons and linestrings
        polygons = defaultdict(list)
        linestrings = defaultdict(list)
        for color, shapes in chain(warp.items(), weft.items()):
            start = None
            end = None
            if shapes[0]:
                if polygons[color]:
                    start = polygons[color][-1].get('inkstitch:end')
                    end = shapes[0][0].get('inkstitch:start')
                    if start and end:
                        start = start[1:-1].split(',')
                        end = end[1:-1].split(',')
                        first_outline = ensure_multi_line_string(outline.boundary).geoms[0]
                        travel = self._get_travel(start, end, first_outline)
                        travel_path_element = self._linestring_to_path(color, travel, shapes[0][0].get('transform'), True)
                        polygons[color].append(travel_path_element)
                polygons[color].extend(shapes[0])
            if shapes[1]:
                if linestrings[color]:
                    start = tuple(list(linestrings[color][-1].get_path().end_points)[-1])
                elif polygons[color]:
                    start = polygons[color][-1].get('inkstitch:end')
                    if start:
                        start = start[1:-1].split(',')
                end = tuple(list(shapes[1][0].get_path().end_points)[0])
                if start and end:
                    first_outline = ensure_multi_line_string(outline.boundary).geoms[0]
                    travel = self._get_travel(start, end, first_outline)
                    travel_path_element = self._linestring_to_path(color, travel, shapes[1][0].get('transform'), True)
                    linestrings[color].append(travel_path_element)
                linestrings[color].extend(shapes[1])

        return polygons, linestrings

    def _get_travel(self, start, end, outline):
        start_distance = outline.project(Point(start))
        end_distance = outline.project(Point(end))
        return substring(outline, start_distance, end_distance)

    def _get_dimensions(self, outline):
        bounds = outline.bounds
        minx, miny, maxx, maxy = bounds
        minx -= self.offset_x
        miny -= self.offset_y
        center = LineString([(bounds[0], bounds[1]), (bounds[2], bounds[3])]).centroid

        if self.rotate != 0:
            # add as much space as necessary to perform a rotation without producing gaps
            min_radius = minimum_bounding_radius(outline)
            minx = center.x - min_radius
            miny = center.y - min_radius
            maxx = center.x + min_radius
            maxy = center.y + min_radius
        return [minx, miny, maxx, maxy], center

    def _polygon_to_path(self, color, polygon, weft, transform, start=None, end=None):
        path = inkex.Path(list(polygon.exterior.coords))
        path.close()
        if path is None:
            return

        for interior in polygon.interiors:
            interior_path = inkex.Path(list(interior.coords))
            interior_path.close()
            path += interior_path

        path_element = inkex.PathElement(
            attrib={'d': str(path)},
            style=f'fill:{color};fill-opacity:0.6;',
            transform=transform
        )

        if self.stitch_type == 'legacy_fill':
            path_element.set('inkstitch:fill_method', 'legacy_fill')
        elif self.stitch_type == 'auto_fill':
            path_element.set('inkstitch:fill_method', 'auto_fill')
            path_element.set('inkstitch:underpath', False)

        path_element.set('inkstitch:fill_underlay', False)
        path_element.set('inkstitch:row_spacing_mm', self.row_spacing)
        if weft:
            angle = self.angle_weft - self.rotate
            path_element.set('inkstitch:angle', angle)
        else:
            angle = self.angle_warp - self.rotate
            path_element.set('inkstitch:angle', angle)

        if start is not None:
            path_element.set('inkstitch:start', str(start))
        if end is not None:
            path_element.set('inkstitch:end', str(end))

        return path_element

    def _linestring_to_path(self, color, line, transform, travel=False):
        path = str(inkex.Path(list(line.coords)))
        if not path:
            return

        path_element = inkex.PathElement(
            attrib={'d': path},
            style=f'fill:none;stroke:{color};stroke-opacity:0.6;',
            transform=transform
        )
        if not travel and self.bean_stitch_repeats > 0:
            path_element.set('inkstitch:bean_stitch_repeats', self.bean_stitch_repeats)
        return path_element
