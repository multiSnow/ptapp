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

from json import dumps
from logging import debug,info
from urllib import urlencode
from urlparse import parse_qs,parse_qsl,urlparse,urlunparse

from webapp2 import RequestHandler,WSGIApplication

from config import CONSUMER_KEY,CONSUMER_SECRET,SCREEN_NAME,ACCESS_TOKEN,ACCESS_TOKEN_SECRET,USER_PASSWORD,GAPLESS
from oauth import TwitterClient
from ppatp import ppatp

editable_api=[['statuses','mentions_timeline.json'],
              ['statuses','user_timeline.json'],
              ['statuses','home_timeline.json'],
              ['statuses','statuses','retweets_of_me.json'],
              ['statuses','show.json'],
              ['statuses','show'],
              ['search','tweets.json'],
              ['favorites','list.json'],
              ['lists','statuses.json']]

dummy_msg='''
<html><head>
<meta http-equiv="content-type" content="text/html;charset=utf-8">
<title>404 Not Found</title>
</head>
<body text=#000000 bgcolor=#ffffff>
<h1>Error: Not Found</h1>
<h2>The requested URL <code>{0}</code> was not found on this server.</h2>
<h2></h2>
</body></html>'''

work_msg='''
<html><head>
<meta http-equiv="content-type" content="text/html;charset=utf-8">
<title>PTAPP is working</title>
</head>
<body>
<h1>PTAPP is working</h1>
<h2>PTAPP for {0} deployed on {1} is working now</h2>
</body></html>
'''

class MainPage(RequestHandler):

    def api(self):

        path_list=self.request.path.split('/')
        if path_list.pop(1)!=USER_PASSWORD:
            self.response.headers['Content-Type']='text/html'
            self.response.set_status(404)
            self.response.write(dummy_msg.format(self.request.path_qs))
            return
        elif path_list==[''] or path_list==['','']:
            self.response.headers['Content-Type']='text/html'
            self.response.write(work_msg.format(SCREEN_NAME,self.request.host))
            return
        elif path_list[2:]==['oauth','access_token']:
            self.response.headers['Content-Type']='text/plain'
            self.response.write(urlencode([('oauth_token',ACCESS_TOKEN),
                                           ('oauth_token_secret',ACCESS_TOKEN_SECRET),
                                           ('user_id',ACCESS_TOKEN.split('-')[0]),
                                           ('screen_name',SCREEN_NAME),
                                           ('x_auth_expires',0)]))
            return
        else:
            editable=(path_list[2:4] in editable_api)

        if GAPLESS and 'since_id' in parse_qs(self.request.query_string):
            qsdict={k:v for k,v in parse_qsl(self.request.query_string)}
            offset=10000
            qsdict.update(count=200)
            qsdict.update(since_id=int(qsdict['since_id'])-offset)
            self.request.query_string=urlencode(qsdict)
            tcqdict=dict(path_list=path_list,
                         qsdict=qsdict,
                         token=self.ACCESS_TOKEN,
                         secret=self.ACCESS_TOKEN_SECRET,
                         body=self.request.body,
                         offset=offset)
        else:
            tcqdict=None

        client=TwitterClient(CONSUMER_KEY,CONSUMER_SECRET,None)
        try:
            data=client.make_request(url=urlunparse(('https','api.twitter.com','/'.join(path_list),None,self.request.query_string,None)),
                                     token=ACCESS_TOKEN,
                                     secret=ACCESS_TOKEN_SECRET,
                                     method=self.request.method,
                                     protected=True,
                                     additional_params=dict([(k,v) for k,v in parse_qsl(self.request.body)]))
        except Exception as error_message:
            debug(error_message)
            self.response.set_status(503)
            self.response.headers['Content-Type']='application/json'
            self.response.write(dumps(dict(error=str(error_message)),separators=(',', ':')))
            return
        else:
            try:
                self.response.set_status(data.status_code)
            except KeyError:
                # GAE does not support special HTTP Status Codes, so it will be logged here and set the status to 403
                # probably 429
                info('Invalid HTTP status code: {0}'.format(data.status_code))
                self.response.set_status(403)
            self.response.headers['Content-Type']=data.headers['Content-Type']
            if data.status_code>399:
                info(data.status_code)
                self.response.write(data.content)
                return
            else:
                if self.request.path.endswith('.json') and self.request.method=='GET' and editable:
                    self.response.write(ppatp(data.content,tcqdict=tcqdict))
                else:
                    self.response.write(data.content)
        return

    get=post=lambda self:self.api()

app=WSGIApplication([('/.*',MainPage)],debug=True)
