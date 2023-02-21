name = 'mastodon_2_album'

from telegram_util import AlbumResult as Result
from bs4 import BeautifulSoup
import re

def getReblogsCount(status):
    try:
        return status.reblogs_count + status.reblog.reblogs_count
    except:
        return status.reblogs_count

def getContentText(content):
    soup = BeautifulSoup(content, 'html.parser')
    return soup.text

def getMediaAttachments(status):
	media_attachments = status.media_attachments
	try:
		media_attachments += status.reblog.media_attachments
	except:
		...
	return media_attachments

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
	if status.url:
		return status.url
	return status.reblog.url

def get(status):
	r = Result()
	r.imgs = getImages(status)
	r.video = getVideo(status)
	r.cap = getCap(status)
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
	return '[%s](%s): %s' % (key, account.url, account.display_name)

def getLog(status):
	return 'count: %d %s %s' % (getReblogsCount(status), 
		getUserInfo(getAuthor(status), 'author'), getUserInfo(getAuthor(status), 'commenter')