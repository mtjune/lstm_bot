# -*- encoding: utf-8 -*-

import argparse
import time
import yaml
import json
import re
import multiprocessing
import threading
from requests.exceptions import ConnectionError, ReadTimeout, SSLError


import oauth2 as oauth
import urllib
from requests_oauthlib import OAuth1Session
from http.client import IncompleteRead

import six.moves.cPickle as pickle
from six.moves import queue


keys_lstmbot = None
with open('keys_lstmbot.yml', 'r') as f:
    keys_lstmbot = yaml.load(f)

keys_mtjuney = None
with open('keys_mtjuney.yml', 'r') as f:
    keys_mtjuney = yaml.load(f)


def get_tweet_streaming():
    global keys_lstmbot, keys_mtjuney
    # consumer = oauth.Consumer(key=keys_mtjuney['CONSUMER_KEY'], secret=keys_mtjuney['CONSUMER_SECRET'])
    # token = oauth.Token(key=keys_mtjuney['ACCESS_TOKEN'], secret=keys_mtjuney['ACCESS_SECRET'])
    #
    # url = 'https://stream.twitter.com/1.1/statuses/sample.json'
    # params = {}
    #
    # request = oauth.Request.from_consumer_and_token(consumer, token, http_url=url, parameters=params)
    # request.sign_request(oauth.SignatureMethod_HMAC_SHA1(), consumer, token)
    # res = urllib.request.urlopen(request.to_url())

    api = OAuth1Session(keys_mtjuney['CONSUMER_KEY'], keys_mtjuney['CONSUMER_SECRET'], keys_mtjuney['ACCESS_TOKEN'], keys_mtjuney['ACCESS_SECRET'])
    url = 'https://stream.twitter.com/1.1/statuses/sample.json'

    params = {}

    res = api.get(url, params=params, stream=True)


    try:
        for r in res.iter_lines():
            data = json.loads(r.decode())
            if 'delete' in data.keys():
                pass
            else:
                if data['lang'] in ['ja']:
                    text = data['text']

                    if re.match(r'^[(RT)【]', text):
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

if __name__ == '__main__':
    get_tweet_streaming()
