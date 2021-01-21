import xbmc

from resources.lib.api import api_get_channels, api_get_all_epg
from resources.lib.util import create_epg, create_playlist

def loop():
    api_get_channels()

    if api_get_all_epg() == True:
        create_playlist()
        create_epg()
        xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.iptvsimple","enabled":false}}')
        xbmc.sleep(2000)
        xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.iptvsimple","enabled":true}}')

def main():
    loop()

    while not xbmc.Monitor().waitForAbort(43200):
        loop()