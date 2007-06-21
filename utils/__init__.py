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
import warnings

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
                if isinstance(event, types.StringTypes):
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
    __used_keys = set()

    re_type = type(re.compile('foobar'))
    def __init__(self, regex, handler, default_args = None):
        if callable(regex):
            regex = regex()
        if isinstance(regex, types.StringTypes):
            try:
                self.__regex = re.compile(regex)
            except Exception, e:
                raise TypeError('Invalid event expression "%s": %s' % (regex, str(e)))
        elif isinstance(regex, EventResolver.re_type):
            self.__regex = regex
        else:
            raise TypeError('Invalid event expression: %s' % regex)

        if not handler:
            raise TypeError('no handler defined: "%s"' % regex)
        if not callable(handler):
            raise TypeError('Handler not callable: %s' % str(handler))
        self.__handler = handler

        self.__default_args = default_args or ()

        # register key if any
        key = self.__get_key(self.__regex.pattern)
        if key:
            self.__used_keys.add(key)

    def match(self, event):
        return self.__regex.match(event)

    def __call__(self, event):
        self.__handler(event, *self.__default_args)

    RE_KEY_REGEX = re.compile(r'^\^?Key (?P<key>.*?)\$?$')
    def __get_key(self, regex_pattern):
        """return the key, if it matches RE_KEY_REGEX, else None"""
        if isinstance(regex_pattern, types.StringTypes):
            match = EventResolver.RE_KEY_REGEX.search(regex_pattern)
            if match:
                return match.groupdict().get('key')
        return None

    @classmethod
    def used_keys(cls):
        """return list of all defined keys"""
        return list(cls.__used_keys)

class Key(str):
    """*DEPRECATED* defines an key."""
    def __init__(self, value):
        warnings.warn('classes Key and MKey are deprecated. please use simple regular expressions.', DeprecationWarning)

    def __call__(self):
        return r'^Key %s$' % self


class MKey(Key):
    """*DEPRECATED* defines an meta key."""
    def __new__(cls, value):
        mk = ''
        try:
            import config
            mk = '%s-' % config.MODKEY
        except:
            logger.warn('MKey() used, but config.MODKEY not defined!')
        return Key.__new__(cls, ''.join((mk, value)))


def patterns(*tuples):
    """
    used to create the EVENT list.

    take callable objects or tuples as parameters.
    the return value of those callable objects or those tuples must have first the regex 
    to match or a callable object which returns the regex.

    the second object in the tuple must be the event handler, which must be a callable
    object. this can be a function or a class instance which implements __call__. the 
    second is the preferred way, especially if default parameters must be specified.

    the third and all following elements in the tuple are taken as default parameters
    for the handler. use this, if your handler is not a callable class instance.

    eg.
        def my_handler(event):
            # normal event handler
            ...
        def my_meta4_shift_r_handler(event, second_parameter):
            # event handler which takes additional parameters
            ...
        EVENTS += patterns(
            (r'REGEX', my_handler),
            ((r'REGEX_1', r'REGEX_2'), my_second_handler),
            (r'^Key Meta4-Shift-r'), my_meta4_shift_r_handler, 42),
            SendSet('Shift-', style='vim'),
            ...
        )
    """
    resolver_list = []
    for t in tuples:
        if callable(t):
            t = t()
        if not isinstance(t, (types.ListType, types.TupleType)):
            t = [t]

        if not t:
            logger.warn('Empty event tuple')
            continue

        regex = t[0]

        try:
            handler = t[1]
        except IndexError:
            handler = None

        default_args = t[2:]

        if callable(regex) and not isinstance(regex, EventResolver):
            regex = regex()
        if not isinstance(regex, (types.ListType, types.TupleType)):
            regex = [regex]

        for r in regex:
            if isinstance(r, EventResolver):
                logger.debug('add event resolver: %s' % r)
                resolver_list.append(r)
            else:
                logger.debug('add event handler: "%s", %s' % (r, handler))
                try:
                    resolver_list.append(EventResolver(r, handler, default_args))
                except TypeError, e:
                    logger.exception(e)
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

TAF_MAPPING_KEY_DISPLAY = {}
TAG_MAPPING_KEY_REAL = {}


def init_tag_mappings(tmap):
    global TAF_MAPPING_KEY_DISPLAY, TAG_MAPPING_KEY_REAL
    clean_tmap = []
    for d, r in tmap:
        if d not in [td for td, tr in clean_tmap] and \
           r not in [tr for td, tr in clean_tmap]:
            clean_tmap.append((d, r))
        else:
            logger.warn('invalid mapping: %s (display) -> %s (real)' % (d, r))

    TAF_MAPPING_KEY_DISPLAY = dict(clean_tmap)
    TAG_MAPPING_KEY_REAL = dict([(r, d) for d, r in clean_tmap])


def display_tag_name(name):
    """map tag name to the display name. ('name' can be callable for lazy mapping)"""
    logger.debug('tag2display: %s', name)
    return TAG_MAPPING_KEY_REAL.get(name, name)


def real_tag_name(name):
    """map tag name to the real tag name. ('name' can be callable for lazy mapping)"""
    logger.debug('display2tag: %s', name)
    return TAF_MAPPING_KEY_DISPLAY.get(name, name)

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

