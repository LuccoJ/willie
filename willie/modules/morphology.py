#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
morphology.py - Phenny Morphology Module
Copyright 2013, Lorenzo J. Lucchini, ljlbox@tiscali.it
Licensed under the Eiffel Forum License 2.

http://languagemodules.sourceforge.net/
"""

import re
import willie.web as web
import subprocess
import string
import urllib
import glob
from willie.tools import deprecated
import willie.natlang as lang
import willie.utils as utils

apertium_prefix = "/usr/local/share/apertium/apertium-"

tagstonames={
# Parts of speech
   'n': ['noun'],
   'vblex': ['verb'],
   'vbmod': ['modal verb'],
   'vbser': ['copula'],
   'vbhaver': ['special verb'],
   'vbdo': ['special verb'],
   'vaux': ['helper verb'],
   'adj': ['adjective'],
   'adv': ['adverb'],
   'preadv': ['pre-adverb'],
   'postadv': ['post-adverb'],
   'det': ['determiner'],
   'prn': ['pronoun'],
   'pr': ['preposition'],
   'num': ['numeral'],
   'np': ['proper noun'],
   'ij': ['interjection'],
   'cnjcoo': ['co-ordinating conjunction', 'co-ord. conj.'],
   'cnjsub': ['sub-ordinating conjunction', 'sub-ord. conj.'],
   'cnjadv': ['conjunctive adverb', 'conj. adverb'],
   'sent': ['punctuation'],
# Person
   'p1': ['1st person', '1p.'],
   'p2': ['2nd person', '2p.'],
   'p3': ['3rd person', '3p.'],
   'impers': ['impersonal'],
# Adjectives
   'sint': ['synthetic', ''],
   'comp': ['comparative', 'comp.'],
   'sup': ['superlative', 'sup.'],
   'attr': ['attributive', 'attr.'],
   'pred': ['predicative', 'pred.'],
# Tense and mode
   'ger': ['gerund'],
   'pprs': ['present participle', 'pres. part.'],
   'past': ['simple past'],
   'pp': ['past participle', 'past part.'],
   'inf': ['infinitive', 'inf.'],
   'pres': ['present', 'pres.'],
   'pii': ['imperfect', 'imperf.'],
   'fti': ['future indicative', 'fut. ind.'],
   'fts': ['future subjunctive', 'fut. subj.'],
   'prs': ['present subjunctive', 'pres subj.'],
   'pis': ['past imperfect subjunctive', 'past imperf. subj.'],
   'cni': ['conditional', 'cond.'],
   'imp': ['imperative', 'imp.'],
   'plu': ['pluperfect', 'pluperf.'],
   'pmp': ['pluperfect', 'pluperf.'],
   'ifi': ['past definite', 'past def.'],
   'pret': ['preterite', 'pret.'],
   'aff': ['affirmative', 'affirm.'],
   'itg': ['interrogative', 'interr.'],
   'neg': ['negative', 'neg.'],
   'pri': ['present indicative', 'pres. ind.'],
   'subs': ['substantive(?)'],
# Voice
   'actv': ['active', 'act.'],
   'pasv': ['passive', 'pass.'],
   'pass': ['passive', 'pass.'],
   'midv': ['middle'],
   'nactv': ['non-active', 'non-act.'],
# Numbers
   'cnt': ['countable', 'count.'],
   'unc': ['uncountable', 'uncount.'],
   'sg': ['singular', 'sing.'],
   'pl': ['plural', 'pl.'],
   'du': ['dual'],
   'ct': ['count'],
   'coll': ['collective'],
   'sp': ['singular or plural', 'sing./pl.'],
   'ND': ['undetermined number'],
# Genders
   'm': ['masculine', 'masc.'],
   'f': ['feminine', 'fem.'],
   'nt': ['neuter', 'neut.'],
   'ma': ['masculine animate'],
   'mi': ['masculine inanimate'],
   'mp': ['masculine personal'],
   'mn': ['masculine or neuter', 'm./n.'],
   'fn': ['feminine or neuter' 'f./n.'],
   'ut': ['common'],
   'mf': ['masculine or feminine', 'm./f.'],
   'mfn': ['masculine or feminine and neuter', 'm./f./n.'],
   'un': ['common or neuter', 'comm./n.'],
   'GD': ['undetermined gender'],
# Cases
   'nom': ['nominative', 'nom.'],
   'gen': ['genitive', 'gen.'],
   'dat': ['dative', 'dat.'],
   'dg': ['dative/genitive', 'dat./gen.'],
   'acc': ['accusative', 'acc.'],
   'voc': ['vocative', 'voc.'],
   'abl': ['ablative', 'abl.'],
   'ins': ['instrumental', 'instr.'],
   'loc': ['locative', 'loc.'],
   'cpr': ['cprepositional', 'cprep.'],
   'prp': ['prepositional', 'prep.'],
# Misc
   'tn': ['stress-carrying', ''],
   'atn': ['non-stress-carrying', ''],
   'detnt': ['neuter determiner', 'neut. det.'],
   'predet': ['pre-determiner', 'pre-det.'],
   'qnt': ['quantifier'],
   'ord': ['ordinal'],
   'obj': ['object', 'obj.'],
   'subj': ['subject', 'subj.'],
   'pro': ['proclitic', 'procl.'],
   'enc': ['enclitic', 'encl.'],
   'acr': ['acronym'],
   'rel': ['relative', 'rel.'],
   'ind': ['indefinite', 'indef.'],
   'dem': ['demonstrative', 'demonstr.'],
   'def': ['definite', 'def.'],
   'pos': ['possessive', 'poss.'],
   'ref': ['reflexive', 'refl.'],
   'prx': ['proximate'],
   'dst': ['distal'],
   'pprep': ['post-preposition'],
   'uns': ['unstressed'],
   'sep': ['separable'],
   'ant': ['anthroponym', 'pers.']
}

namestotags={i:k for k in tagstonames for i in tagstonames[k]}

def morphology(phenny, input): 
   '''Analyzes the morphology of a word or phrase'''
   word, language = lang.args(input.sender, input.group(2), standard='iso639-2', count=1)

   if language is None:
      language="en"

   if word is None:
      phenny.reply("You need to provide a word!")
      return

   try:
      parse = ltproc(word, language)
   except NotImplementedError:
      language = lang.langcode(language, 'iso639-3')
      try:
         parse = ltproc(word, language)
      except NotImplementedError:
         phenny.reply("Unknown language %s. Allowed languages: %s" % (language, ", ".join(listLanguages()).decode('utf-8')))
         return

   lemmas = re.findall(r'\^([^$]*)\$', parse)
   unkeyedentries = [lemma.split('/') for lemma in lemmas]
   entries = []
   for entry in unkeyedentries:
      entries.append((entry[0], entry[1:]))
   for word, entry in entries:
      for i, lemma in enumerate(entry):
         form = re.search('^([^<]*)', lemma).group(0)
         entry[i]=(form if form.lower() != 'prpers' else 'personal pronoun', re.findall(r'<([^>]*)>', lemma))
   entries = [(word, entry) for word, entry in entries if word!="."]
   abbreviate = False
   if len(entries)>2:
      entries = [(word, [entry[0]]) for word, entry in entries]
      if len(entries)>5:
         abbreviate = True

   for short in [False, True]:
      response = [(lang.lemma(word, language) + ": " if word!='' else ' + ') + ", or ".join([describe(lemma, short) for lemma in entry if describe(lemma)]) for word, entry in entries if word!="."]
      if utils.message(phenny, input, "", response, sep='; ', cut=short): return

morphology.commands = ['morphology', 'mo']
morphology.example = 'mo <en being'
morphology.response = '\x02being\x02: singular form of the noun \x1dbeing\x1d, or gerund form of the copula \x1dbe\x1d'
morphology.thread = True
morphology.exposed = True


def describe(lemma, abbreviate=False):
   if len(lemma[1])>1:
      if abbreviate:
         return " ".join(reversed(replaceTags(lemma[1][1:], abbreviate))) + " of " + replaceTags(lemma[1][0]) + " \x1d" + lemma[0] + "\x1d"
      else:
         return " ".join(reversed(replaceTags(lemma[1][1:], abbreviate))) + " form of the " + replaceTags(lemma[1][0]) + " \x1d" + lemma[0] + "\x1d"
   elif len(lemma[1])==1:
      return replaceTags(lemma[1][0], abbreviate)
   else:
      return "unknown word"


def replaceTags(tags, abbreviate=False):
   if type(tags) == list:
     return map(lambda tag: tagstonames[tag][1 if abbreviate and len(tagstonames[tag])>1 else 0] if tag in tagstonames else tag, tags)
   else:
     return tagstonames[tags][1 if abbreviate and len(tagstonames[tags])>1 else 0] if tags in tagstonames else tags

def listLanguages(generate=False):
   if generate:
      rulefiles=glob.glob("/usr/local/share/apertium/apertium-*-*/*-*.autogen.bin")
   else:
      rulefiles=glob.glob("/usr/local/share/apertium/apertium-*-*/*-*.automorf.bin")
   return set(re.findall(r'[^a-z]([a-z][a-z][a-z]?)[^a-z]', " ".join(rulefiles)))


languageprefs = {'en': 'en-es', 'hi': 'en-hi', 'eo': 'eo-en', 'la': 'la-es', 'oc': 'oc-ca', 'it': 'en-it', 'es': 'en-es', 'sv': 'sv-da', 'da': 'sv-da'}

def ltproc(input, language, generate=False):
   if language in languageprefs:
      languagepair = languageprefs[language]
   else:
      languagepair = language
   if generate:
      rulefiles=glob.glob(apertium_prefix+"*"+languagepair+"*/*"+language+".autogen.bin")
   else:
      rulefiles=glob.glob(apertium_prefix+"*"+languagepair+"*/"+language+"*.automorf.bin")
   if len(rulefiles)==0: raise NotImplementedError("Unknown language")
   p_esc = subprocess.Popen(["apertium-destxt"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
   result, errors = p_esc.communicate(input.encode('utf-8')+"\n")
   p_proc = subprocess.Popen(["lt-proc", "-g" if generate else "-a", rulefiles[0]], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
   result, errors = p_proc.communicate(result)
   taggerfiles=glob.glob(apertium_prefix+"*"+languagepair+"*/"+language+"*.prob")
   if len(taggerfiles)>0:
      p_sort = subprocess.Popen(["apertium-tagger", "-g", "-f", taggerfiles[0]], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
      result, errors = p_sort.communicate(result)
#   p_split = subprocess.Popen(["apertium-pretransfer"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
#   result, errors = p_split.communicate(result)
   print "RESULT"
   print result
   return result.decode('utf-8')

