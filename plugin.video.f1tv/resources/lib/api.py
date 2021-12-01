import _strptime
import base64, datetime, os, pyjwt, random, re, string, time, xbmc

from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE, DEFAULT_USER_AGENT, DEFAULT_BROWSER_NAME, DEFAULT_BROWSER_VERSION, DEFAULT_OS_NAME, DEFAULT_OS_VERSION
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, get_credentials, is_file_older_than_x_days, is_file_older_than_x_minutes, load_file, load_profile, load_prefs, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import api_download
from resources.lib.constants import CONST_BASE_HEADERS, CONST_BASE_URL, CONST_DEFAULT_API, CONST_IMAGE_URL, CONST_MAIN_VOD_AR
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

def api_remove_from_watchlist(id, continuewatch=0):
    return None

def api_search(query):
    return None

def api_vod_download(type, start=0):
    type = str(type)

    if type in CONST_MAIN_VOD_AR:
        if type == '804':
            info_url = '{base_url}/2.0/R/ENG/WEB_DASH/ALL/PAGE/SEARCH/VOD/Anonymous/2?orderBy=contractStartDate&sortOrder=asc&filter_Series=W%20Series&filter_orderByDefault=Y&title=W%20Series&pageID=395_804'.format(base_url=CONST_BASE_URL)
        else:
            info_url = '{base_url}/2.0/R/ENG/WEB_DASH/ALL/PAGE/{id}/F1_TV_Pro_Annual/2'.format(base_url=CONST_BASE_URL, id=type)

        download = api_download(url=info_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK' or not check_key(data, 'resultObj') or not check_key(data['resultObj'], 'containers'):
            return None

        if type == '395':
            items = []
            item_ids = []

            for row in data['resultObj']['containers']:
                for row2 in row['retrieveItems']['resultObj']['containers']:
                    if check_key(row2, 'metadata') and check_key(row2['metadata'], 'contentSubtype'):
                        if row2['metadata']['contentSubtype'] == 'LIVE' and not row2['id'] in item_ids:                            
                            item = {}
                            item['id'] = row2['id']
                            item['title'] = row2['metadata']['title']
                            item['description'] = row2['metadata']['longDescription']
                            item['duration'] = row2['metadata']['duration']
                            item['type'] = 'event'
                            item['icon'] = '{image_url}/{image}?w=1920&h=1080&q=HI&o=L'.format(image_url=CONST_IMAGE_URL, image=row2['metadata']['pictureUrl'])
                            item['start'] = ''

                            items.append(item)
                            item_ids.append(row2['id'])

            return items
        else:
            vodJSONtitles = []
            vodJSON = {}
            vodJSON['menu'] = {}

            for row in data['resultObj']['containers']:
                if row['layout'] == 'horizontal_thumbnail':
                    if (type == '493' and ('EXTCOLLECTION' in row['retrieveItems']['uriOriginal'] or 'EXTCOLLECTION' in row['actions'][0]['uri'])) or type == '3946':
                        for row2 in row['retrieveItems']['resultObj']['containers']:
                            if row2['layout'] == 'CONTENT_ITEM':
                                if row2['metadata']['title'] in vodJSONtitles:
                                    continue

                                if len(row2['metadata']['title']) < 1 and len(str(row2['metadata']['season'])) < 1:
                                    continue

                                if check_key(row2, 'retrieveItems') and '2.0' in row2['retrieveItems']['uriOriginal'] and api_check_page(row2['retrieveItems']['uriOriginal']) == False:
                                    vodJSON['menu'][row2['id']] = {}
                                    vodJSON['menu'][row2['id']]['url'] = row2['retrieveItems']['uriOriginal']
                                elif check_key(row2, 'actions') and '2.0' in row2['actions'][0]['uri'] and api_check_page(row2['actions'][0]['uri']) == False:
                                    vodJSON['menu'][row2['id']] = {}
                                    vodJSON['menu'][row2['id']]['url'] = row2['actions'][0]['uri']
                                else:
                                    continue

                                if type == '493':
                                    if check_key(row2['metadata'], 'season') and len(str(row2['metadata']['season'])) > 0:
                                        vodJSON['menu'][row2['id']]['label'] = str(row2['metadata']['season']) + ' Season'
                                    else:
                                        vodJSON['menu'][row2['id']]['label'] = row2['metadata']['title']
                                elif type == '3946':
                                    if check_key(row2['metadata'], 'title') and len(str(row2['metadata']['title'])) > 0:
                                        vodJSON['menu'][row2['id']]['label'] = row2['metadata']['title']

                                vodJSONtitles.append(vodJSON['menu'][row2['id']]['label'])

                                if 'CONTENT/VIDEO/' in vodJSON['menu'][row2['id']]['url']:
                                    vodJSON['menu'][row2['id']]['type'] = 'video'
                                else:
                                    vodJSON['menu'][row2['id']]['type'] = 'content'

                                if check_key(row2['metadata'], 'pictureUrl') and len(row2['metadata']['pictureUrl']) > 0:
                                    vodJSON['menu'][row2['id']]['image'] = "{image_url}/{image}?w=1920&h=1080&q=HI&o=L".format(image_url=CONST_IMAGE_URL, image=row2['metadata']['pictureUrl'])
                                else:
                                    vodJSON['menu'][row2['id']]['image'] = ""

                        continue
                    elif row['metadata']['label'] in vodJSONtitles:
                        continue
                    elif check_key(row, 'retrieveItems') and '2.0' in row['retrieveItems']['uriOriginal'] and api_check_page(row['retrieveItems']['uriOriginal']) == False:
                        vodJSON['menu'][row['id']] = {}
                        vodJSON['menu'][row['id']]['url'] = row['retrieveItems']['uriOriginal']
                    elif check_key(row, 'actions') and '2.0' in row['actions'][0]['uri'] and api_check_page(row['actions'][0]['uri']) == False:
                        vodJSON['menu'][row['id']] = {}
                        vodJSON['menu'][row['id']]['url'] = row['actions'][0]['uri']
                    else:
                        continue

                    if len(row['metadata']['label']) < 1:
                        continue

                    vodJSON['menu'][row['id']]['label'] = row['metadata']['label']
                    vodJSONtitles.append(row['metadata']['label'])

                    if check_key(row['metadata'], 'pictureUrl') and len(row['metadata']['pictureUrl']) > 0:
                        vodJSON['menu'][row['id']]['image'] = "{image_url}/{image}?w=1920&h=1080&q=HI&o=L".format(image_url=CONST_IMAGE_URL, image=row['metadata']['pictureUrl'])
                    elif check_key(row['metadata'], 'imageUrl') and len(row['metadata']['imageUrl']) > 0:
                        vodJSON['menu'][row['id']]['image'] = "{image_url}/{image}?w=1920&h=1080&q=HI&o=L".format(image_url=CONST_IMAGE_URL, image=row['metadata']['imageUrl'])
                    else:
                        vodJSON['menu'][row['id']]['image'] = ""

                    if 'CONTENT/VIDEO/' in vodJSON['menu'][row['id']]['url']:
                        vodJSON['menu'][row['id']]['type'] = 'video'
                    else:
                        vodJSON['menu'][row['id']]['type'] = 'content'
                elif row['layout'] == 'vertical_thumbnail':
                    for row2 in row['retrieveItems']['resultObj']['containers']:
                        if row2['metadata']['title'] in vodJSONtitles:
                            continue

                        if len(row2['metadata']['title']) < 1:
                            continue
                        
                        if check_key(row, 'retrieveItems') and '2.0' in row['retrieveItems']['uriOriginal'] and api_check_page(row['retrieveItems']['uriOriginal']) == False:
                            continue
                        elif check_key(row, 'actions') and '2.0' in row['actions'][0]['uri'] and api_check_page(row['actions'][0]['uri']) == False:
                            continue
                        elif check_key(row2, 'actions') and '2.0' in row2['actions'][0]['uri'] and api_check_page(row2['actions'][0]['uri']) == False:
                            vodJSON['menu'][row2['id']] = {}
                            vodJSON['menu'][row2['id']]['url'] = row2['actions'][0]['uri']
                        else:
                            continue

                        vodJSON['menu'][row2['id']]['label'] = row2['metadata']['title']

                        if check_key(row['metadata'], 'pictureUrl') and len(row2['metadata']['pictureUrl']) > 0:
                            vodJSON['menu'][row2['id']]['image'] = "{image_url}/{image}?w=1920&h=1080&q=HI&o=L".format(image_url=CONST_IMAGE_URL, image=row2['metadata']['pictureUrl'])
                        else:
                            vodJSON['menu'][row2['id']]['image'] = ""

                        if 'CONTENT/VIDEO/' in vodJSON['menu'][row2['id']]['url']:
                            vodJSON['menu'][row2['id']]['type'] = 'video'
                        else:
                            vodJSON['menu'][row2['id']]['type'] = 'content'

                        vodJSONtitles.append(row2['metadata']['title'])

                    if row['metadata']['label'] in vodJSONtitles:
                        continue
                    elif check_key(row, 'retrieveItems') and '2.0' in row['retrieveItems']['uriOriginal'] and api_check_page(row['retrieveItems']['uriOriginal']) == False:
                        vodJSON['menu'][row['id']] = {}
                        vodJSON['menu'][row['id']]['url'] = row['retrieveItems']['uriOriginal']
                    elif check_key(row, 'actions') and '2.0' in row['actions'][0]['uri'] and api_check_page(row['actions'][0]['uri']) == False:
                        vodJSON['menu'][row['id']] = {}
                        vodJSON['menu'][row['id']]['url'] = row['actions'][0]['uri']
                    else:
                        continue

                    if len(row['metadata']['label']) < 1:
                        continue

                    vodJSON['menu'][row['id']]['label'] = row['metadata']['label']

                    if check_key(row['metadata'], 'pictureUrl') and len(row['metadata']['pictureUrl']) > 0:
                        vodJSON['menu'][row['id']]['image'] = "{image_url}/{image}?w=1920&h=1080&q=HI&o=L".format(image_url=CONST_IMAGE_URL, image=row['metadata']['pictureUrl'])
                    else:
                        vodJSON['menu'][row['id']]['image'] = ""

                    if 'CONTENT/VIDEO/' in vodJSON['menu'][row['id']]['url']:
                        vodJSON['menu'][row['id']]['type'] = 'video'
                    else:
                        vodJSON['menu'][row['id']]['type'] = 'content'

                    vodJSONtitles.append(row['metadata']['label'])
                elif row['layout'] == 'CONTENT_ITEM':
                    row2 = row
                    
                    if row2['metadata']['title'] in vodJSONtitles:
                        continue

                    if len(row2['metadata']['title']) < 1:
                        continue

                    if check_key(row2, 'actions') and '2.0' in row2['actions'][0]['uri'] and api_check_page(row2['actions'][0]['uri']) == False:
                        vodJSON['menu'][row2['id']] = {}
                        vodJSON['menu'][row2['id']]['url'] = row2['actions'][0]['uri']
                    else:
                        continue

                    vodJSON['menu'][row2['id']]['label'] = row2['metadata']['title']

                    if check_key(row['metadata'], 'pictureUrl') and len(row2['metadata']['pictureUrl']) > 0:
                        vodJSON['menu'][row2['id']]['image'] = "{image_url}/{image}?w=1920&h=1080&q=HI&o=L".format(image_url=CONST_IMAGE_URL, image=row2['metadata']['pictureUrl'])
                    else:
                        vodJSON['menu'][row2['id']]['image'] = ""

                    if 'CONTENT/VIDEO/' in vodJSON['menu'][row2['id']]['url']:
                        vodJSON['menu'][row2['id']]['type'] = 'video'
                    else:
                        vodJSON['menu'][row2['id']]['type'] = 'content'

                    vodJSONtitles.append(row2['metadata']['title'])
                                       
            write_file(file='cache' + os.sep + 'menu.json', data=vodJSON, isJSON=True)
            return vodJSON
    else:
        vodJSON2 = {}
        menu_data = load_file(file='cache' + os.sep + 'menu.json', isJSON=True)

        if not menu_data["menu"][str(type)] or len(menu_data["menu"][str(type)]['url']) == 0:
            return vodJSON2

        url = "{base_url}{url}".format(base_url=CONST_BASE_URL, url=menu_data["menu"][str(type)]['url'])
        download = api_download(url=url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK' or not check_key(data, 'resultObj') or not check_key(data['resultObj'], 'containers'):
            return vodJSON2

        data2 = api_extract_content(data['resultObj']['containers'])

        for currow in data2:
            row = data2[currow]

            if row['duration'] == 0 and row['type'] == 'movie':
                continue

            vodJSON2[row['id']] = {}
            vodJSON2[row['id']]['id'] = row['id']
            vodJSON2[row['id']]['title'] = row['title']
            vodJSON2[row['id']]['first'] = row['first']
            vodJSON2[row['id']]['description'] = row['desc']
            vodJSON2[row['id']]['duration'] = row['duration']
            vodJSON2[row['id']]['type'] = row['type']
            vodJSON2[row['id']]['main_genre'] = row['main_genre']
            vodJSON2[row['id']]['entitlement'] = row['entitlement']
            vodJSON2[row['id']]['icon'] = row['image']
            vodJSON2[row['id']]['category'] = row['category']
            log("TEST2")
            log(row['title'])
            log(row['image'])

        return vodJSON2

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
            if check_key(row['metadata'], 'additionalStreams'):
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
                    log("TEST3")
                    log(label)
                    log(image)

    return season

def api_vod_seasons(type, id):
    return None

def api_vod_subscription():
    return None

def api_watchlist_listing():
    return None

def api_clean_after_playback():
    pass

def api_check_page(url):
    regex = r"PAGE/([0-9]*)/"
    matches = re.search(regex, url)

    if matches:
        for groupNum in range(0, len(matches.groups())):
            groupNum = groupNum + 1

            try:
                if str(matches.group(groupNum)) in CONST_MAIN_VOD_AR:
                    return True
            except:
                pass

    return False

def api_extract_content(data):
    returnar = {}

    for row in data:
        if row['layout'] != 'CONTENT_ITEM':
            try:
                data2 = api_extract_content(row['retrieveItems']['resultObj']['containers'])
                returnar = {**returnar, **data2}
            except:
                pass

            continue

        if len(row['metadata']['title']) < 1 or row['metadata']['title'] == 'null':
            continue

        categoryStr = ""
        categoryAr = []

        for category in row['metadata']['genres']:
            categoryAr.append(category)

        categoryStr = ", ".join(categoryAr)

        id = row['id']

        returnar[id] = {}

        returnar[id]['main_genre'] = row['metadata']['contentSubtype']
        returnar[id]['id'] = row['id']
        
        #if check_key(row['metadata'], 'season') and len(str(row['metadata']['season'])) > 0 and not str(row['metadata']['season']) in row['metadata']['title']:
        #    returnar[id]['title'] = '[' + str(row['metadata']['season']) + '] ' + str(row['metadata']['title'])
        #else:
        returnar[id]['title'] = row['metadata']['title']
        
        returnar[id]['idtitle'] = returnar[id]['title']
        returnar[id]['sorttitle'] = returnar[id]['title']
        returnar[id]['first'] = returnar[id]['idtitle'][0].upper()

        regex = r"([^A-Z])"
        matches = re.search(regex, returnar[id]['first'])

        if not matches or len(matches.groups()) < 2:
            returnar[id]['first'] = 'other'

        returnar[id]['type'] = 'movie'

        if row['metadata']['emfAttributes']['OBC'] == True:
            returnar[id]['type'] = 'event'

        returnar[id]['desc'] = row['metadata']['longDescription']

        returnar[id]['duration'] = int(row['metadata']['duration'])

        if check_key(row['metadata'], 'entitlement'):
            returnar[id]['entitlement'] = row['metadata']['entitlement']
        else:
            returnar[id]['entitlement'] = ''

        if len(row['metadata']['pictureUrl']) > 0:
            returnar[id]['image'] = "{image_url}/{image}?w=1920&h=1080&q=HI&o=L".format(image_url=CONST_IMAGE_URL, image=row['metadata']['pictureUrl'])
        else:
            returnar[id]['image'] = ""

        returnar[id]['category'] = categoryStr

    return returnar