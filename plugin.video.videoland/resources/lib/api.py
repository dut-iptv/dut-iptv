import base64, json, os, random, re, string, time, xbmc

from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE, CONST_DUT_EPG, SESSION_CHUNKSIZE
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, get_credentials, is_file_older_than_x_days, is_file_older_than_x_minutes, load_file, load_profile, load_prefs, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import api_download, api_get_channels
from resources.lib.constants import CONST_BASE_HEADERS, CONST_BASE_URL, CONST_IMAGES, CONST_GIGYA_URL
from resources.lib.util import plugin_process_info
from urllib.parse import parse_qs, urlparse, quote_plus

def api_add_to_watchlist(id, type):
    if not api_get_session():
        return None

    headers = {
        'videoland-platform': 'videoland',
    }

    watchlist_url = '{base_url}/api/v3/watchlist/{id}'.format(base_url=CONST_BASE_URL, id=id)

    download = api_download(url=watchlist_url, type='post', headers=headers, data=None, json_data=False, return_json=False)
    code = download['code']

    if not code or not code == 200:
        return False

    return True

def api_get_info(id, channel=''):
    profile_settings = load_profile(profile_id=1)

    info = {}

    return info

def api_get_session(force=0, return_data=False):
    force = int(force)

    profile_url = '{base_url}/api/v3/profiles'.format(base_url=CONST_BASE_URL)

    headers = {
        'videoland-platform': 'videoland',
        "Referer": CONST_BASE_URL + "/profielkeuze",
    }

    download = api_download(url=profile_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data[0], 'id'):
        login_result = api_login()

        if not login_result['result']:
            if return_data == True:
                return {'result': False, 'data': login_result['data'], 'code': login_result['code']}

            return False
        else:
            download = api_download(url=profile_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
            data = download['data']
            code = download['code']

    profile_settings = load_profile(profile_id=1)
    profile_settings['last_login_success'] = 1
    profile_settings['last_login_time'] = int(time.time())
    save_profile(profile_id=1, profile=profile_settings)

    if return_data == True:
        return {'result': True, 'data': data, 'code': code}

    return True

def api_get_profiles():
    profiles = api_get_session(force=0, return_data=True)
    return_profiles = {}

    if profiles['result'] == True:
        for result in profiles['data']:
            if result['is_active'] == True:
                return_profiles[result['id']] = {}
                return_profiles[result['id']]['id'] = result['id']
                return_profiles[result['id']]['name'] = result['profilename']

    return return_profiles

def api_get_series_nfo():
    type = 'seriesnfo'
    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    vod_url = '{dut_epg_url}/{type}.zip'.format(dut_epg_url=CONST_DUT_EPG, type=type)
    file = "cache" + os.sep + "{type}.json".format(type=type)
    tmp = ADDON_PROFILE + 'tmp' + os.sep + "{type}.zip".format(type=type)

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        resp = Session().get(vod_url, stream=True)

        if resp.status_code != 200:
            resp.close()
            return None

        with open(tmp, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=SESSION_CHUNKSIZE):
                f.write(chunk)

        resp.close()

        if os.path.isfile(tmp):
            from zipfile import ZipFile

            try:
                with ZipFile(tmp, 'r') as zipObj:
                    zipObj.extractall(ADDON_PROFILE + "cache" + os.sep)
            except:
                try:
                    fixBadZipfile(tmp)

                    with ZipFile(tmp, 'r') as zipObj:
                        zipObj.extractall(ADDON_PROFILE + "cache" + os.sep)

                except:
                    try:
                        from resources.lib.base.l1.zipfile import ZipFile as ZipFile2

                        with ZipFile2(tmp, 'r') as zipObj:
                            zipObj.extractall(ADDON_PROFILE + "cache" + os.sep)
                    except:
                        return None

def api_set_profile(id=''):
    profile_settings = load_profile(profile_id=1)
    profiles = api_get_session(force=0, return_data=True)
    name = ''
    owner_id = ''
    owner_name = ''
    saved_id = ''
    saved_name = ''

    if not profiles or profiles['result'] == False:
        return False

    for result in profiles['data']:
        if result['is_account_owner'] == True:
            owner_id = result['id']
            owner_name = result['profilename']
        if result['is_active'] == True and result['id'] == id:
            name = result['profilename']
        if result['is_active'] == True and result['id'] == profile_settings['profile_id']:
            saved_id = result['id']
            saved_name = result['profilename']

    if len(str(name)) == 0:
        if len(str(saved_name)) > 0:
            id = saved_id
            name = saved_name
        else:
            id = owner_id
            name = owner_name

    switch_url = '{base_url}/api/v3/profiles/{id}/switch'.format(base_url=CONST_BASE_URL, id=id)

    headers = {
        'videoland-platform': 'videoland',
        "Referer": CONST_BASE_URL + "/profielkeuze",
    }

    session_post_data = {
        'customer_id': id
    }

    download = api_download(url=switch_url, type='post', headers=headers, data=session_post_data, json_data=False, return_json=False)
    code = download['code']

    if not code or not code == 204:
        return False

    profile_settings = load_profile(profile_id=1)
    profile_settings['profile_name'] = name
    profile_settings['profile_id'] = id
    save_profile(profile_id=1, profile=profile_settings)

    return True

def api_list_watchlist(continuewatch=0):
    continuewatch = int(continuewatch)

    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    headers = {
        'videoland-platform': 'videoland',
    }

    if continuewatch == 1:
        watchlist_url = '{base_url}/api/v3/progress/{id}'.format(base_url=CONST_BASE_URL, id=profile_settings['profile_id'])
    else:
        watchlist_url = '{base_url}/api/v3/watchlist/{id}'.format(base_url=CONST_BASE_URL, id=profile_settings['profile_id'])

    download = api_download(url=watchlist_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if code and code == 200 and data and check_key(data, 'count'):
        return data

    return None

def api_login():
    creds = get_credentials()
    username = creds['username']
    password = creds['password']

    try:
        os.remove(ADDON_PROFILE + 'stream_cookies')
    except:
        pass

    profile_settings = load_profile(profile_id=1)
    profile_settings['vlid'] = ''
    profile_settings['profile_id'] = ''

    save_profile(profile_id=1, profile=profile_settings)

    headers = {
        "Origin": CONST_GIGYA_URL,
        "Referer": CONST_GIGYA_URL + "/",
    }

    session_post_data = {
        'loginID': username,
        'password': password,
        'sessionExpiration': '0',
        'targetEnv': 'jssdk',
        'include': 'profile,data',
        'includeUserInfo': 'true',
        'lang': 'en',
        'APIKey': '3_t2Z1dFrbWR-IjcC-Bod1kei6W91UKmeiu3dETVG5iKaY4ILBRzVsmgRHWWo0fqqd',
        'sdk': 'js_latest',
        'authMode': 'cookie',
        'pageURL': CONST_BASE_URL + '/',
        'format': 'json',
    }

    login_url = '{gigya_url}/accounts.login'.format(gigya_url=CONST_GIGYA_URL)

    download = api_download(url=login_url, type='post', headers=headers, data=session_post_data, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'signatureTimestamp') or not check_key(data, 'UID') or not check_key(data, 'UIDSignature'):
        return { 'code': code, 'data': data, 'result': False }

    hash_url = '{base_url}/api/v3/login/hash'.format(base_url=CONST_BASE_URL)

    headers = {
        'videoland-platform': 'videoland',
        "Origin": CONST_BASE_URL,
        "Referer": CONST_BASE_URL + "/inloggen",
    }

    session_post_data = {
        'UID': data['UID'],
        'UIDSignature': data['UIDSignature'],
        'signatureTimestamp': data['signatureTimestamp'],
    }

    download = api_download(url=hash_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'vlHash'):
        return { 'code': code, 'data': data, 'result': False }

    profile_settings['vlid'] = data['vlHash']

    cookies = load_file(file='stream_cookies', isJSON=True)

    if not cookies:
        cookies = {}

    cookies['vlId'] = data['vlHash']

    write_file(file='stream_cookies', data=cookies, isJSON=True)

    profile_url = '{base_url}/api/v3/profiles'.format(base_url=CONST_BASE_URL)

    headers = {
        'videoland-platform': 'videoland',
        "Referer": CONST_BASE_URL + "/profielkeuze",
    }

    download = api_download(url=profile_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data[0], 'id'):
        return { 'code': code, 'data': data, 'result': False }

    save_profile(profile_id=1, profile=profile_settings)

    api_set_profile()

    return { 'code': code, 'data': data, 'result': True }

def api_play_url(type, channel=None, id=None, video_data=None, from_beginning=0, pvr=0, change_audio=0):
    playdata = {'path': '', 'license': '', 'info': '', 'properties': {}}

    if not api_get_session():
        return playdata

    from_beginning = int(from_beginning)
    pvr = int(pvr)
    change_audio = int(change_audio)

    profile_settings = load_profile(profile_id=1)

    info = {}
    properties = {}

    if not type or not len(str(type)) > 0:
        return playdata

    headers = {
        'videoland-platform': 'videoland',
    }

    if type == 'channel':
        play_url_path = id

        download = api_download(url=play_url_path, type='get', headers=headers, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'manifest') or not check_key(data, 'token'):
            return playdata

        path = data['manifest']

        if check_key(data, 'licenseUrl'):
            license = data['licenseUrl']

        profile_settings['ticket_id'] = ''
        profile_settings['token'] = data['token']
        save_profile(profile_id=1, profile=profile_settings)

        mpd = ''

        playdata = {'path': path, 'mpd': mpd, 'license': license, 'info': info, 'properties': properties}

        return playdata

    if id.startswith('E'):
        typestr = 'episode'
        id = id[1:]
        id_ar = id.split('###')
        series = id_ar[0]
        season = id_ar[1]
        id = id_ar[2]
        info_url = '{base_url}/api/v3/episodes/{series}/{season}'.format(base_url=CONST_BASE_URL, series=series, season=season)
    elif id.startswith('M'):
        typestr = 'movie'
        id = id[1:]
        info_url = '{base_url}/api/v3/movies/{id}'.format(base_url=CONST_BASE_URL, id=id)
    else:
        return playdata

    download = api_download(url=info_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if code and code == 200 and data:
        if typestr == 'episode':
            if check_key(data, 'details') and check_key(data['details'], 'E' + str(id)):
                info = data['details']['E' + str(id)]
        else:
            info = data

    play_url_path = '{base_url}/api/v3/stream/{id}/widevine?edition=&profile_id={profile_id}'.format(base_url=CONST_BASE_URL, id=id, profile_id=profile_settings['profile_id'])

    download = api_download(url=play_url_path, type='get', headers=headers, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'id') or not check_key(data, 'ticket_id') or not check_key(data, 'stream') or not check_key(data['stream'], 'dash'):
        return playdata

    path = data['stream']['dash']

    if check_key(data, 'drm'):
        license = data['drm']

    profile_settings['ticket_id'] = data['ticket_id']
    profile_settings['token'] = data['stream']['token']
    save_profile(profile_id=1, profile=profile_settings)

    mpd = ''

    if change_audio == 1:
        download = api_download(url=path, type='get', headers=headers, data=None, json_data=False, return_json=False)
        data = download['data']
        code = download['code']

        if code and code == 200:
            mpd = data

    playdata = {'path': path, 'mpd': mpd, 'license': license, 'info': info, 'properties': properties}

    return playdata

def api_remove_from_watchlist(id, continuewatch=0):
    continuewatch = int(continuewatch)

    if not api_get_session():
        return None

    headers = {
        'videoland-platform': 'videoland',
    }

    if continuewatch == 1:
        remove_url = '{base_url}/api/v3/progress/{id}'.format(base_url=CONST_BASE_URL, id=id)
    else:
        remove_url = '{base_url}/api/v3/watchlist/{id}'.format(base_url=CONST_BASE_URL, id=id)

    download = api_download(url=remove_url, type='delete', headers=headers, data=None, json_data=False, return_json=False)
    code = download['code']

    if not code or (not code == 200 and not code == 204):
        return False

    return True

def api_search():
    return None

def api_vod_download():
    return None

def api_vod_season(series, id, raw=False, use_cache=True):
    if not api_get_session():
        return None

    season = []

    type = "vod_season_" + str(id)
    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    id_ar = id.split('###')
    series = id_ar[0]
    seasonstr = id_ar[1]
    cache = 0

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5) and use_cache == True:
        data = load_file(file=file, isJSON=True)
        cache = 1
    else:
        headers = {
            'videoland-platform': 'videoland',
        }

        seasons_url = '{base_url}/api/v3/series/{series}/seasons/{season}'.format(base_url=CONST_BASE_URL, series=series, season=seasonstr)

        download = api_download(url=seasons_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and check_key(data, 'title'):
            write_file(file=file, data=data, isJSON=True)
            
    if raw == True:
        return {'data': data, 'cache': cache}

    if not data or not check_key(data, 'details'):
        return None

    seasonno = ''

    if check_key(data['details'], 'SN' + str(seasonstr)):
        seasonno = data['details']['SN' + str(seasonstr)]['title']

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
                name = 'Aflevering ' + str(row['position'])

            label = '{seasonno}.{episode} - {title}'.format(seasonno=seasonno, episode=row['position'], title=name)

            season.append({'label': label, 'id': 'E' + str(series) + '###' + str(seasonstr) + '###' + str(row['id']), 'media_id': '', 'duration': duration, 'title': name, 'episodeNumber': row['position'], 'description': row['description'], 'image': image})

    return season

def api_vod_seasons(type, id, raw=False, github=False, use_cache=True):
    if not api_get_session():
        return None

    seasons = []

    type = "vod_seasons_" + str(id)

    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    ref = id
    id = id[1:]
    cache = 0

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5) and use_cache == True:
        data = load_file(file=file, isJSON=True)
        cache = 1
    else:
        found = False
    
        if github == True and use_cache == False:
            encodedBytes = base64.b32encode(ref.encode("utf-8"))
            encoded_ref = str(encodedBytes, "utf-8")

            seasons_url = '{dut_epg_url}/{type}.json'.format(dut_epg_url=CONST_DUT_EPG, type=encoded_ref)
            download = api_download(url=seasons_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
            data = download['data']
            code = download['code']

            if code and code == 200 and data and check_key(data, 'title'):
                write_file(file=file, data=data, isJSON=True)
                found = True
    
        if found == False:
            headers = {
                'videoland-platform': 'videoland',
            }

            seasons_url = '{base_url}/api/v3/series/{series}'.format(base_url=CONST_BASE_URL, series=id)

            download = api_download(url=seasons_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
            data = download['data']
            code = download['code']

            if code and code == 200 and data and check_key(data, 'title'):
                write_file(file=file, data=data, isJSON=True)

    if raw == True:
        return {'data': data, 'cache': cache}

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

def api_vod_subscription():
    return None

def api_watchlist_listing():
    return None

def api_clean_after_playback(stoptime):
    profile_settings = load_profile(profile_id=1)

    if len(str(profile_settings['ticket_id'])) > 0:
        offset = "00:00:00"

        if stoptime > 0:
            m, s = divmod(stoptime, 60)
            h, m = divmod(m, 60)
            offset = '{:02d}:{:02d}:{:02d}'.format(h, m, s)

        session_post_data = {
            'action': "stop",
            'buffer_state': 0,
            'buffer_total': 1,
            'offset': offset,
            'token': profile_settings['token']
        }

        headers = {
            'videoland-platform': 'videoland',
        }

        stop_url = '{base_url}/api/v3/heartbeat/{ticket_id}?action=stop&offset={offset}'.format(base_url=CONST_BASE_URL, ticket_id=profile_settings['ticket_id'], offset=offset)

        download = api_download(url=stop_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)

        session_post_data['action'] = 'exit'

        exit_url = '{base_url}/api/v3/heartbeat/{ticket_id}?action=exit&offset={offset}'.format(base_url=CONST_BASE_URL, ticket_id=profile_settings['ticket_id'], offset=offset)

        download = api_download(url=exit_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)