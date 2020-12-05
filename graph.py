'''
graph.py
'''

import pygame
from pygame import Surface, Color, Rect
from pygame.math import Vector2
from functools import partial
from enum import Enum


class Compass(Enum):

    # members (clockwise from NW)
    NW = 135
    N = 90
    NE = 45
    E = 360
    SE = -45
    S = -90
    SW = -135
    W = 180
    # aliases
    NORTHWEST = 135
    NORTH = 90
    NORTHEAST = 45
    EAST = 360
    SOUTHEAST = -45
    SOUTH = -90
    SOUTHWEST = -135
    WEST = 180

    @classmethod
    def _get_name(cls, key):
        # flexible in accepting names (e.g. Northwest, NORTH_WEST, Nw, nw)
        _name = key
        if not isinstance(_name, str):
            _name = key.name

        _name = _name.strip().upper()
        if len(_name) <= 2:
            return _name
        else:
            return _name[0] + _name[-4]

    @classmethod
    def pygame_anchor(cls, key):
        name = cls._get_name(key)
        return {'NW': 'topleft',
                'N' : 'top',
                'NE': 'topright',
                'E' : 'right',
                'SE': 'bottomright',
                'S' : 'bottom',
                'SW': 'bottomleft',
                'W' : 'left'}[name]

    @classmethod
    def xy(cls, key):
        name = cls._get_name(key)
        return {'NW': Vector2(-1,-1),
                'N' : Vector2( 0,-1),
                'NE': Vector2( 1,-1),
                'E' : Vector2( 1, 0),
                'SE': Vector2( 1, 1),
                'S' : Vector2( 0, 1),
                'SW': Vector2(-1, 1),
                'W' : Vector2(-1, 0)}[name]

    @classmethod
    def from_xy(cls, xy):
        xy_tup = (int(xy[0]), int(xy[1]))
        return {(-1,-1): cls['NW'],
                ( 0,-1): cls['N' ],
                ( 1,-1): cls['NE'],
                ( 1, 0): cls['E' ],
                ( 1, 1): cls['SE'],
                ( 0, 1): cls['S' ],
                (-1, 1): cls['SW'],
                (-1, 0): cls['W' ]}[xy_tup]

    @classmethod
    def get(cls, names):
        iterator = names.split() if isinstance(names, str) else names
        return [cls[name.strip().upper()] for name in iterator]

    @classmethod
    def clockwise(cls, start='NW'):
        name0 = cls._get_name(start)
        order = [d.name for d in cls]
        i = order.index(name0)
        return [cls[name] for name in order[i:] + order[:i]]

    @classmethod
    def counter_clockwise(cls, start='NW'):
        name0 = cls._get_name(start)
        order = [d.name for d in reversed(cls)]
        i = order.index(name0)
        return [cls[name] for name in order[i:] + order[:i]]

    @classmethod
    def flip(cls, key):
        name = cls._get_name(key)
        order = [d.name for d in cls]
        i = order.index(name)
        n = len(order)
        j = (i + n//2) % n
        return cls[order[j]]

    @classmethod
    def adjacents(cls):
        return list(iter(cls))

    @classmethod
    def cardinals(cls):
        return [cls.N, cls.E, cls.S, cls.W]

    @classmethod
    def ordinals(cls):
        return [cls.NW, cls.NE, cls.SE, cls.SW]

    @classmethod
    def orthogonals(cls):
        # alias cardinals
        return [cls.N, cls.E, cls.S, cls.W]

    @classmethod
    def diagonals(cls):
        # alias ordinals
        return [cls.NW, cls.NE,
                cls.SE, cls.SW]

    @classmethod
    def verticals(cls):
        return [cls.NW, cls.N, cls.NE,
                cls.SE, cls.S, cls.SW]

    @classmethod
    def horizontals(cls):
        return [cls.NW, cls.NE, cls.E,
                cls.SE, cls.SW, cls.W]

    @classmethod
    def all_north(cls):
        return [cls.NW, cls.N, cls.NE]

    @classmethod
    def all_east(cls):
        return [cls.NE, cls.E, cls.SE]

    @classmethod
    def all_south(cls):
        return [cls.SE, cls.S, cls.SW]

    @classmethod
    def all_west(cls):
        return [cls.SW, cls.W, cls.NW]


class Graph:

    compass = Compass

    def __init__(self, all_nodes, all_markers):
        self.nodes = {node: set() for node in all_nodes}  # lookup marker(s) at node
        self.markers = {marker: None for marker in all_markers}  # reverse lookup
        self.saved = {}
        self.save('empty')

    def all_nodes(self):
        return frozenset(self.nodes.keys())

    def all_markers(self):
        return frozenset(self.markers.keys())

    def _infer_nodes(self):
        # sync with markers
        nodes = {node: set() for node in self.all_nodes()}
        for marker, node in self.markers.items():
            nodes[node].add(marker)
        return nodes

    def _infer_markers(self):
        # sync with nodes
        markers = {marker: None for marker in self.all_markers()}
        for node, markers_at_node in self.nodes.items():
            for marker in markers_at_node:
                markers[marker] = node
        return markers

    def _move_marker(self, marker, node1):
        node = self.markers[marker]
        self.markers[marker] = node1
        self.nodes[node].remove(marker)
        self.nodes[node1].add(marker)

    def _place_marker(self, marker, node):
        assert self.markers[marker] is None
        self.markers[marker] = node
        self.nodes[node].add(marker)

    def save(self, record):
        # since there are less markers than nodes
        self.saved[record] = self.markers.copy()

    def load(self, record):
        self.markers = self.saved[record]
        self.nodes = self._infer_nodes()

    def reset(self):
        # customize starting state
        raise NotImplementedError

    def step(self, *transition):
        raise NotImplementedError

    def validate_transition(self, markers, *directives, **kwdirectives):
        # return args, kwargs for step if transition valid else False
        raise NotImplementedError


class Grid2D(Graph):

    def __init__(self, bounds, all_markers, nodes_out_bounds=None):

        if isinstance(bounds, (float, int)):
            max_x = max_y = int(bounds)
        else:
            max_x, max_y = [int(dim) for dim in bounds]

        if isinstance(all_markers, int):
            all_markers = range(1,all_markers + 1)
        elif isinstance(all_markers, str):
            all_markers = all_markers.split()

        if nodes_out_bounds is None:
            nodes_out_bounds = set()
        elif isinstance(nodes_out_bounds, str):
            nodes_out_bounds = {nodes_out_bounds}
        elif not isinstance(nodes_out_bounds, set):
            nodes_out_bounds = set(nodes_out_bounds)

        nodes_in_bounds = {(x, y) for y in range(max_y) for x in range(max_x)}
        all_nodes = nodes_in_bounds | nodes_out_bounds

        super().__init__(all_nodes, all_markers)

        self.min_x = 0
        self.min_y = 0
        self.max_x = max_x - 1
        self.max_y = max_y - 1
        self.cols = max_x
        self.rows = max_y

    def render(self, max_width=0.75, stroke='white', fill=None):

        if not hasattr(self, '_static_image'):

            screen_width = pygame.display.get_surface().get_width()
            max_width = max_width * screen_width if 0 < max_width < 1 else max_width
            cols, rows = [abs(z1 - z2) for z1, z2 in zip(self.max_node, self.min_node)]
            quadrant_w = quadrant_h = (screen_width - max_width) // cols
            width, height = quadrant_w * cols, quadrant_h * rows

            surf = Surface([width, height])

            fill = Color(fill) if isinstance(fill, str) else Color(*fill)
            stroke = Color(stroke) if isinstance(stroke, str) else Color(*stroke)

            if fill:
                surf.fill(fill)

            for ix, iy in zip(range(cols), range(rows)):
                x = ix * quadrant_w
                y = iy * quadrant_h
                pygame.draw.line(surf, color, (x, 0), (x, height))
                pygame.draw.line(surf, color, (0, y), (width, y))

            self._static_image = surf.convert_alpha()
            self._quadrant_size = (quadrant_w, quadrant_h)

        width, height = self._static_image.get_size()
        surf = Surface([width, height])
        node_surf = Surface(self._quadrant_size)

        for ix, iy in self.nodes:
            x = ix * self._quadrant_size[0]
            y = iy * self._quadrant_size[1]
            node_image = self.render_node(node_surf.copy(), self.nodes[(ix, iy)])
            surf.blit(node_image, (x, y))

        return surf

    def render_node(self, surf, node):
        surf.set_colorkey(surf.get_at((0, 0)))
        return surf



class TransitionTemplates:

    @staticmethod
    def can_marker_move_grid2d(graph, marker, dest,
                               markers_move_pattern=None,
                               dest_must_be_empty=False,
                               custom_dest_validation=None,
                               default_marker_move_pattern='cardinal',
                               max_distance_allowed=1):

        orig = graph.markers[marker]

        if dest_must_be_empty:
            if not self.nodes[dest]:
                return False

        dest_valid = True
        if custom_dest_validation:
            if isinstance(custom_dest_validation, str):
                custom_dest_validation = getattr(graph, custom_dest_validation)
            if callable(custom_dest_validation):
                dest_valid = custom_dest_validation(marker, dest)
                if not dest_valid:
                    return False

        dist = None
        if isinstance(max_distance_allowed, str):
            max_distance_allowed = getattr(graph, max_distance_allowed)
        if callable(max_distance_allowed):
            try:
                dist = max_distance_allowed(orig, dest)
            except TypeError:
                dist = max_distance_allowed(marker, orig, dest)
            if not dist:
                return False
        else:
            dist = ((dest[0] - orig[0])**2 + (dest[1] - orig[1])**2) ** 0.5
            if dist > max_distance_allowed:
                return False

        direction = graph.compass.from_xy(
            0 if dist[0] == 0 else (1 if dist[0] > 0 else -1),
            0 if dist[1] == 0 else (1 if dist[1] > 0 else -1),
        )

        def_pattern = default_marker_move_pattern
        if callable(default_marker_move_pattern):
            def_pattern = default_marker_move_pattern(marker)
        if isinstance(def_pattern, str):
            if hasattr(graph.compass, def_pattern):
                def_pattern = getattr(graph.compass, def_pattern)
                if callable(def_pattern):
                    def_pattern = def_pattern()
            else:
                def_pattern = graph.compass.get(def_pattern)

        markers_move_pattern_dict = {}
        if markers_move_pattern is True:
            markers_move_pattern = 'markers_move_pattern'
        if isinstance(markers_move_pattern, str):
            markers_move_pattern_dict = getattr(graph, markers_move_pattern)
            if callable(markers_move_pattern_dict):
                markers_move_pattern_dict = markers_move_pattern_dict()

        marker_pattern = markers_move_pattern_dict.get(marker, def_pattern)
        if callable(marker_pattern):
            marker_pattern = marker_pattern(marker)
        if isinstance(marker_pattern, str):
            if hasattr(graph.compass, marker_pattern):
                marker_pattern = getattr(graph.compass, marker_pattern)
                if callable(marker_pattern):
                    marker_pattern = marker_pattern()
            else:
                marker_pattern = graph.compass.get(marker_pattern)

        return (direction in marker_pattern)

    @staticmethod
    def validate_transition(graph, markers, dest,
                            method_marker_eligible_to_move=None,
                            all_markers_must_be_eligible=True,
                            only_single_marker=False,
                            method_for_return_value=None):

        if only_single_marker:
            if len(markers) != 1:
                return False

        eligible = markers
        if method_marker_eligible_to_move:
            is_eligible = getattr(graph, method_marker_eligible_to_move)
            if all_markers_must_be_eligible:
                if not all(is_eligible(m, dest) for m in markers):
                    return False
            else:
                eligible = [m for m in markers if is_eligible(m, dest)]

        if len(eligible) > 0:
            if method_for_return_value:
                method = getattr(graph, method_for_return_value)
                try:
                    return method(markers, dest)
                except TypeError:
                    return method()
            else:
                return markers, dest


class StepTemplates:

    @staticmethod
    def move_markers_to_dest(graph, markers, dest, move_capture_to=False,
                             method_for_return_value=None):

        if move_captured_to is not False:
            captured = graph.nodes[dest]

            capt_node = move_capture_to
            if isinstance(move_capture_to, str):
                if hasattr(graph, move_capture_to):
                    method = getattr(graph, move_capture_to)
                    if callable(method):
                        move_capture_to = method

            for capt in captured:
                if callable(move_capture_to):
                    try:
                        if len(markers) > 1:
                            capt_node = move_capture_to(markers, capt)
                        else:
                            capt_node = move_capture_to(markers[0], capt)
                    except TypeError:
                        if len(markers) > 1:
                            capt_node = move_capture_to(graph, markers, capt)
                        else:
                            capt_node = move_capture_to(graph, marker, capt)

                graph._move_marker(capt, capt_node)

        for marker in markers:
            graph._move_marker(marker, dest)

        if method_for_return_value:
            method = getattr(graph, method_for_return_value)
            try:
                return method(markers, dest)
            except TypeError:
                return method()


class Rules:
    '''
    Training data to fit

    - YutNori
    - Chess
    - Checkers
    - LaserChess (*currently not supported)
    - Janggi

    Trans-Step schemes

    -- YutNori --
    UI(mouse_xy) -> eventually gathers (markers_at_node0, toss_outcome, opt_node1)
    T(markers, node1) = rules(toss_outcome, opt_node1)) -> move all markers to node1,
                                                           node1 markers are sent HOME

    Possible characterization:

    def try_transition(markers, *directives, **kwdirectives):
        node0 = self.markers[markers[0]]
        assert all(self.markers[m] == node0 for m in markers)
        toss_outcome = directives[0]
        opt_node1 = kwdirectives.get('opt_node1')
        node1 = self.rules.query(node0, toss_outcome, opt_node1)
        return markers, node1

    def step(*transition):
        markers, node1 = transition
        captured = self.nodes[node1]
        for capt in captured:
            player_home = self.homes[self.owner(capt)]
            self._move(capt, player_home)
        for marker in markers:
            self._move(marker, node1)


    -- Chess --
    UI(mouse_xy) -> eventually gathers (marker_at_node0, node1)
    T(marker, node1) -> check marker move pattern, dest empty, move to node1, captured out

    def try_transition(markers, *directives, **kwdirectives):
        marker, = markers
        node0 = self.markers[marker]
        node1 = directives[0]
        delta = [(x1-x0) for x0, x1 in zip(node0, node1)]
        if not self.nodes[node1]:
            if self.pieces_move_patterns[marker].check(marker, delta):
                if self.rules.check_valid_move(marker, node0, node1):  # no inbet
                    return marker, node1

    def step(*transition):
        marker, node1 = transition
        capt, = self.nodes[node1]
        self._move(capt, self.OUT)
        self._move(marker, node1)


    -- Checkers --
    UI(mouse_xy) -> eventually gathers (marker_at_node0, node1)
    T(marker, node1) -> check move pattern, dest empty, move to node1, in-between out

    def try_transition(markers, *directives, **kwdirectives):
        marker, = markers
        node0 = self.markers[marker]
        node1 = directives[0]
        if not self.nodes[node1]:
            if self.rules.check_valid_move(node0, node1):
                inbet = self.rules.get_inbetweens(node0, node1)
                return marker, node1, inbet

    def step(*transition):
        marker, node1, inbet = transition
        for capt in inbet:
            self._move(capt, self.OUT)
        self._move(marker, node1)


    -- LaserChess --
    UI(mouse_xy) -> eventually gathers (marker_at_node0, orientation_or_node1)
    T(marker, orientation) -> check rot pattern, rotate
    T(marker, node1) -> check move pattern, dest empty, move

    def try_transition(markers, *directives, **kwdirectives):
        marker, = markers
        node0 = self.markers[marker]

        orientation = kwdirectives.get('orientation')
        node1 = kwdirectives.get('node1')

        if orientation and self.rules.pieces_rot_patterns(marker, orientation):
            return marker, {'orientation': orientation}

        if node1 and not self.nodes[node1] and self.rules.pieces_mv_pattern(marker, node0, node1):
            return marker, {'node1': node1}

    def step(*transition):
        marker, kwdirectives = transition
        orientation = kwdirectives.get('orientation')
        node1 = kwdirectives.get('node1')

        if orientation:
            self._orient(marker, orientation)
        if node1:
            self._move(marker, node1)

        self._laser_step()


    -- Janggi --
    UI(mouse_xy) -> eventually gathers (marker_at_node0, node1)
    T(marker, node1) -> check move pattern, dest empty, move; captured opponent HOME

    def try_transition(markers, *directives, **kwdirectives):
        marker, = markers
        node0 = self.markers[marker]
        node1 = directives[0]

        if not self.nodes[node1] and self.rules.pieces_move_pattern(marker, node0, node1):
            return marker, node1

    def step(*transition):
        marker, node1 = transition
        capt, = self.nodes[node1]
        self._move(capt, self.home[self.owner(marker)])
        self._move(marker, node1)

    '''

    trans = TransitionTemplates
    steps = StepTemplates



if __name__ == '__main__':

    from enum import IntEnum


    class Janggi(Grid2D):

        bounds = (4, 3)
        Piece = IntEnum('Piece', 'KING GENERAL MINISTER MAN FEUDALLORD')

        def __init__(self):
            self.players = (-1, +1)
            self.pieces = set().union(
                {+p for p in self.Piece},
                {-p for p in self.Piece}
            )
            self.pieces_move_pattern = {
                +self.Piece.KING: 'adjacents',
                -self.Piece.KING: 'adjacents',
                +self.Piece.GENERAL: 'orthogonals',
                -self.Piece.GENERAL: 'orthogonals',
                +self.Piece.MINISTER: 'diagonals',
                -self.Piece.MINISTER: 'diagonals',
                +self.Piece.MAN: 'west',
                -self.Piece.MAN: 'east',
                +self.Piece.FEUDALLORD: 'n e s w nw sw',
                -self.Piece.FEUDALLORD: 'n e s w ne se',
            }
            self.out_nodes = tuple('OUT{i}' for i, _ in enumerate(self.players))
            super().__init__(self.bounds, self.pieces, self.out_nodes)
            self.config_rules()
            self.reset()

        def _move_capture_to(self, marker, capture):
            return self.out_nodes[0] if capture < 0 else self.out_nodes[1]

        def _finish_step(self, markers, dest):
            print(f'Moved {markers[0]} to node {dest!r}')

        def _can_piece_move_to_dest(self, marker, dest):
            # empty or enemy (cannot go on ally occupied)
            if not self.nodes[dest]:
                return True
            else:
                m, = self.nodes[dest]
                if_opponent_pieces = int(marker > 0) != (m > 0)
                return if_opponent_pieces

        def _max_distance_allowed(self, orig, dest):
            try:
                marker = self.nodes[orig]
                x, y = orig
                x1, y1 = dest
                dx = (x1-x)
                dy = (y1-y)
                return (dx*dx + dy*dy) < 1.5
            except:  # Nones or OutNodes
                # can be captured: yes
                if dest in self.out_nodes:
                    return True
                else:  # can be placed: if dest empty and not territory
                    if not self.nodes[dest]:
                        if marker < 0:
                            return (dest[0] != self.max_x)
                        else:
                            return (dest[0] != 0)

        def config_rules(self):

            self._can_marker_move = partial(Rules.trans.can_marker_move_grid2d,
                self,
                markers_move_pattern='pieces_move_pattern',
                custom_dest_validation='_can_piece_move_to_dest',
                max_distance_allowed='_max_distance_allowed',
            )

            self.validate_transition = partial(Rules.trans.validate_transition,
                self,
                method_marker_eligible_to_move='_can_marker_move',
                only_single_marker=True,
            )

            self.step = partial(Rules.steps.move_markers_to_dest,
                self,
                move_capture_to='_move_capture_to',
                method_for_return_value='_finish_step',
            )

        def reset(self):
            X, Y = self.max_x, self.max_y
            K, G, M, N, F = self.Piece
            self._place_marker(-K, (0, 1))
            self._place_marker(+K, (X, 1))
            self._place_marker(-M, (0, 0))
            self._place_marker(+M, (X, Y))
            self._place_marker(-G, (0, Y))
            self._place_marker(+G, (X, 0))
            self._place_marker(-N, (1, 1))
            self._place_marker(+N, (2, 1))
            self.save('reset')

        def print(self):
            stringify = lambda p: ('+' if next(iter(p)) > 0 else '-') + self.Piece(abs((next(iter(p))))).name[:3].upper()
            for y in range(self.rows):
                nodes = [self.nodes[(x, y)] for x in range(self.cols)]
                print(' '.join([stringify(m) if m else '....' for m in nodes]))


    g = Janggi()
    g.print()

    X, Y = g.max_x, g.max_y
    K, G, M, N, F = g.Piece

    ok = g.validate_transition(g.nodes[(1,1)], (2,1))
    if ok:
        g.step(*ok)

    print()
    g.print()
