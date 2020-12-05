import ctypes
import pygame


class App:

    default_config = dict(
        SIZE  = (600, 600),
        FPS = 60,
        TITLE = None,
    )

    def __init__(self):
        self._reconfig()

    def _reconfig(self):
        # Configure window with given (or default) settings
        if not hasattr(self, 'config'):
            self.config = self.default_config.copy()
        else:
            for req_field, val in self.default_config.items():
                self.config.setdefault(req_field, val)

        self.WIDTH, self.HEIGHT = self.config['SIZE']
        self.FPS = self.config.get('FPS', 60)

        pygame.init()
        ctypes.windll.user32.SetProcessDPIAware()

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.DOUBLEBUF, 32)
        self.clock = pygame.time.Clock()
        self.dt = 1000.0 / self.FPS  # ms

        if self.config['TITLE']:
            pygame.display.set_caption(self.config['TITLE'])

    @property
    def window(self):
        return self.screen.get_rect()

    def run(self):
        self.setup()

        stop = False

        while not stop:
            self.draw(self.screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT or \
                  (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    stop = True
                    break
                self.listen(event)

            self.update(self.dt)
            pygame.display.flip()
            self.dt = self.clock.tick(self.FPS)

        pygame.quit()

    def setup(self):
        pass

    def draw(self, screen):
        pass

    def listen(self, event):
        pass

    def update(self, dt):
        # Called every loop, dt = elapsed milliseconds from last call.
        # Here for debug (to be overloaded)
        pygame.display.set_caption(f"FPS={round(self.clock.get_fps())} mouse={pygame.mouse.get_pos()}")
