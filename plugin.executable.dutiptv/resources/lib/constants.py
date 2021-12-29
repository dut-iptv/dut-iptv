from resources.lib.base.l3.language import _

CONST_ADDONS = [
    { 'addonid': 'plugin.video.betelenet', 'label': 'Telenet TV', 'letter': 'b' },
    { 'addonid': 'plugin.video.canaldigitaal', 'label': 'Canal Digitaal IPTV', 'letter': 'c' },
    { 'addonid': 'plugin.video.kpn', 'label': 'KPN ITV', 'letter': 'k' },
    { 'addonid': 'plugin.video.nlziet', 'label': 'NLZiet', 'letter': 'n' },
    { 'addonid': 'plugin.video.tmobile', 'label': 'T-Mobile TV', 'letter': 't' },
    { 'addonid': 'plugin.video.ziggo', 'label': 'Ziggo GO', 'letter': 'z' },
]

CONST_BASE_DOMAIN = ''
CONST_BASE_DOMAIN_MOD = False
CONST_BASE_IP = ''

CONST_BASE_HEADERS = {}

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
    'plugin.video.betelenet': {
        'large': '',
        'small': '',
        'replace': '[format]'
    },
    'plugin.video.canaldigitaal': {
        'large': '',
        'small': '',
        'replace': '[format]'
    },
    'plugin.video.kpn': {
        'large': '',
        'small': '',
        'replace': '[format]'
    },
    'plugin.video.nlziet': {
        'large': '',
        'small': '',
        'replace': '[format]'
    },
    'plugin.video.tmobile': {
        'large': '',
        'small': '',
        'replace': '[format]'
    },
    'plugin.video.ziggo': {
        'large': '',
        'small': '',
        'replace': '[format]'
    },
}

CONST_LIBRARY = {}
CONST_MOD_CACHE = {}
CONST_VOD_CAPABILITY = []
CONST_WATCHLIST = {}
CONST_WATCHLIST_CAPABILITY = {}