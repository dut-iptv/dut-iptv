import _strptime
import base64, datetime, os, pyjwt, random, string, time, xbmc

from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE, DEFAULT_USER_AGENT, DEFAULT_BROWSER_NAME, DEFAULT_BROWSER_VERSION, DEFAULT_OS_NAME, DEFAULT_OS_VERSION
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, get_credentials, is_file_older_than_x_days, is_file_older_than_x_minutes, load_file, load_profile, load_prefs, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import api_download
from resources.lib.constants import CONST_BASE_HEADERS, CONST_BASE_URL, CONST_DEFAULT_API, CONST_IMAGE_URL
from urllib.parse import parse_qs, urlparse, quote_plus

def api_add_to_watchlist():
    return None

def api_get_info(id, channel=''):
    return {}

def api_get_session(force=0):
    force = int(force)
    profile_settings = load_profile(profile_id=1)
    subscriptionToken = None

    try:
        saved_token = profile_settings['subscriptionToken']

        if saved_token is not None:
            cached_token_expiration_time = datetime.fromtimestamp(pyjwt.decode(saved_token, verify=False)['exp'])

            token_validity_time_remaining = cached_token_expiration_time - datetime.now()

            if token_validity_time_remaining.total_seconds() > 60 * 60 * 24:
                subscriptionToken = saved_token
    except:
        pass

    if subscriptionToken is None:
        login_result = api_login()

        if not login_result['result']:
            return False

    profile_settings = load_profile(profile_id=1)
    profile_settings['last_login_success'] = 1
    profile_settings['last_login_time'] = int(time.time())
    save_profile(profile_id=1, profile=profile_settings)

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

    session_url = '{api_url}/subscriber/authenticate/by-password'.format(api_url=CONST_DEFAULT_API)

    session_post_data = {
        "DeviceType": 16,
        "DistributionChannel": '871435e3-2d31-4d4f-9004-96c6a8011656',
        "Language": 'en-GB',
        "Login": username,
        "Password": password
    }

    headers = {
        "Content-Type": "application/json",
        "apikey": "fCUCjWrKPu9ylJwRAv8BpGLEgiAuThx7",
        "CD-DeviceType": '16',
        "CD-DistributionChannel": '871435e3-2d31-4d4f-9004-96c6a8011656',
        'User-Agent': 'RaceControl'
    }

    download = api_download(url=session_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'SessionId') or not data['data']['subscriptionStatus'] == 'active':
        return { 'code': code, 'data': data, 'result': False }

    profile_settings = load_profile(profile_id=1)
    profile_settings['subscriptionToken'] = data["data"]["subscriptionToken"]
    save_profile(profile_id=1, profile=profile_settings)

    return { 'code': code, 'data': data, 'result': True }

def api_play_url(type, channel=None, id=None, video_data=None, from_beginning=0, pvr=0):
    playdata = {'path': '', 'license': '', 'token': '', 'type': '', 'info': '', 'properties': {}}

    if not api_get_session():
        return playdata

    from_beginning = int(from_beginning)
    pvr = int(pvr)
    profile_settings = load_profile(profile_id=1)

    license = ''
    asset_id = ''
    militime = int(time.time() * 1000)
    typestr = 'PROGRAM'
    properties = {}
    info = {}
    program_id = None
        
    if 'channelId=' in id:
        play_url = '{base_url}/1.0/R/ENG/WEB_HLS/ALL/{id}'.format(base_url=CONST_BASE_URL, id=id)
        qs = parse_qs(play_url)
        info_url = '{base_url}/2.0/R/ENG/WEB_DASH/ALL/CONTENT/VIDEO/{id}/F1_TV_Pro_Annual/2?contentId={id}'.format(base_url=CONST_BASE_URL, id=qs['contentId'][0])
    else:
        play_url = '{base_url}/1.0/R/ENG/WEB_HLS/ALL/CONTENT/PLAY?contentId={id}'.format(base_url=CONST_BASE_URL, id=id)
        info_url = '{base_url}/2.0/R/ENG/WEB_DASH/ALL/CONTENT/VIDEO/{id}/F1_TV_Pro_Annual/2?contentId={id}'.format(base_url=CONST_BASE_URL, id=id)

    download = api_download(url=info_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK' or not check_key(data, 'resultObj') or not check_key(data['resultObj'], 'containers'):
        return playdata

    info = data
    
    headers = {
        'ascendontoken': profile_settings['subscriptionToken']
    }

    download = api_download(url=play_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK' or not check_key(data, 'resultObj') or not check_key(data['resultObj'], 'entitlementToken') or not check_key(data['resultObj'], 'url'):
        return playdata

    path = data['resultObj']['url']
    token = data['resultObj']['entitlementToken']

    if not len(str(token)) > 0:
        return playdata

    playdata = {'path': path, 'license': license, 'token': token, 'type': typestr, 'info': info, 'properties': properties}

    return playdata

def api_remove_from_watchlist():
    return None

def api_search(query):
    return None

def api_vod_download(type, start=0):
    info_url = '{base_url}/2.0/R/ENG/WEB_DASH/ALL/PAGE/{id}/F1_TV_Pro_Annual/2'.format(base_url=CONST_BASE_URL, id=type)
    download = api_download(url=info_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK' or not check_key(data, 'resultObj') or not check_key(data['resultObj'], 'containers'):
        return None

    items = []

    for row in data['resultObj']['containers']:
        for row2 in row['retrieveItems']['resultObj']['containers']:
                if row2['metadata']['contentSubtype'] == 'LIVE':
                    item = {}
                    item['id'] = row2['id']
                    item['title'] = row2['metadata']['title']
                    item['description'] = row2['metadata']['longDescription']
                    item['duration'] = row2['metadata']['duration']
                    item['type'] = 'event'
                    item['icon'] = '{image_url}/{image}?w=1920&h=1080&q=HI&o=L'.format(image_url=CONST_IMAGE_URL, image=row2['metadata']['pictureUrl'])
                    item['start'] = ''

                    items.append(item)

    return items

def api_vod_season(series, id):
    if not api_get_session():
        return playdata
        
    season = []
        
    info_url = '{base_url}/2.0/R/ENG/WEB_DASH/ALL/CONTENT/VIDEO/{id}/F1_TV_Pro_Annual/2?contentId={id}'.format(base_url=CONST_BASE_URL, id=id)
    download = api_download(url=info_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK' or not check_key(data, 'resultObj') or not check_key(data['resultObj'], 'containers'):
        return None

    for row in data['resultObj']['containers']:
        duration = 0
        ep_id = ''
        desc = ''
        image = ''
        label = ''
        seasonno = ''
        episodeno = ''
        start = ''

        if check_key(row['metadata'], 'title'):
            label = 'Main Feed'

        if check_key(row['metadata'], 'duration'):
            duration = row['metadata']['duration']

        if check_key(row, 'id'):
            ep_id = row['id']

        if check_key(row['metadata'], 'longDescription'):
            desc = row['metadata']['longDescription']

        if check_key(row['metadata'], 'pictureUrl'):
            image = '{image_url}/{image}?w=1920&h=1080&q=HI&o=L'.format(image_url=CONST_IMAGE_URL, image=row['metadata']['pictureUrl'])
            
        if check_key(row['metadata'], 'season'):
            seasonno = row['metadata']['season']
            
        season.append({'label': label, 'id': ep_id, 'start': start, 'duration': duration, 'title': label, 'seasonNumber': seasonno, 'episodeNumber': episodeno, 'description': desc, 'image': image})
        
        for n in range(0, 100):        
            for row2 in row['metadata']['additionalStreams']:
                if not n == int(row2['racingNumber']):
                    continue
                    
                ep_id = ''
                label = ''

                if check_key(row['metadata'], 'title'):
                    if n == 0:
                        label = str(row2['title'])
                    elif (check_key(row2, 'teamName') and check_key(row2, 'driverFirstName') and check_key(row2, 'driverLastName')):
                        label = str(row2['racingNumber']) + ' ' + str(row2['driverFirstName']) + ' ' + str(row2['driverLastName']) + ' (' + str(row2['teamName']) + ')'
                    else:
                        label = str(row2['title'])
                        
                if check_key(row2, 'playbackUrl'):
                    ep_id = row2['playbackUrl']
                    
                season.append({'label': label, 'id': ep_id, 'start': start, 'duration': duration, 'title': label, 'seasonNumber': seasonno, 'episodeNumber': episodeno, 'description': desc, 'image': image})

    return season

def api_vod_seasons(type, id):
    return None

def api_vod_subscription():
    return None

def api_watchlist_listing():
    return None

def api_clean_after_playback():
    pass