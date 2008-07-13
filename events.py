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
from utils import patterns
from utils.event_handler import *
from config import MODKEY

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
        (r'^Key %s-%d$' % (MODKEY, i), View(str(i))),
        (r'^Key %s-Shift-%d$' % (MODKEY, i), AddTag(str(i))),
        (r'^Key %s-Control-%d$' % (MODKEY, i), SetTag(str(i))),
    )

# named views (view, add tag, set tag)
NAMED_VIEWS = ['mail', 'browser', 'irssi_downgra_de', 'irssi_logix_tt', 'logs']
for i in range(0, len(NAMED_VIEWS)):
    EVENTS += patterns(
        (r'^Key %s-F%d$' % (MODKEY, (i+1)), View(NAMED_VIEWS[i])),
        (r'^Key %s-Shift-F%d$' % (MODKEY, (i+1)), AddTag(NAMED_VIEWS[i])),
        (r'^Key %s-Control-F%d$' % (MODKEY, (i+1)), SetTag(NAMED_VIEWS[i])),
    )

EVENTS += patterns(
    # focus up/down/left/right/h/j/k/l client
    SelectSet(r'^Key %s-Shift-' % MODKEY, '$', SelectSet.VIM),
    SelectSet(r'^Key %s-Shift-' % MODKEY, '$', SelectSet.CURSOR),
    (r'^Key %s-Tab$' % MODKEY, Select('down')),

    # move selected client up/down/left/right/h/j/k/l
    SendSet(r'^Key %s-Control-' % MODKEY, '$', SendSet.VIM),
    SendSet(r'^Key %s-Control-' % MODKEY, '$', SendSet.CURSOR),

    # switch to next or previous view
    (r'^Key %s-Right$' % MODKEY, NextView()),
    (r'^Key %s-l$' % MODKEY, NextView()),
    (r'^Key %s-Left$' % MODKEY, PrevView()),
    (r'^Key %s-h$'% MODKEY, PrevView()),

    # history
    (r'^Key %s-plus$' % MODKEY, HistoryNext()),
    (r'^Key %s-minus$' % MODKEY, HistoryPrev()),

    # toggle between managed and floating layer
    (r'^Key %s-f$' % MODKEY, Toggle()),
    (r'^Key %s-Control-f$' % MODKEY, SendToggle()),

    # add/set tag for current client selected using dmenu
    (r'^Key %s-Shift-t$' % MODKEY, AddTag(DMenu(TagGenerator()))),
    (r'^Key %s-Control-t$' % MODKEY, SetTag(DMenu(TagGenerator()))),

    # remove current client from view
    (r'^Key %s-Shift-u$' % MODKEY, RemoveTag(active_view)),
    (r'^Key %s-Control-u$' % MODKEY, SetTag(active_view)),

    # switch column modes
    (r'^Key %s-s$' % MODKEY, ColMode('stack')),
    (r'^Key %s-d$' % MODKEY, ColMode()),
    (r'^Key %s-m$' % MODKEY, ColMode('max')),
    # kill client
    (r'^Key %s-Control-c$' % MODKEY, Kill()),

    # run applications
    (r'^Key %s-Return$' % MODKEY, Execute('x-terminal-emulator')),
    (r'^Key %s-Shift-Return$' % MODKEY, Execute('x-terminal-emulator -fg red -e sudo su -')),
    (r'^Key %s-Shift-b$' % MODKEY, Execute('set_random_wallpaper.zsh')),
    (r'^Key %s-F12$' % MODKEY, Execute('slock')),

    # run application selected using dmenu
    (r'^Key %s-p$' % MODKEY, Execute(DMenu(ApplicationGenerator()))),
)

APPLICATIONS = dict(quit = Quit(),
                    lock = Execute('slock'),
                    mail = Execute('start.mail'),
                    ifirefox = Execute('firefox'),
                    iopera = Execute('opera'),
                    firefox = Execute('sudo -H -u surf /home/surf/bin/exec /usr/bin/firefox'),
                    opera = Execute('sudo -H -u surf /home/surf/bin/exec /usr/bin/opera'),
                    wallpaper = Execute('set_random_wallpaper.zsh'))
EVENTS += patterns(
    (r'^Key %s-a$' % MODKEY, CallDMenu(APPLICATIONS)),
)
