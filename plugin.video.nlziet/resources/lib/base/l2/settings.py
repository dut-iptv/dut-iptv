import json, xbmcaddon
from resources.lib.base.l1.constants import ADDON_ID

def open(addon=ADDON_ID):
    xbmcaddon.Addon(addon).openSettings()

def getDict(key, default=None, addon=ADDON_ID):
    try:
        return json.loads(get(key, addon=addon))
    except:
        return default

def setDict(key, value, addon=ADDON_ID):
    set(key, json.dumps(value), addon=addon)

def getInt(key, default=None, addon=ADDON_ID):
    try:
        return int(get(key, addon=addon))
    except:
        return default

def setInt(key, value, addon=ADDON_ID):
    set(key, int(value), addon=addon)

def getBool(key, default=False, addon=ADDON_ID):
    value = get(key, addon=addon).lower()

    if not value:
        return default
    else:
        return value == 'true'

def getEnum(key, choices=None, default=None, addon=ADDON_ID):
    index = getInt(key, addon=addon)

    if index == None or not choices:
        return default

    try:
        return choices[index]
    except KeyError:
        return default

def remove(key, addon=ADDON_ID):
    set(key, '', addon=addon)

def setBool(key, value=True, addon=ADDON_ID):
    set(key, 'true' if value else 'false', addon=addon)

def get(key, default='', addon=ADDON_ID):
    return str(xbmcaddon.Addon(addon).getSetting(key)) or str(default)

def set(key, value='', addon=ADDON_ID):
    xbmcaddon.Addon(addon).setSetting(key, str(value))