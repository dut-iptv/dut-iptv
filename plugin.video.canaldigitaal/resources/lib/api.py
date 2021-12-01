import base64, datetime, os, re, time, uuid, xbmc

from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE, DEFAULT_BROWSER_NAME, DEFAULT_BROWSER_VERSION, DEFAULT_OS_NAME, DEFAULT_OS_VERSION
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, get_credentials, is_file_older_than_x_days, is_file_older_than_x_minutes, load_file, load_profile, load_prefs, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import api_download
from resources.lib.constants import CONST_BASE_HEADERS, CONST_BASE_URL, CONST_DEFAULT_API, CONST_LOGIN_HEADERS, CONST_LOGIN_URL
from resources.lib.util import plugin_process_info
from urllib.parse import parse_qs, urlparse, quote_plus

def api_add_to_watchlist():
    return None

def api_get_info(id, channel=''):
    profile_settings = load_profile(profile_id=1)

    info = {}
    headers = {'Authorization': 'Bearer ' + profile_settings['session_token']}

    info_url = '{api_url}/assets/{channel}'.format(api_url=CONST_DEFAULT_API, channel=id)

    download = api_download(url=info_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'id'):
        return info

    info = data

    info = plugin_process_info({'title': '', 'channel': channel, 'info': info})

    return info

def api_get_session(force=0):
    force = int(force)
    profile_settings = load_profile(profile_id=1)

    headers = {'Authorization': 'Bearer ' + profile_settings['session_token']}

    capi_url = '{api_url}/settings'.format(api_url=CONST_DEFAULT_API)

    download = api_download(url=capi_url, type='get', headers=headers, data=None, json_data=False, return_json=False, allow_redirects=False)
    data = download['data']
    code = download['code']

    if not code or not code == 200:
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

def api_list_watchlist(continuewatch=0):
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

    profile_settings['session_token'] = ''

    if not profile_settings or not check_key(profile_settings, 'devicekey') or len(profile_settings['devicekey']) == 0:
        devicekey = 'w{uuid}'.format(uuid=uuid.uuid4())
        profile_settings['devicekey'] = devicekey

    save_profile(profile_id=1, profile=profile_settings)

    oauth = ''
    auth_url = '{login_url}/authenticate?redirect_uri=https%3A%2F%2Flivetv.canaldigitaal.nl%2Fauth.aspx&state={state}&response_type=code&scope=TVE&client_id=StreamGroup'.format(login_url=CONST_LOGIN_URL, state=int(time.time()))

    download = api_download(url=auth_url, type='get', headers=None, data=None, json_data=False, return_json=False, allow_redirects=False)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data:
        return { 'code': code, 'data': data, 'result': False }

    headers = CONST_LOGIN_HEADERS
    headers.update({'Referer': auth_url})

    session_post_data = {
        "Password": password,
        "Username": username,
    }

    download = api_download(url=CONST_LOGIN_URL, type='post', headers=headers, data=session_post_data, json_data=False, return_json=False, allow_redirects=False)
    data = download['data']
    code = download['code']
    headers = download['headers']

    if not code or not code == 302:
        return { 'code': code, 'data': data, 'result': False }

    params = parse_qs(urlparse(headers['Location']).query)

    if check_key(params, 'code'):
        oauth = params['code'][0]

    if len(oauth) == 0:
        return { 'code': code, 'data': data, 'result': False }

    challenge_url = "{base_url}/m7be2iphone/challenge.aspx".format(base_url=CONST_BASE_URL)

    session_post_data = {
        "autotype": "nl",
        "app": "cds",
        "prettyname": DEFAULT_BROWSER_NAME,
        "model": "web",
        "serial": profile_settings['devicekey'],
        "oauthcode": oauth
    }

    headers = {'Content-Type': 'application/json;charset=UTF-8'}

    download = api_download(url=challenge_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True, allow_redirects=False)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'id') or not check_key(data, 'secret'):
        return { 'code': code, 'data': data, 'result': False }

    login_url = "{base_url}/m7be2iphone/login.aspx".format(base_url=CONST_BASE_URL)

    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

    secret = '{id}\t{secr}'.format(id=data['id'], secr=data['secret'])

    session_post_data = {
        "secret": secret,
        "uid": profile_settings['devicekey'],
        "app": "cds",
    }

    download = api_download(url=login_url, type='post', headers=headers, data=session_post_data, json_data=False, return_json=False, allow_redirects=False)
    data = download['data']
    code = download['code']

    if not code or not code == 302:
        return { 'code': code, 'data': data, 'result': False }

    ssotoken_url = "{base_url}/m7be2iphone/capi.aspx?z=ssotoken".format(base_url=CONST_BASE_URL)

    download = api_download(url=ssotoken_url, type='get', headers=None, data=None, json_data=False, return_json=True, allow_redirects=False)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'ssotoken'):
        return { 'code': code, 'data': data, 'result': False }

    session_url = "{api_url}/session".format(api_url=CONST_DEFAULT_API)

    session_post_data = {
        "sapiToken": data['ssotoken'],
        "deviceType": "PC",
        "deviceModel": DEFAULT_BROWSER_NAME,
        "osVersion": '{name} {version}'.format(name=DEFAULT_OS_NAME, version=DEFAULT_OS_VERSION),
        "deviceSerial": profile_settings['devicekey'],
        "appVersion": DEFAULT_BROWSER_VERSION,
        "brand": "cds"
    }

    headers = {'Content-Type': 'application/json;charset=UTF-8'}

    download = api_download(url=session_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True, allow_redirects=False)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'token'):
        return { 'code': code, 'data': data, 'result': False }

    profile_settings['session_token'] = data['token']
    save_profile(profile_id=1, profile=profile_settings)

    return { 'code': code, 'data': data, 'result': True }

def api_play_url(type, channel=None, id=None, video_data=None, from_beginning=0, pvr=0, change_audio=0):
    playdata = {'path': '', 'license': '', 'info': '', 'properties': {}}

    if not api_get_session():
        return playdata

    from_beginning = int(from_beginning)
    pvr = int(pvr)
    change_audio = int(change_audio)
    
    profile_settings = load_profile(profile_id=1)
    found_alt = False

    info = {}
    properties = {}

    headers = {'Authorization': 'Bearer ' + profile_settings['session_token']}

    if type == 'channel':
        info_url = '{api_url}/assets/{channel}'.format(api_url=CONST_DEFAULT_API, channel=channel)
    else:
        info_url = '{api_url}/assets/{id}'.format(api_url=CONST_DEFAULT_API, id=id)

    play_url = info_url + '/play'

    session_post_data = {
        "player": {
            "name":"Bitmovin",
            "version":"8.22.0",
            "capabilities": {
                "mediaTypes": ["DASH","HLS","MSSS","Unspecified"],
                "drmSystems": ["Widevine"],
            },
            "drmSystems": ["Widevine"],
        },
    }

    if not pvr == 1 or settings.getBool(key='ask_start_from_beginning') or from_beginning == 1:
        download = api_download(url=info_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'id'):
            return playdata

        info = data

        if type == 'channel' and check_key(data, 'params') and check_key(data['params'], 'now') and check_key(data['params']['now'], 'id'):
            play_url2 = '{api_url}/assets/{id}/play'.format(api_url=CONST_DEFAULT_API, id=data['params']['now']['id'])
            info = data['params']['now']

            if from_beginning == 1:
                download = api_download(url=play_url2, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
                data = download['data']
                code = download['code']

                if code and code == 200 and data and check_key(data, 'url'):
                    if check_key(data, 'drm') and check_key(data['drm'], 'licenseUrl'):
                        license = data['drm']['licenseUrl']

                    path = data['url']
                    found_alt = True

    if not from_beginning == 1 or not found_alt:
        download = api_download(url=play_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'url'):
            return playdata

        if check_key(data, 'drm') and check_key(data['drm'], 'licenseUrl'):
            license = data['drm']['licenseUrl']

        path = data['url']

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
    return None

def api_search(query):
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    encodedBytes = base64.b32encode(query.encode("utf-8"))
    queryb32 = str(encodedBytes, "utf-8")

    file = "cache" + os.sep + "{query}.json".format(query=queryb32)

    headers = {'Authorization': 'Bearer ' + profile_settings['session_token']}

    search_url = '{api_url}/search?query={query}'.format(api_url=CONST_DEFAULT_API, query=quote_plus(query))

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=search_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and check_key(data, 'collection'):
            write_file(file=file, data=data, isJSON=True)

    if not data or not check_key(data, 'collection'):
        return None

    items = []
    items_vod = []
    items_program = []

    for currow in data['collection']:
        if not settings.getBool('showMoviesSeries') and currow['label'] == 'sg.ui.search.vod':
            continue
        elif currow['label'] == 'sg.ui.search.epg':
            continue

        if currow['label'] == 'sg.ui.search.vod':
            type = 'vod'
        else:
            type = 'program'

        for row in currow['assets']:
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
                program_image = row['images'][0]['url']
                program_image_large = row['images'][0]['url']

            if type == 'vod':
                item_type = 'Vod'

                label += " (VOD)"
            else:
                item_type = 'Epg'
                label += " (ReplayTV)"

            if check_key(row, 'params'):
                if check_key(row['params'], 'duration'):
                    duration = int(row['params']['duration'])
                elif check_key(row['params'], 'start') and check_key(row['params'], 'end'):
                    duration = int(re.sub('[^0-9]','', row['params']['end'])) - int(re.sub('[^0-9]','', row['params']['end']))

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

    #num = min(len(items_program), len(items_vod))
    #items = [None]*(num*2)
    #items[::2] = items_program[:num]
    #items[1::2] = items_vod[:num]
    #items.extend(items_program[num:])
    #items.extend(items_vod[num:])

    items = items_program

    return items

def api_vod_download():
    return None

def api_vod_season(series, id):
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    season = []
    episodes = []

    headers = {'Authorization': 'Bearer ' + profile_settings['session_token']}

    program_url = '{api_url}/assets?query={id}'.format(api_url=CONST_DEFAULT_API, id=id)

    type = "vod_season_" + str(id)
    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=program_url, type='get', headers=headers, data=None, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and check_key(data, 'assets'):
            write_file(file=file, data=data, isJSON=True)

    if not data or not check_key(data, 'assets'):
        return None

    for row in data['assets']:
        episodes.append(str(row['params']['seriesEpisode']))

        label = '{season}.{episode} - {title}'.format(season=str(row['params']['seriesSeason']), episode=str(row['params']['seriesEpisode']), title=str(row['title']))

        season.append({'label': label, 'id': str(row['id']), 'assetid': '', 'duration': row['params']['duration'], 'title': str(row['title']), 'episodeNumber': '{season}.{episode}'.format(season=str(row['params']['seriesSeason']), episode=str(row['params']['seriesEpisode'])), 'description': '', 'image': str(row['images'][0]['url'])})

    return season

def api_vod_seasons(type, id):
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    seasons = []

    headers = {'Authorization': 'Bearer ' + profile_settings['session_token']}

    program_url = '{api_url}/collections/related,tve?group=default&sort=default&asset={id}'.format(api_url=CONST_DEFAULT_API, id=id)

    type = "vod_seasons_" + str(id)
    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=program_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and check_key(data, 'collection'):
            write_file(file=file, data=data, isJSON=True)

    if not data or not check_key(data, 'collection'):
        return None

    for row in data['collection']:
        if row['label'] == 'sg.ui.season.subst':
            seasons.append({'id': str(row['query']), 'seriesNumber': str(row['labelParams'][0]), 'description': '', 'image': ''})

    return {'type': 'seasons', 'seasons': seasons}

def api_vod_subscription():
    return None

def api_watchlist_listing():
    return None

def api_clean_after_playback():
    pass