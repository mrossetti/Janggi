from pygame.math import Vector2
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
