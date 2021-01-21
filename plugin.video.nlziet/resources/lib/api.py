import base64, datetime, hmac, os, random, re, string, time, xbmc
from hashlib import sha1
from requests_oauthlib import OAuth1

from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, find_highest_bandwidth, get_credentials, is_file_older_than_x_days, is_file_older_than_x_minutes, load_file, load_profile, load_prefs, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import api_download, api_get_channels
from resources.lib.constants import CONST_API_URL, CONST_BASE_URL, CONST_IMAGE_URL

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

    if not check_key(profile_settings, 'resource_verifier'):
        login_result = api_login()

        if not login_result['result']:
            return False
    else:
        token_url_base = '{base_url}/v6/favorites/items'.format(base_url=CONST_API_URL)

        token_parameter = 'oauth_consumer_key=key&oauth_signature_method=HMAC-SHA1&oauth_verifier=' + unicode(profile_settings['resource_verifier']) + '&oauth_token={token}&oauth_version=1.0&oauth_timestamp={timestamp}&oauth_nonce={nonce}&count=1&expand=false&expandlist=false&maxResults=1&offset=0'

        url_encoded = api_oauth_encode(type="GET", base_url=token_url_base, parameters=token_parameter)

        download = api_download(url=url_encoded, type='get', headers=None, data=None, json_data=False, return_json=False)
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

def api_login(force=False):
    creds = get_credentials()
    username = creds['username']
    password = creds['password']
    use_old = False

    profile_settings = load_profile(profile_id=1)

    if not check_key(profile_settings, 'base_resource_key') or not check_key(profile_settings, 'base_resource_secret') or len(profile_settings['base_resource_key']) == 0 or len(profile_settings['base_resource_secret']) == 0 or force == True:
        try:
            os.remove(ADDON_PROFILE + 'stream_cookies')
        except:
            pass

        try:
            profile_settings['base_resource_key'] = ''
            profile_settings['base_resource_secret'] = ''
            profile_settings['resource_key'] = ''
            profile_settings['resource_secret'] = ''
            profile_settings['resource_verifier'] = ''
            save_profile(profile_id=1, profile=profile_settings)
        except:
            pass

        request_token_url = '{base_url}/OAuth/GetRequestToken'.format(base_url=CONST_BASE_URL)

        oauth = OAuth1('key', client_secret='secret', callback_uri='null')

        download = api_download(url=request_token_url, type='post', headers=None, data=None, json_data=False, return_json=False, auth=oauth)
        data = download['data']
        code = download['code']

        credentials = parse_qs(data)

        base_resource_owner_key = credentials.get('oauth_token')[0]
        base_resource_owner_secret = credentials.get('oauth_token_secret')[0]

        login_url = '{base_url}/account/applogin'.format(base_url=CONST_BASE_URL)

        session_post_data = {
            "username": username,
            "password": password,
        }

        headers = {
            'content-type': 'application/x-www-form-urlencoded'
        }

        download = api_download(url=login_url, type='post', headers=headers, data=session_post_data, json_data=False, return_json=False)
        data = download['data']
        code = download['code']

        if code != 200 and code != 302:
            return { 'code': code, 'data': data, 'result': False }

        authorization_url = "{base_url}/OAuth/Authorize?oauth_token={token}".format(base_url=CONST_BASE_URL, token=base_resource_owner_key)

        download = api_download(url=authorization_url, type='get', headers=None, data=None, json_data=False, return_json=False, allow_redirects=False)
        data = download['data']
        code = download['code']

        regex = r"oauth_verifier=([a-zA-Z0-9]+)"
        matches = re.finditer(regex, data, re.MULTILINE)

        resource_verifier = ''

        try:
            for match in matches:
               resource_verifier = match.group(1)
        except:
            pass

        if len(resource_verifier) == 0:
            return { 'code': code, 'data': data, 'result': False }
    else:
        use_old = True
        base_resource_owner_key = profile_settings['base_resource_key']
        base_resource_owner_secret = profile_settings['base_resource_secret']
        resource_verifier = profile_settings['resource_verifier']

    access_token_url = '{base_url}/OAuth/GetAccessToken'.format(base_url=CONST_BASE_URL)

    oauth = OAuth1('key', client_secret='secret', callback_uri='null', resource_owner_key=base_resource_owner_key, resource_owner_secret=base_resource_owner_secret, verifier=resource_verifier)

    download = api_download(url=access_token_url, type='post', headers=None, data=None, json_data=False, return_json=False, auth=oauth)
    data = download['data']
    code = download['code']

    credentials = parse_qs(data)

    try:
        resource_owner_key = credentials.get('oauth_token')[0]
        resource_owner_secret = credentials.get('oauth_token_secret')[0]
    except:
        if use_old == True:
            return api_login(force=True)

        return { 'code': code, 'data': data, 'result': False }
    
    try:
        profile_settings['base_resource_key'] = base_resource_owner_key
        profile_settings['base_resource_secret'] = base_resource_owner_secret
        profile_settings['resource_key'] = resource_owner_key
        profile_settings['resource_secret'] = resource_owner_secret
        profile_settings['resource_verifier'] = resource_verifier
        save_profile(profile_id=1, profile=profile_settings)
    except:
            pass

    return { 'code': code, 'data': data, 'result': True }

def api_mix(list1, list2, list3=None):
    if list3:
        i,j,k = iter(list1), iter(list2), iter(list3)
        result = [item for sublist in zip(i,j,k) for item in sublist]
        result += [item for item in i]
        result += [item for item in j]
        result += [item for item in k]
    else:
        i,j = iter(list1), iter(list2)
        result = [item for sublist in zip(i,j) for item in sublist]
        result += [item for item in i]
        result += [item for item in j]

    return result

def api_oauth_encode(type, base_url, parameters):
    profile_settings = load_profile(profile_id=1)

    base_url_encode = quote(base_url, safe='')

    nonce = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(6))
    token_timestamp = int(time.time())

    parameters = parameters.format(token=profile_settings['resource_key'], timestamp=token_timestamp, nonce=nonce)

    parsed_parameters = parse_qs(parameters, keep_blank_values=True)
    encode_string = ''

    for parameter in sorted(parsed_parameters):
        encode_string += quote(unicode(parameter).replace(" ", "%2520") + "=" + unicode(parsed_parameters[parameter][0]).replace(" ", "%2520") + "&", safe='%')

    if encode_string.endswith("%26"):
        encode_string = encode_string[:-len("%26")]

    base_string = '{type}&{token_url_base_encode}&{token_parameter_encode}'.format(type=type, token_url_base_encode=base_url_encode, token_parameter_encode=encode_string)
    base_string_bytes = base_string.encode('utf-8')
    key = 'secret&{key}'.format(key=profile_settings['resource_secret'])
    key_bytes = key.encode('utf-8')

    hashed = hmac.new(key_bytes, base_string_bytes, sha1)
    signature = quote(base64.b64encode(hashed.digest()).decode(), safe='')

    url = '{token_url_base}?{token_parameter}&oauth_signature={signature}'.format(token_url_base=base_url, token_parameter=parameters, signature=signature)

    return url

def api_play_url(type, channel=None, id=None, video_data=None, from_beginning=0, pvr=0):
    playdata = {'path': '', 'license': '', 'info': '', 'alt_path': '', 'alt_license': ''}

    if not api_get_session():
        return playdata

    from_beginning = int(from_beginning)
    pvr = int(pvr)
    profile_settings = load_profile(profile_id=1)

    alt_path = ''
    alt_license = ''
    found_alt = False
    friendly = ''
    info = {}

    data = api_get_channels()

    try:
        friendly = data[unicode(channel)]['assetid']
    except:
        pass

    if not type == 'vod' and (pvr == 0 or settings.getBool(key='ask_start_from_beginning') or from_beginning == 1):
        if type == 'channel' and friendly:
            channel_url = '{base_url}/v6/epg/locations/{friendly}/live/1?fromDate={date}'.format(base_url=CONST_API_URL, friendly=friendly, date=datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S"))

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

        token_url_base = '{base_url}/v6/epg/location/{location}'.format(base_url=CONST_API_URL, location=id)

        token_parameter = 'oauth_token={token}&oauth_consumer_key=key&oauth_signature_method=HMAC-SHA1&oauth_version=1.0&oauth_timestamp={timestamp}&oauth_nonce={nonce}'
        url_encoded = api_oauth_encode(type="GET", base_url=token_url_base, parameters=token_parameter)

        download = api_download(url=url_encoded, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']
        
        if not code or not code == 200 or not data:
            return playdata

        info = data

        timeshift = ''

        if check_key(info, 'VodContentId') and len(unicode(info['VodContentId'])) > 0:
            token_url_base = '{base_url}/v6/stream/handshake/Widevine/dash/VOD/{id}'.format(base_url=CONST_API_URL, id=info['VodContentId'])
            timeshift = info['VodContentId']

            token_parameter = 'oauth_token={token}&oauth_consumer_key=key&oauth_signature_method=HMAC-SHA1&playerName=NLZIET%20Meister%20Player%20Web&profile=default&maxResolution=&timeshift=' + unicode(timeshift) + '&oauth_version=1.0&oauth_timestamp={timestamp}&oauth_nonce={nonce}'
            url_encoded = api_oauth_encode(type="GET", base_url=token_url_base, parameters=token_parameter)

            download = api_download(url=url_encoded, type='get', headers=None, data=None, json_data=False, return_json=True)
            data = download['data']
            code = download['code']

            if not code or not code == 200 or not data or not check_key(data, 'uri'):
                pass
            else:
                alt_license = data
                alt_path = data['uri']
                found_alt = True

        elif type == 'channel' and channel and friendly:
            token_url_base = '{base_url}/v6/stream/handshake/Widevine/dash/Restart/{id}'.format(base_url=CONST_API_URL, id=id)
            timeshift = 'false'

            token_parameter = 'oauth_token={token}&oauth_consumer_key=key&oauth_signature_method=HMAC-SHA1&playerName=NLZIET%20Meister%20Player%20Web&profile=default&maxResolution=&timeshift=' + unicode(timeshift) + '&oauth_version=1.0&oauth_timestamp={timestamp}&oauth_nonce={nonce}'
            url_encoded = api_oauth_encode(type="GET", base_url=token_url_base, parameters=token_parameter)

            download = api_download(url=url_encoded, type='get', headers=None, data=None, json_data=False, return_json=True)
            data = download['data']
            code = download['code']

            if not code or not code == 200 or not data or not check_key(data, 'uri'):
                pass
            else:
                alt_license = data
                alt_path = data['uri']
                found_alt = True

    if type == 'vod':
        token_url_base = '{base_url}/v6/playnow/ondemand/0/{location}'.format(base_url=CONST_API_URL, location=id)

        token_parameter = 'oauth_token={token}&oauth_consumer_key=key&oauth_signature_method=HMAC-SHA1&oauth_version=1.0&oauth_timestamp={timestamp}&oauth_nonce={nonce}'
        url_encoded = api_oauth_encode(type="GET", base_url=token_url_base, parameters=token_parameter)

        download = api_download(url=url_encoded, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'VideoInformation'):
            return playdata

        info = data['VideoInformation']
        token_url_base = '{base_url}/v6/stream/handshake/Widevine/dash/VOD/{id}'.format(base_url=CONST_API_URL, id=info['Id'])
        timeshift = info['Id']
    elif type == 'channel' and channel and friendly:
        token_url_base = '{base_url}/v6/stream/handshake/Widevine/dash/Live/{friendly}'.format(base_url=CONST_API_URL, friendly=friendly)
        timeshift = 'false'
    else:
        if len(unicode(alt_path)) == 0:
            token_url_base = '{base_url}/v6/stream/handshake/Widevine/dash/Replay/{id}'.format(base_url=CONST_API_URL, id=id)
            timeshift = id
        else:
            license = alt_license = data
            path = alt_path
            alt_license = ''
            alt_path = ''

    if not type == 'program' or found_alt == False:
        token_parameter = 'oauth_token={token}&oauth_consumer_key=key&oauth_signature_method=HMAC-SHA1&playerName=NLZIET%20Meister%20Player%20Web&profile=default&maxResolution=&timeshift=' + unicode(timeshift) + '&oauth_version=1.0&oauth_timestamp={timestamp}&oauth_nonce={nonce}'
        url_encoded = api_oauth_encode(type="GET", base_url=token_url_base, parameters=token_parameter)

        download = api_download(url=url_encoded, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'uri'):
            return playdata

        license = data
        path = data['uri']

    if not len(unicode(license)) > 0:
        return playdata

    playdata = {'path': path, 'license': license, 'info': info, 'alt_path': alt_path, 'alt_license': alt_license}

    return playdata

def api_process_vod(data):
    data = api_mix(data['Items']['npo'], data['Items']['rtl'], data['Items']['sbs'])

    items = []

    for row in data:
        item = {}

        if not check_key(row, 'Type'):
            continue

        if row['Type'] == 'Vod':
            key = 'VideoTile'
        elif row['Type'] == 'Epg':
            key = 'EpgTile'
        elif row['Type'] == 'Serie':
            key = 'SerieTile'
        else:
            continue

        if not check_key(row, key):
            continue

        entry = row[key]

        if not check_key(entry, 'Id') or (not check_key(entry, 'Titel') and (not check_key(entry, 'Serie') or not check_key(entry['Serie'], 'Titel'))):
            continue

        id = entry['Id']
        basetitle = ''
        desc = ''
        start = ''
        duration = 0
        image = ''

        if check_key(entry, 'Serie') and check_key(entry['Serie'], 'Titel'):
            basetitle = entry['Serie']['Titel']

        if check_key(entry, 'Titel'):
            if len(entry['Titel']) > 0 and basetitle != entry['Titel']:
                if len(basetitle) > 0:
                    basetitle += ": " + entry['Titel']
                else:
                    basetitle = entry['Titel']

        if check_key(entry, 'Omschrijving'):
            desc = entry['Omschrijving']

        if check_key(entry, 'Duur'):
            duration = entry['Duur']

        if check_key(entry, 'AfbeeldingUrl'):
            image = entry['AfbeeldingUrl']

            if not 'http' in image:
                image_split = image.rsplit('/', 1)

                if len(image_split) == 2:
                    image = '{image_url}/thumbnails/hd1080/{image}'.format(image_url=CONST_IMAGE_URL, image=image.rsplit('/', 1)[1])
                else:
                    image = '{image_url}/{image}'.format(image_url=CONST_IMAGE_URL, image=image)

        if check_key(entry, 'Uitzenddatum'):
            start = entry['Uitzenddatum']

        item['id'] = id
        item['title'] = basetitle
        item['description'] = desc
        item['duration'] = duration
        item['type'] = row['Type']
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
    type = unicode(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        search_url = '{base_url}/v6/search/v2/combined?searchterm={query}&maxSerieResults=99999999&maxVideoResults=99999999&expand=true&expandlist=true'.format(base_url=CONST_API_URL, query=query)

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
                        image = '{image_url}/thumbnails/hd1080/{image}'.format(image_url=CONST_IMAGE_URL, image=image.rsplit('/', 1)[1])
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
                type = 'VideoTile'
            elif row['Video']['VideoType'] == 'Replay':
                type = 'EpgTile'
            elif row['Video']['VideoType'] == 'Serie':
                type = 'SerieTile'
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
                        image = '{image_url}/thumbnails/hd1080/{image}'.format(image_url=CONST_IMAGE_URL, image=image.rsplit('/', 1)[1])
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
    if unicode(element['seriesNumber']).isnumeric():
        return int(element['seriesNumber'])
    else:
        matches = re.findall(r"Seizoen (\d+)", element['seriesNumber'])

        for match in matches:
            return int(match)

        return 0

def api_vod_download(type, start=0):
    if not api_get_session():
        return None

    if type == "movies":
        url = '{base_url}/v6/tabs/GenreFilms?count=52&expand=true&expandlist=true&maxResults=52&offset={start}'.format(base_url=CONST_API_URL, start=start)
    elif type == "watchahead":
        url = '{base_url}/v6/tabs/VooruitKijken2?count=52&expand=true&expandlist=true&maxResults=52&offset={start}'.format(base_url=CONST_API_URL, start=start)
    elif type == "seriesbinge":
        url = '{base_url}/v6/tabs/SeriesBingewatch?count=52&expand=true&expandlist=true&maxResults=52&offset={start}'.format(base_url=CONST_API_URL, start=start)
    elif type == "mostviewed":
        url = '{base_url}/v6/tabs/MostViewed?count=52&expand=true&expandlist=true&maxResults=52&offset={start}'.format(base_url=CONST_API_URL, start=start)
    elif type == "tipfeed":
        url = '{base_url}/v6/tabs/Tipfeed?count=52&expand=true&expandlist=true&maxResults=52&offset={start}'.format(base_url=CONST_API_URL, start=start)
    else:
        return None

    type = "vod_" + type + "_" + unicode(start)
    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = unicode(encodedBytes, "utf-8")

    file = "cache" + os.sep + type + ".json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)

    if not data or not check_key(data, 'Items'):
        return None

    return api_process_vod(data=data)

def api_vod_season(series, id):
    if not api_get_session():
        return None

    season = []

    program_url = '{base_url}/v6/series/{series}/seizoenItems?seizoenId={id}&count=99999999&expand=true&expandlist=true&maxResults=99999999&offset=0'.format(base_url=CONST_API_URL, series=series, id=id)

    type = "vod_series_" + unicode(series) + "_season_" + unicode(id)
    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = unicode(encodedBytes, "utf-8")

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

        if check_key(row, 'AfleveringTitel') and len(row['AfleveringTitel']) > 0:
            episodeTitle = row['AfleveringTitel']
        else:
            episodeTitle = row['ProgrammaTitel']

        if check_key(row, 'Duur'):
            duration = row['Duur']

        if check_key(row, 'ContentId'):
            ep_id = row['ContentId']

        if check_key(row, 'ProgrammaOmschrijving'):
            desc = row['ProgrammaOmschrijving']

        if check_key(row, 'ProgrammaAfbeelding'):
            image = row['ProgrammaAfbeelding']

            if not 'http' in image:
                image_split = image.rsplit('/', 1)

                if len(image_split) == 2:
                    image = '{image_url}/thumbnails/hd1080/{image}'.format(image_url=CONST_IMAGE_URL, image=image.rsplit('/', 1)[1])
                else:
                    image = '{image_url}/{image}'.format(image_url=CONST_IMAGE_URL, image=image)

        if check_key(row, 'Uitzenddatum'):
            start = row['Uitzenddatum']
            startT = datetime.datetime.fromtimestamp(time.mktime(time.strptime(start, "%Y-%m-%dT%H:%M:%S")))
            startT = convert_datetime_timezone(startT, "UTC", "UTC")

            if xbmc.getLanguage(xbmc.ISO_639_1) == 'nl':
                label += '{weekday} {day} {month} {yearhourminute} '.format(weekday=date_to_nl_dag(startT), day=startT.strftime("%d"), month=date_to_nl_maand(startT), yearhourminute=startT.strftime("%Y %H:%M"))
            else:
                label += startT.strftime("%A %d %B %Y %H:%M ").capitalize()

        if check_key(row, 'SeizoenVolgnummer'):
            label += unicode(row['SeizoenVolgnummer'])

        if check_key(row, 'AfleveringVolgnummer'):
            if len(label) > 0:
                label += "."

            label += unicode(row['AfleveringVolgnummer'])

        if len(label) > 0:
            label += " - "

        label += episodeTitle

        season.append({'label': label, 'id': ep_id, 'start': start, 'duration': duration, 'title': episodeTitle, 'seasonNumber': row['SeizoenVolgnummer'], 'episodeNumber': row['AfleveringVolgnummer'], 'description': desc, 'image': image})

    season[:] = sorted(season, key=api_sort_episodes)

    return season

def api_vod_seasons(type, id):
    if not api_get_session():
        return None

    seasons = []

    program_url = '{base_url}/v6/series/{id}/fullWithSeizoenen?count=99999999&expand=true&expandlist=true&maxResults=99999999&offset=0'.format(base_url=CONST_API_URL, id=id)

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

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)

    if not data or not check_key(data, 'Serie'):
        return None

    season_count = 0
    type = 'seasons'

    if check_key(data, 'SeizoenenForSerie'):
        for row in data['SeizoenenForSerie']:
            season_count += 1

            seasons.append({'id': row['SeizoenId'], 'seriesNumber': row['Titel'], 'description': data['Serie']['Omschrijving'], 'image': data['Serie']['ProgrammaAfbeelding']})

    if check_key(data, 'ItemsForSeizoen') and season_count < 2:
        seasons = []
        type = 'episodes'

        for row in data['ItemsForSeizoen']:
            duration = 0
            ep_id = ''
            desc = ''
            image = ''
            start = ''
            label = ''

            if check_key(row, 'AfleveringTitel'):
                episodeTitle = row['AfleveringTitel']
            else:
                episodeTitle = row['ProgrammaTitel']

            if check_key(row, 'Duur'):
                duration = row['Duur']

            if check_key(row, 'ContentId'):
                ep_id = row['ContentId']

            if check_key(row, 'ProgrammaOmschrijving'):
                desc = row['ProgrammaOmschrijving']

            if check_key(row, 'ProgrammaAfbeelding'):
                image = row['ProgrammaAfbeelding']

                if not 'http' in image:
                    image_split = image.rsplit('/', 1)

                    if len(image_split) == 2:
                        image = '{image_url}/thumbnails/hd1080/{image}'.format(image_url=CONST_IMAGE_URL, image=image.rsplit('/', 1)[1])
                    else:
                        image = '{image_url}/{image}'.format(image_url=CONST_IMAGE_URL, image=image)

            if check_key(row, 'Uitzenddatum'):
                start = row['Uitzenddatum']

            if check_key(row, 'SeizoenVolgnummer'):
                label += unicode(row['SeizoenVolgnummer'])

            if check_key(row, 'AfleveringVolgnummer'):
                if len(label) > 0:
                    label += "."

                label += unicode(row['AfleveringVolgnummer'])

            if len(label) > 0:
                label += " - "

            label += episodeTitle

            seasons.append({'label': label, 'id': ep_id, 'start': start, 'duration': duration, 'title': episodeTitle, 'seasonNumber': row['SeizoenVolgnummer'], 'episodeNumber': row['AfleveringVolgnummer'], 'description': desc, 'image': image})

    if type == 'seasons':
        seasons[:] = sorted(seasons, key=api_sort_season)
    elif type == 'episodes':
        seasons[:] = sorted(seasons, key=api_sort_episodes)

    return {'program': data['Serie'], 'type': type, 'seasons': seasons}

def api_watchlist_listing():
    return None