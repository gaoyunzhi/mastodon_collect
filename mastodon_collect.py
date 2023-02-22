#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import plain_db
import yaml
from mastodon import Mastodon
from telegram.ext import Updater
import time
import album_sender
import mastodon_2_album
from telegram_util import wait_timer, matchKey, send_message

with open('credential') as f:
    credential = yaml.load(f, Loader=yaml.FullLoader)
tele = Updater(credential['bot_token'], use_context=True)
debug_group = tele.bot.get_chat(credential['debug_group'])
tele_channel = tele.bot.get_chat(credential['tele_channel'])

existing = plain_db.load('existing')
user_info = plain_db.loadLargeDB('user_info')
blocked_words = plain_db.loadKeyOnlyDB('main_blocked_words')
weighted_words = plain_db.loadLargeDB('main_weighted_words')
TARGET_COUNT = 100

def getRequireCount(status):
    require = TARGET_COUNT
    core_content = mastodon_2_album.getCoreContent(status)
    if matchKey(core_content, blocked_words.items()):
        return float('Inf')
    min_weight = 1
    for word, weight in weighted_words.items():
        weight = float(weight)
        if weight > 1 and word in core_content:
            require *= weight
        if weight < 1:
            min_weight = min(min_weight, weight)
    require *= min_weight
    return require

def shouldPost(status):
    if existing.get(mastodon_2_album.getUrl(status)):
        return False
    if existing.get(mastodon_2_album.getHash(status)):
        return False
    require_count = getRequireCount(status)
    count = mastodon_2_album.getReblogsCount(status)
    return count > require_count

def getRequireAndAdjust(status):
    return 'require: %d ' % getRequireCount(status)

def log(status):
    log_message = mastodon_2_album.getLog(status) % getRequireAndAdjust(status)
    send_message(tele_channel, log_message)

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
            print('')
            print(mastodon_2_album.getCoreContent(status))
            album = mastodon_2_album.get(status)
            wait_timer.wait(tele_channel.id, len(album.imgs) * 10)
            result = album_sender.send_v2(tele_channel, album)
            log(status)
            updateUserInfo(status)
            existing.update(mastodon_2_album.getUrl(status), 1)
            existing.update(mastodon_2_album.getHash(status), 1)
            return
        
if __name__ == '__main__':
    mastodon_collect()