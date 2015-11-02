# -*- encoding: utf-8 -*-

import argparse
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



if args.modelinput:
    with open(args.modelinput, 'rb') as f:
        lstm = pickle.load(f)
else:
    with open(args.vocabin, 'rb') as f:
        vocabin = pickle.load(f)
    with open(args.vocabout, 'rb') as f:
        vocabout = pickle.load(f)
    lstm = lstm.LSTM(650, vocabin, vocabout)



tweet_q = queue.Queue(maxsize=200)

def feed_tweet():
    global vocab, tweet_q, keys_mtjuney

    api = OAuth1Session(keys_mtjuney['CONSUMER_KEY'], keys_mtjuney['CONSUMER_SECRET'], keys_mtjuney['ACCESS_TOKEN'], keys_mtjuney['ACCESS_SECRET'])
    url = "https://api.twitter.com/1.1/statuses/home_timeline.json"


    last_tweetid = None


    while True:

        if last_tweetid:
            params = {'count': 200, 'exclude_replies': True, 'since_id': last_tweetid}
        else:
            params = {'count': 200, 'exclude_replies': True}

        tweets = api.get(url, params=params)
        tweets_j = tweets.json()

        for tweet in tweets_j:
            text = tweet['text']
            if re.match(r'^RT', text):
                continue

            text = re.sub(r'@[a-zA-Z0-9_]{1,15}', '', text)
            text = re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+', '', text)
            text = text.strip()
            if not tweet_q.full():
                tweet_q.put(text)
                # print(text)

        if len(tweets_j) != 0:
            last_tweetid = tweets_j[0]['id']


        time.sleep(90)


def train_tweet():
    global lstm

    count_train = 1

    while True:

        tweet_text = tweet_q.get()

        lstm.one_tweet_backward(tweet_text)

        if count_train % 500 == 0:
            print('trained {} tweet'.format(count_train))
            lstm.save(args.modeloutput)
            print('saved model as {}'.format(args.modeloutput))

        count_train += 1




if __name__ == '__main__':
    feeder = threading.Thread(target=feed_tweet)
    feeder.daemon = True
    feeder.start()

    train_tweet()
    feeder.join()

    print('finish!')
