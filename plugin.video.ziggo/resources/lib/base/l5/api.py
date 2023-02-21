import base64
import json
import os
import shutil
from collections import OrderedDict

import xbmc

from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile

from resources.lib.base.l1.constants import (ADDON_PROFILE, ADDONS_PATH,
                                             CONST_DUT_EPG, CONST_DUT_EPG_BASE,
                                             SESSION_CHUNKSIZE)
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.util import (check_key, clear_cache, encode32,
                                        extract_zip, is_file_older_than_x_days,
                                        load_file, load_profile, update_prefs,
                                        write_file)
from resources.lib.base.l4.session import Session
from resources.lib.constants import CONST_MOD_CACHE


def api_download(url, type, headers=None, data=None, json_data=True, return_json=True, allow_redirects=True, auth=None):
    session = Session(cookies_key='cookies')

    if headers:
        session.headers = headers

    if type == "post" and data:
        if json_data:
            resp = session.post(url, json=data, allow_redirects=allow_redirects, auth=auth)
        else:
            resp = session.post(url, data=data, allow_redirects=allow_redirects, auth=auth)
    else:
        resp = getattr(session, type)(url, allow_redirects=allow_redirects, auth=auth)

    if return_json:
        try:
            returned_data = json.loads(resp.json().decode('utf-8'), object_pairs_hook=OrderedDict)
        except:
            try:
                returned_data = resp.json(object_pairs_hook=OrderedDict)
            except:
                returned_data = resp.text
    else:
        returned_data = resp.text

    session.close()

    return { 'code': resp.status_code, 'data': returned_data, 'headers': resp.headers, 'url': resp.url }

def api_get_channels():
    channels_url = '{dut_epg_url}/channels.json'.format(dut_epg_url=CONST_DUT_EPG)
    file = os.path.join("cache", "channels.json")

    if check_key(CONST_MOD_CACHE, 'channels'):
        days = CONST_MOD_CACHE['channels']
    else:
        days = 1

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=days):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=channels_url, type='get', headers=None, data=None, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)
            update_prefs(profile_id=1, channels=data)
        else:
            return None

        clear_cache()

    data2 = OrderedDict()

    for currow in data:
        row = data[currow]
        data2[currow] = row

    return data2

def api_get_epg_by_date_channel(date, channel):
    type = '{date}_{channel}'.format(date=date, channel=channel)

    if check_key(CONST_MOD_CACHE, str(type)):
        days = CONST_MOD_CACHE[str(type)]
    else:
        days = 0.5

    type = encode32(txt=type)

    cache_path = full_path = os.path.join("cache", ADDON_PROFILE)
    epg_url = '{dut_epg_url}/list.zip'.format(dut_epg_url=CONST_DUT_EPG, type=type)
    file = os.path.join("cache", "{type}.json".format(type=type))

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=days):
        data = load_file(file=file, isJSON=True)

    else:
        full_path = os.path.join(cache_path, "list.zip")
        http_response = urlopen(epg_url)
        zipfile = ZipFile(BytesIO(http_response.read()))
        zipfile.extractall(path=full_path)

    return data

def api_get_epg_by_idtitle(idtitle, start, end, channels):
    type = str(idtitle)

    if check_key(CONST_MOD_CACHE, str(type)):
        days = CONST_MOD_CACHE[str(type)]
    else:
        days = 0.5

    type = encode32(txt=type)

    epg_url = '{dut_epg_url}/{type}.json'.format(dut_epg_url=CONST_DUT_EPG, type=type)
    file = os.path.join("cache", "{type}.json".format(type=type))

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=days):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=epg_url, type='get', headers=None, data=None, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)
        else:
            return None

    data2 = OrderedDict()

    for currow in data:
        row = data[currow]

        try:
            if int(row['start']) > start or int(row['end']) < end:
                continue
        except:
            pass

        if not row['channel'] in channels:
            continue

        data2[currow] = row

    return data2

def api_get_genre_list(type, add=1):
    add = int(add)

    if not os.path.isdir(os.path.join(ADDON_PROFILE, 'tmp')):
        os.makedirs(os.path.join(ADDON_PROFILE, 'tmp'))

    if add == 1:
        type = type + 'genres'      

    type = encode32(txt=type)

    genres_url = '{dut_epg_url}/{type}.json'.format(dut_epg_url=CONST_DUT_EPG, type=type)
    file = os.path.join("cache", "{type}.json".format(type=type))

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=genres_url, type='get', headers=None, data=None, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)
        else:
            return None

    return data

def api_get_list(start, end, channels, movies=0):
    if not os.path.isdir(os.path.join(ADDON_PROFILE, 'tmp')):
        os.makedirs(os.path.join(ADDON_PROFILE, 'tmp'))

    list_url = '{dut_epg_url}/list.zip'.format(dut_epg_url=CONST_DUT_EPG)
    tmp = os.path.join(ADDON_PROFILE, 'tmp', 'list.zip')
    
    if movies == 1:
        file = os.path.join("cache", "list_movies.json")
    else:
        file = os.path.join("cache", "list.json")

    if check_key(CONST_MOD_CACHE, 'list'):
        days = CONST_MOD_CACHE['list']
    else:
        days = 0.5

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=days):
        data3 = load_file(file=file, isJSON=True)
    else:
        resp = Session().get(list_url, stream=True)

        if resp.status_code != 200:
            resp.close()
            return None

        with open(tmp, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=SESSION_CHUNKSIZE):
                f.write(chunk)

        resp.close()

        if not extract_zip(file=tmp, dest=os.path.join(ADDON_PROFILE, "cache", "")):
            return None
        else:
            data3 = load_file(file=file, isJSON=True)

    data2 = OrderedDict()

    for currow2 in data3:
        data = data3[currow2]

        for currow in data:
            row = data[currow]
            
            try:
                if not int(row['startl']) < start or not int(row['starth']) > end:
                    continue
            except:
                pass

            try:
                found = False

                for station in row['channels']:
                    if station in channels:
                        found = True
                        break

                if found == False:
                    continue
            except:
                pass

            data2[currow] = row

    return data2

def api_get_list_by_first(first, start, end, channels, movies=False):
    if not os.path.isdir(os.path.join(ADDON_PROFILE, 'tmp')):
        os.makedirs(os.path.join(ADDON_PROFILE, 'tmp'))

    list_url = '{dut_epg_url}/list.zip'.format(dut_epg_url=CONST_DUT_EPG)
    tmp = os.path.join(ADDON_PROFILE, 'tmp', 'list.zip')
    
    if movies == True:
        file = os.path.join("cache", "list_movies.json")
    else:
        file = os.path.join("cache", "list.json")

    if check_key(CONST_MOD_CACHE, 'list'):
        days = CONST_MOD_CACHE['list']
    else:
        days = 0.5

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=days):
        data = load_file(file=file, isJSON=True)
    else:
        resp = Session().get(list_url, stream=True)

        if resp.status_code != 200:
            resp.close()
            return None

        with open(tmp, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=SESSION_CHUNKSIZE):
                f.write(chunk)

        resp.close()

        if not extract_zip(file=tmp, dest=os.path.join(ADDON_PROFILE, "cache", "")):
            return None
        else:
            data = load_file(file=file, isJSON=True)

    data2 = OrderedDict()

    try:
        data = data[str(first)]
    except:
        data = []

    for currow in data:
        row = data[currow]

        try:
            if not int(row['startl']) < start or not int(row['starth']) > end:
                continue
        except:
            pass

        try:
            found = False

            for station in row['channels']:
                if station in channels:
                    found = True
                    break

            if found == False:
                continue
        except:
            pass

        data2[currow] = row

    return data2

def api_get_series_nfo():
    type = 'seriesnfo'
    type = encode32(txt=type)

    vod_url = '{dut_epg_url}/{type}.zip'.format(dut_epg_url=CONST_DUT_EPG, type=type)
    file = os.path.join("cache", "{type}.json".format(type=type))
    tmp = os.path.join(ADDON_PROFILE, 'tmp', "{type}.zip".format(type=type))

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=0.45):
        data = load_file(file=file, isJSON=True)
    else:
        resp = Session().get(vod_url, stream=True)

        if resp.status_code != 200:
            resp.close()
            return None

        with open(tmp, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=SESSION_CHUNKSIZE):
                f.write(chunk)

        resp.close()
        extract_zip(file=tmp, dest=os.path.join(ADDON_PROFILE, "cache", ""))

def api_get_vod_by_type(type, character, genre, subscription_filter, menu=0):
    menu = int(menu)

    if not os.path.isdir(os.path.join(ADDON_PROFILE, 'tmp')):
        os.makedirs(os.path.join(ADDON_PROFILE, 'tmp'))

    if check_key(CONST_MOD_CACHE, str(type)):
        days = CONST_MOD_CACHE[str(type)]
    else:
        days = 0.5

    type = encode32(txt=type)

    vod_url = '{dut_epg_url}/{type}.zip'.format(dut_epg_url=CONST_DUT_EPG, type=type)
    file = os.path.join("cache", "{type}.json".format(type=type))
    tmp = os.path.join(ADDON_PROFILE, 'tmp', "{type}.zip".format(type=type))

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=days):
        data = load_file(file=file, isJSON=True)
    else:
        resp = Session().get(vod_url, stream=True)

        if resp.status_code != 200:
            resp.close()
            return None

        with open(tmp, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=SESSION_CHUNKSIZE):
                f.write(chunk)

        resp.close()

        if not extract_zip(file=tmp, dest=os.path.join(ADDON_PROFILE, "cache", "")):
            return None
        else:
            data = load_file(file=file, isJSON=True)

    if menu == 1:
        return data

    data2 = OrderedDict()

    for currow in data:
        row = data[currow]

        id = row['id']
        
        if genre and genre.startswith('C') and genre[1:].isnumeric():
            if not row['vidcollection'] or not genre in row['vidcollection']:
                continue
        elif genre:
            if not row['category'] or not genre in row['category']:
                continue

        if character:
            if not row['first'] == character:
                continue

        if subscription_filter and not int(id) in subscription_filter:
            continue

        data2[currow] = row

    return data2