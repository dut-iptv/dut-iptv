from resources.lib.base.l3.language import _

base = "https://web-api-pepper.horizon.tv/oesp/v2"
base_three = "https://web-api-prod-obo.horizon.tv/oesp/v3"
complete_base_url = '{base_url}/NL/nld'.format(base_url=base)
complete_base_url_three = '{base_url}/NL/nld'.format(base_url=base_three)

CONST_API_URLS = {}

CONST_API_URLS[0] = {
    'base_url': complete_base_url + '/web',
    'clearstreams_url': 'https://web-api-pepper.horizon.tv/oesp/v2/NL/nld/web/playback/clearstreams',
    'devices_url': "https://web-api-pepper.horizon.tv/oesp/v2/NL/nld/web/settopboxes/profile",
    'search_url': "https://web-api-pepper.horizon.tv/oesp/v2/NL/nld/web/search/content",
    'session_url': "https://web-api-pepper.horizon.tv/oesp/v2/NL/nld/web/session",
    'channels_url': "https://web-api-pepper.horizon.tv/oesp/v2/NL/nld/web/channels",
    'token_url': '{complete_base_url}/web/license/token'.format(complete_base_url=complete_base_url),
    'widevine_url': '{complete_base_url}/web/license/eme'.format(complete_base_url=complete_base_url),
    'listings_url': "https://web-api-pepper.horizon.tv/oesp/v2/NL/nld/web/listings",
    'mediaitems_url': "https://web-api-pepper.horizon.tv/oesp/v2/NL/nld/web/mediaitems",
    'mediagroupsfeeds_url': "https://web-api-pepper.horizon.tv/oesp/v2/NL/nld/web/mediagroups/feeds",
    'watchlist_url': "https://web-api-pepper.horizon.tv/oesp/v2/NL/nld/web/watchlists/later"
}

CONST_API_URLS[1] = {
    'base_url': complete_base_url_three + '/web',
    'clearstreams_url': 'https://web-api-prod-obo.horizon.tv/oesp/v3/NL/nld/web/playback/clearstreams',
    'devices_url': "https://web-api-prod-obo.horizon.tv/oesp/v3/NL/nld/web/settopboxes/profile",
    'search_url': "https://web-api-prod-obo.horizon.tv/oesp/v3/NL/nld/web/search/content",
    'session_url': "https://web-api-prod-obo.horizon.tv/oesp/v3/NL/nld/web/session",
    'channels_url': "https://web-api-prod-obo.horizon.tv/oesp/v3/NL/nld/web/channels",
    'token_url': '{complete_base_url_three}/web/license/token'.format(complete_base_url_three=complete_base_url_three),
    'widevine_url': '{complete_base_url_three}/web/license/eme'.format(complete_base_url_three=complete_base_url_three),
    'listings_url': "https://web-api-prod-obo.horizon.tv/oesp/v3/NL/nld/web/listings",
    'mediaitems_url': "https://web-api-prod-obo.horizon.tv/oesp/v3/NL/nld/web/mediaitems",
    'mediagroupsfeeds_url': "https://web-api-prod-obo.horizon.tv/oesp/v3/NL/nld/web/mediagroups/feeds",
    'watchlist_url': 'https://prod.spark.ziggogo.tv/nld/web/watchlist-service/v1/watchlists'
}

CONST_ALLOWED_HEADERS = {
    'user-agent',
    'x-oesp-content-locator',
    'x-oesp-token',
    'x-client-id',
    'x-oesp-username',
    'x-oesp-drm-schemeiduri'
}

CONST_BASE_URL = 'https://www.ziggogo.tv'

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

CONST_DEFAULT_CLIENTID = '4.23.13'

CONST_ONLINE_SEARCH = False

CONST_START_FROM_BEGINNING = True

CONST_VOD_CAPABILITY = [
    { 'file': 'series', 'label': _.SERIES, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'hboseries', 'label': _.HBO_SERIES, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'hbomovies', 'label': _.HBO_MOVIES, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'kidsseries', 'label': _.KIDS_SERIES, 'start': 0, 'online': 0, 'split': 0 },
    { 'file': 'kidsmovies', 'label': _.KIDS_MOVIES, 'start': 0, 'online': 0, 'split': 0 },
]

CONST_WATCHLIST = False