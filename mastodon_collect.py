#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import plain_db
import cached_url
from telegram_util import isCN, isUrl, removeOldFiles
from telepost import getPendingPosts, getPost, getImages, getRawText, exitTelethon
from telegram_util import matchKey
import copy
import time
import yaml
import random
import itertools
import export_to_telegraph
from bs4 import BeautifulSoup
from mastodon import Mastodon

existing = plain_db.load('existing')
with open('credential') as f:
    credential = yaml.load(f, Loader=yaml.FullLoader)

async def postImp(mastodon, channel, post, key):
    post_text = await getText(channel, post, key)
    media_ids = await getMediaIds(mastodon, channel, post)
    if not media_ids:
        mastodon.status_post(post_text, media_ids=media_ids)
        return
    time.sleep(5)
    for sleep_time in [10, 20, 40]:
        try:
            mastodon.status_post(post_text, media_ids=media_ids)
            return
        except Exception as e:
            if matchKey(str(e), ['无法在嘟文中同时插入视频和图片']):
                media_ids = media_ids[:1]
                continue
            if not matchKey(str(e), ['不能附加还在处理中的文件']):
                raise e
        time.sleep(sleep_time)
    try:
        mastodon.status_post(post_text, media_ids=media_ids)
    except Exception as e:
        print('post_mastodon fail', key, str(e))

def getPostFromPending(posts):
    posts = list(itertools.islice(posts, 100))
    posts = [(post.time + random.random(), post) for post in posts]
    posts.sort()
    if not posts:
        return
    if posts[0][0] < time.time() - Day * 2:
        return posts[0][1]
    for post in posts:
        # if post[1].post_id != 128801: # testing
        #     continue
        if random.random() > 0.02:
            continue
        return post[1]

async def runImp():
    removeOldFiles('tmp', day=0.1)
    items = list(setting['channel_map'].items())
    random.shuffle(items)
    for channel, mastodon_name in items:
        sub_setting = setting['setting_map'].get(channel, {})
        mastodon = Mastodon(
            access_token = 'db/%s_mastodon_secret' % mastodon_name,
            api_base_url = credential['mastodon_domain']
        )
        posts = getPendingPosts(channel, existing, 
            max_time=time.time() + Day * sub_setting.get('max_time', -0.05),
            min_time=time.time() + Day * sub_setting.get('min_time', -10))
        post = getPostFromPending(posts)
        if not post:
            continue
        key = 'https://t.me/' + post.getKey()
        try:
            result = await postImp(mastodon, channel, post, key)
            existing.update(key, 1)
        except Exception as e:
            print('post_mastodon', key, e)
            if matchKey(str(e), ['字的限制']): 
                existing.update(key, -1)
                continue
            raise e
        return

async def run():
    await runImp()
    await exitTelethon()
        
if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    r = loop.run_until_complete(run())
    loop.close()