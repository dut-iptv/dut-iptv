from resources.lib.base.l3.language import _

CONST_BASE_DOMAIN = ''
CONST_BASE_DOMAIN_MOD = False
CONST_BASE_IP = ''

CONST_URLS = {
    'api': 'https://api.nlziet.nl',
    'app': 'https://app.nlziet.nl',
    'base': 'https://www.nlziet.nl',
    'id': 'https://id.nlziet.nl',
    'image': 'https://nlzietprodstorage.blob.core.windows.net',
}

CONST_BASE_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': CONST_URLS['app'],
    'Pragma': 'no-cache',
    'Referer': CONST_URLS['app'],
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

CONST_FIRST_BOOT = {
    'erotica': False,
    'minimal': False,
    'regional': True,
    'home': False
}

CONST_HAS = {
    'dutiptv': True,
    'library': True,
    'live': True,
    'onlinesearch': False,
    'profiles': True,
    'proxy': True,
    'replay': True,
    'search': True,
    'startfrombeginning': False,
    'upnext': True,
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

CONST_LIBRARY = {
    'shows': {
        'series': {
            'online': 1,
            'label': 'SERIESBINGE'
        },
    },
    'movies': {
        'movies': {
            'online': 0,
            'label': 'MOVIES'
        },
    }
}

CONST_MOD_CACHE = {}

CONST_VOD_CAPABILITY = [
    { 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 1 },
    { 'file': 'series', 'label': _.SERIESBINGE, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 1 },
    { 'file': 'tipfeednpo', 'label': _.RECOMMENDED + ' NPO', 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    { 'file': 'tipfeed', 'label': _.RECOMMENDED, 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    { 'file': 'watchaheadnpo', 'label': _.WATCHAHEAD + ' NPO', 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    { 'file': 'watchahead', 'label': _.WATCHAHEAD, 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    #{ 'file': 'moviesnpo', 'label': _.MOVIES + ' NPO', 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    #{ 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    #{ 'file': 'seriesbingenpo', 'label': _.SERIESBINGE + ' NPO', 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    #{ 'file': 'seriesbinge', 'label': _.SERIESBINGE, 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    { 'file': 'mostviewed', 'label': _.MOSTVIEWED, 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
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
        'Serie': {
            'type': 'watchlist'
        },
        'season': {
            'type': 'watchlist'
        },
        'episode': {
            'type': 'continuewatch'
        },
        'movie': {
            'type': 'continuewatch'
        },
        'Epg': {
            'type': 'continuewatch'
        },
        'Vod': {
            'type': 'continuewatch'
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
        'add': 1,
        'addlist': _.ADD_TO_CONTINUE,
        'addsuccess': _.ADDED_TO_CONTINUE,
        'addfailed': _.ADD_TO_CONTINUE_FAILED,
        'remove': 1,
        'removelist': _.REMOVE_FROM_CONTINUE,
        'removesuccess': _.REMOVED_FROM_CONTINUE,
        'removefailed': _.REMOVE_FROM_CONTINUE_FAILED
    },
}