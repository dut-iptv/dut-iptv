import base64, os, random, string, time, xbmc

from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE, DEFAULT_USER_AGENT, DEFAULT_BROWSER_NAME, DEFAULT_BROWSER_VERSION, DEFAULT_OS_NAME, DEFAULT_OS_VERSION
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, find_highest_bandwidth, get_credentials, is_file_older_than_x_days, is_file_older_than_x_minutes, load_file, load_profile, load_prefs, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import api_download
from resources.lib.constants import CONST_BASE_HEADERS, CONST_DEFAULT_API, CONST_IMAGE_URL

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

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
    #elif force == 1 and (not check_key(profile_settings, 'last_login_time') or not profile_settings['last_login_success'] == 1):
    #    return False

    devices_url = '{api_url}/USER/DEVICES'.format(api_url=CONST_DEFAULT_API)

    download = api_download(url=devices_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK':
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

    if not profile_settings or not check_key(profile_settings, 'devicekey') or len(profile_settings['devicekey']) == 0:
        devicekey = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(64))
        profile_settings['devicekey'] = devicekey
        save_profile(profile_id=1, profile=profile_settings)

    session_url = '{api_url}/USER/SESSIONS/'.format(api_url=CONST_DEFAULT_API)

    email_or_pin = settings.getBool(key='email_instead_of_customer')

    if email_or_pin:
        session_post_data = {
            "credentialsExtAuth": {
                'credentials': {
                    'loginType': 'UsernamePassword',
                    'username': username,
                    'password': password,
                    'appId': 'KPN',
                },
                'remember': 'Y',
                'deviceInfo': {
                    'deviceId': profile_settings['devicekey'],
                    'deviceIdType': 'DEVICEID',
                    'deviceType' : 'PCTV',
                    'deviceVendor' : DEFAULT_BROWSER_NAME,
                    'deviceModel' : DEFAULT_BROWSER_VERSION,
                    'deviceFirmVersion' : DEFAULT_OS_NAME,
                    'appVersion' : DEFAULT_OS_VERSION
                }
            },
        }
    else:
        session_post_data = {
            "credentialsStdAuth": {
                'username': username,
                'password': password,
                'remember': 'Y',
                'deviceRegistrationData': {
                    'deviceId': profile_settings['devicekey'],
                    'accountDeviceIdType': 'DEVICEID',
                    'deviceType' : 'PCTV',
                    'vendor' : DEFAULT_BROWSER_NAME,
                    'model' : DEFAULT_BROWSER_VERSION,
                    'deviceFirmVersion' : DEFAULT_OS_NAME,
                    'appVersion' : DEFAULT_OS_VERSION
                }
            },
        }

    download = api_download(url=session_url, type='post', headers=None, data=session_post_data, json_data=True, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK':
        return { 'code': code, 'data': data, 'result': False }

    return { 'code': code, 'data': data, 'result': True }

def api_play_url(type, channel=None, id=None, video_data=None, from_beginning=0, pvr=0):
    playdata = {'path': '', 'license': '', 'token': '', 'type': '', 'info': '', 'alt_path': '', 'alt_license': ''}

    if not api_get_session():
        return playdata

    from_beginning = int(from_beginning)
    pvr = int(pvr)
    profile_settings = load_profile(profile_id=1)

    alt_path = ''
    alt_license = ''
    license = ''
    asset_id = ''
    militime = int(time.time() * 1000)
    typestr = 'PROGRAM'
    info = []
    program_id = None

    if type == 'channel':
        play_url = '{api_url}/CONTENT/VIDEOURL/LIVE/{channel}/{id}/?deviceId={device_key}&profile=G02&time={time}'.format(api_url=CONST_DEFAULT_API, channel=channel, id=id, device_key=profile_settings['devicekey'], time=militime)

        if not pvr == 1:
            program_url = '{api_url}/TRAY/SEARCH/PROGRAM?maxResults=1&filter_airingEndTime=now&filter_channelIds={channel}'.format(api_url=CONST_DEFAULT_API, channel=channel)

            download = api_download(url=program_url, type='get', headers=None, data=None, json_data=False, return_json=True)
            data = download['data']
            code = download['code']

            if code and code == 200 and data and check_key(data, 'resultCode') and data['resultCode'] == 'OK' and check_key(data, 'resultObj') and check_key(data['resultObj'], 'containers'):
                for row in data['resultObj']['containers']:
                    program_id = row['id']
    else:
        if type == 'program':
            typestr = "PROGRAM"
        else:
            typestr = "VOD"

        program_id = id

        program_url = '{api_url}/CONTENT/USERDATA/{type}/{id}'.format(api_url=CONST_DEFAULT_API, type=typestr, id=id)
        download = api_download(url=program_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK' or not check_key(data, 'resultObj') or not check_key(data['resultObj'], 'containers'):
            return playdata

        for row in data['resultObj']['containers']:
            if check_key(row, 'entitlement') and check_key(row['entitlement'], 'assets'):
                for asset in row['entitlement']['assets']:
                    if type == 'program':
                        if check_key(asset, 'videoType') and check_key(asset, 'programType') and asset['videoType'] == 'SD_DASH_PR' and asset['programType'] == 'CUTV':
                            asset_id = unicode(asset['assetId'])
                            break
                    else:
                        if check_key(asset, 'videoType') and check_key(asset, 'assetType') and asset['videoType'] == 'SD_DASH_PR' and asset['assetType'] == 'MASTER':
                            if check_key(asset, 'rights') and asset['rights'] == 'buy':
                                return playdata

                            asset_id = unicode(asset['assetId'])
                            break

        if len(unicode(asset_id)) == 0:
            return playdata

        play_url = '{api_url}/CONTENT/VIDEOURL/{type}/{id}/{asset_id}/?deviceId={device_key}&profile=G02&time={time}'.format(api_url=CONST_DEFAULT_API, type=typestr, id=id, asset_id=asset_id, device_key=profile_settings['devicekey'], time=militime)

    if program_id and not pvr == 1:
        info_url = '{api_url}/CONTENT/DETAIL/{type}/{id}'.format(api_url=CONST_DEFAULT_API, type=typestr, id=program_id)
        download = api_download(url=info_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK' or not check_key(data, 'resultObj') or not check_key(data['resultObj'], 'containers'):
            return playdata

        info = data

    download = api_download(url=play_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK' or not check_key(data, 'resultObj') or not check_key(data['resultObj'], 'token') or not check_key(data['resultObj'], 'src') or not check_key(data['resultObj']['src'], 'sources') or not check_key(data['resultObj']['src']['sources'], 'src'):
        return playdata

    if check_key(data['resultObj']['src']['sources'], 'contentProtection') and check_key(data['resultObj']['src']['sources']['contentProtection'], 'widevine') and check_key(data['resultObj']['src']['sources']['contentProtection']['widevine'], 'licenseAcquisitionURL'):
        license = data['resultObj']['src']['sources']['contentProtection']['widevine']['licenseAcquisitionURL']

    path = data['resultObj']['src']['sources']['src']
    token = data['resultObj']['token']

    if not len(unicode(token)) > 0:
        return playdata

    if type == 'channel':
        path = path.split("&", 1)[0]
    else:
        path = path.split("&min_bitrate", 1)[0]

    playdata = {'path': path, 'license': license, 'token': token, 'type': typestr, 'info': info, 'alt_path': alt_path, 'alt_license': alt_license}

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

    program_url = '{api_url}/CONTENT/DETAIL/BUNDLE/{id}'.format(api_url=CONST_DEFAULT_API, id=id)

    type = "vod_season_" + unicode(id)
    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = unicode(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=program_url, type='get', headers=None, data=None, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and check_key(data, 'resultCode') and data['resultCode'] == 'OK' and check_key(data, 'resultObj') and check_key(data['resultObj'], 'containers'):
            write_file(file=file, data=data, isJSON=True)

    if not data or not check_key(data['resultObj'], 'containers'):
        return None

    for row in data['resultObj']['containers']:
        for currow in row['containers']:
            if check_key(currow, 'metadata') and check_key(currow['metadata'], 'season') and unicode(currow['metadata']['contentSubtype']) == 'EPISODE' and not unicode(currow['metadata']['episodeNumber']) in episodes:
                asset_id = ''

                for asset in currow['assets']:
                    if check_key(asset, 'videoType') and asset['videoType'] == 'SD_DASH_PR' and check_key(asset, 'assetType') and asset['assetType'] == 'MASTER':
                        asset_id = unicode(asset['assetId'])
                        break

                episodes.append(unicode(currow['metadata']['episodeNumber']))

                label = '{season}.{episode} - {title}'.format(season=unicode(currow['metadata']['season']), episode=unicode(currow['metadata']['episodeNumber']), title=unicode(currow['metadata']['episodeTitle']))

                season.append({'label': label, 'id': unicode(currow['metadata']['contentId']), 'assetid': asset_id, 'duration': currow['metadata']['duration'], 'title': unicode(currow['metadata']['episodeTitle']), 'episodeNumber': '{season}.{episode}'.format(season=unicode(currow['metadata']['season']), episode=unicode(currow['metadata']['episodeNumber'])), 'description': unicode(currow['metadata']['shortDescription']), 'image': "{image_url}/vod/{image}/1920x1080.jpg?blurred=false".format(image_url=CONST_IMAGE_URL, image=unicode(currow['metadata']['pictureUrl']))})

    return season

def api_vod_seasons(type, id):
    if not api_get_session():
        return None

    seasons = []

    program_url = '{api_url}/CONTENT/DETAIL/GROUP_OF_BUNDLES/{id}'.format(api_url=CONST_DEFAULT_API, id=id)

    type = "vod_seasons_" + unicode(id)
    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = unicode(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=program_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and check_key(data, 'resultCode') and data['resultCode'] == 'OK' and check_key(data, 'resultObj') and check_key(data['resultObj'], 'containers'):
            write_file(file=file, data=data, isJSON=True)

    if not data or not check_key(data['resultObj'], 'containers'):
        return None

    for row in data['resultObj']['containers']:
        for currow in row['containers']:
            if check_key(currow, 'metadata') and check_key(currow['metadata'], 'season') and unicode(currow['metadata']['contentSubtype']) == 'SEASON':
                seasons.append({'id': unicode(currow['metadata']['contentId']), 'seriesNumber': unicode(currow['metadata']['season']), 'description': unicode(currow['metadata']['shortDescription']), 'image': "{image_url}/vod/{image}/1920x1080.jpg?blurred=false".format(image_url=CONST_IMAGE_URL, image=unicode(currow['metadata']['pictureUrl']))})

    return {'type': 'seasons', 'seasons': seasons}

def api_vod_subscription():
    file = "cache" + os.sep + "vod_subscription.json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=1):
        load_file(file=file, isJSON=True)
    else:
        if not api_get_session():
            return None

        subscription = []

        series_url = '{api_url}/TRAY/SEARCH/VOD?from=1&to=9999&filter_contentType=GROUP_OF_BUNDLES,VOD&filter_contentSubtype=SERIES,VOD&filter_contentTypeExtended=VOD&filter_excludedGenres=erotiek&filter_technicalPackages=10078,10081,10258,10255&dfilter_packages=matchSubscription&orderBy=activationDate&sortOrder=desc'.format(api_url=CONST_DEFAULT_API)
        download = api_download(url=series_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK' or not check_key(data, 'resultObj') or not check_key(data['resultObj'], 'containers'):
            return False

        for row in data['resultObj']['containers']:
            subscription.append(row['metadata']['contentId'])

        write_file(file=file, data=subscription, isJSON=True)

    return True

def api_watchlist_listing():
    return None