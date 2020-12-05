from enum import IntEnum
from compass import Compass


class Graph:

    compass = Compass

    def __init__(self, all_nodes, all_markers):
        self.at_node   = {node: set() for node in all_nodes}  # marker at?
        self.wh_marker = {marker: None for marker in all_markers}  # where marker?
        self.saved = {}
        self.save('empty')

    def all_nodes(self):
        return frozenset(self.at_node.keys())

    def all_markers(self):
        return frozenset(self.wh_marker.keys())

    def _infer_nodes(self):
        # sync with markers
        at_node = {node: set() for node in self.all_nodes()}
        for marker, node in self.wh_marker.items():
            if node is not None:
                at_node[node].add(marker)
        return at_node

    def _infer_markers(self):
        # sync with nodes
        wh_marker = {marker: None for marker in self.all_markers()}
        for node, markers_at_node in self.at_node.items():
            for marker in markers_at_node:
                wh_marker[marker] = node
        return wh_marker

    def _move_marker(self, marker, node1):
        assert node1 is not None
        node = self.wh_marker[marker]
        self.wh_marker[marker] = node1
        self.at_node[node].remove(marker)
        self.at_node[node1].add(marker)

    def _place_marker(self, marker, node):
        assert self.wh_marker[marker] is None and node is not None
        self.wh_marker[marker] = node
        self.at_node[node].add(marker)

    def save(self, record):
        # since there are less markers than nodes
        self.saved[record] = self.wh_marker.copy()

    def load(self, record):
        self.wh_marker = self.saved[record].copy()
        self.at_node = self._infer_nodes()

    def reset(self):
        # customize starting state
        raise NotImplementedError

    def step(self, *transition):
        raise NotImplementedError

    def validate_transition(self, markers, *directives, **kwdirectives):
        # return args, kwargs for step if transition valid else False
        raise NotImplementedError



class Janggi(Graph):

    Piece = IntEnum('Piece', 'KING GENERAL MINISTER MAN FEUDAL_LORD')

    def __init__(self):
        self.cols, self.rows = 4, 3
        self.min_x, self.max_x = 0, self.cols-1
        self.min_y, self.max_y = 0, self.rows-1
        self.players = (-1, +1)
        self.pl_pools = ('-', '+')

        self.movement_patterns = {
            +self.Piece.KING: self.compass.adjacents(),
            -self.Piece.KING: self.compass.adjacents(),
            +self.Piece.GENERAL: self.compass.orthogonals(),
            -self.Piece.GENERAL: self.compass.orthogonals(),
            +self.Piece.MINISTER: self.compass.diagonals(),
            -self.Piece.MINISTER: self.compass.diagonals(),
            +self.Piece.MAN: self.compass.get('west'),
            -self.Piece.MAN: self.compass.get('east'),
            +self.Piece.FEUDAL_LORD: self.compass.get('n e s w nw sw'),
            -self.Piece.FEUDAL_LORD: self.compass.get('n e s w ne se'),
        }

        pieces = {piece for piece in self.movement_patterns}
        nodes = {(x, y) for x in range(self.min_x, self.max_x+1)
                        for y in range(self.min_y, self.max_y+1)}
        nodes.update(set(self.pl_pools))  # nodes storing players' avail pieces

        super().__init__(nodes, pieces)

    def reset(self):
        if 'reset' not in self.saved:
            self.load('empty')
            self._place_marker(-self.Piece.KING, (self.min_x, self.min_y+1))
            self._place_marker(+self.Piece.KING, (self.max_x, self.min_y+1))
            self._place_marker(-self.Piece.MINISTER, (self.min_x, self.min_y))
            self._place_marker(+self.Piece.MINISTER, (self.max_x, self.max_y))
            self._place_marker(-self.Piece.GENERAL, (self.min_x, self.max_y))
            self._place_marker(+self.Piece.GENERAL, (self.max_x, self.min_y))
            self._place_marker(-self.Piece.MAN, (self.min_x+1, self.min_y+1))
            self._place_marker(+self.Piece.MAN, (self.max_x-1, self.min_y+1))
            self._infer_nodes()
            self.save('reset')

        self.turn = 0
        self.winner = None
        self.load('reset')

    @property
    def cur_player(self):
        return self.players[int(self.turn + 1) % 2]

    def _owner(self, marker):
        return self.players[int(marker > 0)]

    def _in_opp_terr(self, node, wrt_marker):
        player = self._owner(wrt_marker)
        if player < 0:  # starts at left
            return (node[0] == self.max_x)
        else:  # pl > 0, starts at right
            return (node[0] == self.min_x)

    def _not_occupied(self, node):
        return not bool(self.at_node[node])

    def _not_ally(self, node, wrt_marker):
        player = self._owner(wrt_marker)
        try:  # True if opponent's
            other, = self.at_node[node]
            return (player != self._owner(other))
        except ValueError:  # empty
            return True

    def _valid_move(self, marker, dest):
        x, y = 0, 1
        orig = self.wh_marker[marker]
        delta = (dest[x] - orig[x], dest[y] - orig[y])

        if abs(delta[x]) <= 1 and abs(delta[y]) <= 1:
            unit_delta = (0 if delta[x] == 0 else (1 if delta[x] > 0 else -1),
                          0 if delta[y] == 0 else (1 if delta[y] > 0 else -1))
            direction = self.compass.from_xy(unit_delta)
            return (direction in self.movement_patterns[int(marker)])

        return False

    def _in_bounds(self, node):
        return (node in self.at_node and node not in self.pl_pools)

    def is_step_valid(self, marker, dest):
        assert not self.winner, 'winner. game must be reset() first'

        if self._owner(marker) == self.cur_player and self._in_bounds(dest):
            orig = self.wh_marker[marker]

            if orig in self.pl_pools:  # movement from pool
                if self._not_occupied(dest) and not self._in_opp_terr(dest, marker):
                    return marker, dest

            else:  # movement
                if self._not_ally(dest, marker) and self._valid_move(marker, dest):
                    return marker, dest

        return False

    def step(self, marker, dest):
        assert self.is_step_valid(marker, dest)

        player_marker = self._owner(marker)

        # capture
        if self.at_node[dest]:
            pl = self.players.index(player_marker)
            capture, = self.at_node[dest]
            capture_dest = self.pl_pools[pl]
            self._move_marker(capture, capture_dest)
            piece = self.Piece(abs(int(capture)))
            if piece == self.Piece.KING:
                self.winner = player_marker
            # captured is now player_marker property
            if piece == self.Piece.FEUDAL_LORD:  # when captured, becomes a man
                capt = +self.Piece.MAN if marker > 0 else -self.Piece.MAN
            else:
                capt = +abs(capture) if marker > 0 else -abs(capture)
            if self.wh_marker.get(capt):
                if isinstance(capt, int):
                    capt = capt+0.1 if capt > 0 else capt-0.1
                else:
                    capt = +int(capt) if capt > 0 else -int(capt)
            self.at_node[capture_dest].remove(capture)
            self.wh_marker[capture] = None
            self.at_node[capture_dest].add(capt)
            self.wh_marker[capt] = capture_dest

        # execute movement
        orig = self.wh_marker[marker]
        self._move_marker(marker, dest)

        # promotion
        piece = self.Piece(abs(int(marker)))
        if self._in_opp_terr(dest, marker):
            if piece == self.Piece.KING:
                self.winner = player_marker
            elif piece == self.Piece.MAN:
                new_marker = +self.Piece.FEUDAL_LORD if marker > 0 else -self.Piece.FEUDAL_LORD
                if self.wh_marker[int(new_marker)] is not None:
                    float_marker = new_marker + 0.1 if marker > 0 else new_marker - 0.1
                    if self.wh_marker.get(float_marker):
                        new_marker = int(new_marker)
                    else:
                        new_marker = float_marker
                self.at_node[dest].remove(marker)
                self.wh_marker[marker] = None
                self.at_node[dest].add(new_marker)
                self.wh_marker[new_marker] = dest

        self.turn += 1
        return self.winner

    def print_board(self):
        n = 3
        empty = '.' * (n + 1)
        stringify = lambda p: f'{"+" if p > 0 else "-"}{self.Piece(abs(int(p))).name[:n]}'
        for y in range(self.min_y, self.max_y + 1):
            row = [self.at_node[(x, y)] for x in range(self.min_x, self.max_x + 1)]
            nodes_str = ' '.join([stringify(next(iter(node))) if node else empty for node in row])
            print(nodes_str)
        for i, _ in enumerate(self.players):
            nodes_str = [stringify(p) for p in self.at_node[self.pl_pools[i]]]
            print('Player', self.pl_pools[i], 'pool:', nodes_str)
        print()
