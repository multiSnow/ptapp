#coding: utf8

import urlparse,base64,logging,webapp2,json
from cgi import parse_qsl
from google.appengine.api import urlfetch
import oauth,improve

CONSUMER_KEY=''
CONSUMER_SECRET=''

SCREEN_NAME=''
USER_PASSWORD=''
ACCESS_TOKEN=''
ACCESS_TOKEN_SECRET=''

API_IMPROVE=1

ptapp_message='''
<html><head>
<meta http-equiv="content-type" content="text/html;charset=utf-8">
<title>404 Not Found</title>
</head>
<body text=#000000 bgcolor=#ffffff>
<h1>Error: Not Found</h1>
<h2>The requested URL <code>#request_path#</code> was not found on this server.</h2>
<h2></h2>
</body></html>'''

class MainPage(webapp2.RequestHandler):

    def conver_url(self,orig_url):
        (scm,netloc,path,params,query,_)=urlparse.urlparse(orig_url)
        
        path_parts=path.split('/')

        if path_parts[2]=='api':
            path_parts=path_parts[3:]
            path_parts.insert(0,'/')
            new_path='/'+'/'.join(path_parts[1:]).replace('//','/')
            new_netloc='api.twitter.com'
        elif path_parts[2]=='searchapi':
            path_parts=path_parts[3:]
            path_parts.insert(0,'/')
            new_path='/'+'/'.join(path_parts[1:]).replace('//','/')
            new_netloc='search.twitter.com'
        elif path_parts[2].startswith('search.json'):
            new_path=path
            new_netloc='search.twitter.com'
        else:
            new_path=path
            new_netloc='api.twitter.com'

        new_path=new_path.replace('/'+USER_PASSWORD+'/','/')
        new_url=urlparse.urlunparse(('https',new_netloc,new_path.replace('//','/'),params,query,''))
        return new_url,new_path

    def do_proxy(self,method):
        orig_url=self.request.url
        orig_body=self.request.body

        new_url,new_path=self.conver_url(orig_url)

        if new_path=='/' or new_path=='':
            self.response.set_status(200)
            self.response.headers['Content-Type']='text/html'
            self.response.out.write(ptapp_message.replace('#request_path#',self.request.path))
            return 0
        
        user_access_token=None
        
        callback_url='%s/oauth/verify'%self.request.host_url
        client=oauth.TwitterClient(CONSUMER_KEY,CONSUMER_SECRET,callback_url)

        protected=True
        user_access_token,user_access_secret=ACCESS_TOKEN,ACCESS_TOKEN_SECRET

        additional_params=dict([(k,v) for k,v in parse_qsl(orig_body)])

        use_method=urlfetch.GET if method=='GET' else urlfetch.POST

        try:
            data=client.make_request(url=new_url,
                                     token=user_access_token,
                                     secret=user_access_secret,
                                     method=use_method,
                                     protected=protected,
                                     additional_params=additional_params)
        except Exception,error_message:
            logging.debug(error_message)
            self.response.set_status(503)
            self.response.headers['Content-Type']='text/html'
            self.response.out.write('Server Error:<br/>')
            self.response.out.write(error_message)
        else:
            self.response.headers['Content-Type']='text/html'
            if data.status_code>=500:
                self.response.out.write('{"error":"Twitter / Over capacity"}')
            elif API_IMPROVE==1 and method=='GET' and new_path.endswith('.json') and data.status_code<400:
                self.response.out.write(improve.api_improve(data.content))
            else:
                self.response.out.write(data.content)

    def post(self):
        self.do_proxy('POST')
    
    def get(self):
        self.do_proxy('GET')

class OAuthPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type']='text/html'
        self.response.out.write('oauth_token=%s&oauth_token_secret=%s&user_id=%s&screen_name=%s&x_auth_expires=0'
                                %(ACCESS_TOKEN,
                                  ACCESS_TOKEN_SECRET,
                                  ACCESS_TOKEN.split('-')[0],
                                  SCREEN_NAME))

class DummyPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type']='text/html'
        self.response.set_status(404)
        self.response.out.write(ptapp_message.replace('#request_path#',self.request.path))

app=webapp2.WSGIApplication([('/'+USER_PASSWORD+'/oauth/access_token',OAuthPage),
                             ('/'+USER_PASSWORD+'/.*',MainPage),
                             ('/.*',DummyPage)],debug=True)
