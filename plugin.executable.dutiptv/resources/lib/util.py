import base64, glob, hashlib, io, json, os, re, time, xbmc, xbmcaddon

from collections import OrderedDict
from resources.lib.base.l1.constants import ADDON_ID, ADDON_PATH, ADDON_PROFILE
from resources.lib.base.l2.log import log
from resources.lib.base.l3.util import clear_cache, check_key, is_file_older_than_x_days, load_channels, load_file, load_order, load_prefs, load_profile, load_radio_order, load_radio_prefs, write_file

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
            ch_no = str(order[currow])
            row = prefs[str(currow)]

            if not check_key(row, 'live') or not check_key(row, 'live_channelid') or not check_key(row, 'live_addonid') or not check_key(row, 'channelname') or not int(row['live']) == 1:
                continue

            live_id = str(row['live_channelid'])

            if not check_key(row, 'replay'):
                replay = 0
            else:
                replay = int(row['replay'])

            if not check_key(row, 'replay_channelid'):
                replay_id = ''
            else:
                replay_id = str(row['replay_channelid'])

            if not check_key(row, 'replay_addonid'):
                replay_addonid = ''
            else:
                replay_addonid = str(row['replay_addonid'])

            if replay == 1 and len(replay_id) > 0 and len(replay_addonid) > 0:
                directory = "cache" + os.sep + replay_addonid.replace('plugin.video.', '') + os.sep
                encodedBytes = base64.b32encode(replay_id.encode("utf-8"))
                replay_id = str(encodedBytes, "utf-8")

                data = load_file(directory + replay_id + '.xml', ext=False, isJSON=False)
            else:
                directory = "cache" + os.sep + str(row['live_addonid'].replace('plugin.video.', '')) + os.sep
                encodedBytes = base64.b32encode(live_id.encode("utf-8"))
                live_id = str(encodedBytes, "utf-8")

                data = load_file(directory + live_id + '.xml', ext=False, isJSON=False)

            if data:
                new_xml_epg += data

                try:
                    if replay == 1 and len(replay_id) > 0 and len(replay_addonid) > 0:
                        new_xml_channels += '<channel id="{channelid}"><display-name>{channelname}</display-name><icon src="{channelicon}"></icon><desc></desc></channel>'.format(channelid=str(row['replay_channelid']), channelname=str(row['channelname']), channelicon=str(row['channelicon']))
                    else:
                        new_xml_channels += '<channel id="{channelid}"><display-name>{channelname}</display-name><icon src="{channelicon}"></icon><desc></desc></channel>'.format(channelid=str(row['live_channelid']), channelname=str(row['channelname']), channelicon=str(row['channelicon']))
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
            ch_no = str(order[currow])
            row = prefs[str(currow)]

            if not check_key(row, 'live') or not check_key(row, 'live_channelid') or not check_key(row, 'live_channelassetid') or not check_key(row, 'live_addonid') or not check_key(row, 'channelname') or not int(row['live']) == 1:
                continue

            live_id = str(row['live_channelid'])

            if len(live_id) > 0:
                if not check_key(row, 'channelicon'):
                    image = ''
                else:
                    image = row['channelicon']
                    
                if not check_key(row, 'group') or len(str(row['group'])) == 0:
                    group = 'TV'
                else:
                    group = row['group']

                path = str('plugin://{addonid}/?_=play_video&channel={channel}&id={asset}&type=channel&pvr=1&_l=.pvr'.format(addonid=row['live_addonid'], channel=row['live_channelid'], asset=row['live_channelassetid']))

                if not check_key(row, 'replay'):
                    replay = 0
                else:
                    replay = int(row['replay'])

                if not check_key(row, 'replay_channelid'):
                    replay_id = ''
                else:
                    replay_id = str(row['replay_channelid'])

                try:
                    if replay == 1 and len(replay_id) > 0:
                        catchup = str('plugin://' + row['replay_addonid'] + '/?_=play_video&type=program&channel=' + row['replay_channelid'] + '&id={catchup-id}')
                        playlist += u'#EXTINF:0 tvg-id="{id}" tvg-chno="{channel}" tvg-name="{name}" tvg-logo="{logo}" catchup="default" catchup-source="{catchup}" catchup-days="7" group-title="{group}" radio="false",{name}\n{path}\n'.format(id=str(row['replay_channelid']), channel=ch_no, name=str(row['channelname']), logo=image, catchup=catchup, group=group, path=path)
                    else:
                        playlist += u'#EXTINF:0 tvg-id="{id}" tvg-chno="{channel}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}" radio="false",{name}\n{path}\n'.format(id=str(row['live_channelid']), channel=ch_no, name=str(row['channelname']), logo=image, group=group, path=path)
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
                ch_no = str(order[currow])
                row = prefs[str(currow)]

                if not check_key(row, 'radio') or int(row['radio']) == 0:
                    continue

                id = str(currow)

                if len(id) > 0:
                    if not radio or not check_key(radio, id) or not check_key(radio[id], 'name') or not check_key(radio[id], 'url'):
                        continue

                    if check_key(radio[id], 'mod_name') and len(str(radio[id]['mod_name'])) > 0:
                        label = radio[id]['mod_name']
                    else:
                        label = radio[id]['name']

                    path = radio[id]['url']

                    if check_key(radio[id], 'icon') and len(str(radio[id]['icon'])) > 0:
                        image = radio[id]['icon']
                    else:
                        image = ''
                        
                    if not check_key(row, 'group') or len(str(row['group'])) == 0:
                        group = 'Radio'
                    else:
                        group = row['group']

                    playlist += u'#EXTINF:0 tvg-id="{id}" tvg-chno="{channel}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}" radio="true",{name}\n{path}\n'.format(id=id, channel=ch_no, name=label, logo=image, group=group, path=path)
            except:
                pass

    write_file(file="playlist.m3u8", data=playlist, isJSON=False)