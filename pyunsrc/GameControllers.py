import pygame
from pygame_keys import key_name
from util import key_identified
from configfile import config

class BaseGameController(object):
    def __init__(self, game):
        self.game = game
    def handle_pygame_event(self, event):
        if event.type == pygame.KEYDOWN:
            return self._handle_keydown(event)
        return False

class GenericGameController(BaseGameController):
    """This controller lives the whole game (pregame/started/paused)."""
    def __init__(self, game):
        super(GenericGameController, self).__init__(game)
        self._handle_keydown = self._handle_keydown_normal
    def handle_pygame_event(self, event):
        if super(GenericGameController, self).handle_pygame_event(event):
            return True
        if event.type == pygame.QUIT:
            self.game.exit()
        return False
    def all_keys(self):
        keys = [
            config.CANCEL_KEY,
        ]
        if not self.game.menus.main.enabled:
            keys += [
                config.MENU_KEY,
            ]
        if self.game.is_network_game():
            keys += [
                config.SEND_TEXT_KEY,
            ]
        return keys
    def _send_text_msg(self, to_selected, text):
        if not text.strip():
            return True
        if to_selected:
            # To chosen player(host)
            if self.game._is_started:
                chosen_host = self.game.controller.chosen_host()
                if chosen_host is self.game.network.local_host:
                    self.game.add_text("Cannot send to self!")
                    return False
                if chosen_host is not None:
                    self.game.network.run_action_on(chosen_host, 'send_text', text)
                    self.game.network.run_action_locally('show_sent_text',
                                                         chosen_host.name, text)
                    return True
            self.game.add_text("No chosen host!")
            return False
        else:
            self.game.network.run_action_remotely('send_text', text)
            self.game.network.run_action_locally('show_sent_text', 'all', text)
            return True
    def _send_text_key_pressed(self):
        cur_text = [None]
        def update_text(new_text):
            cur_text[0] = new_text
            self.game.set_text('Message: %s_' % (cur_text[0],))
        update_text('')
        def chat_key_pressed(event):
            if key_identified(event, (0, pygame.K_BACKSPACE)):
                update_text(cur_text[0][:-1])
                return
            for to_selected, key in [(False, config.SEND_TO_ALL_KEY),
                                     (True, config.SEND_TO_HOST_KEY)]:
                if key_identified(event, key):
                    if self._send_text_msg(to_selected, cur_text[0]):
                        self.game.update_message()
                        self._handle_keydown = self._handle_keydown_normal
                    return False
            if key_identified(event, config.CANCEL_KEY):
                self.game.update_message()
                self._handle_keydown = self._handle_keydown_normal
                return False
            try:
                key_value = event.unicode.encode('latin1')
            except UnicodeEncodeError:
                return False
            if len(key_value) != 1 or not 0x20 <= ord(key_value) < 0x80:
                return False
            update_text(cur_text[0] + key_value)
            return False
        self._handle_keydown = chat_key_pressed
    def _handle_keydown_normal(self, event):
        if not self.game.menus.main.enabled and key_identified(event, config.MENU_KEY):
            self.game.menus.main.enable()
            return True
        if self.game.is_network_game():
            if key_identified(event, config.SEND_TEXT_KEY):
                self._send_text_key_pressed()
            # Don't steal the key in any case
            return False
        
class GameController(BaseGameController):
    """This controller lives while the game is started."""
    def __init__(self, game):
        super(GameController, self).__init__(game)
        self._handle_keydown = self._handle_keydown_normal
        self._chosen_player_index = 0

    def chosen_host(self):
        player = self.chosen_player()
        if player is None:
            return None
        for host in self.game.network.hosts:
            if player in host.players:
                return host
        assert 0, "Chosen player not in any host"

    def chosen_player(self):
        self._chosen_player_index %= max(len(list(self.game.all_players())), 1)
        
        all_players = list(self.game.all_players())
        if self._chosen_player_index >= len(all_players):
            return None
        return all_players[self._chosen_player_index]

    def all_keys(self):
        return [config.CREATE_PLAYER_KEY, config.REMOVE_PLAYER_KEY,
                config.PREV_KEY, config.NEXT_KEY]
    def _create_player_key_pressed(self):
        worm_keys = []
        def worm_key_setter_handler(event):
            if key_identified(event, config.CREATE_PLAYER_KEY):
                self.game.set_text('Player creation cancelled')
                self._handle_keydown = self._handle_keydown_normal
                return False
            key_value = (0, event.key)
            keyname = key_name(key_value)
            if not config.ALLOW_SAME_KEYS and key_value in self.game.all_keys() + worm_keys:
                # Key already mapped
                if self.game.is_paused():
                    self.game.set_text('%s is already taken!' % (keyname,))
                return False
            worm_keys.append(key_value)
            if len(worm_keys) == 1:
                self.game.set_text('%s is a nice choice! Now press <rightkey>' % (keyname,))
            elif len(worm_keys) == 2:
                self.game.network.run_action_locally('create_local_player', worm_keys)
                self.game.network.run_action_remotely('create_player')
                self._handle_keydown = self._handle_keydown_normal
            return False
        self.game.set_text("Now choose worm's left and right keys")
        self._handle_keydown = worm_key_setter_handler
    def _handle_keydown_normal(self, event):
        if key_identified(event, config.CREATE_PLAYER_KEY):
            self._create_player_key_pressed()
        elif key_identified(event, config.REMOVE_PLAYER_KEY):
            self._remove_chosen_player()
        elif key_identified(event, config.PREV_KEY):
            self._chosen_player_index -= 1
        elif key_identified(event, config.NEXT_KEY):
            self._chosen_player_index += 1
        return False
    def _remove_chosen_player(self):
        chosen_player = self.chosen_player()
        if not chosen_player:
            return
        if not self.game.is_local_player(chosen_player):
            self.game.set_text('Can only remove players on this host')
        else:
            self.game.network.run_action_remotely('remove_player', chosen_player.name)
            self.game.network.run_action_locally('remove_local_player', chosen_player.name)
