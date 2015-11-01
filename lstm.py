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

        self.vocab = vocab
        self.n_units = n_units

        self.model = chainer.FunctionSet(
            embed=F.EmbedID(len(vocab), n_units),
            l1_x=F.Linear(n_units, 4 * n_units),
            l1_h=F.Linear(n_units, 4 * n_units),
            l2_x=F.Linear(n_units, 4 * n_units),
            l2_h=F.Linear(n_units, 4 * n_units),
            l3=F.Linear(n_units, len(vocab)),
        )


        self.optimizer = optimizers.Adam()
        self.optimizer.setup(self.model)


    def igo_parse(text):
        words = self.tagger.parse(text)
        outputs = [word.surface for word in words]
        return outputs


    def forward_one_step(self, x_data, y_data, state, train=True):
        # Neural net architecture
        x = chainer.Variable(x_data, volatile=not train)
        t = chainer.Variable(y_data, volatile=not train)
        h0 = model.embed(x)
        h1_in = self.model.l1_x(F.dropout(h0, train=train)) + self.model.l1_h(state['h1'])
        c1, h1 = F.lstm(state['c1'], h1_in)
        h2_in = self.model.l2_x(F.dropout(h1, train=train)) + self.model.l2_h(state['h2'])
        c2, h2 = F.lstm(state['c2'], h2_in)
        y = self.model.l3(F.dropout(h2, train=train))
        state = {'c1': c1, 'h1': h1, 'c2': c2, 'h2': h2}
        return state, F.softmax_cross_entropy(y, t)

    def make_initial_state(self, batchsize=1, train=True):
        return {name: chainer.Variable(xp.zeros((batchsize, self.n_units), dtype=np.float32), volatile=not train) for name in ('c1', 'h1', 'c2', 'h2')}


    def one_tweet_backward(self, tweet):
        tweet_split = self.igo_parse(tweet)
        tweet_split.append('<tweetend>')

        accum_loss = chainer.Variable(xp.zeros((), dtype=np.int32))

        if state_stable:
            state = self.state_stable
        else:
            state = self.make_initial_state(batchsize=1, train=True)


        for i in range(len(tweet_split) - 1):
            x_data = xp.array([self.vocab[tweet_split[i]]])
            y_data = xp.array([self.vocab[tweet_split[i + 1]]])

            state, loss_i = self.forward_one_step(x_data, y_data, state)
            accum_loss += loss_i
