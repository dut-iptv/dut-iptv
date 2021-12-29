from resources.lib.base.l3.language import _

CONST_BASE_DOMAIN = ''
CONST_BASE_DOMAIN_MOD = False
CONST_BASE_IP = ''

CONST_URLS = {
    'api': 'https://api.formula1.com/v2/account',
    'base': 'https://f1tv.formula1.com',
    'image': 'https://f1tv.formula1.com/image-resizer/image',
}

CONST_BASE_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': CONST_URLS['base'],
    'Pragma': 'no-cache',
    'Referer': '{}/'.format(CONST_URLS['base']),
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

CONST_FIRST_BOOT = {
    'erotica': False,
    'minimal': False,
    'regional': False,
    'home': False
}

CONST_HAS = {
    'dutiptv': False,
    'library': False,
    'live': False,
    'onlinesearch': False,
    'profiles': False,
    'proxy': False,
    'replay': False,
    'search': False,
    'startfrombeginning': False,
    'upnext': False,
}

CONST_IMAGES = {
    'vod': {
        'large': '',
        'small': '',
        'replace': '[format]'
    },
}

CONST_LIBRARY = {}

CONST_MAIN_VOD_AR = ['395', '1510', '392', '2128', '2130', '493', '410', '413', '3675', '3673', '3946', '804']

CONST_MOD_CACHE = {}

CONST_VOD_CAPABILITY = [
    { 'file': 395, 'label': 'Live', 'start': 0, 'menu': 0, 'online': 1, 'search': 0, 'az': 0 },
    { 'file': 1510, 'label': '2021 Season', 'start': 0, 'menu': 1, 'online': 2, 'search': 0, 'az': 0 },
    { 'file': 392, 'label': '2020 Season', 'start': 0, 'menu': 1, 'online': 2, 'search': 0, 'az': 0 },
    { 'file': 2128, 'label': '2019 Season', 'start': 0, 'menu': 1, 'online': 2, 'search': 0, 'az': 0 },
    { 'file': 2130, 'label': '2018 Season', 'start': 0, 'menu': 1, 'online': 2, 'search': 0, 'az': 0 },  
    { 'file': 493, 'label': 'Archive', 'start': 0, 'menu': 1, 'online': 2, 'search': 0, 'az': 0 },
    { 'file': 410, 'label': 'Shows', 'start': 0, 'menu': 1, 'online': 2, 'search': 0, 'az': 0 },
    { 'file': 413, 'label': 'Documentaries', 'start': 0, 'menu': 1, 'online': 2, 'search': 0, 'az': 0 },
    { 'file': 3675, 'label': 'F2', 'start': 0, 'menu': 1, 'online': 2, 'search': 0, 'az': 0 },
    { 'file': 3673, 'label': 'F3', 'start': 0, 'menu': 1, 'online': 2, 'search': 0, 'az': 0 },
    { 'file': 3946, 'label': 'Porsche Mobil 1 Supercup', 'start': 0, 'menu': 1, 'online': 2, 'search': 0, 'az': 0 },
    { 'file': 804, 'label': 'W Series', 'start': 0, 'menu': 1, 'online': 2, 'search': 0, 'az': 0 },
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