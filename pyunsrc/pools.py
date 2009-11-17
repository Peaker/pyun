import pygame

_names = [
    'red',
    'green',
    'blue',
    'cyan',
    'yellow',
    'darkmagenta',
    'gray',
    'orange',
    'deeppink',
    'white',
]
    

colors = [(name, pygame.color.THECOLORS[name])
          for name in _names]
