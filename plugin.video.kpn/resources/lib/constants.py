from resources.lib.base.l3.language import _

CONST_BASE_URL = 'https://tv.kpn.com'

CONST_BASE_HEADERS = {
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'AVSSite': 'http://www.itvonline.nl',
    'Accept': '*/*',
    'Origin': CONST_BASE_URL,
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': CONST_BASE_URL + '/',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q: 0.9,nl;q: 0.8',
}

CONST_DEFAULT_API = 'https://api.tv.kpn.com/101/1.2.0/A/nld/pctv/kpn'
CONST_IMAGE_URL = 'https://images.tv.kpn.com'

CONST_ONLINE_SEARCH = False

CONST_VOD_CAPABILITY = [
    { 'file': 'series', 'label': _.SERIES, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'kidsseries', 'label': _.KIDS_SERIES, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'kidsmovies', 'label': _.KIDS_MOVIES, 'start': 0, 'online': 0, 'split': 0 },
]

CONST_WATCHLIST = False