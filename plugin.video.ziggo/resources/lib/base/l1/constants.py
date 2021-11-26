import os, xbmcaddon, xbmcvfs

##### ADDON ####
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')

PROVIDER_NAME = ADDON_ID.replace('plugin.video.', '')

ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
ADDON_PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

ADDONS_PATH = xbmcvfs.translatePath('special://home') + 'addons' + os.sep

ADDON_ICON = ADDON.getAddonInfo('icon')
ADDON_FANART = ADDON.getAddonInfo('fanart')
ADDON_VERSION = ADDON.getAddonInfo('version')

#################

CONST_DUT_EPG_BASE = 'https://dut-epg.github.io'
CONST_DUT_EPG = '{base_epg}/{provider}'.format(base_epg=CONST_DUT_EPG_BASE, provider=PROVIDER_NAME)

try:
    CONST_DUT_EPG_SETTINGS = '{base_epg}/{letter}.settings.json'.format(base_epg=CONST_DUT_EPG_BASE, letter=PROVIDER_NAME[0])
except:
    CONST_DUT_EPG_SETTINGS = '{base_epg}/a.settings.json'.format(base_epg=CONST_DUT_EPG_BASE)

CONST_ADDONS = [
    { 'addonid': 'plugin.video.betelenet', 'label': 'Telenet TV', 'letter': 'b' },
    { 'addonid': 'plugin.video.canaldigitaal', 'label': 'Canal Digitaal IPTV', 'letter': 'c' },
    { 'addonid': 'plugin.video.kpn', 'label': 'KPN ITV', 'letter': 'k' },
    { 'addonid': 'plugin.video.nlziet', 'label': 'NLZiet', 'letter': 'n' },
    { 'addonid': 'plugin.video.tmobile', 'label': 'T-Mobile TV', 'letter': 't' },
    { 'addonid': 'plugin.video.ziggo', 'label': 'Ziggo GO', 'letter': 'z' },
]

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
DEFAULT_BROWSER_NAME = 'Chrome'
DEFAULT_BROWSER_VERSION = '87.0.4280.88'
DEFAULT_OS_NAME = 'Windows'
DEFAULT_OS_VERSION = '10'

#### SESSION ####
SESSION_CHUNKSIZE = 4096
#################

AUDIO_LANGUAGES = {
    'nl': 'Nederlands/Dutch',
    'en': 'Engels/English',
    'gos': 'Gesproken ondertiteling/Spoken subtitles',
    'unk': 'Onbekend/Unknown'
}