# -*- encoding: utf-8 -*-

import yaml
import json

from requests_oauthlib import OAuth1Session



keys_lstmbot = None
with open('keys_lstmbot.yml', 'r') as f:
    keys_lstmbot = yaml.load(f)

with open('keys_mtjuney.yml', 'r') as f:
    keys_mtjuney = yaml.load(f)

api = OAuth1Session(keys['CONSUMER_KEY'], keys['CONSUMER_SECRET'], keys['ACCESS_TOKEN'], keys['ACCESS_SECRET'])
url = "https://api.twitter.com/1.1/friends/ids.json"

screen_list = ['mtjuney']
screen_name = ','.join(map(str, screen_list))
params = {'screen_name': screen_name}

sid = api.get(url, params=params)
sid_j = sid.json()

for sid_list in sid_j:
    print(sid_list)

print(len(sid_j['ids']))

for sid_list in sid_j['ids']:
    print(sid_list)
