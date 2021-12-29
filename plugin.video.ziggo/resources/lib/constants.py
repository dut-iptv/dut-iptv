from resources.lib.base.l1.dnsutils import dns_lookup
from resources.lib.base.l3.language import _

CONST_BASE_DOMAIN = 'obo-prod.oesp.ziggogo.tv'
CONST_BASE_DOMAIN_MOD = True
CONST_BASE_IP = dns_lookup('obo-prod.oesp.ziggogo.tv', "1.0.0.1")['A'][0]

CONST_URLS = {
    'base_url': 'https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web',
    'channels_url': "https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/channels",
    'clearstreams_url': 'https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/playback/clearstreams',
    'devices_url': "https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/settopboxes/profile",
    'listings_url': "https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/listings",
    'mediaitems_url': "https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/mediaitems",
    'mediagroupsfeeds_url': "https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/mediagroups/feeds",
    'search_url': "https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/search/content",
    'session_url': "https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/session",
    'token_url': 'https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld//web/license/token',
    'widevine_url': 'https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld//web/license/eme',
    'watchlist_url': 'https://prod.spark.ziggogo.tv/nld/web/watchlist-service/v1/watchlists',                                                                                       
    'web_url': 'https://www.ziggogo.tv'
}

CONST_ALLOWED_HEADERS = {
    'user-agent',
    'x-oesp-content-locator',
    'x-oesp-token',
    'x-client-id',
    'x-oesp-username',
    'x-oesp-drm-schemeiduri'
}

CONST_BASE_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': CONST_URLS['web_url'],
    'Pragma': 'no-cache',
    'Referer': '{web_url}/'.format(web_url=CONST_URLS['web_url']),
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
}

CONST_DEFAULT_CLIENTID = '4.23.13'

CONST_FIRST_BOOT = {
    'erotica': True,
    'minimal': True,
    'regional': True,
    'home': False
}

CONST_HAS = {
    'dutiptv': True,
    'library': False,
    'live': True,
    'onlinesearch': False,
    'profiles': False,
    'proxy': True,
    'replay': True,
    'search': True,
    'startfrombeginning': True,
    'upnext': False,
}

CONST_IMAGES = {
    'still': {
        'large': '',
        'small': '',
        'replace': '[format]'
    },
    'poster': {
        'large': '',
        'small': '',
        'replace': '[format]'
    },
    'replay': {
        'large': '',
        'small': '',
        'replace': '[format]'
    },
    'vod': {
        'large': '',
        'small': '',
        'replace': '[format]'
    },
}

CONST_LIBRARY = {}

CONST_MOD_CACHE = {}

CONST_VOD_CAPABILITY = [
    { 'file': 'series', 'label': _.SERIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'hboseries', 'label': _.HBO_SERIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'hbomovies', 'label': _.HBO_MOVIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'kidsseries', 'label': _.KIDS_SERIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'kidsmovies', 'label': _.KIDS_MOVIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
]

#"show"
#"series"
#"Serie"
#"season"
#"episode"
#"event"
#"Epg"
#"Vod"

CONST_WATCHLIST = {}

CONST_WATCHLIST_CAPABILITY = {}