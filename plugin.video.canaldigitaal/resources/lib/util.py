import _strptime
import datetime, time, xbmc

from collections import OrderedDict
from resources.lib.base.l1.constants import ADDON_ID, DEFAULT_USER_AGENT
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, load_file, write_file
from resources.lib.base.l4 import gui
from resources.lib.base.l5.api import api_get_channels
from resources.lib.base.l6 import inputstream
from resources.lib.constants import CONST_BASE_HEADERS, CONST_IMAGES
from urllib.parse import urlencode

#Included from base.l7.plugin
#plugin_get_device_id

#Included from base.l8.menu
#plugin_ask_for_creds
#plugin_check_devices
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

def plugin_get_device_id():
    return 'NOTNEEDED'

def plugin_login_error(login_result):
    try:
        if check_key(login_result['data'], 'error') and login_result['data']['error'] == 'toomany':
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

    if playdata['info']:
        if check_key(playdata['info'], 'params'):
            if check_key(playdata['info']['params'], 'start') and check_key(playdata['info']['params'], 'end'):
                startT = datetime.datetime.fromtimestamp(time.mktime(time.strptime(playdata['info']['params']['start'], "%Y-%m-%dT%H:%M:%SZ")))
                endT = datetime.datetime.fromtimestamp(time.mktime(time.strptime(playdata['info']['params']['end'], "%Y-%m-%dT%H:%M:%SZ")))

                write_file(file='stream_start', data=int(time.mktime(time.strptime(playdata['info']['params']['start'], "%Y-%m-%dT%H:%M:%SZ"))), isJSON=False)
                write_file(file='stream_end', data=int(time.mktime(time.strptime(playdata['info']['params']['end'], "%Y-%m-%dT%H:%M:%SZ"))), isJSON=False)

                info['duration'] = int((endT - startT).total_seconds())

                if xbmc.getLanguage(xbmc.ISO_639_1) == 'nl':
                    info['label1'] = '{weekday} {day} {month} {yearhourminute} '.format(weekday=date_to_nl_dag(startT), day=startT.strftime("%d"), month=date_to_nl_maand(startT), yearhourminute=startT.strftime("%Y %H:%M"))
                else:
                    info['label1'] = startT.strftime("%A %d %B %Y %H:%M ").capitalize()

                info['label1'] += " - "

        if playdata['title']:
            info['label1'] += playdata['title'] + ' - '

        if check_key(playdata['info'], 'title'):
            info['label1'] += playdata['info']['title']

        if check_key(playdata['info'], 'descriptiondescription'):
            info['description'] = playdata['info']['description']

        if check_key(playdata['info'], 'images') and check_key(playdata['info']['images'][0], 'url'):
            info['image'] = playdata['info']['images'][0]['url']
            info['image_large'] = playdata['info']['images'][0]['url']

        if check_key(playdata['info'], 'params'):
            if check_key(playdata['info']['params'], 'credits'):
                for castmember in playdata['info']['params']['credits']:
                    if castmember['role'] == "Actor":
                        info['cast'].append(castmember['person'])
                    elif castmember['role'] == "Director":
                        info['director'].append(castmember['person'])
                    elif castmember['role'] == "Writer":
                        info['writer'].append(castmember['person'])

            if check_key(playdata['info']['params'], 'genres'):
                for genre in playdata['info']['params']['genres']:
                    if check_key(genre, 'title'):
                        info['genres'].append(genre['title'])

            if check_key(playdata['info']['params'], 'duration'):
                info['duration'] = playdata['info']['params']['duration']

            epcode = ''

            if check_key(playdata['info']['params'], 'seriesSeason'):
                epcode += 'S' + str(playdata['info']['params']['seriesSeason'])

            if check_key(playdata['info']['params'], 'seriesEpisode'):
                epcode += 'E' + str(playdata['info']['params']['seriesEpisode'])

            if check_key(playdata['info']['params'], 'episodeTitle'):
                info['label2'] = playdata['info']['params']['episodeTitle']

                if len(epcode) > 0:
                    info['label2'] += " (" + epcode + ")"
            elif check_key(playdata['info'], 'title'):
                info['label2'] = playdata['info']['title']

            if check_key(playdata['info']['params'], 'channelId'):
                data = api_get_channels()

                try:
                    info['label2'] += " - "  + data[str(playdata['info']['params']['channelId'])]['name']
                except:
                    pass

    return info

def plugin_process_playdata(playdata):
    CDMHEADERS = CONST_BASE_HEADERS
    CDMHEADERS['User-Agent'] = DEFAULT_USER_AGENT

    if check_key(playdata, 'license'):
        item_inputstream = inputstream.Widevine(
            license_key = playdata['license'],
        )
    else:
        item_inputstream = inputstream.MPD()

    return item_inputstream, CDMHEADERS

def plugin_process_vod(data, start=0):
    items = []

    return data

def plugin_process_vod_season(series, id, data):
    season = []
    episodes = []

    if not data or not check_key(data, 'assets'):
        return None

    for row in data['assets']:
        episodes.append(str(row['params']['seriesEpisode']))

        label = '{season}.{episode} - {title}'.format(season=str(row['params']['seriesSeason']), episode=str(row['params']['seriesEpisode']), title=str(row['title']))

        season.append({'label': label, 'id': str(row['id']), 'assetid': '', 'duration': row['params']['duration'], 'title': str(row['title']), 'episodeNumber': '{season}.{episode}'.format(season=str(row['params']['seriesSeason']), episode=str(row['params']['seriesEpisode'])), 'description': '', 'image': str(row['images'][0]['url'])})

    return season

def plugin_process_vod_seasons(id, data):
    seasons = []

    if not data or not check_key(data, 'collection'):
        return None

    for row in data['collection']:
        if row['label'] == 'sg.ui.season.subst':
            seasons.append({'id': str(row['query']), 'seriesNumber': str(row['labelParams'][0]), 'description': '', 'image': ''})

    return {'type': 'seasons', 'seasons': seasons}

def plugin_process_watchlist(data, type='watchlist'):
    items = []

    return items

def plugin_process_watchlist_listing(data, id=None, type='watchlist'):
    items = []

    return items

def plugin_renew_token(data):
    return None

def plugin_vod_subscription_filter():
    return None