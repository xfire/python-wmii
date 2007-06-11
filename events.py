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
        (MKey('%d' % i), View(str(i))),
        (MKey('Shift-%d' % i), AddTag(str(i))),
        (MKey('Control-%d' % i), SetTag(str(i))),
    )

# named views (view, add tag, set tag)
NAMED_VIEWS = ['mail', 'browser', 'irssi_downgra_de', 'irssi_logix_tt', 'logs']
for i in range(0, len(NAMED_VIEWS)):
    EVENTS += patterns(
        (MKey('F%d' % (i+1)), View(d2t(NAMED_VIEWS[i]))),
        (MKey('Shift-F%d' % (i+1)), AddTag(d2t(NAMED_VIEWS[i]))),
        (MKey('Control-F%d' % (i+1)), SetTag(d2t(NAMED_VIEWS[i]))),
    )

EVENTS += patterns(
    # focus up/down/left/right/h/j/k/l client
    SelectSet(MKey('Shift-'), SelectSet.VIM),
    SelectSet(MKey('Shift-'), SelectSet.CURSOR),
    (MKey('Tab'), Select('down')),

    # move selected client up/down/left/right/h/j/k/l
    SendSet(MKey('Control-'), SendSet.VIM),
    SendSet(MKey('Control-'), SendSet.CURSOR),

    # switch to next or previous view
    (MKey('Right'), NextView()),
    (MKey('l'), NextView()),
    (MKey('Left'), PrevView()),
    (MKey('h'), PrevView()),

    # scratch pad
    (MKey('space'), ToggleScratchPad()),
    (MKey('Shift-Space'), AddTag(d2t(SCRATCHPAD))),
    (MKey('Ctrl-Space'), SetTag(d2t(SCRATCHPAD))),

    # history
    (MKey('plus'), HistoryNext()),
    (MKey('minus'), HistoryPrev()),

    # toggle between managed and floating layer
    (MKey('f'), Toggle()),
    (MKey('Shift-f'), SendToggle()),

    # add/set tag for current client selected using dmenu
    (MKey('Shift-t'), AddTag(d2t(DMenu(TagGenerator())))),
    (MKey('Control-t'), SetTag(d2t(DMenu(TagGenerator())))),

    # remove current client from view
    (MKey('Shift-u'), RemoveTag(active_view)),
    (MKey('Control-u'), SetTag(active_view)),

    # switch column modes
    (MKey('s'), ColMode('stack')),
    (MKey('d'), ColMode()),
    (MKey('m'), ColMode('max')),
    # kill client
    (MKey('Control-c'), Kill()),

    # run applications
    (MKey('Return'), Execute('x-terminal-emulator')),
    (MKey('Shift-Return'), Execute('x-terminal-emulator -fg red -e sudo su -')),
    (MKey('Shift-b'), Execute('set_random_wallpaper.zsh')),
    (MKey('F12'), Execute('slock')),

    # run application selected using dmenu
    (MKey('p'), Execute(DMenu(ApplicationGenerator()))),
)

APPLICATIONS = dict(quit = Quit(),
                    lock = Execute('slock'),
                    mail = Execute('start.mail'),
                    firefox = Execute('firefox'),
                    opera = Execute('opera'),
                    wallpaper = Execute('set_random_wallpaper.zsh'))
EVENTS += patterns(
    (MKey('a'), CallDMenu(APPLICATIONS)),
)
