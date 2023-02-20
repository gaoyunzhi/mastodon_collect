#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import plain_db
import yaml
from mastodon import Mastodon

existing = plain_db.load('existing')
with open('credential') as f:
    credential = yaml.load(f, Loader=yaml.FullLoader)

def mastodon_collect():
    mastodon = Mastodon(
        access_token = 'db/main_mastodon_secret',
        api_base_url = credential['mastodon_domain']
    )
    print(mastodon.me())
    print(mastodon.account_following())
        
if __name__ == '__main__':
    mastodon_collect()