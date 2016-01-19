#coding: utf8
# Project PTAPP
#
# Copyright (c) 2014 - 2016 , multiSnow <infinity.blick.winkel@gmail.com>
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

from time import time
from urllib import quote as urlquote,quote_plus as urlquote_plus,unquote as urlunquote
from urlparse import urlparse,urlunparse,parse_qsl

from Crypto.Hash import SHA as sha1
from Crypto.Hash.HMAC import new as hmac
from Crypto.Random.random import choice

from google.appengine.api import urlfetch

seqstr='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

class OAuthClient():

    def __init__(self,service_name,consumer_key,consumer_secret,request_url,access_url,callback_url=None):
        self.service_name=service_name
        self.consumer_key=consumer_key
        self.consumer_secret=consumer_secret
        self.request_url=request_url
        self.access_url=access_url
        self.callback_url=callback_url

    def prepare_request(self,url,token=None,secret='',additional_params={},method='GET'):
        encode=lambda t:urlquote(str(t),'')
        urlquh=lambda t:urlquote(str(t),'~')

        params={'oauth_consumer_key':self.consumer_key,
                'oauth_signature_method':'HMAC-SHA1',
                'oauth_timestamp':str(int(time())),
                'oauth_nonce':''.join(list(choice(seqstr) for i in xrange(64))),
                'oauth_version':'1.0'}

        if token:
            params['oauth_token']=token
        elif self.callback_url:
            params['oauth_callback']=self.callback_url

        params.update(additional_params)
        for k,v in params.iteritems():
            if isinstance(v,unicode):
                params[k]=v.encode('utf8')

        params_str='&'.join([encode(k)+'='+urlquh(v) for k,v in sorted(params.iteritems())])
        params['oauth_signature']=hmac('&'.join([self.consumer_secret,secret]),
                                       '&'.join([method,encode(url),urlquh(params_str)]),
                                       sha1).digest().encode('base64').strip()
        return '&'.join([urlquote_plus(str(k),'~')+'='+urlquote_plus(str(v),'~') for k,v in sorted(params.iteritems())])

    def make_async_request(self,url,token='',secret='',additional_params=None,protected=False,method='GET'):
        urlpr=urlparse(url)
        additional_params.update(dict((k,v) for k,v in parse_qsl(urlpr.query)))
        url=urlunparse(urlpr._replace(scheme='https',query=None,fragment=None))

        payload=self.prepare_request(url,token,secret,additional_params,method)

        if method=='GET':
            url=urlunparse(urlpr._replace(scheme='https',query=payload,fragment=None))
            payload=None
        headers={'Authorization':'OAuth'} if protected else {}

        rpc=urlfetch.create_rpc(deadline=3)
        urlfetch.make_fetch_call(rpc,url,method=method,headers=headers,payload=payload)
        return rpc

    def make_request(self,url,token='',secret='',additional_params=None,protected=False,method='GET'):
        return self.make_async_request(url,token,secret,additional_params,protected,method).get_result()

class TwitterClient(OAuthClient):

    def __init__(self,consumer_key,consumer_secret,callback_url):
        OAuthClient.__init__(self,
                             'twitter',
                             consumer_key,
                             consumer_secret,
                             'https://api.twitter.com/oauth/request_token',
                             'https://api.twitter.com/oauth/access_token',
                             callback_url)
