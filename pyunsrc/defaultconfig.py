# ***************************************************
# * Touch only if you know what you're doing!
# ***************************************************

import pygame

config = dict(
    SHOW_HOST_NAME = True,
    SHOW_TOTAL_SCORE = True,

    CLEAR_COLOR = (0,0,0),

    TIME_BETWEEN_WAITING_FOR_PLAYERS = 0.5,

    ALLOW_SAME_KEYS = False,

    # Note the display must be large enough to contain the worm area size!
    DISPLAY_MODE = (800, 600),
    WORM_AREA_POS = (1, 1),
    WORM_AREA_SIZE = (600, 563),

    WORM_EYE_DIAMETER = 2,

    MENU_FONT_SIZES = (28, 18),
    MENU_NETCONFIG_FONT_SIZES = (20, 18),

    MENU_KEYS_WIDTH = 100,
    MENU_AREA_POS = (75, 100),
    MENU_AREA_SIZE = (450, 420),
    MENU_AREA_COLOR = (10, 10, 10),
    MENU_ALPHA = 0.85,
    MENU_KEY_COLOR = (255, 255, 255),
    MENU_ENABLED_TEXT_COLOR = (80,80,200),
    MENU_DISABLED_TEXT_COLOR = (70,70,80),
    MENU_TEXT_CIRCLE_DIAMETERX = 1.,
    MENU_TEXT_CIRCLE_DIAMETERY = 1./3,
    MENU_TEXT_CIRCLE_PER_ITERATION_UNSELECTED = 1/100.,
    MENU_TEXT_CIRCLE_PER_ITERATION_SELECTED = 1/20.,
    MENU_BOUNDS_RECT_WIDTH = 3,
    MENU_BOUNDS_RECT_COLOR = (255, 255, 255),

    CREDITS_ALPHA = 0.8,
    CREDITS_WORM_TEXT_COLOR = (255, 30, 10),
    CREDITS_WORM_DIAMETER = 10.0,
    CREDITS_TEXT_FONT_SIZE = 45,
    CREDITS_TEXT_COLOR = (200, 40, 40),
    CREDITS_WAIT_BETWEEN_TEXTS = 120,
    CREDITS_GRAVITY = 1,

    BOUNDS_RECT_WIDTH = 1,
    BOUNDS_RECT_COLOR = (255, 255, 255),

    HUD_AREA_POS = (600, 0),
    HUD_AREA_SIZE = (200, 600),
    HUD_FONT_SIZE = 30,
    HUD_AREA_COLOR = (0,0,0),
    HUD_HOST_BASE_COLOR = (15,15,15),

    # Relative to the worm area
    TEXTS_LEFT_BOTTOM = (5, 560),
    TEXTS_MAX_COUNT = 8,
    TEXTS_COLOR = (50, 200, 30),
    TEXTS_ALPHA = 0.9,
    TEXTS_EXPIRATION_TIME = 5,
    TEXTS_FONT_SIZE = 26,

    TEXT_AREA_POS = (0, 565),
    TEXT_AREA_SIZE = (600, 35),
    TEXT_FONT_SIZE = 30,
    TEXT_COLOR = (200, 200, 200),
    KEYS_FONT_SIZE = 22,

    FPS_COLOR = (200, 150, 100),
    FPS_POS = (740, 570),
    FPS_SIZE = (60, 30),

    CREATE_PLAYER_KEY = (0, pygame.K_F1),
    REMOVE_PLAYER_KEY = (0, pygame.K_F2),
    SEND_TEXT_KEY = (0, pygame.K_RETURN),
    SEND_TO_ALL_KEY = (0, pygame.K_RETURN),
    SEND_TO_HOST_KEY = (pygame.KMOD_CTRL, pygame.K_RETURN),

    PREV_KEY = (0, pygame.K_UP),
    NEXT_KEY = (0, pygame.K_DOWN),

    EXIT_KEY = (pygame.KMOD_CTRL, pygame.K_q),
    MENU_KEY = (0, pygame.K_F10),
    OPTIONS_KEY = (pygame.KMOD_CTRL, pygame.K_o),
    MENU_SELECT_KEY = (0, pygame.K_RETURN),
    CANCEL_KEY = (0, pygame.K_ESCAPE),
    PAUSE_KEY = (0, pygame.K_PAUSE),

    MENU_INCREASE_VALUE_KEY = (0, pygame.K_KP_PLUS),
    MENU_DECREASE_VALUE_KEY = (0, pygame.K_KP_MINUS),

    TOGGLE_FULLSCREEN_KEY = (pygame.KMOD_ALT, pygame.K_RETURN),

    START_GAME_KEY = (0, pygame.K_F5),

    INSTRUCTIONS_FONT_SIZE = 30,
    INSTRUCTIONS_ALPHA = 0.8,
    ENABLED_INSTRUCTIONS_COLOR = (120,255,120),
    DISABLED_INSTRUCTIONS_COLOR = (60,90,60),

    WORM_EXAMPLE_WIDTH = 60,

    # How much of the screen's outline is not considered for randomization
    # of the created worm positions.
    POS_RANDOM_OUTLINE_WIDTH = 80,
)

