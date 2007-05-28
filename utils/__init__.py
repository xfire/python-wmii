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

import os
import re
import types
import subprocess
import logging
import threading
import bdeque

logger = logging.getLogger('utils')

p9_impls = ['p9_sock', 'wmiir']
try:
    for impl in p9_impls:
        logger.debug('try to load p9 client: %s' % impl)
        mod = __import__(impl, globals(), locals(), [])
        if mod.p9_available():
            logger.debug('p9 client [%s] available' % impl)
            globals().update(dict([(k, v) for k, v in mod.__dict__.iteritems() if k in mod.__all__]))
            break
except Exception, e:
    logger.exception(e)

if not 'p9_available' in globals() or not p9_available():
    raise StandardError('no suitable p9 client found!')

# ---------------------------------------------------------------------------
# global event queue (thread safe)
EVENT_QUEUE = bdeque.bdeque()
EVENT_LOOP = True
EVENT_HANDLER = None


class EventHandler(threading.Thread):
    """event handler thread"""

    def __init__(self, handler_list):
        self.__handler_list = handler_list
        threading.Thread.__init__(self)

    def run(self):
        global EVENT_LOOP, EVENT_QUEUE
        while EVENT_LOOP:
            event = EVENT_QUEUE.popleft()
            try:
                logger.debug('dispatch event: [%s]' % event)
                if type(event) in types.StringTypes:
                    # call every matching event handler
                    [handler(event) for handler in self.__handler_list if handler.match(event)]
                elif callable(event):
                    # simple call
                    event()
            except Exception, e:
                logger.exception(e)


def stop_event_handler():
    global EVENT_LOOP
    EVENT_LOOP = False


def add_event(event):
    global EVENT_QUEUE, EVENT_HANDLER

    logger.debug('add event: [%s]' % event)
    EVENT_QUEUE.append(event)
    if not EVENT_HANDLER or not EVENT_HANDLER.isAlive():
        from events import EVENTS
        logger.debug('(re)start event handler')
        EVENT_HANDLER = EventHandler(EVENTS)
        EVENT_HANDLER.start()
    return True


class EventResolver(object):
    """encapsulate an event handler"""

    def __init__(self, regex, handler, default_kwargs = None):
        if callable(regex):
            regex = regex()
        if type(regex) in types.StringTypes:
            regex = re.compile(regex)
        self.__regex = regex
        self.__handler = handler
        self.__default_kwargs = default_kwargs or {}

    def match(self, event):
        return self.__regex.match(event)

    def __call__(self, event):
        self.__handler(event, **self.__default_kwargs)


class Key(object):
    """defines an key. must be used in patterns to define key assignments."""
    __used_keys = set()

    def __init__(self, key_desc):
        self.__key_desc = key_desc

    def __str__(self):
        return self.__key_desc

    def __call__(self):
        self.__used_keys.add(self.__key_desc)
        return r'^Key %s$' % self

    def set(self, key_desc):
        """set new key definition"""
        self.__key_desc = key_desc

    def add(self, key_desc):
        """add key_desc to key defintion"""
        self.__key_desc += key_desc

    def replace(self, old, new, count = -1):
        """replace old to new in key defintion"""
        self.__key_desc = self.__key_desc.replace(old, new, count)

    @classmethod
    def used_keys(cls):
        """return list of all defined keys"""
        return cls.__used_keys


class MKey(Key):
    """defines an meta key. must be used in patterns to define meta key assignments."""

    def __init__(self, key_desc):
        from config import MODKEY
        Key.__init__(self, '%s-%s' % (MODKEY, key_desc))


def patterns(*tuples):
    """
    used to create the EVENT list.

    take callable objects or tuples as parameters.

    callable objects should return:
        - one or more regular expressions as string or precompiled 're' objects
        - one or more EventResolver objects (SendSet)

    tuples must have have first the regex to match or a callable object which returns
    the regex. (see Key, MKey)
    the second object in the tuple must be the event handler, which must be a callable
    object.

    eg.
        EVENTS += patterns(
            (r'REGEX', my_handler),
            ((r'REGEX_1', r'REGEX_2'), my_second_handler),
            (MKey('Shift-r'), my_third_handler),
            SendSet('Shift-', style='vim'),
            ...
        )
    """
    resolver_list = []
    for t in tuples:
        if type(t) not in (types.ListType, types.TupleType):
            t = [t]
        regex = t[0]

        try:
            handler = t[1]
        except IndexError:
            handler = None

        default_kwargs = t[2:]

        if callable(regex):
            regex = regex()
        if type(regex) not in (types.ListType, types.TupleType):
            regex = [regex]

        for r in regex:
            if isinstance(r, EventResolver):
                logger.debug('add event resolver: %s' % r)
                resolver_list.append(r)
            else:
                if handler:
                    if callable(handler):
                        logger.debug('add event handler: "%s", %s' % (r, handler))
                        resolver_list.append(EventResolver(r, handler, *default_kwargs))
                    else:
                        logger.warn('invalid handler: "%s", %s' % (r, handler))
                else:
                    logger.warn('no handler defined: "%s"' % r)
    return resolver_list


def autostart():
    """
    run $WMII_CONFPATH/autostart.sh to autostart user defined applications at wmii
    start.
    """
    WMII_CONFPATH = os.environ.get('WMII_CONFPATH', [])
    for path in WMII_CONFPATH.split(':'):
        file = os.path.join(path, 'autostart.sh')
        if os.path.isfile(file):
            try:
                subprocess.Popen(file, shell = True).wait()
            except Exception, e:
                logger.exception(e)

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
    """represents a wmii color"""

    def __init__(self, foreground, background, border = 0):
        self.__foreground, self.__background, self.__border = foreground, background, border

    def __str__(self):
        return '#%.6X #%.6X #%.6X' % (self.__foreground, self.__background, self.__border)

    @property
    def foreground(self):
        return self.__foreground

    @property
    def background(self):
        return self.__background

    @property
    def border(self):
        return self.__background

