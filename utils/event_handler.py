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
import subprocess
import logging
import copy
from utils import *
from utils.ringbuffer import RingBuffer
from config import BAR_NORMAL_COLORS, BAR_FOCUS_COLORS, SCRATCHPAD, \
                   DMENU_FONT, DMENU_NORMAL_COLORS, DMENU_SELECTION_COLORS

logger = logging.getLogger('utils.event_handler')

# ---------------------------------------------------------------------------

class FWrap(object):
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

class View(object):
    """
    switch to a view.

    tag can be set in constructor or is automagically get from the event.
    (last item from event line)

    if the view is get from the event, the button in the event must be in 
    'buttons'.
    """
    def __init__(self, tag = None, buttons = ('1', '2')):
        self._tag = tag
        self._buttons = buttons

    def __call__(self, event = '', tag = None):
        tag = self._tag or tag
        button = self._buttons[0]
        if not tag:
            try:
                tag = event.strip().split()[-1]
            except:
                pass
            try:
                button = event.strip().split()[-2]
            except:
                pass

        if button in self._buttons:
            if callable(tag):
                tag = tag()
            tag = real_tag_name(tag)
            logger.debug('%s: event[%s], tag[%s]' % (self.__class__.__name__, event, tag))
            p9_write('/ctl', 'view %s' % tag)

    def _get_views(self, ignore_scratchpad = True):
        act_v = active_view()
        ignore = ['sel/']
        if ignore_scratchpad and act_v != SCRATCHPAD:
            ignore.append('%s/' % SCRATCHPAD)
        avail_v = [l.rstrip('/') for l in p9_ls('/tag') if l not in ignore]
        return sorted(avail_v)

class WheelView(object):
    """
    if the mouse button is '4' or '5' (mouse wheel up/down), this handler switch to the
    next/previous view.
    """
    def __call__(self, event):
        try:
            button = event.strip().split()[-2]
            logger.debug('view_wheel: event[%s], button[%s]' % (event, button))
            if button == '4':
                PrevView()()
            elif button == '5':
                NextView()()
        except Exception, e:
            logger.exception(e)

class NextView(View):
    """switch to next view. (excluding scratchpad)"""
    def __init__(self, ignore_scratchpad = True):
        View.__init__(self)
        self.__ignore_scratchpad = ignore_scratchpad

    def __call__(self, event = None):
        act_view = active_view()
        avail_views = self._get_views(self.__ignore_scratchpad)
        next_view = avail_views[(avail_views.index(act_view) + 1) % len(avail_views)]
        logger.debug('next_view: %s (act view: %s)' % (next_view, act_view))
        View.__call__(self, tag = next_view)

class PrevView(View):
    """switch to previous view. (excluding scratchpad)"""
    def __init__(self, ignore_scratchpad = True):
        View.__init__(self)
        self.__ignore_scratchpad = ignore_scratchpad

    def __call__(self, event = None):
        act_view = active_view()
        avail_views = self._get_views(self.__ignore_scratchpad)
        prev_view = avail_views[(avail_views.index(act_view) - 1) % len(avail_views)]
        logger.debug('prev_view: %s (act view: %s)' % (prev_view, act_view))
        View.__call__(self, tag = prev_view)

# ---------------------------------------------------------------------------

class SetTag(object):
    """set tag to current client. other tag settings are overwritten."""
    def __init__(self, tag = None):
        self.__tag = tag

    def __call__(self, event = ''):
        tag = self.__tag
        if callable(tag):
            tag = tag()
        tag = real_tag_name(tag)
        logger.debug('%s: event[%s], tag[%s]' % (self.__class__.__name__, event, tag))
        p9_write('/client/sel/tags', tag)

class AddTag(object):
    """add tag to current client. other tag settings are preserved."""
    def __init__(self, tag = None):
        self.__tag = tag

    def __call__(self, event = ''):
        tag_list = set([tag.strip() for tag in p9_read('/client/sel/tags')[0].split('+')])
        tag = self.__tag
        if callable(tag):
            tag = tag()
        tag = real_tag_name(tag)
        tag_list.add(tag)
        tag_list = '+'.join(tag_list)
        logger.debug('%s: event[%s], tag[%s], tag_list[%s]' % (self.__class__.__name__, event, tag, tag_list))
        p9_write('/client/sel/tags', tag_list)

class RemoveTag(object):
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

class TagCreate(object):
    """add left bar entry on tag creation."""
    def __call__(self, event):
        tag = event.strip().split()[-1]
        if tag and tag != 'NULL':
            tag = real_tag_name(tag)
            logger.debug('tag_create: event[%s], tag[%s]' % (event, tag))
            p9_create('/lbar/%s' % real_tag_name(tag), '%s %s' % (BAR_NORMAL_COLORS, display_tag_name(tag)))

class TagDestroy(object):
    """destroy left bar entry on tag deletion."""
    def __call__(self, event):
        tag = event.strip().split()[-1]
        if tag:
            tag = real_tag_name(tag)
            logger.debug('tag_destroy: event[%s], tag[%s]' % (event, tag))
            p9_remove('/lbar/%s' % tag)

class TagFocus(object):
    """set bar focus colors if a tag is focused."""
    def __call__(self, event):
        tag = event.strip().split()[-1]
        if tag and tag != 'NULL':
            tag = real_tag_name(tag)
            logger.debug('tag_focus: event[%s], tag[%s]' % (event, tag))
            p9_write('/lbar/%s' % real_tag_name(tag), '%s %s' % (BAR_FOCUS_COLORS, display_tag_name(tag)))

class TagUnfocus(object):
    """set bar normal colors if a tag is unfocused."""
    def __call__(self, event):
        tag = event.strip().split()[-1]
        if tag and tag != 'NULL':
            tag = real_tag_name(tag)
            logger.debug('tag_unfocus: event[%s], tag[%s]' % (event, tag))
            p9_write('/lbar/%s' % real_tag_name(tag), '%s %s' % (BAR_NORMAL_COLORS, display_tag_name(tag)))

class TagUrgent(object):
    """mark an tag urgent"""
    def __call__(self, event):
        tag = event.strip().split()[-1]
        if tag and tag != 'NULL':
            tag = real_tag_name(tag)
            logger.debug('tag_urgent: event[%s], tag[%s]' % (event, tag))
            p9_write('/lbar/%s' % real_tag_name(tag), '*' + display_tag_name(tag))

class TagNotUrgent(object):
    """unmark an tag urgent"""
    def __call__(self, event):
        tag = event.strip().split()[-1]
        if tag and tag != 'NULL':
            tag = real_tag_name(tag)
            logger.debug('tag_not_urgent: event[%s], tag[%s]' % (event, tag))
            p9_write('/lbar/%s' % real_tag_name(tag), display_tag_name(tag))

# ---------------------------------------------------------------------------

class DirectionNormalizer(object):
    RE_DIRECTION = re.compile(r'^.*(?P<dir>-h|-j|-k|-l|-up|-down|-left|-right)$', re.I)
    def normalize(self, event):
        direction = None
        match = DirectionNormalizer.RE_DIRECTION.match(event)
        if match:
            direction = match.groupdict().get('dir', None)
            if direction:
                direction = direction[1:].lower()
                try:
                    direction = dict(h = 'left', j = 'down', k = 'up', l = 'right')[direction]
                except:
                    pass
        return direction

class Select(DirectionNormalizer):
    """focus client in given direction. (direction will autodetect h/j/k/l/up/down/left/right on specified key)"""
    def __init__(self, direction = None):
        self.__direction = direction

    def __call__(self, event):
        direction = self.__direction
        if not direction:
            direction = self.normalize(event)
        logger.debug('select: direction[%s]' % direction)
        p9_write('/tag/sel/ctl', 'select %s' % direction)

class Send(DirectionNormalizer):
    """send client to given direction. (direction will autodetect h/j/k/l/up/down/left/right on specified key)"""
    def __init__(self, direction = None):
        self.__direction = direction

    def __call__(self, event):
        direction = self.__direction
        if not direction:
            direction = self.normalize(event)
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

    def __init__(self, rprefix, rpostfix, type):
        self.__rprefix = rprefix.rstrip('-')
        self.__rpostfix = rpostfix.lstrip('-')
        self.__type = type

    def __call__(self):
        klist = []
        style_list = self.STYLES[self.__type]
        for style in style_list:
            key = '%s-%s%s' % (self.__rprefix, style, self.__rpostfix)
            klist.append(key)
        return (klist, self.handler())

    def handler(self):
        raise NotImplementedError('%s: please implement handler getter' % self.__class__.__name__)

class SelectSet(DirectionSet):
    def handler(self):
        return Select()

class SendSet(DirectionSet):
    def handler(self):
        return Send()

# ---------------------------------------------------------------------------

class Toggle(object):
    """toggle layer managed - floating."""
    def __call__(self, event):
        logger.debug('toggle: event[%s]' % event)
        p9_write('/tag/sel/ctl', 'select toggle')

class SendToggle(object):
    def __call__(self, event):
        """send current client to mangaged or floating."""
        logger.debug('send_toggle: event[%s]' % event)
        p9_write('/tag/sel/ctl', 'send sel toggle')

# ---------------------------------------------------------------------------

HISTORY = RingBuffer(10)
HISTORY_POS = -1
HISTORY_IGNORE_NEXT = False
HISTORY_DELETE = False
class TagHistory(object):
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

class HistoryPrev(object):
    def __call__(self, event):
        global HISTORY, HISTORY_POS, HISTORY_IGNORE_NEXT
        if HISTORY_POS > 0:
            HISTORY_POS -= 1
            HISTORY_IGNORE_NEXT = True
            logger.debug('history prev: %s' % HISTORY[HISTORY_POS])
            View(HISTORY[HISTORY_POS])()

class HistoryNext(object):
    def __call__(self, event):
        global HISTORY, HISTORY_POS, HISTORY_IGNORE_NEXT
        if HISTORY_POS < len(HISTORY) - 1:
            HISTORY_POS += 1
            HISTORY_IGNORE_NEXT = True
            logger.debug('history next: %s' % HISTORY[HISTORY_POS])
            View(HISTORY[HISTORY_POS])()

# ---------------------------------------------------------------------------

class Execute(object):
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

class Kill(object):
    def __call__(self, event = None):
        """kill current client."""
        logger.debug('kill')
        p9_write('/client/sel/ctl', 'kill')

class Quit(object):
    def __call__(self, event = None):
        """quit wmii."""
        logger.debug('quit')
        p9_write('/ctl', 'quit')

class ColMode(object):
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
class ToggleScratchPad(object):
    def __call__(self, event):
        """warp to scratch pad or back to previous view."""
        global SCRATCHPAD_ORG_VIEW
        act_view = active_view()
        if act_view == SCRATCHPAD:  # warp back from scratch pad
            logger.debug('toggle_scratchpad: event[%s], to[%s]' % (event, SCRATCHPAD_ORG_VIEW))
            View(SCRATCHPAD_ORG_VIEW)()
        else:  # warp to scratch pad
            SCRATCHPAD_ORG_VIEW = act_view
            logger.debug('toggle_scratchpad: event[%s], to[%s]' % (event, SCRATCHPAD))
            View(SCRATCHPAD)()

# ---------------------------------------------------------------------------

DMENU_PATH = 'dmenu'
class DMenu(object):
    """
    use dmenu to get an item from a list.

    the list must be given as callable object which returns an python generator
    or as list.
    (see application_generator and tag_generator)
    """
    def __init__(self, generator, prompt = None, bottom = True, dmenupath = DMENU_PATH):
        self.__generator = generator
        self.__prompt = prompt
        self.__bottom = bottom
        self.__dmenupath = dmenupath

    def __call__(self):
        args = [self.__dmenupath]
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
            sel = proc.stdout.readline().strip()
            proc.stdout.close()
            logger.debug('dmenu: return[%s]' % sel)
            return sel
        except Exception, e:
            logger.exception(e)
            # try to close open subprocess
            try:
                proc.stdin.close()
            except:
                pass
            try:
                proc.stdout.close()
            except:
                pass
        return ''

WMII9PATH = 'wmii9menu'
class WMII9Menu(object):
    """
    use wmii9menu to get an item from a list.

    the list must be given as callable object which returns an python generator
    or as list.
    (see application_generator and tag_generator)
    """
    def __init__(self, generator, wmii9path = WMII9PATH):
        self.__generator = generator
        self.__wmii9path = wmii9path

    def __call__(self):
        args = [self.__wmii9path]
        args.extend(['-font', DMENU_FONT])
        args.extend(['-nf', '#%.6X' % DMENU_NORMAL_COLORS.foreground])
        args.extend(['-nb', '#%.6X' % DMENU_NORMAL_COLORS.background])
        args.extend(['-sf', '#%.6X' % DMENU_SELECTION_COLORS.foreground])
        args.extend(['-sb', '#%.6X' % DMENU_SELECTION_COLORS.background])
        args.extend(['-br', '#%.6X' % DMENU_NORMAL_COLORS.border])
        items = self.__generator
        if callable(items):
            items = items()
        args.extend(items)

        try:
            proc = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE, close_fds = True)
            proc.wait()
            sel = proc.stdout.readline().strip()
            proc.stdout.close()
            logger.debug('wmii9menu: return[%s]' % sel)
            return sel
        except Exception, e:
            logger.exception(e)
        return ''

# ---------------------------------------------------------------------------

class ApplicationGenerator(object):
    def __call__(self):
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

class TagGenerator(object):
    def __init__(self, sort = False):
        self.__sort = sort

    def __call__(self):
        """generate list of available tags"""
        ignore = ['sel/']
        avail_views = [display_tag_name(l.rstrip('/')) for l in p9_ls('/tag') if l not in ignore]

        if self.__sort:
            avail_views.sort()

        for tag in avail_views:
            yield tag

# ---------------------------------------------------------------------------

class Call(object):
    """
    use callable event_source object to find proper event in event map.
    eg.
        (MKey('a'), Call(dmenu(['quit', 'gimp']), dict(quit = quit, gimp = execute('gimp')))),
    """
    def __init__(self, event_source, event_map):
        self.__event_source = event_source
        self.__event_map = event_map

    def __call__(self, event):
        logger.debug('call: event[%s]' % event)
        ev = self.__event_map.get(self.__event_source(), None)
        if ev:
            ev(event)

class CallDMenu(Call):
    """
    simple wrapper for easier menu generation.
    eg.
        (MKey('a'), call_dmenu(dict(quit = quit, gimp = execute('gimp')))),
    """
    def __init__(self, event_map, **kwargs):
        Call.__init__(self, DMenu(event_map.keys(), **kwargs), event_map)

class CallWMII9Menu(Call):
    """
    simple wrapper for easier menu generation.
    eg.
        (MKey('a'), call_wmii9menu(dict(quit = quit, gimp = execute('gimp')))),
    """
    def __init__(self, event_map, **kwargs):
        Call.__init__(self, WMII9Menu(event_map.keys(), **kwargs), event_map)

# ---------------------------------------------------------------------------

class SecondColumnHack(object):
    def __call__(self, event):
        """move second client in tag to second column. restores old wmii-3.6-rc2 behaviour."""
        client_id = event.strip().split()[-1]
        print client_id
        index = [l.strip() for l in p9_read('/tag/sel/index') if not l.strip().startswith('#') and len(l.strip()) > 0]
        if len(index) == 2:
            if index[0][0] == index[1][0] == '1':
                print 'send %s right' % client_id
                logger.debug('move 2nd client %s to 2nd column' % (client_id))
                p9_write('/tag/sel/ctl', 'send %s right' % client_id)

