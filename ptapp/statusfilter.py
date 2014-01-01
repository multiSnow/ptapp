#coding: utf8
# Project PTAPP
#
# Copyright (c) 2014, multiSnow <infinity.blick.winkel@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for
# any purpose with or without fee is hereby granted, provided that the
# above copyright notice and this permission notice appear in all
# copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
# AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
# DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
# PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

from json import dumps,loads
from logging import debug,info
from re import IGNORECASE,search

from config import FILTER_hashtag,FILTER_screen_name,FILTER_source,FILTER_text,FILTER_url

regexp_dict={'source':FILTER_source,
             'screen_name':FILTER_screen_name,
             'url':FILTER_url,
             'hashtag':FILTER_hashtag,
             'text':FILTER_text}

filterkey={'source':1,
           'screen_name':2,
           'url':4,
           'hashtag':8,
           'text':16}

def filterrange(fcode):
    for k in filterkey:
        if fcode&filterkey[k]:
            yield k

def check_source(input_dict):
    # return 1 if dict should be filtered
    if not regexp_dict['source']:
        # no checking if regexp is empty
        return 0
    try:
        if search(regexp_dict['source'],input_dict['retweeted_status']['source'],IGNORECASE):
            return 1
    except KeyError:
        # tweet is not a retweet, go on checking
        pass
    try:
        return 1 if search(regexp_dict['source'],input_dict['source'],IGNORECASE) else 0
    except KeyError:
        # tweet is not a tweet, do nothing
        return 0

def check_screen_name(input_dict):
    # return 2 if dict should be filtered
    if not regexp_dict['screen_name']:
        # no checking if regexp is empty
        return 0
    try:
        if search(regexp_dict['screen_name'],input_dict['retweeted_status']['user']['screen_name'],IGNORECASE):
            return 2
    except KeyError:
        # tweet is not a retweet, go on checking
        pass
    try:
        return 2 if search(regexp_dict['screen_name'],input_dict['user']['screen_name'],IGNORECASE) else 0
    except KeyError:
        # tweet is not a tweet, do nothing
        return 0

def check_url(input_dict):
    # return 4 if dict should be filtered
    if not regexp_dict['url']:
        # no checking if regexp is empty
        return 0
    try:
        for url in input_dict['retweeted_status']['entities']['urls']:
            if search(regexp_dict['url'],url['expanded_url'],IGNORECASE):
                return 4
    except KeyError:
        # tweet is not a retweet, go on checking
        pass
    try:
        for url in input_dict['entities']['urls']:
            if search(regexp_dict['url'],url['expanded_url'],IGNORECASE):
                return 4
        return 0
    except KeyError:
        # tweet is not a tweet, do nothing
        return 0

def check_hashtag(input_dict):
    # return 8 if dict should be filtered
    if not regexp_dict['hashtag']:
        # no checking if regexp is empty
        return 0
    try:
        for hashtag in input_dict['retweeted_status']['entities']['hashtags']:
            if search(regexp_dict['hashtag'],hashtag['text'],IGNORECASE):
                return 8
    except KeyError:
        # tweet is not a retweet, go on checking
        pass
    try:
        for hashtag in input_dict['entities']['hashtags']:
            if search(regexp_dict['hashtag'],hashtag['text'],IGNORECASE):
                return 8
        return 0
    except KeyError:
        # tweet is not a tweet, do nothing
        return 0

def check_text(input_dict):
    # return 16 if dict should be filtered
    if not regexp_dict['text']:
        # no checking if regexp is empty
        return 0
    try:
        # only check text in retweeted_status if exists
        return 16 if search(regexp_dict['text'],input_dict['retweeted_status']['text'],IGNORECASE) else 0
    except KeyError:
        # tweet is not a retweet, go on checking
        pass
    try:
        return 16 if search(regexp_dict['text'],input_dict['text'],IGNORECASE) else 0
    except KeyError:
        # tweet is not a tweet, do nothing
        return 0

def genefilter(l):
    while l:
        d=l.pop(0)
        fcode=check_source(d)+check_screen_name(d)+check_url(d)+check_hashtag(d)+check_text(d)
        if fcode:
            try:
                debug(u'Status {0} filtered according to {1}.'.format(d['id_str'],', '.join([s for s in filterrange(fcode)])))
            except:
                pass
            finally:
                del d
        else:
            yield d
