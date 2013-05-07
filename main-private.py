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

from webapp2 import RequestHandler,WSGIApplication
from logging import debug
from cgi import parse_qsl
from google.appengine.api import urlfetch
from urlparse import urlparse,urlunparse
from oauth import TwitterClient

from config import CONSUMER_KEY,CONSUMER_SECRET,SCREEN_NAME,ACCESS_TOKEN,ACCESS_TOKEN_SECRET,USER_PASSWORD,API_IMPROVE,FILTER

ptapp_message='''
<html><head>
<meta http-equiv="content-type" content="text/html;charset=utf-8">
<title>404 Not Found</title>
</head>
<body text=#000000 bgcolor=#ffffff>
<h1>Error: Not Found</h1>
<h2>The requested URL <code>{0}</code> was not found on this server.</h2>
<h2></h2>
</body></html>'''

class MainPage(RequestHandler):

    def conver_url(self,orig_url):
        (scm,netloc,path,params,query,_)=urlparse(orig_url)
        
        path_parts=path.split('/')

        if path_parts[2]=='api':
            path_parts=path_parts[3:]
            path_parts.insert(0,'/')
            new_path='/{0}'.format('/'.join(path_parts[1:]).replace('//','/'))
            new_netloc='api.twitter.com'
        elif path_parts[2]=='searchapi':
            path_parts=path_parts[3:]
            path_parts.insert(0,'/')
            new_path='/{0}'.format('/'.join(path_parts[1:]).replace('//','/'))
            new_netloc='search.twitter.com'
        elif path_parts[2].startswith('search.json'):
            new_path=path
            new_netloc='search.twitter.com'
        else:
            new_path=path
            new_netloc='api.twitter.com'

        new_path=new_path.replace('/{0}/'.format(USER_PASSWORD),'/')
        new_url=urlunparse(('https',new_netloc,new_path.replace('//','/'),params,query,''))
        return new_url,new_path

    def do_proxy(self,method):
        orig_url=self.request.url
        orig_body=self.request.body

        new_url,new_path=self.conver_url(orig_url)

        if new_path=='/' or new_path=='':
            self.response.set_status(200)
            self.response.headers['Content-Type']='text/html'
            self.response.write(ptapp_message.format(self.request.path))
            return 0
        
        user_access_token=None
        
        callback_url='{0}/oauth/verify'.format(self.request.host_url)
        client=TwitterClient(CONSUMER_KEY,CONSUMER_SECRET,callback_url)

        protected=True
        user_access_token,user_access_secret=ACCESS_TOKEN,ACCESS_TOKEN_SECRET

        additional_params=dict([(k,v) for k,v in parse_qsl(orig_body)])

        use_method=urlfetch.GET if method=='GET' else urlfetch.POST

        try:
            debug('Start communicate to twitter.')
            data=client.make_request(url=new_url,
                                     token=user_access_token,
                                     secret=user_access_secret,
                                     method=use_method,
                                     protected=protected,
                                     additional_params=additional_params)
        except Exception,error_message:
            debug(error_message)
            from json import dumps
            self.response.set_status(503)
            self.response.headers['Content-Type']='application/json'
            self.response.write(dumps(dict(error=str(error_message))))
        else:
            if data.status_code>=500:
                self.response.headers['Content-Type']='application/json'
                self.response.write('{"error":"Twitter / Over capacity"}')
            elif data.status_code>=400:
                self.response.headers['Content-Type']='application/json'
                self.response.write(data.content)
            else:
                if new_path.endswith('.xml'):
                    self.response.headers['Content-Type']='application/xml'
                    self.response.write(data.content)
                elif new_path.endswith('.json'):
                    status=data.content
                    if method=='GET':
                        if FILTER==1:
                            debug('Filter start.')
                            from statusfilter import statusfilter
                            status=statusfilter(status)
                            debug('Filter finished')
                        if API_IMPROVE==1:
                            debug('Rewriter start.')
                            from linkrewriter import linkrewriter
                            status=linkrewriter(status)
                            debug('Rewrite Finished.')
                    self.response.headers['Content-Type']='application/json'
                    self.response.write(status)
                else:
                    self.response.write(data.content)
        return 0

    def post(self):
        self.do_proxy('POST')
    
    def get(self):
        self.do_proxy('GET')

class OAuthPage(RequestHandler):
    def get(self):
        self.response.headers['Content-Type']='text/plain'
        self.response.write('oauth_token={0}&oauth_token_secret={1}&user_id={2}&screen_name={3}&x_auth_expires=0'.format(ACCESS_TOKEN,
                                                                                                                             ACCESS_TOKEN_SECRET,
                                                                                                                             ACCESS_TOKEN.split('-')[0],
                                                                                                                             SCREEN_NAME))

class DummyPage(RequestHandler):
    def get(self):
        self.response.headers['Content-Type']='text/html'
        self.response.set_status(404)
        self.response.write(ptapp_message.format(self.request.path))

app=WSGIApplication([('/{0}/oauth/access_token'.format(USER_PASSWORD),OAuthPage),
                     ('/{0}/.*'.format(USER_PASSWORD),MainPage),
                     ('/.*',DummyPage)],debug=True)
