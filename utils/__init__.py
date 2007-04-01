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

import re, types
import subprocess
import logging

logger = logging.getLogger('utils')

p9_impls = ['p9_sock', 'wmiir']
try:
    for impl in p9_impls:
        logger.debug('try to load p9 client: %s' % impl)
        mod = __import__(impl, globals(), locals(), [])
        if mod.p9_available():
            logger.debug('p9 client [%s] available' % impl)
            globals().update(dict([(k,v) for k,v in mod.__dict__.iteritems() if k in mod.__all__]))
            break
except Exception, e:
    logger.exception(e)

if not globals().has_key('p9_available') or not p9_available():
    raise StandardError('no suitable p9 client found!')

# ---------------------------------------------------------------------------

class EventResolver(object):
    def __init__(self, regex, handler, default_kwargs = None):
        if type(regex) in types.StringTypes:
            regex = re.compile(regex)
        self.__regex = regex
        self.__handler = handler
        self.__default_kwargs = default_kwargs or {}

    def match(self, event):
        return self.__regex.match(event)

    def __call__(self, event):
        self.__handler(event, **self.__default_kwargs)

def event_handler(event_str, event_list):
    """for an event iterate over event list an call all matching events."""
    logger.debug('event: %s' % event_str)
    [event(event_str) for event in event_list if event.match(event_str)]
    return True

class Key(object):
    """defines an key. must be used in patterns to define key assignments."""
    __used_keys = set()

    def __init__(self, key_desc):
        self.__key_desc = key_desc
        self.__used_keys.add(key_desc)

    def __call__(self):
        return r'^Key %s$' % self.__key_desc

    @classmethod
    def used_keys(cls):
        return cls.__used_keys

class MKey(Key):
    """defines an meta key. must be used in patterns to define meta key assignments."""
    def __init__(self, key_desc):
        from config import MODKEY
        Key.__init__(self, '%s-%s' % (MODKEY, key_desc))

def patterns(*tuples):
    """
    used to create the EVENT list. 
    
    take tuples as parameters. 
    
    each tuple must have first the regex to match or a callable object which returns 
    the regex. (see Key, MKey)
    the second object in the tuple must be the event handler.
    at least there can be one dictionary, with parameters for the event handler.

    eg.
        EVENTS += patterns(
            (r'REGEX', my_handler, dict(param_1 = 1000, param_2 = 'foo')),
        )
    """
    resolver_list = []
    for t in tuples:
        regex, handler = t[:2]
        default_kwargs = t[2:]
        if callable(regex): # regex is a callable object, which must return a string or a compiled regex
            regex = regex()
        logger.debug('add event handler: "%s", %s' % (regex, handler))
        resolver_list.append(EventResolver(regex, handler, *default_kwargs))
    return resolver_list

# ---------------------------------------------------------------------------

TAG_MAPPING_T2D = {}
TAG_MAPPING_D2T = {}

def init_tag_mappings(tmap):
    for dname, tag in tmap:
        TAG_MAPPING_T2D[tag] = dname
        TAG_MAPPING_D2T[dname] = tag

class tag_mapping_wrapper(object):
    """lazy tag mapping for callable objects like dmenu"""
    def __init__(self, map_func, call_func):
        self.__map_func = map_func
        self.__call_func = call_func

    def __call__(self):
        return self.__map_func(self.__call_func())

def t2d(tag):
    """map real tag name to the display name. (tag can be callable for lazy mapping)"""
    if callable(tag):
        return tag_mapping_wrapper(t2d, tag)
    logger.debug('tag2display: %s', tag)
    return TAG_MAPPING_T2D.get(tag, tag)

def d2t(dname):
    """map display name to the real tag name. (dname can be callable for lazy mapping)"""
    if callable(dname):
        return tag_mapping_wrapper(d2t, dname)
    logger.debug('display2tag: %s', dname)
    return TAG_MAPPING_D2T.get(dname, dname)

# ---------------------------------------------------------------------------

def active_view():
    """return the active view."""
    act_v = [l for l in p9_read('/ctl') if l.startswith('view ')]
    if act_v:
        act_v = act_v[0].split(' ')[1]
    return act_v

# ---------------------------------------------------------------------------

class Colors(object):
    def __init__(self, foreground, background, border = 0):
        self.__foreground, self.__background, self.__border = foreground, background, border

    def __str__(self):
        return '#%.6X #%.6X #%.6X' % (self.__foreground, self.__background, self.__border)

    @property
    def foreground(self): return self.__foreground

    @property
    def background(self): return self.__background

    @property
    def border(self): return self.__background

