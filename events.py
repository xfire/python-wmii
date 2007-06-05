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
    (r'^CreateTag', tag_create()),
    (r'^DestroyTag', tag_destroy()),
    (r'^FocusTag', tag_focus()),
    (r'^FocusTag', tag_history(15)),
    (r'^UnfocusTag', tag_unfocus()),
    (r'^CreateClient', second_column_hack()),
    (r'^LeftBarClick', view()),
    (r'^LeftBarClick', wheel_view()),
    (r'^ClientMouseDown', call(wmii9menu(['nop', 'close']), dict(close = kill()))),
    (r'^UrgentTag', tag_urgent()),
    (r'^NotUrgentTag', tag_not_urgent()),
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
    # focus up/down/left/right/h/j/k/l client
    SelectSet(MKey('Shift-'), SelectSet.VIM),
    SelectSet(MKey('Shift-'), SelectSet.CURSOR),

    # move selected client up/down/left/right/h/j/k/l
    SendSet(MKey('Control-'), SendSet.VIM),
    SendSet(MKey('Control-'), SendSet.CURSOR),

    # switch to next or previous view
    (MKey('Right'), next_view()),
    (MKey('l'), next_view()),
    (MKey('Left'), prev_view()),
    (MKey('h'), prev_view()),

    # scratch pad
    (MKey('space'), toggle_scratchpad()),
    (MKey('Shift-Space'), add_tag(d2t(SCRATCHPAD))),
    (MKey('Ctrl-Space'), set_tag(d2t(SCRATCHPAD))),

    # history
    (MKey('plus'), history_next()),
    (MKey('minus'), history_prev()),

    # toggle between managed and floating layer
    (MKey('f'), toggle()),
    (MKey('Shift-f'), send_toggle()),

    # add/set tag for current client selected using dmenu
    (MKey('Shift-t'), add_tag(d2t(dmenu(tag_generator())))),
    (MKey('Control-t'), set_tag(d2t(dmenu(tag_generator())))),

    # remove current client from view
    (MKey('Shift-u'), remove_tag(active_view)),
    (MKey('Control-u'), set_tag(active_view)),

    # switch column modes
    (MKey('s'), colmode('stack')),
    (MKey('d'), colmode()),
    (MKey('m'), colmode('max')),
    # kill client
    (MKey('Control-c'), kill()),

    # run applications
    (MKey('Return'), execute('x-terminal-emulator')),
    (MKey('Shift-Return'), execute('x-terminal-emulator -fg red -e sudo su -')),
    (MKey('Shift-b'), execute('set_random_wallpaper.zsh')),
    (MKey('F12'), execute('slock')),

    # run application selected using dmenu
    (MKey('p'), execute(dmenu(application_generator()))),
)

APPLICATIONS = dict(quit = quit(),
                    lock = execute('slock'),
                    mail = execute('start.mail'),
                    firefox = execute('firefox'),
                    opera = execute('opera'),
                    wallpaper = execute('set_random_wallpaper.zsh'))
EVENTS += patterns(
    (MKey('a'), call_dmenu(APPLICATIONS)),
)
