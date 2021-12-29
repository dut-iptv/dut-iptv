from resources.lib.base.l3.language import _

CONST_BASE_DOMAIN = ''
CONST_BASE_DOMAIN_MOD = False
CONST_BASE_IP = ''

CONST_URLS = {
    'base': 'https://www.videoland.com',
    'gigya': 'https://accounts.eu1.gigya.com'
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
    'library': True,
    'live': True,
    'onlinesearch': False,
    'profiles': True,
    'proxy': True,
    'replay': False,
    'search': True,
    'startfrombeginning': False,
    'upnext': True,
}

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
    },
    'replay': {
        'large': '1920x1080',
        'small': '720x405',
        'replace': '[format]'
    },
    'vod': {
        'large': '960x1433',
        'small': '400x600',
        'replace': '[format]'
    },
}

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

CONST_MOD_CACHE = {}

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

#"show"
#"series"
#"Serie"
#"season"
#"episode"
#"event"
#"Epg"
#"Vod"

CONST_WATCHLIST = {
    'vod': {
        'show': {
            'type': 'watchlist'
        },
        'series': {
            'type': 'watchlist'
        },
        'season': {
            'type': 'watchlist'
        },
        'episode': {
            'type': 'watchlist'
        },
        'movie': {
            'type': 'watchlist'
        },
    },
    'replay': {

    }
}

CONST_WATCHLIST_CAPABILITY = {
    'watchlist': {
        'label': _.WATCHLIST,
        'add': 1,
        'addlist': _.ADD_TO_WATCHLIST,
        'addsuccess': _.ADDED_TO_WATCHLIST,
        'addfailed': _.ADD_TO_WATCHLIST_FAILED,
        'remove': 1,
        'removelist': _.REMOVE_FROM_WATCHLIST,
        'removesuccess': _.REMOVED_FROM_WATCHLIST,
        'removefailed': _.REMOVE_FROM_WATCHLIST_FAILED
    },
    'continuewatch': {
        'label': _.CONTINUE_WATCH,
        'add': 0,
        'addlist': '',
        'addsuccess': '',
        'addfailed': '',
        'remove': 1,
        'removelist': _.REMOVE_FROM_CONTINUE,
        'removesuccess': _.REMOVED_FROM_CONTINUE,
        'removefailed': _.REMOVE_FROM_CONTINUE_FAILED
    },
}