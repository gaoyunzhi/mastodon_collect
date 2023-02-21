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
user_info = plain_db.loadLargeDB('user_info')

def shouldPost(status):
    if existing.get(mastodon_2_album.getUrl(status)):
        return False
    if existing.get(mastodon_2_album.getHash(status)):
        return False
    count = mastodon_2_album.getReblogsCount(status)
    return count > 100 # todo

def log(status):
    log_message = mastodon_2_album.getLog(status)
    try:
        tele_channel.send_message(log_message, disable_web_page_preview=True, parse_mode='markdown')
    except Exception as e:
        if 'Timed out' in str(e):
            return
        tele_channel.send_message(log_message, disable_web_page_preview=True)

def updateUserInfo(status):
    for user_id, info in mastodon_2_album.yieldUsersRawInfo(status):
        user_info.update(user_id, info)

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
            album = mastodon_2_album.get(status)
            wait_timer.wait('main', len(album.imgs) * 10)
            result = album_sender.send_v2(tele_channel, album)
            log(status)
            updateUserInfo(status)
            existing.update(mastodon_2_album.getUrl(status), 1)
            existing.update(mastodon_2_album.getHash(status), 1)
            return
        
if __name__ == '__main__':
    mastodon_collect()