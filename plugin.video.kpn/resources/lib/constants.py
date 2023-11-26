from resources.lib.base.l3.language import _

CONST_BASE_DOMAIN = ''
CONST_BASE_DOMAIN_MOD = False
CONST_BASE_IP = ''

CONST_URLS = {
    'api': 'https://api.tv.prod.itvavs.prod.aws.kpn.com/101/1.2.0/A/nld/pctv/kpn',
    'base': 'https://tv.kpn.com',
    'image': 'https://images.tv.kpn.com'
}

CONST_BASE_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'AVSSite': 'http://www.itvonline.nl',
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
    'erotica': True,
    'minimal': True,
    'regional': True,
    'home': True
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
    { 'file': 'series', 'label': _.SERIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 1 },
    { 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 1 },
    { 'file': 'kidsseries', 'label': _.KIDS_SERIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 1 },
    { 'file': 'kidsmovies', 'label': _.KIDS_MOVIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 1 },
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
