import pygame
from configfile import config
from Canvas import Canvas

# TODO: Use State pattern, yuck!

class WormArea(object):
    def __init__(self, game, surface):
        self.game = game
        self.surface = surface
        slot_length = self.game.net_config.DIAMETER*4
        self.canvas = Canvas(config.WORM_AREA_SIZE, (slot_length, slot_length))
        self.clear()
        self.differential_draw_allowed = False

    def clear(self):
        self.canvas.clear()
        self.surface.fill(config.CLEAR_COLOR)

    def draw_circle(self, color, position, diameter):
        x, y = position
        pygame.draw.circle(self.surface, color, map(int, position), diameter/2)

    def undraw_circle(self, position, diameter):
        self.draw_circle(config.CLEAR_COLOR, position, diameter)

    def show_circle(self, sqr_distance, circle):
        if circle in self.min_circles_sqr_distance:
            if sqr_distance >= self.min_circles_sqr_distance[circle]:
                return
        self.min_circles_sqr_distance[circle] = sqr_distance

    def draw(self):
        if self.game.net_config.FOG_ENABLED:
            self.min_circles_sqr_distance = {}
            self.surface.fill(config.CLEAR_COLOR)
            for player in self.game.all_players():
                player.worm.show()
            sqr_fog_radius = (self.game.net_config.FOG_VISION_DIAMETER/2)**2
            for circle, sqr_distance in self.min_circles_sqr_distance.iteritems():
                relative_distance = min(1.0, (1.0*sqr_distance/sqr_fog_radius))
                fade_color = [c*(1.0-relative_distance)
                              for c in circle.worm().color]
                self.draw_circle(fade_color, circle.position, circle.diameter)
            del self.min_circles_sqr_distance
            self.differential_draw_allowed = False
        else:
            if self.differential_draw_allowed:
                for player in self.game.all_players():
                    player.worm.draw_differentially()
            else:
                for player in self.game.all_players():
                    player.worm.draw_full()
                self.differential_draw_allowed = True
