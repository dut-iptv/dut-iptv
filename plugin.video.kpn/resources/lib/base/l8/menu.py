import _strptime

import datetime, json, os, pytz, re, string, sys, time, xbmc, xbmcplugin

from fuzzywuzzy import fuzz
from resources.lib.api import api_add_to_watchlist, api_list_watchlist, api_login, api_play_url, api_remove_from_watchlist, api_search, api_vod_download, api_vod_season, api_vod_seasons, api_watchlist_listing
from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE, PROVIDER_NAME
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, clear_old, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, disable_prefs, get_credentials, load_file, load_profile, load_prefs, save_profile, save_prefs, set_credentials, write_file
from resources.lib.base.l4 import gui
from resources.lib.base.l4.exceptions import Error
from resources.lib.base.l5.api import api_download, api_get_channels, api_get_epg_by_date_channel, api_get_epg_by_idtitle, api_get_list, api_get_list_by_first, api_get_vod_by_type
from resources.lib.base.l7 import plugin
from resources.lib.constants import CONST_BASE_HEADERS, CONST_ONLINE_SEARCH, CONST_VOD_CAPABILITY, CONST_WATCHLIST
from resources.lib.util import plugin_ask_for_creds, plugin_login_error, plugin_post_login, plugin_process_info, plugin_process_playdata, plugin_process_watchlist, plugin_process_watchlist_listing, plugin_renew_token, plugin_vod_subscription_filter

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

try:
    unicode
except NameError:
    unicode = str

ADDON_HANDLE = int(sys.argv[1])
backend = ''

@plugin.route('')
def home(**kwargs):
    clear_old()
    check_first()

    profile_settings = load_profile(profile_id=1)

    folder = plugin.Folder()

    if profile_settings and check_key(profile_settings, 'pswd') and len(profile_settings['pswd']) > 0:
        folder.add_item(label=_(_.LIVE_TV, _bold=True),  path=plugin.url_for(func_or_url=live_tv))
        folder.add_item(label=_(_.CHANNELS, _bold=True), path=plugin.url_for(func_or_url=replaytv))

        if settings.getBool('showMoviesSeries'):
            for vod_entry in CONST_VOD_CAPABILITY:
                folder.add_item(label=_(vod_entry['label'], _bold=True), path=plugin.url_for(func_or_url=vod, file=vod_entry['file'], label=vod_entry['label'], start=vod_entry['start'], online=vod_entry['online'], split=vod_entry['split']))

        if CONST_WATCHLIST:
            folder.add_item(label=_(_.WATCHLIST, _bold=True), path=plugin.url_for(func_or_url=watchlist))

        folder.add_item(label=_(_.SEARCH, _bold=True), path=plugin.url_for(func_or_url=search_menu))

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
        save_profile(profile_id=1, profile=profile_settings)

        gui.ok(message=_.LOGIN_SUCCESS)

        api_get_channels()
        plugin_post_login()

    gui.refresh()

@plugin.route()
def live_tv(**kwargs):
    folder = plugin.Folder(title=_.LIVE_TV)

    for row in get_live_channels():
        folder.add_item(
            label = row['label'],
            info = {'plot': row['description']},
            art = {'thumb': row['image']},
            path = row['path'],
            playable = row['playable'],
            context = row['context'],
        )

    return folder

@plugin.route()
def replaytv(**kwargs):
    folder = plugin.Folder(title=_.CHANNELS)

    folder.add_item(
        label = _.PROGSAZ,
        info = {'plot': _.PROGSAZDESC},
        path = plugin.url_for(func_or_url=replaytv_alphabetical),
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
def replaytv_alphabetical(**kwargs):
    folder = plugin.Folder(title=_.PROGSAZ)
    label = _.OTHERTITLES

    folder.add_item(
        label = label,
        info = {'plot': _.OTHERTITLESDESC},
        path = plugin.url_for(func_or_url=replaytv_list, label=label, start=0, character='other'),
    )

    for character in string.ascii_uppercase:
        label = _.TITLESWITH + character

        folder.add_item(
            label = label,
            info = {'plot': _.TITLESWITHDESC + character},
            path = plugin.url_for(func_or_url=replaytv_list, label=label, start=0, character=character),
        )

    return folder

@plugin.route()
def replaytv_list(character, label='', start=0, **kwargs):
    start = int(start)
    folder = plugin.Folder(title=label)

    processed = process_replaytv_list(character=character, start=start)

    if check_key(processed, 'items'):
        folder.add_items(processed['items'])

    if check_key(processed, 'total') and check_key(processed, 'count2') and processed['total'] > processed['count2']:
        folder.add_item(
            label = _(_.NEXT_PAGE, _bold=True),
            properties = {'SpecialSort': 'bottom'},
            path = plugin.url_for(func_or_url=replaytv_list, character=character, label=label, start=processed['count2']),
        )

    return folder

@plugin.route()
def replaytv_by_day(label='', image='', description='', station='', **kwargs):
    folder = plugin.Folder(title=label)

    for x in range(0, 7):
        curdate = datetime.date.today() - datetime.timedelta(days=x)

        itemlabel = ''

        if x == 0:
            itemlabel = _.TODAY + " - "
        elif x == 1:
            itemlabel = _.YESTERDAY + " - "

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
def vod(file, label, start=0, character=None, online=0, split=0, **kwargs):
    start = int(start)
    online = int(online)
    split = int(split)

    if split == 1:
        folder = plugin.Folder(title=_.PROGSAZ)
        label = _.OTHERTITLES

        folder.add_item(
            label = label,
            info = {'plot': _.OTHERTITLESDESC},
            path = plugin.url_for(func_or_url=vod, file=file, label=label, start=start, character='other', online=online, split=0),
        )

        for character in string.ascii_uppercase:
            label = _.TITLESWITH + character

            folder.add_item(
                label = label,
                info = {'plot': _.TITLESWITHDESC + character},
                path = plugin.url_for(func_or_url=vod, file=file, label=label, start=start, character=character, online=online, split=0),
            )

        return folder
    else:
        folder = plugin.Folder(title=label)

        processed = process_vod_content(data=file, start=start, type=label, character=character, online=online)

        if check_key(processed, 'items'):
            folder.add_items(processed['items'])

        if check_key(processed, 'total') and check_key(processed, 'count2') and processed['total'] > processed['count2']:
            folder.add_item(
                label = _(_.NEXT_PAGE, _bold=True),
                properties = {'SpecialSort': 'bottom'},
                path = plugin.url_for(func_or_url=vod, file=file, label=label, start=processed['count2'], character=character, online=online, split=split),
            )

        return folder

@plugin.route()
def vod_series(label, type, id, **kwargs):
    folder = plugin.Folder(title=label)

    items = []
    context = []

    seasons = api_vod_seasons(type, id)

    title = label

    if seasons and check_key(seasons, 'seasons'):
        if CONST_WATCHLIST and check_key(seasons, 'watchlist'):
            context.append((_.ADD_TO_WATCHLIST, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=add_to_watchlist, id=seasons['watchlist'], type='group')), ))

        if seasons['type'] == "seasons":
            for season in seasons['seasons']:
                label = _.SEASON + " " + unicode(season['seriesNumber']).replace('Seizoen ', '')

                items.append(plugin.Item(
                    label = label,
                    info = {'plot': unicode(season['description']), 'sorttitle': label.upper()},
                    art = {
                        'thumb': unicode(season['image']),
                        'fanart': unicode(season['image'])
                    },
                    path = plugin.url_for(func_or_url=vod_season, label=label, series=id, id=unicode(season['id'])),
                    context = context,
                ))
        else:
            for episode in seasons['seasons']:
                items.append(plugin.Item(
                    label = unicode(episode['label']),
                    info = {
                        'plot': unicode(episode['description']),
                        'duration': episode['duration'],
                        'mediatype': 'video',
                        'sorttitle': unicode(episode['label']).upper(),
                    },
                    art = {
                        'thumb': unicode(episode['image']),
                        'fanart': unicode(episode['image'])
                    },
                    path = plugin.url_for(func_or_url=play_video, type='vod', channel=None, id=unicode(episode['id'])),
                    context = context,
                    playable = True,
                ))

        folder.add_items(items)

    return folder

@plugin.route()
def vod_season(label, series, id, **kwargs):
    folder = plugin.Folder(title=label)

    items = []

    season = api_vod_season(series=series, id=id)

    for episode in season:
        items.append(plugin.Item(
            label = unicode(episode['label']),
            info = {
                'plot': unicode(episode['description']),
                'duration': episode['duration'],
                'mediatype': 'video',
                'sorttitle': unicode(episode['label']).upper(),
            },
            art = {
                'thumb': unicode(episode['image']),
                'fanart': unicode(episode['image'])
            },
            path = plugin.url_for(func_or_url=play_video, type='vod', channel=None, id=unicode(episode['id']), data=json.dumps(episode)),
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

    if CONST_ONLINE_SEARCH:
        folder.add_item(
            label= label + " (Online)",
            path=plugin.url_for(func_or_url=online_search)
        )

    profile_settings = load_profile(profile_id=1)

    for x in range(1, 10):
        try:
            if check_key(profile_settings, 'search' + unicode(x)):
                searchstr = profile_settings['search' + unicode(x)]
            else:
                searchstr = ''

            if searchstr != '':
                label = unicode(searchstr)
                path = plugin.url_for(func_or_url=search, query=searchstr)

                if CONST_ONLINE_SEARCH:
                    if check_key(profile_settings, 'search_type' + unicode(x)):
                        type = profile_settings['search_type' + unicode(x)]
                    else:
                        type = 0

                    if type == 1:
                        label = unicode(searchstr) + ' (Online)'
                        path = plugin.url_for(func_or_url=online_search, query=searchstr)

                folder.add_item(
                    label = label,
                    info = {'plot': _(_.SEARCH_FOR, query=searchstr)},
                    path = path,
                )
        except:
            pass

    return folder

@plugin.route()
def search(query=None, **kwargs):
    items = []

    if not query:
        query = gui.input(message=_.SEARCH, default='').strip()

        if not query:
            return

        profile_settings = load_profile(profile_id=1)

        for x in reversed(range(2, 10)):
            if check_key(profile_settings, 'search' + unicode(x - 1)):
                profile_settings['search' + unicode(x)] = profile_settings['search' + unicode(x - 1)]
            else:
                profile_settings['search' + unicode(x)] = ''

        profile_settings['search1'] = query

        if CONST_ONLINE_SEARCH:
            for x in reversed(range(2, 10)):
                if check_key(profile_settings, 'search_type' + unicode(x - 1)):
                    profile_settings['search_type' + unicode(x)] = profile_settings['search_type' + unicode(x - 1)]
                else:
                    profile_settings['search_type' + unicode(x)] = 0

            profile_settings['search_type1'] = 0

        save_profile(profile_id=1, profile=profile_settings)
    else:
        query = unicode(query)

    folder = plugin.Folder(title=_(_.SEARCH_FOR, query=query))

    processed = process_replaytv_search(search=query)
    items += processed['items']

    if settings.getBool('showMoviesSeries'):
        for vod_entry in CONST_VOD_CAPABILITY:
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
            if check_key(profile_settings, 'search' + unicode(x - 1)):
                profile_settings['search' + unicode(x)] = profile_settings['search' + unicode(x - 1)]
            else:
                profile_settings['search' + unicode(x)] = ''

            if check_key(profile_settings, 'search_type' + unicode(x - 1)):
                profile_settings['search_type' + unicode(x)] = profile_settings['search_type' + unicode(x - 1)]
            else:
                profile_settings['search_type' + unicode(x)] = 0

        profile_settings['search1'] = query
        profile_settings['search_type1'] = 1

        save_profile(profile_id=1, profile=profile_settings)
    else:
        query = unicode(query)

    folder = plugin.Folder(title=_(_.SEARCH_FOR, query=query))

    processed = process_vod_content(data=None, start=0, search=query, type='Online', online=1)
    items += processed['items']

    items[:] = sorted(items, key=_sort_replay_items, reverse=True)
    items = items[:25]

    folder.add_items(items)

    return folder

@plugin.route()
def settings_menu(**kwargs):
    folder = plugin.Folder(title=_.SETTINGS)

    folder.add_item(label=_.CHANNEL_PICKER, path=plugin.url_for(func_or_url=channel_picker_menu))
    folder.add_item(label=_.SET_KODI, path=plugin.url_for(func_or_url=plugin._set_settings_kodi))
    folder.add_item(label=_.INSTALL_WV_DRM, path=plugin.url_for(func_or_url=plugin._ia_install))
    folder.add_item(label=_.RESET_SESSION, path=plugin.url_for(func_or_url=login, ask=0))
    folder.add_item(label=_.RESET, path=plugin.url_for(func_or_url=reset_addon))
    folder.add_item(label=_.LOGOUT, path=plugin.url_for(func_or_url=logout))

    folder.add_item(label="Addon " + _.SETTINGS, path=plugin.url_for(func_or_url=plugin._settings))

    return folder

@plugin.route()
def channel_picker_menu(**kwargs):
    folder = plugin.Folder(title=_.CHANNEL_PICKER)

    folder.add_item(label=_.LIVE_TV, path=plugin.url_for(func_or_url=channel_picker, type='live'))
    folder.add_item(label=_.CHANNELS, path=plugin.url_for(func_or_url=channel_picker, type='replay'))
    folder.add_item(label=_.DISABLE_EROTICA, path=plugin.url_for(func_or_url=disable_prefs_menu, type='erotica'))
    folder.add_item(label=_.DISABLE_MINIMAL, path=plugin.url_for(func_or_url=disable_prefs_menu, type='minimal'))
    folder.add_item(label=_.DISABLE_REGIONAL2, path=plugin.url_for(func_or_url=disable_prefs_menu, type='regional'))

    if PROVIDER_NAME == 'kpn':
        folder.add_item(label=_.DISABLE_HOME_CONNECTION, path=plugin.url_for(func_or_url=disable_prefs_menu, type='home_only'))

    return folder

@plugin.route()
def disable_prefs_menu(type, **kwargs):
    disable_prefs(type=type, channels=api_get_channels())

    xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"GUI.ActivateWindow","params":{"window":"videos","parameters":["plugin://' + unicode(ADDON_ID) + '/?_=channel_picker_menu"]}}')

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
    type = unicode(type)

    for row in rows:
        id = unicode(row['channel'])

        if not prefs or not check_key(prefs, id) or prefs[id][type] == 1:
            color = 'green'
        else:
            color = 'red'

        label = _(unicode(row['label']), _bold=True, _color=color)

        folder.add_item(
            label = label,
            art = {'thumb': unicode(row['image'])},
            path = plugin.url_for(func_or_url=change_channel, type=type, id=id, change=0),
            playable = False,
        )

    return folder

@plugin.route()
def change_channel(type, id, change, **kwargs):
    change = int(change)

    if not id or len(unicode(id)) == 0 or not type or len(unicode(type)) == 0:
        return False

    prefs = load_prefs(profile_id=1)
    id = unicode(id)
    type = unicode(type)

    data = api_get_channels()

    if data and check_key(data, id) and prefs and check_key(prefs, id) and int(prefs[id][type]) == 0:
        if type == 'replay' and int(data[id]['replay']) == 0:
            gui.ok(message=_.EXPLAIN_NO_REPLAY)
            return False
        elif settings.getBool(key='homeConnection') == False and int(data[id]['home_only']) == 1:
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

    if change == 0:
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

    xbmc.executeJSONRPC('{{"jsonrpc":"2.0","id":1,"method":"GUI.ActivateWindow","params":{{"window":"videos","parameters":["plugin://' + unicode(ADDON_ID) + '/?_=channel_picker&type=' + type + '"]}}}}')

@plugin.route()
def reset_addon(**kwargs):
    plugin._reset()
    gui.refresh()

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
def play_video(type=None, channel=None, id=None, data=None, title=None, from_beginning=0, pvr=0, **kwargs):
    profile_settings = load_profile(profile_id=1)
    from_beginning = int(from_beginning)
    pvr = int(pvr)

    if not type or not len(unicode(type)) > 0:
        return False

    proxy_url = "http://127.0.0.1:11189/{provider}".format(provider=PROVIDER_NAME)

    code = 0

    try:
        test_proxy = api_download(url=proxy_url + "/status", type='get', headers=None, data=None, json_data=False, return_json=False)
        code = test_proxy['code']
    except:
        code = 404

    if not code or not code == 200:
        gui.ok(message=_.PROXY_NOT_SET)
        return False

    playdata = api_play_url(type=type, channel=channel, id=id, video_data=data, from_beginning=from_beginning, pvr=pvr)

    if not playdata or not check_key(playdata, 'path'):
        return False

    playdata['channel'] = channel
    playdata['title'] = title

    if check_key(playdata, 'alt_path') and (from_beginning == 1 or (settings.getBool(key='ask_start_from_beginning') and gui.yes_no(message=_.START_FROM_BEGINNING, heading=playdata['title']))):
        path = playdata['alt_path']
        license = playdata['alt_license']
    else:
        path = playdata['path']
        license = playdata['license']

    real_url = "{hostscheme}://{netloc}".format(hostscheme=urlparse(path).scheme, netloc=urlparse(path).netloc)

    path = path.replace(real_url, proxy_url)
    playdata['path'] = path
    playdata['license'] = license

    item_inputstream, CDMHEADERS = plugin_process_playdata(playdata)

    info = plugin_process_info(playdata)

    write_file(file='stream_hostname', data=real_url, isJSON=False)
    write_file(file='stream_duration', data=info['duration'], isJSON=False)

    listitem = plugin.Item(
        label = info['label1'],
        label2 = info['label2'],
        art = {
            'thumb': unicode(info['image']),
            'fanart': unicode(info['image_large'])
        },
        info = {
            'credits': info['credits'],
            'cast': info['cast'],
            'writer': info['writer'],
            'director': info['director'],
            'genre': info['genres'],
            'plot': info['description'],
            'duration': info['duration'],
            'mediatype': 'video',
            'year': info['year'],
            'sorttitle': info['label1'].upper(),
        },
        path = path,
        headers = CDMHEADERS,
        inputstream = item_inputstream,
    )

    return listitem

@plugin.route()
def renew_token(**kwargs):
    data = {}

    for key, value in kwargs.items():
        data[key] = value

    mod_path = plugin_renew_token(data)

    listitem = plugin.Item(
        path = mod_path,
    )

    newItem = listitem.get_li()

    xbmcplugin.addDirectoryItem(ADDON_HANDLE, mod_path, newItem)
    xbmcplugin.endOfDirectory(ADDON_HANDLE, cacheToDisc=False)

    if xbmc.Monitor().waitForAbort(0.1):
        return None

@plugin.route()
def api_add_to_watchlist(id, type, **kwargs):
    if api_add_to_watchlist(id=id, type=type):
        gui.notification(_.ADDED_TO_WATCHLIST)
    else:
        gui.notification(_.ADD_TO_WATCHLIST_FAILED)

@plugin.route()
def api_remove_from_watchlist(id, **kwargs):
    if api_remove_from_watchlist(id=id):
        gui.refresh()
        gui.notification(_.REMOVED_FROM_WATCHLIST)
    else:
        gui.notification(_.REMOVE_FROM_WATCHLIST_FAILED)

@plugin.route()
def watchlist(**kwargs):
    folder = plugin.Folder(title=_.WATCHLIST)

    data = api_list_watchlist()

    if data:
        processed = plugin_process_watchlist(data=data)

        if processed:
            folder.add_items(processed)

    return folder

@plugin.route()
def watchlist_listing(label, id, search=0, **kwargs):
    search = int(search)

    folder = plugin.Folder(title=label)

    data = api_watchlist_listing(id)

    if search == 0:
        id = None

    if data:
        processed = plugin_process_watchlist_listing(data=data, id=id)

        if processed:
            folder.add_items(processed)

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

            id = unicode(row['id'])

            if all or not prefs or not check_key(prefs, id) or prefs[id]['live'] == 1:
                channels.append({
                    'label': unicode(row['name']),
                    'channel': id,
                    'chno': unicode(row['channelno']),
                    'description': unicode(row['description']),
                    'image': unicode(row['icon']),
                    'path':  path,
                    'playable': playable,
                    'context': [
                        (_.START_BEGINNING, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=play_video, type='channel', channel=id, id=unicode(row['assetid']), from_beginning=1, _is_live=True)), ),
                    ],
                })

    return channels

def get_replay_channels(all=False):
    channels = []

    data = api_get_channels()

    prefs = load_prefs(profile_id=1)

    if data:
        for currow in data:
            row = data[currow]

            id = unicode(row['id'])

            if all or not prefs or not check_key(prefs, id) or int(prefs[id]['replay']) == 1:
                channels.append({
                    'label': unicode(row['name']),
                    'channel': id,
                    'chno': unicode(row['channelno']),
                    'description': unicode(row['description']),
                    'image': unicode(row['icon']),
                    'path': plugin.url_for(func_or_url=replaytv_by_day, image=unicode(row['icon']), description=unicode(row['description']), label=unicode(row['name']), station=id),
                    'playable': False,
                    'context': [],
                })

    return channels

def process_replaytv_list(character, start=0):
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

            if not check_key(data, unicode(row)):
                continue

            if int(currow['replay']) == 1:
                channels_ar.append(row)

    data = api_get_list_by_first(first=character, start=nowstamp, end=sevendaysstamp, channels=channels_ar)

    start = int(start)
    items = []
    count = 0
    item_count = 0

    if not data:
        return {'items': items, 'count': item_count, 'count2': count, 'total': 0}

    for currow in data:
        row = data[currow]

        if item_count == 51:
            break

        count += 1

        if count < start + 1:
            continue

        item_count += 1

        label = unicode(row['title'])
        idtitle = unicode(currow)
        icon = unicode(row['icon'])

        items.append(plugin.Item(
            label = label,
            info = {
                'sorttitle': label.upper(),
            },
            art = {
                'thumb': icon,
                'fanart': icon
            },
            path = plugin.url_for(func_or_url=replaytv_item, label=label, idtitle=idtitle, start=0),
        ))

    returnar = {'items': items, 'count': item_count, 'count2': count, 'total': len(data)}

    return returnar

def process_replaytv_search(search):
    now = datetime.datetime.now(pytz.timezone("Europe/Amsterdam"))
    sevendays = datetime.datetime.now(pytz.timezone("Europe/Amsterdam")) - datetime.timedelta(days=7)
    nowstamp = int((now - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())
    sevendaysstamp = int((sevendays - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())

    search = unicode(search)

    data = api_get_channels()

    prefs = load_prefs(profile_id=1)
    channels_ar = []

    if prefs:
        for row in prefs:
            currow = prefs[row]

            if not check_key(data, unicode(row)):
                continue

            if int(currow['replay']) == 1:
                channels_ar.append(row)

    data = api_get_list(start=nowstamp, end=sevendaysstamp, channels=channels_ar)

    items = []

    if not data:
        return {'items': items}

    for currow in data:
        row = data[currow]

        title = unicode(row['title'])
        icon = unicode(row['icon'])

        fuzz_set = fuzz.token_set_ratio(title, search)
        fuzz_partial = fuzz.partial_ratio(title, search)
        fuzz_sort = fuzz.token_sort_ratio(title, search)

        if (fuzz_set + fuzz_partial + fuzz_sort) > 160:
            label = title + ' (ReplayTV)'
            idtitle = unicode(currow)

            items.append(plugin.Item(
                label = label,
                info = {
                    'sorttitle': label.upper(),
                },
                art = {
                    'thumb': icon,
                    'fanart': icon
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

        if item_count == 51:
            break

        count += 1

        if count < start + 1:
            continue

        context = []
        item_count += 1
        channel = unicode(row['channel'])

        startT = datetime.datetime.fromtimestamp(int(row['start']))
        startT = convert_datetime_timezone(startT, "Europe/Amsterdam", "Europe/Amsterdam")
        endT = datetime.datetime.fromtimestamp(int(row['end']))
        endT = convert_datetime_timezone(endT, "Europe/Amsterdam", "Europe/Amsterdam")

        if endT < (datetime.datetime.now(pytz.timezone("Europe/Amsterdam")) - datetime.timedelta(days=7)):
            continue

        label = startT.strftime("%H:%M") + " - " + unicode(row['title'])

        description = unicode(row['description'])

        duration = int((endT - startT).total_seconds())

        program_image = unicode(row['icon'])
        program_image_large = unicode(row['icon'])
        program_id = unicode(row['program_id'])

        if CONST_WATCHLIST:
            context.append((_.ADD_TO_WATCHLIST, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=add_to_watchlist, id=program_id, type='item')), ))

        items.append(plugin.Item(
            label = label,
            info = {
                'plot': description,
                'duration': duration,
                'mediatype': 'video',
                'sorttitle': label.upper(),
            },
            art = {
                'thumb': program_image,
                'fanart': program_image_large
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

            if not check_key(data, unicode(row)):
                continue

            channels_ar2[unicode(row)] = data[unicode(row)]['name']

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

        if item_count == 51:
            break

        count += 1

        if count < start + 1:
            continue

        context = []
        item_count += 1

        channel = unicode(row['channel'])

        startT = datetime.datetime.fromtimestamp(int(row['start']))
        startT = convert_datetime_timezone(startT, "Europe/Amsterdam", "Europe/Amsterdam")
        endT = datetime.datetime.fromtimestamp(int(row['end']))
        endT = convert_datetime_timezone(endT, "Europe/Amsterdam", "Europe/Amsterdam")

        if xbmc.getLanguage(xbmc.ISO_639_1) == 'nl':
            itemlabel = '{weekday} {day} {month} {yearhourminute} '.format(weekday=date_to_nl_dag(startT), day=startT.strftime("%d"), month=date_to_nl_maand(startT), yearhourminute=startT.strftime("%Y %H:%M"))
        else:
            itemlabel = startT.strftime("%A %d %B %Y %H:%M ").capitalize()

        itemlabel += unicode(row['title'])

        try:
            itemlabel += " (" + unicode(channels_ar2[channel]) + ")"
        except:
            pass

        description = unicode(row['description'])
        duration = int((endT - startT).total_seconds())
        program_image = unicode(row['icon'])
        program_image_large = unicode(row['icon'])
        program_id = unicode(row['program_id'])

        if CONST_WATCHLIST:
            context.append((_.ADD_TO_WATCHLIST, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=add_to_watchlist, id=program_id, type='item')), ))

        items.append(plugin.Item(
            label = itemlabel,
            info = {
                'plot': description,
                'duration': duration,
                'mediatype': 'video',
                'sorttitle': itemlabel.upper(),
            },
            art = {
                'thumb': program_image,
                'fanart': program_image_large
            },
            path = plugin.url_for(func_or_url=play_video, type='program', channel=channel, id=program_id),
            playable = True,
            context = context
        ))

    returnar = {'items': items, 'count': item_count, 'count2': count, 'total': len(data)}

    return returnar

def process_vod_content(data, start=0, search=None, type=None, character=None, online=0):
    subscription_filter = plugin_vod_subscription_filter()

    start = int(start)
    type = unicode(type)
    type2 = data

    items = []

    if not online == 1:
        count = 0
    else:
        count = start

    item_count = 0

    if online == 1:
        if search:
            data = api_search(query=search)
        else:
            data = api_vod_download(type=data, start=start)
    else:
        data = api_get_vod_by_type(type=data, character=character, subscription_filter=subscription_filter)

    if not data:
        return {'items': items, 'count': item_count, 'count2': count, 'total': 0}

    for currow in data:
        if not online == 1:
            row = data[currow]
        else:
            row = currow

        if item_count == 51:
            break

        count += 1

        if not online == 1 and count < start + 1:
            continue

        id = unicode(row['id'])
        label = unicode(row['title'])

        if search and not online == 1:
            fuzz_set = fuzz.token_set_ratio(label,search)
            fuzz_partial = fuzz.partial_ratio(label,search)
            fuzz_sort = fuzz.token_sort_ratio(label,search)

            if (fuzz_set + fuzz_partial + fuzz_sort) > 160:
                properties = {"fuzz_set": fuzz.token_set_ratio(label,search), "fuzz_sort": fuzz.token_sort_ratio(label,search), "fuzz_partial": fuzz.partial_ratio(label,search), "fuzz_total": fuzz.token_set_ratio(label,search) + fuzz.partial_ratio(label,search) + fuzz.token_sort_ratio(label,search)}
                label = label + " (" + type + ")"
            else:
                continue

        context = []
        item_count += 1

        properties = []
        description = unicode(row['description'])
        duration = 0

        if row['duration'] and len(unicode(row['duration'])) > 0:
            duration = int(row['duration'])

        program_image = unicode(row['icon'])
        program_image_large = unicode(row['icon'])
        program_type = unicode(row['type'])

        if program_type == "show" or program_type == "Serie":
            path = plugin.url_for(func_or_url=vod_series, type=type2, label=label, id=id)
            info = {'plot': description, 'sorttitle': label.upper()}
            playable = False
        elif program_type == "Epg":
            path = plugin.url_for(func_or_url=play_video, type='program', channel=None, id=id)
            info = {'plot': description, 'duration': duration, 'mediatype': 'video', 'sorttitle': label.upper()}
            playable = True
        elif program_type == "movie" or program_type == "Vod":
            path = plugin.url_for(func_or_url=play_video, type='vod', channel=None, id=id)
            info = {'plot': description, 'duration': duration, 'mediatype': 'video', 'sorttitle': label.upper()}
            playable = True
        else:
            continue

        if CONST_WATCHLIST:
            context.append((_.ADD_TO_WATCHLIST, 'RunPlugin({context_url})'.format(context_url=plugin.url_for(func_or_url=add_to_watchlist, id=id, type='group')), ))

        items.append(plugin.Item(
            label = label,
            properties = properties,
            info = info,
            art = {
                'thumb': program_image,
                'fanart': program_image_large
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

def _sort_replay_items(element):
    return element.get_li().getProperty('fuzz_total')

def check_first():
    profile_settings = load_profile(profile_id=1)

    if not check_key(profile_settings, 'setup_complete'):
        if gui.yes_no(message=_.DISABLE_EROTICA) == False:
            settings.setBool(key='disableErotica', value=False)
        else:
            settings.setBool(key='disableErotica', value=True)

        if gui.yes_no(message=_.MINIMAL_CHANNELS) == False:
            settings.setBool(key='minimalChannels', value=False)
        else:
            settings.setBool(key='minimalChannels', value=True)

        if gui.yes_no(message=_.DISABLE_REGIONAL) == False:
            settings.setBool(key='disableRegionalChannels', value=False)
        else:
            settings.setBool(key='disableRegionalChannels', value=True)

        if PROVIDER_NAME == 'kpn':
            if gui.yes_no(message=_.HOME_CONNECTION) == True:
                settings.setBool(key='homeConnection', value=True)
            else:
                settings.setBool(key='homeConnection', value=False)

        profile_settings['setup_complete'] = 1
        save_profile(profile_id=1, profile=profile_settings)