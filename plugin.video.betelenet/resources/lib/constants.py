from resources.lib.base.l3.language import _

base = "https://obo-prod.oesp.telenettv.be/oesp/v4"
complete_base_url = '{base_url}/BE/nld'.format(base_url=base)

CONST_API_URLS = {}

CONST_API_URLS[0] = {
    'base_url': complete_base_url + '/web',
    'clearstreams_url': 'https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/playback/clearstreams',
    'devices_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/settopboxes/profile",
    'search_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/search/content",
    'session_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/session",
    'channels_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/channels",
    'token_url': '{complete_base_url}/web/license/token'.format(complete_base_url=complete_base_url),
    'widevine_url': '{complete_base_url}/web/license/eme'.format(complete_base_url=complete_base_url),
    'listings_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/listings",
    'mediaitems_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/mediaitems",
    'mediagroupsfeeds_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/mediagroups/feeds",
    'watchlist_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/watchlists/later"
}

CONST_ALLOWED_HEADERS = {
    'user-agent',
    'x-oesp-content-locator',
    'x-oesp-token',
    'x-client-id',
    'x-oesp-username',
    'x-oesp-drm-schemeiduri'
}

CONST_BASE_URL = 'https://www.telenettv.be'

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
    'Sec-Fetch-Site': 'cross-site',
}

CONST_DEFAULT_CLIENTID = '4.29.11'

CONST_FIRST_BOOT = True

CONST_HAS_LIVE = True

CONST_HAS_REPLAY = True

CONST_ONLINE_SEARCH = False

CONST_START_FROM_BEGINNING = True

CONST_VOD_CAPABILITY = [
    { 'file': 'series', 'label': _.SERIES, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'alacarte', 'label': _.ALACARTE, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'kidsseries', 'label': _.KIDS_SERIES, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'kidsmovies', 'label': _.KIDS_MOVIES, 'start': 0, 'online': 0, 'split': 0 },
]

CONST_WATCHLIST = False