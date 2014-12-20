#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sentiments.py - Phenny Sentiments Module
Copyright 2013, Lorenzo J. Lucchini, ljlbox@tiscali.it
Licensed under the Eiffel Forum License 2.

http://languagemodules.sourceforge.net/
"""

import re
import string
import shelve
import random
import willie.natlang as lang
import willie.utils as utils
import willie.web as web

import time


import os

iom_url = 'http://www.insult-o-matic.com/insults/?yourname=LjL&numinsults=1&mode=shakespeare'
iom_re = re.compile(r'<font size=\+3>T</font>(.*)')

scg_url = 'http://www.madsci.org/cgi-bin/cgiwrap/~lynn/jardin/SCG'
scg_re = re.compile(r'<h2>\s*(.*)\s*</h2>')


print os.getcwd()
sentiments = shelve.open("sentiments.db", "r", writeback=True)



def evaluate(phenny, input):
   '''Give a positivity/negativity evaluation of a word'''
   word, language = lang.args(input.sender, input.group(2), count=1)
   response = dict()
   for pos in sentiments:
      print pos
      count = 0
      max_pos = max_neg = 0
      min_pos = min_neg = 1
      for i in range(1, 40) if '#' not in word else [1]:
         if '#' in word: lemma = word
         else: lemma = "%s#%d" % (word, i)
         print lemma
         if lemma in sentiments[pos]:
            print "IN: " + lemma
            val_pos, val_neg = sentiments[pos][lemma]
            if val_pos > max_pos: max_pos = val_pos
            if val_neg > max_neg: max_neg = val_neg
            if val_pos < min_pos: min_pos = val_pos
            if val_neg < min_neg: min_neg = val_neg
            count += 1
         else:
            break
      if count:
         positiveness = (("between %d%% and %d%%" % (min_pos*100, max_pos*100)) if min_pos != max_pos else ("%d%%" % (max_pos*100))) + " positive"
         negativeness = (("between %d%% and %d%%" % (min_neg*100, max_neg*100)) if min_neg != max_neg else ("%d%%" % (max_neg*100))) + " negative"
         if pos == 'a': pos_name = 'adjective'
         if pos == 'n': pos_name = 'noun'
         if pos == 'v': pos_name = 'verb'
         if pos == 'r': pos_name = 'adverb'
         sense=int(word.split("#")[1]) if len(word.split("#"))>1 else 1
         if count==1: response[pos] = "The %s \x02%s\x02 (meaning %s) is %s, %s" % (pos_name, word, ", ".join(lang.wordnet(word.split("#")[0], 'syns'+pos, sense=sense)[:3]), positiveness, negativeness)
         elif count>0: response[pos] = "The %s \x02%s\x02 is %s, %s" % (pos_name, word, positiveness, negativeness)

   if response:
      phenny.reply(" - ".join(response.values()))
   else:
      phenny.reply("Sorry, what? I found nothing.")
         
evaluate.commands = ['evaluate', 'eval', 'ev']
evaluate.example = 'ev nice'
evaluate.response = 'The adjective \x02nice\x02 is between 0% and 87% positive, between 0% and 37% negative - The noun \x02nice\x02 (meaning Nice, city, metropolis) is 0% positive, 0% negative'
evaluate.exposed = True


def build_remark(compliment=False, templates = [
   ("looks like you %s some %s %s", ['v', 'a', 'n']),
   ("you're so %s that I would like to %s you all with my %s", ['a', 'v', 'n']),
   ("has anyone ever told you about the %s %s you %s so %s?", ['a', 'n', 'v', 'r'])
]):
   format, tags = random.choice(templates)
   w=[]
   for pos in tags:
      print pos
      entry = None
      keys = sentiments[pos].keys()
      while entry is None or (entry[0 if compliment else 1]<0.6 or entry[1 if compliment else 0]>0.2):
         word = random.choice(keys)
         entry = sentiments[pos][word]
      w.append(word.replace("_", " ").split("#")[0])
   return format % tuple(w)


def build_idiom():
   print "Doing..."
   w=[]
   for pos in ['v', 'n', 'n']:
      print pos
      entry = None
      keys = sentiments[pos].keys()
      while entry is None or (entry[0]>0.1 or entry[1]>0.1):
         word = random.choice(keys)
         entry = sentiments[pos][word]
      w.append(word.replace("_", " ").split("#")[0])
   return "%s the %s with some %s" % (w[0], w[1], w[2])


def insult(phenny, input):
   '''Insult somebody creatively'''
   if not input.group(2):
      phenny.reply("Whom should I insult?")
      return

   nick = input.group(2)

   if nick == phenny.nick:
      nick = "%s with thy hideous cleverness" % input.sender

   if random.choice(['shakespeare', 'wordnet']) == 'wordnet':
      response = build_remark(compliment=False)
   else:
      response = web.get(iom_url)
      response = iom_re.search(response).group(1)
      if response: response = "t" + response

   if response:
      response = lang.filter_badwords(response)
      response = response.replace("  ", " ")
      phenny.say("%s, %s" % (nick, response))
   else:
      phenny.say("%s, You... you... silly... person...?" % nick)

insult.commands = ['insult', 'it']


def compliment(phenny, input):
   '''Compliment somebody creatively'''
   if not input.group(2):
      phenny.reply("Whom should I compliment?")
      return

   nick = input.group(2)

   if nick == phenny.nick:
      nick = "%s with thy amazing brain" % input.sender

   if random.choice(['scg', 'wordnet']) == 'wordnet':
      response = build_remark(compliment=True)
   else:
      response = web.get(scg_url)
      response = scg_re.search(response.replace("\n", " ")).group(1)

   if response:
      response = lang.filter_badwords(response)
      response = response.replace("  ", " ")
      phenny.say("%s, %s" % (nick, response))
   else:
      phenny.say("%s, You... you... silly... person...?" % nick)

compliment.commands = ['compliment', 'flatter', 'cm']


def action(phenny, input):
   phenny.say("\x01ACTION goes to %s\x01" % build_idiom())

action.commands = ['action']


def sentiwordnet(word, pos):
   '''Give a positivity/negativity evaluation of a word'''
   count = 0
   max_pos = max_neg = 0
   min_pos = min_neg = 1
   for i in range(1, 40) if '#' not in word else [1]:
      if '#' in word: lemma = word
      else: lemma = "%s#%d" % (word, i)
      if lemma in sentiments[pos]:
         val_pos, val_neg = sentiments[pos][lemma]
         if val_pos > max_pos: max_pos = val_pos
         if val_neg > max_neg: max_neg = val_neg
         if val_pos < min_pos: min_pos = val_pos
         if val_neg < min_neg: min_neg = val_neg
         count += 1
      else:
         break
   if count: return ((min_pos, max_pos), (min_neg, max_neg))
   else: return ((None, None), (None, None))


def watch_for_action(phenny, input):
   try:
      line = input.group(1)

      print "Line acquired"

      match = re.match(r"(.*) +" + re.escape(phenny.config.nick.lower()) + r"(?:( +with| +like|)(?: +(a|some|the))? +(.*))?$", line.lower())
      if not match: return

      verb = re.sub(r"ies\b", "y", re.sub(r"s\b", "", match.group(1))).strip()
      preposition = (match.group(2) or '').strip()
      items = (match.group(4) or '').strip().split(" ")

      total_pos = total_neg = 0.0
      for word, pos in [(verb, 'v')] + [(item, 'a') for item in items] + [(item, 'n') for item in items]:
         (min_pos, max_pos), (min_neg, max_neg) = sentiwordnet(word, pos)
         if min_pos is not None:
            total_pos += (min_pos+max_pos) * 0.5
            total_neg += (min_neg+max_neg) * 0.5
         else:
            print "%s (%s) can't be scored" % (word, pos)

      if total_pos < 0.2 and total_neg < 0.2:
         phenny.reply("Do as you wish!")
         return
      elif total_pos > total_neg:
         print "Outputting a compliment"
         compliment = True
      else:
         print "Outputting an insult"
         compliment = False

      response = build_remark(compliment=compliment, templates=[("starts to %%s %s with some %%s %%s" % input.nick, ['v', 'a', 'n'])]) 
      response = lang.filter_badwords(response)

      phenny.say("\x01ACTION %s\x01" % response)

   except Exception as e:
      print "Could NOT respond to action:", e

watch_for_action.rule = r"\x01ACTION (.*)\x01"
watch_for_action.hidden = True


#def go(phenny, input):
#   phenny.say("Starting the movie in...")
#   time.sleep(2)
#   phenny.say("5...")
#   
#   time.sleep(2)
#   phenny.say("4...")
#   time.sleep(2)
#   phenny.say("3...")
#   time.sleep(2)
#   phenny.say("2...")
#   time.sleep(2)
#   phenny.say("1...")
#   time.sleep(2)
#   phenny.say("GO!!!!!!!11111one")

#go.commands = ['go']
