#coding: utf8

import urlparse,json
from threading import Thread
from google.appengine.api import urlfetch

API_IMPROVE_HTTPS_IMG=1
API_IMPROVE_LINK=1

API_IMPROVE_EXP_SHORTURL=1

API_IMPROVE_FULL_EXP_SHORTURL=0

BITLY_LOGIN=''
BITLY_APIKEY=''

EXP_SHORTURL_TIMEOUT=1

def exp_googl(url_in):
    googl_netloc='www.googleapis.com'
    googl_path='/urlshortener/v1/url'
    googl_query='shortUrl=%s'%url_in
    try:
        googl_obj=urlfetch.fetch(urlparse.urlunparse(('https',googl_netloc,googl_path,'',googl_query,'')),method='GET',deadline=EXP_SHORTURL_TIMEOUT)
        url_in=json.loads(googl_obj.content)['longUrl']
    except DownloadError:
        return url_in
    finally:
        return url_in

def exp_bitly(url_in):
    bitly_netloc='api-ssl.bitly.com'
    bitly_path='/v3/expand'
    bitly_query='login=%s&apiKey=%s&shortUrl=%s'%(BITLY_LOGIN,BITLY_APIKEY,url_in)
    try:
        bitly_obj=urlfetch.fetch(urlparse.urlunparse(('https',bitly_netloc,bitly_path,'',bitly_query,'')),method='GET',deadline=EXP_SHORTURL_TIMEOUT)
        url_in=json.loads(bitly_obj.content)['data']['expand'][0]['long_url']
    except DownloadError:
        return url_in
    finally:
        return url_in

def exp_isgd(url_in):
    isgd_netloc='is.gd'
    isgd_path='/forward.php'
    isgd_query='shorturl=%s&format=json'%url_in
    try:
        isgd_obj=urlfetch.fetch(urlparse.urlunparse(('http',isgd_netloc,isgd_path,'',isgd_query,'')),method='GET',deadline=EXP_SHORTURL_TIMEOUT)
        url_in=json.loads(isgd_obj.content)['url']
    except DownloadError:
        return url_in
    finally:
        return url_in

def exp_common(url_in):
    try:
        commonurl_obj=urlfetch.fetch(url_in,method='GET',follow_redirects=False,deadline=EXP_SHORTURL_TIMEOUT)
        url_in=commonurl_obj.headers['location']
    except DownloadError:
        return url_in
    finally:
        return url_in

def https_wrap(url_in):
    (url_in_scm,url_in_netloc,url_in_path,url_in_params,url_in_query,url_in__)=urlparse.urlparse(url_in)
    return urlparse.urlunparse(('https',url_in_netloc,url_in_path,url_in_params,url_in_query,url_in__))

def https_profile_image(input_obj):
    if 'profile_image_url' in input_obj:
        input_obj['profile_image_url']=input_obj['profile_image_url_https']
        input_obj['profile_background_image_url']=input_obj['profile_background_image_url_https']
    if 'recipient' in input_obj:
        if 'profile_image_url' in input_obj['recipient']:
            input_obj['recipient']['profile_image_url']=input_obj['recipient']['profile_image_url_https']
            input_obj['recipient']['profile_background_image_url']=input_obj['recipient']['profile_background_image_url_https']
    if 'sender' in input_obj:
        if 'profile_image_url' in input_obj['sender']:
            input_obj['sender']['profile_image_url']=input_obj['sender']['profile_image_url_https']
            input_obj['sender']['profile_background_image_url']=input_obj['sender']['profile_background_image_url_https']
    if 'user' in input_obj:
        if 'profile_image_url' in input_obj['user']:
            input_obj['user']['profile_image_url']=input_obj['user']['profile_image_url_https']
            input_obj['user']['profile_background_image_url']=input_obj['user']['profile_background_image_url_https']
    if 'retweeted_status' in input_obj:
        if 'profile_image_url' in input_obj['retweeted_status']['user']:
            input_obj['retweeted_status']['user']['profile_image_url']=input_obj['retweeted_status']['user']['profile_image_url_https']
            input_obj['retweeted_status']['user']['profile_background_image_url']=input_obj['retweeted_status']['user']['profile_background_image_url_https']
    return 0

def process_url(tco_expanded_urls):
    (_,tco_expanded_netloc,_,_,_,_)=urlparse.urlparse(tco_expanded_urls['expanded_url'])
    if API_IMPROVE_EXP_SHORTURL==1:
        if API_IMPROVE_FULL_EXP_SHORTURL==1:
            while tco_expanded_netloc in origurl_dict:
                exp_func=origurl_dict[tco_expanded_netloc]
                tco_expanded_urls['expanded_url']=exp_func(tco_expanded_urls['expanded_url'])
                (_,tco_expanded_netloc,_,_,_,_)=urlparse.urlparse(tco_expanded_urls['expanded_url'])
        else:
            if tco_expanded_netloc in origurl_dict:
                exp_func=origurl_dict[tco_expanded_netloc]
                tco_expanded_urls['expanded_url']=exp_func(tco_expanded_urls['expanded_url'])
    if tco_expanded_netloc in insecurl_dict:
        sec_func=insecurl_dict[tco_expanded_netloc]
        tco_expanded_urls['expanded_url']=sec_func(tco_expanded_urls['expanded_url'])
    tco_expanded_urls['display_url']=tco_expanded_urls['expanded_url']
    return 0

def process_media(media_urls):
    media_urls['media_url']=media_urls['media_url_https']
    media_urls['expanded_url']=media_urls['media_url_https']
    media_urls['display_url']=media_urls['media_url_https']
    return 0

def identify_url(input_obj):
    if API_IMPROVE_LINK==1:
        if 'entities' in input_obj:
            if 'urls' in input_obj['entities']:
                for i in range(len(input_obj['entities']['urls'])):
                    mt=Thread(target=process_url,args=(input_obj['entities']['urls'][i],))
                    mt.start()
            if 'media' in input_obj['entities']:
                for i in range(len(input_obj['entities']['media'])):
                    mt=Thread(target=process_media,args=(input_obj['entities']['media'][i],))
                    mt.start()
        if 'retweeted_status' in input_obj:
            if 'entities' in input_obj['retweeted_status']:
                if 'urls' in input_obj['retweeted_status']['entities']:
                    for i in range(len(input_obj['retweeted_status']['entities']['urls'])):
                        mt=Thread(target=process_url,args=(input_obj['retweeted_status']['entities']['urls'][i],))
                        mt.start()
                if 'media' in input_obj['retweeted_status']['entities']:
                    for i in range(len(input_obj['retweeted_status']['entities']['media'])):
                        mt=Thread(target=process_media,args=(input_obj['retweeted_status']['entities']['media'][i],))
                        mt.start()
        if 'status' in input_obj:
            if 'entities' in input_obj['status']:
                if 'urls' in input_obj['status']['entities']:
                    for i in range(len(input_obj['status']['entities']['urls'])):
                        mt=Thread(target=process_url,args=(input_obj['status']['entities']['urls'][i],))
                        mt.start()
                if 'media' in input_obj['status']['entities']:
                    for i in range(len(input_obj['status']['entities']['media'])):
                        mt=Thread(target=process_media,args=(input_obj['status']['entities']['media'][i],))
                        mt.start()
    return 0

def api_improve(content):
    obj_in=json.loads(content)
    if API_IMPROVE_HTTPS_IMG==1:
        if isinstance(obj_in,list):
            for i in range(len(obj_in)):
                mt=Thread(target=https_profile_image,args=(obj_in[i],))
                mt.start()
        else:
            https_profile_image(obj_in)
    if API_IMPROVE_LINK==1:
        if isinstance(obj_in,list):
            for i in range(len(obj_in)):
                mt=Thread(target=identify_url,args=(obj_in[i],))
                mt.start()
        else:
            identify_url(obj_in)
    content=json.dumps(obj_in)
    return content

origurl_dict={'goo.gl':exp_googl,
              'bit.ly':exp_bitly,
              'bitly.com':exp_bitly,
              'j.mp':exp_bitly,
              '4sq.com':exp_bitly,
              'is.gd':exp_isgd,
              'tinyurl.com':exp_common,
              'gobrcm.com':exp_common,
              'instagr.am':exp_common,
              'db.tt':exp_common,
              't.cn':exp_common}

insecurl_dict={'img.ly':https_wrap,
               'twitpic.com':https_wrap}
