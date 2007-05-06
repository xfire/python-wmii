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

import os, re, subprocess, logging, copy
from utils import *
from utils.ringbuffer import RingBuffer
from config import BAR_NORMAL_COLORS, BAR_FOCUS_COLORS, SCRATCHPAD, \
                   DMENU_FONT, DMENU_NORMAL_COLORS, DMENU_SELECTION_COLORS

logger = logging.getLogger('utils.event_handler')

# ---------------------------------------------------------------------------

class fwrap(object):
    """
    warp calls to functions with arguments. both unnamed and named
    arguments are supported.
    """
    def __init__(self, func, *args, **kwargs):
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs

    def __call__(self, event):
        self.__func(*self.__args, **self.__kwargs)

# ---------------------------------------------------------------------------

class view(object):
    """
    switch to a view.

    tag can be set in constructor or is automagically get from the event.
    (last item from event line)
    """
    def __init__(self, tag = None):
        self.__tag = tag

    def __call__(self, event = ''):
        tag = self.__tag or event.strip().split()[-1]
        if callable(tag):
            tag = tag()
        logger.debug('%s: event[%s], tag[%s]' % (self.__class__.__name__, event, tag))
        p9_write('/ctl', 'view %s' % tag)

class set_tag(object):
    """set tag to current client. other tag settings are overwritten."""
    def __init__(self, tag = None):
        self.__tag = tag

    def __call__(self, event = ''):
        tag = self.__tag
        if callable(tag):
            tag = tag()
        logger.debug('%s: event[%s], tag[%s]' % (self.__class__.__name__, event, tag))
        p9_write('/client/sel/tags', tag)

class add_tag(object):
    """add tag to current client. other tag settings are preserved."""
    def __init__(self, tag = None):
        self.__tag = tag

    def __call__(self, event = ''):
        tag_list = set([tag.strip() for tag in p9_read('/client/sel/tags')[0].split('+')])
        tag = self.__tag
        if callable(tag):
            tag = tag()
        tag_list.add(tag)
        tag_list = '+'.join(tag_list)
        logger.debug('%s: event[%s], tag[%s], tag_list[%s]' % (self.__class__.__name__, event, tag, tag_list))
        p9_write('/client/sel/tags', tag_list)

class remove_tag(object):
    """remove tag from current client."""
    def __init__(self, tag = None):
        self.__tag = tag

    def __call__(self, event = ''):
        tag_list = set([tag.strip() for tag in p9_read('/client/sel/tags')[0].split('+')])
        tag = self.__tag
        if callable(tag):
            tag = tag()
        tag_list.discard(tag)
        tag_list = '+'.join(tag_list)
        logger.debug('%s: event[%s], tag[%s], tag_list[%s]' % (self.__class__.__name__, event, tag, tag_list))
        p9_write('/client/sel/tags', tag_list)

def tag_create(event):
    """add left bar entry on tag creation."""
    tag = event.strip().split()[-1]
    if tag and tag != 'NULL':
        logger.debug('tag_create: event[%s], tag[%s]' % (event, tag))
        p9_create('/lbar/%s' % tag, '%s %s' % (BAR_NORMAL_COLORS, t2d(tag)))

def tag_destroy(event):
    """destroy left bar entry on tag deletion."""
    tag = event.strip().split()[-1]
    if tag:
        logger.debug('tag_destroy: event[%s], tag[%s]' % (event, tag))
        p9_remove('/lbar/%s' % tag)

def tag_focus(event):
    """set bar focus colors if a tag is focused."""
    tag = event.strip().split()[-1]
    if tag and tag != 'NULL':
        logger.debug('tag_focus: event[%s], tag[%s]' % (event, tag))
        p9_write('/lbar/%s' % tag, '%s %s' % (BAR_FOCUS_COLORS, t2d(tag)))

def tag_unfocus(event):
    """set bar normal colors if a tag is unfocused."""
    tag = event.strip().split()[-1]
    if tag and tag != 'NULL':
        logger.debug('tag_unfocus: event[%s], tag[%s]' % (event, tag))
        p9_write('/lbar/%s' % tag, '%s %s' % (BAR_NORMAL_COLORS, t2d(tag)))

# ---------------------------------------------------------------------------

RE_DIRECTION = re.compile(r'^.*(?P<dir>-h|-j|-k|-l|-up|-down|-left|-right)$', re.I)
def fit_direction(func):
    def wrapper(event, direction = None):
        if not direction: # try to get direction
            match = RE_DIRECTION.match(event)
            if match:
                direction = match.groupdict().get('dir', None)
                if direction:
                    direction = direction[1:].lower()
                    try:
                        direction = dict(h = 'left', j = 'down', k = 'up', l = 'right')[direction]
                    except:
                        pass
        if direction:
            func(direction.lower())
    return wrapper

@fit_direction
def select(direction):
    """focus client in given direction. (direction will autodetect h/j/k/l/up/down/left/right on specified key)"""
    logger.debug('select: direction[%s]' % direction)
    p9_write('/tag/sel/ctl', 'select %s' % direction)

@fit_direction
def send(direction):
    """send client to given direction. (direction will autodetect h/j/k/l/up/down/left/right on specified key)"""
    logger.debug('send: direction[%s]' % direction)
    p9_write('/tag/sel/ctl', 'send sel %s' % direction)

class DirectionSet(object):
    """
    wrapper to create 4 direction event handlers. derive class and overwrite handler() function.
    see 'SelectSet' and 'SendSet'.
    """
    VIM = 'vim' 
    CURSOR = 'cursor'
    STYLES = dict(cursor = ['Up', 'Down', 'Left', 'Right'], vim = ['h', 'j', 'k', 'l'])
    FUNC = None

    def __init__(self, rprefix, type):
        self.__rprefix = rprefix
        self.__type = type

    def __call__(self):
        hlist = []
        sep = ''
        if str(self.__rprefix)[-1] != '-':
            sep = '-'
        for i in range(0, 4):
            key = copy.deepcopy(self.__rprefix)
            key.add(sep + self.STYLES[self.__type][i])
            hlist.append(EventResolver(key, self.handler()))
        return hlist

    def handler(self):
        raise NotImplementedError('%s: please implement handler getter' % self.__class__.__name__)

class SelectSet(DirectionSet):
    def handler(self):
        return select

class SendSet(DirectionSet):
    def handler(self):
        return send

# ---------------------------------------------------------------------------

def prepare_pn_view(func):
    def wrapper(event):
        act_v = active_view()
        ignore = ['sel/']
        if act_v != SCRATCHPAD:
            ignore.append('%s/' % SCRATCHPAD)
        avail_v = [l.rstrip('/') for l in p9_ls('/tag') if l not in ignore]
        if act_v and act_v in avail_v:
            view(func(act_v, sorted(avail_v)))()
    return wrapper

@prepare_pn_view
def view_next(act_v, avail_v):
    """switch to next view. (excluding scratchpad)"""
    logger.debug('view_next')
    return avail_v[(avail_v.index(act_v) + 1) % len(avail_v)]

@prepare_pn_view
def view_prev(act_v, avail_v):
    """switch to previous view. (excluding scratchpad)"""
    logger.debug('view_prev')
    return avail_v[(avail_v.index(act_v) - 1) % len(avail_v)]

# ---------------------------------------------------------------------------

def toggle(event):
    """toggle layer managed - floating."""
    logger.debug('toggle: event[%s]' % event)
    p9_write('/tag/sel/ctl', 'select toggle')

def send_toggle(event):
    """send current client to mangaged or floating."""
    logger.debug('send_toggle: event[%s]' % event)
    p9_write('/tag/sel/ctl', 'send sel toggle')

# ---------------------------------------------------------------------------

HISTORY = RingBuffer(10)
HISTORY_POS = -1
HISTORY_IGNORE_NEXT = False
HISTORY_DELETE = False
class tag_history(object):
    def __init__(self, max = 20):
        global HISTORY, HISTORY_POS, HISTORY_IGNORE_NEXT, HISTORY_DELETE
        HISTORY = RingBuffer(max)
        HISTORY_POS = -1
        HISTORY_IGNORE_NEXT = False
        HISTORY_DELETE = False

    def __call__(self, event = ''):
        global HISTORY, HISTORY_POS, HISTORY_IGNORE_NEXT, HISTORY_DELETE
        if not HISTORY_IGNORE_NEXT:
            tag = event.strip().split()[-1]
            if tag and tag != 'NULL':
                # clear upper history
                if HISTORY_DELETE:
                    try:
                        for i in range(0, len(HISTORY) - HISTORY_POS):
                            HISTORY.pop()
                    except:
                        pass
                    HISTORY_DELETE = False
                HISTORY.append(tag)
                HISTORY_POS = len(HISTORY) - 1
                logger.debug('history save tag: %s (%d)' % (tag, len(HISTORY)))
                logger.debug('history pos: %s' % HISTORY_POS)
        else:
            HISTORY_IGNORE_NEXT = False
            HISTORY_DELETE = True

def history_prev(event):
    global HISTORY, HISTORY_POS, HISTORY_IGNORE_NEXT
    if HISTORY_POS > 0:
        HISTORY_POS -= 1
        HISTORY_IGNORE_NEXT = True
        logger.debug('history prev: %s' % HISTORY[HISTORY_POS])
        view(HISTORY[HISTORY_POS])()

def history_next(event):
    global HISTORY, HISTORY_POS, HISTORY_IGNORE_NEXT
    if HISTORY_POS < len(HISTORY) - 1:
        HISTORY_POS += 1
        HISTORY_IGNORE_NEXT = True
        logger.debug('history next: %s' % HISTORY[HISTORY_POS])
        view(HISTORY[HISTORY_POS])()

# ---------------------------------------------------------------------------

class execute(object):
    """execute cmd. if cmd is callable, first call cmd to get application path."""
    def __init__(self, cmd):
        self.__cmd = cmd

    def __call__(self, event):
        cmd = self.__cmd
        if callable(cmd):
            cmd = cmd()
        if cmd and len(cmd) > 0:
            logger.debug('execute: event[%s], cmd[%s]' % (event, cmd))
            try:
                subprocess.Popen(cmd.split())
            except Exception, e:
                logger.exception(e)

def kill(event):
    """kill current client."""
    logger.debug('kill')
    p9_write('/client/sel/ctl', 'kill')

def quit(event):
    """quit wmii."""
    logger.debug('quit')
    p9_write('/ctl', 'quit')

class colmode(object):
    """set column mode (default, max, stacked)."""
    def __init__(self, mode = 'default'):
        self.__mode = mode

    def __call__(self, event):
        mode = self.__mode
        if callable(mode):
            mode = mode()
        if mode:
            logger.debug('colmode: event[%s], mode[%s]' % (event, mode))
            p9_write('/tag/sel/ctl', 'colmode sel %s' % mode)

# ---------------------------------------------------------------------------

SCRATCHPAD_ORG_VIEW = SCRATCHPAD
def toggle_scratchpad(event):
    """warp to scratch pad or back to previous view."""
    global SCRATCHPAD_ORG_VIEW
    act_v = active_view()
    if act_v == SCRATCHPAD:  # warp back from scratch pad
        logger.debug('toggle_scratchpad: event[%s], to[%s]' % (event, SCRATCHPAD_ORG_VIEW))
        view(SCRATCHPAD_ORG_VIEW)()
    else:  # warp to scratch pad
        SCRATCHPAD_ORG_VIEW = act_v
        logger.debug('toggle_scratchpad: event[%s], to[%s]' % (event, SCRATCHPAD))
        view(SCRATCHPAD)()

# ---------------------------------------------------------------------------

DMENU_PATH = 'dmenu'
class dmenu(object):
    """
    use dmenu to get an item from a list.

    the list must be given as callable object which returns an python generator 
    or as list. 
    (see application_generator and tag_generator)
    """
    def __init__(self, generator, prompt = None, bottom = True):
        self.__generator = generator
        self.__prompt = prompt
        self.__bottom = bottom

    def __call__(self):
        args = [DMENU_PATH]
        if self.__bottom:
            args.append('-b')
        if self.__prompt:
            args.extend(['-p', self.__prompt])
        args.extend(['-fn', DMENU_FONT])
        args.extend(['-nf', '#%.6X' % DMENU_NORMAL_COLORS.foreground])
        args.extend(['-nb', '#%.6X' % DMENU_NORMAL_COLORS.background])
        args.extend(['-sf', '#%.6X' % DMENU_SELECTION_COLORS.foreground])
        args.extend(['-sb', '#%.6X' % DMENU_SELECTION_COLORS.background])

        try:
            proc = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE, close_fds = True)
            items = self.__generator
            if callable(items):
                items = items()
            proc.stdin.writelines([l + '\n' for l in items])
            proc.stdin.flush()
            proc.stdin.close()
            proc.wait()
            sel = ''.join(proc.stdout.readlines())
            proc.stdout.close()
            logger.debug('dmenu: return[%s]' % sel)
            return sel
        except Exception, e:
            logger.exception(e)
        return ''

# ---------------------------------------------------------------------------

def application_generator():
    """generate list of applications available in $PATH"""
    apps = set()
    validpaths = [path for path in os.environ.get('PATH').split(':') if os.path.exists(path)] 
    for p in validpaths:
        for f in os.listdir(p):
            fullname = os.path.join(p, f)
            if os.path.isfile(fullname) and os.access(fullname, os.X_OK):
                apps.add(f)
                                                            
    for f in sorted(apps):
        yield f

def tag_generator(sort = False):
    """generate list of available tags"""
    ignore = ['sel/']
    avail_v = [t2d(l.rstrip('/')) for l in p9_ls('/tag') if l not in ignore]

    if sort: avail_v.sort()

    for tag in avail_v:
        yield tag

# ---------------------------------------------------------------------------

class call(object):
    """
    use callable event_source object to find proper event in event map.
    eg.
        (MKey('a'), call(dmenu(['quit', 'gimp']), dict(quit = quit, gimp = execute('gimp')))),
    """
    def __init__(self, event_source, event_map):
        self.__event_source = event_source
        self.__event_map = event_map

    def __call__(self, event):
        logger.debug('call: event[%s]' % event)
        ev = self.__event_map.get(self.__event_source(), None)
        if ev:
            ev(event)

class call_dmenu(call):
    """
    simple wrapper for easier menu generation.
    eg.
        (MKey('a'), call_dmenu(dict(quit = quit, gimp = execute('gimp')))),
    """
    def __init__(self, event_map, **kwargs):
        call.__init__(self, dmenu(event_map.keys(), **kwargs), event_map)

# ---------------------------------------------------------------------------

def second_column_hack(event):
    """move second client in tag to second column. restores old wmii-3.6-rc2 behaviour."""
    client_id = event.strip().split()[-1]
    print client_id
    index = [l.strip() for l in p9_read('/tag/sel/index') if not l.strip().startswith('#') and len(l.strip()) > 0]
    if len(index) == 2:
        if index[0][0] == index[1][0] == '1':
            print 'send %s right' % client_id
            logger.debug('move 2nd client %s to 2nd column' % (client_id))
            p9_write('/tag/sel/ctl', 'send %s right' % client_id)


