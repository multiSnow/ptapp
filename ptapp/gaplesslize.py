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
from logging import debug,info
from time import clock,time
from urllib import urlencode
from urlparse import parse_qsl,urlunparse

from oauth import TwitterClient
from config import CONSUMER_KEY,CONSUMER_SECRET

def gaplesslize(status_list,tcqdict):
    if status_list and tcqdict:
        sc,st=clock(),time()
        client=TwitterClient(CONSUMER_KEY,CONSUMER_SECRET,None)
        qsdict=tcqdict['qsdict']
        real_since_id=int(qsdict['since_id'])+10000
        if int(status_list[-1]['id_str'])<=real_since_id:
            del status_list[-1]
            debug('already gaplessed.')
            return
        qsdict.update(since_id=real_since_id-10000)
        retry=2
        while True:
            if retry==0:
                info('abort')
                break
            qsdict.update(max_id=int(status_list[-1]['id_str']))
            try:
                data=client.make_request(url=urlunparse(('https','api.twitter.com','/'.join(tcqdict['path_list']),None,urlencode(qsdict),None)),
                                         token=tcqdict['token'],
                                         secret=tcqdict['secret'],
                                         method='GET',
                                         protected=True,
                                         additional_params=dict([(k,v) for k,v in parse_qsl(tcqdict['body'])]))
            except Exception as error_message:
                info(error_message)
                retry-=1
            else:
                if data.status_code>399:
                    # twitter refuse to response request, or twitter servers is down, abort.
                    info('Error HTTP Status Code in gaplesslize: {0}'.format(data.status_code))
                    break
                else:
                    # it must be a json of list
                    # successful request, reset retry counter
                    debug('requested for gapless')
                    new_status_list,retry=loads(data.content),2
                    if new_status_list:
                        if new_status_list[0]['id_str']==status_list[-1]['id_str']:
                            # delete duplicate tweet
                            del new_status_list[0]
                        if not new_status_list:
                            # empty list after delete duplicate tweet
                            info('empty list after delete duplicate tweet')
                            break
                        status_list.extend(new_status_list)
                        if int(status_list[-1]['id_str'])<=real_since_id:
                            # OK, gapless, so delete the oldest
                            del status_list[-1]
                            debug('Gaplessly, totally {0} tweet.'.format(len(status_list)))
                            break
                    else:
                        debug('twitter return a empty list, should be gapless.')
                        # empty list, should be gapless
                        break
        ec,et=clock(),time()
        debug('gaplesslize use {0:.2f} processor time in {1:.4f} second'.format(ec-sc,et-st))
        return
    else:
        # no need to gaplesslize
        return
