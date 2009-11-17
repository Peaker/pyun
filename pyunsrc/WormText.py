import pygame
import math
from configfile import config
from util import forwarded_pos
from BoundFunc import BoundFunc
from worm_letter_plans import worm_letter_plans

INITIAL_SPEED = 1.5

class WormPainter(object):
    def __init__(self, position, angle, color, diameter, speed_factor, plan):
        self.color = color
        self.speed = speed_factor * INITIAL_SPEED
        self.position = position
        self.angle = math.radians(angle)
        self.diameter = diameter
        self.plan = list(plan)
        self._next_plan_stage()
    def move(self, (dx, dy)):
        x, y = self.position
        x += dx
        y += dy
        self.position = x, y
    def forward(self, surface):
        count = self.speed
        while count > 0:
            MAX_SINGLE_MOVEMENT = 3
            self.position = forwarded_pos(self.position, self.angle, min(count, MAX_SINGLE_MOVEMENT))
            count -= MAX_SINGLE_MOVEMENT
            pygame.draw.circle(surface, self.color, map(int, self.position),
                               int(self.diameter/2))
    def done(self, surface):
        return True
    def plan_nothing(self, surface):
        pass
    def plan_left(self, surface, degrees=5):
        self.forward(surface)
        self.angle -= math.radians(degrees)
    def plan_right(self, surface, degrees=5):
        self.forward(surface)
        self.angle += math.radians(degrees)
    def plan_forward(self, surface):
        self.forward(surface)

    def _next_plan_stage(self):
        if not self.plan:
            self.iteration = self.done
            return
        (method_name, args, kw), self._current_plan_stage_length = self.plan.pop(0)
        planned_stage = BoundFunc(getattr(self, 'plan_%s' % (method_name,)), *args, **kw)
        def run_planned_stage(*args, **kw):
            planned_stage(*args, **kw)
            if self._current_plan_stage_length <= 0:
                self._next_plan_stage()
            self._current_plan_stage_length -= 1
        self.iteration = run_planned_stage

def letter_worm_painters((x, y), color, diameter, speed_factor,
                         ((width, height), plans)):
    for (plan_pos, plan_angle), plan in plans:
        plan_x, plan_y = plan_pos
        position = x + plan_x, y + plan_y
        yield WormPainter(position, plan_angle, color, diameter, speed_factor, plan)

def text_letter_painters(color, diameter, speed_factor, text):
    x = diameter/2
    y = diameter/2
    max_height = 0
    letter_painters = []
    for letter in text:
        (width, height), plans = worm_letter_plans[letter]
        letter_painters.append(letter_worm_painters((x, y), color, diameter, speed_factor,
                                                    ((width, height), plans)))
        x += width + diameter/2
        max_height = max(height, max_height)
    return (x, max_height), letter_painters

class WormText(object):
    def __init__(self, text):
        self._text = text
        
        self.size, text_painters = text_letter_painters(
            config.CREDITS_WORM_TEXT_COLOR,
            config.CREDITS_WORM_DIAMETER, 1.0, text)

        self._text_painters = iter(text_painters)
        self._current_worm_painters = []
        
    def draw(self, surface):
        for worm_painter in self._current_worm_painters[:]:
            if worm_painter.iteration(surface):
                self._current_worm_painters.remove(worm_painter)
        if not self._current_worm_painters:
            try:
                self._current_worm_painters = list(self._text_painters.next())
            except StopIteration:
                return True
