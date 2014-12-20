#!/usr/bin/env python
# coding=utf-8
"""
apertium.py - Phenny Apertium Module
Copyright 2013, Lorenzo J. Lucchini, ljlbox@tiscali.it
Licensed under the Eiffel Forum License 2.

http://languagemodules.sourceforge.net/
"""

import re, urllib
import willie.web as web
import subprocess
import willie.natlang as lang
import willie.pastebin as pastebin
import re
import willie.utils as utils


def translation(phenny, input):
   '''Translate a sentence from a language into another, using various engines.'''
   if not input.group(2):
      phenny.reply("Give me some input! Like '<l1 >l2 text'. I could translate... nothing, but why would I?")
      return

   if input.group(2) == "romanization corrections":
      phenny.reply("\x02LjL\x02 to \x02English\x02:  Hello there!")
      return

   text, (lang1, lang2) = lang.args(input.sender, input.group(2), count=2)

   lang1, lang2 = lang.guess_translation_languages(text, lang1, lang2)
   outputs = lang.translate(text, lang1, lang2)

   print outputs

   before = "\x02%s\x02 to \x02%s\x02 translation:  " % (lang.langcode(lang1, 'name'), lang.langcode(lang2, 'name'))
   if outputs:
      formatted = ["%s (%s)" % (text, engine) if engine != 'suggestion' else "Maybe you meant \"%s\"?" % text for engine, text in outputs]
      utils.message(phenny, input, before, formatted, sep=u' — ')
   else:
      utils.message(phenny, input, before, "No engine could successfully translate that.")

translation.commands = ['translation', 'translate', 'tr']
translation.example = u'tr <it >en Ciao, come va?'
translation.response = u'\x02Italian\x02 to \x02English\x02 translation:  Hello , how are you? (Google) — Ciao, how it goes? (Apertium)'
translation.thread = True
translation.exposed = True


def transliteration(phenny, input):
   '''Translate a sentence from a language into another, using various engines.'''
   if not input.group(2):
      phenny.reply("Give me some input! Like '<l1 >l2 text'. I'm supposed to transliterate something containing letters, or the like.")
      return

   text, (lang1, lang2) = lang.args(input.sender, input.group(2), count=2)

   lang1, lang2 = lang.guess_translation_languages(text, lang1, lang2, fixed=True)
   outputs = lang.translate(text, lang1, lang2, transliterate=True)

   print outputs

   before = "\x02%s\x02 to \x02%s\x02 transliteration: " % (lang.langcode(lang1, 'name', passthru=True), lang.langcode(lang2, 'name', passthru=True))
   if outputs:
      formatted = ["%s (%s)" % (text, engine) if engine != 'suggestion' else "Maybe you meant \"%s\"?" % text for engine, text in outputs]
      utils.message(phenny, input, before, formatted, sep=u' — ')
   else:
      utils.message(phenny, input, before, "No engine could successfully transliterate that.")

transliteration.commands = ['transliteration', 'transliterate', 'tl']
transliteration.example = u'tl <hi >ja नमस्ते'
transliteration.response = u'\x02Hindi\x02 to \x02Japanese\x02 transliteration:  ナマステー (UConv) — Namaste (Google) — Maybe you meant "नमस्ते!"?'
transliteration.thread = True
transliteration.exposed = True


def romanization(phenny, input):
   '''Transliterate a sentence into Latin characters, or from Latin characters into another writing system.'''
   if not input.group(2):
      phenny.reply("Give me some input! Like '<language text'")
      return

   text, language = lang.args(input.sender, input.group(2), count=1)

   lang1, lang2 = lang.guess_translation_languages(text, language, None, fixed=True)

   output, language_hint, suggestion = lang.googletranslate(text, lang1, lang2, romanize=True)
   if suggestion:
      if not output or output.lower() == text.lower(): output = suggestion
      else: output += u" — But maybe you meant: %s" % suggestion

   phenny.reply("\x02%s\x02 romanization:  %s" % (lang.langcode(lang1 if lang1 else language_hint, 'name'), output))

romanization.commands = ['romanization', 'romanize', 'romanisation', 'romanise', 'ro']
romanization.example = u'ro <ja 私'
romanization.response = '\x02Japanese\x02 romanization:  Watashi'
romanization.thread = True
romanization.exposed = True


def apertium(phenny, input): 
   '''Attempts to translate a given piece of text from one language into another using Apertium'''
   if not input.group(2):
      phenny.reply("Give me some input! Like '<l1 >l2 text'")
      return

   text, (lang1, lang2) = lang.args(input.sender, input.group(2), count=2)

   print lang1, lang2

   if lang1 and not lang.langcode(lang1):
      mode, correct_mode = lang1, True
   else:
      lang1, lang2 = lang.guess_translation_languages(text, lang1, lang2)
      mode, correct_mode = lang.apertium_mode(lang1, lang2)

   if text.startswith("http://"):
      format = 'html'
      url = text.strip().split(" ")[0]
      try:
         text = web.get(url)
      except Exception:
         phenny.reply("Could not get the URL '%s'" % url)
         return
   else:
      format = 'txt'

   try:
      response = lang.apertium(text, mode, "/usr/local/share/apertium", format=format, timeout=20)
   except NotImplementedError as e:
      phenny.reply(str(e))
      return

   if len(response)>350 or "\n" in response.strip():
      try:
         response = pastebin.paste(response, 'Apertium translation using mode %s' % mode, 'xml')
      except IOError:
         response = response[:350] + "[...]"

   if lang1: lang1 = lang.langcode(lang1, 'name')
   if lang2: lang2 = lang.langcode(lang2, 'name')

   phenny.reply(u"%s (%s to %s%s, %s mode used)" % (response, lang1, lang2, " not available" if not correct_mode else "", mode))

apertium.commands = ['apertium', 'ap']
apertium.thread = True
apertium.priority = 'low'
apertium.example = 'ap :en :es The quick brown fox jumps over the lazy dog.'
apertium.response = u'El zorro marrón rápido salta el perro perezoso. (English to Spanish, en-es mode used)'


def apertiumlist(phenny, input):
   '''Lists all language pair in Apertium, or all language pairs containing the specified language.'''
   if input.group(2):
      list = lang.apertium_list(input.group(2))
      verbose = True
   else:
      list = lang.apertium_list()
      verbose = False

   if list is None:
      phenny.reply("List has not yet been populated, please wait...")
      return

   phenny.reply(", ".join([element for element in list if len(element)<=6 or verbose]))

apertiumlist.commands = ['apertiumlist', 'al']
apertium.thread = True
apertiumlist.priority = 'low'
apertiumlist.example = 'al it-en'
apertiumlist.response = 'it-en, it-en-anmor, it-en-chunker, it-en-generador, it-en-interchunk, it-en-latin1, it-en-lextor, it-en-multi, it-en-postchunk, it-en-pretransfer, it-en-tagger, it-en_US, it-en_US-generador, test-it-en, test-it-en-anmor, test-it-en-chunker, test-it-en-generador, test-it-en-interchunk, test-it-en-postchunk, test-it-en-pretransfer, test-it-en-tagger'
