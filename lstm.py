# encoding: utf-8


import argparse
import math
import sys
import time
import yaml
import csv

import pymysql

import numpy as np
import six
import six.moves.cPickle as pickle

import chainer
from chainer import cuda
import chainer.functions as F
from chainer import optimizers

import igo


class LSTM:

    GRAD_CLIP = 5    # gradient norm threshold to clip

    n_units = None

    model = None
    tagger = None
    optimizer = None
    state_stable = None
    vocab_in = None
    vocab_out = None
    DIC_DIR = "/home/yamajun/workspace/tmp/igo_ipadic"

    def __init__(self, n_units , vocab_in, vocab_out):
        self.tagger = igo.tagger.Tagger(DIC_DIR)

        self.vocab_in = vocab_in
        self.vocab_out = vocab_out

        self.n_units = n_units

        self.model = chainer.FunctionSet(
            embed=F.EmbedID(len(self.vocab_in), n_units),
            l1_x=F.Linear(self.n_units, 4 * self.n_units),
            l1_h=F.Linear(self.n_units, 4 * self.n_units),
            l2_x=F.Linear(self.n_units, 4 * self.n_units),
            l2_h=F.Linear(self.n_units, 4 * self.n_units),
            l3=F.Linear(self.n_units, len(self.vocab_out)),
        )


        self.optimizer = optimizers.Adam()
        self.optimizer.setup(self.model)


    def _igo_parse(text):
        words = self.tagger.parse(text)
        outputs = [word.surface for word in words]
        return outputs


    def _forward_one_step(self, x_data, state, train=True):
        # Neural net architecture
        x = chainer.Variable(x_data, volatile=not train)
        h0 = model.embed(x)
        h1_in = self.model.l1_x(F.dropout(h0, train=train)) + self.model.l1_h(state['h1'])
        c1, h1 = F.lstm(state['c1'], h1_in)
        h2_in = self.model.l2_x(F.dropout(h1, train=train)) + self.model.l2_h(state['h2'])
        c2, h2 = F.lstm(state['c2'], h2_in)
        y = self.model.l3(F.dropout(h2, train=train))
        state = {'c1': c1, 'h1': h1, 'c2': c2, 'h2': h2}
        return state, y



    def _make_initial_state(self, batchsize=1, train=True):
        return {name: chainer.Variable(xp.zeros((batchsize, self.n_units), dtype=np.float32), volatile=not train) for name in ('c1', 'h1', 'c2', 'h2')}

    def _shaping_and_spilit_tweet(self, tweet):
        global vocab_in

        tweet = tweet.replace('<tweetend>', '')

        tweet_split = self._igo_parse(tweet)

        for i in range(len(tweet_split)):
            if tweet_split[i] not in vocab_in:
                tweet_split[i] = '<unknown>'


        tweet_split.append('<tweetend>')

        return tweet_split


    def one_tweet_backward(self, tweet):
        """
        ツイートひとつ分を学習
        """

        tweet_spilit = self._shaping_and_split_tweet(tweet)

        accum_loss = chainer.Variable(xp.zeros((), dtype=np.int32))

        if state_stable:
            state = self.state_stable
        else:
            state = self._make_initial_state(batchsize=1, train=True)


        for i in range(len(tweet_split) - 1):
            x_data = xp.array([self.vocab[tweet_split[i]]])
            y_data = xp.array([self.vocab[tweet_split[i + 1]]])

            state, y = self._forward_one_step(x_data, state, train=True)
            loss_i = F.softmax_cross_entropy(y, chainer.Variable(y_data, volatile=False))
            accum_loss += loss_i

        self.optimizer.zero_grads()
        accum_loss.backward()
        accum_loss.unchain_backward()


    def generate_tweet(self, first_word, state=None):
        """
        ツイート一つを生成
        """

        tweet = first_word

        if not state:
            state = self._make_initial_state(batchsize=1, train=False)


        text_in = first_word
        while True:
            x_data = xp.array([self.vocab[text_in]])
            state, y = self._forward_one_step(x_data, state, train=False)
            y = F.softmax(y).data.reshape((-1,))
            ind = np.argmax(y)
            text_out = [x[0] for x in vocab.items() if x[1] == ind][0]

            if text_out == '<tweetend>':
                return tweet
            elif len(tweet) + len(text_out) > 140:
                return tweet
            else:
                tweet += text_out
                text_in = text_out

    def save(self, filepath):
        with open(filepath, 'wb') as f:
            pickle.dump(self.model, f, -1)
