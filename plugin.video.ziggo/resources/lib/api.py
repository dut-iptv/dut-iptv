import base64, json, os, re, sys, time, xbmc

from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE, DEFAULT_USER_AGENT
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, get_credentials, is_file_older_than_x_days, is_file_older_than_x_minutes, load_file, load_profile, load_prefs, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import api_download, api_get_channels, api_get_vod_by_type
from resources.lib.constants import CONST_API_URLS, CONST_DEFAULT_CLIENTID, CONST_VOD_CAPABILITY
from resources.lib.util import get_image, get_play_url, plugin_process_info
from urllib.parse import parse_qs, urlparse, quote_plus

def api_add_to_watchlist(id, type):
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    if type == "item":
        mediaitems_url = '{listings_url}/{id}'.format(listings_url=CONST_API_URLS['listings_url'], id=id)
        download = api_download(url=mediaitems_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'mediaGroupId'):
            return False

        id = data['mediaGroupId']

    watchlist_url = '{watchlist_url}/{watchlist_id}/entries/{id}?sharedProfile=true'.format(watchlist_url=CONST_API_URLS['watchlist_url'], watchlist_id=profile_settings['watchlist_id'], id=id)

    download = api_download(url=watchlist_url, type='post', headers=api_get_headers(), data={"mediaGroup": {'id': id}}, json_data=True, return_json=False)
    data = download['data']
    code = download['code']

    if not code or not code == 204 or not data:
        return False

    return True

def api_get_headers():
    creds = get_credentials()
    username = creds['username']

    profile_settings = load_profile(profile_id=1)

    HEADERS = {
        'User-Agent': DEFAULT_USER_AGENT,
        'X-Client-Id': CONST_DEFAULT_CLIENTID + '||' + DEFAULT_USER_AGENT,
        'X-OESP-Token': profile_settings['access_token'],
        'X-OESP-Username': username,
    }

    if check_key(profile_settings, 'ziggo_profile_id') and len(str(profile_settings['ziggo_profile_id'])) > 0:
        HEADERS['X-OESP-Profile-Id'] = profile_settings['ziggo_profile_id']

    return HEADERS

def api_get_info(id, channel=''):
    profile_settings = load_profile(profile_id=1)

    info = {}
    base_listing_url = CONST_API_URLS['listings_url']

    try:
        listing_url = '{listings_url}?byEndTime={time}~&byStationId={channel}&range=1-1&sort=startTime'.format(listings_url=base_listing_url, time=int(time.time() * 1000), channel=id)
        download = api_download(url=listing_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and check_key(data, 'listings'):
            for row in data['listings']:
                if check_key(row, 'program'):
                    info = row['program']

        info = plugin_process_info({'title': '', 'channel': channel, 'info': info})
    except:
        pass

    return info

def api_get_play_token(locator=None, path=None, force=0):
    if not api_get_session():
        return None

    force = int(force)

    profile_settings = load_profile(profile_id=1)

    if not locator == profile_settings['drm_locator']:
        return None

    if not check_key(profile_settings, 'drm_token_age') or not check_key(profile_settings, 'tokenrun') or not check_key(profile_settings, 'tokenruntime') or profile_settings['drm_token_age'] < int(time.time() - 50) and (profile_settings['tokenrun'] == 0 or profile_settings['tokenruntime'] < int(time.time() - 30)):
        force = 1

    if not check_key(profile_settings, 'drm_token_age') or not check_key(profile_settings, 'drm_locator') or locator != profile_settings['drm_locator'] or profile_settings['drm_token_age'] < int(time.time() - 90) or force == 1:
        profile_settings['tokenrun'] = 1
        profile_settings['tokenruntime'] = int(time.time())
        save_profile(profile_id=1, profile=profile_settings)

        if 'sdash' in path:
            jsondata = {"contentLocator": locator, "drmScheme": "sdash:BR-AVC-DASH"}
        else:
            jsondata = {"contentLocator": locator}

        download = api_download(url=CONST_API_URLS['token_url'], type='post', headers=api_get_headers(), data=jsondata, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'token'):
            profile_settings['tokenrun'] = 0
            save_profile(profile_id=1, profile=profile_settings)

            return None

        profile_settings = load_profile(profile_id=1)

        if not locator == profile_settings['drm_locator']:
            return False

        profile_settings['tokenrun'] = 0
        profile_settings['drm_path'] = path
        profile_settings['drm_token'] = data['token']
        write_file(file='widevine_token', data=data['token'], isJSON=False)
        profile_settings['drm_token_age'] = int(time.time())
        profile_settings['drm_locator'] = locator
        save_profile(profile_id=1, profile=profile_settings)

        return data['token']
    else:
        return profile_settings['drm_token']

def api_get_session(force=0):
    force = int(force)
    profile_settings = load_profile(profile_id=1)

    devices_url = CONST_API_URLS['devices_url']

    download = api_download(url=devices_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'isAccountEnabled'):
        login_result = api_login()

        if not login_result['result']:
            return False

    profile_settings = load_profile(profile_id=1)
    profile_settings['last_login_success'] = 1
    profile_settings['last_login_time'] = int(time.time())
    save_profile(profile_id=1, profile=profile_settings)

    return True

def api_get_profiles():
    return None

def api_set_profile(id=''):
    return None

def api_get_watchlist_id():
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    watchlist_url = '{watchlist_url}/profile/{profile_id}?language=nl&maxResults=1&order=DESC&sharedProfile=true&sort=added'.format(watchlist_url=CONST_API_URLS['watchlist_url'], profile_id=profile_settings['ziggo_profile_id'])

    download = api_download(url=watchlist_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'watchlistId'):
        return False

    profile_settings['watchlist_id'] = data['watchlistId']
    save_profile(profile_id=1, profile=profile_settings)

    return True

def api_list_watchlist(continuewatch=0):
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    watchlist_url = '{watchlist_url}/profile/{profile_id}?language=nl&order=DESC&sharedProfile=true&sort=added'.format(watchlist_url=CONST_API_URLS['watchlist_url'], profile_id=profile_settings['ziggo_profile_id'])

    download = api_download(url=watchlist_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'entries'):
        return False

    return data

def api_login():
    creds = get_credentials()
    username = creds['username']
    password = creds['password']

    try:
        os.remove(ADDON_PROFILE + 'stream_cookies')
    except:
        pass

    profile_settings = load_profile(profile_id=1)

    profile_settings['access_token'] = ''
    profile_settings['ziggo_profile_id'] = ''
    profile_settings['household_id'] = ''
    profile_settings['watchlist_id'] = ''
    save_profile(profile_id=1, profile=profile_settings)

    HEADERS = {
        'User-Agent':  DEFAULT_USER_AGENT,
        'X-Client-Id': CONST_DEFAULT_CLIENTID + "||" + DEFAULT_USER_AGENT,
    }

    download = api_download(url=CONST_API_URLS['session_url'], type='post', headers=HEADERS, data={"username": username, "password": password}, json_data=True, return_json=True)
    data = download['data']
    code = download['code']

    if code and data and check_key(data, 'reason') and data['reason'] == 'wrong backoffice':
        return { 'code': code, 'data': data, 'result': False }

    if not code or not data or not check_key(data, 'oespToken'):
        if not code:
            code = {}

        if not data:
            data = {}

        return { 'code': code, 'data': data, 'result': False }

    ziggo_profile_id = ''
    household_id = ''

    try:
        ziggo_profile_id = data['customer']['sharedProfileId']
    except:
        pass

    try:
        household_id = data['customer']['householdId']
    except:
        pass

    profile_settings['access_token'] = data['oespToken']
    profile_settings['ziggo_profile_id'] = ziggo_profile_id
    profile_settings['household_id'] = household_id
    save_profile(profile_id=1, profile=profile_settings)

    if len(str(profile_settings['watchlist_id'])) == 0:
        api_get_watchlist_id()

    return { 'code': code, 'data': data, 'result': True }

def api_play_url(type, channel=None, id=None, video_data=None, from_beginning=0, pvr=0, change_audio=0):
    playdata = {'path': '', 'mpd': '', 'license': '', 'token': '', 'locator': '', 'type': '', 'properties': {}}

    if not api_get_session():
        return playdata

    api_clean_after_playback()

    from_beginning = int(from_beginning)
    pvr = int(pvr)
    change_audio = int(change_audio)

    profile_settings = load_profile(profile_id=1)

    if type == "channel":
        id = channel

    info = {}
    properties = {}
    base_listing_url = CONST_API_URLS['listings_url']
    urldata = None
    urldata2 = None
    path = None
    locator = None

    if not type or not len(str(type)) > 0 or not id or not len(str(id)) > 0:
        return playdata

    if type == 'channel':
        data = api_get_channels()

        try:
            split = data[id]['assetid'].rsplit('&%%&', 1)

            if len(split) == 2:
                urldata = {'play_url': split[0], 'locator': split[1]}
            else:
                return playdata
        except:
            return playdata

        listing_url = '{listings_url}?byEndTime={time}~&byStationId={channel}&range=1-1&sort=startTime'.format(listings_url=base_listing_url, time=int(time.time() * 1000), channel=id)
        download = api_download(url=listing_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and check_key(data, 'listings'):
            for row in data['listings']:
                if check_key(row, 'program'):
                    info = row['program']
    elif type == 'program':
        listings_url = "{listings_url}/{id}".format(listings_url=base_listing_url, id=id)
        download = api_download(url=listings_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'program'):
            return playdata

        info = data['program']
    elif type == 'vod':
        mediaitems_url = '{mediaitems_url}/{id}'.format(mediaitems_url=CONST_API_URLS['mediaitems_url'], id=id)
        download = api_download(url=mediaitems_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data:
            return playdata

        info = data

    if check_key(info, 'videoStreams'):
        urldata2 = get_play_url(content=info['videoStreams'])

    if not type == 'channel' and (not urldata2 or not check_key(urldata2, 'play_url') or not check_key(urldata2, 'locator') or urldata2['play_url'] == 'http://Playout/using/Session/Service'):
        urldata2 = {}

        if type == 'program':
            playout_str = 'replay'
        elif type == 'vod':
            playout_str = 'vod'
        else:
            return playdata

        playout_url = '{base_url}/playout/{playout_str}/{id}?abrType=BR-AVC-DASH'.format(base_url=CONST_API_URLS['base_url'], playout_str=playout_str, id=id)
        download = api_download(url=playout_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'url') or not check_key(data, 'contentLocator'):
            return playdata

        urldata2['play_url'] = data['url']
        urldata2['locator'] = data['contentLocator']

    if urldata and urldata2 and check_key(urldata, 'play_url') and check_key(urldata, 'locator') and check_key(urldata2, 'play_url') and check_key(urldata2, 'locator'):
        if not from_beginning == 1:
            path = urldata['play_url']
            locator = urldata['locator']
        else:
            path = urldata2['play_url']
            locator = urldata2['locator']
    else:
        if urldata and check_key(urldata, 'play_url') and check_key(urldata, 'locator'):
            path = urldata['play_url']
            locator = urldata['locator']
        elif urldata2 and check_key(urldata2, 'play_url') and check_key(urldata2, 'locator'):
            path = urldata2['play_url']
            locator = urldata2['locator']

    if not locator or not len(str(locator)) > 0:
        return playdata

    license = CONST_API_URLS['widevine_url']

    profile_settings = load_profile(profile_id=1)
    profile_settings['drm_locator'] = locator
    save_profile(profile_id=1, profile=profile_settings)

    token = api_get_play_token(locator=locator, path=path, force=1)
    token_orig = token

    if not token or not len(str(token)) > 0:
        return playdata

    token = 'WIDEVINETOKEN'
    token_regex = re.search(r"(?<=;vxttoken=)(.*?)(?=/)", path)

    if token_regex and token_regex.group(1) and len(token_regex.group(1)) > 0:
        path = path.replace(token_regex.group(1), token)
    else:
        if 'sdash/' in path:
            spliturl = path.split('sdash/', 1)

            if len(spliturl) == 2:
                path = '{urlpart1}sdash;vxttoken={token}/{urlpart2}'.format(urlpart1=spliturl[0], token=token, urlpart2=spliturl[1])
        else:
            spliturl = path.rsplit('/', 1)

            if len(spliturl) == 2:
                path = '{urlpart1};vxttoken={token}/{urlpart2}'.format(urlpart1=spliturl[0], token=token, urlpart2=spliturl[1])

    mpd = ''

    if change_audio == 1:
        mpd_path = path.replace('WIDEVINETOKEN', token_orig)

        download = api_download(url=mpd_path, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=False)
        data = download['data']
        code = download['code']

        if code and code == 200:
            mpd = data

    playdata = {'path': path, 'mpd': mpd, 'license': license, 'token': token, 'locator': locator, 'info': info, 'type': type, 'properties': properties}

    return playdata

def api_remove_from_watchlist(id, continuewatch=0):
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    remove_url = '{watchlist_url}/{watchlist_id}/entries/{id}?sharedProfile=true'.format(watchlist_url=CONST_API_URLS['watchlist_url'], watchlist_id=profile_settings['watchlist_id'], id=id)

    download = api_download(url=remove_url, type='delete', headers=api_get_headers(), data=None, json_data=False, return_json=False)
    code = download['code']

    if not code or not code == 204:
        return False

    return True

def api_search(query):
    if not api_get_session():
        return None

    return False

    end = int(time.time() * 1000)
    start = end - (7 * 24 * 60 * 60 * 1000)

    vodstr = ''

    encodedBytes = base64.b32encode(query.encode("utf-8"))
    queryb32 = str(encodedBytes, "utf-8")

    file = "cache" + os.sep + "{query}.json".format(query=queryb32)

    search_url = '{search_url}?byBroadcastStartTimeRange={start}~{end}&numItems=25&byEntitled=true&personalised=true&q={query}'.format(search_url=CONST_API_URLS['search_url'], start=start, end=end, query=quote_plus(query))

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=search_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and (check_key(data, 'tvPrograms') or check_key(data, 'moviesAndSeries')):
            write_file(file=file, data=data, isJSON=True)

    if not data or (not check_key(data, 'tvPrograms') and not check_key(data, 'moviesAndSeries')):
        return False

    items = []
    items_vod = []
    items_program = []
    vod_links = {}

    if not settings.getBool('showMoviesSeries'):
        try:
            data.pop('moviesAndSeries', None)
        except:
            pass
    else:
        for entry in CONST_VOD_CAPABILITY:
            data2 = api_get_vod_by_type(type=entry['file'], character=None, genre=None, subscription_filter=None)

            for currow in data2:
                row = data2[currow]

                vod_links[row['id']] = {}
                vod_links[row['id']]['seasons'] = row['seasons']
                vod_links[row['id']]['duration'] = row['duration']
                vod_links[row['id']]['desc'] = row['description']
                vod_links[row['id']]['type'] = row['type']

    for currow in list(data):
        if currow == "moviesAndSeries":
            type = 'vod'
        else:
            type = 'program'

        for row in data[currow]['entries']:
            if not check_key(row, 'id') or not check_key(row, 'title'):
                continue

            item = {}

            id = row['id']
            label = row['title']
            description = ''
            duration = 0
            program_image = ''
            program_image_large = ''
            start = ''

            if check_key(row, 'images'):
                program_image = get_image("boxart", row['images'])
                program_image_large = get_image("HighResLandscape", row['images'])

                if program_image_large == '':
                    program_image_large = program_image
                else:
                    program_image_large += '?w=1920&mode=box'

            if type == 'vod':
                if check_key(vod_links, row['id']):
                    description = vod_links[row['id']]['desc']
                    item_type = vod_links[row['id']]['type']
                else:
                    item_type = 'Vod'

                label += " (Movies and Series)"
            else:
                item_type = 'Epg'
                label += " (ReplayTV)"

            if check_key(row, 'groupType') and row['groupType'] == 'show':
                if check_key(row, 'episodeMatch') and check_key(row['episodeMatch'], 'seriesEpisodeNumber') and check_key(row['episodeMatch'], 'secondaryTitle'):
                    if len(description) == 0:
                        description += label

                    season = ''

                    if check_key(row, 'seriesNumber'):
                        season = "S" + row['seriesNumber']

                    description += " Episode Match: {season}E{episode} - {secondary}".format(season=season, episode=row['episodeMatch']['seriesEpisodeNumber'], secondary=row['episodeMatch']['secondaryTitle'])
            else:
                if check_key(row, 'duration'):
                    duration = int(row['duration'])
                elif check_key(row, 'episodeMatch') and check_key(row['episodeMatch'], 'startTime') and check_key(row['episodeMatch'], 'endTime'):
                    duration = int(int(row['episodeMatch']['endTime']) - int(row['episodeMatch']['startTime'])) // 1000
                    id = row['episodeMatch']['id']
                elif check_key(vod_links, row['id']) and check_key(vod_links[row['id']], 'duration'):
                    duration = vod_links[row['id']]['duration']

            item['id'] = id
            item['title'] = label
            item['description'] = description
            item['duration'] = duration
            item['type'] = item_type
            item['icon'] = program_image_large
            item['start'] = start

            if type == "vod":
                items_vod.append(item)
            else:
                items_program.append(item)

    num = min(len(items_program), len(items_vod))
    items = [None]*(num*2)
    items[::2] = items_program[:num]
    items[1::2] = items_vod[:num]
    items.extend(items_program[num:])
    items.extend(items_vod[num:])

    return items

def api_vod_download():
    return None

def api_vod_season(series, id):
    if not api_get_session():
        return None

    season = []

    profile_settings = load_profile(profile_id=1)

    season_url = '{mediaitems_url}?byMediaType=Episode%7CFeatureFilm&byParentId={id}&includeAdult=true&range=1-1000&sort=seriesEpisodeNumber|ASC'.format(mediaitems_url=CONST_API_URLS['mediaitems_url'], id=id)
    download = api_download(url=season_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

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

def api_vod_seasons(type, id):
    seasons = []

    data = api_get_vod_by_type(type=type, character=None, genre=None, subscription_filter=None)

    if data:
        try:
            row = data[str(id)]

            data_seasons = json.loads(row['seasons'])

            for season in data_seasons:
                seasons.append({'id': season['id'], 'seriesNumber': season['seriesNumber'], 'description': row['description'], 'image': row['icon']})

        except:
            return None

    return {'type': 'seasons', 'seasons': seasons, 'watchlist': id}

def api_vod_subscription():
    return None

def api_watchlist_listing(id):
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    end = int(time.time() * 1000)
    start = end - (7 * 24 * 60 * 60 * 1000)

    mediaitems_url = '{media_items_url}?&byMediaGroupId={id}&byStartTime={start}~{end}&range=1-250&sort=startTime%7Cdesc'.format(media_items_url=CONST_API_URLS['listings_url'], id=id, start=start, end=end)
    download = api_download(url=mediaitems_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'listings'):
        return False

    return data

def api_clean_after_playback():
    profile_settings = load_profile(profile_id=1)

    headers = api_get_headers()
    headers['Content-type'] = 'application/json'

    download = api_download(url=CONST_API_URLS['clearstreams_url'], type='post', headers=headers, data='{}', json_data=False, return_json=False)