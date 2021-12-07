import base64, shutil, os, json, xbmc

from collections import OrderedDict
from resources.lib.base.l1.constants import ADDON_PROFILE, ADDONS_PATH, CONST_DUT_EPG_BASE, CONST_DUT_EPG, SESSION_CHUNKSIZE
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.util import check_key, clear_cache, fixBadZipfile, is_file_older_than_x_days, load_file, load_profile, update_prefs, write_file
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
    file = "cache" + os.sep + "channels.json"

    if check_key(CONST_MOD_CACHE, 'channels'):
        days = CONST_MOD_CACHE['channels']
    else:
        days = 1

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=days):
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

    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    epg_url = '{dut_epg_url}/{type}.json'.format(dut_epg_url=CONST_DUT_EPG, type=type)
    file = "cache" + os.sep + "{type}.json".format(type=type)

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=days):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=epg_url, type='get', headers=None, data=None, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)
        else:
            return None

    return data

def api_get_epg_by_idtitle(idtitle, start, end, channels):
    type = '{idtitle}'.format(idtitle=idtitle)

    if check_key(CONST_MOD_CACHE, str(type)):
        days = CONST_MOD_CACHE[str(type)]
    else:
        days = 0.5

    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    epg_url = '{dut_epg_url}/{type}.json'.format(dut_epg_url=CONST_DUT_EPG, type=type)
    file = "cache" + os.sep + "{type}.json".format(type=type)

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=days):
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

    if not os.path.isdir(ADDON_PROFILE + 'tmp'):
        os.makedirs(ADDON_PROFILE + 'tmp')

    if add == 1:
        type = type + 'genres'      

    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    genres_url = '{dut_epg_url}/{type}.json'.format(dut_epg_url=CONST_DUT_EPG, type=type)
    file = "cache" + os.sep + "{type}.json".format(type=type)

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
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
    if not os.path.isdir(ADDON_PROFILE + 'tmp'):
        os.makedirs(ADDON_PROFILE + 'tmp')

    list_url = '{dut_epg_url}/list.zip'.format(dut_epg_url=CONST_DUT_EPG)
    tmp = ADDON_PROFILE + 'tmp' + os.sep + 'list.zip'
    
    if movies == 1:
        file = "cache" + os.sep + "list_movies.json"
    else:
        file = "cache" + os.sep + "list.json"

    if check_key(CONST_MOD_CACHE, 'list'):
        days = CONST_MOD_CACHE['list']
    else:
        days = 0.5

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=days):
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

        if os.path.isfile(tmp):
            from zipfile import ZipFile

            try:
                with ZipFile(tmp, 'r') as zipObj:
                    zipObj.extractall(ADDON_PROFILE + "cache" + os.sep)
            except:
                try:
                    fixBadZipfile(tmp)

                    with ZipFile(tmp, 'r') as zipObj:
                        zipObj.extractall(ADDON_PROFILE + "cache" + os.sep)
                except:
                    try:
                        from resources.lib.base.l1.zipfile import ZipFile as ZipFile2

                        with ZipFile2(tmp, 'r') as zipObj:
                            zipObj.extractall(ADDON_PROFILE + "cache" + os.sep)
                    except:
                        return None

            if os.path.isfile(ADDON_PROFILE + file):
                data3 = load_file(file=file, isJSON=True)
            else:
                return None
        else:
            return None

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
    if not os.path.isdir(ADDON_PROFILE + 'tmp'):
        os.makedirs(ADDON_PROFILE + 'tmp')

    list_url = '{dut_epg_url}/list.zip'.format(dut_epg_url=CONST_DUT_EPG)
    tmp = ADDON_PROFILE + 'tmp' + os.sep + 'list.zip'
    
    if movies == True:
        file = "cache" + os.sep + "list_movies.json"
    else:
        file = "cache" + os.sep + "list.json"

    if check_key(CONST_MOD_CACHE, 'list'):
        days = CONST_MOD_CACHE['list']
    else:
        days = 0.5

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=days):
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

        if os.path.isfile(tmp):
            from zipfile import ZipFile

            try:
                with ZipFile(tmp, 'r') as zipObj:
                    zipObj.extractall(ADDON_PROFILE + "cache" + os.sep)
            except:
                try:
                    fixBadZipfile(tmp)

                    with ZipFile(tmp, 'r') as zipObj:
                        zipObj.extractall(ADDON_PROFILE + "cache" + os.sep)
                except:
                    try:
                        from resources.lib.base.l1.zipfile import ZipFile as ZipFile2

                        with ZipFile2(tmp, 'r') as zipObj:
                            zipObj.extractall(ADDON_PROFILE + "cache" + os.sep)
                    except:
                        return None

            if os.path.isfile(ADDON_PROFILE + file):
                data = load_file(file=file, isJSON=True)
            else:
                return None
        else:
            return None

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

def api_get_connector():
    if not os.path.isdir(ADDON_PROFILE + 'tmp'):
        os.makedirs(ADDON_PROFILE + 'tmp')

    connector_url = 'https://dut-iptv.github.io/matrix/plugin.executable.dutiptv/plugin.executable.dutiptv-latest.zip'
    tmp = ADDON_PROFILE + 'tmp' + os.sep + 'connector.zip'
  
    resp = Session().get(connector_url, stream=True)

    if resp.status_code != 200:
        resp.close()
        return None

    with open(tmp, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=SESSION_CHUNKSIZE):
            f.write(chunk)

    resp.close()

    if os.path.isfile(tmp):
        from zipfile import ZipFile

        try:
            with ZipFile(tmp, 'r') as zipObj:
                zipObj.extractall(ADDON_PROFILE + "tmp" + os.sep)
        except:
            try:
                fixBadZipfile(tmp)

                with ZipFile(tmp, 'r') as zipObj:
                    zipObj.extractall(ADDON_PROFILE + "tmp" + os.sep)
            except:
                try:
                    from resources.lib.base.l1.zipfile import ZipFile as ZipFile2

                    with ZipFile2(tmp, 'r') as zipObj:
                        zipObj.extractall(ADDON_PROFILE + "tmp" + os.sep)
                except:
                    return None

        if os.path.isdir(ADDON_PROFILE + "tmp" + os.sep + 'plugin.executable.dutiptv'):
            shutil.move(ADDON_PROFILE + "tmp" + os.sep + 'plugin.executable.dutiptv', ADDONS_PATH + 'plugin.executable.dutiptv')
            
            if os.path.isfile(tmp):
                os.remove(tmp)
                
            return True
    else:
        return None

def api_get_vod_by_type(type, character, genre, subscription_filter, menu=0):
    menu = int(menu)

    if not os.path.isdir(ADDON_PROFILE + 'tmp'):
        os.makedirs(ADDON_PROFILE + 'tmp')

    if check_key(CONST_MOD_CACHE, str(type)):
        days = CONST_MOD_CACHE[str(type)]
    else:
        days = 0.5

    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = str(encodedBytes, "utf-8")

    vod_url = '{dut_epg_url}/{type}.zip'.format(dut_epg_url=CONST_DUT_EPG, type=type)
    file = "cache" + os.sep + "{type}.json".format(type=type)
    tmp = ADDON_PROFILE + 'tmp' + os.sep + "{type}.zip".format(type=type)

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=days):
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

        if os.path.isfile(tmp):
            from zipfile import ZipFile

            try:
                with ZipFile(tmp, 'r') as zipObj:
                    zipObj.extractall(ADDON_PROFILE + "cache" + os.sep)
            except:
                try:
                    fixBadZipfile(tmp)

                    with ZipFile(tmp, 'r') as zipObj:
                        zipObj.extractall(ADDON_PROFILE + "cache" + os.sep)

                except:
                    try:
                        from resources.lib.base.l1.zipfile import ZipFile as ZipFile2

                        with ZipFile2(tmp, 'r') as zipObj:
                            zipObj.extractall(ADDON_PROFILE + "cache" + os.sep)
                    except:
                        return None

            if os.path.isfile(ADDON_PROFILE + file):
                data = load_file(file=file, isJSON=True)
            else:
                return None
        else:
            return None

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