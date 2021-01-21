import base64, os, json, xbmc

from collections import OrderedDict
from resources.lib.base.l1.constants import ADDON_PROFILE, CONST_DUT_EPG_BASE, CONST_DUT_EPG, SESSION_CHUNKSIZE
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.util import change_icon, clear_cache, fixBadZipfile, is_file_older_than_x_days, load_file, load_profile, update_prefs, write_file
from resources.lib.base.l4.session import Session

try:
    unicode
except NameError:
    unicode = str

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

    return { 'code': resp.status_code, 'data': returned_data, 'headers': resp.headers }

def api_get_channels():
    channels_url = '{dut_epg_url}/channels.json'.format(dut_epg_url=CONST_DUT_EPG)
    file = "cache" + os.sep + "channels.json"

    try:
        profile_settings = load_profile(profile_id=1)

        if int(profile_settings['v3']) == 1:
            channels_url = '{dut_epg_url}/channels.v3.json'.format(dut_epg_url=CONST_DUT_EPG)
            file = "cache" + os.sep + "channels.v3.json"
    except:
        pass

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=1):
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

        change_icon()
        clear_cache()

    data2 = OrderedDict()

    for currow in data:
        row = data[currow]
        data2[currow] = row

    return data2

def api_get_epg_by_date_channel(date, channel):
    type = '{date}_{channel}'.format(date=date, channel=channel)

    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = unicode(encodedBytes, "utf-8")

    epg_url = '{dut_epg_url}/{type}.json'.format(dut_epg_url=CONST_DUT_EPG, type=type)
    file = "cache" + os.sep + "{type}.json".format(type=type)

    try:
        profile_settings = load_profile(profile_id=1)

        if int(profile_settings['v3']) == 1:
            epg_url = '{dut_epg_url}/{type}.v3.json'.format(dut_epg_url=CONST_DUT_EPG, type=type)
            file = "cache" + os.sep + "{type}.v3.json".format(type=type)
    except:
        pass

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
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

    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = unicode(encodedBytes, "utf-8")

    epg_url = '{dut_epg_url}/{type}.json'.format(dut_epg_url=CONST_DUT_EPG, type=type)
    file = "cache" + os.sep + "{type}.json".format(type=type)

    try:
        profile_settings = load_profile(profile_id=1)

        if int(profile_settings['v3']) == 1:
            epg_url = '{dut_epg_url}/{type}.v3.json'.format(dut_epg_url=CONST_DUT_EPG, type=type)
            file = "cache" + os.sep + "{type}.v3.json".format(type=type)
    except:
        pass

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
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

def api_get_list(start, end, channels):
    if not os.path.isdir(ADDON_PROFILE + 'tmp'):
        os.makedirs(ADDON_PROFILE + 'tmp')

    list_url = '{dut_epg_url}/list.zip'.format(dut_epg_url=CONST_DUT_EPG)
    tmp = ADDON_PROFILE + 'tmp' + os.sep + 'list.zip'
    file = "cache" + os.sep + "list.json"

    try:
        profile_settings = load_profile(profile_id=1)

        if int(profile_settings['v3']) == 1:
            list_url = '{dut_epg_url}/list.v3.zip'.format(dut_epg_url=CONST_DUT_EPG)
            tmp = ADDON_PROFILE + 'tmp' + os.sep + 'list.v3.zip'
            file = "cache" + os.sep + "list.v3.json"
    except:
        pass

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data3 = load_file(file=file, isJSON=True)
    else:
        resp = Session().get(list_url, stream=True)

        if resp.status_code != 200:
            return None

        with open(tmp, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=SESSION_CHUNKSIZE):
                f.write(chunk)

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
                if not int(row['startl']) < start and not int(row['starth']) > end:
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

def api_get_list_by_first(first, start, end, channels):
    if not os.path.isdir(ADDON_PROFILE + 'tmp'):
        os.makedirs(ADDON_PROFILE + 'tmp')

    list_url = '{dut_epg_url}/list.zip'.format(dut_epg_url=CONST_DUT_EPG)
    tmp = ADDON_PROFILE + 'tmp' + os.sep + 'list.zip'
    file = "cache" + os.sep + "list.json"

    try:
        profile_settings = load_profile(profile_id=1)

        if int(profile_settings['v3']) == 1:
            list_url = '{dut_epg_url}/list.v3.zip'.format(dut_epg_url=CONST_DUT_EPG)
            tmp = ADDON_PROFILE + 'tmp' + os.sep + 'list.v3.zip'
            file = "cache" + os.sep + "list.v3.json"
    except:
        pass

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        resp = Session().get(list_url, stream=True)

        if resp.status_code != 200:
            return None

        with open(tmp, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=SESSION_CHUNKSIZE):
                f.write(chunk)

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

    data = data[unicode(first)]

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

def api_get_vod_by_type(type, character, subscription_filter):
    if not os.path.isdir(ADDON_PROFILE + 'tmp'):
        os.makedirs(ADDON_PROFILE + 'tmp')

    encodedBytes = base64.b32encode(type.encode("utf-8"))
    type = unicode(encodedBytes, "utf-8")

    vod_url = '{dut_epg_url}/{type}.zip'.format(dut_epg_url=CONST_DUT_EPG, type=type)
    file = "cache" + os.sep + "{type}.json".format(type=type)
    tmp = ADDON_PROFILE + 'tmp' + os.sep + "{type}.zip".format(type=type)

    try:
        profile_settings = load_profile(profile_id=1)

        if int(profile_settings['v3']) == 1:
            vod_url = '{dut_epg_url}/{type}.v3.zip'.format(dut_epg_url=CONST_DUT_EPG, type=type)
            file = "cache" + os.sep + "{type}.v3.json".format(type=type)
            tmp = ADDON_PROFILE + 'tmp' + os.sep + "{type}.v3.zip".format(type=type)
    except:
        pass

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=0.5):
        data = load_file(file=file, isJSON=True)
    else:
        resp = Session().get(vod_url, stream=True)

        if resp.status_code != 200:
            return None

        with open(tmp, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=SESSION_CHUNKSIZE):
                f.write(chunk)

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

    for currow in data:
        row = data[currow]

        id = row['id']

        if character:
            if not row['first'] == character:
                continue

        if subscription_filter and not int(id) in subscription_filter:
            continue

        data2[currow] = row

    return data2

def api_get_widevine():
    widevine_url = '{dut_epg_url}/widevine.json'.format(dut_epg_url=CONST_DUT_EPG_BASE)

    file = "cache" + os.sep + "widevine.json"

    if not is_file_older_than_x_days(file=ADDON_PROFILE + file, days=7):
        data = load_file(file=file, isJSON=True)
    else:
        download = api_download(url=widevine_url, type='get', headers=None, data=None, json_data=True, return_json=True)
        data = download['data']
        code = download['code']

        if code and code == 200 and data:
            write_file(file=file, data=data, isJSON=True)
        else:
            return None

    return data