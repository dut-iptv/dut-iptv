import xbmcaddon, xbmcvfs

from resources.lib.dnsutils import dns_lookup

CONST_BASE_DOMAIN = {}
CONST_BASE_IP = {}

CONST_BASE_DOMAIN['ziggo'] = 'prod.spark.ziggogo.tv'

try:
    CONST_BASE_IP['ziggo'] = dns_lookup('prod.spark.ziggogo.tv', "1.0.0.1")['A'][0]
except:
    pass

CONST_BASE_DOMAIN['betelenet'] = 'prod.spark.telenettv.be'

try:
    CONST_BASE_IP['betelenet'] = dns_lookup('prod.spark.telenettv.be', "1.0.0.1")['A'][0]
except:
    pass

PROXY_PROFILE = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))

CONST_ALLOWED_HEADERS = {}

CONST_ALLOWED_HEADERS['betelenet'] = {
    'user-agent',
    'x-oesp-content-locator',
    'x-streaming-token',
    'x-client-id',
    'x-oesp-username',
    'x-drm-schemeId'
}

CONST_ALLOWED_HEADERS['ziggo'] = {
    'user-agent',
    'x-oesp-content-locator',
    'x-streaming-token',
    'x-client-id',
    'x-oesp-username',
    'x-drm-schemeId'
}

CONST_BASE_HEADERS = {}

CONST_BASE_HEADERS['betelenet'] = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': 'https://www.telenettv.be',
    'Pragma': 'no-cache',
    'Referer': 'https://www.telenettv.be/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
}

CONST_BASE_HEADERS['canaldigitaal'] = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q: 0.9,nl;q: 0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': 'https://livetv.canaldigitaal.nl',
    'Pragma': 'no-cache',
    'Referer': 'https://livetv.canaldigitaal.nl/',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
}

CONST_BASE_HEADERS['kpn'] = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q: 0.9,nl;q: 0.8',
    'AVSSite': 'http://www.itvonline.nl',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': 'https://tv.kpn.com',
    'Pragma': 'no-cache',
    'Referer': 'https://tv.kpn.com/',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
}

CONST_BASE_HEADERS['nlziet'] = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': 'https://app.nlziet.nl',
    'Pragma': 'no-cache',
    'Referer': 'https://app.nlziet.nl/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

CONST_BASE_HEADERS['tmobile'] = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': 'https://t-mobiletv.nl',
    'Pragma': 'no-cache',
    'Referer': 'https://t-mobiletv.nl/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

CONST_BASE_HEADERS['videoland'] = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': 'https://www.videoland.com',
    'Pragma': 'no-cache',
    'Referer': 'https://www.videoland.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

CONST_BASE_HEADERS['ziggo'] = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': 'https://www.ziggogo.tv',
    'Pragma': 'no-cache',
    'Referer': 'https://www.ziggogo.tv/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
}

AUDIO_LANGUAGES_REV = {
    'Nederlands/Dutch': 'nl',
    'Engels/English': 'en',
    'Gesproken ondertiteling/Spoken subtitles': 'gos',
    'Onbekend/Unknown': 'unk'
}

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'