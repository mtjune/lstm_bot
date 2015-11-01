# -*- encoding: utf-8 -*-

import yaml
import json
import re
import multiprocessing
from requests.exceptions import ConnectionError, ReadTimeout, SSLError


import oauth2 as oauth
import urllib
from requests_oauthlib import OAuth1Session
from http.client import IncompleteRead

# from six.moves.cPickle as pickle
# from six.moves import queue



keys_lstmbot = None
with open('keys_lstmbot.yml', 'r') as f:
    keys_lstmbot = yaml.load(f)

print(keys_lstmbot)

# with open('keys_mtjuney.yml', 'r') as f:
#     keys_mtjuney = yaml.load(f)


# api = OAuth1Session(keys_lstmbot['CONSUMER_KEY'], keys_lstmbot['CONSUMER_SECRET'], keys_lstmbot['ACCESS_TOKEN'], keys_lstmbot['ACCESS_SECRET'])
# url = "https://api.twitter.com/1.1/users/lookup.json"
#
# screen_list = ['mtjuney']
# screen_name = ','.join(map(str, screen_list))
# params = {'screen_name': screen_name}
#
# sid = api.get(url, params=params)
# sid_j = sid.json()
#
# for sid_list in sid_j:
#     print(sid_list)

# def logger_setting():
#     import logging
#     from logging import FileHandler, Formatter
#     import logging.config
#
#     logging.config.fileConfig('logging_tw.conf')
#     logger = logging.getLogger(__name__)
#     return logger
#
# logger = logger_setting()



def get_tweet_stream():
    global keys_lstmbot, tweet_q
    consumer = oauth.Consumer(key=keys_lstmbot['CONSUMER_KEY'], secret=keys_lstmbot['CONSUMER_SECRET'])
    token = oauth.Token(key=keys_lstmbot['ACCESS_TOKEN'], secret=keys_lstmbot['ACCESS_SECRET'])

    url = 'https://stream.twitter.com/1.1/statuses/sample.json'
    params = {}

    request = oauth.Request.from_consumer_and_token(consumer, token, http_url=url, parameters=params)
    request.sign_request(oauth.SignatureMethod_HMAC_SHA1(), consumer, token)
    res = urllib.request.urlopen(request.to_url())
    
    try:
        for r in res:
            data = json.loads(r.decode('utf-8'))
            if 'delete' in data.keys():
                pass
            else:
                if data['lang'] in ['ja']:
                    text = data['text']

                    if re.match(r'^RT', text):
                        continue

                    text = re.sub(r'@[a-zA-Z0-9_]{1,15}', '', text)
                    text = re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+', '', text)
                    text = text.strip()
                    print(text)


    except IncompleteRead as e:
        print( '=== エラー内容 ===')
        print(  'type:' + str(type(e)))
        print(  'args:' + str(e.args))
        print(  'message:' + str(e.message))
        print(  'e self:' + str(e))
        try:
            if type(e) == exceptions.KeyError:
                print( data.keys())
        except:
            pass
    except Exception as e:
        print( '=== エラー内容 ===')
        print( 'type:' + str(type(e)))
        print( 'args:' + str(e.args))
        print( 'message:' + str(e.message))
        print( 'e self:' + str(e))

    except:
        print( "error.")

    print( "finished.")


# def train():
#     global tweet_q


def get_vocab():
    FILTER_NUM = 1

    vocab_set = set()
    vocab_count = {}


if __name__ == '__main__':
    get_tweet_stream()
