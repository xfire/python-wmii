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

"""
this module loads statusbar plugins from a given path.
these plugins are seen as python modules and must define the method 
'update()' and 'interval()'.

the interval function must return the time between two update calls.

the update method is called all interval() seconds and must return a 
tuple in the form (color, text). it can also return None, which 
results in no update.
"""

import os, re
import logging
import types
from threading import Timer, Lock
from utils import *

__all__ = ['start_statusbar', 'stop_statusbar']

logger = logging.getLogger('utils.statusbar')

POS_RE = re.compile('^(?P<pos>\d{2})_.*$')

RUNNING = True
PLUGIN_LOCK = Lock()
PLUGIN_TIMERS = {}

def _update_plugin(name, mod):
    global RUNNING, PLUGIN_LOCK, PLUGIN_TIMERS

    PLUGIN_LOCK.acquire()
    try:
        uval = mod.update()
        if uval:
            logger.debug('update statusbar plugin: %s %s' % (name, uval))
            p9_write('/rbar/%s' % name, '%s %s' % uval)
    except Exception, e:
        logger.exception(e)
    if RUNNING:
        PLUGIN_TIMERS[name] = Timer(mod.interval(), _update_plugin, [name, mod])
        PLUGIN_TIMERS[name].start()
    PLUGIN_LOCK.release()

def start_statusbar(path, separator = None, start = None, end = None):
    """
    init the statusbar by first try to load all .py files in 'path'
    as modules, except __init__.py.
    while doing this, the ipx file system under /rbar is initialized.

    the name of the .py file is used as name under /rbar. so a sorting can
    be archived by using something like:
        01_load.py
        02_datetime.py
        ...
        99_foobar.py

    ! DEPRECATED !
    if 'separator' is not None, it automagically insert separators between
    the values, using the parameter 'separator' as text.
    for correct functioning the filename should match '^(\d{2})_.*$'.
    'start' and 'end' are special separators, which define an start and end text.
    eg.
        s = Statusbar('statusbar', (BC, '|'), (BC, '['), (BC, ']'))
        --> will produce
                [ foo | bar | blub ]
    'separator', 'start' and 'end' must be a tuple of (color, text).
    ! these three values are deprecated, since wmii supports (again) a border between
    ! the /rbar entries.
    """
    global PLUGIN_LOCK, PLUGIN_TIMERS

    # load and initialize plugins
    plugins = {}
    path = path.rstrip('/')
    flist = [d for d in os.listdir(os.path.expanduser(path)) if d.endswith('.py') and d != '__init__.py']
    flist.sort()
    for f in flist:
        try:
            name = f.replace('.py', '')
            mod = __import__('.'.join((os.path.split(path)[-1], name)), '', '', name)
            if hasattr(mod, 'update') and hasattr(mod, 'interval'):
                val = mod.update()
                if val:
                    p9_create('/rbar/%s' % name, '%s %s' % val)

                if separator and f != flist[-1]:
                    r = self.POS_RE.match(name)
                    if r:
                        pos = r.groupdict().get('pos', None)
                        if pos:
                            p9_create('/rbar/%sz_sep__' % pos, '%s %s' % separator)
                plugins[name] = mod
            else:
                logger.warn('invalid statusbar plugin: %s' % f)
        except Exception, e:
            logger.exception(e)

    if start:
        p9_create('/rbar/000_sep_start__', '%s %s' % start)
    if end:
        p9_create('/rbar/zzz_sep_end__', '%s %s' % end)

    # start plugins
    PLUGIN_LOCK.acquire()
    for name, mod in plugins.iteritems():
        logger.debug('start statusbar plugin: %s' % name)
        PLUGIN_TIMERS[name] = Timer(mod.interval(), _update_plugin, [name, mod])
        PLUGIN_TIMERS[name].start()
    PLUGIN_LOCK.release()

def stop_statusbar():
    global RUNNING, PLUGIN_LOCK, PLUGIN_TIMERS

    PLUGIN_LOCK.acquire()
    RUNNING = False
    for name, timer in PLUGIN_TIMERS.iteritems():
        logger.debug('stop statusbar plugin: %s' % name)
        timer.cancel()
    PLUGIN_LOCK.release()

# ---------------------------------------------------------------------------

def parse_file(path_list, regex_list):
    if type(path_list) not in (types.ListType, types.TupleType):
        path_list = [path_list]

    if type(regex_list) not in (types.ListType, types.TupleType):
        regex_list = [regex_list]

    lines = []
    for path in path_list:
        try:
            file = open(path, 'r')
            lines.extend(file.readlines())
            file.close()
        except IOError, e:
            logger.exception(e)

    ret = {}
    for line in lines:
        for regex in regex_list:
            match = regex.match(line)
            if match:
                for k,v in match.groupdict().iteritems():
                    ov = ret.get(k, v)
                    if ret.has_key(k):
                        ov.append(v)
                    else:
                        ov = [ov]
                    ret[k] = ov

    return ret
