import base64
import json
import os
import re
import sys
import time
from collections import OrderedDict
from contextlib import suppress
from urllib.parse import parse_qs, quote_plus, urlparse

import requests
import xbmc

from resources.lib.base.l1.constants import (ADDON_ID, ADDON_PROFILE,
                                             ADDONS_PATH, CONST_DUT_EPG,
                                             CONST_DUT_EPG_BASE,
                                             DEFAULT_USER_AGENT,
                                             SESSION_CHUNKSIZE)
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import (check_key, encode32, get_credentials,
                                        is_file_older_than_x_days,
                                        is_file_older_than_x_minutes,
                                        load_file, load_prefs, load_profile,
                                        save_prefs, save_profile,
                                        set_credentials, write_file)
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l4.session import Session
from resources.lib.base.l5.api import (api_download, api_get_channels,
                                       api_get_vod_by_type)
from resources.lib.constants import (CONST_DEFAULT_CLIENTID, CONST_IMAGES,
                                     CONST_URLS, CONST_VOD_CAPABILITY)
from resources.lib.util import get_image, get_play_url, plugin_process_info

#contains note to self: unimportant things that might have reasonable impact on user experience

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
    #log('api_add_to_watchlist')
    
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    if type == "item":
        mediaitems_url = '{listings_url}/{id}'.format(listings_url=CONST_URLS['listings_url'], id=id)
        download = api_download(url=mediaitems_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

        if not code or not code == 200 or not data or not check_key(data, 'mediaGroupId'):
            return False

        id = data['mediaGroupId']

    watchlist_url = '{watchlist_url}/{watchlist_id}/entries/{id}?sharedProfile=true'.format(watchlist_url=CONST_URLS['watchlist_url'], watchlist_id=profile_settings['watchlist_id'], id=id)

    download = api_download(url=watchlist_url, type='post', headers=api_get_headers(), data={"mediaGroup": {'id': id}}, json_data=True, return_json=False)
    data = download['data']
    code = download['code']

    if not code or not code == 204 or not data:
        return False

    #log('api_add_to_watchlist sucess')
    return True

def api_clean_after_playback(stoptime):
    #log('api_clean_after_playback, stoptime {}'.format(stoptime))
    
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    headers = api_get_headers()
    headers['Content-type'] = 'application/json'

    download = api_download(url=CONST_URLS['clearstreams_url'], type='post', headers=headers, data='{}', json_data=False, return_json=False)
    
    #log('api_clean_after_playback sucess')

def api_get_headers():
    creds = get_credentials()
    username = creds['username']

    profile_settings = load_profile(profile_id=1)

    headers = {
        'User-Agent': DEFAULT_USER_AGENT,     
    }

    if check_key(profile_settings, 'ziggo_profile_id') and len(str(profile_settings['ziggo_profile_id'])) > 0:
        headers['X-Profile'] = profile_settings['ziggo_profile_id']

    if check_key(profile_settings, 'access_token') and len(str(profile_settings['access_token'])) > 0:
        headers['Cookie'] = profile_settings['access_token']
        headers['Content-Type'] = 'application/json'

    if len(str(username)) > 0:
        headers['X-OESP-Username'] = username

    return headers

def api_get_info(id, channel=''):
    #log('api_get_info, id {},channel {}'.format(id, channel))
    profile_settings = load_profile(profile_id=1)

    info = {}
    base_listing_url = CONST_URLS['listings_url']

    try:
        listing_url = '{listings_url}?byEndTime={time}~&byStationId={channel}&range=1-1&sort=startTime'.format(listings_url=base_listing_url, time=int(time.time() * 1000), channel=id)
        download = api_download(url=listing_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']
        
        #log('URL {}'.format(listing_url))
        #log('Data {}'.format(data))
        #log('Code {}'.format(code))

        if code and code == 200 and data and check_key(data, 'listings'):
            for row in data['listings']:
                if check_key(row, 'program'):
                    info = row['program']

        info = plugin_process_info({'title': '', 'channel': channel, 'info': info})
    except:
        pass

    #log('api_get_info success')
    return info

def api_get_play_token(locator=None, path=None, play_url=None, force=0):
    log('api_get_play_token, locator {}, path {}, force {}'.format(locator, path, force))
    
    if not api_get_session():
        return None

    force = int(force)

    profile_settings = load_profile(profile_id=1)

    if not locator == profile_settings['drm_locator']:
        pass

    if not check_key(profile_settings, 'drm_token_age') or not check_key(profile_settings, 'tokenrun') or not check_key(profile_settings, 'tokenruntime') or profile_settings['drm_token_age'] < int(time.time() - 50) and (profile_settings['tokenrun'] == 0 or profile_settings['tokenruntime'] < int(time.time() - 30)):
        force = 1

    if not check_key(profile_settings, 'drm_token_age') or not check_key(profile_settings, 'drm_locator') or locator != profile_settings['drm_locator'] or profile_settings['drm_token_age'] < int(time.time() - 90) or force == 1:
        profile_settings['tokenrun'] = 1
        profile_settings['tokenruntime'] = int(time.time())
        save_profile(profile_id=1, profile=profile_settings)

        #if 'sdash' in path:
        #    jsondata = {"contentLocator": locator, "drmScheme": "sdash:BR-AVC-DASH"}
        #else:
        #    jsondata = {"contentLocator": locator}

        creds = get_credentials()
        username = creds['username']

        #payload = json.dumps({
        #    "contentLocator": locator,
        #    "drmScheme": "sdash:BR-AVC-DASH"
        #})

        profile_settings = load_profile(profile_id=1)

        def live_layer():
            #the full if statement
            headers = {
                'User-Agent': DEFAULT_USER_AGENT,
                'X-Profile': profile_settings['ziggo_profile_id'],
                'Cookie': profile_settings['access_token'],
                'X-Entitlements-Token': profile_settings['entitlements_token'],
                'Content-Type': 'application/json',
                'X-OESP-Username': username,
            }
            def inner_layer():
                #the point just before it could go wrong
                str = profile_settings['drm_locator']
                channelid = str[39:-17]
                log(channelid)
                base_session = CONST_URLS['session_url']
                session = '{base}/{hid}/live?assetType=Orion-DASH&channelId={cid}&profileId={id}'.format(base=base_session, hid=profile_settings['household_id'], cid=channelid, id=profile_settings['ziggo_profile_id'])
                log(session)
                download = requests.request("POST", session, headers=headers)
                log('getplaytoken; live sessionurl response: {}'.format(download))
                return download, session
            download = inner_layer()[0]
            session = inner_layer()[1]
            code = download.status_code
            try:
                statuscode = download.json()['error']['statusCode']
            except:
                statuscode = None
            print(download.json(), code, statuscode)
            if code == 200:
                #successful, continue using the token
                contentid = download.json()['drmContentId']
                log("contentid")
                wvtoken = download.headers['x-streaming-token']
                log("wvtoken")
                return contentid, wvtoken
            
            elif code == 404 or code == 405 or statuscode == 7666:
                if 'customers//' in session or session == 'https://prod.spark.ziggogo.tv/eng/web/recording-service/customers//recordings?sort=time&sortOrder=desc':
                    log('getplaytoken; live session error: contains // instead of hid, retrying the request')
                    from resources.lib.base.l4 import gui
                    gui.error(message=_.NOT_FOUND)
                else:
                    log('getplaytoken; live session error: does NOT contain the // but chances are hid is still missing')
                    from resources.lib.base.l4 import gui
                    gui.error(message=_.NOT_FOUND)
            elif code == 403 or statuscode == 1101:
                if statuscode == 1101:
                    from resources.lib.base.l4 import gui
                    gui.error(message=_.SESSION_LIMIT)
                else:
                    from resources.lib.base.l4 import gui
                    gui.error(message=_.LOGIN_ERROR_TITLE)

            else:
                #it went wrong, print code, refresh values and try again
                try:
                    log(download.json())
                except:
                    pass
                api_login()
                live_layer()

        def replay_layer():
            #the full if statement
            headers = {
                'User-Agent': DEFAULT_USER_AGENT,
                'X-Profile': profile_settings['ziggo_profile_id'],
                'Cookie': profile_settings['access_token'],
                'X-Entitlements-Token': profile_settings['entitlements_token'],
                'Content-Type': 'application/json',
                'X-OESP-Username': username,
            }
            def inner_layer():
                #the point just before it could go wrong
                program_id = profile_settings['replay_id']
                base_session = CONST_URLS['session_url']
                session = '{base}/{hid}/replay?eventId={eid}&profileId={id}&abrType=BR-AVC-DASH'.format(base=base_session, hid=profile_settings['household_id'], eid=program_id, id=profile_settings['ziggo_profile_id'])
                log(session)
                download = requests.request("POST", session, headers=headers)
                log('getplaytoken; replay sessionurl response: {}'.format(download))
                return download
            download = inner_layer()
            code = download.status_code
            print(download.json(), code)
            if code == 200:
                #successful, continue using the token
                contentid = download.json()['drmContentId']
                wvtoken = download.headers['x-streaming-token']
                return contentid, wvtoken
            
            elif code == 404:
                from resources.lib.base.l4 import gui
                gui.error(message=_.NOT_FOUND)

            else:
                #it went wrong, print code, refresh values and try again
                try:
                    log(download.json())
                except:
                    pass
                api_login()
                replay_layer()

############ WIP ########################

        def recording_layer():
            #the full if statement
            headers = {
                'User-Agent': DEFAULT_USER_AGENT,
                'X-Profile': profile_settings['ziggo_profile_id'],
                'Cookie': profile_settings['access_token'],
                'X-Entitlements-Token': profile_settings['entitlements_token'],
                'Content-Type': 'application/json',
                'X-OESP-Username': username,
            }
            def inner_layer():
                MAX_ATTEMPTS = 3
                counter = 0
                hid=profile_settings['household_id']
                profid=profile_settings['ziggo_profile_id']
                while True:
                    #the point just before it could go wrong
                    max_id_time = time.time() - 3
                    if profile_settings['time_id'] < max_id_time: #RIF probably not needed and should be stable
                        #time.sleep(1)
                        pass #simply pass because no need to sleep, not sure if it even worked
                    program_id = profile_settings['rec_id']
                    base_rec = CONST_URLS['session_url']
                    rec = '{base}/{hid}/recording?recordingId={recid}&profileId={id}&abrType=BR-AVC-DASH'.format(base=base_rec, hid=hid, recid=program_id, id=profid)
                    log(rec)
                    download = requests.request("POST", rec, headers=headers)
                    log('getplaytoken; recording sessionurl response: {}'.format(download))
                    code = download.status_code

                    if code == 200:
                        data = {'code': download.status_code, 'headers': download.headers, 'body': download.json()}
                        return data
            
                    elif code == 404 or code == 405:
                        if 'customers//' in rec or rec == 'https://prod.spark.ziggogo.tv/eng/web/recording-service/customers//recordings?sort=time&sortOrder=desc':
                            log('getplaytoken; recording session error: contains // instead of hid, retrying the request')
                        else:
                            log('getplaytoken; recording session error: does NOT contain the // but chances are hid is still missing')
                            break
                    counter += 1
                    if counter >= MAX_ATTEMPTS:
                        from resources.lib.base.l4 import gui
                        gui.error(message=_.RECORDINGS_NO_RESPONSE)

                data = {'code': download.status_code, 'headers': download.headers, 'body': download.json()}
                return data
                
            data = inner_layer()
            code = data['code']
            print(code)
            
            if code == 200:
                #successful, continue using the token
                contentid = data['body']['drmContentId']
                wvtoken = data['headers']['x-streaming-token']
                playurl = data['body']['url']
                return contentid, wvtoken, playurl

            elif code == 404:
                from resources.lib.base.l4 import gui
                gui.error(message=_.NOT_FOUND)

            else:
                #it went wrong, print code, refresh values and try again
                try:
                    log(data)
                except:
                    pass
                api_login()
                inner_layer()

############ WIP ########################

        def search_layer():
            #the full if statement
            headers = {
                'User-Agent': DEFAULT_USER_AGENT,
                'X-Profile': profile_settings['ziggo_profile_id'],
                'Cookie': profile_settings['access_token'],
                'X-Entitlements-Token': profile_settings['entitlements_token'],
                'Content-Type': 'application/json',
                'X-OESP-Username': username,
            }
            def inner_layer():
                #the point just before it could go wrong
                program_id = profile_settings['search_id']
                base_session = CONST_URLS['session_url']
                session = '{base}/{hid}/replay?eventId={eventid}&profileId={id}&abrType=BR-AVC-DASH'.format(base=base_session, hid=profile_settings['household_id'], eventid=program_id, id=profile_settings['ziggo_profile_id'])
                log(session)
                download = requests.request("POST", session, headers=headers)
                log('getplaytoken; search/replay sessionurl response: {}'.format(download))
                return download
            download = inner_layer()
            code = download.status_code
            print(download.json(), code)
            if code == 200:
                #successful, continue using the token
                contentid = download.json()['drmContentId']
                wvtoken = download.headers['x-streaming-token']
                return contentid, wvtoken

            elif code == 404:
                from resources.lib.base.l4 import gui
                gui.error(message=_.NOT_FOUND)

            else:
                #it went wrong, print code, refresh values and try again
                try:
                    log(download.json())
                except:
                    pass
                api_login()
                search_layer()

        if profile_settings['detect_replay'] == 0:
            #if live_tv
            log("live")
            func = live_layer()
            contentid = func[0]
            wvtoken = func[1]
        
        if profile_settings['detect_replay'] == 1:
            #if replay_tv
            log("replay")
            func = replay_layer()
            contentid = func[0]
            wvtoken = func[1]

        if profile_settings['detect_replay'] == 2:
            #if searched/replay_tv
            log("searched/replay")
            func = search_layer()
            contentid = func[0]
            wvtoken = func[1]

############ WIP ############

        if profile_settings['detect_replay'] == 3:
        #if recorded_tv
            log("recordings")
            func = recording_layer()
            contentid = func[0]
            wvtoken = func[1]
            url = func[2]

############ WIP ############

        #log('URL {}'.format(CONST_URLS['token_url']))
        #log('Data {}'.format(data))
        
        if profile_settings['detect_replay'] == 3 or locator == 'recording':
            locator == 'recording'
        elif not locator == profile_settings['drm_locator']:
            return False

        log(contentid)
        log(locator)

        profile_settings['contentid'] = contentid
        profile_settings['tokenrun'] = 0
        profile_settings['drm_path'] = path
        profile_settings['drm_token'] = wvtoken
        write_file(file='widevine_token', data=wvtoken, isJSON=False)
        profile_settings['drm_token_age'] = int(time.time())
        profile_settings['drm_locator'] = locator
        if profile_settings['detect_replay'] == 3:
            profile_settings['play_url'] = url
            write_file(file='play_url', data=url, isJSON=False)
            save_profile(profile_id=1, profile=profile_settings)
            return wvtoken, url
        else:
            save_profile(profile_id=1, profile=profile_settings)

        #log('api_get_play_token success')
        return wvtoken
    else:
        #log('api_get_play_token success')
        return profile_settings['drm_token']

def api_get_session(force=0, return_data=False):
    #log('api_get_session, force {}, return_data {}'.format(force, return_data))
    force = int(force)
    profile_settings = load_profile(profile_id=1)

    if not 'last_login_success' in profile_settings:
        profile_settings['last_login_success'] = 0
        save_profile(profile_id=1, profile=profile_settings)

    if force==0 and return_data == False and profile_settings['last_login_success'] == 1 and int(profile_settings['last_login_time']) + 3600 > int(time.time()):
        log('api_get_session skipping')       
        return True

    base_cust = CONST_URLS['customer_url']
    cust_url = '{base}/{hid}?with=profiles,devices'.format(base=base_cust, hid=profile_settings['household_id'])
    download = api_download(url=cust_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    #log('Data {}'.format(data))
    log('Session Code {}'.format(code))

    if code and code == 503:
        log('api_get_session code 503, skipping')    
        pass

    elif not code or not code == 200 or not data:
        log('api_login call from api_get_session')
        login_result = api_login()

        if not login_result['result']:
            log('login_result: api_login did not return result!')
            if return_data == True:
                log('login_result: but api_login did return data!')     #note to self: doesnt return_data apply to this function? not the api_login function, so this is pointless
                return {'result': False, 'data': login_result['data'], 'code': login_result['code']} #note to self: never calls itself again, so user needs to ignore error and retry themselves
            log('login_result: neither did api_login return any data!!! (this is bad)')     #note to self part 2: but you dont want to loop it forever when theres some other problem, either
            return False

    profile_settings = load_profile(profile_id=1)
    profile_settings['last_login_success'] = 1
    profile_settings['last_login_time'] = int(time.time())
    save_profile(profile_id=1, profile=profile_settings)

    if return_data == True:
        return {'result': True, 'data': data, 'code': code}

    #log('api_get_session success')

    return True

def api_get_profiles():
    #log('api_get_profiles')
    #log('api_get_profiles success')
    return None

def api_get_watchlist_id():
    #log('api_get_watchlist_id')
    
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    watchlist_url = '{watchlist_url}/profile/{profile_id}/extended?sort=ADDED&order=DESC&language=nl&maxResults=1&sharedProfile=true'.format(watchlist_url=CONST_URLS['watchlist_url'], profile_id=profile_settings['ziggo_profile_id'])
    #log('URL {}'.format(watchlist_url))
    
    download = api_download(url=watchlist_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']
    
    #log('Data {}'.format(data))
    #log('Code {}'.format(code))

    if not code or not code == 200 or not data or not check_key(data, 'watchlistId'):
        return False

    profile_settings['watchlist_id'] = data['watchlistId']
    save_profile(profile_id=1, profile=profile_settings)

    #log('api_get_watchlist_id success')
    return True

def api_list_watchlist(type='watchlist'):
    #log('api_list_watchlist, type {}'.format(type))

    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    watchlist_url = '{watchlist_url}/profile/{profile_id}?language=nl&order=DESC&sharedProfile=true&sort=added'.format(watchlist_url=CONST_URLS['watchlist_url'], profile_id=profile_settings['ziggo_profile_id'])
    #log('URL {}'.format(watchlist_url))
    
    download = api_download(url=watchlist_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    #log('Data {}'.format(data))
    #log('Code {}'.format(code))

    if not code or not code == 200 or not data or not check_key(data, 'entries'):
        return False

    #log('api_list_watchlist success')
    return data

def api_login(retry=False):
    log('api_login, retry {}'.format(retry))
    
    creds = get_credentials()
    username = creds['username']
    password = creds['password']

    try:
        os.remove(os.path.join(ADDON_PROFILE, 'stream_cookies'))
    except:
        pass

    profile_settings = load_profile(profile_id=1)

    profile_settings['access_token'] = ''
    profile_settings['ziggo_profile_id'] = ''
    profile_settings['household_id'] = ''
    profile_settings['watchlist_id'] = ''
    save_profile(profile_id=1, profile=profile_settings)

    headers = {
        'Content-Type': 'application/json',
        'X-Device-Code': 'web',
    }

    downloads = requests.request("POST", CONST_URLS['auth_url'], headers=headers, data=json.dumps({"username": username, "password": password}))
    download = downloads.json()

    household_id = ''

    try:
        household_id = download['householdId']
    except:
        pass

    log('householdId: {}'.format(household_id))

    headers2 = {
        'Content-Type': 'application/json',
        'Cookie': f"ACCESSTOKEN={download['accessToken']}",
    }

    base_cust = CONST_URLS['customer_url']
    cust_url = '{base}/{hid}?with=profiles,devices'.format(base=base_cust, hid=household_id)
    download2 = requests.request("GET", cust_url, headers=headers2)
    profile = download2.json()
    profile_orig = profile

    ziggo_profile_id = ''

    try:
        ziggo_profile_id = profile['profiles'][0]['profileId']
    except:
        pass

    log('profileId {}'.format(ziggo_profile_id))

    base_entitl = CONST_URLS['entitlements_url']
    ent_url = '{base}/{hid}/entitlements'.format(base=base_entitl, hid=household_id)
    entitl = requests.request("GET", ent_url, headers=headers2)
    entitlements = entitl.json()

    entitlements_token = ''

    try:
        entitlements_token = entitlements['token']
    except:
        pass

    log('entitlements: {}'.format(entitlements_token))

    xstoken = download['accessToken']
    log('accesstoken: {}'.format(xstoken))
    profile_settings['access_token'] = f"ACCESSTOKEN={xstoken}"
    profile_settings['ziggo_profile_id'] = ziggo_profile_id
    profile_settings['household_id'] = household_id
    profile_settings['entitlements_token'] = entitlements_token
    save_profile(profile_id=1, profile=profile_settings)

    if len(str(profile_settings['watchlist_id'])) == 0:
        api_get_watchlist_id()
    
    log('api_login success')
    return { 'code': 200, 'data': profile_orig, 'result': True }

def api_play_url(type, channel=None, id=None, video_data=None, from_beginning=0, pvr=0, change_audio=0):
    playdata = {'path': '', 'mpd': '', 'license': '', 'certificate': '', 'token': '', 'locator': '', 'type': '', 'properties': {}}

    if not api_get_session():
        log('no api_get_session')
        return playdata

    api_clean_after_playback(stoptime=0)

    from_beginning = int(from_beginning)
    pvr = int(pvr)
    change_audio = int(change_audio)

    profile_settings = load_profile(profile_id=1)

    if type == "channel":
        id = channel

    info = {}
    properties = {}
    base_listing_url = CONST_URLS['listings_url']
    urldata = None
    urldata2 = None
    path = None
    locator = None
    certificate_data = None

    if not type or not len(str(type)) > 0 or not id or not len(str(id)) > 0:
        return playdata

    if type == 'channel':
        #profile_settings = load_profile(profile_id=1)      #RIF moved to l8.menu.py
        #profile_settings['detect_replay'] = 0
        #save_profile(profile_id=1, profile=profile_settings)

        data = api_get_channels()

        try:
            split = data[id]['assetid'].rsplit('&%%&', 1)

            if len(split) == 2:
                urldata = {'play_url': split[0], 'locator': split[1]}
            else:
                return playdata
        except:
            return playdata

        listing_url = '{listings_url}?byEndTime={time}~&byStationId={channel}&range=1-1&sort=startTime'.format(listings_url=base_listing_url, time=int(time.time() * 1000), channel=id)
        download = api_download(url=listing_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']
        log('api_play_url: type == channel, most likely live tv, listings url to get program info. deprecated; returns empty')
        if code and code == 200 and data and check_key(data, 'listings'):
            for row in data['listings']:
                if check_key(row, 'program'):
                    info = row['program']
    elif type == 'program':
        #profile_settings = load_profile(profile_id=1)      #RIF moved to l8.menu.py
        #profile_settings['detect_replay'] = 1
        #save_profile(profile_id=1, profile=profile_settings)
        
        listings_url = "{listings_url}/{id}".format(listings_url=base_listing_url, id=id)
        download = api_download(url=listings_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']
        log('api_play_url: type == program, listings url to get program info. deprecated; returns empty')
        if not code or not code == 200 or not data or not check_key(data, 'program'):
            pass

        if 'imi' in id:
            profile_settings = load_profile(profile_id=1)
            profile_settings['rec_id'] = id
            save_profile(profile_id=1, profile=profile_settings)
        else:
            log('api_play_url: imi not in id')

        play_token = api_get_play_token(locator=None, path=None)
        urldata2 = {}
        urldata2['play_url'] = play_token[1]
        log(urldata2)

    elif type == 'vod':
        mediaitems_url = '{mediaitems_url}/{id}'.format(mediaitems_url=CONST_URLS['mediaitems_url'], id=id)
        download = api_download(url=mediaitems_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']
        log('api_play_url: type == vod, WARNING: NOT POSSIBLE SINCE FEATURE IS DISABLED! listings url to get movie/series info using mediaitems url. deprecated; returns empty')
        if not code or not code == 200 or not data:
            return playdata

        info = data

    log(info)

    #if not type == 'channel' and (not urldata2 or not check_key(urldata2, 'play_url') or not check_key(urldata2, 'locator') or urldata2['play_url'] == 'http://Playout/using/Session/Service'):
    #    urldata2 = {}
    #
    #    if type == 'program':
    #        playout_str = 'replay'
    #    elif type == 'vod':
    #        playout_str = 'vod'
    #    else:
    #        return playdata
    #
    #    log('api_play_url: playout using session service (note: this is not possible so this will fail)')
    #
    #    baseurl = "https://obo-prod.oesp.ziggogo.tv/oesp/v4/NL/nld/web"
    #    playout_url = '{base_url}/playout/{playout_str}/{id}?abrType=BR-AVC-DASH'.format(base_url=baseurl, playout_str=playout_str, id=id)
    #    download = api_download(url=playout_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
    #    data = download['data']
    #    code = download['code']
    #
    #    if not code or not code == 200 or not data or not check_key(data, 'url') or not check_key(data, 'contentLocator'):
    #        return playdata
    #
    #    urldata2['play_url'] = data['url']
    #    urldata2['locator'] = data['contentLocator']

    if type == 'channel':
        pass
    else:
        try:
            urldata2['locator']
        except:
            urldata2['locator'] = 'recording'

    if urldata and urldata2 and check_key(urldata, 'play_url') and check_key(urldata, 'locator') and check_key(urldata2, 'play_url') and check_key(urldata2, 'locator'):
        if not from_beginning == 1:
            path = urldata['play_url']
            locator = urldata['locator']
        else:
            path = urldata2['play_url']
            locator = urldata2['locator']
    else:
        if urldata and check_key(urldata, 'play_url') and check_key(urldata, 'locator'):
            path = urldata['play_url']
            locator = urldata['locator']
        elif urldata2 and check_key(urldata2, 'play_url'):
            path = urldata2['play_url']
            locator = urldata2['locator']

    if not locator or not len(str(locator)) > 0:
        pass

    license = CONST_URLS['widevine_url']

    log(license)

    profile_settings = load_profile(profile_id=1)
    profile_settings['drm_locator'] = locator
    save_profile(profile_id=1, profile=profile_settings)

    play_token = api_get_play_token(locator=locator, path=None) 
    #note to self: needed for second time because of issues; it must be after the 'imi' check from type == program; but that function needs it as well
    #RIF?

    log(play_token)

    token = play_token
    token_orig = token

    if not token or not len(str(token)) > 0:
        return playdata

    token = 'WIDEVINETOKEN'
    token_regex = re.search(r"(?<=;vxttoken=)(.*?)(?=/)", path)

    if token_regex and token_regex.group(1) and len(token_regex.group(1)) > 0:
        path = path.replace(token_regex.group(1), token)
    else:
        if 'sdash/' in path:
            spliturl = path.split('sdash/', 1)

            if len(spliturl) == 2:
                path = '{urlpart1}sdash;vxttoken={token}/{urlpart2}'.format(urlpart1=spliturl[0], token=token, urlpart2=spliturl[1])
        else:
            spliturl = path.rsplit('/', 1)

            if len(spliturl) == 2:
                path = '{urlpart1};vxttoken={token}/{urlpart2}'.format(urlpart1=spliturl[0], token=token, urlpart2=spliturl[1])

    mpd = ''

    if change_audio == 1:
        mpd_path = path.replace('WIDEVINETOKEN', token_orig)

        download = api_download(url=mpd_path, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=False)
        data = download['data']
        code = download['code']

        if code and code == 200:
            mpd = data
            
    #certificate_data = base64.b64encode(requests.get('{web_url}/content/dam/certs/cert_license_widevine_com.bin'.format(web_url=CONST_URLS['web_url'])).content).decode('utf-8')
    #write_file(file='server_certificate', data=certificate_data, isJSON=False)
    
    playdata = {'path': path, 'mpd': mpd, 'license': license, 'certificate': certificate_data, 'token': token, 'locator': locator, 'info': info, 'type': type, 'properties': properties}

    return playdata

def api_remove_from_watchlist(id, type='watchlist'):
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    remove_url = '{watchlist_url}/{watchlist_id}/entries/{id}?sharedProfile=true'.format(watchlist_url=CONST_URLS['watchlist_url'], watchlist_id=profile_settings['watchlist_id'], id=id)

    download = api_download(url=remove_url, type='delete', headers=api_get_headers(), data=None, json_data=False, return_json=False)
    code = download['code']

    if not code or not code == 204:
        return False

    return True

def api_search(query):
    log("api_search")

    profile_settings = load_profile(profile_id=1)
    
    end = int(time.time() * 1000)
    start = end - (7 * 24 * 60 * 60 * 1000)

    vodstr = ''

    queryb32 = encode32(query)

    file = os.path.join("cache", "{query}.json".format(query=queryb32))

    search_url = '{search_url}?profileId={profid}&sharedProfile=true&includeDetails=true&clientType=209&searchTerm={query}&queryLanguage=nl&startResults=0&maxResults=100&includeExternalProvider=ALL'.format(search_url=CONST_URLS['search_url'], profid=profile_settings['ziggo_profile_id'], start=start, end=end, query=quote_plus(query))

    def data_layer():
        if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=0.5):
            data = load_file(file=file, isJSON=True)
            log("search: not older than 0,5 days")
            return data

        else:
            download = api_download(url=search_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
            data = download['data']
            chkdata = json.dumps(data)
            code = download['code']
            log("and here's the search_url")
            log(search_url)
            if code and code == 200 and chkdata and 'show' in data or 'series' in chkdata:
                log("code==200 and in data, there is show or series")
                write_file(file=file, data=data, isJSON=True)
                return data
    
            if code!=200:
                #it went wrong, print code, refresh values and try again
                log("data of search_url below:")
                log(data)
                api_login()
                data_layer()
            else:
                pass
    try:
        data = data_layer()
        chkdata = json.dumps(data)
    except:
        log("it seems data from data_layer (search function) had some kind of problem ------- ignoring; you WILL get errors")

    if not chkdata or not 'show' in chkdata and not 'series' in chkdata:
        log('returned false at ifnot data ornot show&series')
        log("data of search_url below:")
        log(data)
        return False

    items = []
    items_vod = []
    items_program = []
    vod_links = {}

    if not settings.getBool('showMoviesSeries'):
        try:
            data.pop('moviesAndSeries', None)
        except:
            pass
    else:
        for entry in CONST_VOD_CAPABILITY:
            data2 = api_get_vod_by_type(type=entry['file'], character=None, genre=None, subscription_filter=None)
            log('data2: {0}').format(data2)
            for currow in data2:
                row = data2[currow]

                vod_links[row['id']] = {}
                vod_links[row['id']]['seasons'] = row['seasons']
                vod_links[row['id']]['duration'] = row['duration']
                vod_links[row['id']]['desc'] = row['description']
                vod_links[row['id']]['type'] = row['type']

    for currow in list(data):
        if currow == "moviesAndSeries":
            type = 'vod'
        else:
            type = 'program'
        log("type: {type}".format(type=type))

        for row in data[currow]:
            if not check_key(row, 'id') or not check_key(row, 'name'):
                continue

            item = {}

            id = row['id']
            label = row['name']
            description = ''
            duration = 0
            program_image = ''
            program_image_large = ''
            start = ''

            profile_settings = load_profile(profile_id=1)
            profile_settings['search_id'] = id
            save_profile(profile_id=1, profile=profile_settings)

            log("id:{id}".format(id=id))

            if check_key(row, 'associatedPicture'):
                program_image = row['associatedPicture']

                if program_image_large == '':
                    program_image_large = program_image
                else:
                    program_image_large += '?w=1920&mode=box'

            if type == 'vod':
                if check_key(vod_links, row['id']):
                    description = vod_links[row['id']]['desc']
                    item_type = vod_links[row['id']]['type']
                else:
                    item_type = 'Vod'

                label += " (Movies and Series)"
            else:
                item_type = 'Epg'
                label += " (ReplayTV)"

            if check_key(row, 'groupType') and row['groupType'] == 'show':
                if check_key(row, 'episodeMatch') and check_key(row['episodeMatch'], 'seriesEpisodeNumber') and check_key(row['episodeMatch'], 'secondaryTitle'):
                    if len(description) == 0:
                        description += label

                    season = ''

                    if check_key(row, 'seasonCount'):
                        season = "S" + row['seasonCount']

                    description += " Episode Match: {season}E{episode}".format(season=season, episode=row['episodeCount'])
            else:
                if check_key(row, 'duration'):
                    duration = int(row['duration'])
                elif check_key(row, 'episodeMatch') and check_key(row['episodeMatch'], 'startTime') and check_key(row['episodeMatch'], 'endTime'):
                    duration = int(int(row['episodeMatch']['endTime']) - int(row['episodeMatch']['startTime'])) // 1000
                    id = row['episodeMatch']['id']
                elif check_key(vod_links, row['id']) and check_key(vod_links[row['id']], 'duration'):
                    duration = vod_links[row['id']]['duration']

            recording_url = '{recording_url}/{hid}/details/single/{id}?{profid}&language=nl'.format(recording_url=CONST_URLS['recording_url'], hid=profile_settings['household_id'], id=id, profid=profile_settings['ziggo_profile_id'])
            download = api_download(url=recording_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
            data = download['data']
            code = download['code']
            duration = data['duration']
            description += " - {desc}".format(desc=data['shortSynopsis'])

            item['id'] = id
            item['title'] = label
            item['description'] = description
            log("label: {label}".format(format=format))
            item['duration'] = duration
            item['type'] = item_type
            item['icon'] = program_image_large
            item['start'] = start

            if type == "vod":
                items_vod.append(item)
            else:
                items_program.append(item)

    num = min(len(items_program), len(items_vod))
    items = [None]*(num*2)
    items[::2] = items_program[:num]
    items[1::2] = items_vod[:num]
    items.extend(items_program[num:])
    items.extend(items_vod[num:])

    return items

def api_set_profile(id=''):
    return None

def api_vod_download():
    return None

def api_vod_season(series, id, use_cache=True):
    type = "vod_season_{id}".format(id=id)
    type = encode32(type)

    file = os.path.join("cache", "{type}.json".format(type=type))
    cache = 0

    profile_settings = load_profile(profile_id=1)

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=0.5) and use_cache == True:
        data = load_file(file=file, isJSON=True)
        cache = 1
    else:
        season_url = '{mediaitems_url}?byMediaType=Episode%7CFeatureFilm&byParentId={id}&includeAdult=true&range=1-1000&sort=seriesEpisodeNumber|ASC'.format(mediaitems_url=CONST_URLS['mediaitems_url'], id=id)
        download = api_download(url=season_url, type='get', headers=None, data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']

    return {'data': data, 'cache': cache}

def api_vod_seasons(type, id, use_cache=True):
    type2 = "vod_seasons_{id}".format(id=id)
    type2 = encode32(type2)

    file = os.path.join("cache", "{type}.json".format(type=type2))

    cache = 0

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=0.5) and use_cache == True:
        data = load_file(file=file, isJSON=True)
        cache = 1
    else:
        data = api_get_vod_by_type(type=type, character=None, genre=None, subscription_filter=None)

    return {'data': data, 'cache': cache}

def api_vod_subscription():
    return None

def api_watchlist_listing(id):
    if not api_get_session():
        return None

    profile_settings = load_profile(profile_id=1)

    end = int(time.time() * 1000)
    start = end - (7 * 24 * 60 * 60 * 1000)

    mediaitems_url = '{media_items_url}?&byMediaGroupId={id}&byStartTime={start}~{end}&range=1-250&sort=startTime%7Cdesc'.format(media_items_url=CONST_URLS['listings_url'], id=id, start=start, end=end)
    download = api_download(url=mediaitems_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']

    if not code or not code == 200 or not data or not check_key(data, 'listings'):
        return False

    return data