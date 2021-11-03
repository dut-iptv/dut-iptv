import os, shutil, sys, time, xbmc, xbmcaddon, xbmcplugin

from functools import wraps
from resources.lib.api import api_clean_after_playback, api_get_info
from resources.lib.base.l1.constants import ADDON_ICON, ADDON_FANART, ADDON_ID, ADDON_NAME, ADDON_PROFILE, DEFAULT_USER_AGENT
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import load_file, write_file
from resources.lib.base.l4 import gui
from resources.lib.base.l4.exceptions import PluginError
from resources.lib.base.l5 import signals
from resources.lib.base.l6 import inputstream, router

## SHORTCUTS
url_for = router.url_for
dispatch = router.dispatch
############

def exception(msg=''):
    raise PluginError(msg)

# @plugin.route()
def route(url=None):
    def decorator(f, url):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            item = f(*args, **kwargs)

            if isinstance(item, Folder):
                item.display()
            elif isinstance(item, Item):
                item.play()
            else:
                resolve()

        router.add(url, decorated_function)
        return decorated_function
    return lambda f: decorator(f, url)

def resolve():
    if _handle() > 0:
        xbmcplugin.endOfDirectory(_handle(), succeeded=False, updateListing=False, cacheToDisc=False)

@signals.on(signals.ON_ERROR)
def _error(e):
    try:
        error = str(e)
    except:
        error = e.message.encode('utf-8')

    if not hasattr(e, 'heading') or not e.heading:
        e.heading = _(_.PLUGIN_ERROR, addon=ADDON_NAME)

    log.error(error)
    _close()

    gui.ok(error, heading=e.heading)
    resolve()

@signals.on(signals.ON_EXCEPTION)
def _exception(e):
    log.exception(e)
    _close()
    gui.exception()
    resolve()

@route('')
def _home(**kwargs):
    raise PluginError(_.PLUGIN_NO_DEFAULT_ROUTE)

@route('_ia_install')
def _ia_install(**kwargs):
    _close()
    inputstream.install_widevine()

def reboot():
    _close()
    xbmc.executebuiltin('Reboot')

@signals.on(signals.AFTER_DISPATCH)
def _close():
    signals.emit(signals.ON_CLOSE)

@route('_settings')
def _settings(**kwargs):
    _close()
    settings.open()
    gui.refresh()

@route('_set_settings_kodi')
def _set_settings_kodi(**kwargs):
    _close()

    try:
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"videoplayer.preferdefaultflag", "value":"true"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"locale.audiolanguage", "value":"default"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"locale.subtitlelanguage", "value":"default"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"pvrmanager.preselectplayingchannel", "value":"false"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"pvrmanager.syncchannelgroups", "value":"true"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"pvrmanager.backendchannelorder", "value":"true"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"pvrmanager.usebackendchannelnumbers", "value":"true"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"epg.selectaction", "value":"5"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"epg.pastdaystodisplay", "value":"7"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"epg.futuredaystodisplay", "value":"1"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"epg.hidenoinfoavailable", "value":"true"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"epg.epgupdate", "value":"720"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"epg.preventupdateswhileplayingtv", "value":"true"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"epg.ignoredbforclient", "value":"true"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"pvrrecord.instantrecordaction", "value":"2"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"pvrpowermanagement.enabled", "value":"false"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"settings.SetSettingValue", "params":{"setting":"pvrparental.enabled", "value":"false"}, "id":1}')
        gui.notification(_.DONE_NOREBOOT)
    except:
        pass

@route('_reset')
def _reset(**kwargs):
    if not gui.yes_no(_.PLUGIN_RESET_YES_NO):
        return

    _close()

    try:
        xbmc.executeJSONRPC('{{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{{"addonid":"' + ADDON_ID + '","enabled":false}}}}')

        shutil.rmtree(ADDON_PROFILE)

        directory = os.path.dirname(ADDON_PROFILE + os.sep + "tmp/empty.json")

        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except:
            pass

        directory = os.path.dirname(ADDON_PROFILE + os.sep + "cache/empty.json")

        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except:
            pass
    except:
        pass

    xbmc.executeJSONRPC('{{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{{"addonid":"' + ADDON_ID + '","enabled":true}}}}')

    gui.notification(_.PLUGIN_RESET_OK)
    signals.emit(signals.AFTER_RESET)
    gui.refresh()

def _handle():
    try:
        return int(sys.argv[1])
    except:
        return -1

#Plugin.Item()
class Item(gui.Item):
    def __init__(self, cache_key=None, playback_error=None, *args, **kwargs):
        super(Item, self).__init__(self, *args, **kwargs)
        self.cache_key = cache_key
        self.playback_error = playback_error

    def get_li(self):
        return super(Item, self).get_li()

    def play(self):
        try:
            if 'seekTime' in self.properties or sys.argv[3] == 'resume:true':
                self.properties.pop('ResumeTime', None)
                self.properties.pop('TotalTime', None)
        except:
            pass

        if settings.getBool(key='disable_subtitle'):
            self.properties['disable_subtitle'] = 1

        li = self.get_li()
        handle = _handle()

        #if 'seekTime' in self.properties:
            #li.setProperty('ResumeTime', str(self.properties['seekTime']))

            #if 'totalTime' in self.properties:
            #    li.setProperty('TotalTime', str(self.properties['totalTime']))
            #else:
            #    li.setProperty('TotalTime', '999999')

        player = MyPlayer()

        playbackStarted = False
        seekTime = False
        replay_pvr = False

        if handle > 0:
            if 'Replay' in self.properties or 'PVR' in self.properties:
                replay_pvr = True
                self.properties.pop('Replay', None)
                self.properties.pop('PVR', None)
                xbmcplugin.setResolvedUrl(handle, True, li)
            else:
                xbmcplugin.setResolvedUrl(handle, False, li)
                player.play(self.path, li)
        else:
            player.play(self.path, li)

        while player.is_active:
            if xbmc.getCondVisibility("Player.HasMedia") and player.is_started:
                playbackStarted = True
                
                if 'disable_subtitle' in self.properties:
                    player.showSubtitles(False)
                    self.properties.pop('disable_subtitle', None)

                if 'seekTime' in self.properties:
                    seekTime = True
                    xbmc.Monitor().waitForAbort(1)
                    player.seekTime(int(self.properties['seekTime']))
                    self.properties.pop('seekTime', None)

                if not replay_pvr and not seekTime and 'Live' in self.properties and 'Live_ID' in self.properties and 'Live_Channel' in self.properties:
                    id = self.properties['Live_ID']
                    channel = self.properties['Live_Channel']

                    self.properties.pop('Live', None)
                    self.properties.pop('Live_ID', None)
                    self.properties.pop('Live_Channel', None)

                    wait = 60

                    end = load_file(file='stream_end', isJSON=False)

                    if end:
                        calc_wait = int(end) - int(time.time()) + 30

                        if calc_wait > 60:
                            wait = calc_wait

                    while not xbmc.Monitor().waitForAbort(wait) and xbmc.getCondVisibility("Player.HasMedia") and player.is_started:
                        info = api_get_info(id=id, channel=channel)

                        if info:
                            info2 = {
                                'plot': str(info['description']),
                                'title': str(info['label1']),
                                'tagline': str(info['label2']),
                                'duration': info['duration'],
                                'credits': info['credits'],
                                'cast': info['cast'],
                                'director': info['director'],
                                'writer': info['writer'],
                                'genre': info['genres'],
                                'year': info['year'],
                            }

                            li.setInfo('video', info2)

                            li.setArt({'thumb': info['image'], 'icon': info['image'], 'fanart': info['image_large'] })

                            try:
                                player.updateInfoTag(li)
                            except:
                                pass

                            wait = 60
                            end = load_file(file='stream_end', isJSON=False)

                            if end:
                                calc_wait = int(end) - int(time.time()) + 30

                                if calc_wait > 60:
                                    wait = calc_wait

            xbmc.Monitor().waitForAbort(1)

        if playbackStarted == True:
            api_clean_after_playback()

class MyPlayer(xbmc.Player):
    def __init__(self):
        self.is_active = True
        self.is_started = False

    def onPlayBackPaused(self):
        pass

    def onPlayBackResumed(self):
        pass

    def onPlayBackStarted(self):
        self.is_started = True
        pass

    def onPlayBackEnded(self):
        self.is_active = False

    def onPlayBackStopped(self):
        self.is_active = False

    def sleep(self, s):
        xbmc.sleep(s)

#Plugin.Folder()
class Folder(object):
    def __init__(self, items=None, title=None, content='videos', updateListing=False, cacheToDisc=True, sort_methods=None, thumb=None, fanart=None, no_items_label=_.NO_ITEMS):
        self.items = items or []
        self.title = title
        self.content = content
        self.updateListing = updateListing
        self.cacheToDisc = cacheToDisc
        self.sort_methods = sort_methods or [xbmcplugin.SORT_METHOD_UNSORTED, xbmcplugin.SORT_METHOD_LABEL]
        self.thumb = thumb or ADDON_ICON
        self.fanart = fanart or ADDON_FANART
        self.no_items_label = no_items_label

    def display(self):
        handle = _handle()
        items = [i for i in self.items if i]

        if not items and self.no_items_label:
            items.append(Item(
                label = _(self.no_items_label, _label=True),
                is_folder = False,
            ))

        for item in items:
            item.art['thumb'] = item.art.get('thumb') or self.thumb
            item.art['fanart'] = item.art.get('fanart') or self.fanart

            li = item.get_li()
            xbmcplugin.addDirectoryItem(handle, item.path, li, item.is_folder)

        if self.content: xbmcplugin.setContent(handle, self.content)
        if self.title: xbmcplugin.setPluginCategory(handle, self.title)

        for sort_method in self.sort_methods:
            xbmcplugin.addSortMethod(handle, sort_method)

        xbmcplugin.endOfDirectory(handle, succeeded=True, updateListing=self.updateListing, cacheToDisc=self.cacheToDisc)

    def add_item(self, *args, **kwargs):
        position = kwargs.pop('_position', None)

        item = Item(*args, **kwargs)

        if position == None:
            self.items.append(item)
        else:
            self.items.insert(int(position), item)

        return item

    def add_items(self, items):
        if isinstance(items, list):
            self.items.extend(items)
        elif isinstance(items, Item):
            self.items.append(items)
        else:
            raise Exception('add_items only accepts an Item or list of Items')
