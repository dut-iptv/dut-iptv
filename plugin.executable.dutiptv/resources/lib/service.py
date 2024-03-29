import xbmc, xbmcaddon

from resources.lib.api import api_get_channels, api_get_all_epg
from resources.lib.util import create_epg, create_playlist

def loop():
    api_get_channels()

    res = api_get_all_epg()

    if res == True:
        create_playlist()
        create_epg()

        try:
            xbmcaddon.Addon('pvr.iptvsimple').setSettingInt("m3uPathType", 0)
        except:
            pass

def main():
    loop()

    while not xbmc.Monitor().waitForAbort(43200):
        loop()