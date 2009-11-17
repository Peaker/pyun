from Worm import Collision
from configfile import config
from util import random_of
from Worm import Worm
import math
import PlayerController

class PlayerDied(Exception): pass

class Player(object):
    def __init__(self, game, name, color):
        self.game = game
        self.name = name
        self.score = 0
        self.keys_state = 0
        self.alive = True

        common_randomizer = random_of(self.game.common_random_seed)
        def random():
            if self.game.net_config.WORM_SYNC_HOLES:
                return common_randomizer
            else:
                return self.game.random()
        self.worm = Worm(random, config.WORM_AREA_SIZE,
                         self.game.net_config, self.game.worm_area, color)
        self.reset()
    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self.name)
    def color(self):
        return self.worm.color
    def reset(self):
        """Resets the player and worm parameters to level-start state.
        
        Note this uses random and is therefore only callable after
        random seed synchronization (or followed by a
        sync_players_states)"""
        width, height = config.WORM_AREA_SIZE
        outline_width = config.POS_RANDOM_OUTLINE_WIDTH
        random = self.game.random()
        pos = (random.randrange(outline_width, width - outline_width),
               random.randrange(outline_width, height - outline_width))
        self.worm.reset(pos)
        self.alive = True
    def kill(self):
        self.alive = False
    def increase_score(self):
        self.score += 1
    def update(self):
        if not self.alive:
            return
        angle_diff = math.radians(float(self.game.net_config.ANGLES_PER_SECOND) /
                                  self.game.net_config.GAME_ITERATIONS_PER_SECOND)
        if self.keys_state & PlayerController.LEFT:
            self.worm.left(angle_diff)
        elif self.keys_state & PlayerController.RIGHT:
            self.worm.right(angle_diff)
        try:
            self.worm.forward(self.game.speed)
        except Collision:
            self.kill()
            raise PlayerDied()

    def key_event(self, is_down, event):
        # Ignore keys by default
        pass
