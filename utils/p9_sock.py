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

import os, logging, socket, thread
import P9

logger = logging.getLogger('utils.p9_sock')

__all__ = ['p9_write', 'p9_read', 'p9_create', 'p9_remove', 'p9_ls', 'p9_process', 'p9_available']

def lock(func):
    def wrapper(self, *args, **kwargs):
        self.lock.acquire()
        ret = None
        try:
            ret = func(self, self.counter, *args, **kwargs)
        except Exception, e:
            logger.exception(e)
            try:
                _close(self.counter)
            except:
                pass
        self.counter += 1
        self.lock.release()
        return ret
    return wrapper

class P9Exception(Exception):
    pass
    
class P9Client(object):
    ROOT = 23
    def __init__(self):
        sock_path = os.environ.get('WMII_ADDRESS', '').split('!')
        try:
            if sock_path[0] == 'unix':
                sock = socket.socket(socket.AF_UNIX)
                sock.connect(sock_path[1])
            elif sock_path[0] == 'tcp':
                sock = socket.socket(socket.AF_INET)
                sock.connect((sock_path[1], int(sock_path[2])))
            else:
                return
        except socket.error, e:
            logger.exception(e)
            sys.exit(-1)

        self.__rpc = P9.RpcClient(P9.Sock(sock))

        maxbuf,vers = self.__rpc.version(16 * 1024, P9.version)
        if vers != P9.version :
            raise Error('version mismatch: %r' % vers)

        self.__rpc.attach(self.ROOT, P9.nofid, '', '')
        self.connected = True
        self.counter = 42
        self.lock = thread.allocate_lock()

    def __walk(self, fd, path):
        pstr = path
        root = self.ROOT
        path = filter(None, path.split('/'))
        try: 
            w = self.__rpc.walk(root, fd, path)
        except P9.RpcError, e:
            raise P9Exception('_walk: %s: %s' % (pstr, e.args[0]))
        if len(w) < len(path):
            raise P9Exception('_walk: %s: not found' % pstr)
        return w

    def __open(self, fd, mode = 0):
        try:
            t = self.__rpc.open(fd, mode)
            if not t:
                raise P9Exception('_open: failed to open')
        except P9.RpcError, e:
            raise P9Exception('_open: %s' % e.args[0])
        return t

    def __close(self, fd):
        try:
            self.__rpc.clunk(fd)
        except P9.RpcError, e:
            raise P9Exception('_close: %s' % e.args[0])

    def __read(self, fd, length):
        try:
            pos = 0L
            buf = self.__rpc.read(fd, pos, length)
            while len(buf) > 0:
                pos += len(buf)
                yield buf
                buf = self.__rpc.read(fd, pos, length)
        except P9.RpcError, e:
            raise P9Exception('_read: %s' % e.args[0])

    def __write(self, fd, buf):
        try:
            towrite = len(buf)
            pos = 0
            while pos < towrite:
                pos += self.__rpc.write(fd, pos, buf[pos:pos + 1024])
        except P9.RpcError, e:
            raise P9Exception('_write: %s' % e.args[0])

    def __create(self, fd, name, mode = 1, perm = 0644):
        try:
            return self.__rpc.create(fd, name, perm, mode)
        except P9.RpcError, e:
            self._close()
            raise P9Exception('_create: %s' % e.args[0])

    def __remove(self, fd):
        try:
            self.__rpc.remove(fd)
        except P9.RpcError, e:
            raise P9Exception('_remove: %s' % e.args[0])

    @lock
    def p9_write(self, fd, file, value):
        if type(value) not in (type([]), type(()), type(set())):
            value = [value]
        self.__walk(fd, file)
        self.__open(fd, mode = P9.OWRITE|P9.OTRUNC)
        self.__write(fd, '\n'.join(value) + '\n')
        self.__close(fd)

    @lock
    def p9_read(self, fd, file):
        ret = ''
        self.__walk(fd, file)
        self.__open(fd)
        for buf in self.__read(fd, 4096):
            ret += buf
        ret = ret.split('\n')
        self.__close(fd)
        return ret

    @lock
    def p9_create(self, fd, file, value = None):
        if type(value) not in (type([]), type(()), type(set())):
            value = [value]
        plist = file.split('/')
        path, name = '/'.join(plist[:-1]), plist[-1]
        self.__walk(fd, path)
        self.__create(fd, name)
        self.__write(fd, '\n'.join(value))
        self.__close(fd)

    @lock
    def p9_remove(self, fd, path):
        self.__walk(fd, path)
        self.__open(fd)
        self.__remove(fd)

    @lock
    def p9_ls(self, fd, path):
        ret = []
        self.__walk(fd, path)
        self.__open(fd)
        for buf in self.__read(fd, 4096):
            p9 = self.__rpc.msg
            p9.setBuf(buf)
            for sz,t,d,q,m,at,mt,l,name,u,g,mod in p9._decStat(0) :
                if m & P9.DIR:
                    name += '/'
                ret.append(name)
        self.__close(fd)
        return ret

    @lock
    def p9_process(self, fd, file, func, *args, **kwargs):
        self.__walk(fd, file)
        self.__open(fd)
        obuf = ''
        cont = True
        for buf in self.__read(fd, 4096):
            buf = obuf + buf
            lnl = buf.rfind('\n')
            for line in buf[0:lnl].split('\n'):
                if not func(line.strip(), *args, **kwargs):
                    cont = False
                    break
            if not cont:
                break
            obuf = buf[lnl + 1:]
        self.__close(fd)

cl = P9Client()

def p9_available():
    return cl.connected

def p9_write(path, value):
    global cl
    return cl.p9_write(path, value)

def p9_read(path):
    global cl
    return cl.p9_read(path)

def p9_create(path, value = None):
    global cl
    return cl.p9_create(path, value)

def p9_remove(path):
    global cl
    return cl.p9_remove(path)

def p9_ls(path):
    global cl
    return cl.p9_ls(path)

def p9_process(path, func, *args, **kwargs):
    ncl = P9Client()
    if ncl.connected:
        return ncl.p9_process(path, func, *args, **kwargs)

