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
from threading import Thread
from urllib import urlencode
from urlparse import urlparse,urlunparse,parse_qsl

from config import DOMAIN_TO_HTTPS,EXP_SHORTURL,UNWANTED_QUERY_KEYS
if EXP_SHORTURL==1:
    from unshorten import exp_func_dict
else:
    exp_func_dict=dict()

entites_fulldict={'media':[u'','url'],
                  'urls':[u'','url'],
                  'user_mentions':[u'@','screen_name'],
                  'hashtags':[u'#','text'],
                  'symbols':[u'$','text']}

def urlpp(url_in):
    parse_result=urlparse(url_in)
    for host in DOMAIN_TO_HTTPS:
        if parse_result.netloc.lower().endswith(host):
            parse_result=parse_result._replace(scheme='https')
            break
    newquery_list,delquery_list=[],[]
    for k,v in parse_qsl(parse_result.query):
        if k in UNWANTED_QUERY_KEYS:delquery_list.append((k,v))
        else:newquery_list.append((k,v))
    if delquery_list:
        parse_result=parse_result._replace(query=urlencode(newquery_list))
        debug(u'remove {0} from {1}'.format(urlencode(delquery_list),url_in))
    return urlunparse(parse_result)

def func_reindices(text,string):
    # locate string in text
    # return [start,end]

    fallback_dict={u'@':u'＠',
                   u'#':u'＃'}
    lowered_text=text.lower()
    start=0
    try:
        start=lowered_text.index(string.lower())
    except ValueError:
        try:start=lowered_text.index((fallback_dict[string[0]]+string[1:]).lower())
        except ValueError:raise KeyError
    end=start+len(string)
    return [start,end]

def func_replace_tco(text,entit_list):
    # replace t.co in text using urls from entit_list.
    # NOTE: entit_list will also be modified.
    # 
    # urls should as below at least:
    # urls['url']==t.co_url
    # urls['expanded_url']==orig_url
    # urls['display_url']==url_to_display
    # 
    # urls['media_url_https'] will be tested and processed only when exist
    # 
    # return [text,extit_list]

    repld={}
    for urls in entit_list:
        if urlparse(urls['url']).hostname!='t.co':continue
        url=urls['url']
        if 'video_info' in urls and 'variants' in urls['video_info']:
            ct,br=None,-1
            for video in urls['video_info']['variants']:
                if not ct:
                    ct=video['content_type']
                    expanded_url=video['url']
                    if 'bitrate' in video:br=video['bitrate']
                elif 'bitrate' in video and video['bitrate']>br:
                    ct=video['content_type']
                    expanded_url=video['url']
                    br=video['bitrate']
            urls['expanded_url']=expanded_url
        else:
            try:urls['expanded_url']=expanded_url=urls['media_url_https']
            except KeyError:
                try:[urls['expanded_url'],text]=exp_func_dict[urlparse(urls['expanded_url']).hostname](urls['expanded_url'],text,url)
                except KeyError:pass
                urls['expanded_url']=urlpp(urls['expanded_url'])
                expanded_url=urls['expanded_url']
        urls['display_url']=urls['url']=expanded_url
        if url not in repld:repld[url]=[]
        repld[url].append(expanded_url)
    for k,v in repld.items():
        text=text.replace(k,' '.join(v))
    return [text,entit_list]

def func_url_rewrite(status_dict):
    for entry in ['profile_background_image_url','profile_image_url']:
        try:
            status_dict[entry]=status_dict[entry.replace('image_url','image_url_https')]
        except KeyError:
            pass
        try:
            status_dict['user'][entry]=status_dict['user'][entry.replace('image_url','image_url_https')]
        except KeyError:
            pass

    for entry in ['url','description']:
        try:
            [status_dict['user'][entry],status_dict['user']['entities'][entry]['urls']]=func_replace_tco(status_dict['user'][entry],status_dict['user']['entities'][entry]['urls'])
            for key in status_dict['user']['entities'][entry]['urls']:
                key['indices']=func_reindices(status_dict['user'][entry],(entites_fulldict['urls'][0]+key[entites_fulldict['urls'][1]]))
        except KeyError:
            pass

    if 'extended_entities' in status_dict:
        try:[status_dict['text'],status_dict['extended_entities']['media']]=func_replace_tco(status_dict['text'],status_dict['extended_entities']['media'])
        except KeyError:pass
    else:
        try:[status_dict['text'],status_dict['entities']['media']]=func_replace_tco(status_dict['text'],status_dict['entities']['media'])
        except KeyError:pass

    try:[status_dict['text'],status_dict['entities']['urls']]=func_replace_tco(status_dict['text'],status_dict['entities']['urls'])
    except KeyError:pass
    try:
        for entry in status_dict['entities']:
            for key in status_dict['entities'][entry]:
                key['indices']=func_reindices(status_dict['text'],u'{0}{1}'.format(entites_fulldict[entry][0],key[entites_fulldict[entry][1]]))
    except KeyError:pass
    try:
        for entry in status_dict['extended_entities']:
            for key in status_dict['extended_entities'][entry]:
                key['indices']=func_reindices(status_dict['text'],u'{0}{1}'.format(entites_fulldict[entry][0],key[entites_fulldict[entry][1]]))
    except KeyError:pass

    return

def func_write_dict(input_dict):
    func_url_rewrite(input_dict)
