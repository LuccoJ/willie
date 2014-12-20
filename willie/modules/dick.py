#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sys import stdin, stderr, argv
import os

import willie.utils as utils

def fnDict2Kr(argWord):
    from re import search
    from os import linesep
    from bs4 import BeautifulSoup
    from urllib2 import urlopen, URLError, HTTPError
    from inspect import stack

    """
    Description
        Return English-Korean dictionary result string.

    Usage
        aWord = sys.stdin.readline()
        print fnDict2Kr(aWord)
    """

    argWord = argWord.encode('utf-8')
    mNHNWebDict  = "http://dic.naver.com/search.nhn?dicQuery=%s&x=0&y=0&query=%s&target=dic&ie=utf8&query_utf=&isOnlyViewEE=" \
                   % ((argWord.rstrip(linesep),)*2)

    mFn2Unicode  = lambda x: u" ".join(
        (m for m in (m.strip() for m in x.splitlines()) if m)
    )

    mReturnValue = None

    mResultVector= []

    try:
        mURLopen = urlopen(mNHNWebDict)

        if mURLopen.code == 200 :
            mBS4        = BeautifulSoup(mURLopen.read())
            mResultHTML = mBS4.find("dl", attrs={"class": "dic_search_result"})

            if hasattr(mResultHTML, "find") :
                mIPAVector      = mResultHTML.findAll("dt")
                mMeaningVector  = mResultHTML.findAll("dd")

                for mIdx, mVal in enumerate(m for m in mIPAVector):
                    mIPA        = mVal.get_text()
                    mMeaning    = mMeaningVector[mIdx].get_text()

                    if search(r"\]", mFn2Unicode(mIPA)) :
                        mResultVector.append( "%s - %s" % (mFn2Unicode(mIPA[:mIPA.rindex("]")+1]),mFn2Unicode(mMeaning)) )
                    else:
                        mResultVector.append( "%s - %s" % (mFn2Unicode(mIPA),mFn2Unicode(mMeaning)) )

                mReturnValue = " // ".join(
                    m for m in mResultVector
                )

    except HTTPError, e:
        stderr.write(
            "%s - %d" % (stack()[0][3], e.code)
        )
    except URLError, e:
        stderr.write(
            "%s - %s" % (stack()[0][3], e.args[0])
        )

    return mReturnValue

if __name__ == "__main__":
    mArgv = argv[1:]
    if len(mArgv) > 0 :
        for mWord in mArgv:
            print fnDict2Kr(mWord)
    else:
        for mWord in stdin.readline().split():
            print fnDict2Kr(mWord)



def dick(phenny, input):
    commands= ['dk', 'dick']
    example = 'dk test'
    exposed = False

    mWord   = input.group(2).rstrip(os.linesep)
    utils.message(
         phenny
        ,input
        ,"Korean: "
        ,fnDict2Kr(mWord)
    )

dick.commands= ['dk', 'dick']
dick.example = 'dk test'
dick.exposed = False

