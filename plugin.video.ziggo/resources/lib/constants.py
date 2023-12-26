from resources.lib.base.l1.dnsutils import dns_lookup
from resources.lib.base.l3.language import _

CONST_BASE_DOMAIN = 'prod.spark.ziggogo.tv'
CONST_BASE_DOMAIN_MOD = True
CONST_BASE_IP = dns_lookup('prod.spark.ziggogo.tv', "1.0.0.1")['A'][0]

CONST_URLS = {
    'auth_url': "https://prod.spark.ziggogo.tv/auth-service/v1/authorization",
    'base_url': 'https://prod.spark.ziggogo.tv/eng/web/',
    'channels_url': "https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/channels",
    'clearstreams_url': 'https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/playback/clearstreams',
    'customer_url': "https://prod.spark.ziggogo.tv/eng/web/personalization-service/v1/customer",
    'devices_url': "https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/settopboxes/profile",
    'entitlements_url': 'https://prod.spark.ziggogo.tv/eng/web/purchase-service/v2/customers',
    'listings_url': "https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/listings",
    'mediaitems_url': "https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/mediaitems",
    'mediagroupsfeeds_url': "https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web/mediagroups/feeds",
    'search_url': "https://prod.spark.ziggogo.tv/eng/web/discovery-service/v3/search/contents",
    'recording_url': "https://prod.spark.ziggogo.tv/eng/web/recording-service/customers",
    'session_url': "https://prod.spark.ziggogo.tv/eng/web/session-service/session/v2/web-desktop/customers",
    'token_url': 'https://prod.spark.ziggogo.tv/auth-service/v1/mqtt/token',
    'widevine_url': 'https://prod.spark.ziggogo.tv/eng/web/session-manager/license',
    'watchlist_url': 'https://prod.spark.ziggogo.tv/eng/web/watchlist-service/v2/watchlists',                                                                                       
    'web_url': 'https://www.ziggogo.tv'
}

CONST_ALLOWED_HEADERS = {
    'user-agent',
    'x-oesp-content-locator',
    'x-streaming-token',
    'x-client-id',
    'x-oesp-username',
    'x-drm-schemeId'
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
    'onlinesearch': True,
    'profiles': False,
    'proxy': True,
    'recording': True,
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