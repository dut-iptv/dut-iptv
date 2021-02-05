from resources.lib.base.l3.language import _

CONST_BASE_URL = 'https://t-mobiletv.nl'

CONST_BASE_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': CONST_BASE_URL,
    'Pragma': 'no-cache',
    'Referer': CONST_BASE_URL + '/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

CONST_FIRST_BOOT = True

CONST_HAS_LIVE = True

CONST_HAS_REPLAY = True

CONST_ONLINE_SEARCH = False

CONST_START_FROM_BEGINNING = True

CONST_VOD_CAPABILITY = [
    { 'file': 'series', 'label': _.SERIES, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'film1', 'label': _.FILM1, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'videoshop', 'label': _.VIDEOSHOP, 'start': 0, 'online': 0, 'split': 0 },
]

CONST_WATCHLIST = False