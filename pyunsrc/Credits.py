import pygame

from configfile import config
from util import key_identified
from WormText import WormText

GRAVITY = config.CREDITS_GRAVITY

class Credits(object):
    def __init__(self, game):
        self.game = game
        self.worm_text = WormText('Eyal Lotem')
        
        self._surface = pygame.Surface(config.DISPLAY_MODE, pygame.SWSURFACE)
        self._surface.set_alpha(254 * config.CREDITS_ALPHA)
        
        self.width, self.height = config.DISPLAY_MODE

        worm_text_width, worm_text_height = self.worm_text.size
        self._worm_text_pos = ((self.width-worm_text_width)/2,
                               (self.height-worm_text_height)/2)
        self._worm_text_surface = self._surface.subsurface(self._worm_text_pos,
                                                           self.worm_text.size)
        
        self._font = pygame.font.SysFont('', config.CREDITS_TEXT_FONT_SIZE)
        
        self._texts = iter([
            "Programming",
            "Graphics",
#             "Sounds",
#             "Music",
            "Worm Eyes",
            "Network code",
        ])
        self._cur_text_draw = self._draw_nothing
        self._worm_text_draw = self._worm_text_draw_normal
    
    def _next_text(self):
        try:
            self._cur_text = self._texts.next()
        except StopIteration:
            return
        self._cur_rendered_text = self._font.render(self._cur_text, True, config.CREDITS_TEXT_COLOR)
        text_width, text_height = self._cur_rendered_text.get_size()
        self._cur_text_speed = 0
        self._cur_text_xpos = (self.width - text_width)/2
        self._cur_text_ypos = 0
        worm_text_x, worm_text_y = self._worm_text_pos
        self._cur_text_floor = worm_text_y - text_height - 5
        self._cur_text_draw = self._drop_text

    def _draw_nothing(self, surface):
        pass

    def _drop_text(self, surface):
        surface.blit(self._cur_rendered_text,
                     (self._cur_text_xpos,
                      self._cur_text_ypos))
        self._cur_text_ypos += self._cur_text_speed
        self._cur_text_speed += GRAVITY
        if self._cur_text_ypos >= self._cur_text_floor:
            self._cur_text_ypos = self._cur_text_floor
            self._wait_time = config.CREDITS_WAIT_BETWEEN_TEXTS
            self._cur_text_draw = self._wait_with_text
    
    def _wait_with_text(self, surface):
        surface.blit(self._cur_rendered_text,
                     (self._cur_text_xpos,
                      self._cur_text_ypos))
        self._wait_time -= 1
        if self._wait_time == 0:
            self._next_text()
    
    def handle_pygame_event(self, event):
        if event.type == pygame.KEYDOWN:
            return self._handle_keydown(event)
        return False
    
    def _handle_keydown(self, event):
        if key_identified(event, config.CANCEL_KEY):
            self.game.unshow_credits()
            return True

    def all_keys(self):
        return [config.CANCEL_KEY]

    def _worm_text_draw_existing_surface(self, surface):
        surface.blit(self._surface, (0, 0))
    
    def _worm_text_draw_normal(self, surface):
        if self.worm_text.draw(self._worm_text_surface):
            self._next_text()
            self._worm_text_draw = self._worm_text_draw_existing_surface
        self._worm_text_draw_existing_surface(surface)

    def draw(self, surface):
        self._worm_text_draw(surface)
        self._cur_text_draw(surface)
