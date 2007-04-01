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

import time
from config import BAR_NORMAL_COLORS, BAR_FOCUS_COLORS

LAST_CALL_TIME = 0
def update(call_time):
    global LAST_CALL_TIME

    if call_time - LAST_CALL_TIME > 60:
        LAST_CALL_TIME = call_time
        return (BAR_NORMAL_COLORS, time.strftime('%Y-%m-%d - %H:%M'))
    else:
        return None
