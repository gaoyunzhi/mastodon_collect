#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import plain_db
import yaml
from mastodon import Mastodon
from telegram.ext import Updater
import time
import album_sender
import mastodon_2_album
from telegram_util import wait_timer

with open('credential') as f:
    credential = yaml.load(f, Loader=yaml.FullLoader)
tele = Updater(credential['bot_token'], use_context=True)
debug_group = tele.bot.get_chat(credential['debug_group'])
tele_channel = tele.bot.get_chat(credential['tele_channel'])

existing = plain_db.load('existing')

def shouldPost(status):
    if existing.get(mastodon_2_album.getUrl(status)):
        return False
    if existing.get(mastodon_2_album.getHash(status)):
        return False
    count = mastodon_2_album.getRepostCount(status)
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
            album = mastodon_2_album.get(status)
            result = album_sender.send_v2(tele_channel, album)
            wait_timer('main', len(result) * 5)

            wait_timer('main', len(result) * 5)
            existing.update(mastodon_2_album.getUrl(status), 1)
            existing.update(mastodon_2_album.getHash(status), 1)

            return
        
if __name__ == '__main__':
    mastodon_collect()