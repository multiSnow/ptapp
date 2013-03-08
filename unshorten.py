#coding:utf-8

import json
from google.appengine.api.urlfetch import fetch
from urlparse import urlparse,urlunparse

BITLY_LOGIN=''
BITLY_PASSWD=''
BITLY_APIKEY=''

def exp_bitly(url_in,text,url_replace,timeout):
    bitly_netloc='api-ssl.bitly.com'
    bitly_path='/v3/expand'
    bitly_query='login={0}&apiKey={1}&shortUrl={2}'.format(BITLY_LOGIN,BITLY_APIKEY,url_in)
    try:
        bitly_respond=fetch(urlunparse(('https',bitly_netloc,bitly_path,'',bitly_query,'')),method='GET',deadline=timeout)
        url_in=json.loads(bitly_respond.content)['data']['expand'][0]['long_url']
    except DownloadError:
        return [url_in,text]
    finally:
        return [url_in,text]

def exp_googl(url_in,text,url_replace,timeout):
    googl_netloc='www.googleapis.com'
    googl_path='/urlshortener/v1/url'
    googl_query='shortUrl={0}'.format(url_in)
    try:
        googl_respond=fetch(urlunparse(('https',googl_netloc,googl_path,'',googl_query,'')),method='GET',deadline=timeout)
        url_in=json.loads(googl_respond.content)['longUrl']
    except DownloadError:
        return [url_in,text]
    finally:
        return [url_in,text]

def exp_isgd(url_in,text,url_replace,timeout):
    isgd_netloc='is.gd'
    isgd_path='/forward.php'
    isgd_query='shorturl={0}&format=json'.format(url_in)
    try:
        isgd_respond=fetch(urlunparse(('http',isgd_netloc,isgd_path,'',isgd_query,'')),method='GET',deadline=timeout)
        url_in=json.loads(isgd_respond.content)['url']
    except DownloadError:
        return [url_in,text]
    finally:
        return [url_in,text]

def exp_instaragm(url_in,text,url_replace,timeout):
    instaragm_netloc='api.instagram.com'
    instaragm_path='/oembed'
    instaragm_query='url={0}'.format(url_in)
    try:
        instaragm_respond=fetch(urlunparse(('https',instaragm_netloc,instaragm_path,'',instaragm_query,'')),method='GET',deadline=timeout)
        url_in=json.loads(instaragm_respond.content)['url']
    except DownloadError:
        return [url_in,text]
    finally:
        return [url_in,text]

def exp_tldg(url_in,text,url_replace,timeout):
    url_id=''
    for string in urlparse(url_in).path.split('/'):
        if string!='' and string!='show':
            url_id=string
    if not url_id:
        return [url_in,text]

    from lxml.objectify import fromstring
    tldg_netloc='www.twitlonger.com'
    tldg_path='/api_read/{0}'.format(url_id)
    try:
        tldg_respond=fetch(urlunparse(('http',tldg_netloc,tldg_path,'','','')),method='GET',deadline=timeout)
        orig_text=fromstring(tldg_respond.content)['post']['content'].text
        new_text=u'({0})『{1}』'.format(url_replace,orig_text)
        text=text.replace(url_replace,new_text)
    except DownloadError:
        return [url_in,text]
    finally:
        return [url_in,text]


exp_func_dict={'/4sq.com/':exp_bitly,
               '/bit.ly/':exp_bitly,
               '/bitly.com/':exp_bitly,
               '/buff.ly/':exp_bitly,
               '/goo.gl/':exp_googl,
               '/instagr.am/':exp_instaragm,
               '/is.gd/':exp_isgd,
               '/j.mp/':exp_bitly,
               '/tl.gd/':exp_tldg,
               '/www.twitlonger.com/show/':exp_tldg}
