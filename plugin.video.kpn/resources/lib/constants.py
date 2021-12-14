from resources.lib.base.l3.language import _

CONST_BASE_DOMAIN = ''
CONST_BASE_DOMAIN_MOD = False
CONST_BASE_IP = ''

CONST_BASE_URL = 'https://tv.kpn.com'

CONST_BASE_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'AVSSite': 'http://www.itvonline.nl',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': CONST_BASE_URL,
    'Pragma': 'no-cache',
    'Referer': CONST_BASE_URL + '/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

CONST_CONTINUE_WATCH = False

CONST_DEFAULT_API = 'https://api.tv.kpn.com/101/1.2.0/A/nld/pctv/kpn'

CONST_FIRST_BOOT = True

CONST_HAS_DUTIPTV = True

CONST_HAS_LIBRARY = False

CONST_HAS_LIVE = True

CONST_HAS_REPLAY = True

CONST_HAS_SEARCH = True

CONST_IMAGES = {
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

CONST_IMAGE_URL = 'https://images.tv.kpn.com'

CONST_LIBRARY = {}

CONST_MOD_CACHE = {}

CONST_ONLINE_SEARCH = False

CONST_START_FROM_BEGINNING = True

CONST_USE_PROXY = True

CONST_USE_PROFILES = False

CONST_VOD_CAPABILITY = [
    { 'file': 'series', 'label': _.SERIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 1 },
    { 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 1 },
    { 'file': 'kidsseries', 'label': _.KIDS_SERIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 1 },
    { 'file': 'kidsmovies', 'label': _.KIDS_MOVIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 1 },
]

CONST_WATCHLIST = False