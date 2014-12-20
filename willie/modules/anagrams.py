#!/usr/bin/env python
"""
anagrams.py - Phenny Anagrams Module
Copyright 2012, Lorenzo J. Lucchini, ljlbox@tiscali.it
Licensed under the Eiffel Forum License 2.

http://languagemodules.sourceforge.net/
"""

import re
import subprocess
import string

import willie.utils as utils
from willie.module import commands, example

@commands('anagrams', 'anagram', 'an')
@example('an pink coons')
def anagrams(phenny, input):
   '''Find anagrams for a given word or short piece of text.'''

   text = utils.commandline(phenny, input, "Give me a word or phrase to find anagrams for!")
   if not text: return

   utils.message(phenny, input, "Anagrams of \x02%s\x02: " % text, wordplay(text), sep=', ')

anagrams.commands = ['anagrams', 'anagram', 'an']
anagrams.thread = True  
anagrams.example = 'an pink coons'
#anagrams.response = 'nick snoop, nick spoon, nick on sop, nick no sop, pick non so, pick on son, pick no son, sock nip on, sock nip no, sock pin on, sock pin no, sock pi non, conn sip ok, con ink sop, con kin sop, con pink so, con skip on, con skip no, con spin ok, con snip ok, cop ink son, cop kin son, cop sink on, cop sink no, cop skin on, cop'
anagrams.exposed = True


def wordplay(text):
   p = subprocess.Popen(["timeout", "5s", "wordplay", "-s", text], stdout=subprocess.PIPE)
   output=p.communicate()[0].lower().strip().split("\n")
   print output
   return sorted(output,key=lambda x:x.count(" "))[:200]

