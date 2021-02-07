from resources.lib.base.l3.language import _

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

CONST_DEFAULT_API = 'https://api.tv.kpn.com/101/1.2.0/A/nld/pctv/kpn'

CONST_FIRST_BOOT = True

CONST_HAS_LIVE = True

CONST_HAS_REPLAY = True

CONST_IMAGE_URL = 'https://images.tv.kpn.com'

CONST_ONLINE_SEARCH = False

CONST_START_FROM_BEGINNING = True

CONST_VOD_CAPABILITY = [
    { 'file': 'series', 'label': _.SERIES, 'start': 0, 'online': 0, 'search': 1, 'az': 1 },
    { 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'online': 0, 'search': 1, 'az': 1 },
    { 'file': 'kidsseries', 'label': _.KIDS_SERIES, 'start': 0, 'online': 0, 'search': 1, 'az': 1 },
    { 'file': 'kidsmovies', 'label': _.KIDS_MOVIES, 'start': 0, 'online': 0, 'search': 1, 'az': 1 },
]

CONST_WATCHLIST = False