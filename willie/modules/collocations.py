#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
collocations.py - Phenny Collocations Module
Copyright 2012, Lorenzo J. Lucchini, ljlbox@tiscali.it
Licensed under the Eiffel Forum License 2.

http://languagemodules.sourceforge.net/
"""

import re
import subprocess
import string
import urllib
import willie.utils as utils
import willie.web as web
#from tools import deprecated

url = 'http://forbetterenglish.com/index.cgi?str=%s'
r_collocations = re.compile(r'004444;">(.*)</span>')

def collocations(phenny, input): 
   '''Provides collocations for a given word.'''
   word = input.group(2)

   page = web.get(url % word)
   colls = r_collocations.findall(page)
   output = [c.replace(word, u'~') for c in colls]

   if not output:
      output = "No collocations found for " + word

   utils.message(phenny, input, "Collocations for \x02%s\x02" % word, output, sep=', ')

collocations.rule = (['collocations', 'co'], r"(.*)$")
collocations.thread = True
collocations.priority = 'medium'
collocations.example = 'co test'
