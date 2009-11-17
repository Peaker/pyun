import pygame
import pools
import math
import LinePainter
from util import font_height, average
from configfile import config

class LinePainter(LinePainter.LinePainter):
    def __init__(self, diameter):
        super(LinePainter, self).__init__()
        self._diameter = diameter
        self._radius = self._diameter/2
    def put_text(self, font, color, bgcolor, text, antialiased=True):
        self.put(font.render(text, antialiased, color, bgcolor))
    def put_worm(self, color, bgcolor):
        self.put(self._create_worm_surface(color, bgcolor))
    def _create_worm_surface(self, color, bgcolor):
        surface = pygame.Surface((config.WORM_EXAMPLE_WIDTH, self._diameter*2+6))
        surface.fill(bgcolor)
        xs = xrange(self._radius+2, config.WORM_EXAMPLE_WIDTH-self._radius-2)
        for i, x in enumerate(xs):
            radian_part = float(i) * 2 * math.pi / len(xs)
            y = self._diameter+3 + math.sin(radian_part * 2)*self._radius
            pygame.draw.circle(surface, color, map(int, (x, y)), self._radius)
        return surface

class Hud(object):
    def __init__(self, game):
        """Initialize the Hud display

        The Hud must be initialized before any players are created.
        """
        self.game = game
        self._font = pygame.font.SysFont('', config.HUD_FONT_SIZE)
        self._bold_font = pygame.font.SysFont('', config.HUD_FONT_SIZE, bold=True)
        self._small_font = pygame.font.SysFont('', config.KEYS_FONT_SIZE)

    def _host_color(self, host):
        def player_colors_component(x):
            return [player.worm.color[x] for player in host.players]
        r, g, b = tuple([average(player_colors_component(i))/4.0
                         for i in xrange(3)])
        br, bg, bb = config.HUD_HOST_BASE_COLOR
        return r+br, g+bg, b+bb

    def draw(self, surface):
        surface.fill(config.HUD_AREA_COLOR)

        x, y = (5, 5)
        for host in self.game.network.hosts:
            painter = LinePainter(self.game.net_config.DIAMETER)
            host_color = self._host_color(host)
            if self.game.is_network_game() and config.SHOW_HOST_NAME:
                painter.put_text(self._font, (255, 255, 255), host_color, host.name)
                painter.end_line()
            for player in host.players:
                color = player.worm.color
                if not player.alive:
                    color = tuple([i/2 for i in color])

                font = self._font
                if player is self.game.controller.chosen_player():
                    font = self._bold_font
                
                painter.put_text(font, color, host_color, '%02d ' % (player.score,))
                painter.put_worm(color, host_color)

                controller = self.game.player_controllers.get(player)
                if controller is None:
                    control_str = ''
                else:
                    control_str = controller.control_str()
                painter.put_text(self._small_font, color, host_color, ' ' + control_str)
                painter.end_line()

            if self.game.is_network_game() and config.SHOW_TOTAL_SCORE:
                total = sum([player.score for player in host.players])
                painter.put_text(self._small_font, (255, 255, 255), host_color, 'Total: %02d' % (total,))
                painter.end_line()
            
            width, height = painter.size()
            hud_width, hud_height = config.HUD_AREA_SIZE
            surface.fill(host_color, ((x, y), (hud_width, height)))
            painter.draw(surface, (x, y))
            
            y += height + 5
        painter = LinePainter(self.game.net_config.DIAMETER)
        for color_name, color in pools.colors:
            painter.put_worm(color, config.CLEAR_COLOR)
            painter.end_line()
        painter.draw(surface, (x, y))
