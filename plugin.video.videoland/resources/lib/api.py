import base64, json, os, random, re, string, time, xbmc

from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, get_credentials, is_file_older_than_x_days, is_file_older_than_x_minutes, load_file, load_profile, load_prefs, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import api_download, api_get_channels
from resources.lib.constants import CONST_BASE_HEADERS, CONST_BASE_URL, CONST_GIGYA_URL
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

def api_get_session(force=0):
    force = int(force)

    profile_url = '{base_url}/api/v3/profiles'.format(base_url=CONST_BASE_URL)

    headers = {
        'videoland-platform': 'videoland',
        "Referer": CONST_BASE_URL + "/profielkeuze",
    }

    download = api_download(url=profile_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data[0], 'id') or not check_key(data[0], 'gigya_id'):
        login_result = api_login()

        if not login_result['result']:
            return False

    profile_settings = load_profile(profile_id=1)
    profile_settings['last_login_success'] = 1
    profile_settings['last_login_time'] = int(time.time())
    save_profile(profile_id=1, profile=profile_settings)

    return True

def api_list_watchlist():
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    headers = {
        'videoland-platform': 'videoland',
    }

    watchlist_url = '{base_url}/api/v3/watchlist?profileId={profile_id}'.format(base_url=CONST_BASE_URL, profile_id=profile_settings['profile_id'])

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
    profile_settings['gigya_id'] = ''

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

    if not code or not code == 200 or not data or not check_key(data[0], 'id') or not check_key(data[0], 'gigya_id'):
        return { 'code': code, 'data': data, 'result': False }

    profile_settings['profile_id'] = data[0]['id']
    profile_settings['gigya_id'] = data[0]['gigya_id']
    save_profile(profile_id=1, profile=profile_settings)

    return { 'code': code, 'data': data, 'result': True }

def api_play_url(type, channel=None, id=None, video_data=None, from_beginning=0, pvr=0):
    playdata = {'path': '', 'license': '', 'info': '', 'properties': {}}

    if not api_get_session():
        return playdata

    profile_settings = load_profile(profile_id=1)
    info = {}
    properties = {}

    if not type or not len(str(type)) > 0:
        return playdata

    headers = {
        'videoland-platform': 'videoland',
    }

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

    playdata = {'path': path, 'license': license, 'info': info, 'properties': properties}

    return playdata

def api_remove_from_watchlist(id):
    if not api_get_session():
        return None

    headers = {
        'videoland-platform': 'videoland',
    }

    remove_url = '{base_url}/api/v3/watchlist/{id}'.format(base_url=CONST_BASE_URL, id=id)

    download = api_download(url=remove_url, type='delete', headers=headers, data=None, json_data=False, return_json=False)
    code = download['code']

    if not code or not code == 200:
        return False

    return True

def api_search():
    return None

def api_vod_download():
    return None

def api_vod_season(series, id):
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

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
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
                image = row['still'].replace('[format]', '1920x1080')

            if check_key(row, 'title') and len(str(row['title'])) > 0:
                name = row['title']
            else:
                name = 'Aflevering ' + str(row['position'])

            label = '{seasonno}.{episode} - {title}'.format(seasonno=seasonno, episode=row['position'], title=name)

            season.append({'label': label, 'id': 'E' + str(series) + '###' + str(seasonstr) + '###' + str(row['id']), 'media_id': '', 'duration': duration, 'title': name, 'episodeNumber': row['position'], 'description': row['description'], 'image': image})

    return season

def api_vod_seasons(type, id):
    if not api_get_session():
        return None

    seasons = []

    type = "vod_seasons_" + str(id)

    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    ref = id
    id = id[1:]

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        headers = {
            'videoland-platform': 'videoland',
        }

        seasons_url = '{base_url}/api/v3/series/{series}'.format(base_url=CONST_BASE_URL, series=id)

        download = api_download(url=seasons_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and check_key(data, 'title'):
            write_file(file=file, data=data, isJSON=True)

    if not data or not check_key(data, 'details'):
        return None

    for currow in data['details']:
        row = data['details'][currow]

        if check_key(row, 'type') and row['type'] == 'season':
            seasons.append({'id': str(id) + '###' + str(row['id']), 'seriesNumber': row['title'], 'description': data['description'], 'image': data['poster'].replace('[format]', '960x1433'), 'watchlist': ref})

    return {'type': 'seasons', 'seasons': seasons}

def api_vod_subscription():
    return None

def api_watchlist_listing():
    return None

def api_clean_after_playback():
    profile_settings = load_profile(profile_id=1)

    session_post_data = {
        'action': "stop",
        'buffer_state': 0,
        'buffer_total': 1,
        'offset': "00:00:00",
        'token': profile_settings['token']
    }

    headers = {
        'videoland-platform': 'videoland',
    }

    stop_url = '{base_url}/api/v3/heartbeat/{ticket_id}?action=stop&offset=00:00:00'.format(base_url=CONST_BASE_URL, ticket_id=profile_settings['ticket_id'])

    download = api_download(url=stop_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)

    session_post_data['action'] = 'exit'

    exit_url = '{base_url}/api/v3/heartbeat/{ticket_id}?action=exit&offset=00:00:00'.format(base_url=CONST_BASE_URL, ticket_id=profile_settings['ticket_id'])

    download = api_download(url=exit_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)