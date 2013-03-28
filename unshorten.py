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
from logging import info
from threading import Thread
from urlparse import urlparse,urlunparse
from google.appengine.api.urlfetch import fetch

from config import BITLY_LOGIN,BITLY_APIKEY,TIMEOUT

def geturl(url):
    def fetch_to_dict(dict_in):
        respond=fetch(dict_in['url'],method='GET')
        dict_in['text']=respond.content
        return 0

    dict_req=dict(url=url,text=None)
    mt=Thread(target=fetch_to_dict,args=(dict_req,))
    mt.daemon=True
    mt.start()
    mt.join(TIMEOUT)
    if mt.isAlive():
        info('Timeout in require {0}'.format(urlparse(url).netloc))
    return dict_req['text']

def getloc(url):
    def header_to_dict(dict_in):
        respond=fetch(dict_in['url'],method='HEAD',follow_redirects=False)
        dict_in['text']=respond.headers['location']
        return 0

    dict_req=dict(url=url,text=None)
    mt=Thread(target=header_to_dict,args=(dict_req,))
    mt.daemon=True
    mt.start()
    mt.join(TIMEOUT)
    if mt.isAlive():
        info('Timeout in require {0}'.format(urlparse(url).netloc))
    return dict_req['text']

def exp_bitly(url_in,text,url_replace):
    bitly_netloc='api-ssl.bitly.com'
    bitly_path='/v3/expand'
    bitly_query='login={0}&apiKey={1}&shortUrl={2}'.format(BITLY_LOGIN,BITLY_APIKEY,url_in)
    bitly_respond=geturl(urlunparse(('https',bitly_netloc,bitly_path,'',bitly_query,'')))
    if bitly_respond:
        url_in=json.loads(bitly_respond)['data']['expand'][0]['long_url']
    return [url_in,text]

def exp_googl(url_in,text,url_replace):
    googl_netloc='www.googleapis.com'
    googl_path='/urlshortener/v1/url'
    googl_query='shortUrl={0}'.format(url_in)
    googl_respond=geturl(urlunparse(('https',googl_netloc,googl_path,'',googl_query,'')))
    if googl_respond:
        url_in=json.loads(googl_respond)['longUrl']
    return [url_in,text]

def exp_isgd(url_in,text,url_replace):
    isgd_netloc='is.gd'
    isgd_path='/forward.php'
    isgd_query='shorturl={0}&format=json'.format(url_in)
    isgd_respond=geturl(urlunparse(('http',isgd_netloc,isgd_path,'',isgd_query,'')))
    if isgd_respond:
        url_in=json.loads(isgd_respond)['url']
    return [url_in,text]

def exp_instaragm(url_in,text,url_replace):
    instaragm_netloc='api.instagram.com'
    instaragm_path='/oembed'
    instaragm_query='url={0}'.format(url_in)
    instaragm_respond=geturl(urlunparse(('https',instaragm_netloc,instaragm_path,'',instaragm_query,'')))
    if instaragm_respond:
        url_in=json.loads(instaragm_respond)['url']
    return [url_in,text]

def exp_tldg(url_in,text,url_replace):
    url_id=''
    for string in urlparse(url_in).path.split('/'):
        if string!='' and string!='show':
            url_id=string
    if not url_id:
        return [url_in,text]

    from lxml.objectify import fromstring
    tldg_netloc='www.twitlonger.com'
    tldg_path='/api_read/{0}'.format(url_id)
    tldg_respond=geturl(urlunparse(('http',tldg_netloc,tldg_path,'','','')))
    if tldg_respond:
        orig_text=fromstring(tldg_respond)['post']['content'].text
        new_text=u'({0})『{1}』'.format(url_replace,orig_text)
        text=text.replace(url_replace,new_text)
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

exp_func_dict={'/4sq.com/':exp_bitly,
               '/bit.ly/':exp_bitly,
               '/bitly.com/':exp_bitly,
               '/buff.ly/':exp_bitly,
               '/goo.gl/':exp_googl,
               '/img.ly/':exp_imgly,
               '/instagr.am/':exp_instaragm,
               '/instagram.com/':exp_instaragm,
               '/is.gd/':exp_isgd,
               '/j.mp/':exp_bitly,
               '/tl.gd/':exp_tldg,
               '/www.twitlonger.com/show/':exp_tldg}
