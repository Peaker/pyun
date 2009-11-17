import pygame
from util import font_height
from CachedFunc import CachedFunc
from configfile import config

def create_surface(lines):
    font = pygame.font.SysFont('', config.INSTRUCTIONS_FONT_SIZE)
    surface = pygame.Surface(config.WORM_AREA_SIZE, pygame.SWSURFACE)
    surface.set_alpha(config.INSTRUCTIONS_ALPHA * 255)

    text_height = font_height(font)

    width, height = config.WORM_AREA_SIZE
    y = height/2 - len(lines)*text_height/2
    for color, line in lines:
        line_surface = font.render(line, True, color)
        x = width/2 - line_surface.get_width()/2
        surface.blit(line_surface, (x, y))
        y += text_height
    return surface
create_surface = CachedFunc(create_surface)
