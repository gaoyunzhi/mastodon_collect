#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import plain_db
import yaml
from mastodon import Mastodon
from telegram.ext import Updater
import time

tele = Updater(credential['bot_token'], use_context=True)
debug_group = tele.bot.get_chat(credential['debug_group'])
tele_channel = tele.bot.get_chat(credential['tele_channel'])

existing = plain_db.load('existing')
with open('credential') as f:
    credential = yaml.load(f, Loader=yaml.FullLoader)

def getContentText(content):
    soup = BeautifulSoup(content, 'html.parser')
    return soup.text

def shouldPost(status):
    if existing.get(status.url):
        return False
    count = status.reblogs_count
    try:
        count += status.reblog.reblogs_count
    except:
        ...
    return count > 100 # todo

def mastodon_collect():
    mastodon = Mastodon(
        access_token = 'db/main_mastodon_secret',
        api_base_url = credential['mastodon_domain']
    )
    my_id = mastodon.me().id
    for user in mastodon.account_following(my_id, limit=80):
        statuses = mastodon.account_statuses(user.id, limit=40)
        for status in statuses:
            if not shouldPost(status):
                continue
            print(status)
            return
        
if __name__ == '__main__':
    mastodon_collect()