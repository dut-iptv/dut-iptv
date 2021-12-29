import base64, json, os, requests, xbmc

from collections import OrderedDict
from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE, CONST_DUT_EPG_BASE, SESSION_CHUNKSIZE
from resources.lib.base.l2.log import log
from resources.lib.base.l3.util import check_key, fixBadZipfile, is_file_older_than_x_days, load_file, load_profile, write_file
from resources.lib.util import clear_cache_connector

#Included from base.l7.plugin
#api_clean_after_playback
#api_get_info

def api_clean_after_playback(stoptime):
    pass

def api_get_channels():
    directory = os.path.dirname(os.path.join(ADDON_PROFILE, 'tmp', 'a.channels.zip'))

    if not os.path.exists(directory):
        os.makedirs(directory)

    directory = os.path.dirname(os.path.join(ADDON_PROFILE, "cache", "a.channels.json"))

    if not os.path.exists(directory):
        os.makedirs(directory)

    channels_url = '{dut_epg_url}/a.channels.zip'.format(dut_epg_url=CONST_DUT_EPG_BASE)

    file = os.path.join("cache", "a.channels.json")
    tmp = os.path.join(ADDON_PROFILE, 'tmp', 'a.channels.zip')

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=1):
        return True
    else:
        resp = requests.get(channels_url, stream=True)

        if resp.status_code != 200:
            resp.close()
            return False

        with open(tmp, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=SESSION_CHUNKSIZE):
                f.write(chunk)
        
        resp.close()
        
        if os.path.isfile(tmp):
            from zipfile import ZipFile

            try:
                with ZipFile(tmp, 'r') as zipObj:
                    zipObj.extractall(os.path.join(ADDON_PROFILE, "cache", ""))
            except:
                try:
                    fixBadZipfile(tmp)

                    with ZipFile(tmp, 'r') as zipObj:
                        zipObj.extractall(os.path.join(ADDON_PROFILE, "cache", ""))
                except:
                    try:
                        from resources.lib.base.l1.zipfile import ZipFile as ZipFile2

                        with ZipFile2(tmp, 'r') as zipObj:
                            zipObj.extractall(os.path.join(ADDON_PROFILE, "cache", ""))
                    except:
                        return False
        else:
            return False

        clear_cache_connector()

    return True

def api_get_info(id, channel=''):
    pass

def api_get_all_epg():
    updated = False

    profile_settings = load_profile(profile_id=1)

    for x in range(1, 6):
        if check_key(profile_settings, 'addon' + str(x)):
            if len(profile_settings['addon' + str(x)]) > 0:
                if api_get_epg_by_addon(profile_settings['addon' + str(x)].replace('plugin.video.', '')) == True:
                    updated = True

    clear_cache_connector()

    if updated == True:
        return True
    else:
        return False

def api_get_epg_by_addon(addon):
    type = addon[0]
    directory = os.path.dirname(os.path.join(ADDON_PROFILE, 'tmp', 'epg.zip'))

    if not os.path.exists(directory):
        os.makedirs(directory)

    directory = os.path.dirname(os.path.join(ADDON_PROFILE, "cache", str(addon), 'epg.zip'))

    if not os.path.exists(directory):
        os.makedirs(directory)

    epg_url = '{dut_epg_url}/{type}.epg.zip'.format(dut_epg_url=CONST_DUT_EPG_BASE, type=type)
    tmp = os.path.join(ADDON_PROFILE, 'tmp', '{type}.epg.zip'.format(type=type))

    if not is_file_older_than_x_days(file=tmp, days=0.5):
        return False
    else:
        resp = requests.get(epg_url, stream=True)

        if resp.status_code != 200:
            resp.close()
            return False

        with open(tmp, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=SESSION_CHUNKSIZE):
                f.write(chunk)

        resp.close()

        if os.path.isfile(tmp):
            from zipfile import ZipFile

            try:
                with ZipFile(tmp, 'r') as zipObj:
                    zipObj.extractall(os.path.join(ADDON_PROFILE, "cache", str(addon), ""))
            except:
                try:
                    fixBadZipfile(tmp)

                    with ZipFile(tmp, 'r') as zipObj:
                        zipObj.extractall(os.path.join(ADDON_PROFILE, "cache", str(addon), ""))
                except:
                    try:
                        from resources.lib.base.l1.zipfile import ZipFile as ZipFile2

                        with ZipFile2(tmp, 'r') as zipObj:
                            zipObj.extractall(os.path.join(ADDON_PROFILE, "cache", str(addon), ""))
                    except:
                        return False
        else:
            return False

    return True