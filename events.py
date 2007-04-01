#
# Copyright (C) 2007 Rico Schiekel (fire at downgra dot de)
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# vim:syntax=python:sw=4:ts=4:expandtab

import sys
from utils import patterns, t2d
from utils.event_handler import *

EVENTS = patterns(
    (r'^Start wmiirc$', fwrap(sys.exit, 0)),
    (r'^CreateTag', tag_create),
    (r'^DestroyTag', tag_destroy),
    (r'^FocusTag', tag_focus),
    (r'^UnfocusTag', tag_unfocus),
    (r'^LeftBarClick', view()),
)

# work views (view, add tag, set tag)
for i in range(1, 10):
    EVENTS += patterns(
        (MKey('%d' % i), view(str(i))),
        (MKey('Shift-%d' % i), add_tag(str(i))),
        (MKey('Control-%d' % i), set_tag(str(i))),
    )

# named views (view, add tag, set tag)
NAMED_VIEWS = ['mail', 'browser', 'irssi_downgra_de', 'irssi_logix_tt', 'logs']
for i in range(0, len(NAMED_VIEWS)):
    EVENTS += patterns(
        (MKey('F%d' % (i+1)), view(d2t(NAMED_VIEWS[i]))),
        (MKey('Shift-F%d' % (i+1)), add_tag(d2t(NAMED_VIEWS[i]))),
        (MKey('Control-F%d' % (i+1)), set_tag(d2t(NAMED_VIEWS[i]))),
    )

EVENTS += patterns(
    # focus up/down/left/right client
    (MKey('Shift-Up'), select),
    (MKey('Shift-Down'), select),
    (MKey('Shift-Left'), select),
    (MKey('Shift-Right'), select),

    # move selected client up/down/left/right
    (MKey('Control-Up'), send),
    (MKey('Control-Down'), send),
    (MKey('Control-Left'), send),
    (MKey('Control-Right'), send),

    # switch to next or previous view
    (MKey('Right'), view_next),
    (MKey('Left'), view_prev),

    # scratch pad
    (MKey('space'), toggle_scratchpad),
    (MKey('Shift-Space'), add_tag(d2t(SCRATCHPAD))),
    (MKey('Ctrl-Space'), set_tag(d2t(SCRATCHPAD))),

    # toggle between managed and floating layer
    (MKey('l'), toggle),
    (MKey('Shift-l'), send_toggle),

    # add/set tag for current client selected using dmenu
    (MKey('Shift-t'), add_tag(d2t(dmenu(tag_generator)))),
    (MKey('Control-t'), set_tag(d2t(dmenu(tag_generator)))),

    # remove current client from view
    (MKey('Shift-u'), remove_tag(active_view)),
    (MKey('Control-u'), set_tag(active_view)),

    # switch column modes
    (MKey('s'), colmode('stack')),
    (MKey('d'), colmode()),
    (MKey('m'), colmode('max')),
    # kill client
    (MKey('Control-c'), kill),

    # run applications
    (MKey('Return'), execute('x-terminal-emulator')),
    (MKey('Shift-Return'), execute('x-terminal-emulator -fg red -e sudo su -')),
    (MKey('Shift-f'), execute('x-www-browser')),
    (MKey('Shift-b'), execute('set_random_wallpaper.zsh')),
    (MKey('F12'), execute('slock')),

    # run application selected using dmenu
    (MKey('p'), execute(dmenu(application_generator))),
)

APPLICATIONS = dict(quit = quit, 
                    lock = execute('slock'),
                    mail = execute('start.mail'),
                    firefox = execute('firefox'),
                    opera = execute('x-www�browser'),
                    wallpaper = execute('set_random_wallpaper.zsh'))
EVENTS += patterns(
    (MKey('a'), call_dmenu(APPLICATIONS)),
)
