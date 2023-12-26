import datetime
import json
import os
import string
import sys
import time
from urllib.parse import urlparse
from xml.dom.minidom import parseString
import math
import threading
import pytz
import xbmc
import xbmcaddon
import xbmcplugin
from fuzzywuzzy import fuzz

from resources.lib.api import *
from resources.lib.api import (api_add_to_watchlist, api_get_profiles,
                               api_list_watchlist, api_login, api_play_url,
                               api_remove_from_watchlist, api_search,
                               api_set_profile, api_vod_download,
                               api_vod_season, api_vod_seasons,
                               api_watchlist_listing)
from resources.lib.base.l1.constants import (ADDON_ID, ADDON_PROFILE,
                                             ADDON_VERSION, ADDONS_PATH,
                                             AUDIO_LANGUAGES, PROVIDER_NAME)
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import (add_library_sources, change_icon,
                                        check_key, clear_cache,
                                        convert_datetime_timezone,
                                        date_to_nl_dag, date_to_nl_maand,
                                        disable_prefs, get_credentials,
                                        is_file_older_than_x_days,
                                        is_file_older_than_x_minutes, json_rpc,
                                        load_file, load_prefs, load_profile,
                                        remove_dir, remove_file,
                                        remove_library, save_prefs,
                                        save_profile, set_credentials,
                                        write_file)
from resources.lib.base.l4 import gui
from resources.lib.base.l4.exceptions import Error, PluginError
from resources.lib.base.l5.api import (api_download, api_get_channels,
                                       api_get_epg_by_date_channel,
                                       api_get_epg_by_idtitle,
                                       api_get_genre_list, api_get_list,
                                       api_get_list_by_first,
                                       api_get_vod_by_type)
from resources.lib.base.l7 import plugin
from resources.lib.constants import (CONST_BASE_HEADERS, CONST_FIRST_BOOT,
                                     CONST_HAS, CONST_IMAGES, CONST_LIBRARY)
from resources.lib.constants import CONST_URLS as CONST_URLS2
from resources.lib.constants import (CONST_VOD_CAPABILITY, CONST_WATCHLIST,
                                     CONST_WATCHLIST_CAPABILITY)
from resources.lib.util import (plugin_ask_for_creds, plugin_check_devices,
                                plugin_check_first, plugin_login_error,
                                plugin_post_login, plugin_process_info,
                                plugin_process_playdata,
                                plugin_process_rec_seasons, plugin_process_vod,
                                plugin_process_vod_season,
                                plugin_process_vod_seasons,
                                plugin_process_watchlist,
                                plugin_process_watchlist_listing,
                                plugin_renew_token,
                                plugin_vod_subscription_filter)

#GEHEUGENSTEUN: RIF BETEKENT REMOVED IN FUTURE
#DIT MOET ELKE KEER OVERWEGEN WORDEN WEG TE HALEN EN IS MOGELIJK GEVAARLIJK OM VOOR ALTIJD TE LATEN
#   **dit staat in elk document waar iets weg moet**

def bg_thread(func_name, interval, stop_event):
    #(note: this is a loop that executes the given function name every minute, used in a different function in combination with threads)
    while not stop_event.is_set():
        func_name()
        #check if stop_event is set within every interval (in seconds)
        for _ in range(interval): #refresh token every interval (in seconds)
            if stop_event.is_set():
                break
            time.sleep(1) #sleep 1 second so the code gets executed every second within one interval, which translates to "waiting" exactly one interval

main_stop_event = threading.Event() #main signal used to stop all threads that **USE** this, upon exit

login_stop_event = threading.Event() #signal used to stop login thread upon exit
login_thread = threading.Thread(target=bg_thread, args=(api_login, 110, login_stop_event)) #define thread to be started

threads = [login_thread] #edit this to add threads to the list of background threads
stop_events = [login_stop_event, main_stop_event] #edit this to add stop_events to the list used to stop the above threads

def on_plugin_stop(): #built-in function name, to be called upon exiting
    for stop_event in stop_events:
        stop_event.set() #signal to stop thread

    for thread in threads:
        threading.Timer(5, thread.cancel).start() #RIF: below doesnt work correctly, so forcefully stopping for now

    #if bg_thread.is_alive():  #wait max 5 secs for thread to stop
        #bg_thread.join(5) #wait for thread to stop before quiting Kodi


ADDON_HANDLE = int(sys.argv[1])
backend = ''

@plugin.route('')
def home(**kwargs):
    profile_settings = load_profile(profile_id=1)

    #stop_event.clear() #clear any set values
    try:
        for thread in threads:
            thread.daemon = True #thread on background
            thread.start() #start thread
    except:
        gui.error(message=_.DAEMON_ALREADY_ACTIVE)
        try:
            for thread in threads:
                thread.daemon = True #thread on background
                thread.start() #start thread
        except:
            gui.error(message=_(_.PLUGIN_EXCEPTION, addon="Daemon"))


    if not ADDON_ID == 'plugin.executable.dutiptv' and (not check_key(profile_settings, 'version') or not ADDON_VERSION == profile_settings['version']):
        change_icon()
        clear_cache(clear_all=1)
        profile_settings['version'] = ADDON_VERSION
        save_profile(profile_id=1, profile=profile_settings)
        check_first()

    folder = plugin.Folder()

    if profile_settings and check_key(profile_settings, 'pswd') and len(profile_settings['pswd']) > 0:
        if CONST_HAS['live']:
            folder.add_item(label=_(_.LIVE_TV, _bold=True),  path=plugin.url_for(func_or_url=live_tv))

        if CONST_HAS['replay']:
            folder.add_item(label=_(_.CHANNELS, _bold=True), path=plugin.url_for(func_or_url=replaytv, movies=0))

        if CONST_HAS['recording']:
            folder.add_item(label=_(_.RECORDINGS, _bold=True), path=plugin.url_for(func_or_url=rectv, movies=0))

        if settings.getBool('showMoviesSeries'):
            for vod_entry in CONST_VOD_CAPABILITY:
                folder.add_item(label=_(vod_entry['label'], _bold=True), path=plugin.url_for(func_or_url=vod, file=vod_entry['file'], label=vod_entry['label'], start=vod_entry['start'], online=vod_entry['online'], az=vod_entry['az'], menu=vod_entry['menu']))

        for entry in CONST_WATCHLIST_CAPABILITY:
            row = CONST_WATCHLIST_CAPABILITY[entry]
            folder.add_item(label=_(row['label'], _bold=True), path=plugin.url_for(func_or_url=watchlist, type=entry))

        if CONST_HAS['search']:
            folder.add_item(label=_(_.SEARCH, _bold=True), path=plugin.url_for(func_or_url=search_menu))

        if CONST_HAS['profiles']:
            if check_key(profile_settings, 'profile_name') and len(str(profile_settings['profile_name'])) > 0:
                profile_txt = '{}: {}'.format(_.PROFILE, profile_settings['profile_name'])
            else:
                profile_txt = '{}: {}'.format(_.PROFILE, _.DEFAULT)

            folder.add_item(label=_(profile_txt, _bold=True), path=plugin.url_for(func_or_url=switch_profile))

    folder.add_item(label=_(_.LOGIN, _bold=True), path=plugin.url_for(func_or_url=login))
    folder.add_item(label=_.SETTINGS, path=plugin.url_for(func_or_url=settings_menu))

    return folder

#Main menu items
@plugin.route()
def login(ask=1, **kwargs):
    ask = int(ask)

    creds = get_credentials()

    if len(creds['username']) < 1 or len(creds['password']) < 1 or ask == 1:
        user_info = plugin_ask_for_creds(creds)

        if user_info['result']:
            set_credentials(username=user_info['username'], password=user_info['password'])

    login_result = api_login()

    if not login_result['result']:
        profile_settings = load_profile(profile_id=1)
        profile_settings['last_login_success'] = 0
        profile_settings['pswd'] = ''
        save_profile(profile_id=1, profile=profile_settings)

        plugin_login_error(login_result)
    else:
        profile_settings = load_profile(profile_id=1)
        profile_settings['last_login_success'] = 1
        profile_settings['time_id'] = time.time()
        save_profile(profile_id=1, profile=profile_settings)

        gui.ok(message=_.LOGIN_SUCCESS)

        api_get_channels()
        plugin_post_login()

    gui.refresh()

@plugin.route()
def live_tv(**kwargs):
    folder = plugin.Folder(title=_.LIVE_TV)

    profile_settings = load_profile(profile_id=1)
    profile_settings['detect_replay'] = 0
    save_profile(profile_id=1, profile=profile_settings)

    for row in get_live_channels():
        folder.add_item(
            label = row['label'],
            info = {'plot': row['description']},
            art = {'thumb': row['image']},
            path = row['path'],
            context = row['context'],
        )

    return folder

@plugin.route()
def replaytv(movies=0, **kwargs):
    movies = int(movies)

    profile_settings = load_profile(profile_id=1)
    profile_settings['detect_replay'] = 1
    save_profile(profile_id=1, profile=profile_settings)

    folder = plugin.Folder(title=_.CHANNELS)

    folder.add_item(
        label = _.MOVIES,
        path = plugin.url_for(func_or_url=replaytv_alphabetical, movies=1),
    )

    folder.add_item(
        label = _.PROGSAZ,
        info = {'plot': _.PROGSAZDESC},
        path = plugin.url_for(func_or_url=replaytv_alphabetical, movies=movies),
    )

    for row in get_replay_channels():
        folder.add_item(
            label = row['label'],
            info = {'plot': row['description']},
            art = {'thumb': row['image']},
            path = row['path'],
            playable = row['playable'],
        )

    return folder

@plugin.route()
def replaytv_alphabetical(movies=0, **kwargs):
    movies = int(movies)

    folder = plugin.Folder(title=_.PROGSAZ)

    label = _.ALLTITLES

    folder.add_item(
        label = label,
        info = {'plot': _.ALLTITLESDESC},
        path = plugin.url_for(func_or_url=replaytv_list, label=label, start=0, character='', movies=movies),
    )

    label = _.OTHERTITLES

    folder.add_item(
        label = label,
        info = {'plot': _.OTHERTITLESDESC},
        path = plugin.url_for(func_or_url=replaytv_list, label=label, start=0, character='other', movies=movies),
    )

    for character in string.ascii_uppercase:
        label = _.TITLESWITH + character

        folder.add_item(
            label = label,
            info = {'plot': _.TITLESWITHDESC + character},
            path = plugin.url_for(func_or_url=replaytv_list, label=label, start=0, character=character, movies=movies),
        )

    return folder

@plugin.route()
def replaytv_list(character, label='', start=0, movies=0, **kwargs):
    start = int(start)
    movies = int(movies)
    folder = plugin.Folder(title=label)

    processed = process_replaytv_list(character=character, start=start, movies=movies)

    if check_key(processed, 'items'):
        folder.add_items(processed['items'])

    if check_key(processed, 'total') and check_key(processed, 'count2') and processed['total'] > processed['count2']:
        folder.add_item(
            label = _(_.NEXT_PAGE, _bold=True),
            properties = {'SpecialSort': 'bottom'},
            path = plugin.url_for(func_or_url=replaytv_list, character=character, label=label, start=processed['count2'], movies=movies),
        )

    return folder

@plugin.route()
def replaytv_by_day(label='', image='', description='', station='', **kwargs):
    folder = plugin.Folder(title=label)

    for x in range(0, 7):
        curdate = datetime.date.today() - datetime.timedelta(days=x)

        itemlabel = ''

        if x == 0:
            itemlabel = '{} - '.format(_.TODAY)
        elif x == 1:
            itemlabel = '{} - '.format(_.YESTERDAY)

        if xbmc.getLanguage(xbmc.ISO_639_1) == 'nl':
            itemlabel += date_to_nl_dag(curdate=curdate) + curdate.strftime(" %d ") + date_to_nl_maand(curdate=curdate) + curdate.strftime(" %Y")
        else:
            itemlabel += curdate.strftime("%A %d %B %Y").capitalize()

        folder.add_item(
            label = itemlabel,
            info = {'plot': description},
            art = {'thumb': image},
            path = plugin.url_for(func_or_url=replaytv_content, label=itemlabel, day=x, station=station),
        )

    return folder

@plugin.route()
def replaytv_item(label=None, idtitle=None, start=0, **kwargs):
    start = int(start)
    folder = plugin.Folder(title=label)

    processed = process_replaytv_list_content(label=label, idtitle=idtitle, start=start)

    if check_key(processed, 'items'):
        folder.add_items(processed['items'])

    if check_key(processed, 'total') and check_key(processed, 'count2') and processed['total'] > processed['count2']:
        folder.add_item(
            label = _(_.NEXT_PAGE, _bold=True),
            properties = {'SpecialSort': 'bottom'},
            path = plugin.url_for(func_or_url=replaytv_item, label=label, idtitle=idtitle, start=processed['count2']),
        )

    return folder

@plugin.route()
def replaytv_content(label, day, station='', start=0, **kwargs):
    day = int(day)
    start = int(start)
    folder = plugin.Folder(title=label)

    processed = process_replaytv_content(station=station, day=day, start=start)

    if check_key(processed, 'items'):
        folder.add_items(processed['items'])

    if check_key(processed, 'total') and check_key(processed, 'count2') and processed['total'] > processed['count2']:
        folder.add_item(
            label = _(_.NEXT_PAGE, _bold=True),
            properties = {'SpecialSort': 'bottom'},
            path = plugin.url_for(func_or_url=replaytv_content, label=label, day=day, station=station, start=processed['count2']),
        )

    return folder


















@plugin.route()
def do_nothing(**kwargs):
    pass



@plugin.route()
def rectv(**kwargs):

    profile_settings = load_profile(profile_id=1)
    profile_settings['detect_replay'] = 3
    save_profile(profile_id=1, profile=profile_settings)

    folder = plugin.Folder(title=_.RECORDINGS)

    file = os.path.join("cache", "recordings.json")
    if not is_file_older_than_x_minutes(file=os.path.join(ADDON_PROFILE, file), minutes=15):
        recsfile = load_file(file=file, isJSON=True)
        total = recsfile['total']
        quota = recsfile['quota']
    else:
        total = get_recs_list()['total']
        quota = get_recs_list()['quota']

    folder.add_item(
        label = "Total: {}".format(total),
        path = plugin.url_for(func_or_url=do_nothing),
    )

    limit = quota['quota'] / 3600
    occupied = quota['occupied'] / 3600
    perc = round(((occupied / limit) * 100), 1)
    used = round(occupied, 0)

    folder.add_item(
        label = "Quota: {0} ({1}%)".format(used, perc),
        path = plugin.url_for(func_or_url=do_nothing),
    )

    recs = get_recs()
    log('its me, recstv(). Im just above get_recs() loop')

    for key in recs.keys():
        log('entering recstv() loop, prepare for key to be printed')    #RIF this can be much better, its slow, but it works (multi-threading? cleanup?)
        log(key)                                                        #Update: already made a cache for recordings, cannot be older than 15 minutes or will simply contact API again
        row = recs[key]
        folder.add_item(
            label = row['label'],
            info = {'plot': row['description']},
            art = {'thumb': row['image']},
            path = row['path'],
            playable = row['playable'],
        )

    return folder



def get_recs():
    recordings = OrderedDict()
    log('get_recs()')
    
    file = os.path.join("cache", "recordings.json")
    if not is_file_older_than_x_minutes(file=os.path.join(ADDON_PROFILE, file), minutes=30):
        recsfile = load_file(file=file, isJSON=True)
        data = recsfile['recs']
    else:
        data = get_recs_list()['recs']

    #no meaning, might be removed in future (RIF)
    #prefs = load_prefs(profile_id=1)

    if data:
        for currow in data:
            row = data[currow]
            log('get_recs: for currow loop, before appending, currow printing:')

            recordings[row['name']] = {
                'label': str(row['name']),
                #'description': str(row['description']),
                'description': '',
                'image': str(row['img']),
                'path': plugin.url_for(func_or_url=recs_seasons, label=str(row['name']), img=str(row['img']), id=str(row['id']), source=str(row['source']), channel=str(row['channel']), e_id=str(row['e_id'])),
                'playable': False,
                'context': [],
                'id': str(row['id']),
                'channel': str(row['channel']),
                'source': str(row['source']),
            }
    #log(recordings)

    return recordings








@plugin.route()
def recs_seasons(label, img, id, source, channel, e_id=None, **kwargs):

    folder = plugin.Folder(title=label)

    data = get_recs()
    added_seasons = False

    if not e_id:
        e_id == False

    if data:
        if 'imi' in id:
            #RIF multi-threading? cleanup?
            plugin.url_for(func_or_url=recs_content, label=label, id=id, img=img, channel=channel, seasons=False)

        else:
            recs = get_recs_seasons(label=label, id=id, e_id=e_id, episodes=False)

            for season in recs:
                row = recs[season]
                log('entering recs_seasons(), seasons, prepare for key to be printed')    #RIF multi-threading? cleanup?
                folder.add_item(
                    label = 'Seizoen {}'.format(row['season_number']),
                    info = {'plot': row['description']},
                    #info = {'plot': ''},
                    art = {'thumb': row['season_image']},
                    path = row['path'],
                    playable = False,
                )
            added_seasons = True


            if added_seasons == True:
                return folder

@plugin.route()
def recs_content(label, id, img, channel=None, seasons=None, season_number=None, **kwargs):
        folder = plugin.Folder(title=label)
        if channel == None:
            channel = 'recordings'
        if season_number != None or season_number != False:
            seasons = True

        if seasons == False:
            data = get_recs_content()
            profile_settings = load_profile(profile_id=1)
            profile_settings['rec_id'] = id
            profile_settings['time_id'] = time.time()
            save_profile(profile_id=1, profile=profile_settings)
            log('menu_recs_content: saving rec_id')

            #(playable) episodes
            folder.add_item(
                label = label,
                #info = {'plot': row['description']},
                info = {'plot': ''},
                art = {'thumb': img},       #WIP: use image from season, not program itself
                path = plugin.url_for(func_or_url=play_video, type='program', channel=channel, id=id),
                playable = True,
            )
            return folder
        
        elif seasons == True:
            data = get_recs_seasons(label=label, id=id, episodes=True, season_number=season_number)   #API returns response with 'data' list (e.g. [] )
            log(data)

            #(playable) episodes
            for row in data:
                currow = data[row]
                id = currow['ep_id']
                profile_settings = load_profile(profile_id=1)
                profile_settings['time_id'] = time.time()
                save_profile(profile_id=1, profile=profile_settings)
                folder.add_item(
                    label = currow['ep_title'],
                    info = {'plot': currow['description']},
                    art = {'thumb': currow['ep_img']},
                    path = plugin.url_for(func_or_url=play_video, type='program', channel=channel, id=id),
                    playable = currow['playable'],
                )
            return folder


def get_recs_content(id):
    
    profile_settings = load_profile(profile_id=1)

    rec_folder = os.path.join("cache", "recordings")
    season_folder = os.path.join(rec_folder, "episodes")
    file = os.path.join(season_folder, "{id}.json".format(id=id.replace(":", "_")))

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=7):
        data = load_file(file=file, isJSON=True)
        code = 'file'
    else:
        base_rec = CONST_URLS2['recording_url']
        recs_seasons_url = '{base}/{hid}/details/single/{id}profileId={profid}'.format(base=base_rec, hid=profile_settings['household_id'], id=id, profid=profile_settings['ziggo_profile_id'])
        #log(recs_seasons_url)
        download = api_download(url=recs_seasons_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        code = download['code']
        write_file(file=os.path.join(ADDON_PROFILE, file), data=data, isJSON=True)


    if data and (code == 200 or code == 'file'):
        #log('get_recs_content() Code: {}'.format(code))
        desc = str(data.get('Synopsis', "N/A"))
        if desc == "N/A":
            desc = str(data.get('shortSynopsis', "N/A"))

        ep_img = str(data.get('background', {}).get('url', "N/A"))
        if ep_img == "N/A":
            ep_img = str(data.get('poster', {}).get('url', "N/A"))

        rec_episode = {
            'ep_title': str(data.get('episodeTitle', "N/A")),
            'description': desc,
            'ep_img': ep_img,
            'path': plugin.url_for(func_or_url=play_video, type='program', channel='recordings', id=id),
            'playable': True,
            'context': [],
        }

    log(rec_episode)
    return rec_episode










def get_recs_seasons(label, id, e_id=None, e_id_needed=None, episodes=None, season_number=None, **kwargs):
    rec_seasons = OrderedDict()
    rec_episodes = OrderedDict()
    #log('get_recs_season()')
    if not e_id:
        e_id == False
    
    profile_settings = load_profile(profile_id=1)

    rec_folder = os.path.join("cache", "recordings")
    season_folder = os.path.join(rec_folder, "seasons")
    file = os.path.join(season_folder, "{id}.json".format(id=id.replace(":", "_")))

    if not is_file_older_than_x_days(file=os.path.join(ADDON_PROFILE, file), days=1):
        data = load_file(file=file, isJSON=True)
        code = 'file'
    else:
        base_rec = CONST_URLS2['recording_url']
        if e_id_needed == True:
            id = e_id
        else:
            id=id
        recs_seasons_url = '{base}/{hid}/episodes/shows/{id}?sort=time&sortOrder=desc&profileId={profid}&source=recording&limit=100'.format(base=base_rec, hid=profile_settings['household_id'], id=id, profid=profile_settings['ziggo_profile_id'])
        log(recs_seasons_url)
        download = api_download(url=recs_seasons_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
        data = download['data']
        log(data)
        code = download['code']
        write_file(file=os.path.join(ADDON_PROFILE, file), data=data, isJSON=True)



    if episodes == False:
        if data and (code == 200 or code == 'file'):
            try:
                seasons = data['seasons']
            except: #RIF since it either works or returns false (?)
                try:
                    #e_id_needed == True
                    #get_recs_seasons(label, id, e_id, e_id_needed, episodes)
                    #log('menu: get_recs_seasons episodes false, except-try statement')
                    #log(id)
                    #log(e_id)
                    pass
                except:
                    return False
            
            for season in seasons:
                log('get_recs_seasons: for season loop, before appending, season printing:')

                desc = str(season.get('shortSynopsis', "N/A"))
                if desc == "N/A":
                    desc = str(data.get('shortSynopsis', "N/A"))

                season_img = str(season.get('poster', {}).get('url', "N/A"))

                rec_seasons[str(season.get('number', "N/A"))] = {
                    'season_number': str(season.get('number', "N/A")),
                    'description': desc,
                    'season_image': str(season.get('poster', {}).get('url', "N/A")),
                    'path': plugin.url_for(func_or_url=recs_content, label=label, id=id, img=season_img, season_number=str(season.get('number', "N/A"))),
                    'playable': False,
                    'context': [],
                }
        else:
            api_login()
            get_recs_seasons(label, id, episodes)
        log(rec_seasons)
        return rec_seasons

    elif episodes == True:

        if data and (code == 200 or code == 'file'):
            episodes = data['data']
            seasons = {}

            for episode in sorted(episodes, key=lambda x: (x['seasonNumber'], x['episodeNumber'])):     #sort episodes per season in a loop
                log('get_recs_seasons: for episodes loop, sorting by season, episodes printing:')
                log(episode)
                season = episode['seasonNumber']
                
                if season not in seasons:
                    seasons[season] = []
                seasons[season].append(episode)
                log(seasons)

            for episode in seasons[int(season_number)]:
                if episode['recordingState'] == 'recorded':
                    log('get_recs_seasons: for episodes loop, before appending, episodes printing:')
                    log(seasons)
                    log(episode)
                    ep_img = str(episode.get('background', {}).get('url', "N/A"))
                    if ep_img == "N/A":
                        ep_img = str(episode.get('poster', {}).get('url', "N/A"))


                    ep_number = str(episode.get('episodeNumber', "N/A"))
                    ep_season = str(episode.get('seasonNumber', "N/A"))

                    rec_episodes[ep_number] = {
                        'ep_title': str(episode.get('episodeTitle', "N/A")),
                        'ep_id': str(episode.get('episodeId', "N/A")),
                        'ep_number': ep_number,
                        'description': str(episode.get('synopsis', "N/A")),
                        'ep_img': ep_img,
                        'path': plugin.url_for(func_or_url=play_video, type='program', channel='recordings', id=id),
                        'playable': True,
                        'context': [],
                    }

        log(rec_episodes)
        return rec_episodes






def get_recs_list():

    profile_settings = load_profile(profile_id=1)

    base_rec = CONST_URLS2['recording_url']
    recs_url = '{base}/{hid}/recordings?sort=time&sortOrder=desc'.format(base=base_rec, hid=profile_settings['household_id'])
    log(recs_url)
    download = api_download(url=recs_url, type='get', headers=api_get_headers(), data=None, json_data=False, return_json=True)
    data = download['data']
    code = download['code']


    recs_file = os.path.join("cache", "recordings.json")

    #log('Data {}'.format(data))
    log('Recordings Code {}'.format(code))

    if code == 401:
        login_result = api_login()
        if not login_result['result']:
            log('login_result: api_login did not return result!')
            log('this is very bad')
        return get_recs_list()
        #if total_only == True:
        #    return get_recs_list(total_only=True)
        #RIF removed/disabled for now >> consider reworking: when full_data True, and code==401, function will be called with full_data is false, 
        #    returning the list with recordings (and not raw data)
        #else:
        #    return get_recs_list(total_only=False)

    elif code == 503:
        log('get_rec_list code 503, skipping')
        pass

    elif not code or not data or not code == 200:
        raise PluginError(_(_.RECORDINGS_NO_RESPONSE))

    #log(data)
    total = data['total']
    quota = data['quota']
    recs = data['data']
    data2 = OrderedDict()

    #loop through every name of the recordings (show N/A if, for some reason, the array 'title' does not exist)
    programs = []
    for x in recs:
        program = {}
        for key, value in x.items():
            program[key] = value
        programs.append(program)

        for program in programs:
            title = program.get('title',"N/A")
            poster_url = program.get("poster", {}).get("url", "N/A")
            source = program.get('source', "N/A")
            if source == 'single':
                id = program.get('id', "N/A")
            else:
                if 'showId' in program:
                    id = program.get('showId', "N/A")
                    emerg_id = program.get('id', "N/A") #in case of some weird things that showId isnt correct id (remember Fire country, source: show and type:season; yet showId is wrong)
                else:
                    id = program.get('id', "N/A")
            channel = program.get('channelId', "N/A")
            data2[title] = {"name": title, "img": poster_url, "id": id, "e_id": emerg_id, "source": source, "channel": channel}

    returnar = {}
    returnar['total'] = total
    returnar['quota'] = quota
    returnar['recs'] = data2
    write_file(file=recs_file, data=returnar, isJSON=True)
    return returnar

    #log("get_recs_list - total_only == {} - data2  is below:".format(total_only))
    #log(data2)



#                #if above isnt true this will NOT run, dangerous to leave like this (RIF)
#                folder.add_item(
#                    label = itemlabel,
#                    info = {'plot': description},
#                    art = {'thumb': image},
#                    path = plugin.url_for(func_or_url=replaytv_content, label=itemlabel, station=station),
#                )






@plugin.route()
def vod(file, label, start=0, character=None, genre=None, online=0, az=0, menu=0, **kwargs):
    start = int(start)
    online = int(online)
    az = int(az)
    menu = int(menu)

    if az == 1 or az == 2:
        folder = plugin.Folder(title=_.PROGSAZ)

        if az == 2:
            label = _.TITLESBYGENRE

            folder.add_item(
                label = label,
                info = {'plot': _.TITLESBYGENREDESC},
                path = plugin.url_for(func_or_url=vod, file=file, label=label, start=start, online=online, az=3, menu=menu),
            )

        label = _.ALLTITLES

        folder.add_item(
            label = label,
            info = {'plot': _.ALLTITLESDESC},
            path = plugin.url_for(func_or_url=vod, file=file, label=label, start=start, online=online, az=0, menu=menu),
        )

        label = _.OTHERTITLES

        folder.add_item(
            label = label,
            info = {'plot': _.OTHERTITLESDESC},
            path = plugin.url_for(func_or_url=vod, file=file, label=label, start=start, character='other', online=online, az=0, menu=menu),
        )

        for character in string.ascii_uppercase:
            label = _.TITLESWITH + character

            folder.add_item(
                label = label,
                info = {'plot': _.TITLESWITHDESC + character},
                path = plugin.url_for(func_or_url=vod, file=file, label=label, start=start, character=character, online=online, az=0, menu=menu),
            )

        return folder
    elif az == 3 or az == 4:
        folder = plugin.Folder(title=_.PROGSGENRE)

        if az == 4:
            data = api_get_genre_list(type=file, add=0)
        else:
            data = api_get_genre_list(type=file)

        if data:
            for genre in data:
                if az == 4:
                    label = data[genre]
                else:
                    label = genre

                if not label or len(str(label.strip())) == 0:
                    continue

                folder.add_item(
                    label = label,
                    info = {'plot': genre},
                    path = plugin.url_for(func_or_url=vod, file=file.replace(PROVIDER_NAME, ''), label=label, start=start, genre=genre, online=online, az=0),
                )

        return folder
    else:
        folder = plugin.Folder(title=label)

        if menu == 1:
            processed = process_vod_menu_content(data=file, start=start, type=label, character=character, genre=genre, online=online)

            if check_key(processed, 'items'):
                folder.add_items(processed['items'])
        else:
            processed = process_vod_content(data=file, start=start, type=label, character=character, genre=genre, online=online)

            if check_key(processed, 'items'):
                folder.add_items(processed['items'])

            if check_key(processed, 'total') and check_key(processed, 'count2') and processed['total'] > processed['count2']:
                folder.add_item(
                    label = _(_.NEXT_PAGE, _bold=True),
                    properties = {'SpecialSort': 'bottom'},
                    path = plugin.url_for(func_or_url=vod, file=file, label=label, start=processed['count2'], character=character, genre=genre, online=online, az=az, menu=menu),
                )

        return folder

@plugin.route()
def vod_series(label, type, id, **kwargs):
    folder = plugin.Folder(title=label)

    items = []
    context = []
    seasons = []

    data = api_vod_seasons(type, id)

    if data:
        seasons = plugin_process_vod_seasons(id=id, data=data['data'])

    title = label

    if seasons and check_key(seasons, 'seasons'):
        program_type = 'season'

        if check_key(CONST_WATCHLIST, 'vod') and check_key(CONST_WATCHLIST['vod'], program_type) and CONST_WATCHLIST_CAPABILITY[CONST_WATCHLIST['vod'][program_type]['type']]['add'] == 1:
            context.append((CONST_WATCHLIST_CAPABILITY[CONST_WATCHLIST['vod'][program_type]['type']]['addlist'], 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=add_to_watchlist, id=id, program_type=program_type, type=CONST_WATCHLIST['vod'][program_type]['type'])), ))

        if seasons['type'] == "seasons":
            for season in seasons['seasons']:
                label = '{} {}'.format(_.SEASON, str(season['seriesNumber']).replace('Seizoen ', ''))

                items.append(plugin.Item(
                    label = label,
                    info = {'plot': str(season['description']), 'sorttitle': label.upper()},
                    art = {
                        'thumb': str(season['image']),
                        'fanart': str(season['image'])
                    },
                    path = plugin.url_for(func_or_url=vod_season, label=label, series=id, id=str(season['id'])),
                    context = context,
                ))
        else:
            for episode in seasons['seasons']:
                context2 = context.copy()
                context2.append(
                    (_.SELECT_AUDIO_LANGUAGE, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=play_video, type='vod', channel=None, id=str(episode['id']), change_audio=1)), ),
                )

                items.append(plugin.Item(
                    label = str(episode['label']),
                    info = {
                        'plot': str(episode['description']),
                        'duration': episode['duration'],
                        'mediatype': 'video',
                        'sorttitle': str(episode['label']).upper(),
                    },
                    art = {
                        'thumb': str(episode['image']),
                        'fanart': str(episode['image'])
                    },
                    path = plugin.url_for(func_or_url=play_video, type='vod', channel=None, id=str(episode['id'])),
                    context = context,
                    playable = True,
                ))

        folder.add_items(items)

    return folder

@plugin.route()
def vod_season(label, series, id, **kwargs):
    folder = plugin.Folder(title=label)

    items = []
    season = []

    data = api_vod_season(series=series, id=id)

    if data:
        season = plugin_process_vod_season(series=series, id=id, data=data['data'])

    for episode in season:
        context = []

        program_type = 'episode'

        if check_key(CONST_WATCHLIST, 'vod') and check_key(CONST_WATCHLIST['vod'], program_type) and CONST_WATCHLIST_CAPABILITY[CONST_WATCHLIST['vod'][program_type]['type']]['add'] == 1:
            context.append((CONST_WATCHLIST_CAPABILITY[CONST_WATCHLIST['vod'][program_type]['type']]['addlist'], 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=add_to_watchlist, id=episode['id'], season=id, series=series, program_type=program_type, type=CONST_WATCHLIST['vod'][program_type]['type'])), ))

        context.append(
            (_.SELECT_AUDIO_LANGUAGE, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=play_video, type='vod', channel=None, id=str(episode['id']), data=json.dumps(episode), change_audio=1)), ),
        )

        items.append(plugin.Item(
            label = str(episode['label']),
            info = {
                'plot': str(episode['description']),
                'duration': episode['duration'],
                'mediatype': 'video',
                'sorttitle': str(episode['label']).upper(),
            },
            art = {
                'thumb': str(episode['image']),
                'fanart': str(episode['image'])
            },
            path = plugin.url_for(func_or_url=play_video, type='vod', channel=None, id=str(episode['id']), data=json.dumps(episode)),
            context = context,
            playable = True,
        ))

    folder.add_items(items)

    return folder

@plugin.route()
def search_menu(**kwargs):
    folder = plugin.Folder(title=_.SEARCHMENU)
    label = _.NEWSEARCH

    folder.add_item(
        label = label,
        info = {'plot': _.NEWSEARCHDESC},
        path = plugin.url_for(func_or_url=search),
    )

    if CONST_HAS['onlinesearch']:
        folder.add_item(
            label = str(label) + " (Online)",
            path=plugin.url_for(func_or_url=online_search)
        )

    profile_settings = load_profile(profile_id=1)
    profile_settings['detect_replay'] = 2

    for x in range(1, 10):
        try:
            if check_key(profile_settings, 'search' + str(x)):
                searchstr = profile_settings['search' + str(x)]
            else:
                searchstr = ''

            if searchstr != '':
                label = str(searchstr)
                path = plugin.url_for(func_or_url=search, query=searchstr)

                if CONST_HAS['onlinesearch']:
                    if check_key(profile_settings, 'search_type' + str(x)):
                        type = profile_settings['search_type' + str(x)]
                    else:
                        type = 0

                    if type == 1:
                        label = '{} (Online)'.format(searchstr)
                        path = plugin.url_for(func_or_url=online_search, query=searchstr)

                folder.add_item(
                    label = label,
                    info = {'plot': _(_.SEARCH_FOR, query=searchstr)},
                    path = path,
                )
        except:
            pass

    save_profile(profile_id=1, profile=profile_settings)
    return folder

@plugin.route()
def switch_profile(**kwargs):
    profiles = api_get_profiles()
    select_list = []
    id_list = {}

    for row in profiles:
        profile = profiles[row]

        id_list[profile['name']] = profile['id']
        select_list.append(profile['name'])

    if len(select_list) > 1:
        selected = gui.select(_.SELECT_PROFILE, select_list)

        try:
            result = api_set_profile(id=id_list[select_list[selected]])

            if result:
                gui.ok(message=_.SELECT_PROFILE_SUCCESS + str(select_list[selected]))
            else:
                gui.ok(message=_.SELECT_PROFILE_FAILED)
        except:
            gui.ok(message=_.SELECT_PROFILE_FAILED)
    else:
        gui.ok(message=_.SELECT_PROFILE_FAILED)

@plugin.route()
def search(query=None, **kwargs):
    items = []

    if not query:
        query = gui.input(message=_.SEARCH, default='').strip()

        if not query:
            return

        profile_settings = load_profile(profile_id=1)

        for x in reversed(range(2, 10)):
            if check_key(profile_settings, 'search' + str(x - 1)):
                profile_settings['search' + str(x)] = profile_settings['search' + str(x - 1)]
            else:
                profile_settings['search' + str(x)] = ''

        profile_settings['search1'] = query

        if CONST_HAS['onlinesearch']:
            for x in reversed(range(2, 10)):
                if check_key(profile_settings, 'search_type' + str(x - 1)):
                    profile_settings['search_type' + str(x)] = profile_settings['search_type' + str(x - 1)]
                else:
                    profile_settings['search_type' + str(x)] = 0

            profile_settings['search_type1'] = 0

        save_profile(profile_id=1, profile=profile_settings)
    else:
        query = str(query)

    folder = plugin.Folder(title=_(_.SEARCH_FOR, query=query))

    if CONST_HAS['replay']:
        processed = process_replaytv_search(search=query)
        items += processed['items']

    if settings.getBool('showMoviesSeries'):
        for vod_entry in CONST_VOD_CAPABILITY:
            if vod_entry['search'] == 0:
                continue

            processed = process_vod_content(data=vod_entry['file'], start=vod_entry['start'], search=query, type=vod_entry['label'], online=vod_entry['online'])
            items += processed['items']

    items[:] = sorted(items, key=_sort_replay_items, reverse=True)
    items = items[:25]

    folder.add_items(items)

    return folder

@plugin.route()
def online_search(query=None, **kwargs):
    items = []

    if not query:
        query = gui.input(message=_.SEARCH, default='').strip()

        if not query:
            return

        profile_settings = load_profile(profile_id=1)

        for x in reversed(range(2, 10)):
            if check_key(profile_settings, 'search' + str(x - 1)):
                profile_settings['search' + str(x)] = profile_settings['search' + str(x - 1)]
            else:
                profile_settings['search' + str(x)] = ''

            if check_key(profile_settings, 'search_type' + str(x - 1)):
                profile_settings['search_type' + str(x)] = profile_settings['search_type' + str(x - 1)]
            else:
                profile_settings['search_type' + str(x)] = 0

        profile_settings['search1'] = query
        profile_settings['search_type1'] = 1

        save_profile(profile_id=1, profile=profile_settings)
    else:
        query = str(query)

    folder = plugin.Folder(title=_(_.SEARCH_FOR, query=query))

    processed = process_vod_content(data='', start=0, search=query, type='Online', online=1)
    items += processed['items']

    items[:] = sorted(items, key=_sort_replay_items, reverse=True)
    items = items[:25]

    folder.add_items(items)

    return folder

@plugin.route()
def settings_menu(**kwargs):
    folder = plugin.Folder(title=_.SETTINGS)

    if CONST_HAS['live'] or CONST_HAS['replay']:
        folder.add_item(label=_.CHANNEL_PICKER, path=plugin.url_for(func_or_url=channel_picker_menu))

    if CONST_HAS['library']:
        folder.add_item(label=_.SETUP_LIBRARY, path=plugin.url_for(func_or_url=setup_library))

    if CONST_HAS['dutiptv']:
        folder.add_item(label=_.INSTALL_DUT_IPTV, path=plugin.url_for(func_or_url=install_connector))
        folder.add_item(label=_.SET_KODI, path=plugin.url_for(func_or_url=plugin._set_settings_kodi))

    folder.add_item(label=_.RESET_SESSION, path=plugin.url_for(func_or_url=login, ask=0))

    if CONST_HAS['library']:
        folder.add_item(label=_.ASK_RESET_LIBRARY, path=plugin.url_for(func_or_url=delete_library))
        
    if CONST_HAS['upnext']:
        folder.add_item(label=_.SETUP_UPNEXT, path=plugin.url_for(func_or_url=setup_upnext))

    folder.add_item(label=_.REMOVE_TEMP, path=plugin.url_for(func_or_url=clear_all_cache))

    folder.add_item(label=_.RESET, path=plugin.url_for(func_or_url=reset_addon))
    folder.add_item(label=_.LOGOUT, path=plugin.url_for(func_or_url=logout))

    folder.add_item(label="Addon {}".format(_.SETTINGS), path=plugin.url_for(func_or_url=plugin._settings))

    return folder

@plugin.route()
def setup_upnext(**kwargs):
    addon = 'service.upnext'

    if xbmc.getCondVisibility('System.HasAddon({addon})'.format(addon=addon)) == 1:
        try:
            VIDEO_ADDON = xbmcaddon.Addon(id=addon)
            gui.ok(message=_.DONE_NOREBOOT)
        except:
            method = 'Addons.SetAddonEnabled'
            json_rpc(method, {"addonid": addon, "enabled": "true"})

            try:
                VIDEO_ADDON = xbmcaddon.Addon(id=addon)
                gui.ok(message=_.DONE_NOREBOOT)
            except:
                pass
    else:
        xbmc.executebuiltin('InstallAddon({})'.format(addon), True)

    settings.setBool('upnext_enabled', True)

@plugin.route()
def clear_all_cache(**kwargs):
    clear_cache(clear_all=1)

@plugin.route()
def install_connector(**kwargs):
    addon = 'plugin.executable.dutiptv'

    if xbmc.getCondVisibility('System.HasAddon({addon})'.format(addon=addon)) == 1:
        try:
            VIDEO_ADDON = xbmcaddon.Addon(id=addon)
            gui.ok(message=_.DUT_IPTV_ALREADY_INSTALLED)
        except:
            method = 'Addons.SetAddonEnabled'
            json_rpc(method, {"addonid": addon, "enabled": "true"})

            try:
                VIDEO_ADDON = xbmcaddon.Addon(id=addon)
                gui.ok(message=_.DUT_IPTV_ENABLED)
            except:
                gui.ok(message=_.DUT_IPTV_ENABLE_FROM_ADDONS)
    else:
        xbmc.executebuiltin('InstallAddon({})'.format(addon), True)

@plugin.route()
def channel_picker_menu(**kwargs):
    folder = plugin.Folder(title=_.CHANNEL_PICKER)

    if CONST_HAS['live']:
        folder.add_item(label=_.LIVE_TV, path=plugin.url_for(func_or_url=channel_picker, type='live'))

    if CONST_HAS['replay']:
        folder.add_item(label=_.CHANNELS, path=plugin.url_for(func_or_url=channel_picker, type='replay'))

    if CONST_HAS['live'] and CONST_HAS['replay']:
        folder.add_item(label=_.LIVE_TV + ' = ' + _.CHANNELS, path=plugin.url_for(func_or_url=copy_channels, dest='live', source='replay'))
        folder.add_item(label=_.CHANNELS + ' = ' + _.LIVE_TV, path=plugin.url_for(func_or_url=copy_channels, dest='replay', source='live'))

    if CONST_FIRST_BOOT['erotica']:
        folder.add_item(label=_.DISABLE_EROTICA, path=plugin.url_for(func_or_url=disable_prefs_menu, type='erotica'))

    if CONST_FIRST_BOOT['minimal']:
        folder.add_item(label=_.DISABLE_MINIMAL, path=plugin.url_for(func_or_url=disable_prefs_menu, type='minimal'))

    if CONST_FIRST_BOOT['regional']:
        folder.add_item(label=_.DISABLE_REGIONAL2, path=plugin.url_for(func_or_url=disable_prefs_menu, type='regional'))

    if CONST_FIRST_BOOT['home']:
        folder.add_item(label=_.DISABLE_HOME_CONNECTION, path=plugin.url_for(func_or_url=disable_prefs_menu, type='home_only'))

    return folder

@plugin.route()
def disable_prefs_menu(type, **kwargs):
    disable_prefs(type=type, channels=api_get_channels())

    method = 'GUI.ActivateWindow'
    json_rpc(method, {"window": "videos", "parameters":["plugin://" + ADDON_ID + "/?_=channel_picker_menu"]})
@plugin.route()
def channel_picker(type, **kwargs):
    if type=='live':
        title = _.LIVE_TV
        rows = get_live_channels(all=True)
    elif type=='replay':
        title = _.CHANNELS
        rows = get_replay_channels(all=True)

    folder = plugin.Folder(title=title)
    prefs = load_prefs(profile_id=1)
    type = str(type)

    for row in rows:
        id = str(row['channel'])

        if not prefs or not check_key(prefs, id) or prefs[id][type] == 1:
            color = 'green'
        else:
            color = 'red'

        label = _(str(row['label']), _bold=True, _color=color)

        folder.add_item(
            label = label,
            art = {'thumb': str(row['image'])},
            path = plugin.url_for(func_or_url=change_channel, type=type, id=id, change=0),
            playable = False,
        )

    return folder

@plugin.route()
def copy_channels(dest, source, **kwargs):
    live = get_live_channels(all=True)
    replay = get_replay_channels(all=True)
    prefs = load_prefs(profile_id=1)

    if dest == 'live':
        source_rows = replay
        dest_rows = live
    else:
        source_rows = live
        dest_rows = replay

    for row in source_rows:
        id = str(row['channel'])

        if not prefs or not check_key(prefs, id) or prefs[id][source] == 1:
            set_value = 2
        else:
            set_value = 1

        change_channel(type=dest, id=id, change=0, set_value=set_value)

@plugin.route()
def change_channel(type, id, change, set_value=0, **kwargs):
    change = int(change)
    set_value = int(set_value)

    if not id or len(str(id)) == 0 or not type or len(str(type)) == 0:
        return False

    prefs = load_prefs(profile_id=1)
    id = str(id)
    type = str(type)

    data = api_get_channels()

    if data and check_key(data, id) and prefs and check_key(prefs, id) and int(prefs[id][type]) == 0:
        if type == 'replay' and int(data[id]['replay']) == 0:
            if set_value == 0:
                gui.ok(message=_.EXPLAIN_NO_REPLAY)
            return False
        elif settings.getBool(key='homeConnection') == False and int(data[id]['home_only']) == 1:
            if set_value == 0:
                gui.ok(message=_.EXPLAIN_HOME_CONNECTION)
            return False

    keys = ['live', 'replay']

    mod_pref = {
        'live': 1,
        'replay': 1,
    }

    if prefs and check_key(prefs, id):
        for key in keys:
            if key == type:
                continue

            mod_pref[key] = prefs[id][key]

    if set_value > 0:
        mod_pref[type] = set_value - 1
    elif change == 0:
        if not check_key(prefs, id):
            mod_pref[type] = 0
        else:
            if prefs[id][type] == 1:
                mod_pref[type] = 0
            else:
                mod_pref[type] = 1
    else:
        mod_pref[type] = 1

    prefs[id] = mod_pref
    save_prefs(profile_id=1, prefs=prefs)

    if set_value == 0:
        method = 'GUI.ActivateWindow'
        json_rpc(method, {"window": "videos", "parameters":["plugin://" + ADDON_ID + "/?_=channel_picker&type=" + type]})

@plugin.route()
def reset_addon(**kwargs):
    if CONST_HAS['library']:
        remove_library('movies')
        remove_library('shows')

    plugin._reset()
    gui.refresh()

@plugin.route()
def delete_library(**kwargs):
    if gui.yes_no(message=_.ASK_RESET_LIBRARY + ': ' + _.MOVIES):
        remove_library('movies')

    if gui.yes_no(message=_.ASK_RESET_LIBRARY + ': ' + _.SERIES):
        remove_library('shows')

    gui.ok(message=_.LIBRARY_RESET)

@plugin.route()
def setup_library(**kwargs):
    select_list = []
    select_list.append(_.DISABLE_INTEGRATION)
    select_list.append(_.ENABLE_INTEGRATION_MOVIES_WATCHLIST)
    select_list.append(_.ENABLE_INTEGRATION_MOVIES)

    selected = gui.select(_.ENABLE_LIBRARY_MOVIES, select_list)

    try:
        settings.setInt('library_movies', selected)
    except:
        settings.setInt('library_movies', 0)

    for type in CONST_LIBRARY['movies']:
        row = CONST_LIBRARY['movies'][type]

        if not gui.yes_no(message=_.ENABLE_LIBRARY_MOVIES + ": " + getattr(_, row['label'])):
            settings.setBool('library_movies_' + str(type), False)
        else:
            settings.setBool('library_movies_' + str(type), True)

    select_list = []
    select_list.append(_.DISABLE_INTEGRATION)
    select_list.append(_.ENABLE_INTEGRATION_SHOWS_WATCHLIST)
    select_list.append(_.ENABLE_INTEGRATION_SHOWS)

    selected = gui.select(_.ENABLE_LIBRARY_SHOWS, select_list)

    try:
        settings.setInt('library_shows', selected)
    except:
        settings.setInt('library_shows', 0)

    for type in CONST_LIBRARY['shows']:
        row = CONST_LIBRARY['shows'][type]

        if not gui.yes_no(message=_.ENABLE_LIBRARY_SHOWS + ": " + getattr(_, row['label'])):
            settings.setBool('library_shows_' + str(type), False)
        else:
            settings.setBool('library_shows_' + str(type), True)

    add_library_sources()

    gui.ok(message=_.DONE_REBOOT_REQUIRED)

@plugin.route()
def logout(**kwargs):
    if not gui.yes_no(message=_.LOGOUT_YES_NO):
        return

    profile_settings = load_profile(profile_id=1)
    profile_settings['pswd'] = ''
    profile_settings['username'] = ''
    save_profile(profile_id=1, profile=profile_settings)

    gui.refresh()

@plugin.route()
def play_dbitem(id, **kwargs):
    json_rpc("Player.Open", {"item":{"episodeid": int(id)}})
    
@plugin.route()
def play_video(type=None, channel=None, id=None, data=None, title=None, from_beginning=0, pvr=0, change_audio=0, **kwargs):
    profile_settings = load_profile(profile_id=1)
    from_beginning = int(from_beginning)
    pvr = int(pvr)
    change_audio = int(change_audio)

    profile_settings = load_profile(profile_id=1)
    profile_settings['rec_id'] = id
    save_profile(profile_id=1, profile=profile_settings)
    log('menu_play_video: saving rec_id') #2nd saving because it sometimes is using old id
    #RIF solved in api_play_url because play_token was called before updating id

    if not type or not len(str(type)) > 0:
        return False

    proxy_url = "http://127.0.0.1:11189/{provider}".format(provider=PROVIDER_NAME)

    if CONST_HAS['proxy']:
        code = 0

        try:
            test_proxy = api_download(url="{proxy_url}/status".format(proxy_url=proxy_url), type='get', headers=None, data=None, json_data=False, return_json=False)
            code = test_proxy['code']
        except:
            code = 404

        if not code or not code == 200:
            gui.ok(message=_.PROXY_NOT_SET)
            return False

    if CONST_HAS['startfrombeginning'] and not from_beginning == 1 and settings.getBool(key='ask_start_from_beginning') and gui.yes_no(message=_.START_FROM_BEGINNING):
        from_beginning = 1

    playdata = api_play_url(type=type, channel=channel, id=id, video_data=data, from_beginning=from_beginning, pvr=pvr, change_audio=change_audio)

    log(playdata)

    if not playdata or not check_key(playdata, 'path'):
        return False

    playdata['channel'] = channel
    playdata['title'] = title
    info = plugin_process_info(playdata)

    if pvr == 1:
        try:
            data = api_get_channels()

            info['image'] = data[str(channel)]['icon']
            info['image_large'] = data[str(channel)]['icon']
        except:
            pass

    path = playdata['path']
    license = playdata['license']

    log(path)
    log(license)

    if CONST_HAS['startfrombeginning'] and from_beginning == 1:
        playdata['properties']['seekTime'] = 0

        if ADDON_ID == 'plugin.video.tmobile':
            start = load_file(file='stream_start', isJSON=False)

            if start:
                time_diff = int(time.time()) - int(start)

                if time_diff > 0:
                    time_diff2 = 7190 - time_diff

                    if time_diff2 > 0:
                        playdata['properties']['seekTime'] = time_diff2
    else:
        remove_stream_start()

    try:
        os.remove(os.path.join(ADDON_PROFILE, 'stream_language'))
    except:
        pass

    plugin_check_devices()

    if check_key(playdata, 'mpd') and len(str(playdata['mpd'])) > 0:
        language_list = {}
        root = parseString(playdata['mpd'].encode('utf8'))
        mpd = root.getElementsByTagName("MPD")[0]
        select_list = []

        for adap_set in root.getElementsByTagName('AdaptationSet'):
            if 'audio' in adap_set.getAttribute('mimeType'):
                for stream in adap_set.getElementsByTagName("Representation"):
                    attrib = {}

                    for key in adap_set.attributes.keys():
                        attrib[key] = adap_set.getAttribute(key)

                    for key in stream.attributes.keys():
                        attrib[key] = stream.getAttribute(key)

                    if check_key(attrib, 'lang') and not check_key(language_list, attrib['lang']):
                        if check_key(AUDIO_LANGUAGES, attrib['lang']):
                            language_list[attrib['lang']] = AUDIO_LANGUAGES[attrib['lang']]
                        else:
                            language_list[attrib['lang']] = attrib['lang']

                        select_list.append(language_list[attrib['lang']])

        if len(language_list) > 1:
            selected = gui.select(_.SELECT_AUDIO_LANGUAGE, select_list)

            try:
                write_file(file='stream_language', data=select_list[selected], isJSON=False)
            except:
                pass

    if CONST_HAS['proxy']:
        real_url = "{hostscheme}://{netloc}".format(hostscheme=urlparse(path).scheme, netloc=urlparse(path).netloc)
        path = path.replace(real_url, proxy_url)
        write_file(file='stream_hostname', data=real_url, isJSON=False)

    playdata['path'] = path
    playdata['license'] = license

    item_inputstream, CDMHEADERS = plugin_process_playdata(playdata)

    write_file(file='stream_duration', data=info['duration'], isJSON=False)

    if pvr == 1:
        playdata['properties']['PVR'] = 1
    elif type == 'program' or type == 'vod':
        playdata['properties']['Replay'] = 1
    else:
        playdata['properties']['Live'] = 1
        playdata['properties']['Live_ID'] = channel
        playdata['properties']['Live_Channel'] = playdata['channel']

    listitem = plugin.Item(
        label = str(info['label1']),
        label2 = str(info['label2']),
        art = {
            'thumb': str(info['image']),
            'fanart': str(info['image_large'])
        },
        info = {
            'credits': info['credits'],
            'cast': info['cast'],
            'writer': info['writer'],
            'director': info['director'],
            'genre': info['genres'],
            'plot': str(info['description']),
            'duration': info['duration'],
            'mediatype': 'video',
            'year': info['year'],
            'sorttitle': str(info['label1']).upper(),
        },
        path = path,
        headers = CDMHEADERS,
        properties = playdata['properties'],
        inputstream = item_inputstream,
    )

    try:
        if settings.getInt(key='max_bandwidth') > 0:
            plugin._set_network_bandwidth()
    except:
        pass

    return listitem

@plugin.route()
def renew_token(**kwargs):
    data = {}

    for key, value in kwargs.items():
        data[key] = value

    mod_path = plugin_renew_token(data)
    log('renew token incoming, first data:')
    log(data)
    log('now mod_path (the function in util that builds the new url afaik)')
    log(mod_path)

@plugin.route()
def add_to_watchlist(id, program_type='', type='watchlist', series='', season='', **kwargs):
    if api_add_to_watchlist(id=id, series=series, season=season, program_type=program_type, type=type):
        gui.notification(CONST_WATCHLIST_CAPABILITY[type]['addsuccess'])
    else:
        gui.notification(CONST_WATCHLIST_CAPABILITY[type]['addfailed'])

@plugin.route()
def remove_from_watchlist(id, type='watchlist', **kwargs):
    if api_remove_from_watchlist(id=id, type=type):
        gui.refresh()
        gui.notification(CONST_WATCHLIST_CAPABILITY[type]['removesuccess'])
    else:
        gui.notification(CONST_WATCHLIST_CAPABILITY[type]['removefailed'])

@plugin.route()
def watchlist(type='watchlist', **kwargs):
    folder = plugin.Folder(title=CONST_WATCHLIST_CAPABILITY[type]['label'])

    data = api_list_watchlist(type=type)

    if data:
        processed = plugin_process_watchlist(data=data, type=type)

        if processed:
            items = []

            for ref in processed:
                currow = processed[ref]

                progress = {}

                if int(currow['progress']) > 0 and int(currow['duration']) > 0:
                    progress['TotalTime'] = str(currow['duration'])
                    progress['ResumeTime'] = str(int((int(currow['progress']) / 100) * (int(currow['duration']))))

                items.append(plugin.Item(
                    label = currow['label1'],
                    info = {
                        'plot': currow['description'],
                        'duration': currow['duration'],
                        'mediatype': currow['mediatype'],
                        'sorttitle': currow['label1'].upper(),
                    },
                    art = {
                        'thumb': currow['image'],
                        'fanart': currow['image_large']
                    },
                    path = currow['path'],
                    playable = currow['playable'],
                    properties = progress,
                    context = currow['context']
                ))

            folder.add_items(items)

    return folder

@plugin.route()
def watchlist_listing(label, id, search=0, type='watchlist', **kwargs):
    search = int(search)

    folder = plugin.Folder(title=label)

    data = api_watchlist_listing(id, type=type)

    if search == 0:
        id = None

    if data:
        processed = plugin_process_watchlist_listing(data=data, id=id, type=type)

        if processed:
            items = []

            for ref in processed:
                currow = processed[ref]

                items.append(plugin.Item(
                    label = currow['label1'],
                    info = {
                        'plot': currow['description'],
                        'duration': currow['duration'],
                        'mediatype': currow['mediatype'],
                        'sorttitle': currow['label1'].upper(),
                    },
                    art = {
                        'thumb': currow['image'],
                        'fanart': currow['image_large']
                    },
                    path = currow['path'],
                    playable = currow['playable'],
                    context = currow['context']
                ))

            folder.add_items(items)

    return folder

#Support functions
def get_live_channels(all=False):
    global backend
    channels = []

    data = api_get_channels()

    prefs = load_prefs(profile_id=1)

    if data:
        for currow in data:
            row = data[currow]

            path = plugin.url_for(func_or_url=play_video, type='channel', channel=row['id'], id=row['assetid'], _is_live=True)
            playable = True

            id = str(row['id'])

            if all or not prefs or not check_key(prefs, id) or prefs[id]['live'] == 1:
                context = []

                if CONST_HAS['startfrombeginning']:
                    context = [
                        (_.START_BEGINNING, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=play_video, type='channel', channel=id, id=str(row['assetid']), from_beginning=1, _is_live=True)), ),
                    ]

                context = [
                    (_.SELECT_AUDIO_LANGUAGE, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=play_video, type='channel', channel=id, id=str(row['assetid']), from_beginning=0, change_audio=1, _is_live=True)), ),
                ]

                channels.append({
                    'label': str(row['name']),
                    'channel': id,
                    'chno': str(row['channelno']),
                    'description': str(row['description']),
                    'image': str(row['icon']),
                    'path':  path,
                    'playable': playable,
                    'context': context,
                })

    return channels

def get_replay_channels(all=False):
    channels = []

    data = api_get_channels()

    prefs = load_prefs(profile_id=1)

    if data:
        for currow in data:
            row = data[currow]

            id = str(row['id'])

            if all or not prefs or not check_key(prefs, id) or int(prefs[id]['replay']) == 1:
                channels.append({
                    'label': str(row['name']),
                    'channel': id,
                    'chno': str(row['channelno']),
                    'description': str(row['description']),
                    'image': str(row['icon']),
                    'path': plugin.url_for(func_or_url=replaytv_by_day, image=str(row['icon']), description=str(row['description']), label=str(row['name']), station=id),
                    'playable': False,
                    'context': [],
                })

    return channels

def process_replaytv_list(character, start=0, movies=0):
    movies = int(movies)

    now = datetime.datetime.now(pytz.timezone("Europe/Amsterdam"))
    sevendays = datetime.datetime.now(pytz.timezone("Europe/Amsterdam")) - datetime.timedelta(days=7)
    nowstamp = int((now - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())
    sevendaysstamp = int((sevendays - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())

    data = api_get_channels()

    prefs = load_prefs(profile_id=1)
    channels_ar = []

    if prefs:
        for row in prefs:
            currow = prefs[row]

            if not check_key(data, str(row)):
                continue

            if int(currow['replay']) == 1:
                channels_ar.append(row)

    if len(str(character)) > 0:
        data = api_get_list_by_first(first=character, start=nowstamp, end=sevendaysstamp, channels=channels_ar, movies=movies)
    else:
        data = api_get_list(start=nowstamp, end=sevendaysstamp, channels=channels_ar, movies=movies)

    start = int(start)
    items = []
    count = 0
    item_count = 0

    if not data:
        return {'items': items, 'count': item_count, 'count2': count, 'total': 0}

    for currow in data:
        row = data[currow]

        if item_count == settings.getInt('item_count'):
            break

        count += 1

        if count < start + 1:
            continue

        item_count += 1

        label = str(row['title'])
        idtitle = str(currow)
        image = str(str(row['icon']).replace(CONST_IMAGES['replay']['replace'], CONST_IMAGES['replay']['small'])).strip()

        items.append(plugin.Item(
            label = label,
            info = {
                'sorttitle': label.upper(),
            },
            art = {
                'thumb': image,
                'fanart': image
            },
            path = plugin.url_for(func_or_url=replaytv_item, label=label, idtitle=idtitle, start=0),
        ))

    returnar = {'items': items, 'count': item_count, 'count2': count, 'total': len(data)}

    return returnar

def process_replaytv_search(search, movies=0):
    movies = int(movies)
    now = datetime.datetime.now(pytz.timezone("Europe/Amsterdam"))
    sevendays = datetime.datetime.now(pytz.timezone("Europe/Amsterdam")) - datetime.timedelta(days=7)
    nowstamp = int((now - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())
    sevendaysstamp = int((sevendays - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())

    search = str(search)

    data = api_get_channels()

    prefs = load_prefs(profile_id=1)
    channels_ar = []

    if prefs:
        for row in prefs:
            currow = prefs[row]

            if not check_key(data, str(row)):
                continue

            if int(currow['replay']) == 1:
                channels_ar.append(row)

    data = api_get_list(start=nowstamp, end=sevendaysstamp, channels=channels_ar, movies=movies)

    items = []

    if not data:
        return {'items': items}

    for currow in data:
        row = data[currow]

        title = str(row['title'])
        image = str(str(row['icon']).replace(CONST_IMAGES['replay']['replace'], CONST_IMAGES['replay']['small'])).strip()

        fuzz_set = fuzz.token_set_ratio(title, search)
        fuzz_partial = fuzz.partial_ratio(title, search)
        fuzz_sort = fuzz.token_sort_ratio(title, search)

        if (fuzz_set + fuzz_partial + fuzz_sort) > 160:
            label = title + ' (ReplayTV)'
            idtitle = str(currow)

            items.append(plugin.Item(
                label = label,
                info = {
                    'sorttitle': label.upper(),
                },
                art = {
                    'thumb': image,
                    'fanart': image
                },
                properties = {"fuzz_set": fuzz_set, "fuzz_sort": fuzz_sort, "fuzz_partial": fuzz_partial, "fuzz_total": fuzz_set + fuzz_partial + fuzz_sort},
                path = plugin.url_for(func_or_url=replaytv_item, label=label, idtitle=idtitle, start=0),
            ))

    returnar = {'items': items}

    return returnar

def process_replaytv_content(station, day=0, start=0):
    day = int(day)
    start = int(start)
    curdate = datetime.date.today() - datetime.timedelta(days=day)

    startDate = convert_datetime_timezone(datetime.datetime(curdate.year, curdate.month, curdate.day, 0, 0, 0), "Europe/Amsterdam", "UTC")
    endDate = convert_datetime_timezone(datetime.datetime(curdate.year, curdate.month, curdate.day, 23, 59, 59), "Europe/Amsterdam", "UTC")
    startTimeStamp = int((startDate - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())
    endTimeStamp = int((endDate - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())

    data = api_get_epg_by_date_channel(date=curdate.strftime('%Y') + curdate.strftime('%m') + curdate.strftime('%d'), channel=station)

    items = []
    count = 0
    item_count = 0

    if not data:
        return {'items': items, 'count': item_count, 'count2': count, 'total': 0}

    for currow in data:
        row = data[currow]

        if item_count == settings.getInt('item_count'):
            break

        count += 1

        if count < start + 1:
            continue

        context = []
        item_count += 1
        channel = str(row['channel'])

        startT = datetime.datetime.fromtimestamp(int(row['start']))
        startT = convert_datetime_timezone(startT, "Europe/Amsterdam", "Europe/Amsterdam")
        endT = datetime.datetime.fromtimestamp(int(row['end']))
        endT = convert_datetime_timezone(endT, "Europe/Amsterdam", "Europe/Amsterdam")

        if endT < (datetime.datetime.now(pytz.timezone("Europe/Amsterdam")) - datetime.timedelta(days=7)):
            continue

        label = "{time} - {title}".format(time=startT.strftime("%H:%M"), title=row['title'])

        description = str(row['description'])

        duration = int((endT - startT).total_seconds())

        image = str(str(row['icon']).replace(CONST_IMAGES['replay']['replace'], CONST_IMAGES['replay']['small'])).strip()
        program_id = str(row['program_id'])
        program_type = 'program'

        profile_settings = load_profile(profile_id=1)
        profile_settings['replay_id'] = program_id
        save_profile(profile_id=1, profile=profile_settings)

        if check_key(CONST_WATCHLIST, 'replay') and check_key(CONST_WATCHLIST['replay'], program_type) and CONST_WATCHLIST_CAPABILITY[CONST_WATCHLIST['replay'][program_type]['type']]['add'] == 1:
            context.append((CONST_WATCHLIST_CAPABILITY[CONST_WATCHLIST['replay'][program_type]['type']]['addlist'], 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=add_to_watchlist, id=program_id, program_type=program_type, type=CONST_WATCHLIST['replay'][program_type]['type'])), ))

        context.append((_.SELECT_AUDIO_LANGUAGE, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=play_video, type='program', channel=channel, id=program_id, change_audio=1)), ))

        items.append(plugin.Item(
            label = label,
            info = {
                'plot': description,
                'duration': duration,
                'mediatype': 'video',
                'sorttitle': label.upper(),
            },
            art = {
                'thumb': image,
                'fanart': image
            },
            path = plugin.url_for(func_or_url=play_video, type='program', channel=channel, id=program_id),
            context = context,
            playable = True,
        ))

    returnar = {'items': items, 'count': item_count, 'count2': count, 'total': len(data)}

    return returnar

def process_replaytv_list_content(label, idtitle, start=0):
    start = int(start)

    now = datetime.datetime.now(pytz.timezone("Europe/Amsterdam"))
    sevendays = datetime.datetime.now(pytz.timezone("Europe/Amsterdam")) - datetime.timedelta(days=7)
    nowstamp = int((now - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())
    sevendaysstamp = int((sevendays - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())

    data = api_get_channels()

    prefs = load_prefs(profile_id=1)
    channels_ar = []
    channels_ar2 = {}

    if prefs:
        for row in prefs:
            currow = prefs[row]

            if not check_key(data, str(row)):
                continue

            channels_ar2[str(row)] = data[str(row)]['name']

            if int(currow['replay']) == 1:
                channels_ar.append(row)

    data = api_get_epg_by_idtitle(idtitle=idtitle, start=nowstamp, end=sevendaysstamp, channels=channels_ar)

    items = []
    count = 0
    item_count = 0

    if not data:
        return {'items': items, 'count': item_count, 'count2': count, 'total': 0}

    for currow in data:
        row = data[currow]

        if item_count == settings.getInt('item_count'):
            break

        count += 1

        if count < start + 1:
            continue

        context = []
        item_count += 1

        channel = str(row['channel'])

        startT = datetime.datetime.fromtimestamp(int(row['start']))
        startT = convert_datetime_timezone(startT, "Europe/Amsterdam", "Europe/Amsterdam")
        endT = datetime.datetime.fromtimestamp(int(row['end']))
        endT = convert_datetime_timezone(endT, "Europe/Amsterdam", "Europe/Amsterdam")

        if xbmc.getLanguage(xbmc.ISO_639_1) == 'nl':
            itemlabel = '{weekday} {day} {month} {yearhourminute} '.format(weekday=date_to_nl_dag(startT), day=startT.strftime("%d"), month=date_to_nl_maand(startT), yearhourminute=startT.strftime("%Y %H:%M"))
        else:
            itemlabel = startT.strftime("%A %d %B %Y %H:%M ").capitalize()

        itemlabel += str(row['title'])

        try:
            itemlabel += " ({channelstr})".format(channelstr=channels_ar2[channel])
        except:
            pass

        description = str(row['description'])
        duration = int((endT - startT).total_seconds())
        image = str(str(row['icon']).replace(CONST_IMAGES['replay']['replace'], CONST_IMAGES['replay']['small'])).strip()
        program_id = str(row['program_id'])
        program_type = 'program'

        if check_key(CONST_WATCHLIST, 'replay') and check_key(CONST_WATCHLIST['replay'], program_type) and CONST_WATCHLIST_CAPABILITY[CONST_WATCHLIST['replay'][program_type]['type']]['add'] == 1:
            context.append((CONST_WATCHLIST_CAPABILITY[CONST_WATCHLIST['replay'][program_type]['type']]['addlist'], 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=add_to_watchlist, id=program_id, program_type=program_type, type=CONST_WATCHLIST['replay'][program_type]['type'])), ))

        context.append((_.SELECT_AUDIO_LANGUAGE, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=play_video, type='program', channel=channel, id=program_id, change_audio=1)), ))

        items.append(plugin.Item(
            label = itemlabel,
            info = {
                'plot': description,
                'duration': duration,
                'mediatype': 'video',
                'sorttitle': itemlabel.upper(),
            },
            art = {
                'thumb': image,
                'fanart': image
            },
            path = plugin.url_for(func_or_url=play_video, type='program', channel=channel, id=program_id),
            playable = True,
            context = context
        ))

    returnar = {'items': items, 'count': item_count, 'count2': count, 'total': len(data)}

    return returnar

def process_vod_content(data, start=0, search=None, type=None, character=None, genre=None, online=0):
    subscription_filter = plugin_vod_subscription_filter()

    start = int(start)
    online = int(online)
    type = str(type)
    type2 = data

    items = []

    if not online == 1:
        count = 0
    else:
        count = start

    item_count = 0

    if online > 0:
        if search:
            data = api_search(query=search)
        else:
            data = api_vod_download(type=data, start=start)

            if data:
                data = plugin_process_vod(data=data, start=start)
    else:
        data = api_get_vod_by_type(type=data, character=character, genre=genre, subscription_filter=subscription_filter, menu=0)

    if not data:
        return {'items': items, 'count': item_count, 'count2': count, 'total': 0}

    for currow in data:
        row = data[currow]

        if item_count == settings.getInt('item_count'):
            break

        count += 1

        if not online == 1 and count < start + 1:
            continue

        id = str(row['id'])

        profile_settings = load_profile(profile_id=1)
        profile_settings['search_id'] = id
        save_profile(profile_id=1, profile=profile_settings)
        
        label = str(row['title'])

        if search and not online == 1:
            fuzz_set = fuzz.token_set_ratio(label,search)
            fuzz_partial = fuzz.partial_ratio(label,search)
            fuzz_sort = fuzz.token_sort_ratio(label,search)

            if (fuzz_set + fuzz_partial + fuzz_sort) > 160:
                properties = {"fuzz_set": fuzz.token_set_ratio(label,search), "fuzz_sort": fuzz.token_sort_ratio(label,search), "fuzz_partial": fuzz.partial_ratio(label,search), "fuzz_total": fuzz.token_set_ratio(label,search) + fuzz.partial_ratio(label,search) + fuzz.token_sort_ratio(label,search)}
                label += " ({type})".format(type=type)
            else:
                continue

        context = []
        item_count += 1

        properties = []
        description = str(row['description'])
        duration = 0

        if row['duration'] and len(str(row['duration'])) > 0:
            duration = int(row['duration'])

        image = str(str(row['icon']).replace(CONST_IMAGES['vod']['replace'], CONST_IMAGES['vod']['small'])).strip()
        program_type = str(row['type'])

        if check_key(CONST_WATCHLIST, 'vod') and check_key(CONST_WATCHLIST['vod'], program_type) and CONST_WATCHLIST_CAPABILITY[CONST_WATCHLIST['vod'][program_type]['type']]['add'] == 1:
            context.append((CONST_WATCHLIST_CAPABILITY[CONST_WATCHLIST['vod'][program_type]['type']]['addlist'], 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=add_to_watchlist, id=id, program_type=program_type, type=CONST_WATCHLIST['vod'][program_type]['type'])), ))

        if program_type == "show" or program_type == "Serie" or program_type == "series":
            path = plugin.url_for(func_or_url=vod_series, type=type2, label=label, id=id)
            info = {'plot': description, 'sorttitle': label.upper()}
            playable = False
        elif program_type == "event":
            path = plugin.url_for(func_or_url=vod_season, label=label, series=0, id=id)
            info = {'plot': description, 'sorttitle': label.upper()}
            playable = False
        elif program_type == "Epg":
            context.append((_.SELECT_AUDIO_LANGUAGE, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=play_video, type='program', channel=None, id=id, change_audio=1)), ))
            path = plugin.url_for(func_or_url=play_video, type='program', channel=None, id=id)
            info = {'plot': description, 'duration': duration, 'mediatype': 'video', 'sorttitle': label.upper()}
            playable = True
        elif program_type == "movie" or program_type == "Vod":
            context.append((_.SELECT_AUDIO_LANGUAGE, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=play_video, type='vod', channel=None, id=id, change_audio=1)), ))
            path = plugin.url_for(func_or_url=play_video, type='vod', channel=None, id=id)
            info = {'plot': description, 'duration': duration, 'mediatype': 'video', 'sorttitle': label.upper()}
            playable = True
        else:
            continue

        items.append(plugin.Item(
            label = label,
            properties = properties,
            info = info,
            art = {
                'thumb': image,
                'fanart': image
            },
            path = path,
            playable = playable,
            context = context
        ))

    if not online == 1:
        total = len(data)
    else:
        total = int(len(data) + start)

    returnar = {'items': items, 'count': item_count, 'count2': count, 'total': total}

    return returnar

def process_vod_menu_content(data, start=0, search=None, type=None, character=None, genre=None, online=0):
    subscription_filter = plugin_vod_subscription_filter()

    start = int(start)
    type = str(type)
    type2 = data

    items = []

    if not online == 1:
        count = 0
    else:
        count = start

    item_count = 0

    if online > 0:
        if search:
            data = api_search(query=search)
        else:
            data = api_vod_download(type=data, start=start)

            if data:
                data = plugin_process_vod(data=data, start=start)
    else:
        data = api_get_vod_by_type(type=data, character=character, genre=genre, subscription_filter=subscription_filter, menu=1)

    if not data:
        return {'items': items, 'count': item_count, 'count2': count, 'total': 0}

    for currow in data['menu']:
        row = data['menu'][currow]

        id = str(currow)
        label = str(row['label'])
        menu_type = str(row['type'])
        image = str(row['image'])

        if menu_type == 'content':
            path = plugin.url_for(func_or_url=vod, file=id, label=label, start=0, character=character, online=online, az=0, menu=0)
            playable = False
        elif menu_type == 'video':
            path = plugin.url_for(func_or_url=play_video, type='vod', channel=None, id=id)
            info = {'mediatype': 'video', 'sorttitle': label.upper()}
            playable = True
        elif menu_type == 'menu':
            path = plugin.url_for(func_or_url=vod, file=id, label=label, start=0, character=character, online=online, az=0, menu=1)
            playable = False
        else:
            continue

        items.append(plugin.Item(
            label = label,
            art = {
                'thumb': image,
                'fanart': image
            },
            path = path,
            playable = playable,
        ))

    if not online == 1:
        total = len(data)
    else:
        total = int(len(data) + start)

    returnar = {'items': items, 'count': item_count, 'count2': count, 'total': total}

    return returnar

def _sort_replay_items(element):
    return element.get_li().getProperty('fuzz_total')

def check_first():
    profile_settings = load_profile(profile_id=1)

    if not check_key(profile_settings, 'setup_complete'):
        if CONST_FIRST_BOOT['erotica'] == True:
            if gui.yes_no(message=_.DISABLE_EROTICA) == False:
                settings.setBool(key='disableErotica', value=False)
            else:
                settings.setBool(key='disableErotica', value=True)

        if CONST_FIRST_BOOT['minimal'] == True:
            if gui.yes_no(message=_.MINIMAL_CHANNELS) == False:
                settings.setBool(key='minimalChannels', value=False)
            else:
                settings.setBool(key='minimalChannels', value=True)

        if CONST_FIRST_BOOT['regional'] == True:
            if gui.yes_no(message=_.DISABLE_REGIONAL) == False:
                settings.setBool(key='disableRegionalChannels', value=False)
            else:
                settings.setBool(key='disableRegionalChannels', value=True)

        if CONST_FIRST_BOOT['home'] == True:
            if gui.yes_no(message=_.HOME_CONNECTION) == True:
                settings.setBool(key='homeConnection', value=True)
            else:
                settings.setBool(key='homeConnection', value=False)

        profile_settings['setup_complete'] = 1
        save_profile(profile_id=1, profile=profile_settings)

    plugin_check_first()

def remove_stream_start():
    remove_file(file='stream_start', ext=False)