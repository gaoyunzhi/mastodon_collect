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
import random
import warnings
warnings.filterwarnings('ignore')

with open('credential') as f:
    credential = yaml.load(f, Loader=yaml.FullLoader)
tele = Updater(credential['bot_token'], use_context=True)
debug_group = tele.bot.get_chat(credential['debug_group'])
tele_channel = tele.bot.get_chat(credential['tele_channel'])
monitor_words_channel = tele.bot.get_chat(credential['monitor_words_channel'])

existing = plain_db.load('existing')
user_info = plain_db.loadLargeDB('user_info')
blocked_words = plain_db.loadKeyOnlyDB('blocked_words')
weighted_words = plain_db.loadLargeDB('weighted_words')
following = plain_db.loadKeyOnlyDB('following')
monitor_words = plain_db.loadKeyOnlyDB('monitor_words')
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
    require_count = getRequireCount(status)
    count = mastodon_2_album.getReblogsCount(status)
    return count > require_count

def getRequireAndAdjust(status):
    result = 'require: %d ' % getRequireCount(status)
    core_content = mastodon_2_album.getCoreContent(status)
    weights = []
    for word, raw_weight in weighted_words.items():
        weight = float(raw_weight)
        if (not 0.9 < weight < 1.1) and word in core_content:
            weights.append((weight, raw_weight, word))
    weights.sort()
    result += ''.join(['%s(%s) ' % (w[2], w[1]) for w in weights])
    return result

def log(chat, status, add_url_in_log):
    additional_info = ''
    log_message = ''
    if chat.id == tele_channel.id:
        additional_info = getRequireAndAdjust(status)
    try:
        log_message = mastodon_2_album.getLog(status) % additional_info
    except Exception as e:
        print('mastodon_collect log_message exception (try resolving)', mastodon_2_album.getUrl(status), mastodon_2_album.getLog(status), additional_info, e)
        log_message = mastodon_2_album.getLog(status) + ' ' + additional_info
    if add_url_in_log:
        log_message += ' ' + mastodon_2_album.getUrl(status)
    send_message(chat, log_message)

def updateUserInfo(status):
    for user_id, info in mastodon_2_album.yieldUsersRawInfo(status):
        user_info.update(user_id, info)

def shouldMonitor(status):
    if monitor_words.contain(mastodon_2_album.getAuthor(status).url.split('/')[3][1:]):
        if not mastodon_2_album.getCommenter(status):
            return False
        if not mastodon_2_album.getContentText(status):
            return False   
    core_content = mastodon_2_album.getCoreContent(status)     
    return matchKey(core_content, monitor_words.items())

def getChannel(status):
    if existing.get(mastodon_2_album.getUrl(status)):
        return 
    if existing.get(mastodon_2_album.getHash(status)):
        return 
    if shouldMonitor(status):
        return monitor_words_channel
    if shouldPost(status):
        return tele_channel

def fetchAll(mastodon, result, limit=80):
    while len(result) == limit:
        for item in result:
            yield item
        result = mastodon.fetch_next(result)
        print('fetched next', len(result))
    for item in result:
        yield item

def getFollowing(mastodon):
    for item in following.items():
        yield mastodon.account(int(item))
    followings = list(fetchAll(mastodon, 
        account_following(mastodon.me().id, limit=80), limit=80))
    random.shuffle(followings)
    for account in followings:
        yield account

def getFollowings(mastodon, accounts):
    exist = set()
    for account in accounts:
        exist.add(account.id)
        yield account    
    account_ids = list(exist)
    random.shuffle(account_ids)
    for account_id in account_ids:
        followings = mastodon.account_following(account_id, limit=80)
        for account in fetchAll(mastodon, followings, limit=80):
            if account.id in exist:
                continue
            yield account
            exist.add(account.id)

def mastodonSingleCollect(mastodon, account_id):
    statuses = mastodon.account_statuses(account_id, limit=40)
    for status in statuses:
        chat = getChannel(status)
        if not chat:
            continue
        # print(status)
        # print('')
        # print(mastodon_2_album.getCoreContent(status))
        album = mastodon_2_album.get(status)
        len_imgs = len(album.imgs)
        wait_timer.wait(chat.id, len_imgs * 10 + len_imgs * len_imgs)
        add_url_in_log = False
        try:
            album_sender.send_v2(chat, album)
        except Exception as e:
            print('mastodon_collect send fail', mastodon_2_album.getUrl(status), e)
            add_url_in_log = True
        log(chat, status, add_url_in_log=add_url_in_log)
        updateUserInfo(status)
        existing.update(mastodon_2_album.getUrl(status), 1)
        existing.update(mastodon_2_album.getHash(status), 1)
        
def mastodonCollect():
    mastodon = Mastodon(
        access_token = 'db/main_mastodon_secret',
        api_base_url = credential['mastodon_domain']
    )
    followings_followings = getFollowings(mastodon, getFollowing(mastodon))
    for account in followings_followings: # testing
    # for account in getFollowing(mastodon): 
        mastodonSingleCollect(mastodon, account.id)

if __name__ == '__main__':
    mastodonCollect()