from resources.lib.base.l3.language import _

CONST_BASE_URL = 'https://www.videoland.com'

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

CONST_FIRST_BOOT = False

CONST_GIGYA_URL = 'https://accounts.eu1.gigya.com'

CONST_HAS_LIVE = False

CONST_HAS_REPLAY = False

CONST_ONLINE_SEARCH = False

CONST_START_FROM_BEGINNING = False

CONST_VOD_CAPABILITY = [
    { 'file': 'series', 'label': _.SERIES, 'start': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'kidsseries', 'label': _.KIDS_SERIES, 'start': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'kidsmovies', 'label': _.KIDS_MOVIES, 'start': 0, 'online': 0, 'search': 1, 'az': 2 },
]

CONST_WATCHLIST = False