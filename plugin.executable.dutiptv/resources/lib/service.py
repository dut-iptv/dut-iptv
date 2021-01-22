import xbmc, xbmcaddon

from resources.lib.api import api_get_channels, api_get_all_epg
from resources.lib.base.l2.log import log
from resources.lib.base.l3.util import get_kodi_version
from resources.lib.util import create_epg, create_playlist

def loop():
    api_get_channels()

    res = api_get_all_epg()

    if res == True:
        create_playlist()
        create_epg()

        if get_kodi_version() > 18:
            try:
                xbmcaddon.Addon('pvr.iptvsimple').setSettingInt("m3uPathType", 0)
            except:
                pass
        elif not xbmc.getCondVisibility('Pvr.IsPlayingTv') and not xbmc.getCondVisibility('Pvr.IsPlayingRadio'):
            xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.iptvsimple","enabled":false}}')
            xbmc.Monitor().waitForAbort(2)
            xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.iptvsimple","enabled":true}}')

def main():
    loop()

    while not xbmc.Monitor().waitForAbort(43200):
        loop()