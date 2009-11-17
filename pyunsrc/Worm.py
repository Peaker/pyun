import math
import weakref
from sets import Set as set
from util import forwarded_pos, angle_towards
from configfile import config

import pygame

import Canvas

class Collision(Exception): pass

class Circle(Canvas.Circle):
    def __init__(self, worm, position, diameter):
        self.worm = weakref.ref(worm)
        super(Circle, self).__init__(position, diameter)

class Worm(object):
    def __init__(self, random, worm_area_size, net_config, worm_area, color):
        self._random = random
        self.worm_area_size = width, height = worm_area_size
        self.center = width/2, height/2
        self.net_config = net_config
        self._worm_area = worm_area
        self.color = color

        self._circles_to_draw = []
        self._last_collisions = set()

    def reset(self, position):
        self.position = position
        self.angle = angle_towards(position, self.center)
        self._current_circle = None
        self._hole_circle = self._old_hole_circle = None
        self._old_eyes = self._eyes = []
        
        del self._circles_to_draw[:]
        self._last_collisions.clear()

        self._start_drawing()

    def _undraw_temporary(self):
        if self._old_hole_circle is not None:
            self._worm_area.undraw_circle(self._old_hole_circle, self.net_config.DIAMETER)
        for eye in self._old_eyes:
            self._worm_area.undraw_circle(eye, config.WORM_EYE_DIAMETER)

    def _post_draw(self):
        # Draw the eyes/holes separately
        if self._hole_circle is not None:
            self._worm_area.draw_circle(self.color, self._hole_circle, self.net_config.DIAMETER)
        for eye in self._eyes:
            self._worm_area.draw_circle([x^255 for x in self.color],
                                        eye, config.WORM_EYE_DIAMETER)
        del self._circles_to_draw[:-1]

    def draw_differentially(self):
        self._undraw_temporary()

        # Leave the last hole to redraw, to restore what was behind
        # the old hold circle we removed
        for position in self._circles_to_draw:
            self._worm_area.draw_circle(self.color, position, self.net_config.DIAMETER)

        self._post_draw()

    def draw_full(self):
        for circle in self._worm_area.canvas.items():
            self._worm_area.draw_circle(circle.worm().color, circle.position, circle.diameter)
        
        self._post_draw()
    
    def show(self):
        fog_diameter = self.net_config.FOG_VISION_DIAMETER
        vision_circle = Canvas.Circle(self._current_position(), fog_diameter)
        for circle in self._worm_area.canvas.collisions(vision_circle):
            x1, y1 = circle.position
            x2, y2 = self.position
            sqr_distance = ((x1-x2)**2 + (y1-y2)**2)
            self._worm_area.show_circle(sqr_distance, circle)

        self._post_draw()

    def left(self, angle_diff):
        self.angle -= angle_diff
    def right(self, angle_diff):
        self.angle += angle_diff
    def forward(self, speed):
        self._old_eyes = self._eyes

        self._forward_body(speed)
        
        self._eyes = []
        if self.net_config.FOG_ENABLED:
            self._eyes = [forwarded_pos(self.position, self.angle-30, self.net_config.DIAMETER/2),
                          forwarded_pos(self.position, self.angle+30, self.net_config.DIAMETER/2)]

    def _forward_body(self, speed):
        self._old_hole_circle = self._hole_circle

        self._forward_split(speed)

    def _forward_split(self, speed):
        max_single_movement = min(3, self.net_config.DIAMETER//3)
        while speed > max_single_movement:
            self._forward(max_single_movement)
            speed -= max_single_movement
        self._forward(speed)
        
    def _collides_with_wall(self):
        x, y = self.position
        width, height = self.worm_area_size
        return (x < self.net_config.DIAMETER/2 or
                y < self.net_config.DIAMETER/2 or
                x > width-self.net_config.DIAMETER/2 or
                y > height-self.net_config.DIAMETER/2)

    def _current_position(self):
        return tuple(map(int, self.position))
    
    def _forward_current_hole(self, movement):
        if self._counter <= 0:
            self._start_drawing()
        self._counter -= movement

        position = self._current_position()
        self._hole_circle = position
        self._current_circle = Circle(self, position, self.net_config.DIAMETER)
        
    def _forward_current_paint(self, movement):
        if self._counter <= 0:
            self._start_hole()
        self._counter -= movement

        position = self._current_position()
        self._circles_to_draw.append(position)
        
        self._current_circle = Circle(self, position, self.net_config.DIAMETER)
        self._worm_area.canvas.add(self._current_circle)
        
        self._hole_circle = None
    
    def _start_drawing(self):
        self._counter = self._random().randrange(self.net_config.MIN_DRAW_SIZE,
                                                 self.net_config.MAX_DRAW_SIZE)
        self._forward_current = self._forward_current_paint
    def _start_hole(self):
        self._counter = self._random().randrange(self.net_config.MIN_HOLE_SIZE,
                                                 self.net_config.MAX_HOLE_SIZE)
        self._forward_current = self._forward_current_hole

    def _forward(self, delta):
        self.position = forwarded_pos(self.position, self.angle, delta)

        if self._collides_with_wall():
            raise Collision()

        self._forward_current(delta)

        # The following allows detection of collisions only with
        # things we stopped colliding with and re-collided with
        
        new_collisions = set(self._worm_area.canvas.collisions(self._current_circle))
        if new_collisions - self._last_collisions - set([self._current_circle]):
            raise Collision()

        self._last_collisions = new_collisions
