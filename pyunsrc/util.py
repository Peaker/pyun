import math
import pygame
import socket
import random

static_modifiers = pygame.KMOD_CAPS | pygame.KMOD_MODE | pygame.KMOD_NUM

def random_of(seed):
    return random.WichmannHill(seed)

def angle_towards((x1, y1), (x2, y2)):
    if x2-x1 == 0:
        radians = -math.pi/2
    else:
        radians = math.atan(float(y2 - y1) / (x2 - x1))
    if int(radians>0) ^ int(y2>y1):
        # We need to go up and radians goes down
        # or we need to go down and radians goes up
        radians += math.pi
    return radians%(2*math.pi)

def forwarded_pos((x, y), angle, distance):
    distancex = distance * math.cos(angle)
    distancey = distance * math.sin(angle)
    return x+distancex, y+distancey

def accessor(obj, name):
    def get():
        return getattr(obj, name)
    def set(value):
        setattr(obj, name, value)
    return get, set

def get_computer_name():
    return socket.gethostname()

def key_identified(event, (mod, key)):
    return ((mod == 0 or event.mod & mod) and
            # Disallow different modifiers
            0 == (event.mod & ~static_modifiers & ~mod) and
            event.key == key)

def font_height(font):
    example = font.render('', False, (0,0,0))
    return example.get_height()

def arg_discarder(func):
    def new_func(*args, **kw):
        func()
    return new_func

def exec_python_file(filename):
    namespace = {}
    execfile(filename, namespace)
    return namespace

def do_nothing():
    pass

def average(seq):
    if not seq:
        return 0
    return float(sum(seq)) / len(seq)
