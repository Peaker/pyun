#! /usr/bin/env python

import sys
import pygame
from pyunsrc.Game import Game

DEFAULT_PORT = 10002

def usage():
    print "Usage: pyun.py myname -c hostname[:port]  Network mode, connect to"
    print "                                          game hosted by hostname"
    print
    print "   or: pyun.py myname -l [port]           Network mode, become host of game"
    print
    print "   or: pyun.py                            Local play"
    sys.exit()

def cmd_int(x):
    try:
        return int(x)
    except ValueError:
        usage()

def get_cmdline(args):
    if len(args) == 0:
        return 'local', 'local', ()
    if not 2 <= len(args) <= 3:
        usage()
    if args[1] not in ['-c', '-l']:
        usage()
    if args[1] == '-c':
        if len(args) != 3:
            usage()
        hoststr = args[2]
        if ':' in hoststr:
            hostname, port = hoststr.split(':', 1)
        else:
            hostname, port = hoststr, DEFAULT_PORT
        return 'connect', args[0], (hostname, cmd_int(port))
    else:
        if len(args) < 3:
            port = DEFAULT_PORT
        else:
            port = cmd_int(args[2])
        return 'listen', args[0], port

def main(args):
    cmdline = get_cmdline(args)
    pygame.init()
    game = Game(cmdline)
    game.run()
    # pygame.quit()
    # sys.exit()
    import os
    os._exit(0)

if __name__ == '__main__':
    if sys.argv[1:2] == ['-profile']:
        del sys.argv[1]
        import profile
        profile.run('main(sys.argv[1:])')
    else:
        main(sys.argv[1:])
