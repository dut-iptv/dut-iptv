import _strptime
import datetime, re, time, xbmc

from collections import OrderedDict
from resources.lib.base.l1.constants import ADDON_ID, DEFAULT_USER_AGENT
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, encode_obj, load_file, load_profile, write_file
from resources.lib.base.l4 import gui
from resources.lib.base.l6 import inputstream
from resources.lib.constants import CONST_URLS, CONST_IMAGES, CONST_WATCHLIST_CAPABILITY
from urllib.parse import urlencode

#Included from base.l7.plugin
#plugin_get_device_id

#Included from base.l8.menu
#plugin_ask_for_creds
#plugin_check_devices
#plugin_check_first
#plugin_login_error
#plugin_post_login
#plugin_process_info
#plugin_process_playdata
#plugin_process_vod
#plugin_process_vod_season
#plugin_process_vod_seasons
#plugin_process_watchlist
#plugin_process_watchlist_listing
#plugin_renew_token
#plugin_vod_subscription_filter

def convert_to_seconds(s):
    UNITS = {'s':'seconds', 'm':'minutes', 'u':'hours', 'd':'days', 'w':'weeks'}

    return int(datetime.timedelta(**{
        UNITS.get(m.group('unit').lower(), 'seconds'): int(m.group('val'))
        for m in re.finditer(r'(?P<val>\d+)(?P<unit>[smudw]?)', s, flags=re.I)
    }).total_seconds())

def plugin_ask_for_creds(creds):
    username = str(gui.input(message=_.ASK_USERNAME, default=creds['username'])).strip()

    if not len(str(username)) > 0:
        gui.ok(message=_.EMPTY_USER, heading=_.LOGIN_ERROR_TITLE)
        return {'result': False, 'username': '', 'password': ''}

    password = str(gui.input(message=_.ASK_PASSWORD, hide_input=True)).strip()

    if not len(str(password)) > 0:
        gui.ok(message=_.EMPTY_PASS, heading=_.LOGIN_ERROR_TITLE)
        return {'result': False, 'username': '', 'password': ''}

    return {'result': True, 'username': username, 'password': password}

def plugin_check_devices():
    pass

def plugin_check_first():
    pass

def plugin_get_device_id():
    return 'NOTNEEDED'

def plugin_login_error(login_result):
    try:
        if (login_result['code'] == 403 and 'Teveel verschillende apparaten' in login_result['data']):
            gui.ok(message=_.TOO_MANY_DEVICES, heading=_.LOGIN_ERROR_TITLE)
        else:
            gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)
    except:
        gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)

def plugin_post_login():
    pass

def plugin_process_info(playdata):
    info = {
        'label1': '',
        'label2': '',
        'description': '',
        'image': '',
        'image_large': '',
        'duration': 0,
        'credits': [],
        'cast': [],
        'director': [],
        'writer': [],
        'genres': [],
        'year': '',
    }

    if check_key(playdata['info'], 'Start') and check_key(playdata['info'], 'End'):
        startT = datetime.datetime.fromtimestamp(time.mktime(time.strptime(playdata['info']['Start'], "%Y-%m-%dT%H:%M:%S")))
        startT = convert_datetime_timezone(startT, "UTC", "UTC")
        endT = datetime.datetime.fromtimestamp(time.mktime(time.strptime(playdata['info']['End'], "%Y-%m-%dT%H:%M:%S")))
        endT = convert_datetime_timezone(endT, "UTC", "UTC")

        write_file(file='stream_start', data=int(time.mktime(time.strptime(playdata['info']['Start'], "%Y-%m-%dT%H:%M:%S"))), isJSON=False)
        write_file(file='stream_end', data=int(time.mktime(time.strptime(playdata['info']['End'], "%Y-%m-%dT%H:%M:%S"))), isJSON=False)

        if check_key(playdata['info'], 'DurationInSeconds'):
            info['duration'] = playdata['info']['DurationInSeconds']
        elif check_key(playdata['info'], 'Duur'):
            info['duration'] = playdata['info']['Duur']
        else:
            info['duration'] = int((endT - startT).total_seconds())

        if xbmc.getLanguage(xbmc.ISO_639_1) == 'nl':
            info['label1'] = '{weekday} {day} {month} {yearhourminute} '.format(weekday=date_to_nl_dag(startT), day=startT.strftime("%d"), month=date_to_nl_maand(startT), yearhourminute=startT.strftime("%Y %H:%M"))
        else:
            info['label1'] = startT.strftime("%A %d %B %Y %H:%M ").capitalize()

    if check_key(playdata['info'], 'Duur'):
        info['duration'] = playdata['info']['Duur']

    if check_key(playdata['info'], 'Title'):
        if len(str(info['label1'])) > 0:
            info['label1'] += " - "

        if len(str(info['label2'])) > 0:
            info['label2'] += " - "

        info['label1'] += playdata['info']['Title']
        info['label2'] += playdata['info']['Title']
    elif check_key(playdata['info'], 'Serie') and check_key(playdata['info']['Serie'], 'Titel') and len(playdata['info']['Serie']['Titel']):
        if len(str(info['label1'])) > 0:
            info['label1'] += " - "

        if len(str(info['label2'])) > 0:
            info['label2'] += " - "

        info['label1'] += playdata['info']['Serie']['Titel']
        info['label2'] += playdata['info']['Serie']['Titel']

        if check_key(playdata['info'], 'Titel') and len(playdata['info']['Titel']) > 0 and playdata['info']['Titel'] != playdata['info']['Serie']['Titel']:
            if len(str(info['label1'])) > 0:
                info['label1'] += ": "

            if len(str(info['label2'])) > 0:
                info['label2'] += ": "

            info['label1'] += playdata['info']['Titel']
            info['label2'] += playdata['info']['Titel']

    if check_key(playdata['info'], 'LongDescription'):
        info['description'] = playdata['info']['LongDescription']
    elif check_key(playdata['info'], 'Omschrijving'):
        info['description'] = playdata['info']['Omschrijving']

    if check_key(playdata['info'], 'CoverUrl'):
        info['image'] = playdata['info']['CoverUrl']
        info['image_large'] = playdata['info']['CoverUrl']
    elif check_key(playdata['info'], 'AfbeeldingUrl'):
        info['image'] = playdata['info']['AfbeeldingUrl']
        info['image_large'] = playdata['info']['AfbeeldingUrl']

    if check_key(playdata['info'], 'ChannelTitle'):
        if len(str(info['label2'])) > 0:
            info['label2'] += " - "

        info['label2'] += playdata['info']['ChannelTitle']
    elif check_key(playdata['info'], 'Zender'):
        if len(str(info['label2'])) > 0:
            info['label2'] += " - "

        info['label2'] += playdata['info']['Zender']

    return info

def plugin_process_playdata(playdata):
    CDMHEADERS = {}

    if check_key(playdata, 'license') and check_key(playdata['license'], 'drmConfig') and check_key(playdata['license']['drmConfig'], 'widevine'):
        if 'nlznl.solocoo.tv' in playdata['license']['drmConfig']['widevine']['drmServerUrl']:
            if xbmc.Monitor().waitForAbort(1):
                return False

        if check_key(playdata['license']['drmConfig']['widevine'], 'customHeaders'):
            for row in playdata['license']['drmConfig']['widevine']['customHeaders']:
                CDMHEADERS[row] = playdata['license']['drmConfig']['widevine']['customHeaders'][row]

        item_inputstream = inputstream.Widevine(
            license_key = playdata['license']['drmConfig']['widevine']['drmServerUrl'],
        )
    else:
        item_inputstream = inputstream.MPD()

    return item_inputstream, CDMHEADERS

def plugin_process_vod(data, start=0):
    items = {}

    for row in data:
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

        if start > 0:
            start -= 1
            continue

        id = row['id']
        items[id] = {}

        episodeTitle = row['title']

        if check_key(row, 'subtitle') and len(row['subtitle']) > 0:
            if episodeTitle in row['subtitle']:
                episodeTitle = row['subtitle']
            else:
                episodeTitle += " - {subtitle}".format(subtitle=row['subtitle'])           
            
        label = ''
        desc = ''
        starttime = ''
        duration = 0
        image = ''

        if check_key(row, 'description'):
            desc = row['description']

        if check_key(row, 'formattedDuration'):
            duration = convert_to_seconds(row['formattedDuration'])

        if check_key(row, 'image') and check_key(row['image'], 'portraitUrl'):
            image = row['image']['portraitUrl']
        elif check_key(row, 'image') and check_key(row['image'], 'landscapeUrl'):
            image = row['image']['landscapeUrl']

        if not 'http' in image and len(str(image)) > 0:
            image_split = image.rsplit('/', 1)

            if len(image_split) == 2:
                image = '{image_url}/legacy/thumbnails/{image}'.format(image_url=CONST_URLS['image'], image=image.rsplit('/', 1)[1])
            else:
                image = '{image_url}/{image}'.format(image_url=CONST_URLS['image'], image=image)

        if check_key(row, 'formattedDate') and check_key(row, 'formattedTime'):
            starttime = "{date} {time}".format(date=row['formattedDate'], time=row['formattedTime'])
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

        items[id]['id'] = id
        items[id]['title'] = label
        items[id]['description'] = desc
        items[id]['duration'] = duration
        items[id]['type'] = type
        items[id]['icon'] = image
        items[id]['start'] = starttime

    return items

def plugin_process_vod_season(series, id, data):
    season = []

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

        if check_key(row, 'image'):
            if check_key(row['image'], 'portraitUrl'):
                image = row['image']['portraitUrl']
            elif check_key(row['image'], 'landscapeUrl'):
                image = row['image']['landscapeUrl']

            if not 'http' in image:
                image_split = image.rsplit('/', 1)

                if len(image_split) == 2:
                    image = '{image_url}/legacy/thumbnails/{image}'.format(image_url=CONST_URLS['image'], image=image.rsplit('/', 1)[1])
                else:
                    image = '{image_url}/{image}'.format(image_url=CONST_URLS['image'], image=image)

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

    season[:] = sorted(season, key=sort_episodes)

    return season

def plugin_process_vod_seasons(id, data):
    seasons = []

    if not data:
        return None

    season_count = 0

    if check_key(data, 'seasons'):
        for row in data['seasons']:
            season_count += 1
            image = ''

            if check_key(data, 'image'):
                if check_key(data['image'], 'portraitUrl'):
                    image = data['image']['portraitUrl']
                elif check_key(data['image'], 'landscapeUrl'):
                    image = data['image']['landscapeUrl']

            seasons.append({'id': row['id'], 'seriesNumber': row['title'], 'description': data['description'], 'image': image})

    seasons[:] = sorted(seasons, key=sort_season)

    return {'program': data, 'type': 'seasons', 'seasons': seasons}

def plugin_process_watchlist(data, type='watchlist'):
    items = {}
    items2 = plugin_process_vod(data, 0)

    for id in items2:
        currow = items2[id]

        context = []

        params = []
        params.append(('_', 'remove_from_watchlist'))
        params.append(('type', type))

        progress = 0
        remove_txt = CONST_WATCHLIST_CAPABILITY[type]['removelist']

        params.append(('id', id))

        if CONST_WATCHLIST_CAPABILITY[type]['remove'] == 1:
                context.append((remove_txt, 'RunPlugin({context_url})'.format(context_url='plugin://{0}/?{1}'.format(ADDON_ID, urlencode(encode_obj(params)))), ))

        if currow['type'] == 'Serie' and not type == 'continuewatch':
            params = []
            params.append(('_', 'vod_series'))
            params.append(('type', 'series'))
            params.append(('label', currow['title']))
            params.append(('id', id))

            path = 'plugin://{0}/?{1}'.format(ADDON_ID, urlencode(encode_obj(params)))
            playable = False
            mediatype = ''
        else:
            params = []
            params.append(('_', 'play_video'))
            params.append(('type', 'movie'))
            params.append(('channel', None))
            params.append(('id', id))
            params.append(('title', None))

            path = 'plugin://{0}/?{1}'.format(ADDON_ID, urlencode(encode_obj(params)))
            playable = True
            mediatype = 'video'

        items[str(id)] = {
            'label1': currow['title'],
            'description': currow['description'],
            'duration': currow['duration'],
            'mediatype': mediatype,
            'image': currow['icon'],
            'image_large': currow['icon'],
            'path': path,
            'playable': playable,
            'progress': progress,
            'context': context,
            'type': currow['type']
        }

    return items

def plugin_process_watchlist_listing(data, id=None, type='watchlist'):
    items = []

    return items

def plugin_renew_token(data):
    return None

def plugin_vod_subscription_filter():
    return None
    
def sort_episodes(element):
    try:
        return element['episodeNumber']
    except:
        return 0

def sort_season(element):
    if str(element['seriesNumber']).isnumeric():
        return int(element['seriesNumber'])
    else:
        matches = re.findall(r"Seizoen (\d+)", element['seriesNumber'])

        for match in matches:
            return int(match)

        return 0