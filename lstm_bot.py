# -*- encoding: utf-8 -*-

import argparse
import yaml
import json
import time
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

import lstm


with open('keys_lstmbot.yml', 'r') as f:
    keys_lstmbot = yaml.load(f)

with open('keys_mtjuney.yml', 'r') as f:
    keys_mtjuney = yaml.load(f)


parser = argparse.ArgumentParser()
parser.add_argument('--vocabin', '-vi', default='dumps/vocab_ready_in.dump')
parser.add_argument('--vocabout', '-vo', default='dumps/vocab_ready_out.dump')
parser.add_argument('--modelinput', '-mi', default=None)
parser.add_argument('--modeloutput', '-mo', default='dumps/model_lstm.dump')

args = parser.parse_args()


with open(args.vocabin, 'rb') as f:
    vocabin = pickle.load(f)
with open(args.vocabout, 'rb') as f:
    vocabout = pickle.load(f)
lstm = lstm.LSTM(650, vocabin, vocabout, loadpath=args.modelinput)



tweet_q = queue.Queue(maxsize=300)

# def feed_tweet():
#     global vocab, tweet_q, keys_mtjuney
#
#     api = OAuth1Session(keys_mtjuney['CONSUMER_KEY'], keys_mtjuney['CONSUMER_SECRET'], keys_mtjuney['ACCESS_TOKEN'], keys_mtjuney['ACCESS_SECRET'])
#     url = "https://api.twitter.com/1.1/statuses/home_timeline.json"
#
#
#     last_tweetid = None
#
#
#     while True:
#
#         if last_tweetid:
#             params = {'count': 200, 'exclude_replies': True, 'since_id': last_tweetid}
#         else:
#             params = {'count': 200, 'exclude_replies': True}
#
#         tweets = api.get(url, params=params)
#         tweets_j = tweets.json()
#
#         for tweet in tweets_j:
#             text = tweet['text']
            # if re.match(r'^RT', text):
            #     continue
            #
            # text = re.sub(r'@[a-zA-Z0-9_]{1,15}', '', text)
            # text = re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+', '', text)
            # text = re.sub(r'[\n\s]+', ' ', text)
            # text = text.strip()
            # if not tweet_q.full():
            #     tweet_q.put(text)
#                 # print(text)
#
#         if len(tweets_j) != 0:
#             last_tweetid = tweets_j[0]['id']
#
#
#         time.sleep(90)


def feed_tweet():
    global tweet_q, keys_mtjuney

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
                    if not tweet_q.full():
                        tweet_q.put(text)

    except Exception as e:
        print( '=== エラー内容 ===')
        print( 'type:' + str(type(e)))
        print( 'args:' + str(e.args))
        print( 'message:' + str(e.message))
        print( 'e self:' + str(e))

    except:
        print( "error.")



def train_tweet():
    global lstm, tweet_q

    count_train = 1
    total_time_train = 0.
    while True:

        tweet_text = tweet_q.get()

        start_at = time.time()
        lstm.one_tweet_backward(tweet_text)
        end_at = time.time()
        total_time_train += (end_at - start_at)

        if count_train % 500 == 0:
            now_at = time.time()
            print('trained {} tweet ({} tweet/sec)'.format(count_train, float(count_train) / total_time_train))
            print('\tqueue_size : {}'.format(tweet_q.qsize()))
            lstm.save(args.modeloutput)
            print('\tsaved model as {}'.format(args.modeloutput))

        count_train += 1




if __name__ == '__main__':
    feeder = threading.Thread(target=feed_tweet)
    feeder.daemon = True
    feeder.start()

    train_tweet()
    feeder.join()

    print('finish!')
