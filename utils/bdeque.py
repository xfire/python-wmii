# blocking deque
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

from collections import deque
from threading import Semaphore

__all__ = ['bdeque']

class bdeque(deque):
    def __init__(self, iterable = []):
        self.__size_sema = Semaphore(len(iterable))
        deque.__init__(self, iterable)

    def append(self, x):
        deque.append(self, x)
        self.__size_sema.release()

    def appendleft(self, x):
        deque.appendleft(self, x)
        self.__size_sema.release()

    def clear():
        l = len(self)
        deque.clear(self)
        for i in range(0, l):
            self.__size_sema.acquire()
        
    def extend(self, iterable):
        deque.extend(self, iterable)
        for i in range(0, len(iterable)):
            self.__size_sema.release()
        
    def extendleft(self, iterable):
        deque.extend(self, iterable)
        for i in range(0, len(iterable)):
            self.__size_sema.release()

    def pop(self):
        self.__size_sema.acquire()
        return deque.pop(self)

    def popleft(self):
        self.__size_sema.acquire()
        return deque.popleft(self)

