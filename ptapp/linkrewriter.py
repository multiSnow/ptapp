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
from logging import info
from threading import Thread
from urllib import urlencode
from urlparse import urlparse,urlunparse,parse_qsl

from config import DOMAIN_TO_HTTPS,EXP_SHORTURL,UNWANTED_QUERY_KEYS
if EXP_SHORTURL==1:
    from unshorten import exp_func_dict
else:
    exp_func_dict=dict()

def urlpp(url_in):
    (url_in_scm,url_in_netloc,url_in_path,url_in_params,url_in_query,url_in_fragment)=urlparse(url_in)
    for host in DOMAIN_TO_HTTPS:
        if url_in_netloc.lower().endswith(host):
            url_in_scm='https'
            break
    newquery_list=[]
    for k,v in parse_qsl(url_in_query):
        if k in UNWANTED_QUERY_KEYS:
            info('remove {0} from {1}'.format(urlencode([(k,v)]),url_in))
        else:
            newquery_list.append((k,v))
    return urlunparse((url_in_scm,url_in_netloc,url_in_path,url_in_params,urlencode(newquery_list),url_in_fragment))

def func_reindices(text,string):
    # locate string in text
    # return [start,end]

    fallback_dict={u'@':u'＠',
                   u'#':u'＃'}
    lowered_text=text.lower()
    try:
        start=lowered_text.index(string.lower())
    except ValueError:
        start=lowered_text.index(u'{0}{1}'.format(fallback_dict[string[0]],string.lower()[1:]))
    end=start+len(string)
    return [start,end]

def func_replace_tco(text,entit_list):
    # replace t.co in text using urls from entit_list.
    # NOTE: entit_list willl also be modified.
    # 
    # url should as below at least:
    # url['url']==t.co_url
    # url['expanded_url']==orig_url
    # url['display_url']==url_to_display
    # 
    # url['media_url_https'] will be tested and processed only when exist
    # 
    # return [text,extit_list]

    for urls in entit_list:
        if urlparse(urls['url']).hostname!='t.co':
            continue
        url=urls['url']
        if 'media_url_https' in urls:
            urls['expanded_url']=expanded_url=urls['media_url_https']
        else:
            if urlparse(urls['expanded_url']).hostname in exp_func_dict:
                [urls['expanded_url'],text]=exp_func_dict[urlparse(urls['expanded_url']).hostname](urls['expanded_url'],text,url)
            urls['expanded_url']=urlpp(urls['expanded_url'])
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
            except:
                info('Error in force https profile image.')
                pass

    if 'user' in status_dict:
        if 'entities' in status_dict['user']:
            for entry in ['url','description']:
                try:
                    if urlparse(status_dict['user']['url']).hostname=='t.co':
                        [status_dict['user'][entry],status_dict['user']['entities'][entry]['urls']]=func_replace_tco(status_dict['user'][entry],status_dict['user']['entities'][entry]['urls'])
                        for entities_entry in status_dict['user'][entry]:
                            entities_entry['indices']=func_reindices(status_dict['user'][entry],entities_entry['url'])
                except:
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
                    user['indices']=func_reindices(status_dict['text'],u'@{0}'.format(user['screen_name']))
            elif entities_child=='hashtags':
                for hashtag in status_dict['entities'][entities_child]:
                    hashtag['indices']=func_reindices(status_dict['text'],u'#{0}'.format(hashtag['text']))
            elif entities_child=='symbols':
                for symbols in status_dict['entities'][entities_child]:
                    symbols['indices']=func_reindices(status_dict['text'],u'${0}'.format(symbols['text']))

    return status_dict

def func_write_dict(input_dict):
    input_dict=func_url_rewrite(input_dict)
    return 0

def linkrewriter(content):
    try:
        status_list=loads(content);
        if type(status_list)==list:
            thread_list=[]
            for status in status_list:
                mt=Thread(target=func_write_dict,args=(status,))
                mt.start()
                thread_list.append(mt)
                if 'retweeted_status' in status:
                    nt=Thread(target=func_write_dict,args=(status['retweeted_status'],))
                    nt.start()
                    thread_list.append(nt)

            for threads in thread_list:
                threads.join()
            return dumps(status_list)
        elif type(status_list)==dict:
            func_write_dict(status_list)
            return dumps(status_list)
        else:
            return content

    except:
        info('Twitter respond a non-json string.')
        return content
