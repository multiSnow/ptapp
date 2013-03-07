#coding:utf-8

def func_reindices(text,string):
    #locate string in text
    #return [start,end]
    start=text.find(string)
    end=start+len(string)
    return [start,end]

def func_replace_tco(text,entit_list):
    #replace t.co in text using urls from entit_list.
    #
    #url should as below at least:
    #url['url']==t.co_url
    #url['expanded_url']==orig_url
    #url['display_url']==url_to_display
    #
    #url['media_url_https'] will be tested and processed only when exist
    #
    #return [text,extit_list]
    for urls in entit_list:
        url=urls['url']
        if 'media_url_https' in urls:
            expanded_url=urls['media_url_https']
            urls['expanded_url']=expanded_url
        else:
            expanded_url=urls['expanded_url']
        text=text.replace(url,expanded_url)
        urls['url']=expanded_url
        urls['display_url']=expanded_url
    return [text,entit_list]

def func_url_rewrite(status_dict):
    try:
        for entry in ['profile_background_image_url','profile_image_url']:
            if entry in status_dict:
                status_dict[entry]=status_dict[entry.replace('image_url','image_url_https')]
            if 'user' in status_dict:
                status_dict['user'][entry]=status_dict['user'][entry.replace('image_url','image_url_https')]
    finally:
        pass

    try:
        if 'user' in status_dict:
            if status_dict['user']['url']:
                if '//t.co/' in status_dict['user']['url']:
                    [status_dict['user']['url'],status_dict['user']['entities']['url']['urls']]=func_replace_tco(status_dict['user']['url'],status_dict['user']['entities']['url']['urls'])
    finally:
        pass

    try:
        if 'user' in status_dict:
            [status_dict['user']['description'],status_dict['user']['entities']['description']['urls']]=func_replace_tco(status_dict['user']['description'],status_dict['user']['entities']['description']['urls'])
    finally:
        pass

    try:
        if 'entities' in status_dict:
            for entities_child in status_dict['entities']:
                if entities_child=='media' or entities_child=='urls':
                    [status_dict['text'],status_dict['entities'][entities_child]]=func_replace_tco(status_dict['text'],status_dict['entities'][entities_child])
    finally:
        pass

    try:
        if 'entities' in status_dict:
            for entities_child in status_dict['entities']:
                if entities_child=='media' or entities_child=='urls':
                    for urls in status_dict['entities'][entities_child]:
                        urls['indices']=func_reindices(status_dict['text'],urls['url'])
                elif entities_child=='user_mentions':
                    for user in status_dict['entities'][entities_child]:
                        user['indices']=func_reindices(status_dict['text'],'@{0}'.format(user['screen_name']))
                elif entities_child=='hashtags':
                    for user in status_dict['entities'][entities_child]:
                        user['indices']=func_reindices(status_dict['text'],user['text'])
    finally:
        pass

    return status_dict

def func_write_dict(input_dict):
    input_dict=func_url_rewrite(input_dict)
    return 0

def https_wrap(url_in):
    (url_in_scm,url_in_netloc,url_in_path,url_in_params,url_in_query,url_in__)=urlparse.urlparse(url_in)
    return urlparse.urlunparse(('https',url_in_netloc,url_in_path,url_in_params,url_in_query,url_in__))

insecurl_dict=['img.ly','twitpic.com']

def linkrewriter(content):
    import json
    from threading import Thread
    from time import sleep

    status_list=json.loads(content);
    if type(status_list)==list:
        mts=[]
        for p in status_list:
            mt=Thread(target=func_write_dict,args=(p,))
            mt.start()
            mts.append(mt)
            if 'retweeted_status' in p:
                q=p['retweeted_status']
                nt=Thread(target=func_write_dict,args=(q,))
                nt.start()
                mts.append(nt)

        for t in mts:
            t.join()
    elif type(status_list)==dict:
        func_write_dict(status_list)
    else:
        pass

    return json.dumps(status_list)
