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

from json import dumps,loads
from logging import debug,info
from threading import Thread

from config import API_IMPROVE,FILTER

if FILTER==1:
    from statusfilter import genefilter
else:
    def genefilter(l):
        while l:
            yield l.pop(0)

if API_IMPROVE==1:
    from linkrewriter import func_write_dict
else:
    func_write_dict=lambda *a,**k:None

def threadmap(func,gentor):
    def gerthread(f,g):
        l=[]
        for i in g:
            t=Thread(target=f,args=(i,))
            t.start()
            l.append(t)
        while l:
            yield l.pop(0)
    for t in gerthread(func,gentor):
        t.join()

def locgen(g,l):
    for d in g:
        l.append(d)
        yield d
        if 'retweeted_status' in d:
            yield d['retweeted_status']

def ppatp(content):
    try:
        status=loads(content);
    except:
        info('Twitter respond a non-json string.')
        return content
    else:
        if type(status) is list:
            ctnlist=[]
            threadmap(func_write_dict,locgen(genefilter(status),ctnlist))
            return dumps(ctnlist,separators=(',', ':'))
        elif type(status) is dict:
            func_write_dict(status)
            return dumps(status,separators=(',', ':'))
        else:
            # I'm not sure whether there will be any other type
            return content
