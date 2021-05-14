import base64, datetime, hashlib, hmac, os, random, re, string, time, xbmc

from bs4 import BeautifulSoup as bs4
from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, get_credentials, is_file_older_than_x_days, is_file_older_than_x_minutes, load_file, load_profile, load_prefs, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import api_download, api_get_channels
from resources.lib.constants import CONST_API_URL, CONST_APP_URL, CONST_BASE_URL, CONST_ID_URL, CONST_IMAGE_URL
from resources.lib.util import plugin_process_info
from urllib.parse import parse_qs, urlparse, quote_plus

def api_add_to_watchlist():
    return None

def api_get_info(id, channel=''):
    profile_settings = load_profile(profile_id=1)

    info = {}
    friendly = ''
    headers = { 'authorization': 'Bearer {id_token}'.format(id_token=profile_settings['access_token'])}

    data = api_get_channels()

    try:
        friendly = data[str(id)]['assetid']
    except:
        return info

    channel_url = '{base_url}/v7/epg/locations/{friendly}/live/1?fromDate={date}'.format(base_url=CONST_API_URL, friendly=friendly, date=datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S"))

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

    info_url = '{base_url}/v7/epg/location/{location}'.format(base_url=CONST_API_URL, location=id)

    download = api_download(url=info_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data:
        return info

    info = data

    return plugin_process_info({'title': '', 'channel': channel, 'info': info})

def api_get_session(force=0):
    force = int(force)
    profile_settings = load_profile(profile_id=1)

    if not check_key(profile_settings, 'access_token_age') or not check_key(profile_settings, 'access_token') or int(profile_settings['access_token_age']) < int(time.time() - 3540):
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

    base_authorization_url = "{id_url}/connect/authorize".format(id_url=CONST_ID_URL)

    if check_key(profile_settings, 'id_token') and force == False:
        id_token_hint = profile_settings['id_token']

        authorization_url = "{base_url}?response_type=code&client_id=triple-web&scope=openid api&redirect_uri={app_url}/callback-silent.html&state={state}&code_challenge={code_challenge}&code_challenge_method=S256&response_mode=query&prompt=none&id_token_hint={id_token_hint}".format(base_url=base_authorization_url, app_url=CONST_APP_URL, state=state, code_challenge=code_challenge, id_token_hint=id_token_hint)

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
                        "redirect_uri": "{app_url}/callback-silent.html".format(app_url=CONST_APP_URL),
                        "code_verifier": code_verifier,
                        "grant_type": "authorization_code"
                    }

                    download = api_download(url="{id_url}/connect/token".format(id_url=CONST_ID_URL), type='post', headers=None, data=post_data, json_data=False, return_json=True, allow_redirects=False)
                    data = download['data']
                    code = download['code']

                    if data and code == 200 and check_key(data, 'id_token') and check_key(data, 'access_token'):
                        loggedin = True

    if not loggedin:
        try:
            os.remove(ADDON_PROFILE + 'stream_cookies')
        except:
            pass

        profile_settings['access_token'] = ''
        profile_settings['access_token_age'] = 0
        profile_settings['id_token'] = ''
        save_profile(profile_id=1, profile=profile_settings)

        authorization_url = "{base_url}?response_type=code&client_id=triple-web&scope=openid api&redirect_uri={app_url}/callback&state={state}&code_challenge={code_challenge}&code_challenge_method=S256&response_mode=query".format(base_url=base_authorization_url, app_url=CONST_APP_URL, state=state, code_challenge=code_challenge)

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

                        download = api_download(url=CONST_ID_URL + redirect, type='get', headers=None, data=None, json_data=False, return_json=False, allow_redirects=False)
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
                                        "redirect_uri": "{app_url}/callback".format(app_url=CONST_APP_URL),
                                        "code_verifier": code_verifier,
                                        "grant_type": "authorization_code"
                                    }

                                    download = api_download(url="{id_url}/connect/token".format(id_url=CONST_ID_URL), type='post', headers=None, data=post_data, json_data=False, return_json=True, allow_redirects=False)
                                    data = download['data']
                                    code = download['code']

                                    if data and check_key(data, 'id_token') and check_key(data, 'access_token'):
                                        loggedin = True

    if not loggedin:
        return { 'code': code, 'data': data, 'result': False }

    profile_settings['id_token'] = data['id_token']
    profile_settings['access_token'] = data['access_token']
    profile_settings['access_token_age'] = int(time.time())
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

    headers = { 'authorization': 'Bearer {id_token}'.format(id_token=profile_settings['access_token'])}

    friendly = ''
    info = {}
    properties = {}

    data = api_get_channels()

    try:
        friendly = data[str(channel)]['assetid']
    except:
        pass
        
    if type == 'channel' and friendly:
        channel_url = '{base_url}/v7/epg/locations/{friendly}/live/1?fromDate={date}'.format(base_url=CONST_API_URL, friendly=friendly, date=datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S"))

        download = api_download(url=channel_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data:
            return playdata

        for row in data:
            if not check_key(row, 'Channel') or not check_key(row, 'Locations'):
                return playdata

            for row2 in row['Locations']:
                id = row2['LocationId']

    if not id:
        return playdata
        
    if type == 'vod':
        url_base = '{base_url}/v7/stream/handshake/Widevine/dash/VOD/{id}'.format(base_url=CONST_API_URL, id=id)
    elif type == 'channel' and channel and friendly:
        url_base = '{base_url}/v7/stream/handshake/Widevine/dash/Live/{id}'.format(base_url=CONST_API_URL, id=id)
    else:
        url_base = '{base_url}/v7/stream/handshake/Widevine/dash/Replay/{id}'.format(base_url=CONST_API_URL, id=id)

    play_url = '{url_base}?playerName=BitmovinWeb'.format(url_base=url_base)

    download = api_download(url=play_url, type='get', headers=headers, data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'uri'):
        return playdata

    license = data
    path = data['uri']

    if not type == 'vod' and (pvr == 0):
        info_url = '{base_url}/v7/epg/location/{location}'.format(base_url=CONST_API_URL, location=id)

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

def api_process_vod(data):
    items = []

    for row in data:
        item = {}

        if not check_key(row, 'type'):
            type = 'Serie'
        else:
            if row['type'] == 'Vod':
                type = 'Vod'
            elif row['type'] == 'Epg':
                type = 'Epg'
            else:
                continue

        if not check_key(row, 'id') or not check_key(row, 'title'):
            continue

        id = row['id']
        basetitle = row['title']
        desc = ''
        start = ''
        duration = 0
        image = ''

        if check_key(row, 'description'):
            desc = row['description']

        if check_key(row, 'formattedDuration'):
            duration = convert_to_seconds(row['formattedDuration'])

        if check_key(row, 'image'):
            image = row['image']['landscapeUrl']

            if not 'http' in image:
                image_split = image.rsplit('/', 1)

                if len(image_split) == 2:
                    image = '{image_url}/legacy/thumbnails/{image}'.format(image_url=CONST_IMAGE_URL, image=image.rsplit('/', 1)[1])
                else:
                    image = '{image_url}/{image}'.format(image_url=CONST_IMAGE_URL, image=image)

        if check_key(row, 'formattedDate') and check_key(row, 'formattedTime'):
            start = "{date} {time}".format(date=row['formattedDate'], time=row['formattedTime'])

        item['id'] = id
        item['title'] = basetitle
        item['description'] = desc
        item['duration'] = duration
        item['type'] = type
        item['icon'] = image
        item['start'] = start

        items.append(item)

    return items

def api_remove_from_watchlist():
    return None

def api_search(query):
    if not api_get_session():
        return None

    type = "search_" + query
    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        search_url = '{base_url}/v7/search/combined?searchterm={query}&maxSerieResults=99999999&maxVideoResults=99999999&expand=true&expandlist=true'.format(base_url=CONST_API_URL, query=quote_plus(query))

        download = api_download(url=search_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)

    if not data:
        return None

    items = []

    if check_key(data, 'Series'):
        for row in data['Series']:
            item = {}

            if not check_key(row, 'SerieId') or not check_key(row, 'Name'):
                continue

            desc = ''
            image = ''

            if check_key(row, 'Omschrijving'):
                desc = row['Omschrijving']

            if check_key(row, 'ProgrammaAfbeelding'):
                image = row['ProgrammaAfbeelding']

                if not 'http' in image:
                    image_split = image.rsplit('/', 1)

                    if len(image_split) == 2:
                        image = '{image_url}/legacy/thumbnails/{image}'.format(image_url=CONST_IMAGE_URL, image=image.rsplit('/', 1)[1])
                    else:
                        image = '{image_url}/{image}'.format(image_url=CONST_IMAGE_URL, image=image)

            item['id'] = row['SerieId']
            item['title'] = row['Name']
            item['description'] = desc
            item['duration'] = 0
            item['type'] = 'Serie'
            item['icon'] = image

            items.append(item)

    if check_key(data, 'Videos'):
        for row in data['Videos']:
            item = {}

            if not check_key(row, 'Video') or not check_key(row['Video'], 'VideoId') or not check_key(row['Video'], 'VideoType') or (not check_key(row, 'Titel') and (not check_key(row, 'Serie') or not check_key(row['Serie'], 'Titel'))):
                continue

            id = row['Video']['VideoId']

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
                        image = '{image_url}/legacy/thumbnails/{image}'.format(image_url=CONST_IMAGE_URL, image=image.rsplit('/', 1)[1])
                    else:
                        image = '{image_url}/{image}'.format(image_url=CONST_IMAGE_URL, image=image)

            if check_key(row, 'Uitzenddatum'):
                start = row['Uitzenddatum']

            item['id'] = id
            item['title'] = basetitle
            item['description'] = desc
            item['duration'] = duration
            item['type'] = type
            item['icon'] = image
            item['start'] = start

            items.append(item)

    return items

def api_sort_episodes(element):
    try:
        return element['episodeNumber']
    except:
        return 0

def api_sort_season(element):
    if str(element['seriesNumber']).isnumeric():
        return int(element['seriesNumber'])
    else:
        matches = re.findall(r"Seizoen (\d+)", element['seriesNumber'])

        for match in matches:
            return int(match)

        return 0

def api_vod_download(type, start=0):
    if not api_get_session():
        return None

    if type == "moviesnpo":
        url = '{base_url}/v7/recommend/movies?limit=52&offset={start}&contentProvider=npo'.format(base_url=CONST_API_URL, start=start)
    elif type == "movies":
        url = '{base_url}/v7/recommend/movies?limit=52&offset={start}'.format(base_url=CONST_API_URL, start=start)
    elif type == "watchaheadnpo":
        url = '{base_url}/v7/watchinadvance?limit=52&offset={start}&contentProvider=npo'.format(base_url=CONST_API_URL, start=start)
    elif type == "watchahead":
        url = '{base_url}/v7/watchinadvance?limit=52&offset={start}'.format(base_url=CONST_API_URL, start=start)
    elif type == "seriesbingenpo":
        url = '{base_url}/v7/recommend/series?limit=52&offset={start}&contentProvider=npo'.format(base_url=CONST_API_URL, start=start)
    elif type == "seriesbinge":
        url = '{base_url}/v7/recommend/series?limit=52&offset={start}'.format(base_url=CONST_API_URL, start=start)
    elif type == "mostviewed":
        url = '{base_url}/v7/recommend/trendingvideos?limit=52&offset={start}'.format(base_url=CONST_API_URL, start=start)
    elif type == "tipfeednpo":
        url = '{base_url}/v7/recommend/recommendedvideos?limit=52&offset={start}&contentProvider=npo'.format(base_url=CONST_API_URL, start=start)
    elif type == "tipfeed":
        url = '{base_url}/v7/recommend/recommendedvideos?limit=52&offset={start}'.format(base_url=CONST_API_URL, start=start)
    else:
        return None

    type = "vod_" + type + "_" + str(start)
    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)

    if not data:
        return None

    return api_process_vod(data=data)

def api_vod_season(series, id):
    if not api_get_session():
        return None

    season = []

    program_url = '{base_url}/v7/series/{series}/episodes?seasonId={id}&limit=999&offset=0'.format(base_url=CONST_API_URL, series=series, id=id)

    type = "vod_series_" + str(series) + "_season_" + str(id)
    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=program_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)

    if not data:
        return None

    for row in data:
        duration = 0
        ep_id = ''
        desc = ''
        image = ''
        label = ''

        if check_key(row, 'subtitle') and len(row['subtitle']) > 0:
            episodeTitle = row['subtitle']
        else:
            episodeTitle = row['title']

        if check_key(row, 'formattedDuration'):
            duration = convert_to_seconds(row['formattedDuration'])

        if check_key(row, 'id'):
            ep_id = row['id']

        if check_key(row, 'description'):
            desc = row['description']

        if check_key(row, 'image') and check_key(row['image'], 'landscapeUrl'):
            image = row['image']['landscapeUrl']

            if not 'http' in image:
                image_split = image.rsplit('/', 1)

                if len(image_split) == 2:
                    image = '{image_url}/legacy/thumbnails/{image}'.format(image_url=CONST_IMAGE_URL, image=image.rsplit('/', 1)[1])
                else:
                    image = '{image_url}/{image}'.format(image_url=CONST_IMAGE_URL, image=image)

        if check_key(row, 'formattedDate') and check_key(row, 'formattedTime'):
            label += "{date} {time}".format(date=row['formattedDate'], time=row['formattedTime'])

        seasonno = ''
        episodeno = ''

        if check_key(row, 'formattedEpisodeNumbering'):
            label += " " + str(row['formattedEpisodeNumbering'])

            regex = r"S([0-9]*):A([0-9]*)"
            matches = re.finditer(regex, str(row['formattedEpisodeNumbering']))

            for matchNum, match in enumerate(matches, start=1):
                if len(match.groups()) == 2:
                    seasonno = match.group(1)
                    episodeno = match.group(2)

        if len(label) > 0:
            label += " - "

        label += episodeTitle

        season.append({'label': label, 'id': ep_id, 'start': '', 'duration': duration, 'title': episodeTitle, 'seasonNumber': seasonno, 'episodeNumber': episodeno, 'description': desc, 'image': image})

    season[:] = sorted(season, key=api_sort_episodes)

    return season

def api_vod_seasons(type, id):
    if not api_get_session():
        return None

    seasons = []

    program_url = '{base_url}/v7/series/{id}'.format(base_url=CONST_API_URL, id=id)

    type = "vod_seasons_" + str(id)
    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=program_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)

    if not data:
        return None

    season_count = 0
    type = 'seasons'

    if check_key(data, 'seasons'):
        for row in data['seasons']:
            season_count += 1

            seasons.append({'id': row['id'], 'seriesNumber': row['title'], 'description': data['description'], 'image': data['image']['landscapeUrl']})

    seasons[:] = sorted(seasons, key=api_sort_season)

    return {'program': data, 'type': type, 'seasons': seasons}

def api_watchlist_listing():
    return None

def api_clean_after_playback():
    pass
    
def convert_to_seconds(s):
    UNITS = {'s':'seconds', 'm':'minutes', 'h':'hours', 'd':'days', 'w':'weeks'}

    return int(datetime.timedelta(**{
        UNITS.get(m.group('unit').lower(), 'seconds'): int(m.group('val'))
        for m in re.finditer(r'(?P<val>\d+)(?P<unit>[smhdw]?)', s, flags=re.I)
    }).total_seconds())