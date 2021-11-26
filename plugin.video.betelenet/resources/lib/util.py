import _strptime
import datetime, io, json, os, re, sys, xbmc, xbmcvfs

from resources.lib.base.l1.constants import ADDON_ID, DEFAULT_USER_AGENT
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, get_credentials, load_file, load_profile, write_file
from resources.lib.base.l4 import gui
from resources.lib.base.l5.api import api_download, api_get_channels
from resources.lib.base.l6 import inputstream
from resources.lib.constants import CONST_API_URLS, CONST_DEFAULT_CLIENTID
from urllib.parse import urlencode

def check_devices():
    device_id = load_file('device_id', isJSON=False)
    
    if not device_id:
        LOGPATH = xbmcvfs.translatePath('special://logpath')
        LOGFILE = os.path.join(LOGPATH, 'kodi.old.log')
        
        with io.open(LOGFILE, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            
        regex = r"HEADER_IN:\sX-DRM-Device-ID:\s([a-zA-Z0-9]*)"

        matches = re.finditer(regex, text, re.MULTILINE)

        for matchNum, match in enumerate(matches, start=1):
            device_id = match.group(1)
            break
            
        if not device_id:
            LOGFILE = os.path.join(LOGPATH, 'kodi.log')
        
            with io.open(LOGFILE, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                
            regex = r"HEADER_IN:\sX-DRM-Device-ID:\s([a-zA-Z0-9]*)"

            matches = re.finditer(regex, text, re.MULTILINE)

            for matchNum, match in enumerate(matches, start=1):
                device_id = match.group(1)
                break

        if device_id:
            from resources.lib.api import api_list_devices, api_replace_device, api_new_device

            devices = api_list_devices()
            
            select_list = []
            device_ar = {}
            count = 0

            if devices:
                found = False

                for device in devices:
                    if str(device['deviceId']) == device_id:
                        found = True
                        break

                    device_ar[count] = device['deviceId']
                    count += 1
                    select_list.append(device['customerDefinedName'])

                if found == False:
                    if len(devices) == 5:
                        selected = gui.select('Selecteer Device om te vervangen:', select_list)
                        if check_key(device_ar, selected):
                            api_replace_device(device_ar[selected], device_id)
                    else:
                        api_new_device(device_id)
        else:
            gui.ok(message='Geen device ID gevonden. Het afspelen zal zo mislukken, hierna wordt automatisch een device ID gegenereerd. Je krijgt hier geen bericht van. Herstart direct het afspelen.', heading='Geen device ID gevonden')

def check_entitlements():
    from resources.lib.api import api_get_play_token

    media_groups_url = '{mediagroups_url}/crid:~~2F~~2Fschange.com~~2F63494ff3-70b4-4ce6-866a-9645f2b76d3e?byHasCurrentVod=true&range=1-1&sort=playCount7%7Cdesc'.format(mediagroups_url=CONST_API_URLS['mediagroupsfeeds_url'])

    download = api_download(url=media_groups_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'entryCount'):
        gui.ok(message=_.NO_MOVIES_SERIES, heading=_.CHECKED_ENTITLEMENTS)
        settings.setBool(key='showMoviesSeries', value=False)
        return

    id = data['mediaGroups'][0]['id']

    media_item_url = '{mediaitem_url}/{mediaitem_id}'.format(mediaitem_url=CONST_API_URLS['mediaitems_url'], mediaitem_id=id)

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

            playout_url = '{base_url}/playout/vod/{id}?abrType=BR-AVC-DASH'.format(base_url=CONST_API_URLS['base_url'], id=id)
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

def encode_obj(in_obj):
    def encode_list(in_list):
        out_list = []
        for el in in_list:
            out_list.append(encode_obj(el))
        return out_list

    def encode_dict(in_dict):
        out_dict = {}

        if sys.version_info < (3, 0):
            for k, v in in_dict.iteritems():
                out_dict[k] = encode_obj(v)
        else:
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

    if not len(username) > 0:
        gui.ok(message=_.EMPTY_USER, heading=_.LOGIN_ERROR_TITLE)
        return {'result': False, 'username': '', 'password': ''}

    password = str(gui.input(message=_.ASK_PASSWORD, hide_input=True)).strip()

    if not len(password) > 0:
        gui.ok(message=_.EMPTY_PASS, heading=_.LOGIN_ERROR_TITLE)
        return {'result': False, 'username': '', 'password': ''}

    return {'result': True, 'username': username, 'password': password}

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
        'X-OESP-License-Token-Type': 'velocix',
        'X-OESP-Token': profile_settings['access_token'],
        'X-OESP-Username': creds['username'],
        'X-OESP-License-Token': profile_settings['drm_token'],
        'X-OESP-DRM-SchemeIdUri': 'urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed',
        'X-OESP-Content-Locator': playdata['locator']
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

    item_inputstream = inputstream.Widevine(
        license_key = playdata['license'],
        #server_certificate = load_file('widevine_cert', isJSON=False),
        #license_flags = 'persistent_storage'
        #media_renewal_url = 'plugin://{0}/?{1}'.format(ADDON_ID, urlencode(encode_obj(params))),
        #media_renewal_time = 60,
        #manifest_update_parameter = 'full',
    )

    return item_inputstream, CDMHEADERS

def plugin_renew_token(data):
    from resources.lib.api import api_get_play_token

    api_get_play_token(locator=data['locator'], path=data['path'])

    data['path'] = data['path'].replace("/manifest.mpd", "/")

    splitpath = data['path'].split('/Manifest?device', 1)

    if len(splitpath) == 2:
        data['path'] = splitpath[0] + "/"

    return data['path']

def plugin_process_watchlist(data):
    items = []

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

            items.append(plugin.Item(
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
                context = context
            ))

    return items

def plugin_process_watchlist_listing(data, id=None):
    items = []

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

            items.append(plugin.Item(
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
            ))

    return items

def plugin_vod_subscription_filter():
    return None