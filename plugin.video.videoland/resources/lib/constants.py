from resources.lib.base.l3.language import _

CONST_BASE_DOMAIN = ''
CONST_BASE_DOMAIN_MOD = False
CONST_BASE_IP = ''

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

CONST_CONTINUE_WATCH = True

CONST_FIRST_BOOT = False

CONST_GIGYA_URL = 'https://accounts.eu1.gigya.com'

CONST_HAS_LIVE = True

CONST_HAS_REPLAY = False

CONST_HAS_SEARCH = True

CONST_IMAGES = {
    'still': {
        'large': '1920x1080',
        'small': '720x405',
        'replace': '[format]'
    },
    'poster': {
        'large': '960x1433',
        'small': '400x600',
        'replace': '[format]'
    }
}

CONST_MOD_CACHE = {}

CONST_ONLINE_SEARCH = False

CONST_START_FROM_BEGINNING = False

CONST_USE_PROXY = True

CONST_USE_PROFILES = True

CONST_USE_LIBRARY = True

CONST_LIBRARY = {
    'shows': {
        'series': {
            'online': 1,
            'label': 'SERIES' 
        },
        'kidsseries': {
            'online': 1,
            'label': 'KIDS_SERIES'
        },
    },
    'movies': {
        'movies': {
            'online': 0,
            'label': 'MOVIES'
        },
        'kidsmovies': {
            'online': 0,
            'label': 'KIDS_MOVIES'
        },
    }
}

CONST_VOD_CAPABILITY = [
    { 'file': 'series', 'label': _.SERIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'seriesvideoland', 'label': _.SERIES + ' (Categorie)', 'start': 0, 'menu': 0, 'online': 0, 'search': 0, 'az': 4 },
    { 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'moviesvideoland', 'label': _.MOVIES + ' (Categorie)', 'start': 0, 'menu': 0, 'online': 0, 'search': 0, 'az': 4 },
    { 'file': 'kidsseries', 'label': _.KIDS_SERIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'kidsseriesvideoland', 'label': _.KIDS_SERIES + ' (Categorie)', 'start': 0, 'menu': 0, 'online': 0, 'search': 0, 'az': 4 },
    { 'file': 'kidsmovies', 'label': _.KIDS_MOVIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'kidsmoviesvideoland', 'label': _.KIDS_MOVIES + ' (Categorie)', 'start': 0, 'menu': 0, 'online': 0, 'search': 0, 'az': 4 },
]

CONST_WATCHLIST = True