name = 'mastodon_2_album'

from telegram_util import AlbumResult as Result
from bs4 import BeautifulSoup
import re

def getReblogsCount(status):
    try:
        return status.reblogs_count + status.reblog.reblogs_count
    except:
        return status.reblogs_count

def getReblogsCountRaw(status):
    try:
        if status.reblogs_count == 0:
            return '%d' % status.reblog.reblogs_count
        return '%d %d' % status.reblog.reblogs_count, status.reblogs_count
    except:
        return '%d' % status.reblogs_count

def getContentText(content):
    soup = BeautifulSoup(content, 'html.parser')
    content = str(soup).replace('<br/>', '\n')
    soup = BeautifulSoup(content, 'html.parser')
    result = []
    for paragraph in soup.find_all('p'):
        text = paragraph.text
        if len(text.split()) == 1 and text.startswith('@'):
            continue
        result.append(text)
    return '\n\n'.join(result)

def getMediaAttachments(status):
    media_attachments = status.media_attachments
    try:
        media_attachments += status.reblog.media_attachments
    except:
        ...
    deduped_media_attachments = []
    media_ids = set()
    for media in media_attachments:
    	if media.id in media_ids:
    		continue
    	deduped_media_attachments.append(media)
    	media_ids.add(media.id)
    return deduped_media_attachments

def getImages(status):
    media_attachments = getMediaAttachments(status)
    if not [media for media in media_attachments if media.type == 'image']:
        return []
    return [media.url for media in media_attachments]

def getVideo(status):
    media_attachments = getMediaAttachments(status)
    if [media for media in media_attachments if media.type == 'image']:
        return
    for media in media_attachments:
        if media.type != 'image':
            return media.url

def getOriginCap(status):
    try:
        return getContentText(status.reblog.content)
    except:
        return ''

def getCap(status):
    cap = getContentText(status.content)
    origin_cap = getOriginCap(status)
    if not origin_cap:
        return cap
    if not cap:
        return origin_cap
    return origin_cap + '\n\n【网评】' + cap

def getUrl(status):
    if status.url and not status.url.endswith('/activity'):
        return status.url
    return status.reblog.url

def get(status):
    r = Result()
    r.imgs = getImages(status)
    r.video = getVideo(status)
    r.cap_html_v2 = getCap(status)
    r.url = getUrl(status)
    return r

def getHash(status):
    cap = getContentText(status.content)
    origin_cap = getOriginCap(status)
    raw_content = origin_cap + cap
    raw_content += ''.join(getImages(status))
    raw_content += str(getVideo(status))
    result = []
    for x in raw_content:
        if re.search(u'[\u4e00-\u9fff]', x):
            result.append(x)
            if len(result) > 10:
                break
    return ''.join(result)

def getAuthor(status):
    try:
        return status.reblog.account
    except:
        return status.account

def getCommenter(status):
    if getAuthor(status).id != status.account.id:
        return status.account

def getUserInfo(account, key):
    if not account:
        return ''
    return '[%s](%s): %s %d' % (key, account.url, account.display_name or account.username, account.id)

def yieldUsersRawInfo(status):
    users = [getCommenter(status), getAuthor(status)]
    users = [user for user in users if user]
    for user in users:
        yield user.id, user.url + ' ' + user.display_name

def getLog(status):
    return 'count: %s ' % getReblogsCountRaw(status) + '%s' + ' %s %s' % (
        getUserInfo(getAuthor(status), 'author'), getUserInfo(getCommenter(status), 'commenter'))

def getCoreContent(status):
    result = []
    for user_id, user_info in yieldUsersRawInfo(status):
        result.append('%d %s' % (user_id, user_info))
    result += [getContentText(status.content), getOriginCap(status)]
    return '=' + ' '.join(result)