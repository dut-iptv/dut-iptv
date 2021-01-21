import base64, glob, hashlib, io, json, os, re, time, xbmc, xbmcaddon

from collections import OrderedDict
from resources.lib.base.l1.constants import ADDON_ID, ADDON_PATH, ADDON_PROFILE
from resources.lib.base.l2.log import log

try:
    unicode
except NameError:
    unicode = str

def check_addon(addon):
    if xbmc.getCondVisibility('System.HasAddon(%s)' % addon) == 1:
        try:
            VIDEO_ADDON = xbmcaddon.Addon(id=addon)

            return True
        except:
            return False

    return False

def check_key(object, key):
    if key in object and object[key] and (len(unicode(object[key])) > 0 or int(object[key]) == 0):
        return True
    else:
        return False

def check_loggedin(addon):
    VIDEO_ADDON_PROFILE = ADDON_PROFILE.replace(ADDON_ID, addon)

    profile = load_file(VIDEO_ADDON_PROFILE + 'profile.json', ext=True, isJSON=True)

    if not profile:
        return False
    else:
        try:
            if len(unicode(profile['pswd'])) > 0 and int(profile['last_login_success']) == 1:
                return True
            else:
                return False
        except:
            return False

def clear_cache():
    if not os.path.isdir(ADDON_PROFILE + "cache"):
        os.makedirs(ADDON_PROFILE + "cache")

    for file in glob.glob(ADDON_PROFILE + "cache" + os.sep + "*.json"):
        if is_file_older_than_x_days(file=file, days=1):
            os.remove(file)

    addonlist = ['canaldigitaal', 'kpn', 'nlziet', 'tmobile', 'ziggo']

    for addon in addonlist:
        try:
            for file in glob.glob(ADDON_PROFILE + "cache" + os.sep + addon + os.sep + "*.xml"):
                if is_file_older_than_x_days(file=file, days=1):
                    os.remove(file)
        except:
            pass

    if not os.path.isdir(ADDON_PROFILE + "tmp"):
        os.makedirs(ADDON_PROFILE + "tmp")

    for file in glob.glob(ADDON_PROFILE + "tmp" + os.sep + "*.zip"):
        if is_file_older_than_x_days(file=file, days=1):
            os.remove(file)

def create_epg():
    order = load_order(profile_id=1)
    prefs = load_prefs(profile_id=1)

    new_xml_start = '<?xml version="1.0" encoding="utf-8" ?><tv generator-info-name="{addonid}">'.format(addonid=ADDON_ID)
    new_xml_end = '</tv>'
    new_xml_channels = ''
    new_xml_epg = ''

    for currow in order:
        ch_no = unicode(order[currow])
        row = prefs[unicode(currow)]

        if int(row['live']) == 0:
            continue

        live_id = unicode(row['live_channelid'])
        replay_id = unicode(row['replay_channelid'])

        if int(row['replay']) == 1 and len(replay_id) > 0:
            directory = "cache" + os.sep + unicode(row['replay_addonid'].replace('plugin.video.', '')) + os.sep
            encodedBytes = base64.b32encode(replay_id.encode("utf-8"))
            replay_id = unicode(encodedBytes, "utf-8")

            data = load_file(directory + replay_id + '.xml', ext=False, isJSON=False)
        else:
            directory = "cache" + os.sep + unicode(row['live_addonid'].replace('plugin.video.', '')) + os.sep
            encodedBytes = base64.b32encode(live_id.encode("utf-8"))
            live_id = unicode(encodedBytes, "utf-8")

            data = load_file(directory + live_id + '.xml', ext=False, isJSON=False)

        if data:
            new_xml_epg += data

            try:
                if int(row['replay']) == 1 and len(replay_id) > 0:
                    new_xml_channels += '<channel id="{channelid}"><display-name>{channelname}</display-name><icon-name src="{channelicon}"></icon-name><desc></desc></channel>'.format(channelid=unicode(row['replay_channelid']), channelname=unicode(row['channelname']), channelicon=unicode(row['channelicon']))
                else:
                    new_xml_channels += '<channel id="{channelid}"><display-name>{channelname}</display-name><icon-name src="{channelicon}"></icon-name><desc></desc></channel>'.format(channelid=unicode(row['live_channelid']), channelname=unicode(row['channelname']), channelicon=unicode(row['channelicon']))
            except:
                pass

    write_file(file='epg.xml', data=new_xml_start + new_xml_channels + new_xml_epg + new_xml_end, isJSON=False)

def create_playlist():
    playlist = u'#EXTM3U\n'

    order = load_order(profile_id=1)
    prefs = load_prefs(profile_id=1)

    for currow in order:
        ch_no = unicode(order[currow])
        row = prefs[unicode(currow)]

        if int(row['live']) == 0:
            continue

        live_id = unicode(row['live_channelid'])

        if len(live_id) > 0:
            image = row['channelicon']

            path = unicode('plugin://{addonid}/?_=play_video&channel={channel}&id={asset}&type=channel&pvr=1&_l=.pvr'.format(addonid=row['live_addonid'], channel=row['live_channelid'], asset=row['live_channelassetid']))

            replay_id = unicode(row['replay_channelid'])

            try:
                if int(row['replay']) == 1 and len(replay_id) > 0:
                    catchup = unicode('plugin://' + row['replay_addonid'] + '/?_=play_video&type=program&channel=' + row['replay_channelid'] + '&id={catchup-id}')
                    playlist += u'#EXTINF:0 tvg-id="{id}" tvg-chno="{channel}" tvg-name="{name}" tvg-logo="{logo}" catchup="default" catchup-source="{catchup}" catchup-days="7" group-title="TV" radio="false",{name}\n{path}\n'.format(id=unicode(row['replay_channelid']), channel=ch_no, name=unicode(row['channelname']), logo=image, catchup=catchup, path=path)
                else:
                    playlist += u'#EXTINF:0 tvg-id="{id}" tvg-chno="{channel}" tvg-name="{name}" tvg-logo="{logo}" group-title="TV" radio="false",{name}\n{path}\n'.format(id=unicode(row['live_channelid']), channel=ch_no, name=unicode(row['channelname']), logo=image, path=path)
            except:
                pass

    profile_settings = load_profile(profile_id=1)

    if int(profile_settings['radio']) == 1:
        order = load_radio_order(profile_id=1)
        prefs = load_radio_prefs(profile_id=1)
        radio = load_channels(type='radio')

        for currow in order:
            ch_no = unicode(order[currow])
            row = prefs[unicode(currow)]

            if int(row['radio']) == 0:
                continue

            id = unicode(currow)

            if len(id) > 0:
                if not radio or not check_key(radio, id):
                    continue

                if len(unicode(radio[id]['mod_name'])) > 0:
                    label = unicode(radio[id]['mod_name'])
                else:
                    label = unicode(radio[id]['name'])

                path = unicode(radio[id]['url'])
                image = unicode(radio[id]['icon'])

                playlist += u'#EXTINF:0 tvg-id="{id}" tvg-chno="{channel}" tvg-name="{name}" tvg-logo="{logo}" group-title="Radio" radio="true",{name}\n{path}\n'.format(id=id, channel=ch_no, name=label, logo=image, path=path)

    write_file(file="playlist.m3u8", data=playlist, isJSON=False)

def fixBadZipfile(zipFile):
    f = open(zipFile, 'r+b')
    data = f.read()
    
    try:
        pos = data.find(b'\x50\x4b\x05\x06') # End of central directory signature
    except:
        pos = data.find('\x50\x4b\x05\x06')
    
    if (pos > 0):
        f.seek(pos + 22)   # size of 'ZIP end of central directory record'
        f.truncate()
        f.close()

def is_file_older_than_x_days(file, days=1):
    if not os.path.isfile(file):
        return True

    file_time = os.path.getmtime(file)
    totaltime = int(time.time()) - int(file_time)
    totalhours = float(totaltime) / float(3600)

    if totalhours > 24*days:
        return True
    else:
        return False

def is_file_older_than_x_minutes(file, minutes=1):
    if not os.path.isfile(file):
        return True

    file_time = os.path.getmtime(file)
    totaltime = int(time.time()) - int(file_time)
    totalminutes = float(totaltime) / float(60)

    if totalminutes > minutes:
        return True
    else:
        return False

def load_channels(type):
    if type == 'ziggo':
        VIDEO_ADDON_PROFILE = ADDON_PROFILE.replace(ADDON_ID, 'plugin.video.ziggo')
        profile = load_file(VIDEO_ADDON_PROFILE + 'profile.json', ext=True, isJSON=True)

        try:
            if int(profile['v3']) == 1:
                return load_file(file='cache' + os.sep + type[0] + '.channels.v3.json', ext=False, isJSON=True)
        except:
            pass

    return load_file(file='cache' + os.sep + type[0] + '.channels.json', ext=False, isJSON=True)

def load_file(file, ext=False, isJSON=False):
    if ext:
        full_path = file
    else:
        full_path = ADDON_PROFILE + file

    if not os.path.isfile(full_path):
        file = re.sub(r'[^a-z0-9.]+', '_', file).lower()

        if ext:
            full_path = file
        else:
            full_path = ADDON_PROFILE + file

        if not os.path.isfile(full_path):
            return None

    with io.open(full_path, 'r', encoding='utf-8') as f:
        try:
            if isJSON == True:
                return json.load(f, object_pairs_hook=OrderedDict)
            else:
                return f.read()
        except:
            return None

def load_prefs(profile_id=1):
    prefs = load_file('prefs.json', ext=False, isJSON=True)

    if not prefs:
        return OrderedDict()
    else:
        return prefs

def load_profile(profile_id=1):
    profile = load_file('profile.json', ext=False, isJSON=True)

    if not profile:
        return OrderedDict()
    else:
        return profile

def load_order(profile_id=1):
    order = load_file('order.json', ext=False, isJSON=True)

    if not order:
        return OrderedDict()
    else:
        return order

def load_radio_prefs(profile_id=1):
    prefs = load_file('radio_prefs.json', ext=False, isJSON=True)

    if not prefs:
        return OrderedDict()
    else:
        return prefs

def load_radio_order(profile_id=1):
    order = load_file('radio_order.json', ext=False, isJSON=True)

    if not order:
        return OrderedDict()
    else:
        return order

def md5sum(filepath):
    if not os.path.isfile(filepath):
        return None

    return hashlib.md5(open(filepath,'rb').read()).hexdigest()

def save_prefs(profile_id=1, prefs=None):
    write_file('prefs.json', data=prefs, ext=False, isJSON=True)

def save_profile(profile_id=1, profile=None):
    write_file('profile.json', data=profile, ext=False, isJSON=True)

def save_order(profile_id=1, order=None):
    write_file('order.json', data=order, ext=False, isJSON=True)

def save_radio_prefs(profile_id=1, prefs=None):
    write_file('radio_prefs.json', data=prefs, ext=False, isJSON=True)

def save_radio_order(profile_id=1, order=None):
    write_file('radio_order.json', data=order, ext=False, isJSON=True)

def write_file(file, data, ext=False, isJSON=False):
    if ext:
        full_path = file
    else:
        full_path = ADDON_PROFILE + file

    directory = os.path.dirname(full_path)

    if not os.path.exists(directory):
        os.makedirs(directory)

    with io.open(full_path, 'w', encoding="utf-8") as f:
        if isJSON == True:
            f.write(unicode(json.dumps(data, ensure_ascii=False)))
        else:
            f.write(unicode(data))