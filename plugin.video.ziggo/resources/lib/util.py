import datetime
import json
import re
import sys
from collections import OrderedDict
from urllib.parse import urlencode

import _strptime
import xbmc

from resources.lib.base.l1.constants import (ADDON_ID, DEFAULT_USER_AGENT,
                                             PROVIDER_NAME)
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import (check_key, convert_datetime_timezone,
                                        date_to_nl_dag, date_to_nl_maand,
                                        encode_obj, get_credentials, load_file,
                                        load_profile, write_file)
from resources.lib.base.l4 import gui
from resources.lib.base.l5.api import api_download, api_get_channels
from resources.lib.base.l6 import inputstream
from resources.lib.constants import (CONST_DEFAULT_CLIENTID, CONST_IMAGES,
                                     CONST_URLS)

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

def check_entitlements():
    from resources.lib.api import api_get_play_token

    media_groups_url = '{mediagroups_url}/crid%3A~~2F~~2Fschange.com~~2F64e9e221-aebf-4620-b248-8681feada6e8?byHasCurrentVod=true&range=1-1&sort=playCount7%7Cdesc'.format(mediagroups_url=CONST_URLS['mediagroupsfeeds_url'])

    download = api_download(url=media_groups_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'entryCount'):
        gui.ok(message=_.NO_MOVIES_SERIES, heading=_.CHECKED_ENTITLEMENTS)
        settings.setBool(key='showMoviesSeries', value=False)
        return

    id = data['mediaGroups'][0]['id']

    media_item_url = '{mediaitem_url}/{mediaitem_id}'.format(mediaitem_url=CONST_URLS['mediaitems_url'], mediaitem_id=id)

    download = api_download(url=media_item_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data:
        gui.ok(message=_.NO_MOVIES_SERIES, heading=_.CHECKED_ENTITLEMENTS)
        settings.setBool(key='showMoviesSeries', value=False)
        return

    if check_key(data, 'videoStreams'):
        urldata = get_play_url(content=data['videoStreams'])

    if (not urldata or not check_key(urldata, 'play_url') or not check_key(urldata, 'locator') or urldata['play_url'] == 'http://Playout/using/Session/Service'):
            urldata = {}

            playout_url = '{base_url}/playout/vod/{id}?abrType=BR-AVC-DASH'.format(base_url=CONST_URLS['base_url'], id=id)
            download = api_download(url=playout_url, type='get', headers=None, data=None, json_data=False, return_json=True)
            data = download['data']
            code = download['code']

            if not code or not code == 200 or not data or not check_key(data, 'url') or not check_key(data, 'contentLocator'):
                gui.ok(message=_.NO_MOVIES_SERIES, heading=_.CHECKED_ENTITLEMENTS)
                settings.setBool(key='showMoviesSeries', value=False)
                return

            urldata['play_url'] = data['url']
            urldata['locator'] = data['contentLocator']

    if not urldata or not check_key(urldata, 'play_url') or not check_key(urldata, 'locator'):
        gui.ok(message=_.NO_MOVIES_SERIES, heading=_.CHECKED_ENTITLEMENTS)
        settings.setBool(key='showMoviesSeries', value=False)
        return

    token = api_get_play_token(locator=urldata['locator'], path=urldata['play_url'], force=1)

    if not token or not len(token) > 0:
        gui.ok(message=_.NO_MOVIES_SERIES, heading=_.CHECKED_ENTITLEMENTS)
        settings.setBool(key='showMoviesSeries', value=False)
        return

    gui.ok(message=_.YES_MOVIES_SERIES, heading=_.CHECKED_ENTITLEMENTS)
    settings.setBool(key='showMoviesSeries', value=True)

    return

def get_image(prefix, content):
    best_image = 0
    image_url = ''

    for images in content:
        if prefix in images['assetTypes']:
            if best_image < 7:
                best_image = 7
                image_url = images['url']
        elif ('HighResPortrait') in images['assetTypes']:
            if best_image < 6:
                best_image = 6
                image_url = images['url']
        elif ('HighResLandscapeShowcard') in images['assetTypes']:
            if best_image < 5:
                best_image = 5
                image_url = images['url']
        elif ('HighResLandscape') in images['assetTypes']:
            if best_image < 4:
                best_image = 4
                image_url = images['url']
        elif (prefix + '-xlarge') in images['assetTypes']:
            if best_image < 3:
                best_image = 3
                image_url = images['url']
        elif (prefix + '-large') in images['assetTypes']:
            if best_image < 2:
                best_image = 2
                image_url = images['url']
        elif (prefix + '-medium') in images['assetTypes']:
            if best_image < 1:
                best_image = 1
                image_url = images['url']

    return image_url

def get_play_url(content):
    if check_key(content, 'url') and check_key(content, 'contentLocator'):
        return {'play_url': content['url'], 'locator': content['contentLocator']}
    else:
        for stream in content:
            if  'streamingUrl' in stream and 'contentLocator' in stream and 'assetTypes' in stream and 'Orion-DASH' in stream['assetTypes']:
                return {'play_url': stream['streamingUrl'], 'locator': stream['contentLocator']}

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

def plugin_check_devices():
    pass

def plugin_check_first():
    pass

def plugin_get_device_id():
    return 'NOTNEEDED'

def plugin_login_error(login_result):
    gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)

def plugin_post_login():
    check_entitlements()

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

    if check_key(playdata, 'info'):
        if check_key(playdata['info'], 'latestBroadcastEndTime') and check_key(playdata['info'], 'latestBroadcastStartTime'):
            startsplit = int(int(playdata['info']['latestBroadcastStartTime']) // 1000)
            endsplit = int(int(playdata['info']['latestBroadcastEndTime']) // 1000)
            duration = endsplit - startsplit

            startT = datetime.datetime.fromtimestamp(startsplit)
            startT = convert_datetime_timezone(startT, "UTC", "UTC")
            endT = datetime.datetime.fromtimestamp(endsplit)
            endT = convert_datetime_timezone(endT, "UTC", "UTC")

            write_file(file='stream_start', data=startsplit, isJSON=False)
            write_file(file='stream_end', data=endsplit, isJSON=False)

            if xbmc.getLanguage(xbmc.ISO_639_1) == 'nl':
                info['label1'] = '{weekday} {day} {month} {yearhourminute} '.format(weekday=date_to_nl_dag(startT), day=startT.strftime("%d"), month=date_to_nl_maand(startT), yearhourminute=startT.strftime("%Y %H:%M"))
            else:
                info['label1'] = startT.strftime("%A %d %B %Y %H:%M ").capitalize()

        if playdata['title']:
            info['label1'] += playdata['title'] + ' - ' + playdata['info']['title']
        else:
            info['label1'] += playdata['info']['title']

        if check_key(playdata['info'], 'duration'):
            info['duration'] = int(playdata['info']['duration'])
        elif check_key(playdata['info'], 'latestBroadcastStartTime') and check_key(playdata['info'], 'latestBroadcastEndTime'):
            info['duration'] = int(int(playdata['info']['latestBroadcastEndTime']) - int(playdata['info']['latestBroadcastStartTime'])) // 1000

        if check_key(playdata['info'], 'description'):
            info['description'] = playdata['info']['description']

        if check_key(playdata['info'], 'duration'):
            info['duration'] = int(playdata['info']['duration'])

        if check_key(playdata['info'], 'year'):
            info['year'] = int(playdata['info']['year'])

        if check_key(playdata['info'], 'images'):
            info['image'] = get_image("boxart", playdata['info']['images'])
            info['image_large'] = get_image("HighResLandscape", playdata['info']['images'])

            if info['image_large'] == '':
                info['image_large'] = info['image']
            else:
                info['image_large'] += '?w=1920&mode=box'

        if check_key(playdata['info'], 'categories'):
            for categoryrow in playdata['info']['categories']:
                info['genres'].append(categoryrow['title'])

        if check_key(playdata['info'], 'cast'):
            for castrow in playdata['info']['cast']:
                info['cast'].append(castrow)

        if check_key(playdata['info'], 'directors'):
            for directorrow in playdata['info']['directors']:
                info['director'].append(directorrow)

        epcode = ''

        if check_key(playdata['info'], 'seriesNumber'):
            epcode += 'S' + str(playdata['info']['seriesNumber'])

        if check_key(playdata['info'], 'seriesEpisodeNumber'):
            epcode += 'E' + str(playdata['info']['seriesEpisodeNumber'])

        if check_key(playdata['info'], 'secondaryTitle'):
            info['label2'] = playdata['info']['secondaryTitle']

            if len(epcode) > 0:
                info['label2'] += " (" + epcode + ")"
        else:
            info['label2'] = playdata['info']['title']

        data = api_get_channels()

        try:
            info['label2'] += " - "  + data[str(playdata['channel'])]['name']
        except:
            pass

    return info

def plugin_process_playdata(playdata):
    creds = get_credentials()
    profile_settings = load_profile(profile_id=1)

    CDMHEADERS = {
        'User-Agent': DEFAULT_USER_AGENT,
        #'X-Client-Id': CONST_DEFAULT_CLIENTID + '||' + DEFAULT_USER_AGENT,
        #'X-OESP-License-Token-Type': 'velocix',
        'Cookie': profile_settings['access_token'],
        'X-Profile': profile_settings['ziggo_profile_id'],
        'X-OESP-Username': creds['username'],
        'x-streaming-token': profile_settings['drm_token'],
        'x-drm-schemeId': 'edef8ba9-79d6-4ace-a3c8-27dcd51d21ed',
        #'X-OESP-Content-Locator': playdata['locator'],
    }

    params = []

    try:
        params.append(('_', 'renew_token'))
        params.append(('path', str(playdata['path']).encode('utf-8')))
        params.append(('locator', str(playdata['locator']).encode('utf-8')))
    except:
        params.append(('_', 'renew_token'))
        params.append(('path', playdata['path']))
        params.append(('locator', playdata['locator']))

    write_file(file='token_renew', data='plugin://{0}/?{1}'.format(ADDON_ID, urlencode(encode_obj(params))), isJSON=False)
    log('token renewed?')
    if check_key(playdata, 'certificate'):
        log('if statement succesful, token renewed')
        item_inputstream = inputstream.Widevine(
            #license_key = "http://127.0.0.1:11189/{provider}/license".format(provider=PROVIDER_NAME),
            license_key = playdata['license'],
            #server_certificate = playdata['certificate'],
        )
    else:
        log('else statement executed, forcing renew; no certificate found (shouldnt be a problem)')
        log(playdata['license'])
        item_inputstream = inputstream.Widevine(
            #license_key = "http://127.0.0.1:11189/{provider}/license".format(provider=PROVIDER_NAME),
            license_key = playdata['license'],
        )
                
    #write_file(file='stream_license', data=playdata['license'], isJSON=False)

    return item_inputstream, CDMHEADERS

def plugin_process_vod(data, start=0):
    items = []

    return data

def plugin_process_vod_season(series, id, data):
    season = []

    if not data or not check_key(data, 'mediaItems'):
        return None

    data['mediaItems'] = list(data['mediaItems'])

    for row in data['mediaItems']:
        desc = ''
        image = ''
        label = ''

        if not check_key(row, 'title') or not check_key(row, 'id'):
            continue

        if check_key(row, 'description'):
            desc = row['description']

        if check_key(row, 'duration'):
            duration = int(row['duration'])

        if check_key(row, 'images'):
            program_image = get_image("boxart", row['images'])
            image = get_image("HighResLandscape", row['images'])

            if image == '':
                image = program_image
            else:
                image += '?w=1920&mode=box'

        if check_key(row, 'earliestBroadcastStartTime'):
            startsplit = int(row['earliestBroadcastStartTime']) // 1000

            startT = datetime.datetime.fromtimestamp(startsplit)
            startT = convert_datetime_timezone(startT, "UTC", "UTC")

            if xbmc.getLanguage(xbmc.ISO_639_1) == 'nl':
                label = date_to_nl_dag(startT) + startT.strftime(" %d ") + date_to_nl_maand(startT) + startT.strftime(" %Y %H:%M ") + row['title']
            else:
                label = (startT.strftime("%A %d %B %Y %H:%M ") + row['title']).capitalize()
        else:
            label = row['title']

        season.append({'label': label, 'id': row['id'], 'start': '', 'duration': duration, 'title': row['title'], 'seasonNumber': '', 'episodeNumber': '', 'description': desc, 'image': image})

    return season

def plugin_process_vod_seasons(id, data):
    seasons = []

    if data:
        try:
            row = data[str(id)]

            data_seasons = json.loads(row['seasons'])

            for season in data_seasons:
                seasons.append({'id': season['id'], 'seriesNumber': season['seriesNumber'], 'description': row['description'], 'image': row['icon']})

        except:
            return None

    return {'type': 'seasons', 'seasons': seasons, 'watchlist': id}

def plugin_process_rec_seasons(id, data):
    seasons = []

    if data:
        try:

            data_seasons = json.loads(data['seasonNumber'])
            data_season_type = json.loads(data['type'])
            
            if data_seasons and data_season_type == 'single':
                for season in data:
                    seasons.append({'id': season['id'], 'seriesNumber': season['seriesNumber']})

            elif data_seasons:
                if data_season_type == 'show' or data_season_type == 'season':
                    for season in data:
                        seasons.append({'id': season['id'], 'seriesNumber': season['seriesNumber']})

        except:
            return None

    return {'type': 'seasons', 'seasons': seasons, 'watchlist': id}

def plugin_process_watchlist(data, type='watchlist'):
    items = {}

    if check_key(data, 'entries'):
        for row in data['entries']:
            context = []

            if check_key(row, 'mediaGroup') and check_key(row['mediaGroup'], 'medium') and check_key(row['mediaGroup'], 'id'):
                currow = row['mediaGroup']
                id = currow['id']
            elif check_key(row, 'mediaItem') and check_key(row['mediaItem'], 'medium') and check_key(row['mediaItem'], 'mediaGroupId'):
                currow = row['mediaItem']
                id = currow['mediaGroupId']
            else:
                continue

            if not check_key(currow, 'title'):
                continue

            context.append((_.REMOVE_FROM_WATCHLIST, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=remove_from_watchlist, id=id)), ))

            if check_key(currow, 'isReplayTv') and currow['isReplayTv'] == "false":
                if not settings.getBool('showMoviesSeries'):
                    continue

                type = 'vod'
            else:
                type = 'program'

            channel = ''
            mediatype = ''
            duration = ''
            description = ''
            program_image = ''
            program_image_large = ''
            playable = False
            path = ''

            if check_key(currow, 'description'):
                description = currow['description']

            if check_key(currow, 'images'):
                program_image = get_image("boxart", currow['images'])
                program_image_large = get_image("HighResLandscape", currow['images'])

                if program_image_large == '':
                    program_image_large = program_image
                else:
                    program_image_large += '?w=1920&mode=box'

            if currow['medium'] == 'TV':
                if not check_key(currow, 'seriesLinks'):
                    path = plugin.url_for(func_or_url=watchlist_listing, label=currow['title'], id=id, search=0)
                else:
                    path = plugin.url_for(func_or_url=vod_series, type='series', label=currow['title'], id=id)
            elif currow['medium'] == 'Movie':
                if check_key(currow, 'duration'):
                    duration = int(currow['duration'])
                elif check_key(currow, 'startTime') and check_key(currow, 'endTime'):
                    duration = int(int(currow['endTime']) - int(currow['startTime'])) // 1000
                else:
                    duration = 0

                path = plugin.url_for(func_or_url=play_video, type=type, channel=channel, id=currow['id'], title=None)
                playable = True
                mediatype = 'video'

            items[str(currow['id'])] = plugin.Item(
                label = currow['title'],
                info = {
                    'plot': description,
                    'duration': duration,
                    'mediatype': mediatype,
                    'sorttitle': currow['title'].upper(),
                },
                art = {
                    'thumb': program_image,
                    'fanart': program_image_large
                },
                path = path,
                playable = playable,
                progress = 0,
                context = context
            )

    return items

def plugin_process_watchlist_listing(data, id=None, type='watchlist'):
    items = {}

    if check_key(data, 'listings'):
        for row in data['listings']:
            context = []

            if not check_key(row, 'program'):
                continue

            currow = row['program']

            if not check_key(currow, 'title') or not check_key(row, 'id'):
                continue

            duration = 0

            if check_key(row, 'endTime') and check_key(row, 'startTime'):
                startsplit = int(row['startTime']) // 1000
                endsplit = int(row['endTime']) // 1000
                duration = endsplit - startsplit

                startT = datetime.datetime.fromtimestamp(startsplit)
                startT = convert_datetime_timezone(startT, "UTC", "UTC")
                endT = datetime.datetime.fromtimestamp(endsplit)
                endT = convert_datetime_timezone(endT, "UTC", "UTC")

                if endT < (datetime.datetime.now(pytz.timezone("UTC")) - datetime.timedelta(days=7)):
                    continue

                if xbmc.getLanguage(xbmc.ISO_639_1) == 'nl':
                    label = '{weekday} {day} {month} {yearhourminute} '.format(weekday=date_to_nl_dag(startT), day=startT.strftime("%d"), month=date_to_nl_maand(startT), yearhourminute=startT.strftime("%Y %H:%M"))
                else:
                    label = startT.strftime("%A %d %B %Y %H:%M ").capitalize()

                label += currow['title']
            else:
                label = currow['title']

            data2 = api_get_channels()

            try:
                label += ' ({station})'.format(station=data2[str(currow['stationId'])]['name'])
            except:
                pass

            if id:
                context.append((_.ADD_TO_WATCHLIST, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=add_to_watchlist, id=id, type="group")), ))

            channel = ''
            description = ''
            program_image = ''
            program_image_large = ''

            if check_key(currow, 'description'):
                description = currow['description']

            if check_key(currow, 'duration'):
                duration = int(currow['duration'])

            if check_key(currow, 'images'):
                program_image = get_image("boxart", currow['images'])
                program_image_large = get_image("HighResLandscape", currow['images'])

                if program_image_large == '':
                    program_image_large = program_image
                else:
                    program_image_large += '?w=1920&mode=box'

            items[str(row['id'])] = plugin.Item(
                label = label,
                info = {
                    'plot': description,
                    'duration': duration,
                    'mediatype': 'video',
                    'sorttitle': label.upper(),
                },
                art = {
                    'thumb': program_image,
                    'fanart': program_image_large
                },
                path = plugin.url_for(func_or_url=play_video, type="program", channel=channel, id=row['id']),
                playable = True,
                context = context
            )

    return items

def plugin_renew_token(data):
    from resources.lib.api import api_get_play_token

    api_get_play_token(locator=data['locator'], path=data['path'])

    if 'manifest.mpd' in data['path']:
        data['path'] = data['path'].replace("/manifest.mpd", "/")
    elif 'index.mpd' in data['path']:
        data['path'] = data['path'].replace("/index.mpd", "/")

    splitpath = data['path'].split('/Manifest?device', 1)

    if len(splitpath) == 2:
        data['path'] = splitpath[0] + "/"

    return data['path']

def plugin_vod_subscription_filter():
    return None