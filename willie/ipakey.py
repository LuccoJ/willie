#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ipa.py - Phenny IPA Tables
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

ipa_key_best_languages = {'eng': ['eng'], 'swe': ['swe', 'eng'], 'ita': ['ita', 'eng']}

ipa_key = {
   u'b': {'eng': u'[b]uy', 'swe': u'a[b]ort', 'ita': u'[b]ene'},
   u'd': {'eng': u'[d]o', 'swe': u'[d]ag', 'ita': u'[d]ove'},
   u'ð': {'eng': u'[th]is'},
   u'dz': {'eng': u'la[ds]', 'ita': u'[z]ona'},
   u'dʒ': {'eng': u'[j]am', 'ita': u'[g]ita'},
   u'ɖ': {'swe': u'no[rd]', 'ita': u'be[ddh]u (siciliano)'},
   u'f': {'eng': u'[f]an', 'swe': u'[f]ot', 'ita': u'[f]are'},
   u'ɡ': {'eng': u'[g]uy', 'swe': u'[g]od', 'ita': u'[g]ara'},
   u'ɡ': {'eng': u'[g]uy', 'swe': u'[g]od', 'ita': u'[g]ara'},
   u'h': {'eng': u'[h]i', 'swe': u'[h]att', 'ita': u'[h]aha'},
   u'ɧ': {'eng': u'~lo[ch]/[wh]ich', 'swe': u'[sj]ö'},
   u'j': {'eng': u'[y]es', 'swe': u'[j]ojo', 'ita': u'[i]eri'},
   u'k': {'eng': u'[k]ey', 'swe': u'[k]afé', 'ita': u'[k]asa'},
   u'l': {'eng': u'[l]ie', 'swe': u'[l]ake', 'ita': u'[l]ato'},
   u'ɭ': {'eng': u'twir[l]', 'swe': u'Ka[rl]'},
   u'm': {'eng': u'[m]y', 'swe': u'[m]an', 'ita': u'[m]are'},
   u'n': {'eng': u'[n]o', 'swe': u'[n]att', 'ita': u'[n]ave'},
   u'ŋ': {'eng': u'si[ng]', 'swe': u'ti[ng]', 'ita': u'a[n]ca'},
   u'ɳ': {'eng': u'~tur[n]er', 'swe': u'ba[rn]'},
   u'θ': {'eng': u'[th]ink'},
   u'p': {'eng': u'[p]ie', 'swe': u'[p]appa', 'ita': u'[p]enna'},
   u'r': {'eng': u'[r]un', 'swe': u'å[r]', 'ita': u'[r]ana'},
   u's': {'eng': u'[s]et', 'swe': u'[s]abel', 'ita': u'[s]eta'},
   u'ʃ': {'eng': u'[sh]y', 'swe': u'~fö[rs]tå', 'ita': u'[sc]iocco'},
   u'ɕ': {'swe': u'[K]ina'},
   u'ʂ': {'eng': u'~mar[sh]al', 'swe': u'to[rs]dag', 'ita': u'[str]ata (siciliano)'},
   u't': {'eng': u'[t]est', 'swe': u'[t]orsdag', 'ita': u'[t]ono'},
   u'ts': {'eng': u'ca[ts]', 'swe': u'ka[tts]', 'ita': u'a[z]ione'},
   u'tʃ': {'eng': u'[ch]eck', 'ita': u'[c]era'},
   u'ʈ': {'eng': u'~car[t]el', 'swe': u'pa[rt]i', 'ita': u'[t]renu (siciliano)'},
   u'v': {'eng': u'[v]an', 'swe': u'[v]aktel', 'ita': u'[v]oto'},
   u'w': {'eng': u'[w]est', 'ita': u'[u]ovo'},
   u'z': {'eng': u'[z]oo', 'ita': u'ca[s]o'},
   u'ʒ': {'eng': u'vi[si]on', 'ita': u'gara[ge]'},
   u'x': {'eng': u'lo[ch] (Scottish)', 'swe': u'~[sj]ö', 'ita': u'[c]asa (toscano)'},
   u'ɑ': {'eng': u'f[a]ther', 'swe': u'm[a]t'},
   u'ɒ': {'eng': u'l[o]t'},
   u'æ': {'eng': u'tr[a]p', 'swe': u'f[ä]rsk'},
   u'æː': {'eng': u'h[a]m (Australian)', 'swe': u'[ä]ra'},
   u'a': {'eng': u'tr[a]p', 'swe': u'f[a]st', 'ita': u'[a]'},
   u'aɪ': {'eng': u'r[i]de', 'ita': u'~[ai]'},
   u'ʌɪ': {'eng': u'r[i]de', 'ita': u'~[ai]'},
   u'aʊ': {'eng': u'l[ou]d', 'ita': u'~c[au]sa'},
   u'ɛ': {'eng': u'b[e]d', 'swe': u'h[ä]ll', 'ita': u'[è]'},
   u'ɛː': {'eng': u'b[e]d (long)', 'swe': u'h[ä]l', 'ita': u'[è] (ma lunga)'},
   u'e': {'eng': u's[a]ve (Scottish)', 'swe': u'h[e]l', 'ita': u'[e]'},
   u'eɪ': {'eng': u'f[a]ce', 'swe': u'~tj[ej]', 'ita': u'~n[ei]'},
   u'ɪ': {'eng': u'k[i]t', 'swe': u's[i]ll', 'ita': u'~d[i]'},
   u'i': {'eng': u's[ee]', 'swe': u's[i]l (men kort)', 'ita': u'scr[i]tto'},
   u'iː': {'eng': u's[ee]', 'swe': u's[i]l', 'ita': u'v[i]a'},
   u'o': {'swe': u'm[å]l (men kort)', 'ita': u'p[o]llo'},
   u'oː': {'eng': u'st[o]ve (Scottish/Canadian)', 'swe': u'm[å]l', 'ita': u'[o]'},
   u'ɔ': {'eng': u'str[aw]', 'swe': u'm[o]ll', 'ita': u'h[o]'},
   u'øː': {'swe': u'd[ö]', 'ita': u'c[oeu]r (milanese)'},
   u'œ': {'swe': u'n[ö]tt'},
   u'œː': {'swe': u'[ö]ra'},
   u'ɔɪ': {'eng': u'c[oi]n', 'ita': u'~bu[oi]'},
   u'oʊ': {'eng': u'g[o]'},
   u'əʊ': {'eng': u'g[o]', 'ita': u'~n[eu]rone'},
   u'ʊ': {'eng': u'f[u]ll', 'swe': u'b[o]tt'},
   u'u': {'eng': u'f[oo]d (but short)', 'swe': u'b[o]t (men kort)', 'ita': u't[u]tto'},
   u'uː': {'eng': u'f[oo]d', 'swe': u'b[o]t', 'ita': u't[u]bo'},
   u'ʉː': {'swe': u'f[u]l'},
   u'ju': {'eng': u'[you]', 'swe': u'[jo]rd', 'ita': u'[iu]ta'},
   u'yː': {'swe': u's[y]l'},
   u'ʏ': {'swe': u's[y]ll'},
   u'ʌ': {'eng': u'c[u]p'},
   u'ɑr': {'eng': u'st[ar]t', 'swe': u'~t[ar]', 'ita': u'~[ar]te'},
   u'ɔr': {'eng': u'b[or]n', 'ita': u'~f[or]te'},
   u'jʊ': {'eng': u'c[u]re'},
   u'ʌr': {'eng': u'h[urr]y'},
   u'ɝ': {'eng': u'gI[r]l'},
   u'ɜr': {'eng': u'gI[r]l'},
   u'ə': {'eng': u'comm[a]', 'swe': u'b[e]gå'},
   u'ɨ': {'eng': u'ros[e]s'},
   u'ɵ': {'eng': u'[o]mission', 'swe': u'f[u]ll'},
   u'ʉ': {'eng': u'beautif[u]l', 'swe': u'f[u]l (men kort)'},
#   u'ər': {'eng': u'p[er]ceive'},
   u'ɚ': {'eng': u'p[er]ceive'},
   u'əl': {'eng': u'bott[le]'},
   u'ən': {'eng': u'butt[on]'},
   u'əm': {'eng': u'rhyth[m]'},
   u'ŋɡ': {'eng': u'fi[ng]er'},
   u'ː': {'eng': u'(long)', 'swe': u'(lång)', 'ita': u'(lunga)'},
   u':': {'eng': u'(long)', 'swe': u'(lång)', 'ita': u'(lunga)'},
   u'\'': {'eng': u'(stress ->)', 'swe': u'(betoning ->)', 'ita': u'(acc. ->)'},
   u'ˈ': {'eng': u'(stress ->)', 'swe': u'(betoning ->)', 'ita': u'(acc. ->)'},
   u'.': {'eng': u',', 'swe': u',', 'ita': u','},
   u'narrow': {'eng': u'This is a narrow/phonetic representation:', 'swe': u'', 'ita': u'Rappresentazione fonetica:'},
   u'broad': {'eng': u'This is a broad/phonemic representation:', 'swe': u'', 'ita': u'Rappresentazione fonemica:'}
}

ipa_features = {
   'anterior': {
      'description': 'Anteriors are articulated with the tip/blade of the tongue at or in front of the alveolar ridge (covers bilabials, labiodentals, dentals, alveolars, and retroflexes).',
      'position': 1000,
      'plus': ('anterior',),
      'minus': (None, 'posterior',)
   },
   'aspirated': {
      'description': 'Aspiration is the strong burst of air that accompanies either the release or the closure (preaspiration) of some obstruents.',
      'url': 'http://en.wikipedia.org/wiki/Aspiration_(phonetics)',
      'position': 2000,
      'plus': ('aspirated',),
      'minus': (None, 'unaspirated',)
   },
   'back': {
      'description': 'Back sounds are produced with the tongue dorsum bunched and retracted slightly to the back of the mouth (covers velars, uvulars and pharyngeals, and back vowels)',
      'url': 'http://en.wikipedia.org/wiki/Back_vowel',
      'position': 10,
      'plus': ('back',),
      'minus': (None,),
      'central': ('near-back',)
   },
   'central': {
      'description': 'The defining characteristic of a central vowel is that the tongue is positioned halfway between a front vowel and a back vowel.',
      'url': 'http://en.wikipedia.org/wiki/Central_vowel',
      'position': 10,
      'plus': ('central',),
      'minus': (None,),
      'back': ('near-back',)
   },
   'consonantal': {
      'description': 'Consonants are produced with an audible constriction in the vocal tract (includes obstruents, nasals, liquids, and trills; vowels, glides and laryngeal segments are not consonantal).',
      'url': 'http://en.wikipedia.org/wiki/Consonant',
      'position': 0,
      'plus': ('consonant', 'consonantal',),
      'minus': (None,)
   },
   'continuant': {
      'description': 'Continuants are produced without significant obstruction of the tract, so air flows continuously (covers nasals, fricatives, approximants, and vowels).',
      'url': 'http://en.wikipedia.org/wiki/Continuant',
      'position': 10,
      'plus': ('continuant',),
      'minus': ('stop', 'plosive',),
      'syllabic': ('vowel',),
   },
   'coronal': {
      'description': 'Coronal sounds are articulated with the tip and/or blade of the tongue (covers dentals, alveolars, postalveolars and retroflexes).',
      'url': 'http://en.wikipedia.org/wiki/Coronal_consonant',
      'position': 2000,
      'plus': ('coronal',),
      'minus': (None, 'peripheral',)
   },
   'delayedrelease': {
      'description': 'Affricates are consonants that begin as stops but release as a fricative rather than directly into the following vowel.',
      'url': 'http://en.wikipedia.org/wiki/Affricate_consonant',
      'position': 10,
      'plus': ('affricate', 'delayedrelease', 'delayed-release'),
      'minus': (None,)
   },
   'dental': {
      'description': 'Dental and labiodental consonants are articulated with the tongue or a lip against the teeth.',
      'url': 'http://en.wikipedia.org/wiki/Dental_consonant',
      'position': 20,
      'plus': ('dental',),
      'minus': (None,),
      'labial': ('labio-dental',)
   },
   'labial': {
      'description': 'Labial sounds are articulated with the lips. As consonants, these include bilabial and labiodental consonants.',
      'url': 'http://en.wikipedia.org/wiki/Labial_consonant',
      'position': 20,
      'plus': ('bilabial', 'labial'),
      'minus': (None,),
      'dental': ('labio-dental',)
   },
   'egressive': {
      'description': 'In egressive sounds, air is pushed outwards.',
      'url': 'http://en.wikipedia.org/wiki/Airstream_mechanism#Types_of_airstream_mechanism',
      'position': 1000,
      'plus': (None, 'egressive',),
      'minus': ('ingressive',)
   },
   'front': {
      'description': 'In a front vowel is the tongue is positioned as far in front as possible in the mouth without creating a consonantal constriction.',
      'url': 'https://en.wikipedia.org/wiki/Front_vowel',
      'position': 10,
      'plus': ('front',),
      'minus': (None,),
      'central': ('near-front',)
   },
   'glottalic': {
      'description': 'Glottalic consonants are produced with a contribution from the glottis (covers implosives and ejectives).',
      'url': 'http://en.wikipedia.org/wiki/Glottalic_consonant',
      'position': 1000,
      'plus': ('glottalic',),
      'minus': (None, 'pulmonic',)
   },
   'high': {
      'description': 'Close or high sounds have the back of the tongue raised towards the upper palate (covers close vowels and postalveolars, palatals and velars).',
      'url': 'http://en.wikipedia.org/wiki/Close_vowel',
      'position': 20,
      'plus': ('close', 'high',),
      'minus': (None,),
      'lax': ('near-close', 'near-high',),
      'mid': ('close-mid', 'high-mid', 'mid-close', 'mid-high',)
   },
   'lateral': {
      'description': 'A lateral is an L-like consonant, in which airstream proceeds along the sides of the tongue, but is blocked by the tongue from going through the middle of the mouth.',
      'url': 'http://en.wikipedia.org/wiki/Lateral_consonant',
      'position': 10,
      'plus': ('lateral',),
      'minus': (None, 'central',)
   },
   'long': {
      'description': 'Long sounds last a longer time than normal. Vowels can have a long/short contrast, and consonants can also be short ("single") or long ("geminate").',
      'url': 'http://en.wikipedia.org/wiki/Chroneme',
      'position': 2000,
      'plus': ('long',),
      'minus': (None, 'short',),
      'vibration': ('trill',)
   },
   'low': {
      'description': 'An open vowel is a vowel sound in which the tongue is positioned as far as possible from the roof of the mouth (also covers pharyngeal consonants).',
      'url': 'http://en.wikipedia.org/wiki/Open_vowel',
      'position': 20,
      'plus': ('open', 'low',),
      'minus': (None,),
      'lax': ('near-open', 'near-low',),
      'mid': ('open-mid', 'high-mid', 'mid-open', 'mid-high')
   },
   'mid': {
      'description': 'The defining characteristic of a mid vowel is that the tongue is positioned mid-way between an open vowel and a close vowel.',
      'url': 'http://en.wikipedia.org/wiki/Mid_vowel',
      'position': 20,
      'plus': ('mid',),
      'minus': (None,),
      'high': ('close-mid',),
      'low': ('open-mid',)
   },
   'lax': {
      'description': 'Lax refers to vowels pronounced with less "force" than normal vowels, and it can refer to near-front and near-back (as opposed to front and back) vowels.',
      'url': 'http://en.wikipedia.org/wiki/Tenseness',
      'position': 30,
      'plus': ('lax',),
      'minus': (None, 'tense',),
      'front': ('near-front',),
      'back': ('near-back',)
   },
   'nasal': {
      'description': 'Nasal sounds are produced by lowering the velum so that air can pass through the nasal tract.',
      'url': 'http://en.wikipedia.org/wiki/Nasalization',
      'position': 2000,
      'plus': ('nasal',),
      'minus': (None, 'oral',)
   },
   'retroflex': {
      'description': 'Retroflex consonants are coronal consonants where the tongue has a flat, concave, or even curled shape, and are articulated between the alveolar ridge and the hard palate.',
      'url': 'http://en.wikipedia.org/wiki/Retroflex_consonant',
      'position': 2000,
      'plus': ('retroflex',),
      'minus': (None,)
   },
   'rounded': {
      'description': 'Rounded sounds are produced with lip rounding (covers rounded vowels and some labials).',
      'url': 'http://en.wikipedia.org/wiki/Roundedness',
      'position': 5,
      'plus': ('rounded',),
      'minus': (None, 'unrounded',)
   },
   'sonorant': {
      'description': 'Sonorants are sounds made with continuous, non-turbulent airflow in the vocal tract.',
      'url': 'http://en.wikipedia.org/wiki/Sonorant',
      'position': 2000,
      'plus': ('sonorant',),
      'minus': ('obstruent', None,),
      'syllabic': ('vowel',)
   },
   'syllabic': {
      'description': 'A syllabic segment is a vowel or other sound that acts as syllable nucleus.',
      'url': 'http://en.wikipedia.org/wiki/Vowel',
      'position': 0,
      'plus': ('syllabic',),
      'minus': (None, 'non-syllabic',),
      'voiced': ('vowel',),
      'continuant': ('vowel',)
   },
   'velaric': {
      'description': '"Click" consonants are velaric.',
      'url': 'http://en.wikipedia.org/wiki/Click_consonant',
      'position': 10,
      'plus': ('click', 'velaric',),
      'minus': (None,)
   },
   'velarized': {
      'description': 'Velarization is a secondary articulation of consonants by which the back of the tongue is raised toward the velum during the articulation of the consonant.',
      'url': 'http://en.wikipedia.org/wiki/Velarization',
      'position': 1500,
      'plus': ('velarized', 'dark',),
      'minus': (None,),
   },
   'vibration': {
      'description': 'Sounds involving vibration are trills and taps/flaps.',
      'url': 'http://en.wikipedia.org/wiki/Trill_consonant',
      'position': 10,
      'plus': ('tap', 'flap', 'vibrated', 'vibration'),
      'minus': (None,),
      'long': ('trill',)
   },
   'voiced': {
      'description': 'Voiced sounds are made while the vocal cords vibrate.',
      'url': 'https://en.wikipedia.org/wiki/Voice_(phonetics)',
      'position': 2000,
      'plus': ('voiced',),
      'minus': ('voiceless', 'unvoiced', None,),
      'syllabic': ('vowel',)
   },
}
