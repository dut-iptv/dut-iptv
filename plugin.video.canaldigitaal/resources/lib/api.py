import base64, datetime, os, time, uuid, xbmc

from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE, DEFAULT_BROWSER_NAME, DEFAULT_BROWSER_VERSION, DEFAULT_OS_NAME, DEFAULT_OS_VERSION
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, find_highest_bandwidth, get_credentials, is_file_older_than_x_days, is_file_older_than_x_minutes, load_file, load_profile, load_prefs, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import api_download
from resources.lib.constants import CONST_BASE_HEADERS, CONST_BASE_URL, CONST_DEFAULT_API, CONST_LOGIN_HEADERS, CONST_LOGIN_URL

try:
    from urllib.parse import parse_qs, urlparse, quote
except ImportError:
    from urlparse import parse_qs, urlparse
    from urllib import quote

try:
    unicode
except NameError:
    unicode = str

def api_add_to_watchlist():
    return None

def api_get_session(force=0):
    force = int(force)
    profile_settings = load_profile(profile_id=1)

    #if not force ==1 and check_key(profile_settings, 'last_login_time') and profile_settings['last_login_time'] > int(time.time() - 3600) and profile_settings['last_login_success'] == 1:
    #    return True
    #elif force == 1 and not profile_settings['last_login_success'] == 1:
    #    return False
    
    headers = {'Authorization': 'Bearer ' + profile_settings['session_token']}

    capi_url = '{api_url}/settings'.format(api_url=CONST_DEFAULT_API)

    download = api_download(url=capi_url, type='get', headers=headers, data=None, json_data=False, return_json=False, allow_redirects=False)
    data = download['data']
    code = download['code']

    if not code or not code == 200:
        login_result = api_login()

        if not login_result['result']:
            return False

    try:
        profile_settings = load_profile(profile_id=1)
        profile_settings['last_login_success'] = 1
        profile_settings['last_login_time'] = int(time.time())
        save_profile(profile_id=1, profile=profile_settings)
    except:
        pass

    return True

def api_list_watchlist():
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

    try:
        profile_settings['session_token'] = data['token']
        save_profile(profile_id=1, profile=profile_settings)
    except:
        pass

    return { 'code': code, 'data': data, 'result': True }

def api_play_url(type, channel=None, id=None, video_data=None, from_beginning=0, pvr=0):
    playdata = {'path': '', 'license': '', 'info': '', 'alt_path': '', 'alt_license': ''}

    if not api_get_session():
        return playdata

    alt_path = ''
    alt_license = ''

    from_beginning = int(from_beginning)
    pvr = int(pvr)
    profile_settings = load_profile(profile_id=1)

    info = []

    headers = {'Authorization': 'Bearer ' + profile_settings['session_token']}

    if type == 'channel':
        info_url = '{api_url}/assets/{channel}'.format(api_url=CONST_DEFAULT_API, channel=channel)
    else:
        info_url = '{api_url}/assets/{id}'.format(api_url=CONST_DEFAULT_API, id=id)

    play_url = info_url + '/play'
    playfrombeginning = False
    
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

            download = api_download(url=play_url2, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
            data = download['data']
            code = download['code']

            if code and code == 200 and data and check_key(data, 'url'):
                if check_key(data, 'drm') and check_key(data['drm'], 'licenseUrl'):
                    alt_license = data['drm']['licenseUrl']

                alt_path = data['url']

    if not playfrombeginning:
        download = api_download(url=play_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'url'):
        return playdata

    if check_key(data, 'drm') and check_key(data['drm'], 'licenseUrl'):
        license = data['drm']['licenseUrl']

    path = data['url']

    playdata = {'path': path, 'license': license, 'info': info, 'alt_path': alt_path, 'alt_license': alt_license}

    return playdata

def api_remove_from_watchlist():
    return None

def api_search():
    return None

def api_vod_download():
    return None

def api_vod_season(series, id):
    if not api_get_session():
        return None

    season = []
    episodes = []
    return season

def api_vod_seasons(type, id):
    if not api_get_session():
        return None

    seasons = []
    return {'type': 'seasons', 'seasons': seasons}

def api_vod_subscription():
    return None

def api_watchlist_listing():
    return None