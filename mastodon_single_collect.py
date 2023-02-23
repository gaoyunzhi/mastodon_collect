from mastodon_collect import mastodonSingleCollect, credential
import sys
from mastodon import Mastodon 

if __name__ == '__main__':
    mastodon = Mastodon(
        access_token = 'db/main_mastodon_secret',
        api_base_url = credential['mastodon_domain']
    )
    mastodonSingleCollect(mastodon, int(sys.argv[1]))