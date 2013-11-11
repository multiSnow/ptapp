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

from json import loads
from logging import info
from urllib import urlencode
from urlparse import urlparse,urlunparse
from google.appengine.api.urlfetch import fetch

from config import BITLY_LOGIN,BITLY_APIKEY,TIMEOUT

def geturl(url):
    try:
        respond=fetch(url,method='GET',deadline=TIMEOUT)
        return respond.content
    except:
        info('Error in GET {0}'.format(url))
        return None

def getloc(url):
    try:
        respond=fetch(dict_inurl,method='HEAD',deadline=TIMEOUT)
        return respond.headers['location']
    except:
        info('Error in HEAD {0}'.format(url))
        return None

def exp_bitly(url_in,text,url_replace):
    if not (BITLY_LOGIN and BITLY_APIKEY):
        info('no BITLY_LOGIN and BITLY_APIKEY, do nothing')
        return [url_in,text]
    bitly_netloc='api-ssl.bitly.com'
    bitly_path='/v3/expand'
    bitly_query=urlencode([('login',BITLY_LOGIN),('apiKey',BITLY_APIKEY),('shortUrl',url_in)])
    bitly_respond=geturl(urlunparse(('https',bitly_netloc,bitly_path,'',bitly_query,'')))
    if bitly_respond:
        try:
            url_in=loads(bitly_respond)['data']['expand'][0]['long_url']
        except:
            info('invailid respond from bitly: {0}'.format(bitly_respond))
    return [url_in,text]

def exp_googl(url_in,text,url_replace):
    googl_netloc='www.googleapis.com'
    googl_path='/urlshortener/v1/url'
    googl_query=urlencode([('shortUrl',url_in)])
    googl_respond=geturl(urlunparse(('https',googl_netloc,googl_path,'',googl_query,'')))
    if googl_respond:
        try:
            url_in=loads(googl_respond)['longUrl']
        except:
            info('invailid respond from googl: {0}'.format(googl_respond))
    return [url_in,text]

def exp_isgd(url_in,text,url_replace):
    isgd_netloc='is.gd'
    isgd_path='/forward.php'
    isgd_query=urlencode([('shorturl',url_in),('format','json')])
    isgd_respond=geturl(urlunparse(('http',isgd_netloc,isgd_path,'',isgd_query,'')))
    if isgd_respond:
        try:
            url_in=loads(isgd_respond)['url']
        except:
            info('invailid respond from isgd: {0}'.format(isgd_respond))
    return [url_in,text]

def exp_instaragm(url_in,text,url_replace):
    instaragm_netloc='api.instagram.com'
    instaragm_path='/oembed'
    instaragm_query='url={0}'.format(url_in)
    instaragm_respond=geturl(urlunparse(('https',instaragm_netloc,instaragm_path,'',instaragm_query,'')))
    if instaragm_respond:
        try:
            url_in=loads(instaragm_respond)['url']
        except:
            info('invailid respond from instaragm: {0}'.format(instaragm_respond))
    return [url_in,text]

def exp_tldg(url_in,text,url_replace):
    p=urlparse(url_in)
    try:
        if p.hostname=='www.twitlonger.com':
            url_id=p.path.split('/')[2] if p.path.startswith('/show/') else None
        elif p.hostname=='tl.gd':
            url_id=p.path.split('/')[1]
        else:
            url_id=None
    except:
        url_id=None
    if not url_id:
        return [url_in,text]

    from lxml.objectify import fromstring
    tldg_netloc='www.twitlonger.com'
    tldg_path='/api_read/{0}'.format(url_id)
    tldg_respond=geturl(urlunparse(('http',tldg_netloc,tldg_path,'','','')))
    if tldg_respond:
        try:
            orig_text=fromstring(tldg_respond)['post']['content'].text
            new_text=u'({0})『{1}』'.format(url_replace,orig_text)
            text=text.replace(url_replace,new_text)
        except:
            info('invailid respond from tldg: {0}'.format(tldg_respond))
    return [url_in,text]

def exp_imgly(url_in,text,url_replace):
    url_id=''
    for string in urlparse(url_in).path.split('/'):
        if string!='':
            url_id=string
    if not url_id:
        return [url_in,text]

    imgly_netloc='img.ly'
    imgly_path='/show/full/{0}'.format(url_id)
    imgly_respond=getloc(urlunparse(('https',imgly_netloc,imgly_path,'','','')))
    if imgly_respond:
        url_in=imgly_respond
    return [url_in,text]

exp_func_dict={'4sq.com':exp_bitly,
               'bit.ly':exp_bitly,
               'bitly.com':exp_bitly,
               'buff.ly':exp_bitly,
               'goo.gl':exp_googl,
               'img.ly':exp_imgly,
               'instagr.am':exp_instaragm,
               'instagram.com':exp_instaragm,
               'is.gd':exp_isgd,
               'j.mp':exp_bitly,
               'tl.gd':exp_tldg,
               'www.twitlonger.com':exp_tldg}
