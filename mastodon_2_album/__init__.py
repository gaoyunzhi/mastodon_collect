name = 'mastodon_2_album'

from telegram_util import AlbumResult as Result

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

def get(status):
	r = Result()
	r.imgs = getImages(status)
	r.video = getVideo(status)
	r.cap = getCap(status)
	r.url = status.url