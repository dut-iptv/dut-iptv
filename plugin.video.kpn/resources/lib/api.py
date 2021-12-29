import _strptime
import base64, datetime, os, random, string, time, xbmc

from collections import OrderedDict
from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE, DEFAULT_USER_AGENT, DEFAULT_BROWSER_NAME, DEFAULT_BROWSER_VERSION, DEFAULT_OS_NAME, DEFAULT_OS_VERSION
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, get_credentials, encode32, is_file_older_than_x_days, is_file_older_than_x_minutes, load_file, load_profile, load_prefs, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import api_download
from resources.lib.constants import CONST_BASE_HEADERS, CONST_URLS, CONST_IMAGES
from urllib.parse import parse_qs, urlparse, quote_plus

#Included from base.l7.plugin
#api_clean_after_playback
#api_get_info

#Included from base.l8.menu
#api_add_to_watchlist
#api_get_profiles
#api_list_watchlist
#api_login
#api_play_url
#api_remove_from_watchlist
#api_search
#api_set_profile
#api_vod_download
#api_vod_season
#api_vod_seasons
#api_watchlist_listing

def api_add_to_watchlist(id, series='', season='', program_type='', type='watchlist'):
    return None

def api_clean_after_playback(stoptime):
    pass

def api_get_info(id, channel=''):
    profile_settings = load_profile(profile_id=1)

    info = {}
    militime = int(time.time() * 1000)
    program_id = None

    program_url = '{api_url}/TRAY/SEARCH/PROGRAM?maxResults=1&filter_airingEndTime=now&filter_channelIds={channel}'.format(api_url=CONST_URLS['api'], channel=id)

    download = api_download(url=program_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if code and code == 200 and data and check_key(data, 'resultCode') and data['resultCode'] == 'OK' and check_key(data, 'resultObj') and check_key(data['resultObj'], 'containers'):
        for row in data['resultObj']['containers']:
            program_id = row['id']

    if not program_id:
        return info

    info_url = '{api_url}/CONTENT/DETAIL/PROGRAM/{id}'.format(api_url=CONST_URLS['api'], id=program_id)
    download = api_download(url=info_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK' or not check_key(data, 'resultObj') or not check_key(data['resultObj'], 'containers'):
        return info

    info = data

    playdata = {'title': '', 'channel': channel, 'info': info}

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

    if playdata['info'] and check_key(playdata['info'], 'resultObj'):
        for row in playdata['info']['resultObj']['containers']:
            if check_key(row, 'metadata'):
                if check_key(row['metadata'], 'airingStartTime') and check_key(row['metadata'], 'airingEndTime'):
                    startT = datetime.datetime.fromtimestamp(int(int(row['metadata']['airingStartTime']) // 1000))
                    startT = convert_datetime_timezone(startT, "UTC", "UTC")
                    endT = datetime.datetime.fromtimestamp(int(int(row['metadata']['airingEndTime']) // 1000))
                    endT = convert_datetime_timezone(endT, "UTC", "UTC")

                    info['duration'] = int((endT - startT).total_seconds())

                    if xbmc.getLanguage(xbmc.ISO_639_1) == 'nl':
                        info['label1'] = '{weekday} {day} {month} {yearhourminute} '.format(weekday=date_to_nl_dag(startT), day=startT.strftime("%d"), month=date_to_nl_maand(startT), yearhourminute=startT.strftime("%Y %H:%M"))
                    else:
                        info['label1'] = startT.strftime("%A %d %B %Y %H:%M ").capitalize()

                    info['label1'] += " - "

                    write_file(file='stream_start', data=int(int(row['metadata']['airingStartTime']) // 1000), isJSON=False)
                    write_file(file='stream_end', data=int(int(row['metadata']['airingEndTime']) // 1000), isJSON=False)

                if check_key(playdata, 'title') and len(str(playdata['title'])) > 0:
                    info['label1'] += playdata['title']

                    if len(str(info['label2'])) > 0:
                        info['label2'] += " - "

                    info['label2'] += playdata['title']

                if check_key(row['metadata'], 'title') and len(str(row['metadata']['title'])) > 0:
                    info['label1'] += row['metadata']['title']

                    if len(str(info['label2'])) > 0:
                        info['label2'] += " - "

                    info['label2'] += row['metadata']['title']

                if check_key(row['metadata'], 'longDescription'):
                    info['description'] = row['metadata']['longDescription']

                if check_key(row['metadata'], 'pictureUrl'):
                    info['image'] = "{image_url}/epg/{image}/1920x1080.jpg?blurred=false".format(image_url=CONST_URLS['image'], image=row['metadata']['pictureUrl'])
                    info['image_large'] = "{image_url}/epg/{image}/1920x1080.jpg?blurred=false".format(image_url=CONST_URLS['image'], image=row['metadata']['pictureUrl'])

                if check_key(row['metadata'], 'actors'):
                    for castmember in row['metadata']['actors']:
                        info['cast'].append(castmember)

                if check_key(row['metadata'], 'directors'):
                    for directormember in row['metadata']['directors']:
                        info['director'].append(directormember)

                if check_key(row['metadata'], 'authors'):
                    for writermember in row['metadata']['authors']:
                        info['writer'].append(writermember)

                if check_key(row['metadata'], 'genres'):
                    for genre in row['metadata']['genres']:
                        info['genres'].append(genre)

                if check_key(row['metadata'], 'duration'):
                    info['duration'] = row['metadata']['duration']

                epcode = ''

                if check_key(row['metadata'], 'season'):
                    epcode += 'S' + str(row['metadata']['season'])

                if check_key(row['metadata'], 'episodeNumber'):
                    epcode += 'E' + str(row['metadata']['episodeNumber'])

                if check_key(row['metadata'], 'episodeTitle'):
                    if len(str(info['label2'])) > 0:
                        info['label2'] += " - "

                    info['label2'] += str(row['metadata']['episodeTitle'])

                    if len(epcode) > 0:
                        info['label2'] += " (" + epcode + ")"

                if check_key(row, 'channel'):
                    if check_key(row['channel'], 'channelName'):
                        if len(str(info['label2'])) > 0:
                            info['label2'] += " - "

                        info['label2'] += str(row['channel']['channelName'])

    return info

def api_get_session(force=0, return_data=False):
    force = int(force)
    profile_settings = load_profile(profile_id=1)

    devices_url = '{api_url}/USER/DEVICES'.format(api_url=CONST_URLS['api'])

    download = api_download(url=devices_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK':
        login_result = api_login()

        if not login_result['result']:
            if return_data == True:
                return {'result': False, 'data': login_result['data'], 'code': login_result['code']}
                
            return False

    profile_settings = load_profile(profile_id=1)
    profile_settings['last_login_success'] = 1
    profile_settings['last_login_time'] = int(time.time())
    save_profile(profile_id=1, profile=profile_settings)

    if return_data == True:
        return {'result': True, 'data': data, 'code': code}

    return True

def api_get_profiles():
    return None

def api_list_watchlist(type='watchlist'):
    return None

def api_login():
    creds = get_credentials()
    username = creds['username']
    password = creds['password']

    try:
        os.remove(os.path.join(ADDON_PROFILE, 'stream_cookies'))
    except:
        pass

    profile_settings = load_profile(profile_id=1)

    if not profile_settings or not check_key(profile_settings, 'devicekey') or len(profile_settings['devicekey']) == 0:
        devicekey = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(64))
        profile_settings['devicekey'] = devicekey
        save_profile(profile_id=1, profile=profile_settings)

    session_url = '{api_url}/USER/SESSIONS/'.format(api_url=CONST_URLS['api'])

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

def api_play_url(type, channel=None, id=None, video_data=None, from_beginning=0, pvr=0, change_audio=0):
    playdata = {'path': '', 'license': '', 'token': '', 'type': '', 'info': '', 'properties': {}}

    if not api_get_session():
        return playdata

    from_beginning = int(from_beginning)
    pvr = int(pvr)
    change_audio = int(change_audio)
    
    profile_settings = load_profile(profile_id=1)

    license = ''
    asset_id = ''
    militime = int(time.time() * 1000)
    typestr = 'PROGRAM'
    properties = {}
    info = {}
    program_id = None

    if type == 'channel':
        play_url = '{api_url}/CONTENT/VIDEOURL/LIVE/{channel}/{id}/?deviceId={device_key}&profile=G02&time={time}'.format(api_url=CONST_URLS['api'], channel=channel, id=id, device_key=profile_settings['devicekey'], time=militime)

        if not pvr == 1:
            program_url = '{api_url}/TRAY/SEARCH/PROGRAM?maxResults=1&filter_airingEndTime=now&filter_channelIds={channel}'.format(api_url=CONST_URLS['api'], channel=channel)

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

        program_url = '{api_url}/CONTENT/USERDATA/{type}/{id}'.format(api_url=CONST_URLS['api'], type=typestr, id=id)
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
                            asset_id = str(asset['assetId'])
                            break
                    else:
                        if check_key(asset, 'videoType') and check_key(asset, 'assetType') and asset['videoType'] == 'SD_DASH_PR' and asset['assetType'] == 'MASTER':
                            if check_key(asset, 'rights') and asset['rights'] == 'buy':
                                return playdata

                            asset_id = str(asset['assetId'])
                            break

        if len(str(asset_id)) == 0:
            return playdata

        play_url = '{api_url}/CONTENT/VIDEOURL/{type}/{id}/{asset_id}/?deviceId={device_key}&profile=G02&time={time}'.format(api_url=CONST_URLS['api'], type=typestr, id=id, asset_id=asset_id, device_key=profile_settings['devicekey'], time=militime)

    if program_id and not pvr == 1:
        info_url = '{api_url}/CONTENT/DETAIL/{type}/{id}'.format(api_url=CONST_URLS['api'], type=typestr, id=program_id)
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

    if not len(str(token)) > 0:
        return playdata

    if type == 'channel':
        path = path.split("&", 1)[0]
    else:
        path = path.split("&min_bitrate", 1)[0]

    mpd = ''

    if change_audio == 1:
        download = api_download(url=path, type='get', headers=None, data=None, json_data=False, return_json=False)
        data = download['data']
        code = download['code']

        if code and code == 200:
            mpd = data

    playdata = {'path': path, 'mpd': mpd, 'license': license, 'token': token, 'type': typestr, 'info': info, 'properties': properties}

    return playdata

def api_remove_from_watchlist(id, type='watchlist'):
    return None

def api_search(query):
    return None
    
def api_set_profile(id=''):
    return None    

def api_vod_download():
    return None

def api_vod_season(series, id, use_cache=True):
    type = "vod_season_{id}".format(id=id)
    type = encode32(type)

    file = os.path.join("cache", "{type}.json".format(type=type))

    program_url = '{api_url}/CONTENT/DETAIL/BUNDLE/{id}'.format(api_url=CONST_URLS['api'], id=id)
    cache = 0

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=0.5) and use_cache == True:
        data = load_file(file=file, isJSON=True)
        cache = 1
    else:
        download = api_download(url=program_url, type='get', headers=None, data=None, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and check_key(data, 'resultCode') and data['resultCode'] == 'OK' and check_key(data, 'resultObj') and check_key(data['resultObj'], 'containers'):
            write_file(file=file, data=data, isJSON=True)

    return {'data': data, 'cache': cache}

def api_vod_seasons(type, id, use_cache=True):
    type = "vod_seasons_{id}".format(id=id)
    type = encode32(type)

    file = os.path.join("cache", "{type}.json".format(type=type))

    program_url = '{api_url}/CONTENT/DETAIL/GROUP_OF_BUNDLES/{id}'.format(api_url=CONST_URLS['api'], id=id)
    cache = 0

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=0.5) and use_cache == True:
        data = load_file(file=file, isJSON=True)
        cache = 1
    else:
        download = api_download(url=program_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data and check_key(data, 'resultCode') and data['resultCode'] == 'OK' and check_key(data, 'resultObj') and check_key(data['resultObj'], 'containers'):
            write_file(file=file, data=data, isJSON=True)

    return {'data': data, 'cache': cache}

def api_vod_subscription():
    file = "cache" + os.sep + "vod_subscription.json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=1):
        load_file(file=file, isJSON=True)
    else:
        if not api_get_session():
            return None

        subscription = []

        series_url = '{api_url}/TRAY/SEARCH/VOD?from=1&to=9999&filter_contentType=GROUP_OF_BUNDLES,VOD&filter_contentSubtype=SERIES,VOD&filter_contentTypeExtended=VOD&filter_excludedGenres=erotiek&filter_technicalPackages=10078,10081,10258,10255&dfilter_packages=matchSubscription&orderBy=activationDate&sortOrder=desc'.format(api_url=CONST_URLS['api'])
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