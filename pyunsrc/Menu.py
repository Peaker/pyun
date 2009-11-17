import pygame
import math
from util import key_identified
from pygame_keys import key_name
from CachedFunc import CachedFunc
from configfile import config

def always():
    return True

def never():
    return False

def do_nothing():
    def nothing_doer():
        return
    return nothing_doer

def text(x):
    def gen_text():
        return x
    return gen_text

def conditional_text(enabled_func, t, f):
    def gen_text():
        if enabled_func():
            return t
        return f
    return gen_text

OPTION_FONT_SIZE, OPTION_KEYS_FONT_SIZE = config.MENU_FONT_SIZES

class Option(object):
    def __init__(self, enabled_func, text,
                 text_size=OPTION_FONT_SIZE,
                 keys_text_size=OPTION_KEYS_FONT_SIZE,
                 description=''):
        self.enabled_func = enabled_func
        self.text = text
        self.circle_count = 0
        self.description = description

        self.size = max(text_size, keys_text_size)
        self.font = pygame.font.SysFont('', text_size)
        self.keys_font = pygame.font.SysFont('', keys_text_size)
        self._make_line_surfaces = CachedFunc(self._make_line_surfaces)

    def _make_line_surfaces(self, is_enabled, text):
        if is_enabled:
            color = config.MENU_ENABLED_TEXT_COLOR
        else:
            color = config.MENU_DISABLED_TEXT_COLOR
        return (self.font.render(self.text(), True,
                                 color, config.MENU_AREA_COLOR),
                self.keys_font.render(self.keys_str(), True,
                                      config.MENU_KEY_COLOR,
                                      config.MENU_AREA_COLOR))

    def line_surfaces(self):
        return self._make_line_surfaces(self.enabled_func(), self.text())

class EventOption(Option):
    def __init__(self, enabled_func, action, text, keys, steal_key=False, **kw):
        super(EventOption, self).__init__(enabled_func, text, **kw)
        def menu_action(menu):
            self._preaction(menu)
            action()
        self.action = menu_action
        self.keys = keys
        self.steal_key = steal_key
    
    def selected__handle_pygame_event(self, menu, event):
        if event.type != pygame.KEYDOWN:
            return False
        if key_identified(event, config.MENU_SELECT_KEY):
            self.action(menu)
            return True
        return False

    def handle_pygame_event(self, menu, event):
        if event.type != pygame.KEYDOWN:
            return False
        for key in self.keys:
            if key_identified(event, key):
                self.action(menu)
                return self.steal_key
        return False

    def all_keys(self):
        return self.keys

    def selected__all_keys(self):
        return [config.MENU_SELECT_KEY]

    def _preaction(self, menu):
        menu.disable()

    def keys_str(self):
        if self.keys:
            return '[%s]' % (key_name(self.keys[0]),)
        return ''

class BooleanOption(EventOption):
    def __init__(self, enabled_func, option_name, accessor, keys, steal_key=False, **kw):
        get, set = accessor
        def text():
            return option_name() + ' (%s)' % (bool(get()),)
        def action():
            set(not get())
        super(BooleanOption, self).__init__(enabled_func, action, text, keys, steal_key, **kw)
        def menu_action(menu):
            self._preaction(menu)
            action()
    def _preaction(self, menu):
        pass
    
class NumberOption(Option):
    def __init__(self, enabled_func, option_name, accessor,
                 min=None, max=None, jump=1, **kw):
        self._get, self._set = accessor
        self.min = min
        self.max = max
        self.jump = jump
        def text():
            return option_name() + ' (%s)' % (self._get(),)
        super(NumberOption, self).__init__(enabled_func, text, **kw)

    def _change_val(self, delta):
        x = self._get()
        x += delta
        if self.max is not None and x > self.max:
            return
        if self.min is not None and x < self.min:
            return
        self._set(x)
    
    def keys_str(self):
        return '[%s/%s]' % (key_name(config.MENU_INCREASE_VALUE_KEY),
                            key_name(config.MENU_DECREASE_VALUE_KEY))

    def selected__handle_pygame_event(self, menu, event):
        if event.type != pygame.KEYDOWN:
            return False
        if key_identified(event, config.MENU_INCREASE_VALUE_KEY):
            self._change_val(self.jump)
            return True
        if key_identified(event, config.MENU_DECREASE_VALUE_KEY):
            self._change_val(-self.jump)
            return True
        return False

    def handle_pygame_event(self, menu, event):
        return False

    def all_keys(self):
        return []

    def selected__all_keys(self):
        return [config.MENU_INCREASE_VALUE_KEY,
                config.MENU_DECREASE_VALUE_KEY]

class Splitter(Option):
    def __init__(self, size=10, **kw):
        super(Splitter, self).__init__(never, text(''), text_size=size, keys_text_size=size, **kw)

    def ignore_event(self, menu, event):
        return False
    selected__handle_pygame_event = handle_pygame_event = ignore_event

    def empty_key_list(self):
        return []
    selected__all_keys = all_keys = empty_key_list

    def keys_str(self):
        return ''

class Menu(object):
    def __init__(self, game, options):
        self.game = game
        self.options = options
        self.counter = 0
        self.surface = pygame.Surface(config.MENU_AREA_SIZE, pygame.SWSURFACE)
        self.surface.set_alpha(254 * config.MENU_ALPHA)
        
        self.enabled = False

    def is_enabled(self):
        return self.enabled
        
    def enable(self):
        self.enabled = True
        self.selected_index = -1
        self._move_selected_index(1)
        
    def disable(self):
        self.enabled = False
        self.game.update_message()
        
    def draw(self, target_surface):
        if not self.enabled:
            return
        self.surface.fill(config.MENU_AREA_COLOR)
        rect = pygame.Rect((0, 0), config.MENU_AREA_SIZE)
        self._draw_text()
        pygame.draw.rect(self.surface,
                         config.MENU_BOUNDS_RECT_COLOR, rect,
                         config.MENU_BOUNDS_RECT_WIDTH)
        target_surface.blit(self.surface, (0, 0))
        self.counter += 1
        
    def _draw_text(self):
        circles_per_iteration = {
            False : config.MENU_TEXT_CIRCLE_PER_ITERATION_UNSELECTED,
            True : config.MENU_TEXT_CIRCLE_PER_ITERATION_SELECTED,
        }
        y = 5
        for index, option in enumerate(self.options):
            cpi = circles_per_iteration[self.selected_index == index]
            y += self._draw_option(option, cpi, y)
            
    def _draw_option(self, option, cpi, y):
        radiusx = config.MENU_TEXT_CIRCLE_DIAMETERX/2 * option.size
        radiusy = config.MENU_TEXT_CIRCLE_DIAMETERY/2 * option.size
        diameterx = config.MENU_TEXT_CIRCLE_DIAMETERX * option.size
        diametery = config.MENU_TEXT_CIRCLE_DIAMETERY * option.size
        
        line_surface, key_surface = option.line_surfaces()

        height = max([line_surface.get_height() + diametery,
                      key_surface.get_height()])
        option.circle_count += cpi
        width = line_surface.get_width()
        max_width = self.surface.get_width() - config.MENU_KEYS_WIDTH
        assert width < max_width
        radians = option.circle_count * math.pi * 2
        extra_x, extra_y = math.cos(radians) * radiusx, math.sin(radians) * radiusy

        line_x = (max_width - width) / 2 + extra_x
        line_y = y + (height - line_surface.get_height()) / 2 + extra_y
        self.surface.blit(line_surface, (line_x, line_y))

        keys_y = y + (height - key_surface.get_height()) / 2
        keys_offsetx = config.MENU_AREA_SIZE[0] - config.MENU_KEYS_WIDTH
        self.surface.blit(key_surface, (keys_offsetx, keys_y))
        
        return height
    
    def handle_pygame_event(self, event):
        if self.enabled:
            selected_option = self.options[self.selected_index]
            if selected_option.selected__handle_pygame_event(self, event):
                return True
        # Allow keys to be pressed even when out of menu
        for option in self.enabled_options():
            if option.handle_pygame_event(self, event):
                return True
        if event.type == pygame.KEYDOWN:
            return self._handle_keydown(event)
        return False
    def enabled_options(self):
        for option in self.options:
            if option.enabled_func():
                yield option
    def _handle_keydown(self, event):
        if self.enabled:
            delta = 0
            if key_identified(event, config.NEXT_KEY):
                delta = 1
            elif key_identified(event, config.PREV_KEY):
                delta = -1
            if delta:
                self._move_selected_index(delta)
                return True
        return False
    def _move_selected_index(self, delta):
        # Find next
        count = 0
        while True:
            count += 1
            assert count <= len(self.options), "No enabled options"
            self.selected_index += delta
            self.selected_index %= len(self.options)
            selected_option = self.options[self.selected_index]
            if selected_option.enabled_func():
                break
        self.game.set_text(selected_option.description)
    def all_keys(self):
        keys = ([config.NEXT_KEY, config.PREV_KEY] +
                sum([option.all_keys()
                     for option in self.enabled_options()], []))
        if self.enabled:
            selected_option = self.options[self.selected_index]
            keys += selected_option.selected__all_keys()
        return keys
