#coding: utf8
# Project PTAPP
#
# Copyright (c) 2012, multiSnow <infinity.blick.winkel@gmail.com>
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

def check_source(input_dict):
    # no checking if regexp is empty
    if not regexp_dict['source']:
        return 0
    # return 1 if dict should be filtered
    if 'retweeted_status' in input_dict:
        if 'source' in input_dict['retweeted_status']:
            if search(regexp_dict['source'],input_dict['retweeted_status']['source'],IGNORECASE):
                debug(u'Filtered source: {0}'.format(input_dict['retweeted_status']['source']))
                return 1
    else:
        if 'source' in input_dict:
            if search(regexp_dict['source'],input_dict['source'],IGNORECASE):
                debug(u'Filtered source: {0}'.format(input_dict['source']))
                return 1
    return 0

def check_screen_name(input_dict):
    # no checking if regexp is empty
    if not regexp_dict['screen_name']:
        return 0
    # return 1 if dict should be filtered
    if 'retweeted_status' in input_dict:
        if 'user' in input_dict['retweeted_status']:
            if search(regexp_dict['screen_name'],input_dict['retweeted_status']['user']['screen_name'],IGNORECASE):
                debug(u'Filtered source: {0}'.format(input_dict['retweeted_status']['user']['screen_name']))
                return 1
    else:
        if 'user' in input_dict:
            if search(regexp_dict['screen_name'],input_dict['user']['screen_name'],IGNORECASE):
                debug(u'Filtered source: {0}'.format(input_dict['user']['screen_name']))
                return 1
    return 0

def check_url(input_dict):
    # no checking if regexp is empty
    if not regexp_dict['url']:
        return 0
    # return 1 if dict should be filtered
    if 'retweeted_status' in input_dict:
        if 'entities' in input_dict['retweeted_status']:
            for url in input_dict['retweeted_status']['entities']['urls']:
                if search(regexp_dict['url'],url['expanded_url'],IGNORECASE):
                    debug(u'Filtered url: {0}'.format(url['expanded_url']))
                    return 1
    else:
        if 'entities' in input_dict:
            for url in input_dict['entities']['urls']:
                if search(regexp_dict['url'],url['expanded_url'],IGNORECASE):
                    debug(u'Filtered url: {0}'.format(url['expanded_url']))
                    return 1
    return 0

def check_hashtag(input_dict):
    # no checking if regexp is empty
    if not regexp_dict['hashtag']:
        return 0
    # return 1 if dict should be filtered
    if 'retweeted_status' in input_dict:
        if 'entities' in input_dict['retweeted_status']:
            for hashtag in input_dict['retweeted_status']['entities']['hashtags']:
                if search(regexp_dict['hashtag'],hashtag['text'],IGNORECASE):
                    debug(u'Filtered hashtag: {0}'.format(hashtag['text']))
                    return 1
    else:
        if 'entities' in input_dict:
            for hashtag in input_dict['entities']['hashtags']:
                if search(regexp_dict['hashtag'],hashtag['text'],IGNORECASE):
                    debug(u'Filtered hashtag: {0}'.format(hashtag['text']))
                    return 1
    return 0

def check_text(input_dict):
    # no checking if regexp is empty
    if not regexp_dict['text']:
        return 0
    # return 1 if dict should be filtered
    if 'retweeted_status' in input_dict:
        # only check text in retweeted_status if exists
        if 'text' in input_dict['retweeted_status']:
            if search(regexp_dict['text'],input_dict['retweeted_status']['text'],IGNORECASE):
                debug(u'Filtered text: {0}'.format(input_dict['retweeted_status']['text']))
                return 1
            else:
                return 0
    else:
        if 'text' in input_dict:
            if search(regexp_dict['text'],input_dict['text'],IGNORECASE):
                debug(u'Filtered text: {0}'.format(input_dict['text']))
                return 1
    return 0

def checkfilter(input_dict):
    try:
        # return 1 if dict should be filtered
        return 1 if check_source(input_dict)+check_screen_name(input_dict)+check_url(input_dict)+check_hashtag(input_dict)+check_text(input_dict) else 0
    except:
        return 0

def statusfilter(content):
    try:
        status=loads(content);
        if type(status)==list:
            i=0
            while i<len(status):
                if checkfilter(status[i]):
                    status.pop(i)
                else:
                    i+=1
            return dumps(status,separators=(',', ':'))
        else:
            return content
    except:
        info('Twitter respond a non-json string.')
        return content
