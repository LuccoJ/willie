#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
utils.py - Phenny Brainstorm Utilities
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

import re
import willie.web

max_length = 510


def commandline(phenny, input, error="Invalid syntax", regexps=None):
   if not input.group(2):
      phenny.reply(error)
      return None

   if regexps:
      if type(regexps) != list: regexps = [regexps]
      for exp in regexps:
         match = re.match(exp, input.group(2).strip())
         if match: return match

      phenny.reply(error)
      return None

   return input.group(2).strip()


def message(phenny, input, before, elements=[], after='', sep=u' — ', cut=True, reply=True, ctcp=False, clear=False, prompt=None):
   global remainder

   if not prompt: prompt = " [... want %smore?]" % phenny.config.prefix

   if not elements: elements = []
   if type(elements) != list: elements = elements.split("\n")
   first = None
   output = None
   done = False
   max = 0
   for max in range(0, len(elements)+2):
      candidates = [first] if first else elements[:max]
      previous = output
      output = buildmsg(phenny, input, before, candidates, after, sep, reply, ctcp, prompt if first or max < len(elements) else "")
      overflow = len(":%s!%s@%s PRIVMSG %s :%s" % (phenny.nick, phenny.user, ' '*63, input.sender, output)) - max_length
      print "MAX", max, len(elements), overflow
      if first: break
      if overflow > 0:
         if not cut:
            print "Not sending message, as it's too long and it won't be cut"
            return False
         else:
            if max > 1:
               print "Can't fit element", max
               max -= 1
               output = previous
               break
            else:
               first = " ".join(elements[0][:-overflow].split(" ")[:-1])
               if not first: first = elements[0][:-overflow]
               print "Cutting first element to", first
   else:
      max -= 1

   if clear:
      del remainder[input.sender.lower()]
   remainder[input.sender.lower()] = ((([elements[0][len(first):]] + elements[1:]) if first else elements[max:]), elements, sep)
   
#   print len(output), output
   if len(output) > max_length: raise Exception("Message still too long after all I did to shorten it: %d characters" % len(output))
   if len(output) == 0: print "Not sending empty message"

   phenny.say(output)

   return True


def buildmsg(phenny, input, before, elements, after="", sep=u"\n", reply=True, ctcp=False, prompt=u''):
   if elements:
      body = sep.join(elements) + prompt
      print "BUILDMSG", type(elements), type(elements[0]), elements
   else:
      body = ""
      print "BUILDMSG", before, after
   output = before + body + after
   if reply: output = "%s, %s" % (input.nick, output)
   if ctcp: output = "\x01%s\x01" % output
   return output


def more(phenny, input):
   channel = input.sender.lower()
   if input.sender.lower() in remainder:
      pending, full, separator = remainder[channel]
      if not pending:
         message(phenny, input, "There is nothing more to show.")
      else:
         post = buildmsg(phenny, input, "" , full, sep="\n", reply=False)
         if not message(phenny, input, "[...] ", pending, sep=separator, cut=False):
            message(phenny, input, "[...] ", pending, u' — %s' % paste(post), sep=separator, prompt=" [...]")
            del remainder[channel]
   else:
      message(phenny, input, "I have said all there was to say!")


def paste(text, title="", format='text'):
   global pastebin_key

   response = web.post("http://pastebin.com/api/api_post.php", {
      'api_option': 'paste',
      'api_dev_key': pastebin_key,
      'api_paste_code': text.encode('utf-8'),
      'api_paste_private': '0',
      'api_paste_name': title.encode('utf-8'),
      'api_paste_expire_date': '1D',
      'api_paste_format': format
   })

   if len(response) > 200: raise IOError("Pastebin is not responding correctly")

   return response


remainder = {}


# Omit
pastebin_key = '2de0c133e1d1e0c0f3656c7789d8b4be'
