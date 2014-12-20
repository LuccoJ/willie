#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
natlang.py - Phenny Natural Language Tools
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
import subprocess
import web
import os.path
import threading
import random
import shelve
import datetime
import ctypes
import locale
import time
import urllib
from collections import defaultdict

#locale.setlocale(locale.LC_ALL, '')

import languages
import ipakey
import willie.brainstorm as db

import nltk
from ipazounds import ipa, zounds
from cobe.brain import Brain
import cobe
import guess_language
#import cld
import langid
#import textcat

from ZODB.FileStorage import FileStorage
from ZODB.DB import DB
from BTrees.OOBTree import OOBTree
from persistent.list import PersistentList



initialized = defaultdict(bool)


global_stopwords = {u'like', u'a', u'the', u'is'}
custom_languages_extended_latin = {'sme'}
custom_languages_cyrillic = {'kum'}

languagedb = None
languagedb_lock = threading.Lock()
language_cache = defaultdict(lambda: defaultdict(lambda: None))


try:
   textcat_identifier = textcat.TextCat("/usr/share/libexttextcat/fpdb.conf", "/usr/share/libexttextcat")
except:
   textcat_identifier = None

ode_url = 'http://www.oxforddictionaries.com/definition/english/%s?q=%s'
ode_re = re.compile(r'<a href="http://(?:www.)?oxforddictionaries.com/words/key-to-pronunciation"> ([^<]*)</a>')


markov_backlog = defaultdict(list)
markov_locks = defaultdict(threading.RLock)

markov_order = 2



class PhonologyError(Exception):
   pass

class PhonologyRuleError(PhonologyError):
   pass

class PhonologyDateError(PhonologyError):
   pass

class PhonologyRepresentationError(PhonologyError):
   pass


class GrammarScorer(cobe.scoring.Scorer):
   def score(self, reply):
      if check_grammar(reply.to_text(), 'eng'):
#      if check_grammar("This is a test.", 'eng'):
         return 1.0
      else:
         return 0.0


class OriginalityScorer(cobe.scoring.Scorer):
   def __init__(self, reference_brain):
      self.reference_brain = reference_brain

   def score(self, reply):
      global_brain_cache = self.cache.setdefault('brain_cache', get_brain(self.reference_brain))



def startup():
   global initialized
   global guess_language

   guess_language.guess_language.EXTENDED_LATIN += list(custom_languages_extended_latin)
   guess_language.guess_language.ALL_LATIN += list(custom_languages_extended_latin)
   guess_language.guess_language.CYRILLIC += list(custom_languages_cyrillic)

   print "Opening database..."
   opendb()
   print "Caching language names..."
   build_language_cache()
   print "Pre-loading language identifiers..."
   identify_language("")
   print "Populating Apertium list..."
   populate_apertium_list()

   print "Initialized."

def closedb():
   global languagedb, initialzed

   initialized['db'] = False
   db.closedb()
   languagedb = None

def opendb():
   global languagedb, initialized

   languagedb = db.opendb()
   initialized['db'] = True

def packdb():
   db.packdb()

print "Initializing..."

thread = threading.Thread(target=startup)
thread.daemon = True
thread.start()


last_line = {}

def memory(source, line=None):
   global last_line

   if source.lower() in last_line:
      previous = last_line[source.lower()]
   else:
      previous = "I have no memories..."

   if line:
      last_line[source.lower()] = line

   return previous


def args(channel, input, count=2, standard='linguistlist', mixed=False, expandurls=False):

   source = []
   dest = []

   if count > 0:
      words = input.split(' ')
      leftovers = []
      while words:
         if not words[0]: pass
         elif u'→' in words[0]:
            s, _, d = words[0].partition(u'→')
            source.append(langcode(s, standard=standard, passthru=True))
            dest.append(langcode(d, standard=standard, passthru=True))
         elif words[0].startswith("<"): source.append(words[0][1:])
         elif words[0].startswith(">"): dest.append(words[0][1:])
         elif words[0].startswith(":") or words[0].startswith("-"):
            if source: dest.append(langcode(words[0][1:], standard=standard, passthru=True))
            else: source.append(langcode(words[0][1:], standard=standard, passthru=True))
         elif not mixed: break
         else: leftovers.append(words[0])

         words.pop(0)

      text = u' '.join(words + leftovers)

      if text == '^':
         text = memory(channel)

      if text.startswith("http://"):
         format = 'html'  
         url = text.strip().split(" ")[0]
         try:
            text = web.get(url).decode('utf-8')
         except:
            pass

   source = [e if e.startswith('"') else langcode(e, standard=standard, passthru=True) for e in source]
   dest = [e if e.startswith('"') else langcode(e, standard=standard, passthru=True) for e in dest]

   
   if count == 0:
      return input
   elif count == 1:
      return text, source[0] if source else dest[0] if dest else None
   elif count == 2:
      return text, (source[0] if source else None, dest[0] if dest else None)
   elif count > 2:
      return text, (source, dest)
   else:
      raise Exception("Bad count")


def getrecord(word, language='eng'):
   if not initialized['db']: raise IOError("Database is currently closed, try later")

   spellings = {}
   if word in languagedb[language]['dict']:
      entry=languagedb[language]['dict'][word]
      if 'spellings' not in entry:
         print "Word '%s' has no spellings listed!!!" % word
         print entry
         return entry
      for source in entry['spellings']:
         spelling=entry['spellings'][source]
         spellings.setdefault(source, spelling)
         if spelling in languagedb[language]['dict']:
            newentry = languagedb[language]['dict'][spelling]
            newentry.update(entry)
            entry = newentry
      return entry
   else:
      return None


def langinfo(language, info):
   if not initialized['db']: raise IOError("Database is currently closed, try later")

   code = langcode(language)
   if code in languagedb:
      if info in languagedb[code]:
         return languagedb[code][info]

   return None


def langtree(language):
   if not initialized['db']: raise IOError("Database is currently closed, try later")

   code = langcode(language)
   tree = [code]

   while 'parent' in languagedb[code]:
      parent = languagedb[code]['parent']
      if parent in tree:
         tree.append(parent)
         break
      else:
         tree.append(parent)
      code = parent
      print code

   return reversed(tree)


def langchildren(language):
   if not initialized['db']: raise IOError("Database is currently closed, try later")

   code = langcode(language)

   children=set()

   for lang in languagedb:
      if 'parent' in languagedb[lang] and languagedb[lang]['parent']==code:
         children.add(lang)

   return children


def listlangs(family=None):
   if not initialized['db']: raise IOError("Database is currently closed, try later")

   print "Listing languages in family", family
   if family is None: return None
   result=[]

   for lang in languagedb:
      add = True
      if family:
         if 'tree' not in languagedb[lang] or family.lower() not in [node.lower() for node in languagedb[lang]['tree']]:
            add = False

      if add: result.append(lang)

   print "Finished listing languages in family", family

   return result

def langsearch(input, standard='linguistlist', search_substrings=True, extensive=False):
   global language_cache, initialized

   term = input.lower().strip()
   result = []

   subterms = re.split(r"[ ,]", term)

   if not initialized['cache']: raise IOError("Language database not yet loaded, try again later")

   for substring in [False, True] if search_substrings else [False]:
      if not substring:
         if term in language_cache:
            result.append(language_cache[term][standard])
            if not extensive: return result
      else:
         for name in language_cache:
            names = [n.lower() for n in language_cache[name]['names']]
            if not substring:
               if term in names: result.append(language_cache[name][standard])
            else:
               for secondary_name in names:
                  found = True
                  for subterm in subterms:
                     if subterm not in secondary_name:
                        found = False
                  if found:
                     result.append(language_cache[name][standard])
                     break

   return result


def langcode(input, standard='linguistlist', passthru=False):
   global language_cache, initialized

   if standard!='linguistlist' and standard!='wals' and standard!='name' and standard!='names' and standard!='iso639-2' and standard!='iso639-3':
      raise NotImplementedError("No such standard '%s'" % standard)

   if not input: raise Exception("No language code input given")

   if input.startswith('"') and input.endswith('"'): return input.strip('"')

   if not initialized['db']: return input

   if input in languagedb:
      name = languagedb[input]['names'][0]
      byname = False
      if initialized['cache'] and name.lower() in language_cache:
         return language_cache[name.lower()][standard]

      if standard == 'name': return name
      if standard == 'iso639-3' and len(input)==3: return input
      if standard == 'wals' and input.startswith('wals-'): return languagedb[input].get('code_wals')
      if standard == 'linguistlist' and len(input)>=3: return input
      if standard == 'iso639-2' and len(input)==2: return input
   else:
      name = input
      byname = True

   name = name.lower()

   print "Searching for language '%s' ('%s') for standard %s" % (name, input, standard)

   hits = langsearch(name, standard, search_substrings=byname)

   if len(hits) > 1:
      print "More than one hit found:", hits

   if len(hits) < 1:
      print "No language '%s' found." % name
      return input.strip('"') if passthru else None

   return hits[0]


def build_language_cache():
   global language_cache, languagedb, initialized

   t = time.time()
   conflicts = 0

   language_cache = defaultdict(lambda: defaultdict(lambda: None))

   for code in languagedb:
      original_name = languagedb[code]['names'][0]
      name = original_name.lower()

      entry = defaultdict(lambda: None)
      entry['names'] = languagedb[code]['names']
      entry['name'] = original_name
      entry['parent'] = languagedb[code].get('parent')
      entry['type'] = languagedb[code].get('type')

      if len(code) == 2: entry['iso639-2'] = code
      if len(code) == 3 and code.isalpha(): entry['iso639-3'] = code
      if len(code) >= 3: entry['linguistlist'] = code
      if 'code_wals' in languagedb[code]: entry['wals'] = languagedb[code]['code_wals']

      new_name = other_name = None

      for attribute in entry:
         if language_cache[name].get(attribute, entry[attribute]) != entry[attribute]:
            if entry['type'] == 'group' and language_cache[name]['type'] != 'group':
               new_name = original_name + (" group of %s" % languagedb[entry.get('parent')]['names'][0] if entry.get('parent') else " group")
            elif language_cache[name]['type'] == 'group' and entry['type'] != 'group':
               other_name = original_name + (" group of %s" % languagedb[language_cache[name].get('parent')]['names'][0] if language_cache[name].get('parent') else " group")
            elif language_cache[name]['type'] == 'group' and entry['type'] == 'group' and entry.get('parent') != language_cache[name].get('parent'):
               if language_cache[name].get('parent'):
                  other_name = original_name + " group of %s" % languagedb[language_cache[name]['parent']]['names'][0]
               if entry.get('parent'):
                  new_name = original_name + " group of %s" % languagedb[entry['parent']]['names'][0]
            elif entry['type'] == 'dialect' and language_cache[name]['type'] != 'dialect':
               new_name = original_name + " dialect"
            elif entry['type'] != 'dialect' and language_cache[name]['type'] == 'dialect':
               other_name = original_name + " dialect"
            elif entry['type'] == 'dialect' and language_cache[name]['type'] == 'dialect' and entry.get('parent') != language_cache[name].get('parent'):
               if language_cache[name].get('parent'):
                  other_name = original_name + " dialect of %s" % languagedb[language_cache[name]['parent']]['names'][0]
               if entry.get('parent'):
                  new_name = original_name + " dialect of %s" % languagedb[entry['parent']]['names'][0]
            elif entry['parent'] and not language_cache[name]['parent']:
               pass
            elif not entry['parent'] and language_cache[name]['parent']:
               entry['parent'] = language_cache[name]['parent']
            elif entry['type'] and not language_cache[name]['type']:
               pass
            elif not entry['type'] and language_cache[name]['type']:
               entry['type'] = language_cache[name]['type']
            else:
               print "!!! Conflict between %s codes for %s: " % (attribute, name), entry[attribute], "vs", language_cache[name][attribute]
               new_name = original_name + " (alternate)"
               conflicts += 1

         if new_name or other_name: break

      if other_name:
         other_entry = language_cache[name]
         other_entry['name'] = other_name
         if other_name not in other_entry['names']: other_entry['names'].append(other_name)
         language_cache[other_name.lower()] = other_entry
         del language_cache[name]
         #print "Renaming old %s entry to %s" % (original_name, other_name)

      if new_name: 
         entry['name'] = new_name   
         if new_name not in entry['names']: entry['names'].append(name)
         language_cache[new_name.lower()] = entry
         #print "Renaming new %s entry to %s" % (original_name, new_name)
      else:
         language_cache[name].update(entry)

   initialized['cache'] = True

   print "Done building language cache, took %f seconds, %d conflicts" % (time.time()-t, conflicts)


def addlanguage(code, names, type='language', parent=None):
   global languagedb, languagedb_lock

   if code in languagedb:
      raise Exception("Language already exists")

   if len(code)>7:
      raise Exception("Invalid code length")

   with languagedb_lock:
      languagedb[code]=OOBTree()
      languagedb[code]['names']=names
      languagedb[code]['type']=type
      languagedb[code]['parent']=parent
      db.transaction.commit()


def langfeatures(langs=None, features=None):
#   if type(features)==str:
#      feature_list = findfeatures(features)
#   elif type(features)==list:
#      feature_list = [findfeatures(f) for f, v in features]
#      if [] in feature_list: raise Exception("Missing value")
#      feature_list = [item for sublist in feature_list for item in sublist]
#   else:
#      feature_list = [(key, None) for key in languages.features.keys()]

   feature_list = features

   if type(langs)==str:
      language_list={langcode(langs, 'wals'): langs}
   elif type(langs)==list:
      language_list={langcode(lang, 'wals'): lang for lang in langs}
   else:
      language_list = {languagedb[lang]['code_wals']: lang for lang in languagedb if 'code_wals' in languagedb[lang]}

   result = dict()

   print "Requested features:", feature_list

   for language in language_list:
      if language not in languages.feature_matrix:
         continue

      temp=dict()

      for feature, value in feature_list:
         if feature.upper() not in languages.features:
            raise NotImplementedError("Unknown feature '%s'" % feature)

         if feature in languages.feature_matrix[language]:
            if languages.feature_matrix[language][feature]==value:
               temp[namefeature(feature)]=namevalue(feature, languages.feature_matrix[language][feature], long=True)

      if len(temp)>=len(feature_list): result[language_list[language]]=temp

   return result


def namefeature(feature):
   if feature not in languages.features:
      raise Exception("Unknown feature '%s'" % feature)

   return languages.features[feature]['name']


def namevalue(feature, value, long=False):
   if feature not in languages.features:
      raise Exception("Unknown feature '%s'" % feature)

   if value is None:
      return [languages.features[feature][k][1 if long else 0] for k in languages.features[feature] if k!='name']

   if value not in languages.features[feature]:
      raise Exception("Unknown feature value '%s'" % value)

   return languages.features[feature][value][1 if long else 0]


def findfeatures(string):
   result = []
   parts = string.lower().split(":")
   if len(parts)>1:
      requested_feature = parts[0].strip().lower()
      requested_value = parts[1].strip().lower()
   else:
      requested_feature = requested_value = parts[0].strip().lower()

   found = False
   for id, feature in languages.features.iteritems():
      if requested_feature in feature['name'].lower().strip():
         if requested_feature==feature['name'].lower().strip():
            if requested_feature == requested_value: return [(id, None)]
            else: found = True
         else:
            if requested_feature == requested_value: result.append((id, None))
            else: found = True

      for number, value in feature.iteritems():
         if number == 'name': continue
         if found or requested_feature == requested_value:
            if requested_value in value[0].lower() or requested_value in value[1].lower():
               if requested_value==value[0].lower() or requested_value==value[1].lower():
                  return [(id, number)]
               else:
                  result.append((id, number))

      if found: break


   return result


def wordcategories(word, lang='eng'):
   entry = getrecord(word, lang)
   if not entry: return None
   categories=set()
   if 'mwords_file' in entry: categories |= entry['mwords_file']
#   if 'scowl_file' in entry: categories |= entry['scowl_file']
   return categories


def wordspellings(word, lang='eng'):
   entry = getrecord(word, lang)
   if not entry: return None
   if 'spellings' not in entry: return None
   spellings={}
   for note, spelling in entry['spellings'].items():
      source, info = (note.split(" ", 1) + [None])[:2]
      if source == 'varcon_A' or source == 'varcon_A.': source = 'American'
      elif source == 'varcon_B' or source == 'varcon_B.': source = 'British'
      elif source == 'varcon_C' or source == 'varcon_C.': source = 'Canadian'
      elif source == 'varcon_Z' or source == 'varcon_Z.': source = 'British OED'
      elif source == 'varcon_Av': source = 'American variant'
      elif source == 'varcon_Bv' or source == 'varcon_Zv': source = 'British variant'
      elif source == 'varcon_Cv': source = 'Canadian variant'
      elif source == 'varcon_AV': source = 'uncommon American variant'
      elif source == 'varcon_BV' or source == 'varcon_ZV': source = 'uncommon British variant'
      elif source == 'varcon_CV': source = 'uncommon Canadian variant'
      elif source == 'varcon_A-': source = 'rare American variant'
      elif source == 'varcon_B-' or source == 'varcon_Z-': source = 'rare British variant'
      elif source == 'varcon_C-': source = 'rare Canadian variant'
      elif source == 'varcon__' or source == 'varcon__.': source = 'other'
      elif source == 'varcon__v': source = 'variant'
      elif source == 'varcon__V': source = 'uncommon variant'
      elif source == 'varcon__-': source = 'rare variant'
      elif source == 'scowl': source = 'SCOWL'
      elif source == 'mwords': source = 'Moby Words'

      spellings.setdefault(spelling, set())
      spellings[spelling].add(source)

   return spellings


def wordpos(word, lang='eng'):
   entry = getrecord(word, lang)
   if not entry: return None
   pos = set()
   if 'mpron' in entry: pos |= {p for p in entry['mpron'] if p is not None}
   if 'mpos' in entry: pos |= entry['mpos']
   return pos

def filterbypos(words, pos, lang='eng'):
   return [word for word in words if pos.lower() in wordpos(word, lang)]


def thesaurus(word, lang='eng'):
   entry = getrecord(word, lang)
   if not entry or 'mthes' not in entry: return None
   terms = entry['mthes']
   return sortedbyfrequency(terms, lang)


def sortedbyfrequency(words, lang='eng'):
   decorated = []
   for word in words:
      entry = getrecord(word, lang)
      if not entry or 'scowl_file' not in entry:
         decorated.append((100, word))
      else:
         frequencies = [int(file.split(".", 1)[1])*(0.5 if file.startswith("english-words") else 1) for file in entry['scowl_file']]
         decorated.append((min(frequencies), word))
   undecorated = [word for decorator, word in sorted(decorated)]
   return undecorated


def syllabify(word, lang='eng'):
   if languagedb is None: raise IOError("Language database is not open")
   if lang in languagedb and 'dict' in languagedb[lang] and word.lower() in languagedb[lang]['dict'] and 'mhyph' in languagedb[lang]['dict'][word.lower()]:
      return languagedb[lang]['dict'][word.lower()]['mhyph']
   else:
      return [word]


def hyphenate(word, lang='eng'):
   try:
      return u"\u2027".join(syllabify(word, lang))
   except IOError:
      return word


def lemma(word, lang='eng'):
   print "TYPE", type(word)
   try:
      return u"\x02" + u"\x02\u2027\x02".join(syllabify(word, lang)) + u"\x02"
   except IOError:
      return u"\x02" + word + u"\x02"

def IPA2Features(ipa_text):
   converter = ipa.convert.NormalisedFormConverter()
   try:
      arrays = [list(array) for array in converter.ipa_to_script(ipa_text).split('Y') if array]
      return [{('+' if v=='1' else '-') + converter.features[i] for i, v in enumerate(array)} for array in arrays]
   except ipa.convert.InvalidCharError, e:
      raise NotImplementedError(e)

def Features2IPA(features):
   converter = ipa.convert.NormalisedFormConverter()
   array = converter.base_feature_set
   for i, feature in enumerate(converter.features):
      if feature in features or '+'+feature in features:
         array[i+1]='1'
      elif '-'+feature in features:
         array[i+1]='0'

   return converter.script_to_ipa(''.join(array))      


def SAMPA2IPA(sampa_text):
   converter = ipa.convert.XSAMPAConverter()
   try:
      return "[" + converter.script_to_ipa(sampa_text) + "]"
   except ipa.convert.InvalidCharError, e:
      raise NotImplementedError(e)


def IPA2SAMPA(ipa_text):
   converter = ipa.convert.XSAMPAConverter()
   try:
      return converter.ipa_to_script(ipa_text.replace("[", "").replace("]", "").replace("/", ""))
   except ipa.convert.InvalidCharError, e:
      raise NotImplementedError(e)


def describe_feature(feature):
   feature = feature.lower()
   description = set()
   subfeatures = set()
   name = feature
   if feature.startswith('-'):
      plusorminus = ['minus', 'plus']
      name = feature[1:]
   else:
      if feature.startswith('+'): name = feature[1:]
      plusorminus = ['plus', 'minus']
   for candidate, record in ipakey.ipa_features.items():
      if name in record['plus']:
         description.add(record['description'])
         subfeatures.add(candidate)
      elif name in record['minus']:
         description.add(record['description'] + " %s is the opposite of %s." % (name.capitalize(), record['plus'][0 if record['plus'][0] else 1]))
         subfeatures.add(candidate)
      else:
         for n, v in record.items():
            if type(v) == tuple:
               if name in v:
                  description.add(record['description'])
                  subfeatures.add(candidate)
                  description.add(ipakey.ipa_features[n]['description'])
                  subfeatures.add(n)

   if not description:
      return "unknown feature"
   else:
      output = ' '.join(description)
      if len(subfeatures) > 1: output += " %s sounds are %s." % (feature.capitalize(), ', '.join(subfeatures))
      else: output += " " + ipakey.ipa_features[list(subfeatures)[0]]['url']
      return output


def pretty_features(features, negatives=False):
   features=[feature.lower() for feature in features]
   print "FEATURES", features
   description = set()
   for feature, data in ipakey.ipa_features.items():
      descriptor = None
      if feature in features or feature in [f[1:] for f in features if f.startswith('+')]:
         for combiner in data.keys():
            if combiner in features or combiner in [f[1:] for f in features if f.startswith('+')]:
               print "FOUND COMBINER", combiner, "FOR", feature
               descriptor = (min(data['position'], ipakey.ipa_features[combiner]['position']), data[combiner][0])
               break
         if not descriptor and data['plus'][0]:
            descriptor = (data['position'], data['plus'][0])
      elif feature in [f[1:] for f in features if f.startswith('-')]:
         if data['minus'][0]:
            descriptor = (data['position'], data['minus'][0])
         elif negatives:
            if len(data['minus'])>1: descriptor = (data['position'], data['minus'][1])
            else: descriptor = (10000, "non-" + data['plus'][0 if data['plus'][0] else 1])
      if descriptor: description.add(descriptor)
   description = [word for decorator, word in reversed(sorted(description))]
   return ' '.join(description)



def IPA2Key(ipa_text, language='en'):
   result = []
   if '[' in ipa_text:
      result.append(ipakey.ipa_key['narrow'][language])
   elif '/' in ipa_text:
      result.append(ipakey.ipa_key['broad'][language])
   pruned = ipa_text
   pruned = pruned.replace(u'\u0361', '')
   pruned = pruned.replace('/', '')
   pruned = pruned.replace('[', '')
   pruned = pruned.replace(']', '')
   while len(pruned)>0:
      for i in reversed(range(1, 4)):
         done = False
         for best_language in ipakey.ipa_key_best_languages[language]:
            if pruned[:i] in ipakey.ipa_key and best_language in ipakey.ipa_key[pruned[:i]]:
                  key = ipakey.ipa_key[pruned[:i]][best_language]
                  key = key.replace("[", "\x02")
                  key = key.replace("]", "\x02")
                  key = key.replace("(", "\x1d(")
                  key = key.replace(")", ")\x1d")
                  result.append(key + (" \x1d(%s)\x1d" % best_language if best_language != language else ""))
                  pruned = pruned[i:]
                  done = True
                  break
         if i == 1 and not done:
            result.append(pruned[:1])
            pruned = pruned[1:]
   return result


def pronunciation(word, language='en'):
   pronunciations = []
   if language == 'en':
      try:
         result = ode(word)
         if result is not None: pronunciations.append((result.strip(), "ODE, British"))
      except IOError: pass
      try:
         result = cmu(word)
         if result is not None: pronunciations.append((result.strip(), "CMU, American"))
      except IOError: pass
      try:
         result = mpron(word)
         if result is not None: pronunciations.append((result.strip(), "Moby, American"))
      except IOError: pass
      result = espeak(word, 'en-uk')
      if result is not None: pronunciations.append((result.strip(), "eSpeak, British"))
      result = espeak(word, 'en-us')
      if result is not None: pronunciations.append((result.strip(), "eSpeak, American"))
   else:
      result = espeak(word, language)
      if result is not None: pronunciations.append((result.strip(), "eSpeak, " + language))
   if pronunciations:
      return pronunciations
   else:
      raise NotImplementedError("No pronunciation for word '" + word + "' in language '" + language +"'")
   

def ode(word):
   result = web.get(ode_url % (word.encode('utf-8'), word.encode('utf-8')))
   result = ode_re.search(result)
   print result
   if result and result.group(1):
      return result.group(1).decode('utf-8').strip()
   else:
      return None


def cmu(word):
   entry = getrecord(word, 'eng')
   if not entry or not 'cmu' in entry: return None
   result = languagedb['eng']['dict'][word]['cmu']
   return u' or '.join(("/" + Arpa2IPA(u''.join(p)) + "/" for p in result)).strip()


def mpron(word):
   entry = getrecord(word, 'eng')
   if not entry or not 'mpron' in entry: return None
   result = entry['mpron']
   result = ["/" + Moby2IPA(result[pos]) + "/" + (" as %s" % pos if pos else "") for pos in sorted(result.keys())]
   return u' or '.join(result).strip()


espeak_lock = threading.Lock()

def espeak(word, language):
   global espeak_lock
   try:
      with espeak_lock:
         return "[" + re.sub("^ ", "", (subprocess.check_output(["espeak", "-v", language, "-q", "-x", "--ipa=1", word])).decode('utf-8', errors='ignore')) + "]"
   except subprocess.CalledProcessError:
      raise NotImplementedError("Language '" + language + "' unavailable")


def Moby2IPA(moby):
   moby = moby.replace(u'/', u'')
   moby = moby.replace(u'_', u' ')
   moby = moby.replace(u"'", u'ˈ')
   moby = moby.replace(u",", u'ˌ')

   moby = moby.replace(u'(@)', u'ɛ')
   moby = moby.replace(u'[@]r', u'ɝ')
   moby = moby.replace(u'ir', u'ɪɹ')
   moby = moby.replace(u'oUr', u'ɔɹ')
   moby = moby.replace(u'Ar', u'ɑr')
   moby = moby.replace(u'oU', u'oʊ')
   moby = moby.replace(u'Oi', u'ɔɪ')
   moby = moby.replace(u'aI', u'aɪ')
   moby = moby.replace(u'aU', u'aʊ')
   moby = moby.replace(u'eI', u'eɪ')
   moby = moby.replace(u'&', u'æ')
   moby = moby.replace(u'-', u'(ə)')
   moby = moby.replace(u'@r', u'ɚ')
   moby = moby.replace(u'@', u'ə')
   moby = moby.replace(u'A', u'ɑː')
   moby = moby.replace(u'D', u'ð')
   moby = moby.replace(u'dZ', u'd͡ʒ')
   moby = moby.replace(u'E', u'ɛ')
   moby = moby.replace(u'i', u'iː')
   moby = moby.replace(u'I', u'ɪ')
   moby = moby.replace(u'N', u'ŋ')
   moby = moby.replace(u'g', u'ɡ')
   moby = moby.replace(u'O', u'ɔː')
   moby = moby.replace(u'S', u'ʃ')
   moby = moby.replace(u'T', u'θ')
   moby = moby.replace(u'tS', u't͡ʃ')
   moby = moby.replace(u'u', u'uː')
   moby = moby.replace(u'U', u'ʊ')
   moby = moby.replace(u'Z', u'ʒ')
   moby = moby.replace(u'Y', u'y')
   moby = moby.replace(u'R', u'ɻ')
   moby = moby.replace(u'r', u'ɹ')

   return moby

def Arpa2IPA(arpa):
   arpa = arpa.lower()

   arpa=re.sub(r'(..)1', u'ˈ\\1', arpa);
   arpa=re.sub(r'(..)2', u'ˌ\\1', arpa);

   arpa = arpa.replace('ah0', u'ə')
   arpa = arpa.replace('ah', u'ʌ')
   arpa = arpa.replace('aa', u'ɑ')
   arpa = arpa.replace('aw', u'aʊ')
   arpa = arpa.replace('eh', u'ɛ')
   arpa = arpa.replace('ey', u'eɪ') 
   arpa = arpa.replace('ih', u'ɪ')
   arpa = arpa.replace('ow', u'oʊ')
   arpa = arpa.replace('uh', u'ʊ')
   arpa = arpa.replace('ae', u'æ')
   arpa = arpa.replace('ao', u'ɔ') 
   arpa = arpa.replace('ay', u'aɪ')
   arpa = arpa.replace('er0', u'ɚ')
   arpa = arpa.replace('er', u'ɝ')
   arpa = arpa.replace('iy0', u'i')
   arpa = arpa.replace('iy', u'iː')
   arpa = arpa.replace('oy', u'ɔɪ')
   arpa = arpa.replace('uw0', u'uː') 
   arpa = arpa.replace('uw', u'uː')
   arpa = arpa.replace('th', u'θ')
   arpa = arpa.replace('dh', u'ð')
   arpa = arpa.replace('ch', u't͡ʃ')
   arpa = arpa.replace('jh', u'd͡ʒ') 
   arpa = arpa.replace('sh', u'ʃ')
   arpa = arpa.replace('zh', u'ʒ')
   arpa = arpa.replace('y', u'j')
   arpa = arpa.replace('hh', u'h')
   arpa = arpa.replace('ng', u'ŋ') 
   arpa = arpa.replace('0', u'')

   return arpa


def wordnet(word, option, sense=0, tag=False, synonyms=True, glosses=False):
   output = wn(word, option, sense, tag, glosses)
   output = str.join('\n', (output.split("\n")[3:]))
   if not synonyms:
      output = str.join('\n', re.findall(r'^.*=>.*$', output, re.MULTILINE))
   output = str.join('\n', re.findall(r'^(?!Sense [0-9]).*$', output, re.MULTILINE))
   if glosses:
      glosses = re.findall(r'-- \((.+)\)$', output, re.MULTILINE)
      return glosses
   else:
      words = re.findall(r'([a-zA-z][a-zA-z0-9# -]*)[,\n]', output, re.MULTILINE)
      if re.search(r'senses of', words[0]): del words[0]
      return words


wn_lock = threading.Lock()

def wn(word, option, sense=0, tag=False, glosses=False):
   global wn_lock
   command=["wordnet", word, "-" + option, "-n" + str(sense)]
   if tag:
      command.append("-s")
   if glosses:
      command.append("-g")
   print command

   with wn_lock:
      p = subprocess.Popen(command, stdout=subprocess.PIPE)
      return p.communicate()[0]



def getwotd(lang='eng'):
   if lang not in languagedb or 'wotd' not in languagedb[lang]:
      raise NotImplementedError("WOTD not available for %s" % lang)

   return random.choice(languagedb[lang]['wotd'].keys())


def addwotd(word, lang='eng'):
   global languagedb, languagedb_lock

   with languagedb_lock:
      if lang not in languagedb: languagedb[lang]=OOBTree()
      if 'wotd' not in languagedb[lang]: languagedb[lang]['wotd']=OOBTree()
      if word not in languagedb[lang]['wotd']:
         print "Adding '%s' to WOTD list for %s" % (word, lang)
         languagedb[lang]['wotd'][word] = None
         db.transaction.commit()


apertium_lock = threading.Lock()

def apertium(input, mode, directory=None, format='txt', timeout=8):
   global apertium_lock, initialized

   if not initialized['apertium']: raise IOError("Apertium modes list not yet ready, try later")
   if mode.lower() not in apertium_modes: raise NotImplementedError("Apertium has no mode '%s'" % mode)

   print "Translating in mode %s with apertium" % mode
   if format != 'txt': timeout += 15

   with apertium_lock:
      if directory:
         if not os.path.exists(os.path.join(directory, "modes", mode+".mode")):
            raise NotImplementedError("Mode '%s' does not exist in %s" % (mode, directory))
         p = subprocess.Popen(["timeout", "%ds" % timeout, "apertium", "-f", format, "-d", directory, mode], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
      else:
         p = subprocess.Popen(["timeout", "%ds" % timeout, "apertium", "-f", format, mode], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

   output = p.communicate(input.encode('utf-8')+"\n")[0].decode('utf-8').strip()
   if p.returncode == 0: return output
   elif p.returncode == 124: raise IOError("Apertium timed out")
   elif p.returncode == 1: raise NotImplementedError("Mode '%s' does not exist in %s" % (mode, directory))
   else: raise RuntimeError("Apertium couldn't translate in mode '%s'" % mode)


def apertium_mode(lang1, lang2=None):
   standards = ['iso639-3', 'iso639-2']
   success = False

   if not lang2:
      if lang1 in apertium_list(r"^%s$" % re.escape(mode)):
         return (lang1, True)

   for standard in standards:
      mode = "%s-%s" % (langcode(lang1, standard), langcode(lang2, standard))
      if mode in apertium_list(r"^%s$" % re.escape(mode)):
         success = True
         break
   else:
      for standard in standards:
         if mode not in apertium_list(mode) and langcode(lang1, standard):
            modes = apertium_list(r"^%s-" % re.escape(langcode(lang1, standard)))
            if modes: mode = modes[0]

   return (mode, success)


apertium_modes = None

def populate_apertium_list():
   global apertium_modes, initialized

   apertium_modes = [line.strip() for line in subprocess.check_output(["apertium", "-l"]).split("\n")]

   initialized['apertium'] = True

   print "Done building Apertium modes list."


def apertium_list(substring=None):
   global apertium_modes

   if not initialized['apertium'] or not apertium_modes: raise IOError("Apertium mode list not ready, try again later")

   if substring:
      return sorted([mode for mode in apertium_modes if not substring or re.search(substring, mode)])
   else:
      return apertium_modes


def googletranslate(text, lang1=None, lang2=None, romanize=False, dictionary=False):
   import urllib2, json

   print "Google translation from %s to %s requested." % (lang1, lang2)

   opener = urllib2.build_opener()
   opener.addheaders = [(
      'User-Agent', 'Mozilla/5.0' + 
      '(X11; U; Linux i686)' + 
      'Gecko/20071127 Firefox/2.0.0.11'
   )]

   if lang1:
      code1 = langcode(lang1, 'iso639-2')
      if not code1: code1 = langcode(lang1, 'iso639-3')
   else: code1 = 'auto'
   if lang2:
      code2 = langcode(lang2, 'iso639-2')
      if not code2: code2 = langcode(lang2, 'iso639-3')
   else: code2 = 'en'

   lang1, lang2 = code1, code2

   if not lang1 or not lang2: raise NotImplementedError("Only languages with an ISO639-3 code are accepted")

   print "GOOGLE", lang1, lang2

   quoted_lang1, quoted_lang2 = (urllib.quote(lang1) if lang1 else 'auto', urllib.quote(lang2) if lang2 else 'en')
   quoted_text = urllib.quote(text.encode('utf-8'))

   result = opener.open('http://translate.google.com/translate_a/t?' +
      ('client=t&hl=en&sl=%s&tl=%s&multires=1' % (quoted_lang1, quoted_lang2)) + 
      ('&otf=1&ssel=0&tsel=0&uptl=%s&sc=1&text=%s' % (quoted_lang2, quoted_text))).read()

   while ',,' in result: 
      result = result.replace(',,', ',null,')
   while '[,' in result:
      result = result.replace('[,', '[null,')
   while ',]' in result:
      result = result.replace(',]', ',null]')
   data = json.loads(result)

   try: detected_language = data[2]
   except: detected_language = None

   try: suggestion = data[7][1]
   except: suggestion = None

   if not dictionary:
      output = u''.join(x[3 if romanize else 0] for x in data[0])
      if romanize and not output: raise NotImplementedError("Google doesn't appear to transliterate %s-%s" % (lang1, lang2))
   else:
      pass

   print "Google Translate output:", data

   if data[3]: raise NotImplementedError(data[3])
   if text == output and (len(code1) > 2 or len(code2) > 2): raise NotImplementedError("Google doesn't appear to know about the language pair %s-%s" % (lang1, lang2))

   return output, detected_language, suggestion


def uconv(text, transliterator):
   try:
      print "Trying to uconv with mode %s" % transliterator
      p = subprocess.Popen(["uconv", "-x", transliterator], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
      output, error = p.communicate(text.encode('utf-8'))
      print "uconv returned %s" % output
      if p.returncode != 0: raise NotImplementedError("Transliterator '%s' unavailable" % transliterator)
      return output.decode('utf-8')
   except subprocess.CalledProcessError:
      raise NotImplementedError("UConv is not available")


def translate(text, lang1, lang2, engines=['UConv', 'Google', 'Apertium', 'suggestion', 'games'], transliterate=False):
   suggested_language = None
   suggested_text = None
   outputs = []

   for engine in engines:
      output = None

      if transliterate:
         if engine == 'Google':
            try:
               output = text
               if lang1 not in ['eng']: output, _, suggested_text = googletranslate(output, lang1, 'eng', romanize=True)
               if lang2 not in ['eng']: _, _, output = googletranslate(output, lang2, 'eng', romanize=False)
            except (NotImplementedError, IOError):
               print "Google can't transliterate from %s to %s" % (lang1, lang2)
         elif engine == 'UConv':
            code1, code2 = langcode(lang1, 'iso639-2', passthru=True), langcode(lang2, 'iso639-2', passthru=True)
            for template in ["%s-%s", "%s-any; any-%s", "%s-Latin; Latin-%s"]:
               try:
                  output = uconv(text, template % (code1, code2))
                  break
               except NotImplementedError:
                  continue
            if not output: "uconv cannot transliterate from %s to %s" % (lang1, lang2)

      else:
         if engine == 'Google':
            try:
               output, detected_language, suggested_text = googletranslate(text, lang1, lang2)
               if langcode(detected_language) != lang1:
                  suggested_language = detected_language
                  print "!!! Google thinks it's %s, but we think it's %s" % (suggested_language, lang1)
            except (NotImplementedError, IOError):
               print "Google can't translate from %s to %s" % (lang1, lang2)
         elif engine == 'Apertium':
            try:
               mode, exists = apertium_mode(lang1, lang2)
               if exists: output = apertium(text, mode, timeout=8)
            except (NotImplementedError, IOError):
               print "Apertium can't translate from %s to %s" % (lang1, lang2)
         elif engine == 'games' and lang2 and lang2.strip('" ') in [
             'b1ff', 'censor', 'chef', 'cockney', 'eleet', 'espdiff', 'fanboy', 'fudd', 'jethro', 'jibberish',
            'jive', 'ken', 'kenny', 'kraut', 'ky00te', 'nethackify', 'newspeak', 'nyc', 'pirate', 'rasterman',
            'scottish', 'scramble', 'spammer', 'studly', 'uniencode', 'upside-down', 'rot13'
         ]:
            p = subprocess.Popen([lang2.strip('" ')], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            output = p.communicate(text.encode('utf-8')+"\n")[0].decode('utf-8').strip().replace("\n", " ")

      if engine == 'suggestion':
         print "Suggested text is %s" % suggested_text
         output = suggested_text

      if output:
         outputs.append((engine, output))
         print "Obtained translation from %s:" % engine, output

   return outputs


def phonological_rule(language, name, date, rules, add=False):
   global languagedb, languagedb_lock

   lang = langcode(language)

   if not lang:
      raise NotImplementedError("Unknown language %s" % language)

   print "RULES: ", rules

   try:
      if rules:
         expanded_rules = []
         for rule in rules:
            rule = rule.replace("C", "+consonantal")
            rule = rule.replace("V", "+syllabic")
            input, output, contexts = rule.split("/")
            input = input.strip()
            output = output.strip()
            contexts = contexts.split(",")
            for context in contexts:
               context = context.strip()
               expanded_rules.append("%s/%s/%s" % (input, output, context))
         rules = expanded_rules
         for rule in rules:
            print "Evaluating rule %s..." % rule
            ipa.Rule(rule)
   except zounds.InvalidRuleError, e:
      raise PhonologyRuleError(e)

   with languagedb_lock:
      if lang not in languagedb: languagedb[lang]=OOBTree()
      if 'phon' not in languagedb[lang]: languagedb[lang]['phon']=OOBTree()
      if 'rules' not in languagedb[lang]['phon']: languagedb[lang]['phon']['rules']=OOBTree()
 
      formatted_name = name.strip().replace(" ", "_").replace("'", "").lower()

      if formatted_name not in languagedb[lang]['phon']['rules']: languagedb[lang]['phon']['rules'][formatted_name]=OOBTree()

      if date:
         if date == 'remove':
            languagedb[lang]['phon']['rules'][formatted_name]['date']=None
         elif date == 'persist':
            languagedb[lang]['phon']['rules'][formatted_name]['date']='persist'
         else:
            if 'max_date' in languagedb[lang]['phon'] and date > languagedb[lang]['phon']['max_date']:
               raise PhonologyDateError("Date %d is too late for %s (maximum %d)" % (date, lang, languagedb[lang]['phon']['max_date']))
            if 'min_date' in languagedb[lang]['phon'] and date < languagedb[lang]['phon']['min_date']:
               raise PhonologyDateError("Date %d is too early for %s (maximum %d)" % (date, lang, languagedb[lang]['phon']['min_date']))
            languagedb[lang]['phon']['rules'][formatted_name]['date']=date

      if rules:
         languagedb[lang]['phon']['rules'][formatted_name].setdefault('list', PersistentList())
         if add: languagedb[lang]['phon']['rules'][formatted_name]['list']+=rules
         else: languagedb[lang]['phon']['rules'][formatted_name]['list']=PersistentList(rules)

      db.transaction.commit()


def produce_rules(language):
   global languagedb

   lang = langcode(language)
   if not lang: raise NotImplementedError("No such language %s" % language)

   config = "Section Groups\n"

   for name in languagedb[lang]['phon']['rules']:
      config += "   Group %s\n" % (name)
      if 'list' not in languagedb[lang]['phon']['rules'][name]:
         config += "# There is no 'list' value in rule '%s'\n" % name
      else:
         for rule in languagedb[lang]['phon']['rules'][name]['list']:
            config += "      %s\n" % (rule)

   persistent = ""
   for name in languagedb[lang]['phon']['rules']:
      if languagedb[lang]['phon']['rules'][name]['date']=='persist':
         persistent += "   %s\n" % (name)
   if persistent: config += "\nSection Persistent\n" + persistent


   config += "\nSection Rules\n"
   for name in sorted(languagedb[lang]['phon']['rules'], key=lambda rule: languagedb[lang]['phon']['rules'][rule]['date']):
      if type(languagedb[lang]['phon']['rules'][name]['date']) is int:
         config += "   %d\n   %s\n" % (languagedb[lang]['phon']['rules'][name]['date'], name)

   config += "\n"

   for name in languagedb[lang]['phon']['rules']:
      if languagedb[lang]['phon']['rules'][name]['date'] is None:
         config += "# Undated or removed rule group: %s\n" % (name)

   config += "\n"

   return config


def apply_rules(language, word, reverse=False, start_date=None, end_date=None):
   wordlist = ipa.compile_words([word])
   print "Types:", type(word)
   parser = ipa.RulesParser(produce_rules(language).split("\n"))
   print produce_rules(language).split("\n")
   rules = parser.get_rules(start_date, end_date)
   for r in rules: print r
   if reverse:
      applier = ipa.ReverseSoundChange(rules, parser.get_phonotactics())
   else:
      applier = ipa.SoundChange(rules)

   result = applier.transform_lexicon(wordlist)

   for r in result:
      derivatives = r.get_final_derivatives()
      for d in derivatives: print "Final derivatives:", type(d.get_form('display'))

   return [w.get_form('display') for w in derivatives]


def normalize_word(word, language):
   normalized = word.strip()
   print "Types:", type(word), type(normalized)
   if (normalized.startswith('/') and normalized.endswith('/')) or (normalized.startswith('[') and normalized.endswith(']')):
      normalized = normalized.strip("[]/")
      try:
         normalized = SAMPA2IPA(normalized)
         normalized = normalized.strip("[]/")
      except:
         try: IPA2SAMPA(normalized)
         except: raise PhonologyRepresentationError("[%s] is not valid IPA" % normalized)
   else:
      try:
         normalized, source = pronunciation(normalized, language)[0]
      except NotImplementedError:
         raise NotImplementedError("Cannot generate IPA representation for language '%s' (try giving IPA between square brackets directly)" % language)
      normalized = normalized.strip("[]/")

   return normalized


def add_resource(url, label, category, language, priority=0):
   global languagedb, languagedb_lock

   lang=langcode(language)
   if not lang: raise NotImplementedError("No such language %s" % language)

   with languagedb_lock:
      languagedb.setdefault(lang, OOBTree()).setdefault('links', OOBTree()).setdefault(category, PersistentList())

      for u, l, p in languagedb[lang]['links'][category]:
         print u, l, p
         if u.lower() == url.lower(): return

      languagedb[lang]['links'][category].append((url, label, priority))

      db.transaction.commit()


def list_resources(language, description, min_priority=0):
   global languagedb

   lang=langcode(language)
   if not lang: raise NotImplementedError("No such language %s" % language)

   if lang not in languagedb: return []
   if 'links' not in languagedb[lang]: return []

   c = None
   entries = []
   for match in (['perfect', 'substring', 'extended'] if description else ['extended']):
      for category in languagedb[lang]['links']:
         if match == 'perfect':
            if description.lower() == category.lower():
               c = category
               break
         if match == 'substring':
            if description.lower() in category.lower():
               c = category
               break
         if match == 'extended':
            for u, l, p in languagedb[lang]['links'][category]:
               if description.lower() in l.lower() or description.lower() in u.lower():
                  entries.append((u, l, p))

   if c: entries = languagedb[lang]['links'][c]

   print entries

   return [(u, l, p) for u, l, p in reversed(sorted(entries, key=lambda resource: resource[2])) if p >= min_priority]


def set_resource_priority(language, url, priority, add=True):
   global languagedb, languagedb_lock

   lang=langcode(language)
   if not lang: raise NotImplementedError("No such language %s" % language)

   if lang not in languagedb: raise NotImplementedError("No resources for language %s" % lang)
   if 'links' not in languagedb[lang]: return NotImplementedError("No resources for language %s" % lang)

   with languagedb_lock:
      changed = 0
      for category in languagedb[lang]['links']:
         for i, tuple in enumerate(languagedb[lang]['links'][category]):
            u, l, p = languagedb[lang]['links'][category][i]
            if u.lower() == url.lower() or url.lower() == l.lower():
               if add: p += priority
               else: p = priority
               languagedb[lang]['links'][category][i] = u, l, p
               changed += 1

      db.transaction.commit()

   return changed


def get_brain(filename, stemmer=None, create=False):
   global markov_order, markov_locks, markov_backlog

   with markov_locks[filename]:
      if create:
         try:
            Brain.init(filename, markov_order)
            print "Creating brain %s..." % filename
         except Exception as e:
            print "Not creating %s:" % filename, e
            pass # it already exists, or something weird happened, which we should catch later

      try:
         if os.path.isfile(filename):
            brain = Brain(filename)
            brain.scorer = cobe.scoring.ScorerGroup()
            brain.scorer.add_scorer(0.5, cobe.scoring.CobeScorer())
            brain.scorer.add_scorer(0.5, cobe.scoring.InformationScorer())

            print brain.scorer.scorers
            if stemmer:
               try:
                  brain.set_stemmer(stemmer)
               except KeyError:
                  print "Error: stemming algorithm not found, reverting to default"
            return brain
         else:
            print "%s is not a valid file." % filename
      except Exception as e:
         print "Cannot load brain %s:" % filename, str(e)

   return None


def brain_reply(filename, prompt, stemmer=None):
   global markov_locks

   stopwords = get_stopwords(stemmer)

   with markov_locks[filename]:
      brain = get_brain(filename)
      if brain:
         line = ' '.join([word.strip() for word in prompt.strip().split(' ') if word.strip() not in stopwords])
         print "'%s' has been pruned to '%s'" % (prompt, line)
         return brain.reply(line)
      else:
         return None


def brain_learn(filename, line=None, stemmer=None):
   global markov_locks, markov_backlog

   with markov_locks[filename]:
      if filename not in markov_backlog: markov_backlog[filename] = []
      if line: markov_backlog[filename].append(line)

      if len(markov_backlog[filename]) > 40 or not line:
         print "Saving data for brain '%s'..." % filename
         brain = get_brain(filename, stemmer, create=True)
         brain.start_batch_learning()
         for l in markov_backlog[filename]:
            brain.learn(l)
         brain.stop_batch_learning()
         del markov_backlog[filename]
         print "Done."


def brain_exists(filename):
   global markov_locks

   with markov_locks[filename]:
      if get_brain(filename) is not None:
         return True
      else:
         return False


#link_parser = ctypes.cdll.LoadLibrary("liblink-grammar.so")
#link_parser_opts = link_parser.parse_options_create()
#link_parser_dicts = {}
#link_parser_lock = threading.Lock()

def check_grammar(sentence, language='eng'):
   global link_parser_dicts, link_parser_lock

   with link_parser_lock:
      lang = langcode(language, 'iso639-2')

      if lang not in link_parser_dicts:
         link_parser_dicts[lang] = link_parser.dictionary_create_lang(lang)

      if not link_parser_dicts[lang]:
         raise NotImplementedError("Cannot load dictionary for language '%s'" % lang)

      s = link_parser.sentence_create(sentence, link_parser_dicts[lang])
      link_parser.sentence_split(s, link_parser_opts)

      if link_parser.sentence_parse(s, link_parser_opts):
         print "At least one linkage found for '%s'." % sentence
         response = True
      else:
         print "No linkages found for '%s'." % sentence
         response = False

      link_parser.sentence_delete(s)

   return response


def get_stopwords(language):
   global nltk, global_stopwords

   stopwords = global_stopwords

   if language: lang = langcode(language, 'name').lower()
   else: lang = None

   try:
      stopwords += nltk.corpus.stopwords.words(lang)
   except:
      print "Cannot load stopwords for '%s'" % lang

   return stopwords


def guess_translation_languages(text, lang1, lang2, defaults=['eng', 'epo'], alternative=False, fixed=False):
   guesses = identify_language(text)
   first_guess, score = guesses[0]
   second_guess, score = guesses[1] if len(guesses)>1 else (first_guess, score)
   if not first_guess:
      try: _, first_guess, _ = googletranslate(text)
      except: first_guess = second_guess

#   if lang1: lang1 = langcode(lang1)
#   if lang2: lang2 = langcode(lang2)

   if fixed:
      if not lang1:
         if alternative:
            first_guess, second_guess = second_guess, first_guess
            alternative = False
         if lang2 == first_guess: lang1 = second_guess
         else: lang1 = first_guess

      if not lang2:
         if alternative:
            default1, default2 = defaults[1], defaults[0]
         else:
            default1, default2 = defaults[0], defaults[1]
         if lang1 == default1: lang2 = default2
         else: lang2 = default1         

   else:
      if not lang1 and first_guess:
         if first_guess == lang2:
            lang1, lang2 = first_guess if not alternative else second_guess, defaults[0]
         else:
            lang1, lang2 = first_guess if not alternative else second_guess, lang2

      if not lang2:
         if first_guess != lang1:
            lang1, lang2 = first_guess, lang1
         else:
            lang2 = defaults[0]

      if first_guess == lang2 and alternative: lang1, lang2 = first_guess, lang1     
      if lang1 == lang2: lang2 = defaults[1]
   
   print "Guessing %s to %s (detected language is %s or %s)" % (lang1, lang2, first_guess, second_guess)

   return (lang1, lang2)


def identify_language(text, standard='linguistlist', methods={'langid': 1.0, 'guess-language': 1.0, 'textcat': 0.0}, max_entries=10):
   results = defaultdict(list)
   languages = defaultdict(list)
   for method in methods:
      t = time.time()

      line = text
      if method == 'textcat' and textcat_identifier:
         try:
            entries = textcat_identifier.classify(line)
            total = 0.0
            for i, language in reversed(list(enumerate(entries[:max_entries]))):
               score = (1.0 / float((i+1)**2)) - total
               assert score >= 0.0
               total += score
               results[method].append((langcode(language.split('-')[0], standard), score))
         except (textcat.UnknownException, textcat.ShortException):
            results[method].append((None, 0.6))
      elif method == 'langid':
         entries = langid.rank(line)[:max_entries]
         for language, score in entries:
            results[method].append((langcode(language, standard), score))
      elif method == 'guess-language':
         try:
            language = guess_language.guess_language(line)
            results[method].append((langcode(language, standard) if language!='UNKNOWN' else None, 0.7))
         except Exception as e:
            print "Error running guess-language:", e
      elif method == 'cld':
         percentage = 0.0
         language_name, language, reliable, bytes, details = cld.detect(line.encode('utf-8'), removeWeakMatches=False)
         if details:
            for language_name, language, percentage, score in details:
               results[method].append((langcode(language, standard) if language!='un' else None, percentage*0.01*(1.0 if reliable else 0.5)))
         else:
            results[method].append((langcode(language, standard) if language!='un' else None, percentage*0.01))

      print "Method %s took %f" % (method, time.time()-t)

   for method, entries in results.items():
      for code, score in entries:
         print "Method %s gave %f for %s" % (method, score, code)
         languages[code].append(score * methods[method])

   for code in languages:
      print "Language %s with probability %f" % (code, sum(languages[code]) / float(len(languages[code])))
      languages[code] = sum(languages[code]) / sum(methods.values())

   output = [(code, languages[code]) for code in sorted(languages, key=languages.get, reverse=True) if languages[code]>0.1][:max_entries]

   return output if output else [(None, 0.0)]


def filter_badwords(text, language='eng'):
   return text

   lang = langcode(language)

   if not lang in languagedb: return text
   if not 'dict' in languagedb[lang]: return text

   words = text.split(" ")
   filtered = []
   for word in words:
      if languagedb[lang]['dict'].get(word, {}).get('attr', {}).get('bad', False):
         print "Bad word '%s' spotted!" % word
         filtered.append("#$%&")
      else:
         filtered.append(word)

   print text, filtered

   return u" ".join(filtered)
