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
    #if check_key(login_result['data'], 'result') and check_key(login_result['data']['result'], 'retCode') and login_result['data']['result']['retCode'] == "157022007":
    #    gui.ok(message=_.TOO_MANY_DEVICES, heading=_.LOGIN_ERROR_TITLE)
    #else:
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

    if check_key(playdata['info'], 'title'):
        info['label1'] += playdata['info']['title']
        info['label2'] = playdata['info']['title']

    if check_key(playdata['info'], 'runtime'):
        info['duration'] = int(playdata['info']['runtime'])

    if check_key(playdata['info'], 'description'):
        info['description'] = playdata['info']['description']

    if check_key(playdata['info'], 'still'):
        info['image'] = str(playdata['info']['still']).replace('[format]', '1920x1080')
        info['image_large'] = str(playdata['info']['still']).replace('[format]', '1920x1080')
    elif check_key(playdata['info'], 'poster'):
        info['image'] = str(playdata['info']['poster']).replace('[format]', '960x1433')
        info['image_large'] = str(playdata['info']['poster']).replace('[format]', '960x1433')

    if check_key(playdata['info'], 'year'):
        info['year'] = playdata['info']['year']

    if check_key(playdata['info'], 'cast') and check_key(playdata['info']['cast'], 'actors'):
        info['cast'] = playdata['info']['cast']['actors']

    if check_key(playdata['info'], 'genres'):
        info['genres'] = playdata['info']['genres']

    if check_key(playdata['info'], 'directors'):
        info['director'] = playdata['info']['directors']

    return info

def plugin_process_playdata(playdata):
    profile_settings = load_profile(profile_id=1)

    CDMHEADERS = {
        'User-Agent': DEFAULT_USER_AGENT,
    }

    if check_key(playdata, 'license') and check_key(playdata['license'], 'widevine') and check_key(playdata['license']['widevine'], 'license'):
        item_inputstream = inputstream.Widevine(
            license_key = playdata['license']['widevine']['license'],
        )
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