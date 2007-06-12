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
    (r'^Start wmiirc$', FWrap(sys.exit, 0)),
    (r'^CreateTag', TagCreate()),
    (r'^DestroyTag', TagDestroy()),
    (r'^FocusTag', TagFocus()),
    (r'^FocusTag', TagHistory(15)),
    (r'^UnfocusTag', TagUnfocus()),
    (r'^CreateClient', SecondColumnHack()),
    (r'^LeftBarClick', View()),
    (r'^LeftBarClick', WheelView()),
    (r'^ClientMouseDown', Call(WMII9Menu(['nop', 'close']), dict(close = Kill()))),
    (r'^UrgentTag', TagUrgent()),
    (r'^NotUrgentTag', TagNotUrgent()),
)

# work views (view, add tag, set tag)
for i in range(1, 10):
    EVENTS += patterns(
        (r'^Key Mod4-%d' % i, View(str(i))),
        (r'^Key Mod4-Shift-%d' % i, AddTag(str(i))),
        (r'^Key Mod4-Control-%d' % i, SetTag(str(i))),
    )

# named views (view, add tag, set tag)
NAMED_VIEWS = ['mail', 'browser', 'irssi_downgra_de', 'irssi_logix_tt', 'logs']
for i in range(0, len(NAMED_VIEWS)):
    EVENTS += patterns(
        (r'^Key Mod4-F%d' % (i+1), View(d2t(NAMED_VIEWS[i]))),
        (r'^Key Mod4-Shift-F%d' % (i+1), AddTag(d2t(NAMED_VIEWS[i]))),
        (r'^Key Mod4-Control-F%d' % (i+1), SetTag(d2t(NAMED_VIEWS[i]))),
    )

EVENTS += patterns(
    # focus up/down/left/right/h/j/k/l client
    SelectSet(r'^Key Mod4-Shift-', SelectSet.VIM),
    SelectSet(r'^Key Mod4-Shift-', SelectSet.CURSOR),
    (r'^Key Mod4-Tab', Select('down')),

    # move selected client up/down/left/right/h/j/k/l
    SendSet(r'^Key Mod4-Control-', SendSet.VIM),
    SendSet(r'^Key Mod4-Control-', SendSet.CURSOR),

    # switch to next or previous view
    (r'^Key Mod4-Right', NextView()),
    (r'^Key Mod4-l', NextView()),
    (r'^Key Mod4-Left', PrevView()),
    (r'^Key Mod4-h', PrevView()),

    # scratch pad
    (r'^Key Mod4-Space', ToggleScratchPad()),
    (r'^Key Mod4-Shift-Space', AddTag(d2t(SCRATCHPAD))),
    (r'^Key Mod4-Ctrl-Space', SetTag(d2t(SCRATCHPAD))),

    # history
    (r'^Key Mod4-plus', HistoryNext()),
    (r'^Key Mod4-minus', HistoryPrev()),

    # toggle between managed and floating layer
    (r'^Key Mod4-f', Toggle()),
    (r'^Key Mod4-Shift-f', SendToggle()),

    # add/set tag for current client selected using dmenu
    (r'^Key Mod4-Shift-t', AddTag(d2t(DMenu(TagGenerator())))),
    (r'^Key Mod4-Control-t', SetTag(d2t(DMenu(TagGenerator())))),

    # remove current client from view
    (r'^Key Mod4-Shift-u', RemoveTag(active_view)),
    (r'^Key Mod4-Control-u', SetTag(active_view)),

    # switch column modes
    (r'^Key Mod4-s', ColMode('stack')),
    (r'^Key Mod4-d', ColMode()),
    (r'^Key Mod4-m', ColMode('max')),
    # kill client
    (r'^Key Mod4-Control-c', Kill()),

    # run applications
    (r'^Key Mod4-Return', Execute('x-terminal-emulator')),
    (r'^Key Mod4-Shift-Return', Execute('x-terminal-emulator -fg red -e sudo su -')),
    (r'^Key Mod4-Shift-b', Execute('set_random_wallpaper.zsh')),
    (r'^Key Mod4-F12', Execute('slock')),

    # run application selected using dmenu
    (r'^Key Mod4-p', Execute(DMenu(ApplicationGenerator()))),
)

APPLICATIONS = dict(quit = Quit(),
                    lock = Execute('slock'),
                    mail = Execute('start.mail'),
                    firefox = Execute('firefox'),
                    opera = Execute('opera'),
                    wallpaper = Execute('set_random_wallpaper.zsh'))
EVENTS += patterns(
    (r'^Key Mod4-a', CallDMenu(APPLICATIONS)),
)
