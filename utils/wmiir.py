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

import os, subprocess, logging

logger = logging.getLogger('utils.wmiir')

__all__ = ['p9_write', 'p9_read', 'p9_create', 'p9_remove', 'p9_ls', 'p9_process', 'p9_available']

WMIIR_PATH = '/usr/bin/wmiir'

def wmiir(cmd):
    def decorator(func):
        def wrapped(path, *args, **kwargs):
            try:
                proc = subprocess.Popen([WMIIR_PATH, cmd, path], stdin = subprocess.PIPE, stdout = subprocess.PIPE, close_fds = True)
                try:
                    ret = func(proc.stdin, proc.stdout, *args, **kwargs)
                finally:
                    proc.stdin.close()
                    proc.stdout.close()
                return ret
            except IOError, e:
                logger.exception(e)
            return None
        return wrapped
    return decorator

@wmiir('write')
def p9_write(stdin, stdout, value):
    if type(value) not in (type([]), type(()), type(set())):
        value = [value]
    stdin.writelines([v + '\n' for v in value])

@wmiir('read')
def p9_read(stdin, stdout):
    return [l.strip() for l in stdout.readlines()]

@wmiir('create')
def p9_create(stdin, stdout, value = None):
    if type(value) not in (type([]), type(())):
        value = [value]
    stdin.writelines([v + '\n' for v in value])

@wmiir('remove')
def p9_remove(stdin, stdout):
    pass

@wmiir('ls')
def p9_ls(stdin, stdout):
    return [l.strip() for l in stdout.readlines()]

@wmiir('read')
def p9_process(stdin, stdout, func, *args, **kwargs):
    """
    call func with each line as parameter. func must return True
    to continue reading.
    """
    next = stdout.readline()
    while next and func(next.strip(), *args, **kwargs):
        next = stdout.readline()

def p9_available():
    if os.path.isfile(WMIIR_PATH):
        return True
    return False
