#coding: utf8
# Project PTAPP
#
# Copyright (c) 2014 - 2017 , multiSnow <infinity.blick.winkel@gmail.com>
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
from threading import Thread
from urllib import urlencode
from urlparse import urlparse,urlunparse,parse_qsl

from config import DOMAIN_TO_HTTPS,EXP_SHORTURL,UNWANTED_QUERY_KEYS
if EXP_SHORTURL==1:
    from unshorten import exp_func_dict
else:
    exp_func_dict=dict()

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
        debug(u'remove {} from {}'.format(urlencode(delquery_list),url_in))
    return urlunparse(parse_result)

def func_reindices(text,string):
    # locate string in text
    # return [start,end]
    start=0
    try:start=text.lower().index(string.lower())
    except ValueError:info(u'failed reindices: {}, {}'.format(text,string))
    end=start+len(string)
    return start,end

def func_entities_hashtags(text,entitl,stlist=[]):
    text=text.replace(u'＃',u'#')
    for hashtags in entitl:
        stlist.append((u'#{}'.format(hashtags['text']),hashtags))
    return text

def func_entities_symbols(text,entitl,stlist=[]):
    for symbols in entitl:
        stlist.append((u'${}'.format(symbols['text']),symbols))
    return text

def func_entities_urls(text,entitl,stlist=[]):
    for url in entitl:
        if urlparse(url['url']).hostname!='t.co':continue
        origurl=url['url']
        try:expanded_url,text=exp_func_dict[urlparse(url['expanded_url']).hostname](url['expanded_url'],text,origurl)
        except KeyError:expanded_url=url['expanded_url']
        expanded_url=urlpp(expanded_url)
        url['display_url']=url['expanded_url']=url['url']=expanded_url
        text=text.replace(origurl,expanded_url)
    for url in entitl:
        stlist.append((url['expanded_url'],url))
    return text

def func_entities_user_mentions(text,entitl,stlist=[]):
    text=text.replace(u'＠',u'@')
    for user_mentions in entitl:
        stlist.append((u'@{}'.format(user_mentions['screen_name']),user_mentions))
    return text

def func_entit_media(text,media,stlist=[]):
    realurl=media['media_url_https']
    stlist.append((realurl,media))
    text=text.replace(media['url'],realurl)
    media.update(display_url=realurl,
                 expanded_url=realurl,
                 media_url=realurl,
                 media_url_https=realurl,
                 url=realurl)
    return text

def func_entities_media(text,entitl,stlist=[]):
    for media in entitl:
        text=func_entit_media(text,media,stlist=stlist)
    return text

def func_extend_media_photo(media,stlist=[]):
    realurl=media['media_url_https']
    media.update(display_url=realurl,
                 expanded_url=realurl,
                 media_url=realurl,
                 url=realurl)
    stlist.append((realurl,media))

def func_extend_media_video(media,stlist=[]):
    ct,br,realurl=None,-1,None
    for video in media['video_info']['variants']:
        if 'bitrate' not in video:continue
        if video['bitrate']>br:
            ct=video['content_type']
            br=video['bitrate']
            realurl=video['url']
    media.update(display_url=realurl,
                 expanded_url=realurl,
                 media_url=media['media_url_https'],
                 url=realurl)
    stlist.append((realurl,media))

def func_extend_media(text,entitl,extentitl,stlist=[]):
    urld,urll,c={},[],0
    for media in extentitl:
        origurl=media['url']
        func=func_extend_media_photo if 'photo' in media['type'] else func_extend_media_video
        func(media,stlist=stlist)
        if origurl not in urld:urld[origurl]=[]
        urld[origurl].append({k:media[k] for k in ('id','id_str','media_url',
                                                   'media_url_https','url',
                                                   'display_url','expanded_url',
                                                   'sizes','type','indices',)})
    while c<len(entitl):
        origurl=entitl[c]['url']
        if origurl not in urld:
            text=func_entit_media(text,entitl[c],stlist=stlist)
            c+=1
            continue
        if not urld[origurl]:raise KeyError(entitl[c]['url'])
        entitl[c:c+1]=urld[origurl]
        c+=len(urld[origurl])
        urll.append((origurl,[m['expanded_url'] for m in urld[origurl]]))
        stlist.extend([(m['expanded_url'],m) for m in urld[origurl]])
    for ourl,nurls in urll:
        text=text.replace(ourl,' '.join(nurls))
    return text

entites_funcdict={'hashtags':func_entities_hashtags,
                  'symbols':func_entities_symbols,
                  'urls':func_entities_urls,
                  'user_mentions':func_entities_user_mentions,}

def func_entities(text,entitl,etype,stlist=[]):
    # replace t.co in text using entities.
    # entitl edited in-place.
    # return text
    return entites_funcdict[etype](text,entitl,stlist=stlist) if etype in entites_funcdict else text

def func_profile_image(status_dict,entry,idstr):
    status_dict[entry]=status_dict[entry.replace('image_url','image_url_https')]

def func_user_link(user_dict,entry,idstr):
    ustlist=[]
    user_dict[entry]=func_entities(user_dict[entry],
                                   user_dict['entities'][entry]['urls'],
                                   'urls',
                                   stlist=ustlist)
    for s,t in ustlist:
        if 'indices' not in t:raise KeyError(s)
        t['indices']=func_reindices(user_dict[entry],s)

def func_url_rewrite(status_dict):

    textkey='full_text' if 'full_text' in status_dict else 'text'

    for entry in ('profile_background_image_url','profile_image_url'):
        if entry in status_dict:func_profile_image(status_dict,entry,status_dict['id_str'])
        if entry in status_dict.setdefault('user',{}):func_profile_image(status_dict['user'],entry,status_dict['id_str'])

    for entry in ('url','description'):
        if entry in status_dict['user'] and status_dict['user'][entry]:func_user_link(status_dict['user'],entry,status_dict['id_str'])

    sstlist=[]

    if 'extended_entities' in status_dict:
        status_dict[textkey]=func_extend_media(status_dict[textkey],
                                               status_dict['entities']['media'],
                                               status_dict['extended_entities']['media'],
                                               stlist=sstlist)
    elif 'media' in status_dict.setdefault('entities',dict(hashtags=[],symbols=[],user_mentions=[],urls=[])):
        status_dict[textkey]=func_entities_media(status_dict[textkey],
                                                 status_dict['entities']['media'],
                                                 stlist=sstlist)

    for entry in ('urls','hashtags','user_mentions','symbols'):
        status_dict[textkey]=func_entities(status_dict[textkey],status_dict['entities'][entry],entry,stlist=sstlist)
    for s,t in sstlist:
        if 'indices' not in t:raise KeyError(s)
        t['indices']=func_reindices(status_dict[textkey],s)

    status_dict['possibly_sensitive_appealable']=status_dict['possibly_sensitive']=False
    if textkey!='text':status_dict['text']=status_dict[textkey]
    status_dict.pop('display_text_range',None)

    return

def func_write_dict(input_dict):
    textkey='full_text' if 'full_text' in input_dict else 'text'
    if 'retweeted_status' in input_dict:
        func_write_dict(input_dict['retweeted_status'])
        input_dict[textkey]=u'♺ @{} {}'.format(input_dict['retweeted_status']['user']['screen_name'],input_dict['retweeted_status'][textkey])
    if 'quoted_status' in input_dict:
        func_write_dict(input_dict['quoted_status'])
        input_dict[textkey]=u'{} 『({}) {}』'.format(input_dict[textkey],input_dict['quoted_status']['user']['screen_name'],input_dict['quoted_status'][textkey])
    func_url_rewrite(input_dict)
