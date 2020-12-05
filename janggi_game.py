import pygame
from pygame import Surface, Rect, Color
from collections import namedtuple
from app import App
from compass import Compass
from janggi import Janggi


class JanggiGame(App):
    """
    Janggi 4x3 in local multiplayer
    """

    config = dict(
        SIZE = (600, 600),
        TITLE = "Janggi",
    )

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.game = Janggi()
        self.init_ui()

    def setup(self):
        self.game.reset()

    def listen(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.game.reset()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._start_drag()
        elif event.type == pygame.MOUSEBUTTONUP:
            self._stop_drag()

    def _start_drag(self):
        # if stopped before starting, correct!
        if self.ui.sel_dest:
            self.ui.sel_dest = None
        # locate marker to be selected (if any)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # -- pieces in board --
        board_x, board_y = self.ui.assets.board.rect.topleft
        quad_w, quad_h = self.ui.assets.board.quadrant.rect.size
        ix = (mouse_x - board_x) // quad_w
        iy = (mouse_y - board_y) // quad_h
        if self.game._in_bounds((ix, iy)) and self.game.at_node[(ix, iy)]:
            self.ui.sel_marker, = self.game.at_node[(ix, iy)]
        # -- pieces out board (pools) --
        else:
            for pl, pool in enumerate(self.ui.assets.board.pools):
                node = self.game.pl_pools[pl]
                markers = list(self.game.at_node[node])
                for i, rect in enumerate(pool.rects):
                    if i >= len(markers):
                        break
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.ui.sel_marker = markers[i]
                        break

    def _stop_drag(self):
        if self.ui.sel_marker:
            # locate dest quadrant to be selected (if any)
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # -- quadrants in board --
            board_x, board_y = self.ui.assets.board.rect.topleft
            quad_w, quad_h = self.ui.assets.board.quadrant.rect.size
            ix = (mouse_x - board_x) // quad_w
            iy = (mouse_y - board_y) // quad_h
            if self.game._in_bounds((ix, iy)):
                self.ui.sel_dest = (ix, iy)
            else:
                self.ui.sel_marker = None

    def draw(self, screen):
        screen.fill(Color('#91464a'))
        self.draw_static(screen)
        self.draw_dynamic(screen)

    def update(self, dt):
        # DEBUG: pygame.display.set_caption(f'{self.ui.sel_marker}, {self.ui.sel_dest}')
        # try to perform step
        if not self.game.winner and self.ui.sel_marker and self.ui.sel_dest:
            # reset selections
            marker, self.ui.sel_marker = self.ui.sel_marker, None
            dest, self.ui.sel_dest = self.ui.sel_dest, None
            # check validity and step() only if valid
            if self.game.is_step_valid(marker, dest):
                self.game.step(marker, dest)

    def init_ui(self):

        class Assets:
            pass

        class UI:
            sel_marker = None
            sel_dest   = None
            assets = Assets()

        self.ui = UI()
        self.ui.assets = Assets()
        self.ui.assets.board = self._get_board()

    def _get_board(self):

        class Board:
            pass

        self._config_board_pos_sizes(Board)
        self._config_board_graphics(Board)

        return Board

    def _config_board_pos_sizes(self, board):

        screen = pygame.display.get_surface()
        width, height = screen.get_size()
        rows, cols = self.game.rows, self.game.cols
        n_fit = max(rows, cols)

        board_w = width * 84//100
        for dw in range(n_fit):
            w = board_w + dw
            if (w % n_fit and (width - w) % 2):
                board_w = w
                break
        else:
            board_w = (board_w + 1) if board_w % 2 else board_w

        qoutl_x = qoutl_y = 1
        quad_w = quad_h = board_w // n_fit
        board_h = rows * quad_h
        board_x = (width - board_w) // 2
        board_y = quad_h // 2

        piece_w = quad_w * 78//100
        piece_w = (piece_w + 1) if piece_w % 2 else piece_w
        piece_h = piece_w
        piece_x, piece_y = ((quad_w - piece_w) // 2,
                            (quad_h - piece_h) // 2)

        avail_h = height - (board_y + board_h)
        pool_margin_y = avail_h * 15//100  # top / bot margin
        pool_piece_w = pool_piece_h = pool_row_h = avail_h * 30//100
        pool_spacing_y = avail_h * 10//100  # between 1st and 2nd row
        pool_x1st = board_x
        pool_x2nd = board_x + board_w - pool_piece_w
        pool_y1st = board_y + board_h + pool_margin_y
        pool_y2nd = pool_y1st + pool_row_h + pool_spacing_y
        max_x1st = width // 2 - pool_piece_w
        min_x2nd = width // 2 + pool_piece_w
        spacing_x = pool_piece_w // 2
        pp = (pool_piece_w, pool_piece_h)

        row1st_left = [Rect(x, pool_y1st, *pp) for x in range(pool_x1st, max_x1st, pool_piece_w+spacing_x)]
        row2nd_left = [Rect(x, pool_y2nd, *pp) for x in range(pool_x1st, max_x1st, pool_piece_w+spacing_x)]
        row1st_right = [Rect(x, pool_y1st, *pp) for x in range(pool_x2nd, min_x2nd,-pool_piece_w-spacing_x)]
        row2nd_right = [Rect(x, pool_y2nd, *pp) for x in range(pool_x2nd, min_x2nd,-pool_piece_w-spacing_x)]

        class Quadrant:
            rect = Rect(qoutl_x, qoutl_y, quad_w, quad_h)

        class Piece:
            rect = Rect(piece_x, piece_y, piece_w, piece_h)

        class Pool:
            def __init__(self, row1st, row2nd):
                # index that separates top_row and bot_row
                self.sep = len(row1st)-1
                self.rects = row1st + row2nd

        Pools = namedtuple('Pools', 'left right')

        board.rect = Rect(board_x, board_y, board_w, board_h)
        board.quadrant = Quadrant
        board.piece = Piece
        board.pools = Pools(Pool(row1st_left, row2nd_left),
                            Pool(row1st_right, row2nd_right))

        return board

    def _config_board_graphics(self, board):

        # quadrants
        qx, qy, qw, qh = board.quadrant.rect
        qsurf = Surface([qw, qh])
        qsurf.fill(Color('white'))

        qleft = qsurf.copy()
        qmid = qsurf.copy()
        qright = qsurf.copy()

        qleft.fill(Color('#a66767'), (qx, qy, qw-qx-qx, qh-qy-qy))
        qmid.fill(Color('#ddbf95'), (qx, qy, qw-qx-qx, qh-qy-qy))
        qright.fill(Color('#8d9360'), (qx, qy, qw-qx-qx, qh-qy-qy))

        board.quadrant.left = qleft.convert()
        board.quadrant.mid = qmid.convert()
        board.quadrant.right = qright.convert()

        # pieces
        b = border = 4
        px, py, pw, ph = board.piece.rect
        psurf = Surface([pw, ph])
        psurfs = {}

        psurf_in = Surface([pw-b-b, ph-b-b])
        psurf_in.fill(Color('white'))

        ROOT_PATH = '/'.join(__file__.replace('\\', '/').split('/')[:-1]) + '/'
        chinese_font = pygame.font.Font(ROOT_PATH + 'MFSongHe_Noncommercial-Regular.ttf', 48)
        Piece = self.game.Piece
        ptexts = {
            Piece.KING: '王',
            Piece.GENERAL: '将',
            Piece.MINISTER: '相',
            Piece.MAN: '子',
            Piece.FEUDAL_LORD: '侯',
        }

        def draw_triangles(surf, directions, color, radius=8, offset=4):
            off = offset
            rx = ry = radius
            w, h = surf.get_size()

            for direction in directions:
                is_corner = direction in Compass.ordinals()
                vx, vy = (0+off if 'W' in direction.name else (w-1-off if 'E' in direction.name else w//2-1),
                          0+off if 'N' in direction.name else (h-1-off if 'S' in direction.name else h//2-1))
                rx = ry = radius * 75//100 if not is_corner else radius
                dx, dy = Compass.xy(Compass.flip(direction))
                dx, dy = int(dx), int(dy)

                if is_corner:
                    vx += dx * rx
                    vy += dy * ry

                Ax, Ay = None, None
                Bx, By = None, None

                if not dx:  # north, south
                    Ax = vx - rx
                    Bx = vx + rx
                    Ay = By = vy + dy * ry

                elif not dy:  # east, west
                    Ay = vy - ry
                    By = vy + ry
                    Ax = Bx = vx + dx * rx

                else:  # diagonals
                    Ax = vx + dx * rx
                    By = vy + dy * ry
                    Ay = vy
                    Bx = vx

                tri = [(vx, vy), (Ax, Ay), (Bx, By)]
                pygame.draw.polygon(surf, color, tri)


        for piece, directions in self.game.movement_patterns.items():
            srf = psurf_in.copy()
            piece_type = Piece(abs(int(piece)))

            if piece_type == Piece.KING:
                srf.fill(Color('#1a602e') if piece > 0 else Color('#a7041f'))
                draw_triangles(srf, directions, Color('white'))
            else:
                draw_triangles(srf, directions, Color('black'))

            piece_text = ptexts[piece_type]
            ptext_srf = chinese_font.render(piece_text, True, (0,0,0))
            ptext_srf = pygame.transform.rotate(ptext_srf, 90 if piece > 0 else 270)
            srf.blit(ptext_srf, ptext_srf.get_rect(center=srf.get_rect().center))

            pouter = psurf.copy()
            pouter.fill(Color('#244f21') if piece > 0 else Color('#75131c'))
            pouter.blit(srf, (b, b))
            psurfs[piece] = pouter.convert()

        board.piece.by_id = psurfs

        # board static
        bw, bh = board.rect.size
        bsurf = Surface([bw, bh])

        for i in range(self.game.rows):
            for j in range(self.game.cols):
                x, y = j * qw, i * qh
                if j == self.game.min_x: bsurf.blit(qleft, (x, y))
                elif j == self.game.max_x: bsurf.blit(qright, (x, y))
                else: bsurf.blit(qmid, (x, y))

        board.static_surf = bsurf.convert()

    def draw_static(self, screen):
        screen.blit(self.ui.assets.board.static_surf, self.ui.assets.board.rect)

    def draw_dynamic(self, screen):
        # player turn
        font = pygame.font.SysFont('Arial', 24, bold=True)
        player = 'GREEN' if self.game.cur_player > 0 else 'RED'
        color = Color('#244f21') if self.game.cur_player > 0 else Color('#75131c')
        text = font.render(f'{player} turn', True, color)
        rect = text.get_rect(center=self.ui.assets.board.rect.center)
        rect.bottom = self.ui.assets.board.rect.y * 75//100
        screen.blit(text, rect)

        # in bounds
        bx, by, bw, bh = self.ui.assets.board.rect
        qw, qh = self.ui.assets.board.quadrant.rect.size

        for piece, node in self.game.wh_marker.items():
            if self.game._in_bounds(node):
                ix, iy = node
                x, y = bx + ix * qw, by + iy * qh
                quad_rect = Rect(x, y, qw, qh)
                surf = self.ui.assets.board.piece.by_id[int(piece)]
                screen.blit(surf, surf.get_rect(center=quad_rect.center))

        # out pools
        for pl, pool_nd in enumerate(self.game.pl_pools):
            lgc_pool = self.game.at_node[pool_nd]
            gfx_pool = self.ui.assets.board.pools[pl]

            for i, piece in enumerate(lgc_pool):
                rect = gfx_pool.rects[i]
                surf = self.ui.assets.board.piece.by_id[int(piece)]
                surf = pygame.transform.scale(surf, rect.size)
                surf = pygame.transform.rotate(surf, 270 if pl else 90)
                screen.blit(surf, rect)

        # preview marker being dragged
        if self.ui.sel_marker is not None:
            surf = self.ui.assets.board.piece.by_id[int(self.ui.sel_marker)].copy()
            surf.set_alpha(200)
            rect = surf.get_rect(center=pygame.mouse.get_pos())
            screen.blit(surf, rect)

        # game over
        if self.game.winner:
            font = pygame.font.SysFont('Arial', 48, bold=True)
            winner = 'GREEN' if self.game.winner > 0 else 'RED'
            color = Color('#244f21') if self.game.winner > 0 else Color('#75131c')
            text1 = font.render(f'{winner} wins!', True, color)
            text2 = font.render(f'R to restart', True, Color('black'))
            screen_rect = screen.get_rect()
            rect1 = text1.get_rect(center=self.ui.assets.board.rect.center)
            rect2 = text2.get_rect(center=self.ui.assets.board.rect.center)
            rect1.y -= rect1.height // 2
            rect2.y += rect2.height // 2
            screen.blit(text1, rect1)
            screen.blit(text2, rect2)



if __name__ == '__main__':
    JanggiGame().run()
