from resources.lib.base.l3.language import _

CONST_BASE_DOMAIN = ''
CONST_BASE_DOMAIN_MOD = False
CONST_BASE_IP = ''

CONST_BASE_URL = 'https://livetv.canaldigitaal.nl'
CONST_DEFAULT_API = 'https://tvapi.solocoo.tv/v1'
CONST_LOGIN_URL = 'https://login.canaldigitaal.nl'

CONST_LOGIN_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'deflate, br',
    'Accept-Language': 'en-US,en;q: 0.9,nl;q: 0.8',
    'Cache-Control': 'no-cache',
    'Content-Type': 'application/x-www-form-urlencoded',
    'DNT': '1',
    'Origin': CONST_LOGIN_URL,
    'Pragma': 'no-cache',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
}

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

CONST_CONTINUE_WATCH = False

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

CONST_LIBRARY = {}

CONST_MOD_CACHE = {}

CONST_START_FROM_BEGINNING = True

CONST_ONLINE_SEARCH = False

CONST_USE_PROXY = True

CONST_USE_PROFILES = False

CONST_VOD_CAPABILITY = [
    { 'file': 'cnlseriesnl', 'label': 'Canal+ ' + _.SERIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'film1', 'label': 'Film1', 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'cnlvodnl', 'label': 'Canal Video On Demand', 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 1 },
    { 'file': 'bbcsnl', 'label': 'BBC', 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 1 },
    { 'file': 'lovnaten', 'label': 'Love Nature', 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 1 },
]

CONST_WATCHLIST = False