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

from utils import Colors

MODKEY = 'Mod4'

# theme
FONT = '-artwiz-snap-*-*-*-*-*-100-*-*-*-*-*-*'

NORMAL_COLORS = Colors(0xb6b4b8, 0x1c2636, 0x0f1729)
FOCUS_COLORS = Colors(0xffffff, 0x1c2636, 0x0f1729)

BAR_NORMAL_COLORS = Colors(0xa0a0a0, 0x505050, 0x404040)
BAR_FOCUS_COLORS = Colors(0xffffff, 0x1c2636, 0x0f1729)

BORDER = 0

# status bar
STATUS_BAR_SEPARATOR = None
STATUS_BAR_START = None
STATUS_BAR_END = None

# dmenu
DMENU_FONT = FONT
DMENU_NORMAL_COLORS = Colors(0xb6b4b8, 0x1c2636)
DMENU_SELECTION_COLORS = Colors(0xffffff, 0x1c2636)

# scratch pad tag name
SCRATCHPAD = '_sp'

# tag mappings: (display tag name, real tag name), ...
TAG_MAPPING = (
    ('mail', '01_mail'),
    ('browser', '02_browser'),
    ('irssi_downgra_de', '03_irssi_downgra_de'),
    ('irssi_logix_tt', '04_irssi_logix_tt'),
    ('logs', '05_logs'),
    ('sp', '_sp'),
)

# tag rules
TAG_RULES = (
    '/XMMS.*/ -> ~',
    '/MPlayer.*/ -> ~',
    '/Opera.*/ -> 02_browser',
    '/Firefox.*/ -> 02_browser',
    '/Gimp.*/ -> gimp',
    '/mail_downgrade.*/ -> 01_mail',
    '/mail_logixtt.*/ -> 01_mail',
    '/irssi_downgra_de.*/ -> 03_irssi_downgra_de',
    '/irssi_logix_tt.*/ -> 04_irssi_logix_tt',
    '/logger_.*/ -> 05_logs',
    '/.*/ -> !',
    '/.*/ -> 1',
)

# colrules
COL_RULES = (
    '/05_logs/ -> 100',
    '/.*/ -> 50+50',
)

# import logging
# LOG_LEVEL = logging.DEBUG
