# -*- encoding: utf-8 -*-

import argparse
import time
import yaml
import json

import six.moves.cPickle as pickle
from six.moves import queue

parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', default='dumps/vocab_set.dump')
parser.add_argument('--outputvocabin', '-oi', default='dumps/vocab_ready_in.dump')
parser.add_argument('--outputvocabout', '-oo', default='dumps/vocab_ready_out.dump')
args = parser.parse_args()


with open(args.input, 'rb') as f:
    vocab_set = pickle.load(f)

print('read', args.input)

vocab_set.add('<tweetend>')

vocab_set_in = vocab_set.copy()
vocab_set_out = vocab_set.copy()


vocab_set_in.add('<unknown>')



vocab_ready_in = {}
vocab_ready_out = {}

for word in vocab_set_in:
    vocab_ready_in[word] = len(vocab_ready_in)

for word in vocab_set_out:
    vocab_ready_out[word] = len(vocab_ready_out)

with open(args.outputvocabin, 'wb') as f:
    pickle.dump(vocab_ready_in, f, -1)

with open(args.outputvocabout, 'wb') as f:
    pickle.dump(vocab_ready_out, f, -1)

print('saved', args.outputvocabin, args.outputvocabout)
