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

import re, logging, math

from utils import Colors
from utils.statusbar import parse_file
from config import BAR_NORMAL_COLORS, BAR_FOCUS_COLORS

logger = logging.getLogger('statusbar.battery')

FILE_BAT_INFO = '/proc/acpi/battery/C1BE/info'
FILE_BAT_STATE = '/proc/acpi/battery/C1BE/state'
FILE_AC = '/proc/acpi/ac_adapter/C1BC/state'

RE_FULL_CAPACITY = re.compile(r'^last full capacity:\s+(?P<lastfull>\d+).*$')
RE_REMAINING_CAPACITY = re.compile(r'^remaining capacity:\s+(?P<remain>\d+).*$')
RE_PRESENT_RATE = re.compile(r'^present rate:\s+(?P<rate>\d+).*$')
RE_AC_ONLINE = re.compile(r'^state:\s*(?P<state>on.line).*$')

LAST_CALL_TIME = 0
def update(call_time):
    global LAST_CALL_TIME

    if call_time - LAST_CALL_TIME > 2:
        ac_vals = parse_file(FILE_AC, RE_AC_ONLINE)
        bat_vals = parse_file([FILE_BAT_INFO, FILE_BAT_STATE], [RE_FULL_CAPACITY, RE_REMAINING_CAPACITY, RE_PRESENT_RATE])

        bat = '--'
        ac = '--'
        color = BAR_NORMAL_COLORS
        try:
            lastfull = float(bat_vals['lastfull'][0])
            remain = float(bat_vals['remain'][0])
            rate = float(bat_vals['rate'][0])

            percent = math.floor(remain / lastfull * 100.0 + 0.5)
            bat = '%d%%' % percent
            if percent < 50:
                color = Colors(0xFFFF00, BAR_NORMAL_COLORS.background, BAR_NORMAL_COLORS.border)
            elif percent < 25:
                color = Colors(0xFF0000, BAR_NORMAL_COLORS.background, BAR_NORMAL_COLORS.border)

            if ac_vals:
                ac = '*AC*'
            elif rate > 0:
                mins = (3600.0 * (remain / rate)) / 60.0
                hours = math.floor(mins / 60.0)
                mins = math.floor(mins - (hours * 60.0))
                ac = '%02d:%02d' % (hours, mins)
        except Exception, e:
            logger.exception(e)

        LAST_CALL_TIME = call_time
        return (color, 'BAT: %s' % (' '.join((bat, ac))))
    return None
