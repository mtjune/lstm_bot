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

    xp = None

    GRAD_CLIP = 5    # gradient norm threshold to clip

    n_units = None

    model = None
    tagger = None
    optimizer = None
    state_stable = None
    vocab_in = None
    vocab_out = None
    DIC_DIR = "/home/yamajun/workspace/tmp/igo_ipadic"

    def __init__(self, n_units , vocab_in, vocab_out, loadpath=None, gpu=-1):
        self.xp = np

        self.tagger = igo.tagger.Tagger(self.DIC_DIR)

        self.vocab_in = vocab_in
        self.vocab_out = vocab_out

        self.n_units = n_units

        if loadpath:
            with open(loadpath, 'rb') as f:
                self.model = pickle.load(f)

        else:
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


    def _igo_parse(self, text):
        words = self.tagger.parse(text)
        outputs = [word.surface for word in words]
        return outputs


    def _forward_one_step(self, x_data, state, train=True):
        # Neural net architecture
        x = chainer.Variable(x_data, volatile=not train)
        h0 = self.model.embed(x)
        h1_in = self.model.l1_x(F.dropout(h0, train=train)) + self.model.l1_h(state['h1'])
        c1, h1 = F.lstm(state['c1'], h1_in)
        h2_in = self.model.l2_x(F.dropout(h1, train=train)) + self.model.l2_h(state['h2'])
        c2, h2 = F.lstm(state['c2'], h2_in)
        y = self.model.l3(F.dropout(h2, train=train))
        state = {'c1': c1, 'h1': h1, 'c2': c2, 'h2': h2}
        return state, y



    def _make_initial_state(self, batchsize=1, train=True):
        return {name: chainer.Variable(self.xp.zeros((batchsize, self.n_units), dtype=np.float32), volatile=not train) for name in ('c1', 'h1', 'c2', 'h2')}

    def _shaping_and_split_tweet(self, tweet):

        tweet = tweet.replace('<tweetend>', '')

        tweet_split = self._igo_parse(tweet)

        for i in range(len(tweet_split)):
            if tweet_split[i] not in self.vocab_in:
                tweet_split[i] = '<unknown>'


        tweet_split.append('<tweetend>')

        return tweet_split


    def one_tweet_backward(self, tweet):
        """
        ツイートひとつ分を学習
        """

        tweet_split = self._shaping_and_split_tweet(tweet)

        accum_loss = chainer.Variable(self.xp.zeros((), dtype=np.float32))

        if self.state_stable:
            state = self.state_stable
        else:
            state = self._make_initial_state(batchsize=1, train=True)

        count_train = 0
        for i in range(len(tweet_split) - 1):
            if tweet_split[i + 1] == '<unknown>':
                x_data = self.xp.array([self.vocab_in[tweet_split[i]]], dtype=np.int32)
                state, y = self._forward_one_step(x_data, state, train=True)

            else:
                x_data = self.xp.array([self.vocab_in[tweet_split[i]]], dtype=np.int32)
                y_data = self.xp.array([self.vocab_out[tweet_split[i + 1]]], dtype=np.int32)

                state, y = self._forward_one_step(x_data, state, train=True)
                loss_i = F.softmax_cross_entropy(y, chainer.Variable(y_data, volatile=False))
                accum_loss += loss_i
                count_train += 1

        if count_train != 0:
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
            x_data = self.xp.array([self.vocab[text_in]], dtype=np.int32)
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
