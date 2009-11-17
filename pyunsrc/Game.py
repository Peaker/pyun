import weakref
import time
import pygame
import pools
import network
import instructions
import menus
import os
import DictAttrAccessor

import configfile
from configfile import config
from sets import Set as set
from Bunch import Bunch
from log import warning, debug_log
from util import font_height, get_computer_name

from Hud import Hud
from Player import PlayerDied, Player
from PlayerController import PlayerController
from WormArea import WormArea
from GameControllers import GenericGameController, GameController
from Credits import Credits

from pygame_keys import key_name
from version import VERSION

class KillRequest(Exception): pass

class Game(object):
    def __init__(self, network_mode):
        self.network_mode, self.local_name, self.network_data = network_mode
        self._pause_state = None
        self._is_started = False
        self._all_controllers = []
        self.player_controllers = {}

        # The network object must exist early
        self._init_network()
        
        self.generic_controller = GenericGameController(self._weakref())
        self.register_controller(self.generic_controller, priority=1)
        self._last_waiting_for_players = 0

        self._init_graphics()

        # Start network only after graphics is set up
        self._start_network()

        self.worm_area = WormArea(self._weakref(), self.worm_area_surface)

        self.update_message()

    def can_start_game(self):
        return not self._is_started and self.is_network_game()

    def can_unpause(self):
        # Can only unpause if paused and at least 2 players are online
        return self.is_paused() and len(list(self.all_players())) >= 2

    def can_pause(self):
        return self._is_started and not self.is_paused()

    def is_local_player(self, player):
        return player in self.network.local_host.players

    def _init_graphics(self):
        self._display_flags = 0
        self._setup_display()
        
        self.worm_area_surface = pygame.Surface(config.WORM_AREA_SIZE, pygame.SWSURFACE)
        
        self._init_font()
        self._init_text()
        self._init_hud()
        self._instructions_surface = None
        self._init_menus()
        self.credits = None

    def _net_config_accessor(self, name):
        def get():
            return getattr(self.net_config, name)
        def set(value):
            self.network.run_action_on_all('netconfig_setattr', name, value)
        return get, set

    def get_latency(self):
        return self.network.latency
    
    def _init_menus(self):
        self.menus = menus.create_menus(self._weakref())
        for menu in self.menus:
            self.register_controller(getattr(self.menus, menu), priority=0)

    def _start_game(self):
        self.common_random_seed = self.random().randrange(1L<<32)
        self._is_started = True
        self._instructions_surface = None
        self.controller = GameController(self._weakref())
        self.register_controller(self.controller, priority=5)
        self._start_pause_and_reset_game()

    def _weakref(self):
        return weakref.proxy(self)

    def save_net_config(self):
        filename = configfile.save_net_config(DictAttrAccessor.dict(self.net_config))
        self.add_text('Saved configuration to %s' % (os.path.realpath(filename),))
    
    def save_config(self):
        filename = configfile.save_config(config)
        self.add_text('Saved configuration to %s' % (os.path.realpath(filename),))

    def _init_network(self):
        if self.network_mode == 'local':
            self.network = network.Hoster(self._weakref(), get_computer_name(),
                                          publicized_data=configfile.default_net_config)
        else:
            if self.network_mode == 'listen':
                self.network = network.Listener(self._weakref(), self.local_name,
                                                port=self.network_data,
                                                protocol_version=VERSION,
                                                publicized_data=configfile.default_net_config)
            else:
                assert self.network_mode == 'connect'
                self.network = network.Connector(self._weakref(), self.local_name,
                                                 address=self.network_data,
                                                 protocol_version=VERSION)
            self._clock_tick = self._pregame_clock_tick

    def _start_network(self):
        if self.network_mode != 'local':
            self.network.start_connecting()
            self._instructions_surface = self._pregame_instructions_surface
        self._set_net_config(self.network.publicized_data())
        if self.network_mode == 'local':
            self._start_game()
        else:
            self.network.latency = self.net_config.LATENCY

    def _pregame_clock_tick(self, is_net_iteration):
        pass

    def all_players(self):
        for host in self.network.hosts:
            for player in host.players:
                yield player
    
    def living_players(self):
        for player in self.all_players():
            if player.alive:
                yield player

    def is_network_game(self):
        return len(self.network.hosts) >= 2

    def is_paused(self):
        return self._pause_state is not None

    def is_fullscreen(self):
        return bool(self._display_flags & pygame.FULLSCREEN)

    def set_fullscreen(self, value):
        self._display_flags &= ~pygame.FULLSCREEN
        if value:
            self._display_flags |= pygame.FULLSCREEN
        size = self.display.get_size()
        copy = pygame.Surface(size, pygame.SWSURFACE)
        copy.blit(self.display, (0, 0))
        pygame.display.quit()
        pygame.display.init()
        self._setup_display()
        self.display.blit(copy, (0, 0))

    def all_keys(self):
        return sum([list(controller.all_keys())
                    for priority, controller in self._all_controllers],
                   [])

    def register_controller(self, controller, priority):
        self._all_controllers.append((priority, controller))
        self._all_controllers.sort()
    def unregister_controller(self, controller):
        for index, (cur_priority, cur_controller) in enumerate(self._all_controllers):
            if cur_controller == controller:
                break
        else:
            raise KeyError("Can't find specified controller")
        self._all_controllers.pop(index)

    def update_message(self):
        player_count = len(list(self.all_players()))
        if not self.is_paused():
            # The game is running, don't bother...
            text = ''
        elif player_count < 2:
            if 2 - player_count == 1:
                p = 'player'
            else:
                p = '2 players'
            text = 'Another %s must be created to start a game' % (p,)
        else:
            text = 'Press %s to start the game' % (key_name(config.PAUSE_KEY),)
        self.set_text(text)

    def get_text(self):
        return self._current_text
    
    def set_text(self, text):
        self._current_text = text
        self._current_text_surface = self._font.render(text, True, config.TEXT_COLOR)

    def add_text(self, text):
        if len(self._texts) >= config.TEXTS_MAX_COUNT:
            self._texts.pop(0)
        self._texts.append((time.time(), text))

    def exit(self):
        raise KillRequest()

    def _run(self):
        counter = 0
        self._clock = pygame.time.Clock()
        while True:
            counter += 1
            is_net_iteration = (counter >= self.net_config.NET_INTERVAL)
            self._clock.tick(self.net_config.GAME_ITERATIONS_PER_SECOND)
            self.handle_all_events()
            self._clock_tick(is_net_iteration)
            self._draw()
            if is_net_iteration:
                self.network.update()
                self.execute_actions()
                counter = 0

    def run(self):
        try:
            self._run()
        except KillRequest:
            pass

    def execute_actions(self):
        for host, host_actions in self.network.iteration_actions():
            for action_str, action_args in host_actions:
                action = getattr(self, '_action__%s' % (action_str,))
                action(host, *action_args)

    def _start_pause(self, after_pause_callback,
                     required_unpausers=set()):
        self._clock_tick = self._pause_clock_tick
        
        self._pause_state = ps = Bunch()
        self._instructions_surface = self._paused_instructions_surface
        ps.required_unpausers = required_unpausers
        ps.unpausers = set()
        ps.callback = after_pause_callback
        
        self.update_message()

    def _to_game_state(self):
        self._clock_tick = self._game_clock_tick

    def _init_font(self):
        self._font = pygame.font.SysFont('', config.TEXT_FONT_SIZE)
        self._texts_font = pygame.font.SysFont('', config.TEXTS_FONT_SIZE)

    def _init_text(self):
        self._texts = []

    def _init_hud(self):
        self.hud = Hud(self._weakref())

    def _instructions_line(self, (boolean, line)):
        if boolean:
            return config.ENABLED_INSTRUCTIONS_COLOR, line
        else:
            return config.DISABLED_INSTRUCTIONS_COLOR, line

    def _paused_instructions_surface(self):
        lines = map(self._instructions_line, [
            (True, "PAUSED"),
            (True, ""),
            (True, "Press %s to invoke the menu" % (key_name(config.MENU_KEY),)),
            (True, "Press %s,<leftkey>,<rightkey> to create a player" %
             (key_name(config.CREATE_PLAYER_KEY),)),
            (len(list(self.all_players())) >= 1,
             "Press %s/%s to select a player" % (key_name(config.PREV_KEY),
                                                 key_name(config.NEXT_KEY))),
            (self.controller.chosen_host() is self.network.local_host,
             "Press %s to remove the selected player" % (key_name(config.REMOVE_PLAYER_KEY),)),
            (self.can_unpause(), "Press %s to unpause the game" % (key_name(config.PAUSE_KEY),)),
            (self.is_network_game(), "Press %s to send a text message" % (key_name(config.SEND_TEXT_KEY),)),
        ])
        return instructions.create_surface(lines)

    def _pregame_instructions_surface(self):
        lines = map(self._instructions_line, [
            (True, "GAME SETUP"),
            (True, ""),
            (True, "Press %s to invoke the menu" % (key_name(config.MENU_KEY),)),
            (self.is_network_game(), ""),
            (self.is_network_game(), "Press %s to start the game" % (key_name(config.START_GAME_KEY),)),
            (self.is_network_game(), "Press %s to send a text message" % (key_name(config.SEND_TEXT_KEY),)),
        ])
        return instructions.create_surface(lines)

    def _set_net_config(self, net_config_dict):
        self.net_config_dict = net_config_dict.copy()
        self.net_config = DictAttrAccessor.DictAttrAccessor(self.net_config_dict)
    
    def _setup_display(self):
        self.display = pygame.display.set_mode(config.DISPLAY_MODE, self._display_flags)
        self.hud_area = self.display.subsurface((config.HUD_AREA_POS, config.HUD_AREA_SIZE))
        self.menu_area = self.display.subsurface((config.MENU_AREA_POS, config.MENU_AREA_SIZE))
    
    def _handle_pygame_event(self, event):
        for priority, controller in self._all_controllers[:]:
            if controller.handle_pygame_event(event):
                break

    def _draw(self):
        self._draw_worm_area()
        self._draw_instructions()
        
        self.hud.draw(self.hud_area)
        self._draw_bounds_rect()
        self._draw_text()
        self._draw_fps()

        for menu in self.menus.itervalues():
            menu.draw(self.menu_area)

        self._draw_credits()

        pygame.display.update()

    def _draw_worm_area(self):
        self.worm_area.draw()
        self.display.blit(self.worm_area_surface, config.WORM_AREA_POS)
    
    def _draw_credits(self):
        if self.credits is not None:
            self.credits.draw(self.display)

    def _draw_instructions(self):
        if self._instructions_surface is not None:
            self.display.blit(self._instructions_surface(), config.WORM_AREA_POS)

    def _draw_fps(self):
        self.display.fill(config.CLEAR_COLOR, (config.FPS_POS, config.FPS_SIZE))
        
        text = '%.2f' % (self._clock.get_fps(),)
        fps_text_surface = self._font.render(text, True, config.FPS_COLOR)
        fpsx, fpsy = config.FPS_POS
        width, height = config.FPS_SIZE
        x = fpsx + width - fps_text_surface.get_width()
        self.display.blit(fps_text_surface, (x, fpsy))

    def _draw_text(self):
        self.display.fill(config.CLEAR_COLOR, (config.TEXT_AREA_POS, config.TEXT_AREA_SIZE))
        self.display.blit(self._current_text_surface, config.TEXT_AREA_POS)

        if not self._texts:
            return
        for index, (text_time, text) in enumerate(self._texts):
            if text_time + config.TEXTS_EXPIRATION_TIME > time.time():
                # text has not expired yet
                break
            # keep going while texts are expired
        else:
            index = len(self._texts)
        # Get rid of all the expired texts
        self._texts = self._texts[index:]

        x, y = config.TEXTS_LEFT_BOTTOM
        x += config.WORM_AREA_POS[0]
        y += config.WORM_AREA_POS[1]
        # Now x, y are the display-relative position of the bottom of the texts area

        text_height = font_height(self._texts_font)
        height = text_height*len(self._texts)
        y -= height
        # Now x, y are the top of the texts area
        
        for text_time, text in self._texts:
            text_surface = self._texts_font.render(text, True, config.TEXTS_COLOR)
            self.display.blit(text_surface, (x, y))
            y += text_height

    def _draw_bounds_rect(self):
        (x, y), (w, h) = config.WORM_AREA_POS, config.WORM_AREA_SIZE
        rw = config.BOUNDS_RECT_WIDTH
        rect = ((x - rw, y - rw),
                (w + rw, h + rw))
        pygame.draw.rect(self.display, config.BOUNDS_RECT_COLOR, rect, config.BOUNDS_RECT_WIDTH)

    def _update_players(self):
        for player in self.all_players():
            try:
                player.update()
            except PlayerDied:
                for player in self.living_players():
                    player.increase_score()
    
    def _reset_players(self):
        for player in self.all_players():
            player.reset()

    def random(self):
        return self.network.random()

    def _reset(self):
        self.worm_area.clear()
        self._reset_players()
        self._last_speed_increase = self.network.iteration_count
        self.speed = (float(self.net_config.INITIAL_SPEED) /
                      self.net_config.GAME_ITERATIONS_PER_SECOND)
    
    def _reset_back_to_game(self):
        self._reset()
        self._to_game_state()

    def _pause_clock_tick(self, is_net_iteration):
        pass

    def _game_clock_tick(self, is_net_iteration):
        if is_net_iteration:
            self._sync_key_states()
        
        self._game_increase_speed()
        self._update_players()
        
        if len(list(self.living_players())) <= 1:
            self._start_pause_and_reset_game()

    def _start_pause_and_reset_game(self):
        self._start_pause(self._reset_back_to_game)

    def handle_all_events(self):
        for event in pygame.event.get():
            self._handle_pygame_event(event)

    def _game_increase_speed(self):
        speed_increase_iterations = (float(self.net_config.SPEED_INCREASE_INTERVAL) *
                                     self.net_config.GAME_ITERATIONS_PER_SECOND /
                                     self.net_config.NET_INTERVAL)
        if self.network.iteration_count - self._last_speed_increase >= speed_increase_iterations:
            self.add_text("Speeding up!")
            self.speed *= self.net_config.SPEED_INCREASE
            self._last_speed_increase = self.network.iteration_count
    
    def _sync_key_states(self):
        keys_states = [self.player_controllers[player].current_keys_state
                       for player in self.network.local_host.players]
        self.network.run_action_on_all('update_keys_states', keys_states)

    def _find_player_in_host(self, host, player_name):
        for player_index, player in enumerate(host.players):
            if player.name == player_name:
                return player_index, player
        return None

    def _remove_player(self, host, player_name):
        player_index, player = self._find_player_in_host(host, player_name)
        if player is None:
            warning("Request to remove inexistent player, ignoring...")
            return
        pools.colors.insert(0, (player.name, player.color()))
        host.players.pop(player_index)
        self.update_message()
        return player

    def _create_player(self, host):
        if not pools.colors:
            self.set_text('No more worms available!')
            return
        name, color = pools.colors.pop(0)

        player = Player(self._weakref(), name, color)
        host.players.append(player)
        self.update_message()
        return player

    # Network event handlers
    def network__timeout_group_add(self, host): pass
    def network__timeout_group_remove(self, host): pass
    def network__iteration_done(self): pass

    def network__timeout(self):
        # During timeout, network code contains mainloop, so we must
        # draw in it...
        host_names = ', '.join([host.name for host in self.network.timeout_group])
        if time.time() - self._last_waiting_for_players > config.TIME_BETWEEN_WAITING_FOR_PLAYERS:
            self._last_waiting_for_players = time.time()
            self.add_text('Waiting for %s' % host_names)
        self.handle_all_events()
        self._draw()

    def network__host_added(self, host):
        host.players = []

    def network__host_connected(self, host):
        self.add_text("Connected to %s" % (host.name,))
    
    def network__host_removed(self, host):
        self.add_text("%s has left the game" % (host.name,))
        
    def network__new_connector1(self, remote_host_name, remote_address): pass
    def network__new_connector2(self, remote_host_name, remote_address): pass
    def network__got_first_connection(self): pass
    def network__in_network(self):
        self.add_text("Join game complete")

    def network__hosting_new_host(self, remote_host): pass

    def show_credits(self):
        self.credits = Credits(self._weakref())
        self.register_controller(self.credits, priority=0)

    def unshow_credits(self):
        self.unregister_controller(self.credits)
        self.credits = None
    
    # Action handlers
    def _action__add_interval(self, src_host, count):
        self.net_config.NET_INTERVAL = max(1, self.net_config.NET_INTERVAL+count)
        self.add_text('%s set net interval to %d' % (src_host.name, self.net_config.NET_INTERVAL))

    def _action__update_keys_states(self, src_host, keys_states):
        for player, new_keys_state in zip(src_host.players, keys_states):
            # Update the players' key states
            player.keys_state = new_keys_state

    def _action__create_player(self, src_host):
        self._create_player(src_host)

    def _action__create_local_player(self, src_host, worm_keys):
        player = self._create_player(self.network.local_host)
        
        player_controller = PlayerController(player, worm_keys)
        self.register_controller(player_controller, priority=6)
        self.player_controllers[player] = player_controller

    def _action__remove_player(self, src_host, player_name):
        self._remove_player(src_host, player_name)

    def _action__remove_local_player(self, src_host, player_name):
        player = self._remove_player(src_host, player_name)
        assert src_host is self.network.local_host
        self.unregister_controller(self.player_controllers[player])
        del self.player_controllers[player]

    def _action__unpause(self, src_host):
        if not self.can_unpause():
            return
        ps = self._pause_state
        ps.unpausers.add(src_host)
        if not (ps.required_unpausers - ps.unpausers):
            # Unpause conditions filled
            if src_host is not self.network.local_host:
                self.add_text("%s has unpaused game" % (src_host.name,))
            callback = ps.callback
            self._pause_state = self._instructions_surface = None
            self.update_message()
            callback()

    def _action__pause(self, src_host):
        if not self.is_paused():
            if src_host is not self.network.local_host:
                self.add_text('%s has paused the game.' % (src_host.name,))
            required_unpausers = set()
            if self.net_config.ONLY_PAUSER_CAN_UNPAUSE:
                required_unpausers.add(src_host)
            self._start_pause(self._to_game_state,
                              required_unpausers=required_unpausers)
    
    def _action__send_text(self, src_host, text):
        self.add_text('From %s: %s' % (src_host.name, text))
    
    def _action__show_sent_text(self, src_host, to, text):
        assert src_host is self.network.local_host
        self.add_text('To %s: %s' % (to, text))
    
    def _action__start_game(self, src_host):
        if self._is_started or len(self.network.hosts) <= 1:
            return
        if src_host is not self.network.local_host:
            self.add_text("%s has started the game" % (src_host.name,))
        self.network.stop_connecting()
        self._start_game()
        
    def _action__set_latency(self, host, latency):
        self.add_text("%s set latency to %d" % (host.name, latency))
        self.net_config.LATENCY = latency
        self.network.latency = latency

    # List of allowed net_config options to change
    def _action__netconfig_setattr(self, src_host, name, value):
        self.add_text("%s set %s to %s" %
                      (src_host.name, name, value))
        setattr(self.net_config, name, value)
