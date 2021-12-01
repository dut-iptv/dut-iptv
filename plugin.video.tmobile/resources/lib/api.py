import base64, json, os, random, re, string, time, xbmc

from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, get_credentials, is_file_older_than_x_days, is_file_older_than_x_minutes, load_file, load_profile, load_prefs, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import api_download, api_get_channels
from resources.lib.constants import CONST_BASE_HEADERS, CONST_BASE_URL
from resources.lib.util import plugin_process_info
from urllib.parse import parse_qs, urlparse, quote_plus

def api_add_to_watchlist():
    return None

def api_getCookies(cookie_jar, domain):
    cookie_dict = json.loads(cookie_jar)
    found = ['%s=%s' % (name, value) for (name, value) in cookie_dict.items()]
    return '; '.join(found)

def api_get_info(id, channel=''):
    profile_settings = load_profile(profile_id=1)

    info = {}
    headers = {'Content-Type': 'application/json', 'X_CSRFToken': profile_settings['csrf_token']}
    militime = int(time.time() * 1000)

    data = api_get_channels()

    session_post_data = {
        'needChannel': '0',
        'queryChannel': {
            'channelIDs': [
                id,
            ],
            'isReturnAllMedia': '1',
        },
        'queryPlaybill': {
            'count': '1',
            'endTime': militime,
            'isFillProgram': '1',
            'offset': '0',
            'startTime': militime,
            'type': '0',
        }
    }

    channel_url = '{base_url}/VSP/V3/QueryPlaybillListStcProps?SID=queryPlaybillListStcProps3&DEVICE=PC&DID={deviceID}&from=throughMSAAccess'.format(base_url=CONST_BASE_URL, deviceID=profile_settings['devicekey'])

    download = api_download(url=channel_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'result') or not check_key(data['result'], 'retCode') or not data['result']['retCode'] == '000000000' or not check_key(data, 'channelPlaybills') or not check_key(data['channelPlaybills'][0], 'playbillLites') or not check_key(data['channelPlaybills'][0]['playbillLites'][0], 'ID'):
        return info

    id = data['channelPlaybills'][0]['playbillLites'][0]['ID']

    session_post_data = {
        'playbillID': id,
        'channelNamespace': '310303',
        'isReturnAllMedia': '1',
    }

    program_url = '{base_url}/VSP/V3/QueryPlaybill?from=throughMSAAccess'.format(base_url=CONST_BASE_URL)

    download = api_download(url=program_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'result') or not check_key(data['result'], 'retCode') or not data['result']['retCode'] == '000000000' or not check_key(data, 'playbillDetail'):
        return info
    else:
        info = data['playbillDetail']

    info = plugin_process_info({'title': '', 'channel': channel, 'info': info})

    return info

def api_get_session(force=0):
    force = int(force)
    profile_settings = load_profile(profile_id=1)

    heartbeat_url = '{base_url}/VSP/V3/OnLineHeartbeat?from=inMSAAccess'.format(base_url=CONST_BASE_URL)

    headers = {'Content-Type': 'application/json', 'X_CSRFToken': profile_settings['csrf_token']}

    session_post_data = {}

    download = api_download(url=heartbeat_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'result') or not check_key(data['result'], 'retCode') or not data['result']['retCode'] == '000000000':
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

def api_login(selected=None):
    creds = get_credentials()
    username = creds['username']
    password = creds['password']

    try:
        os.remove(ADDON_PROFILE + 'stream_cookies')
    except:
        pass

    profile_settings = load_profile(profile_id=1)
    profile_settings['csrf_token'] = ''
    profile_settings['user_filter'] = ''

    if not profile_settings or not check_key(profile_settings, 'devicekey') or len(profile_settings['devicekey']) == 0:
        devicekey = ''.join(random.choice(string.digits) for _ in range(10))
        profile_settings['devicekey'] = devicekey

    save_profile(profile_id=1, profile=profile_settings)

    login_url = '{base_url}/VSP/V3/Authenticate?from=throughMSAAccess'.format(base_url=CONST_BASE_URL)

    session_post_data = {
        "authenticateBasic": {
            'VUID': '6_7_{devicekey}'.format(devicekey=profile_settings['devicekey']),
            'clientPasswd': password,
            'isSupportWebpImgFormat': '0',
            'lang': 'nl',
            'needPosterTypes': [
                '1',
                '2',
                '3',
                '4',
                '5',
                '6',
                '7',
            ],
            'timeZone': 'Europe/Amsterdam',
            'userID': username,
            'userType': '0',
        },
        'authenticateDevice': {
            'CADeviceInfos': [
                {
                    'CADeviceID': profile_settings['devicekey'],
                    'CADeviceType': '7',
                },
            ],
            'deviceModel': '3103_PCClient',
            'physicalDeviceID': profile_settings['devicekey'],
            'terminalID': profile_settings['devicekey'],
        },
        'authenticateTolerant': {
            'areaCode': '',
            'bossID': '',
            'subnetID': '',
            'templateName': '',
            'userGroup': '',
        },
    }

    download = api_download(url=login_url, type='post', headers=None, data=session_post_data, json_data=True, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'result') or not check_key(data['result'], 'retCode') or not data['result']['retCode'] == '000000000' or not check_key(data, 'csrfToken'):
        if check_key(data, 'result') and check_key(data['result'], 'retCode') and data['result']['retCode'] == "157022007" and check_key(data, 'devices'):
            for row in data['devices']:
                if not check_key(row, 'name') and check_key(row, 'deviceModel') and check_key(row, 'status') and check_key(row, 'onlineState') and check_key(row, 'physicalDeviceID') and row['deviceModel'] == '3103_PCClient' and row['status'] == '1' and row['onlineState'] == '0':
                    profile_settings['devicekey'] = row['physicalDeviceID']
                    save_profile(profile_id=1, profile=profile_settings)

                    return api_login()

            for row in data['devices']:
                if check_key(row, 'status') and check_key(row, 'onlineState') and check_key(row, 'physicalDeviceID'):
                    if row['status'] == '1' and row['onlineState'] == '0' and (not check_key(row, 'name') or len(str(row['name'])) < 1 or 'PC' in str(row['name'])):
                        profile_settings['devicekey'] = row['physicalDeviceID']
                        save_profile(profile_id=1, profile=profile_settings)

                        return api_login()
                        
            for row in data['devices']:
                if check_key(row, 'status') and check_key(row, 'onlineState') and check_key(row, 'physicalDeviceID'):
                    if row['status'] == '1':
                        profile_settings['devicekey'] = row['physicalDeviceID']
                        save_profile(profile_id=1, profile=profile_settings)

                        return api_login()

        return { 'code': code, 'data': data, 'result': False }

    profile_settings['csrf_token'] = data['csrfToken']
    profile_settings['user_filter'] = data['userFilter']
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

    headers = {'Content-Type': 'application/json', 'X_CSRFToken': profile_settings['csrf_token']}

    mediaID = None
    info = {}
    properties = {}

    if not type or not len(str(type)) > 0:
        return playdata

    militime = int(time.time() * 1000)

    if not type == 'vod':
        if video_data:
            try:
                video_data = json.loads(video_data)
                mediaID = int(video_data['media_id']) + 1
            except:
                pass

        data = api_get_channels()

        try:
            mediaID = data[str(channel)]['assetid']
        except:
            pass

    if type == 'channel' and channel:
        if not pvr == 1 or settings.getBool(key='ask_start_from_beginning') or from_beginning == 1:
            session_post_data = {
                'needChannel': '0',
                'queryChannel': {
                    'channelIDs': [
                        channel,
                    ],
                    'isReturnAllMedia': '1',
                },
                'queryPlaybill': {
                    'count': '1',
                    'endTime': militime,
                    'isFillProgram': '1',
                    'offset': '0',
                    'startTime': militime,
                    'type': '0',
                }
            }

            channel_url = '{base_url}/VSP/V3/QueryPlaybillListStcProps?SID=queryPlaybillListStcProps3&DEVICE=PC&DID={deviceID}&from=throughMSAAccess'.format(base_url=CONST_BASE_URL, deviceID=profile_settings['devicekey'])

            download = api_download(url=channel_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
            data = download['data']
            code = download['code']

            if not code or not code == 200 or not data or not check_key(data, 'result') or not check_key(data['result'], 'retCode') or not data['result']['retCode'] == '000000000' or not check_key(data, 'channelPlaybills') or not check_key(data['channelPlaybills'][0], 'playbillLites') or not check_key(data['channelPlaybills'][0]['playbillLites'][0], 'ID'):
                return playdata

            id = data['channelPlaybills'][0]['playbillLites'][0]['ID']

            session_post_data = {
                'playbillID': id,
                'channelNamespace': '310303',
                'isReturnAllMedia': '1',
            }

            program_url = '{base_url}/VSP/V3/QueryPlaybill?from=throughMSAAccess'.format(base_url=CONST_BASE_URL)

            download = api_download(url=program_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
            data = download['data']
            code = download['code']

            if not code or not code == 200 or not data or not check_key(data, 'result') or not check_key(data['result'], 'retCode') or not data['result']['retCode'] == '000000000' or not check_key(data, 'playbillDetail'):
                info = {}
            else:
                info = data['playbillDetail']

        session_post_data = {
            "businessType": "BTV",
            "channelID": channel,
            "checkLock": {
                "checkType": "0",
            },
            "isHTTPS": "1",
            "isReturnProduct": "1",
            "mediaID": mediaID,
        }
    elif type == 'program' and id:
        if not pvr == 1:
            session_post_data = {
                'playbillID': id,
                'channelNamespace': '310303',
                'isReturnAllMedia': '1',
            }

            program_url = '{base_url}/VSP/V3/QueryPlaybill?from=throughMSAAccess'.format(base_url=CONST_BASE_URL)

            download = api_download(url=program_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
            data = download['data']
            code = download['code']

            if not code or not code == 200 or not data or not check_key(data, 'result') or not check_key(data['result'], 'retCode') or not data['result']['retCode'] == '000000000' or not check_key(data, 'playbillDetail'):
                info = {}
            else:
                info = data['playbillDetail']

        session_post_data = {
            "businessType": "CUTV",
            "channelID": channel,
            "checkLock": {
                "checkType": "0",
            },
            "isHTTPS": "1",
            "isReturnProduct": "1",
            "mediaID": mediaID,
            "playbillID": id,
        }
    elif type == 'vod' and id:
        session_post_data = {
            'VODID': id
        }

        program_url = '{base_url}/VSP/V3/QueryVOD?from=throughMSAAccess'.format(base_url=CONST_BASE_URL)

        download = api_download(url=program_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'result') or not check_key(data['result'], 'retCode') or not data['result']['retCode'] == '000000000' or not check_key(data, 'VODDetail') or not check_key(data['VODDetail'], 'VODType'):
            return playdata

        info = data['VODDetail']

        session_post_data = {
            "VODID": id,
            "checkLock": {
                "checkType": "0",
            },
            "isHTTPS": "1",
            "isReturnProduct": "1",
            "mediaID": '',
        }

        if not check_key(info, 'mediaFiles') or not check_key(info['mediaFiles'][0], 'ID'):
            return playdata

        if check_key(info, 'series') and check_key(info['series'][0], 'VODID'):
            session_post_data["seriesID"] = info['series'][0]['VODID']

        session_post_data["mediaID"] = info['mediaFiles'][0]['ID']

    if not len(str(session_post_data["mediaID"])) > 0:
        return playdata

    if type == 'vod':
        play_url_path = '{base_url}/VSP/V3/PlayVOD?from=throughMSAAccess'.format(base_url=CONST_BASE_URL)
    else:
        play_url_path = '{base_url}/VSP/V3/PlayChannel?from=throughMSAAccess'.format(base_url=CONST_BASE_URL)

    download = api_download(url=play_url_path, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'result') or not check_key(data['result'], 'retCode') or not data['result']['retCode'] == '000000000' or not check_key(data, 'playURL'):
        return playdata

    path = data['playURL']

    if check_key(data, 'authorizeResult'):
        profile_settings = load_profile(profile_id=1)

        data['authorizeResult']['cookie'] = api_getCookies(load_file('stream_cookies'), '')
        license = data['authorizeResult']

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

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        profile_settings = load_profile(profile_id=1)

        headers = {'Content-Type': 'application/json', 'X_CSRFToken': profile_settings['csrf_token']}

        session_post_data = {
            'VODID': str(id),
            'offset': '0',
            'count': '35',
        }

        seasons_url = '{base_url}/VSP/V3/QueryEpisodeList?from=throughMSAAccess'.format(base_url=CONST_BASE_URL)

        download = api_download(url=seasons_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and check_key(data, 'result') and check_key(data['result'], 'retCode') and data['result']['retCode'] == '000000000' and check_key(data, 'episodes'):
            write_file(file=file, data=data, isJSON=True)

    if not data or not check_key(data, 'episodes'):
        return None

    for row in data['episodes']:
        if check_key(row, 'VOD') and check_key(row['VOD'], 'ID') and check_key(row['VOD'], 'name') and check_key(row, 'sitcomNO'):
            image = ''
            duration = 0

            if not check_key(row['VOD'], 'mediaFiles') or not check_key(row['VOD']['mediaFiles'][0], 'ID'):
                continue

            if check_key(row['VOD']['mediaFiles'][0], 'elapseTime'):
                duration = row['VOD']['mediaFiles'][0]['elapseTime']

            if check_key(row['VOD'], 'picture') and check_key(row['VOD']['picture'], 'posters'):
                image = row['VOD']['picture']['posters'][0]

            label = '{episode} - {title}'.format(episode=row['sitcomNO'], title=row['VOD']['name'])

            season.append({'label': label, 'id': row['VOD']['ID'], 'media_id': row['VOD']['mediaFiles'][0]['ID'], 'duration': duration, 'title': row['VOD']['name'], 'episodeNumber': row['sitcomNO'], 'description': '', 'image': image})

    return season

def api_vod_seasons(type, id):
    if not api_get_session():
        return None

    seasons = []

    type = "vod_seasons_" + str(id)

    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        profile_settings = load_profile(profile_id=1)

        headers = {'Content-Type': 'application/json', 'X_CSRFToken': profile_settings['csrf_token']}

        session_post_data = {
            'VODID': str(id),
            'offset': '0',
            'count': '50',
        }

        seasons_url = '{base_url}/VSP/V3/QueryEpisodeList?from=throughMSAAccess'.format(base_url=CONST_BASE_URL)

        download = api_download(url=seasons_url, type='post', headers=headers, data=session_post_data, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and check_key(data, 'result') and check_key(data['result'], 'retCode') and data['result']['retCode'] == '000000000' and check_key(data, 'episodes'):
            write_file(file=file, data=data, isJSON=True)

    if not data or not check_key(data, 'episodes'):
        return None

    for row in data['episodes']:
        if check_key(row, 'VOD') and check_key(row['VOD'], 'ID') and check_key(row, 'sitcomNO'):
            image = ''

            if check_key(row['VOD'], 'picture') and check_key(row['VOD']['picture'], 'posters'):
                image = row['VOD']['picture']['posters'][0]

            seasons.append({'id': row['VOD']['ID'], 'seriesNumber': row['sitcomNO'], 'description': '', 'image': image})

    return {'type': 'seasons', 'seasons': seasons}

def api_vod_subscription():
    return None

def api_watchlist_listing():
    return None

def api_clean_after_playback():
    pass