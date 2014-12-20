#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
db.py - Phenny Natural Language Tools
Copyright 2013, Lorenzo J. Lucchini, ljlbox@tiscali.it

http://languagemodules.sourceforge.net/

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import threading

from ZODB.FileStorage import FileStorage
from ZODB.DB import DB
from BTrees.OOBTree import OOBTree
import transaction

connection = db = None


def closedb():
   global db, connection
   connection.close()
   connection = db = None

def opendb():
   global db, connection
   if not db:
      connection = DB(FileStorage('brainstorm.fs'))
      db = connection.open().root()
   return db

def packdb():
   connection.pack()
