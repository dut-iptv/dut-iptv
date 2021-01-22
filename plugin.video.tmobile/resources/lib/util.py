import _strptime
import datetime, re, xbmc

from resources.lib.base.l1.constants import DEFAULT_USER_AGENT
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, load_file, load_profile, write_file
from resources.lib.base.l4 import gui
from resources.lib.base.l5.api import api_get_channels
from resources.lib.base.l6 import inputstream

try:
    unicode
except NameError:
    unicode = str

def plugin_ask_for_creds(creds):
    username = unicode(gui.input(message=_.ASK_USERNAME, default=creds['username'])).strip()

    if not len(unicode(username)) > 0:
        gui.ok(message=_.EMPTY_USER, heading=_.LOGIN_ERROR_TITLE)

        return {'result': False, 'username': '', 'password': ''}

    password = unicode(gui.input(message=_.ASK_PASSWORD, hide_input=True)).strip()

    if not len(unicode(password)) > 0:
        gui.ok(message=_.EMPTY_PASS, heading=_.LOGIN_ERROR_TITLE)

        return {'result': False, 'username': '', 'password': ''}

    return {'result': True, 'username': username, 'password': password}

def plugin_login_error(login_result):
    if check_key(login_result['data'], 'result') and check_key(login_result['data']['result'], 'retCode') and login_result['data']['result']['retCode'] == "157022007":
        gui.ok(message=_.TOO_MANY_DEVICES, heading=_.LOGIN_ERROR_TITLE)
    else:
        gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)

def plugin_post_login():
    pass

def plugin_process_info(playdata):
    info = {
        'label1': '',
        'label2': '',
        'description': '',
        'image': '',
        'image_large': '',
        'duration': 0,
        'credits': [],
        'cast': [],
        'director': [],
        'writer': [],
        'genres': [],
        'year': '',
    }

    if check_key(playdata['info'], 'startTime') and check_key(playdata['info'], 'endTime'):
        startT = datetime.datetime.fromtimestamp(int(int(playdata['info']['startTime']) // 1000))
        startT = convert_datetime_timezone(startT, "UTC", "UTC")
        endT = datetime.datetime.fromtimestamp(int(int(playdata['info']['endTime']) // 1000))
        endT = convert_datetime_timezone(endT, "UTC", "UTC")

        write_file(file='stream_start', data=int(int(playdata['info']['startTime']) // 1000), isJSON=False)
        write_file(file='stream_end', data=int(int(playdata['info']['endTime']) // 1000), isJSON=False)

        info['duration'] = int((endT - startT).total_seconds())

        if xbmc.getLanguage(xbmc.ISO_639_1) == 'nl':
            info['label1'] = '{weekday} {day} {month} {yearhourminute} '.format(weekday=date_to_nl_dag(startT), day=startT.strftime("%d"), month=date_to_nl_maand(startT), yearhourminute=startT.strftime("%Y %H:%M"))
        else:
            info['label1'] = startT.strftime("%A %d %B %Y %H:%M ").capitalize()

        info['label1'] += " - "

    if check_key(playdata['info'], 'name'):
        info['label1'] += playdata['info']['name']
        info['label2'] = playdata['info']['name']

    if check_key(playdata['info'], 'introduce'):
        info['description'] = playdata['info']['introduce']

    if check_key(playdata['info'], 'picture'):
        info['image'] = playdata['info']['picture']['posters'][0]
        info['image_large'] = playdata['info']['picture']['posters'][0]

    data = api_get_channels()

    try:
        info['label2'] += " - "  + data[unicode(playdata['channel'])]['name']
    except:
        pass

    return info

def plugin_process_playdata(playdata):
    profile_settings = load_profile(profile_id=1)

    CDMHEADERS = {
        'User-Agent': DEFAULT_USER_AGENT,
        'X_CSRFToken': profile_settings['csrf_token'],
        'Cookie': playdata['license']['cookie'],
    }

    if check_key(playdata, 'license') and check_key(playdata['license'], 'triggers') and check_key(playdata['license']['triggers'][0], 'licenseURL'):
        item_inputstream = inputstream.Widevine(
            license_key = playdata['license']['triggers'][0]['licenseURL'],
        )

        if check_key(playdata['license']['triggers'][0], 'customData'):
            CDMHEADERS['AcquireLicense.CustomData'] = playdata['license']['triggers'][0]['customData']
            CDMHEADERS['CADeviceType'] = 'Widevine OTT client'
    else:
        item_inputstream = inputstream.MPD()

    return item_inputstream, CDMHEADERS

def plugin_renew_token(data):
    return None

def plugin_vod_subscription_filter():
    return None

def plugin_process_watchlist(data):
    items = []

    return items

def plugin_process_watchlist_listing(data, id=None):
    items = []

    return items