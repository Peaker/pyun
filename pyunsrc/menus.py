import Menu
from ADict import ADict
from BoundFunc import BoundFunc
from util import accessor
from configfile import config

NETCONFIG_TEXT_SIZE, NETCONFIG_KEYS_TEXT_SIZE = config.MENU_NETCONFIG_FONT_SIZES

def create_menus(game):
    menus = ADict()
    net_config_kw = dict(text_size=NETCONFIG_TEXT_SIZE, keys_text_size=NETCONFIG_KEYS_TEXT_SIZE)

    def netconfig_number_option(pretty_name, net_config_name, (min, max, jump),
                                with_small_font=True,
                                enabled_func=Menu.always,
                                **kw):
        if with_small_font:
            kw.update(net_config_kw)
        return Menu.NumberOption(
            enabled_func = enabled_func,
            option_name = Menu.text(pretty_name),
            accessor = game._net_config_accessor(net_config_name),
            min = min, max = max, jump = jump,
            **kw)

    def netconfig_bool_option(pretty_name, net_config_name,
                              description):
        return Menu.BooleanOption(enabled_func = Menu.always,
                                  option_name = Menu.text(pretty_name),
                                  accessor = game._net_config_accessor(net_config_name),
                                  keys = [],
                                  description = description,
                                  **net_config_kw)

    def common_net_options(menu_is_enabled, leave_menu):
        return [
            Menu.Splitter(),
            Menu.EventOption(enabled_func = Menu.always,
                             action = game.save_net_config,
                             text = Menu.text('Save network options'),
                             keys = [],
                             description = 'Save options to net_config.py'),
            Menu.Splitter(),
            Menu.EventOption(enabled_func = menu_is_enabled,
                             action = leave_menu,
                             text = Menu.text('Leave Menu'),
                             keys = [config.CANCEL_KEY, config.MENU_KEY],
                             steal_key = True),
        ]

    options = [
        netconfig_number_option('Game Speed', 'GAME_ITERATIONS_PER_SECOND',
                                (20, 60, 5),
                                description='The number of game iterations/second'),
        netconfig_number_option('Initial Worm Speed', 'INITIAL_SPEED',
                                (1, 1000, 2),
                                description='The initial worm speed when the game starts'),
        netconfig_number_option('Worm turn speed', 'ANGLES_PER_SECOND',
                                (1, 1000, 2),
                                description='The speed the worm turns (Angles per second)'),

        netconfig_number_option('Speed increase interval', 'SPEED_INCREASE_INTERVAL',
                                (1, 1000, 1),
                                description='The amount of time in seconds between increasing worm speed'),
        netconfig_number_option('Speed increase ratio', 'SPEED_INCREASE',
                                (0.05, 1000, 0.01),
                                description='The multiplier of the worm speed'),

        netconfig_number_option('Min draw length', 'MIN_DRAW_SIZE',
                                (1, 1000, 2),
                                description='The minimal length of the distance between holes'),
        netconfig_number_option('Max draw length', 'MAX_DRAW_SIZE',
                                (1, 1000, 2),
                                description='The maximal length of the distance between holes'),

        netconfig_number_option('Min hole length', 'MIN_HOLE_SIZE',
                                (1, 1000, 2),
                                description='The minimal length of the worm holes'),
        netconfig_number_option('Max hole length', 'MAX_HOLE_SIZE',
                                (1, 1000, 2),
                                description='The maximal length of the worm holes'),
        netconfig_number_option('Worm size', 'DIAMETER',
                                (1, 1000, 1),
                                description='The size of the worm'),
        netconfig_bool_option('Fog enabled', 'FOG_ENABLED',
                              description='Fog is enabled'),
        netconfig_number_option('Fog vision diameter', 'FOG_VISION_DIAMETER',
                                (0, 1000, 10),
                                enabled_func=lambda : game.net_config.FOG_ENABLED,
                                description='The diameter of the vision in fog'),
    ] + common_net_options(lambda : menus.obscure_net_options.is_enabled(),
                           lambda : menus.net_options.enable())
    menus.obscure_net_options = Menu.Menu(game, options)
    
    options = [
        Menu.BooleanOption(enabled_func = game.is_network_game,
                           option_name = Menu.text('Only pauser can unpause'),
                           accessor = game._net_config_accessor('ONLY_PAUSER_CAN_UNPAUSE'),
                           keys = []),
        Menu.BooleanOption(enabled_func = Menu.always,
                           option_name = Menu.text('Synchronized holes'),
                           accessor = game._net_config_accessor('WORM_SYNC_HOLES'),
                           keys = []),
        Menu.NumberOption(enabled_func = Menu.always,
                          option_name = Menu.text('Latency'),
                          accessor = (game.get_latency,
                                      BoundFunc(game.network.run_action_on_all, 'set_latency')),
                          min = 0, max = 100, jump = 1,
                          description = 'The amount of time it takes the game to respond'),
        netconfig_number_option('Net Interval', 'NET_INTERVAL',
                                 (1, 100, 1),
                                 description='The amount of time between sampling activity',
                                with_small_font=False),
        Menu.EventOption(enabled_func = lambda : not menus.obscure_net_options.is_enabled(),
                         action = menus.obscure_net_options.enable,
                         text = Menu.text('More network Options'),
                         keys = [],
                         steal_key = True),
    ] + common_net_options(lambda : menus.net_options.is_enabled(),
                           Menu.do_nothing)
    menus.net_options = Menu.Menu(game, options)
    
    options = [
        Menu.BooleanOption(enabled_func = Menu.always,
                           option_name = Menu.text('Fullscreen'),
                           accessor = (game.is_fullscreen, game.set_fullscreen),
                           keys = [config.TOGGLE_FULLSCREEN_KEY]),
        Menu.BooleanOption(enabled_func = Menu.always,
                           option_name = Menu.text('Allow same keys'),
                           accessor = accessor(config, 'ALLOW_SAME_KEYS'),
                           keys = [],
                           description='Allow mapping same keys to multiple worms (difficult to add a player in action!)'),
        Menu.EventOption(enabled_func = lambda : not menus.net_options.is_enabled(),
                         action = menus.net_options.enable,
                         text = Menu.text('Network Options'),
                         keys = [],
                         steal_key = True),
        Menu.Splitter(),
        Menu.EventOption(enabled_func = Menu.always,
                         action = game.save_config,
                         text = Menu.text('Save options'),
                         keys = [],
                         description = 'Save options to config.py'),
        Menu.Splitter(),
        Menu.EventOption(enabled_func = lambda : menus.options.is_enabled(),
                         action = Menu.do_nothing,
                         text = Menu.text('Leave Menu'),
                         keys = [config.CANCEL_KEY, config.MENU_KEY, config.OPTIONS_KEY],
                         steal_key = True),
    ]
    menus.options = Menu.Menu(game, options)
    
    options = [
        Menu.EventOption(enabled_func = game.can_start_game,
                         action = BoundFunc(game.network.run_action_on_all, 'start_game'),
                         text = Menu.text('Start Game'),
                         keys = [config.START_GAME_KEY],
                         description = 'Stop listening to new connections and start the game'),
        Menu.EventOption(enabled_func = game.can_unpause,
                         action = BoundFunc(game.network.run_action_on_all, 'unpause'),
                         text = Menu.text('Unpause'),
                         keys = [config.PAUSE_KEY]),
        Menu.EventOption(enabled_func = game.can_pause,
                         action = BoundFunc(game.network.run_action_on_all, 'pause'),
                         text = Menu.text('Pause'),
                         keys = [config.PAUSE_KEY]),
        Menu.EventOption(enabled_func = lambda : not menus.options.is_enabled(),
                         action = menus.options.enable,
                         text = Menu.text('Options'),
                         keys = [config.OPTIONS_KEY],
                         steal_key = True),
        Menu.EventOption(enabled_func = Menu.always,
                         action = game.show_credits,
                         text = Menu.text('Credits'),
                         keys = [],
                         description = 'Who made this damned game?'),
        Menu.EventOption(enabled_func = Menu.always,
                         action = game.exit,
                         text = Menu.text('Exit'),
                         keys = [config.EXIT_KEY],
                         description = 'Go back to the real world'),
        Menu.Splitter(),
        Menu.EventOption(enabled_func = lambda : menus.main.is_enabled(),
                         action = Menu.do_nothing,
                         text = Menu.text('Leave Menu'),
                         keys = [config.CANCEL_KEY, config.MENU_KEY],
                         steal_key = True),
    ]
    menus.main = Menu.Menu(game, options)
    
    return menus
