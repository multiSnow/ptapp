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

import json
from threading import Thread
from urlparse import urlparse,urlunparse

TIMEOUT=5

before_dict=['img.ly/','twitpic.com/','google.com/']

short_dict=['/4sq.com/',
            '/bit.ly/',
            '/bitly.com/',
            '/buff.ly/',
            '/goo.gl/',
            '/instagr.am/',
            '/is.gd/',
            '/j.mp/',
            '/tl.gd/',
            '/www.twitlonger.com/show/']

def https_wrap(url_in):
    (url_in_scm,url_in_netloc,url_in_path,url_in_params,url_in_query,url_in__)=urlparse(url_in)
    return urlunparse(('https',url_in_netloc,url_in_path,url_in_params,url_in_query,url_in__))

def func_reindices(text,string):
    #locate string in text
    #return [start,end]
    lowered_text=text.lower()
    start=lowered_text.find(string.lower())
    end=start+len(string)
    return [start,end]

def func_replace_tco(text,entit_list):
    #replace t.co in text using urls from entit_list.
    #NOTE: entit_list willl also be modified.
    #
    #url should as below at least:
    #url['url']==t.co_url
    #url['expanded_url']==orig_url
    #url['display_url']==url_to_display
    #
    #url['media_url_https'] will be tested and processed only when exist
    #
    #return [text,extit_list]
    for urls in entit_list:
        if '//t.co/' not in urls['url']:
            continue
        url=urls['url']
        if 'media_url_https' in urls:
            urls['expanded_url']=expanded_url=urls['media_url_https']
        else:
            for url_short in short_dict:
                if url_short in urls['expanded_url']:
                    from unshorten import exp_func_dict
                    [urls['expanded_url'],text]=exp_func_dict[url_short](urls['expanded_url'],text,url,TIMEOUT)
            for url_before in before_dict:
                if url_before in urls['expanded_url']:
                    urls['expanded_url']=https_wrap(urls['expanded_url'])
            expanded_url=urls['expanded_url']
        text=text.replace(url,expanded_url)
        urls['display_url']=urls['url']=expanded_url
    return [text,entit_list]

def func_url_rewrite(status_dict):
    for entry in ['profile_background_image_url','profile_image_url']:
        if entry in status_dict:
            status_dict[entry]=status_dict[entry.replace('image_url','image_url_https')]
        if 'user' in status_dict:
            try:
                status_dict['user'][entry]=status_dict['user'][entry.replace('image_url','image_url_https')]
            finally:
                pass

    if 'user' in status_dict:
        try:
            if status_dict['user']['url']:
                if '//t.co/' in status_dict['user']['url']:
                    [status_dict['user']['url'],status_dict['user']['entities']['url']['urls']]=func_replace_tco(status_dict['user']['url'],status_dict['user']['entities']['url']['urls'])
        finally:
            pass

    if 'user' in status_dict:
        try:
            [status_dict['user']['description'],status_dict['user']['entities']['description']['urls']]=func_replace_tco(status_dict['user']['description'],status_dict['user']['entities']['description']['urls'])
        finally:
            pass

    if 'entities' in status_dict:
        for entities_child in status_dict['entities']:
            if entities_child=='media' or entities_child=='urls':
                [status_dict['text'],status_dict['entities'][entities_child]]=func_replace_tco(status_dict['text'],status_dict['entities'][entities_child])

    if 'entities' in status_dict:
        for entities_child in status_dict['entities']:
            if entities_child=='media' or entities_child=='urls':
                for urls in status_dict['entities'][entities_child]:
                    urls['indices']=func_reindices(status_dict['text'],urls['url'])
            elif entities_child=='user_mentions':
                for user in status_dict['entities'][entities_child]:
                    user['indices']=func_reindices(status_dict['text'],'@{0}'.format(user['screen_name']))
            elif entities_child=='hashtags':
                for user in status_dict['entities'][entities_child]:
                    user['indices']=func_reindices(status_dict['text'],u'#{0}'.format(user['text']))

    return status_dict

def func_write_dict(input_dict):
    input_dict=func_url_rewrite(input_dict)
    return 0

def linkrewriter(content):
    try:
        status_list=json.loads(content);
        if type(status_list)==list:
            mts=[]
            for p in status_list:
                mt=Thread(target=func_write_dict,args=(p,))
                mt.start()
                mts.append(mt)
                if 'retweeted_status' in p:
                    q=p['retweeted_status']
                    nt=Thread(target=func_write_dict,args=(q,))
                    nt.start()
                    mts.append(nt)

            for t in mts:
                t.join()

        elif type(status_list)==dict:
            func_write_dict(status_list)
        else:
            pass

    finally:
        return json.dumps(status_list)
