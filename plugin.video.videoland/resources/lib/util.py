import _strptime
import datetime, re, xbmc

from resources.lib.base.l1.constants import ADDON_ID, DEFAULT_USER_AGENT
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, load_file, load_profile, write_file
from resources.lib.base.l4 import gui
from resources.lib.base.l5.api import api_get_channels
from resources.lib.base.l6 import inputstream
from resources.lib.constants import CONST_IMAGES

from urllib.parse import urlencode

def check_devices():
    pass

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
        if settings.getBool('use_small_images', default=False) == True:
            info['image'] = str(playdata['info']['still']).replace(CONST_IMAGES['still']['replace'], CONST_IMAGES['still']['small'])
            info['image_large'] = str(playdata['info']['still']).replace(CONST_IMAGES['still']['replace'], CONST_IMAGES['still']['small'])
        else:
            info['image'] = str(playdata['info']['still']).replace(CONST_IMAGES['still']['replace'], CONST_IMAGES['still']['large'])
            info['image_large'] = str(playdata['info']['still']).replace(CONST_IMAGES['still']['replace'], CONST_IMAGES['still']['large'])
    elif check_key(playdata['info'], 'poster'):
        if settings.getBool('use_small_images', default=False) == True:
            info['image'] = str(playdata['info']['poster']).replace(CONST_IMAGES['poster']['replace'], CONST_IMAGES['poster']['small'])
            info['image_large'] = str(playdata['info']['poster']).replace(CONST_IMAGES['poster']['replace'], CONST_IMAGES['poster']['small'])
        else:
            info['image'] = str(playdata['info']['poster']).replace(CONST_IMAGES['poster']['replace'], CONST_IMAGES['poster']['large'])
            info['image_large'] = str(playdata['info']['poster']).replace(CONST_IMAGES['poster']['replace'], CONST_IMAGES['poster']['large'])

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

    if check_key(playdata, 'license') and len(str(profile_settings['ticket_id'])) == 0:
        CDMHEADERS['Authorization'] = 'Bearer ' + profile_settings['token']

        item_inputstream = inputstream.Widevine(
            license_key = playdata['license'],
        )
    elif check_key(playdata, 'license') and check_key(playdata['license'], 'widevine') and check_key(playdata['license']['widevine'], 'license'):
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

def plugin_process_watchlist(data, continuewatch=0):
    continuewatch = int(continuewatch)

    items = {}

    if check_key(data, 'details'):
        for row in data['details']:
            currow = data['details'][row]

            info = plugin_process_info({'info': currow})

            context = []

            params = []
            params.append(('_', 'remove_from_watchlist'))
            params.append(('continuewatch', continuewatch))

            progress = 0

            if continuewatch == 1:
                remove_txt = _.REMOVE_FROM_CONTINUE

                if currow['type'] == 'episode':
                    params.append(('id', str(currow['id']) + '?series=' + str(currow['series_ref'])))
                else:
                    params.append(('id', str(currow['id']) + '?series='))

                if not currow['type'] == 'series':
                    progress = data['progress'][row]
            else:
                remove_txt = _.REMOVE_FROM_WATCHLIST
                params.append(('id', currow['ref']))

            context.append((remove_txt, 'RunPlugin({context_url})'.format(context_url='plugin://{0}/?{1}'.format(ADDON_ID, urlencode(encode_obj(params)))), ))

            type = 'vod'

            if currow['type'] == 'episode':
                params = []
                params.append(('_', 'play_video'))
                params.append(('type', type))
                params.append(('channel', None))

                params.append(('id', 'E' + str(currow['series_ref'][1:]) + '###' + str(currow['season_id']) + '###' + str(currow['id'])))
                params.append(('title', None))

                path = 'plugin://{0}/?{1}'.format(ADDON_ID, urlencode(encode_obj(params)))
                playable = True
                mediatype = 'video'
            elif currow['type'] == 'series' and continuewatch == 0:
                params = []
                params.append(('_', 'vod_series'))
                params.append(('type', 'series'))
                params.append(('label', currow['title']))
                params.append(('id', currow['ref']))

                path = 'plugin://{0}/?{1}'.format(ADDON_ID, urlencode(encode_obj(params)))
                playable = False
                mediatype = ''
            elif currow['type'] == 'movie':
                params = []
                params.append(('_', 'play_video'))
                params.append(('type', type))
                params.append(('channel', None))
                params.append(('id', currow['ref']))
                params.append(('title', None))

                path = 'plugin://{0}/?{1}'.format(ADDON_ID, urlencode(encode_obj(params)))
                playable = True
                mediatype = 'video'
            else:
                continue

            items[str(currow['ref'])] = {
                'label1': info['label1'],
                'description': info['description'],
                'duration': info['duration'],
                'mediatype': mediatype,
                'image': info['image'],
                'image_large': info['image_large'],
                'path': path,
                'playable': playable,
                'progress': progress,
                'context': context,
                'type': currow['type']
            }

    return items

def plugin_process_watchlist_listing(data, id=None, continuewatch=0):
    continuewatch = int(continuewatch)

    items = []

    return items

def encode_obj(in_obj):
    def encode_list(in_list):
        out_list = []
        for el in in_list:
            out_list.append(encode_obj(el))
        return out_list

    def encode_dict(in_dict):
        out_dict = {}

        for k, v in in_dict.items():
            out_dict[k] = encode_obj(v)

        return out_dict

    if isinstance(in_obj, str):
        return in_obj.encode('utf-8')
    elif isinstance(in_obj, list):
        return encode_list(in_obj)
    elif isinstance(in_obj, tuple):
        return tuple(encode_list(in_obj))
    elif isinstance(in_obj, dict):
        return encode_dict(in_obj)

    return in_obj