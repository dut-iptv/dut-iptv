from resources.lib.base.l3.language import _

CONST_BASE_DOMAIN = ''
CONST_BASE_DOMAIN_MOD = False
CONST_BASE_IP = ''

CONST_BASE_URL = 'https://f1tv.formula1.com'

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

CONST_DEFAULT_API = 'https://api.formula1.com/v2/account'

CONST_FIRST_BOOT = False

CONST_HAS_LIVE = False

CONST_HAS_REPLAY = False

CONST_HAS_SEARCH = False

CONST_IMAGE_URL = 'https://ott.formula1.com/image-resizer/image'

CONST_MOD_CACHE = {
    '1510': 0.042
}

CONST_ONLINE_SEARCH = False

CONST_START_FROM_BEGINNING = False

CONST_USE_PROXY = False

CONST_VOD_CAPABILITY = [
    { 'file': 395, 'label': 'Live', 'start': 0, 'menu': 0, 'online': 1, 'search': 0, 'az': 0 },
    { 'file': 1510, 'label': '2021 Season', 'start': 0, 'menu': 1, 'online': 0, 'search': 0, 'az': 0 },
    { 'file': 392, 'label': '2020 Season', 'start': 0, 'menu': 1, 'online': 0, 'search': 0, 'az': 0 },
    { 'file': 2128, 'label': '2019 Season', 'start': 0, 'menu': 1, 'online': 0, 'search': 0, 'az': 0 },
    { 'file': 2130, 'label': '2018 Season', 'start': 0, 'menu': 1, 'online': 0, 'search': 0, 'az': 0 },
    { 'file': 493, 'label': 'Archive', 'start': 0, 'menu': 1, 'online': 0, 'search': 0, 'az': 0 },
    { 'file': 410, 'label': 'Shows', 'start': 0, 'menu': 1, 'online': 0, 'search': 0, 'az': 0 },
    { 'file': 413, 'label': 'Documentaries', 'start': 0, 'menu': 1, 'online': 0, 'search': 0, 'az': 0 },
]

CONST_WATCHLIST = False