import base64, datetime, hashlib, hmac, os, random, re, string, time, xbmc

from bs4 import BeautifulSoup as bs4
from collections import OrderedDict
from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, encode32, get_credentials, is_file_older_than_x_days, is_file_older_than_x_minutes, load_file, load_profile, load_prefs, remove_dir, remove_file, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import api_download, api_get_channels
from resources.lib.constants import CONST_IMAGES, CONST_URLS
from resources.lib.util import convert_to_seconds, plugin_process_info
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
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)
    headers = { 'authorization': 'Bearer {id_token}'.format(id_token=profile_settings['access_token'])}

    if type == 'continuewatch':
        watchlist_url = '{base_url}/v7/watchlist/{id}'.format(base_url=CONST_URLS['api'], id=id)
    elif type == 'watchlist':
        watchlist_url = '{base_url}/v7/trackedseries/{id}'.format(base_url=CONST_URLS['api'], id=id)

    download = api_download(url=watchlist_url, type='post', headers=headers, data=None, json_data=False, return_json=False)
    code = download['code']

    if not code or not code == 200:
        return False

    return True

def api_clean_after_playback(stoptime):
    pass

def api_get_info(id, channel=''):
    profile_settings = load_profile(profile_id=1)

    info = {}
    friendly = ''

    data = api_get_channels()

    try:
        friendly = data[str(id)]['assetid']
    except:
        return info

    channel_url = '{base_url}/v7/epg/locations/{friendly}/live/1?fromDate={date}'.format(base_url=CONST_URLS['api'], friendly=friendly, date=datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S"))

    download = api_download(url=channel_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data:
        return info

    for row in data:
        if not check_key(row, 'Channel') or not check_key(row, 'Locations'):
            return info

        for row2 in row['Locations']:
            id = row2['LocationId']

    if not id:
        return info

    info_url = '{base_url}/v7/epg/location/{location}'.format(base_url=CONST_URLS['api'], location=id)

    download = api_download(url=info_url, type='get', headers=None, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data:
        return info

    info = data

    return plugin_process_info({'title': '', 'channel': channel, 'info': info})

def api_get_session(force=0, return_data=False):
    force = int(force)
    code = None
    data = None
    profile_settings = load_profile(profile_id=1)
    profile_url = '{base_url}/v7/profile'.format(base_url=CONST_URLS['api'])

    if check_key(profile_settings, 'access_token_age') and check_key(profile_settings, 'access_token') and int(profile_settings['access_token_age']) > int(time.time()):
        headers = { 'authorization': 'Bearer {id_token}'.format(id_token=profile_settings['access_token'])}
        download = api_download(url=profile_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

    if not code or not code == 200:
        login_result = api_login()

        if not login_result['result']:
            if return_data == True:
                return {'result': False, 'data': login_result['data'], 'code': login_result['code']}

            return False
        else:
            profile_settings = load_profile(profile_id=1)
            headers = { 'authorization': 'Bearer {id_token}'.format(id_token=profile_settings['access_token'])}
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
            return_profiles[result['id']] = {}
            return_profiles[result['id']]['id'] = result['id']
            return_profiles[result['id']]['name'] = result['displayName']

    return return_profiles

def api_list_watchlist(type='watchlist'):
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)
    headers = { 'authorization': 'Bearer {id_token}'.format(id_token=profile_settings['access_token'])}

    if type == 'continuewatch':
        watchlist_url = '{base_url}/v7/watchlist?limit=999&offset=0'.format(base_url=CONST_URLS['api'])
    elif type == 'watchlist':
        watchlist_url = '{base_url}/v7/trackedseries?limit=999&offset=0'.format(base_url=CONST_URLS['api'])

    download = api_download(url=watchlist_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if code and code == 200 and data:
        return data

    return None

    if not data:
        return None

    return data

def api_login(force=False):
    creds = get_credentials()
    username = creds['username']
    password = creds['password']
    loggedin = False

    profile_settings = load_profile(profile_id=1)

    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    code_verifier = re.sub('[^a-zA-Z0-9]+', '', code_verifier)

    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
    code_challenge = code_challenge.replace('=', '')

    state = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(32))

    base_authorization_url = "{id_url}/connect/authorize".format(id_url=CONST_URLS['id'])

    if check_key(profile_settings, 'id_token') and force == False:
        id_token_hint = profile_settings['id_token']

        authorization_url = "{base_url}?response_type=code&client_id=triple-web&scope=openid api&redirect_uri={app_url}/callback-silent.html&state={state}&code_challenge={code_challenge}&code_challenge_method=S256&response_mode=query&prompt=none&id_token_hint={id_token_hint}".format(base_url=base_authorization_url, app_url=CONST_URLS['app'], state=state, code_challenge=code_challenge, id_token_hint=id_token_hint)

        download = api_download(url=authorization_url, type='get', headers=None, data=None, json_data=False, return_json=False, allow_redirects=False)
        data = download['data']
        code = download['code']

        if code == 302:
            redirect = download['headers']['Location']

            auth_code = None
            query = None
            redirect_params = None

            try:
                query = urlparse(redirect).query
                redirect_params = parse_qs(query)
                auth_code = redirect_params['code'][0]
            except:
                pass

            if auth_code:
                download = api_download(url=redirect, type='get', headers=None, data=None, json_data=False, return_json=False, allow_redirects=False)
                data = download['data']
                code = download['code']

                if code == 200:
                    post_data={
                        "client_id": 'triple-web',
                        "code": auth_code,
                        "redirect_uri": "{app_url}/callback-silent.html".format(app_url=CONST_URLS['app']),
                        "code_verifier": code_verifier,
                        "grant_type": "authorization_code"
                    }

                    download = api_download(url="{id_url}/connect/token".format(id_url=CONST_URLS['id']), type='post', headers=None, data=post_data, json_data=False, return_json=True, allow_redirects=False)
                    data = download['data']
                    code = download['code']

                    if data and code == 200 and check_key(data, 'id_token') and check_key(data, 'access_token'):
                        loggedin = True

    if not loggedin:
        remove_file(file='stream_cookies', ext=False)

        profile_settings['access_token'] = ''
        profile_settings['access_token_age'] = 0
        profile_settings['id_token'] = ''
        save_profile(profile_id=1, profile=profile_settings)

        authorization_url = "{base_url}?response_type=code&client_id=triple-web&scope=openid api&redirect_uri={app_url}/callback&state={state}&code_challenge={code_challenge}&code_challenge_method=S256&response_mode=query".format(base_url=base_authorization_url, app_url=CONST_URLS['app'], state=state, code_challenge=code_challenge)

        download = api_download(url=authorization_url, type='get', headers=None, data=None, json_data=False, return_json=False, allow_redirects=False)
        data = download['data']
        code = download['code']

        if code == 302:
            redirect = download['headers']['Location']

            download = api_download(url=redirect, type='get', headers=None, data=None, json_data=False, return_json=False, allow_redirects=False)
            data = download['data']
            code = download['code']

            if code == 200:
                soup = bs4(data, 'html.parser')
                token = None

                try:
                    token = soup.find('input', {'name':'__RequestVerificationToken'})['value']
                except:
                    pass

                query = urlparse(redirect).query
                request_params = parse_qs(query)

                if token and request_params and check_key(request_params, 'ReturnUrl'):
                    post_data={
                        "ReturnUrl": request_params['ReturnUrl'][0],
                        "EmailAddress": username,
                        "Password": password,
                        "RememberLogin": "true",
                        "button": "login",
                        "__RequestVerificationToken": token
                    }

                    download = api_download(url=redirect, type='post', headers=None, data=post_data, json_data=False, return_json=False, allow_redirects=False)
                    data = download['data']
                    code = download['code']

                    if code == 302:
                        redirect = download['headers']['Location']

                        download = api_download(url=CONST_URLS['id'] + redirect, type='get', headers=None, data=None, json_data=False, return_json=False, allow_redirects=False)
                        data = download['data']
                        code = download['code']

                        if code == 302:
                            redirect = download['headers']['Location']
                            auth_code = None
                            query = None
                            redirect_params = None

                            try:
                                query = urlparse(redirect).query
                                redirect_params = parse_qs(query)
                                auth_code = redirect_params['code'][0]
                            except:
                                pass

                            if auth_code:
                                download = api_download(url=redirect, type='get', headers=None, data=None, json_data=False, return_json=False, allow_redirects=False)
                                data = download['data']
                                code = download['code']

                                if code == 200:
                                    post_data={
                                        "client_id": 'triple-web',
                                        "code": auth_code,
                                        "redirect_uri": "{app_url}/callback".format(app_url=CONST_URLS['app']),
                                        "code_verifier": code_verifier,
                                        "grant_type": "authorization_code"
                                    }

                                    download = api_download(url="{id_url}/connect/token".format(id_url=CONST_URLS['id']), type='post', headers=None, data=post_data, json_data=False, return_json=True, allow_redirects=False)
                                    data = download['data']
                                    code = download['code']

                                    if data and check_key(data, 'id_token') and check_key(data, 'access_token'):
                                        loggedin = True

    if not loggedin:
        return { 'code': code, 'data': data, 'result': False }

    profile_settings['id_token'] = data['id_token']
    profile_settings['access_token'] = data['access_token']
    profile_settings['access_token_age'] = int(time.time()) + int(data['expires_in'])
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

    headers = { 'authorization': 'Bearer {id_token}'.format(id_token=profile_settings['access_token'])}

    friendly = ''
    info = {}
    properties = {}

    data = api_get_channels()

    try:
        friendly = data[str(channel)]['assetid']
    except:
        pass

    if type == 'channel':
        channel_url = '{base_url}/v8/epg/programlocations/live'.format(base_url=CONST_URLS['api'])

        download = api_download(url=channel_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']       

        if not code or not code == 200 or not data:
            return playdata

        for row in data["data"]:
            if row["channel"]["id"] == channel:
                id = row["programLocations"][0]["assetId"]
    elif not type == 'vod':
        detail_url = '{base_url}/v7/content/detail/{id}'.format(base_url=CONST_URLS['api'], id=id)

        download = api_download(url=detail_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            if check_key(data, 'assets'):
                if check_key(data['assets'], 'epg') and check_key(data['assets']['epg'][0], 'locationId'):
                    id = data['assets']['epg'][0]['locationId']

    if not id:
        return playdata

    if type == 'vod':
        url_base = '{base_url}/v7/stream/handshake/Widevine/dash/VOD/{id}'.format(base_url=CONST_URLS['api'], id=id)
    elif type == 'channel' and channel and friendly:
        url_base = '{base_url}/v7/stream/handshake/Widevine/dash/Live/{id}'.format(base_url=CONST_URLS['api'], id=id)
    else:
        url_base = '{base_url}/v7/stream/handshake/Widevine/dash/Replay/{id}'.format(base_url=CONST_URLS['api'], id=id)

    play_url = '{url_base}?playerName=BitmovinWeb'.format(url_base=url_base)

    download = api_download(url=play_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'uri'):
        return playdata

    license = data
    path = data['uri']

    if not type == 'vod' and (pvr == 0):
        info_url = '{base_url}/v7/epg/location/{location}'.format(base_url=CONST_URLS['api'], location=id)

        download = api_download(url=info_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data:
            return playdata

        info = data

    if not len(str(license)) > 0:
        return playdata

    mpd = ''

    if change_audio == 1:
        download = api_download(url=path, type='get', headers=headers, data=None, json_data=False, return_json=False)
        data = download['data']
        code = download['code']

        if code and code == 200:
            mpd = data

    playdata = {'path': path, 'mpd': mpd, 'license': license, 'info': info, 'properties': properties}

    return playdata

def api_remove_from_watchlist(id, type='watchlist'):
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)
    headers = { 'authorization': 'Bearer {id_token}'.format(id_token=profile_settings['access_token'])}

    if type == 'continuewatch':
        watchlist_url = '{base_url}/v7/watchlist/{id}'.format(base_url=CONST_URLS['api'], id=id)
    elif type == 'watchlist':
        watchlist_url = '{base_url}/v7/trackedseries/{id}'.format(base_url=CONST_URLS['api'], id=id)

    download = api_download(url=watchlist_url, type='delete', headers=headers, data=None, json_data=False, return_json=False)
    code = download['code']

    if not code or (not code == 200 and not code == 204):
        return False

    return True

def api_search(query):
    type = "search_{query}".format(query=query)
    type = encode32(txt=type)

    file = os.path.join("cache", "{type}.json".format(type=type))

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        search_url = '{base_url}/v7/search/combined?searchterm={query}&maxSerieResults=99999999&maxVideoResults=99999999&expand=true&expandlist=true'.format(base_url=CONST_URLS['api'], query=quote_plus(query))

        download = api_download(url=search_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)

    if not data:
        return None

    items = {}

    if check_key(data, 'Series'):
        for row in data['Series']:
            if not check_key(row, 'SerieId') or not check_key(row, 'Name'):
                continue

            items[row['SerieId']] = {}

            desc = ''
            image = ''

            if check_key(row, 'Omschrijving'):
                desc = row['Omschrijving']

            if check_key(row, 'ProgrammaAfbeelding'):
                image = row['ProgrammaAfbeelding']

                if not 'http' in image:
                    image_split = image.rsplit('/', 1)

                    if len(image_split) == 2:
                        image = '{image_url}/legacy/thumbnails/{image}'.format(image_url=CONST_URLS['image'], image=image.rsplit('/', 1)[1])
                    else:
                        image = '{image_url}/{image}'.format(image_url=CONST_URLS['image'], image=image)

            items[row['SerieId']]['id'] = row['SerieId']
            items[row['SerieId']]['title'] = row['Name']
            items[row['SerieId']]['description'] = desc
            items[row['SerieId']]['duration'] = 0
            items[row['SerieId']]['type'] = 'Serie'
            items[row['SerieId']]['icon'] = image

    if check_key(data, 'Videos'):
        for row in data['Videos']:
            if not check_key(row, 'Video') or not check_key(row['Video'], 'VideoId') or not check_key(row['Video'], 'VideoType') or (not check_key(row, 'Titel') and (not check_key(row, 'Serie') or not check_key(row['Serie'], 'Titel'))):
                continue

            id = row['Video']['VideoId']
            items[id] = {}

            if row['Video']['VideoType'] == 'VOD':
                type = 'Vod'
            elif row['Video']['VideoType'] == 'Replay':
                type = 'Epg'
            elif row['Video']['VideoType'] == 'Serie':
                type = 'Serie'
            else:
                continue

            basetitle = ''
            desc = ''
            start = ''
            duration = 0
            image = ''

            if check_key(row, 'Serie') and check_key(row['Serie'], 'Titel'):
                basetitle = row['Serie']['Titel']

            if check_key(row, 'Titel'):
                if len(row['Titel']) > 0 and basetitle != row['Titel']:
                    if len(basetitle) > 0:
                        basetitle += ": " + row['Titel']
                    else:
                        basetitle = row['Titel']

            if check_key(row, 'Omschrijving'):
                desc = row['Omschrijving']

            if check_key(row, 'Duur'):
                duration = row['Duur']

            if check_key(row, 'AfbeeldingUrl'):
                image = row['AfbeeldingUrl']

                if not 'http' in image:
                    image_split = image.rsplit('/', 1)

                    if len(image_split) == 2:
                        image = '{image_url}/legacy/thumbnails/{image}'.format(image_url=CONST_URLS['image'], image=image.rsplit('/', 1)[1])
                    else:
                        image = '{image_url}/{image}'.format(image_url=CONST_URLS['image'], image=image)

            if check_key(row, 'Uitzenddatum'):
                start = row['Uitzenddatum']

            items[id]['id'] = id
            items[id]['title'] = basetitle
            items[id]['description'] = desc
            items[id]['duration'] = duration
            items[id]['type'] = type
            items[id]['icon'] = image
            items[id]['start'] = start

    return items

def api_set_profile(id=''):
    profiles = api_get_session(force=0, return_data=True)

    if not profiles or profiles['result'] == False:
        return False

    profile_settings = load_profile(profile_id=1)
    headers = { 'authorization': 'Bearer {id_token}'.format(id_token=profile_settings['access_token'])}

    name = ''
    owner_id = ''
    owner_name = ''
    saved_id = ''
    saved_name = ''

    for result in profiles['data']:
        if len(str(owner_id)) == 0:
            owner_id = result['id']
            owner_name = result['displayName']

        if result['id'] == id:
            name = result['displayName']

        if check_key(profile_settings, 'profile_id'):
            if result['id'] == profile_settings['profile_id']:
                saved_id = result['id']
                saved_name = result['displayName']

    if len(str(name)) == 0:
        if len(str(saved_name)) > 0:
            id = saved_id
            name = saved_name
        else:
            id = owner_id
            name = owner_name

    switch_url = '{base_url}/connect/token'.format(base_url=CONST_URLS['id'])

    session_post_data = {
        'client_id': 'triple-web',
        'profile': id,
        'scope': 'openid api',
        'grant_type': 'profile'
    }

    download = api_download(url=switch_url, type='post', headers=headers, data=session_post_data, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not check_key(data, 'access_token'):
        return False

    profile_settings = load_profile(profile_id=1)
    profile_settings['profile_name'] = name
    profile_settings['profile_id'] = id
    profile_settings['access_token'] = data['access_token']
    profile_settings['access_token_age'] = int(time.time()) + int(data['expires_in'])
    save_profile(profile_id=1, profile=profile_settings)

    return True

def api_vod_download(type, start=0):
    if type == "moviesnpo":
        url = '{base_url}/v7/recommend/movies?limit=9999&offset=0&contentProvider=npo'.format(base_url=CONST_URLS['api'], start=start)
    elif type == "movies":
        url = '{base_url}/v7/recommend/movies?limit=9999&offset=0'.format(base_url=CONST_URLS['api'], start=start)
    elif type == "watchaheadnpo":
        url = '{base_url}/v7/watchinadvance?limit=9999&offset=0&contentProvider=npo'.format(base_url=CONST_URLS['api'], start=start)
    elif type == "watchahead":
        url = '{base_url}/v7/watchinadvance?limit=9999&offset=0'.format(base_url=CONST_URLS['api'], start=start)
    elif type == "seriesbingenpo":
        url = '{base_url}/v7/recommend/series?limit=9999&offset=0&contentProvider=npo'.format(base_url=CONST_URLS['api'], start=start)
    elif type == "seriesbinge":
        url = '{base_url}/v7/recommend/series?limit=9999&offset=0'.format(base_url=CONST_URLS['api'], start=start)
    elif type == "mostviewed":
        url = '{base_url}/v7/recommend/trendingvideos?limit=9999&offset=0'.format(base_url=CONST_URLS['api'], start=start)
    elif type == "tipfeednpo":
        url = '{base_url}/v7/recommend/recommendedvideos?limit=9999&offset=0&contentProvider=npo'.format(base_url=CONST_URLS['api'], start=start)
    elif type == "tipfeed":
        url = '{base_url}/v7/recommend/recommendedvideos?limit=9999&offset=0'.format(base_url=CONST_URLS['api'], start=start)
    else:
        return None

    type = "vod_{type}_{start}".format(type=type, start=start)
    type = encode32(txt=type)

    file = os.path.join("cache", "{type}.json".format(type=type))

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)

    if not data:
        return None

    return data

def api_vod_season(series, id, use_cache=True):
    type = "vod_season_{series}###{id}".format(series=series, id=id)
    type = encode32(txt=type)

    file = os.path.join("cache", "{type}.json".format(type=type))

    cache = 0

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=0.5) and use_cache == True:
        data = load_file(file=file, isJSON=True)
        cache = 1
    else:
        program_url = '{base_url}/v7/series/{series}/episodes?seasonId={id}&limit=999&offset=0'.format(base_url=CONST_URLS['api'], series=series, id=id)
        download = api_download(url=program_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)

    return {'data': data, 'cache': cache}

def api_vod_seasons(type, id, use_cache=True):
    type = "vod_seasons_{id}".format(id=id)
    type = encode32(txt=type)

    file = os.path.join("cache", "{type}.json".format(type=type))

    cache = 0

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=0.5) and use_cache == True:
        data = load_file(file=file, isJSON=True)
        cache = 1
    else:
        program_url = '{base_url}/v7/series/{id}'.format(base_url=CONST_URLS['api'], id=id)
        download = api_download(url=program_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)

    return {'data': data, 'cache': cache}

def api_watchlist_listing():
    return None
