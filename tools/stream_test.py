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
    global keys_mtjuney

    api = OAuth1Session(
        keys_mtjuney['CONSUMER_KEY'],
        client_secret=keys_mtjuney['CONSUMER_SECRET'],
        resource_owner_key=keys_mtjuney['ACCESS_TOKEN'],
        resource_owner_secret=keys_mtjuney['ACCESS_SECRET']
    )

    url = 'https://userstream.twitter.com/1.1/user.json'

    params = {}

    res = api.get(url, params=params, stream=True)


    try:
        for r in res.iter_lines():
            if not r:
                continue
            data = json.loads(r.decode())
            if 'delete' in data.keys() or 'lang' not in data:
                pass
            else:
                if data['lang'] in ['ja']:
                    text = data['text']

                    if re.match(r'^(RT|@[a-zA-Z0-9]+)', text):
                        continue

                    text = re.sub(r'@[a-zA-Z0-9_]{1,15}', '', text)
                    text = re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+', '', text)
                    text = re.sub(r'[\n\s]+', ' ', text)
                    text = text.strip()
                    
                    print(text)

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
