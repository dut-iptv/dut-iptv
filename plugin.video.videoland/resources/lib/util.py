import _strptime
import datetime, re, xbmc

from collections import OrderedDict
from resources.lib.base.l1.constants import ADDON_ID, DEFAULT_USER_AGENT, PROVIDER_NAME
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, encode_obj, load_file, load_profile, write_file
from resources.lib.base.l4 import gui
from resources.lib.base.l6 import inputstream
from resources.lib.constants import CONST_IMAGES, CONST_WATCHLIST_CAPABILITY
from urllib.parse import urlencode

#Included from base.l7.plugin
#plugin_get_device_id

#Included from base.l8.menu
#plugin_ask_for_creds
#plugin_check_devices
#plugin_check_first
#plugin_login_error
#plugin_post_login
#plugin_process_info
#plugin_process_playdata
#plugin_process_vod
#plugin_process_vod_season
#plugin_process_vod_seasons
#plugin_process_watchlist
#plugin_process_watchlist_listing
#plugin_renew_token
#plugin_vod_subscription_filter

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

def plugin_check_devices():
    pass

def plugin_check_first():
    pass

def plugin_get_device_id():
    return 'NOTNEEDED'

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
            #license_key = "http://127.0.0.1:11189/{provider}/license".format(provider=PROVIDER_NAME)
        )

        #write_file(file='stream_license', data=playdata['license'], isJSON=False)
    elif check_key(playdata, 'license') and check_key(playdata['license'], 'widevine') and check_key(playdata['license']['widevine'], 'license'):
        item_inputstream = inputstream.Widevine(
            license_key = playdata['license']['widevine']['license'],
            #license_key = "http://127.0.0.1:11189/{provider}/license".format(provider=PROVIDER_NAME)
        )

        #write_file(file='stream_license', data=playdata['license']['widevine']['license'], isJSON=False)
    else:
        item_inputstream = inputstream.MPD()

    return item_inputstream, CDMHEADERS

def plugin_process_vod(data, start=0):
    items = {}

    return data

def plugin_process_vod_season(series, id, data):
    if not data or not check_key(data, 'details'):
        return None

    id_ar = id.split('###')
    series = id_ar[0]
    seasonstr = id_ar[1]

    season = []
    seasonno = ''

    if check_key(data['details'], 'SN' + str(seasonstr)):
        seasonno = re.sub("[^0-9]", "", data['details']['SN' + str(seasonstr)]['title'])

    for currow in data['details']:
        row = data['details'][currow]

        if check_key(row, 'type') and row['type'] == 'episode':
            image = ''
            duration = 0

            if check_key(row, 'runtime'):
                duration = row['runtime']

            if check_key(row, 'still'):
                if settings.getBool('use_small_images', default=False) == True:
                    image = row['still'].replace(CONST_IMAGES['still']['replace'], CONST_IMAGES['still']['small'])
                else:
                    image = row['still'].replace(CONST_IMAGES['still']['replace'], CONST_IMAGES['still']['large'])

            if check_key(row, 'title') and len(str(row['title'])) > 0:
                name = row['title']
            else:
                name = 'Aflevering {position}'.format(position=row['position'])

            label = '{seasonno}.{episode} - {title}'.format(seasonno=seasonno, episode=row['position'], title=name)

            season.append({'label': label, 'id': 'E' + str(series) + '###' + str(seasonstr) + '###' + str(row['id']), 'media_id': '', 'duration': duration, 'title': name, 'episodeNumber': row['position'], 'description': row['description'], 'image': image})

    return season

def plugin_process_vod_seasons(id, data):
    seasons = []

    ref = id
    id = id[1:]

    if not data or not check_key(data, 'details'):
        return None

    for currow in data['details']:
        row = data['details'][currow]

        if check_key(row, 'type') and row['type'] == 'season':
            if settings.getBool('use_small_images', default=False) == True:
                image = data['poster'].replace(CONST_IMAGES['poster']['replace'], CONST_IMAGES['poster']['small'])
            else:
                image = data['poster'].replace(CONST_IMAGES['poster']['replace'], CONST_IMAGES['poster']['large'])

            seasons.append({'id': str(id) + '###' + str(row['id']), 'seriesNumber': row['title'], 'description': data['description'], 'image': image, 'watchlist': ref})

    return {'type': 'seasons', 'seasons': seasons}

def plugin_process_watchlist(data, type='watchlist'):
    items = {}

    if check_key(data, 'details'):
        for row in data['details']:
            currow = data['details'][row]

            info = plugin_process_info({'info': currow})

            context = []

            params = []
            params.append(('_', 'remove_from_watchlist'))
            params.append(('type', type))

            progress = 0
            remove_txt = CONST_WATCHLIST_CAPABILITY[type]['removelist']

            if type == 'continuewatch':
                if currow['type'] == 'episode':
                    params.append(('id', str(currow['id']) + '?series=' + str(currow['series_ref'])))
                else:
                    params.append(('id', str(currow['id']) + '?series='))

                if not currow['type'] == 'series':
                    progress = data['progress'][row]
            else:
                params.append(('id', currow['ref']))

            if CONST_WATCHLIST_CAPABILITY[type]['remove'] == 1:
                context.append((remove_txt, 'RunPlugin({context_url})'.format(context_url='plugin://{0}/?{1}'.format(ADDON_ID, urlencode(encode_obj(params)))), ))

            type2 = 'vod'

            if currow['type'] == 'episode':
                params = []
                params.append(('_', 'play_video'))
                params.append(('type', type2))
                params.append(('channel', None))

                params.append(('id', 'E' + str(currow['series_ref'][1:]) + '###' + str(currow['season_id']) + '###' + str(currow['id'])))
                params.append(('title', None))

                path = 'plugin://{0}/?{1}'.format(ADDON_ID, urlencode(encode_obj(params)))
                playable = True
                mediatype = 'video'
            elif currow['type'] == 'series' and not type == 'continuewatch':
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
                params.append(('type', type2))
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

def plugin_process_watchlist_listing(data, id=None, type='watchlist'):
    items = {}

    return items

def plugin_renew_token(data):
    return None

def plugin_vod_subscription_filter():
    return None