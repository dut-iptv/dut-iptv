import _strptime
import datetime, time, xbmc

from resources.lib.base.l1.constants import ADDON_ID, DEFAULT_USER_AGENT
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, encode_obj, load_file, load_profile, write_file
from resources.lib.base.l4 import gui
from resources.lib.base.l6 import inputstream
from resources.lib.constants import CONST_IMAGE_URL, CONST_IMAGES
from urllib.parse import urlencode

def check_devices():
    pass

def check_entitlements():
    return

def get_image(prefix, content):
    return ''

def get_play_url(content):
    return {'play_url': '', 'locator': ''}

def plugin_ask_for_creds(creds):
    username = str(gui.input(message=_.ASK_USERNAME, default=creds['username'])).strip()

    if not len(str(username)) > 0:
        gui.ok(message=_.EMPTY_USER, heading=_.LOGIN_ERROR_TITLE)
        return {'result': False, 'username': '', 'password': ''}

    password = str(gui.input(message=_.ASK_PASSWORD, hide_input=True)).strip()

    if not len(str(password)) > 0:
        gui.ok(message=_.EMPTY_PASS, heading=_.LOGIN_ERROR_TITLE)
        return {'result': False, 'username': '', 'password': ''}

    return {'result': True, 'username': username, 'password': password}

def plugin_login_error(login_result):
    try:
        if (login_result['code'] == 403 and 'Teveel verschillende apparaten' in login_result['data']):
            gui.ok(message=_.TOO_MANY_DEVICES, heading=_.LOGIN_ERROR_TITLE)
        else:
            gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)
    except:
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

    if check_key(playdata['info'], 'Start') and check_key(playdata['info'], 'End'):
        startT = datetime.datetime.fromtimestamp(time.mktime(time.strptime(playdata['info']['Start'], "%Y-%m-%dT%H:%M:%S")))
        startT = convert_datetime_timezone(startT, "UTC", "UTC")
        endT = datetime.datetime.fromtimestamp(time.mktime(time.strptime(playdata['info']['End'], "%Y-%m-%dT%H:%M:%S")))
        endT = convert_datetime_timezone(endT, "UTC", "UTC")

        write_file(file='stream_start', data=int(time.mktime(time.strptime(playdata['info']['Start'], "%Y-%m-%dT%H:%M:%S"))), isJSON=False)
        write_file(file='stream_end', data=int(time.mktime(time.strptime(playdata['info']['End'], "%Y-%m-%dT%H:%M:%S"))), isJSON=False)

        if check_key(playdata['info'], 'DurationInSeconds'):
            info['duration'] = playdata['info']['DurationInSeconds']
        elif check_key(playdata['info'], 'Duur'):
            info['duration'] = playdata['info']['Duur']
        else:
            info['duration'] = int((endT - startT).total_seconds())

        if xbmc.getLanguage(xbmc.ISO_639_1) == 'nl':
            info['label1'] = '{weekday} {day} {month} {yearhourminute} '.format(weekday=date_to_nl_dag(startT), day=startT.strftime("%d"), month=date_to_nl_maand(startT), yearhourminute=startT.strftime("%Y %H:%M"))
        else:
            info['label1'] = startT.strftime("%A %d %B %Y %H:%M ").capitalize()

    if check_key(playdata['info'], 'Duur'):
        info['duration'] = playdata['info']['Duur']

    if check_key(playdata['info'], 'Title'):
        if len(str(info['label1'])) > 0:
            info['label1'] += " - "

        if len(str(info['label2'])) > 0:
            info['label2'] += " - "

        info['label1'] += playdata['info']['Title']
        info['label2'] += playdata['info']['Title']
    elif check_key(playdata['info'], 'Serie') and check_key(playdata['info']['Serie'], 'Titel') and len(playdata['info']['Serie']['Titel']):
        if len(str(info['label1'])) > 0:
            info['label1'] += " - "

        if len(str(info['label2'])) > 0:
            info['label2'] += " - "

        info['label1'] += playdata['info']['Serie']['Titel']
        info['label2'] += playdata['info']['Serie']['Titel']

        if check_key(playdata['info'], 'Titel') and len(playdata['info']['Titel']) > 0 and playdata['info']['Titel'] != playdata['info']['Serie']['Titel']:
            if len(str(info['label1'])) > 0:
                info['label1'] += ": "

            if len(str(info['label2'])) > 0:
                info['label2'] += ": "

            info['label1'] += playdata['info']['Titel']
            info['label2'] += playdata['info']['Titel']

    if check_key(playdata['info'], 'LongDescription'):
        info['description'] = playdata['info']['LongDescription']
    elif check_key(playdata['info'], 'Omschrijving'):
        info['description'] = playdata['info']['Omschrijving']

    if check_key(playdata['info'], 'CoverUrl'):
        info['image'] = playdata['info']['CoverUrl']
        info['image_large'] = playdata['info']['CoverUrl']
    elif check_key(playdata['info'], 'AfbeeldingUrl'):
        info['image'] = playdata['info']['AfbeeldingUrl']
        info['image_large'] = playdata['info']['AfbeeldingUrl']

    if check_key(playdata['info'], 'ChannelTitle'):
        if len(str(info['label2'])) > 0:
            info['label2'] += " - "

        info['label2'] += playdata['info']['ChannelTitle']
    elif check_key(playdata['info'], 'Zender'):
        if len(str(info['label2'])) > 0:
            info['label2'] += " - "

        info['label2'] += playdata['info']['Zender']

    return info

def plugin_process_playdata(playdata):
    CDMHEADERS = {}

    if check_key(playdata, 'license') and check_key(playdata['license'], 'drmConfig') and check_key(playdata['license']['drmConfig'], 'widevine'):
        if 'nlznl.solocoo.tv' in playdata['license']['drmConfig']['widevine']['drmServerUrl']:
            if xbmc.Monitor().waitForAbort(1):
                return False

        if check_key(playdata['license']['drmConfig']['widevine'], 'customHeaders'):
            for row in playdata['license']['drmConfig']['widevine']['customHeaders']:
                CDMHEADERS[row] = playdata['license']['drmConfig']['widevine']['customHeaders'][row]

        item_inputstream = inputstream.Widevine(
            license_key = playdata['license']['drmConfig']['widevine']['drmServerUrl'],
        )
    else:
        item_inputstream = inputstream.MPD()

    return item_inputstream, CDMHEADERS

def plugin_renew_token(data):
    return None

def plugin_process_watchlist(data, continuewatch=0):
    items = []

    return items

def plugin_process_watchlist_listing(data, id=None, continuewatch=0):
    items = []

    return items
    
def plugin_vod_subscription_filter():
    return None