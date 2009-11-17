import pygame
from pygame_keys import key_name

LEFT = 1
RIGHT = 2

class PlayerController(object):
    def __init__(self, player, keys):
        self.player = player
        self.current_keys_state = 0
        self.left_key, self.right_key = keys
        assert self.left_key[0] == self.right_key[0] == 0, \
               "Modifiers not allowed on player controller keys"
    def all_keys(self):
        return self.left_key, self.right_key
    def handle_pygame_event(self, event):
        if event.type == pygame.KEYDOWN:
            is_down = True
        elif event.type == pygame.KEYUP:
            is_down = False
        else:
            # Uninteresting event
            return False
        # Ignore modifiers on worms
        if event.key == self.left_key[1]:
            bit = LEFT
        elif event.key == self.right_key[1]:
            bit = RIGHT
        else:
            return False
        if is_down:
            self.current_keys_state |= bit
        else:
            self.current_keys_state &= ~bit
        # Don't "steal" the key, no matter what...
        return False
    def control_str(self):
        keys_strs = (key_name(self.left_key), key_name(self.right_key))
        return '%s %s' % keys_strs
