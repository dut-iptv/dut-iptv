import base64, glob, hashlib, io, json, os, re, time, xbmc, xbmcaddon

from collections import OrderedDict
from resources.lib.base.l1.constants import ADDON_ID, ADDON_PATH, ADDON_PROFILE
from resources.lib.base.l2.log import log
from resources.lib.base.l3.util import clear_cache, check_key, is_file_older_than_x_days, load_channels, load_file, load_order, load_prefs, load_profile, load_radio_order, load_radio_prefs, write_file

try:
    unicode
except NameError:
    unicode = str

def clear_cache_connector():
    clear_cache()

    addonlist = ['canaldigitaal', 'kpn', 'nlziet', 'tmobile', 'ziggo']

    for addon in addonlist:
        try:
            for file in glob.glob(ADDON_PROFILE + "cache" + os.sep + addon + os.sep + "*.xml"):
                if is_file_older_than_x_days(file=file, days=1):
                    os.remove(file)
        except:
            pass

def create_epg():
    order = load_order(profile_id=1)
    prefs = load_prefs(profile_id=1)

    new_xml_start = '<?xml version="1.0" encoding="utf-8" ?><tv generator-info-name="{addonid}">'.format(addonid=ADDON_ID)
    new_xml_end = '</tv>'
    new_xml_channels = ''
    new_xml_epg = ''

    for currow in order:
        try:
            ch_no = unicode(order[currow])
            row = prefs[unicode(currow)]

            if not check_key(row, 'live') or not check_key(row, 'live_channelid') or not check_key(row, 'live_addonid') or not check_key(row, 'channelname') or not int(row['live']) == 1:
                continue

            live_id = unicode(row['live_channelid'])

            if not check_key(row, 'replay'):
                replay = 0
            else:
                replay = int(row['replay'])

            if not check_key(row, 'replay_channelid'):
                replay_id = ''
            else:
                replay_id = unicode(row['replay_channelid'])

            if not check_key(row, 'replay_addonid'):
                replay_addonid = ''
            else:
                replay_addonid = unicode(row['replay_addonid'])

            if replay == 1 and len(replay_id) > 0 and len(replay_addonid) > 0:
                directory = "cache" + os.sep + replay_addonid.replace('plugin.video.', '') + os.sep
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
                    if replay == 1 and len(replay_id) > 0 and len(replay_addonid) > 0:
                        new_xml_channels += '<channel id="{channelid}"><display-name>{channelname}</display-name><icon src="{channelicon}"></icon><desc></desc></channel>'.format(channelid=unicode(row['replay_channelid']), channelname=unicode(row['channelname']), channelicon=unicode(row['channelicon']))
                    else:
                        new_xml_channels += '<channel id="{channelid}"><display-name>{channelname}</display-name><icon src="{channelicon}"></icon><desc></desc></channel>'.format(channelid=unicode(row['live_channelid']), channelname=unicode(row['channelname']), channelicon=unicode(row['channelicon']))
                except:
                    pass
        except:
            pass

    write_file(file='epg.xml', data=new_xml_start + new_xml_channels + new_xml_epg + new_xml_end, isJSON=False)

def create_playlist():
    playlist = u'#EXTM3U\n'

    order = load_order(profile_id=1)
    prefs = load_prefs(profile_id=1)

    for currow in order:
        try:
            ch_no = unicode(order[currow])
            row = prefs[unicode(currow)]

            if not check_key(row, 'live') or not check_key(row, 'live_channelid') or not check_key(row, 'live_channelassetid') or not check_key(row, 'live_addonid') or not check_key(row, 'channelname') or not int(row['live']) == 1:
                continue

            live_id = unicode(row['live_channelid'])

            if len(live_id) > 0:
                if not check_key(row, 'channelicon'):
                    image = ''
                else:
                    image = row['channelicon']

                path = unicode('plugin://{addonid}/?_=play_video&channel={channel}&id={asset}&type=channel&pvr=1&_l=.pvr'.format(addonid=row['live_addonid'], channel=row['live_channelid'], asset=row['live_channelassetid']))

                if not check_key(row, 'replay'):
                    replay = 0
                else:
                    replay = int(row['replay'])

                if not check_key(row, 'replay_channelid'):
                    replay_id = ''
                else:
                    replay_id = unicode(row['replay_channelid'])

                try:
                    if replay == 1 and len(replay_id) > 0:
                        catchup = unicode('plugin://' + row['replay_addonid'] + '/?_=play_video&type=program&channel=' + row['replay_channelid'] + '&id={catchup-id}')
                        playlist += u'#EXTINF:0 tvg-id="{id}" tvg-chno="{channel}" tvg-name="{name}" tvg-logo="{logo}" catchup="default" catchup-source="{catchup}" catchup-days="7" group-title="TV" radio="false",{name}\n{path}\n'.format(id=unicode(row['replay_channelid']), channel=ch_no, name=unicode(row['channelname']), logo=image, catchup=catchup, path=path)
                    else:
                        playlist += u'#EXTINF:0 tvg-id="{id}" tvg-chno="{channel}" tvg-name="{name}" tvg-logo="{logo}" group-title="TV" radio="false",{name}\n{path}\n'.format(id=unicode(row['live_channelid']), channel=ch_no, name=unicode(row['channelname']), logo=image, path=path)
                except:
                    pass
        except:
            pass

    profile_settings = load_profile(profile_id=1)

    if check_key(profile_settings, 'radio') and int(profile_settings['radio']) == 1:
        order = load_radio_order(profile_id=1)
        prefs = load_radio_prefs(profile_id=1)
        radio = load_channels(type='radio')

        for currow in order:
            try:
                ch_no = unicode(order[currow])
                row = prefs[unicode(currow)]

                if not check_key(row, 'radio') or int(row['radio']) == 0:
                    continue

                id = unicode(currow)

                if len(id) > 0:
                    if not radio or not check_key(radio, id) or not check_key(radio[id], 'name') or not check_key(radio[id], 'url'):
                        continue

                    if check_key(radio[id], 'mod_name') and len(unicode(radio[id]['mod_name'])) > 0:
                        label = unicode(radio[id]['mod_name'])
                    else:
                        label = unicode(radio[id]['name'])

                    path = unicode(radio[id]['url'])

                    if check_key(radio[id], 'icon') and len(unicode(radio[id]['icon'])) > 0:
                        image = unicode(radio[id]['icon'])
                    else:
                        image = ''

                    playlist += u'#EXTINF:0 tvg-id="{id}" tvg-chno="{channel}" tvg-name="{name}" tvg-logo="{logo}" group-title="Radio" radio="true",{name}\n{path}\n'.format(id=id, channel=ch_no, name=label, logo=image, path=path)
            except:
                pass

    write_file(file="playlist.m3u8", data=playlist, isJSON=False)