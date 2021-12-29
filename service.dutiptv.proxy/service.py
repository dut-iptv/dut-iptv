import datetime, io, json, pytz, os, re, requests, sys, threading, time, xbmc, xbmcaddon, xbmcvfs, xbmcgui
import http.server as ProxyServer

from collections import OrderedDict
from resources.lib.constants import *
from resources.lib.dnsutils import override_dns
from xml.dom.minidom import parseString

stream_url = {}
now_playing = 0
last_token = 0
audio_segments = {}
last_segment = 0
last_timecode = 0

class HTTPMonitor(xbmc.Monitor):
    def __init__(self, addon):
        super(HTTPMonitor, self).__init__()
        self.addon = addon

class HTTPServer(ProxyServer.HTTPServer):
    def __init__(self, addon, server_address):
        ProxyServer.HTTPServer.__init__(self, server_address, HTTPRequestHandler)
        self.addon = addon

class HTTPRequestHandler(ProxyServer.BaseHTTPRequestHandler):
    def do_GET(self):
        global stream_url, now_playing, last_token, audio_segments, last_segment, last_timecode

        if "/status" in self.path:
            self.send_response(200)
            self.send_header('X-TEST', 'OK')
            self.end_headers()
        else:
            if "/betelenet/" in self.path:
                addon_name = 'betelenet'
            elif "/canaldigitaal/" in self.path:
                addon_name = 'canaldigitaal'
            elif "/kpn/" in self.path:
                addon_name = 'kpn'
            elif "/nlziet/" in self.path:
                addon_name = 'nlziet'
            elif "/tmobile/" in self.path:
                addon_name = 'tmobile'
            elif "/videoland/" in self.path:
                addon_name = 'videoland'
            elif "/ziggo/" in self.path:
                addon_name = 'ziggo'

            self.path = self.path.replace('{addon_name}/'.format(addon_name=addon_name), '', 1)

            ADDON = xbmcaddon.Addon(id="plugin.video.{addon_name}".format(addon_name=addon_name))
            ADDON_PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

            if proxy_get_match(path=self.path, addon_name=addon_name) and os.path.isfile(ADDON_PROFILE + 'stream_hostname'):
                stream_url[addon_name] = load_file(file=ADDON_PROFILE + 'stream_hostname', isJSON=False)

                try:
                    os.remove(ADDON_PROFILE + 'stream_hostname')
                except:
                    pass

                now_playing = int(time.time())
                last_token = int(time.time()) + 60

                URL = proxy_get_url(proxy=self, addon_name=addon_name, ADDON_PROFILE=ADDON_PROFILE)

                if addon_name == 'kpn':
                    start = load_file(file=ADDON_PROFILE + 'stream_start', isJSON=False)

                    if start:
                        startT = datetime.datetime.fromtimestamp(int(start))
                        mytz = pytz.timezone('Europe/Amsterdam')
                        startTUTC = mytz.normalize(mytz.localize(startT, is_dst=True)).astimezone(pytz.timezone('UTC'))
                        URL += '&t={date1}%3A{date2}%3A{date3}.000'.format(date1=startTUTC.strftime('%Y-%m-%dT%H'), date2=startTUTC.strftime('%M'), date3=startTUTC.strftime('%S'))

                session = proxy_get_session(proxy=self, addon_name=addon_name)
                r = session.get(URL)

                xml = r.text

                if 'mpd' in xml.lower():
                    #write_file(file=ADDON_PROFILE + 'full_url', data=URL, isJSON=False)
                    #write_file(file=ADDON_PROFILE + 'orig.mpd', data=xml, isJSON=False)

                    xml = sly_mpd_parse(data=xml).decode('utf-8')

                    #write_file(file=ADDON_PROFILE + 'after_sly_mpd_parse.mpd', data=xml, isJSON=False)

                    xml = mpd_parse(data=xml, addon_name=addon_name, URL=URL).decode('utf-8')

                    #write_file(file=ADDON_PROFILE + 'after_mpd_parse.mpd', data=xml, isJSON=False)

                self.send_response(r.status_code)

                r.headers['Content-Length'] = len(xml)

                for header in r.headers:
                    if not 'Content-Encoding' in header and not 'Transfer-Encoding' in header:
                        self.send_header(header, r.headers[header])

                self.end_headers()
                r.close()

                try:
                    xml = xml.encode('utf-8')
                except:
                    pass

                try:
                    self.wfile.write(xml)
                except:
                    pass

                try:
                    self.connection.close()
                except:
                    pass
            else:
                URL = proxy_get_url(proxy=self, addon_name=addon_name, ADDON_PROFILE=ADDON_PROFILE)

                if addon_name == "kpn" and 'npo1-audio_dut=128000-' in URL.lower():
                    URL = fix_audio(URL)

                now_playing = int(time.time())

                if (addon_name == 'betelenet' or addon_name == 'ziggo') and last_token < now_playing:
                    token_renew = load_file(file=ADDON_PROFILE + 'token_renew', isJSON=False)
                    xbmc.executebuiltin('RunPlugin(%s)' % (token_renew))
                    last_token = int(time.time()) + 60

                self.send_response(302)
                self.send_header('Location', URL)
                self.end_headers()

                try:
                    self.connection.close()
                except:
                    pass

    def log_message(self, format, *args):
        return

class RemoteControlBrowserService(xbmcaddon.Addon):
    def __init__(self):
        super(RemoteControlBrowserService, self).__init__()
        self.pluginId = self.getAddonInfo('id')

        self.addonFolder = xbmcvfs.translatePath(self.getAddonInfo('path'))
        self.profileFolder = xbmcvfs.translatePath(self.getAddonInfo('profile'))

        self.settingsChangeLock = threading.Lock()
        self.isShutdown = False
        self.HTTPServer = None
        self.HTTPServerThread = None

    def clearBrowserLock(self):
        """Clears the pidfile in case the last shutdown was not clean"""
        browserLockPath = os.path.join(self.profileFolder, 'browser.pid')
        try:
            os.remove(browserLockPath)
        except OSError:
            pass

    def reloadHTTPServer(self):
        with self.settingsChangeLock:
            self.startHTTPServer()

    def shutdownHTTPServer(self):
        with self.settingsChangeLock:
            self.stopHTTPServer()
            self.isShutdown = True

    def startHTTPServer(self):
        if self.isShutdown:
            return

        self.stopHTTPServer()

        try:
            self.HTTPServer = HTTPServer(self, ('', 11189))
        except IOError as e:
            pass

        threadStarting = threading.Thread(target=self.HTTPServer.serve_forever)
        threadStarting.start()
        self.HTTPServerThread = threadStarting

    def stopHTTPServer(self):
        if self.HTTPServer is not None:
            self.HTTPServer.shutdown()
            self.HTTPServer = None
        if self.HTTPServerThread is not None:
            self.HTTPServerThread.join()
            self.HTTPServerThread = None

class Session(requests.Session):
    def __init__(self, addon_name='', headers=None, cookies_key=None, save_cookies=True, base_url='{}', timeout=None, attempts=None):
        super(Session, self).__init__()

        base_headers = CONST_BASE_HEADERS[addon_name]
        base_headers.update({'User-Agent': DEFAULT_USER_AGENT})

        if headers:
            base_headers.update(headers)

        self._headers = base_headers or {}
        self._cookies_key = cookies_key
        self._save_cookies = save_cookies
        self._base_url = base_url
        self._timeout = timeout or (5, 10)
        self._attempts = attempts or 2
        self._addon_name = addon_name

        ADDON = xbmcaddon.Addon(id="plugin.video." + addon_name)

        self._addon_profile = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

        self.headers.update(self._headers)

        if self._cookies_key:
            try:
                cookies = load_file(file=self._addon_profile + 'stream_cookies', isJSON=True)
            except:
                cookies = {}

            self.cookies.update(cookies)

    def request(self, method, url, timeout=None, attempts=None, **kwargs):
        if not url.startswith('http'):
            url = self._base_url.format(url)

        kwargs['timeout'] = timeout or self._timeout
        attempts = attempts or self._attempts

        if sys.version_info < (3, 0):
            rngattempts = range(1, attempts+1)
        else:
            rngattempts = list(range(1, attempts+1))

        for i in rngattempts:
            #log.debug('Attempt {}/{}: {} {} {}'.format(i, attempts, method, url, kwargs if method.lower() != 'post' else ""))

            try:
                if (self._addon_name == 'betelenet' or self._addon_name == 'ziggo'):
                    override_dns(CONST_BASE_DOMAIN[self._addon_name], CONST_BASE_IP[self._addon_name])

                data = super(Session, self).request(method, url, **kwargs)

                if self._cookies_key and self._save_cookies:
                    self.save_cookies(ADDON_PROFILE=self._addon_profile)

                return data
            except:
                if i == attempts:
                    raise

    def save_cookies(self, ADDON_PROFILE):
        if not self._cookies_key:
            raise Exception('A cookies key needs to be set to save cookies')

        write_file(file=ADDON_PROFILE + 'stream_cookies', data=self.cookies.get_dict(), isJSON=True)

    def clear_cookies(self):
        self.cookies.clear()

    def chunked_dl(self, url, dst_path, method='GET'):
        resp = self.request(method, url, stream=True)
        resp.raise_for_status()

        with open(dst_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=4096):
                f.write(chunk)

def main():
    global now_playing

    service = RemoteControlBrowserService()
    service.clearBrowserLock()
    monitor = HTTPMonitor(service)

    loop = True

    while loop == True:
        xbmc.log('(RE)START DUT-IPTV PROXY')
        service.reloadHTTPServer()

        if monitor.waitForAbort(3600):
            loop = False

        while int(now_playing) + 120 > int(time.time()) and loop == True:
            if monitor.waitForAbort(600):
                loop = False

    service.shutdownHTTPServer()

def sly_mpd_parse(data):
    data = data.replace('_xmlns:cenc', 'xmlns:cenc')
    data = data.replace('_:default_KID', 'cenc:default_KID')
    data = data.replace('<pssh', '<cenc:pssh')
    data = data.replace('</pssh>', '</cenc:pssh>')

    root = parseString(data.encode('utf8'))

    mpd = root.getElementsByTagName("MPD")[0]

    ## Set publishtime to utctime
    utc_time = mpd.getElementsByTagName("UTCTiming")
    if utc_time:
        value = utc_time[0].getAttribute('value')
        mpd.setAttribute('publishTime', value)

    for elem in mpd.getElementsByTagName("SupplementalProperty"):
        if elem.getAttribute('schemeIdUri') == 'urn:scte:dash:utc-time':
            value = elem.getAttribute('value')
            mpd.setAttribute('publishTime', value)
            break

    base_url_nodes = []

    for node in mpd.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            if node.localName == 'BaseURL':
                base_url_nodes.append(node)

    if base_url_nodes:
        base_url_nodes.pop(0)

        for e in base_url_nodes:
            e.parentNode.removeChild(e)

    if 'type' in mpd.attributes.keys() and mpd.getAttribute('type').lower() == 'dynamic':
        periods = [elem for elem in root.getElementsByTagName('Period')]

        if len(periods) > 1:
            periods.pop()
            for e in periods:
                e.parentNode.removeChild(e)

    for elem in root.getElementsByTagName('AudioChannelConfiguration'):
        if elem.getAttribute('schemeIdUri') == 'tag:dolby.com,2014:dash:audio_channel_configuration:2011':
            elem.setAttribute('schemeIdUri', 'urn:dolby:dash:audio_channel_configuration:2011')

    for elem in root.getElementsByTagName('Representation'):
        parent = elem.parentNode
        parent.removeChild(elem)
        parent.appendChild(elem)

    video_sets = []
    other_sets = []
    trick_sets = []

    for adap_set in root.getElementsByTagName('AdaptationSet'):
        highest_bandwidth = 0
        is_video = False
        is_trick = False

        adapt_frame_rate = adap_set.getAttribute('frameRate')
        if adapt_frame_rate and '/' not in adapt_frame_rate:
            adapt_frame_rate = None

        if adapt_frame_rate:
            adap_set.removeAttribute('frameRate')

        if 'video' in adap_set.getAttribute('mimeType'):
            is_video = True

        for stream in adap_set.getElementsByTagName("Representation"):
            attrib = {}

            for key in adap_set.attributes.keys():
                attrib[key] = adap_set.getAttribute(key)

            for key in stream.attributes.keys():
                attrib[key] = stream.getAttribute(key)

            if adapt_frame_rate and not stream.getAttribute('frameRate'):
                stream.setAttribute('frameRate', adapt_frame_rate)

            if 'bandwidth' in attrib:
                bandwidth = int(attrib['bandwidth'])
                if bandwidth > highest_bandwidth:
                    highest_bandwidth = bandwidth

            if 'maxPlayoutRate' in attrib:
                is_video = False
                is_trick = True

        parent = adap_set.parentNode
        parent.removeChild(adap_set)

        if is_trick:
            trick_sets.append([highest_bandwidth, adap_set, parent])
        elif is_video:
            video_sets.append([highest_bandwidth, adap_set, parent])
        else:
            other_sets.append([highest_bandwidth, adap_set, parent])

    video_sets.sort(key=lambda  x: x[0], reverse=True)
    trick_sets.sort(key=lambda  x: x[0], reverse=True)
    other_sets.sort(key=lambda  x: x[0], reverse=True)

    for elem in video_sets:
        elem[2].appendChild(elem[1])

    for elem in trick_sets:
        elem[2].appendChild(elem[1])

    for elem in other_sets:
        elem[2].appendChild(elem[1])

    elems = root.getElementsByTagName('SegmentTemplate')
    elems.extend(root.getElementsByTagName('SegmentURL'))

    for e in elems:
        def process_attrib(attrib):
            if attrib not in e.attributes.keys():
                return

        process_attrib('initialization')
        process_attrib('media')

        if 'presentationTimeOffset' in e.attributes.keys():
            e.removeAttribute('presentationTimeOffset')

    return root.toxml(encoding='utf-8')

def mpd_parse(data, addon_name, URL):
    global audio_segments, last_segment, last_timecode

    audio_segments = {}
    temp_segments = {}
    temp_audio_segments = []
    ac3_found = False

    root = parseString(data.encode('utf8'))
    mpd = root.getElementsByTagName("MPD")[0]

    ADDON = xbmcaddon.Addon(id="plugin.video." + addon_name)
    ADDON_PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

    duration = load_file(file=ADDON_PROFILE + 'stream_duration', isJSON=False)

    if duration and int(duration) > 0 and 'mediaPresentationDuration' in mpd.attributes.keys():
        duration = int(duration)
        given_duration = 0
        given_day = 0
        given_hour = 0
        given_minute = 0
        given_second = 0

        duration += ADDON.getSettingInt("add_duration")

        mediaPresentationDuration = mpd.getAttribute('mediaPresentationDuration').lower()

        regex = r"pt([0-9]*)[d]*([0-9]*)[h]*([0-9]*)[m]*([0-9]*)[s]*"
        matches = re.finditer(regex, mediaPresentationDuration)

        for matchNum, match in enumerate(matches, start=1):
            if not match.group(1):
                continue
            elif not match.group(4):
                given_second = int(match.group(1))
            elif not match.group(3):
                given_minute = int(match.group(1))
                given_second = int(match.group(4))
            elif not match.group(2):
                given_hour = int(match.group(1))
                given_minute = int(match.group(3))
                given_second = int(match.group(4))
            else:
                given_day = int(match.group(1))
                given_hour = int(match.group(2))
                given_minute = int(match.group(3))
                given_second = int(match.group(4))

            given_duration = (given_day * 24* 60 * 60) + (given_hour * 60 * 60) + (given_minute * 60) + given_second

        if not given_duration > 0 or given_duration > duration:
            minute, second = divmod(duration, 60)
            hour, minute = divmod(minute, 60)

            mpd.setAttribute('mediaPresentationDuration', 'PT{hour}H{minute}M{second}S'.format(hour=hour, minute=minute, second=second))

    prefered_language = load_file(file=ADDON_PROFILE + 'stream_language', isJSON=False)

    try:
        prefered_language = AUDIO_LANGUAGES_REV[prefered_language]
    except:
        pass

    for adap_set in root.getElementsByTagName('AdaptationSet'):
        if 'audio' in adap_set.getAttribute('mimeType'):
            for stream in adap_set.getElementsByTagName("Representation"):
                attrib = {}

                for key in adap_set.attributes.keys():
                    attrib[key] = adap_set.getAttribute(key)

                for key in stream.attributes.keys():
                    attrib[key] = stream.getAttribute(key)

                if prefered_language and check_key(attrib, 'lang') and attrib['lang'].lower() != prefered_language:
                    parent = stream.parentNode
                    parent.removeChild(stream)
                    continue

                try:
                    if attrib['codecs'].lower() == 'ac-3':
                        ac3_found = True
                except:
                    pass
        elif 'video' in adap_set.getAttribute('mimeType') and ADDON.getSettingBool('force_highest_bandwidth'):
            highest_bandwidth = 0
            is_video = True
            is_trick = False

            for stream in adap_set.getElementsByTagName("Representation"):
                attrib = {}

                for key in adap_set.attributes.keys():
                    attrib[key] = adap_set.getAttribute(key)

                for key in stream.attributes.keys():
                    attrib[key] = stream.getAttribute(key)

                if 'bandwidth' in attrib:
                    bandwidth = int(attrib['bandwidth'])
                    if bandwidth > highest_bandwidth:
                        highest_bandwidth = bandwidth

                if 'maxPlayoutRate' in attrib:
                    is_video = False
                    is_trick = True

            if is_trick:
                for stream in adap_set.getElementsByTagName("Representation"):
                    attrib = {}

                    for key in adap_set.attributes.keys():
                        attrib[key] = adap_set.getAttribute(key)

                    for key in stream.attributes.keys():
                        attrib[key] = stream.getAttribute(key)

                    if 'bandwidth' in attrib and 'maxPlayoutRate' in attrib:
                        bandwidth = int(attrib['bandwidth'])

                        if bandwidth != highest_bandwidth:
                            parent = stream.parentNode
                            parent.removeChild(stream)
            elif is_video:
                for stream in adap_set.getElementsByTagName("Representation"):
                    attrib = {}

                    for key in adap_set.attributes.keys():
                        attrib[key] = adap_set.getAttribute(key)

                    for key in stream.attributes.keys():
                        attrib[key] = stream.getAttribute(key)

                    if 'bandwidth' in attrib and not 'maxPlayoutRate' in attrib:
                        bandwidth = int(attrib['bandwidth'])

                        if bandwidth != highest_bandwidth:
                            parent = stream.parentNode
                            parent.removeChild(stream)

    if ac3_found == True and ADDON.getSettingBool('force_ac3'):
        for adap_set in root.getElementsByTagName('AdaptationSet'):
            if 'audio' in adap_set.getAttribute('mimeType'):
                for stream in adap_set.getElementsByTagName("Representation"):
                    attrib = {}

                    for key in adap_set.attributes.keys():
                        attrib[key] = adap_set.getAttribute(key)

                    for key in stream.attributes.keys():
                        attrib[key] = stream.getAttribute(key)

                    try:
                        if not attrib['codecs'].lower() == 'ac-3':
                            parent = stream.parentNode
                            parent.removeChild(stream)
                    except:
                        pass

    if addon_name == "kpn" and 'npo1' in URL.lower():
        last_segment = 0
        last_timecode = 0

        for adap_set in root.getElementsByTagName('AdaptationSet'):
            if 'audio' in adap_set.getAttribute('mimeType'):
                for segmenttimeline in adap_set.getElementsByTagName("SegmentTimeline"):
                    for segment in segmenttimeline.getElementsByTagName("S"):
                        if not 'd' in segment.attributes.keys():
                            continue

                        temp_segments[segment.getAttribute('d')] = 1

    for segment in temp_segments:
        temp_audio_segments.append(segment)

    last = 0
    count = int(len(temp_audio_segments)) - 1

    temp_audio_segments.reverse()

    for segment in temp_audio_segments:
        if last == 0:
            audio_segments[segment] = temp_audio_segments[count]
        else:
            audio_segments[segment] = last

        last = segment
                
    for adap_set in root.getElementsByTagName('AdaptationSet'):
        if len(adap_set.getElementsByTagName("Representation")) == 0:
            parent = adap_set.parentNode
            parent.removeChild(adap_set)

    return root.toxml(encoding='utf-8')

def fix_audio(URL):
    global audio_segments, last_segment, last_timecode

    old_last_timecode = 0
    temp_last_timecode = 0

    try:
        if int(URL.replace('.dash', '').rsplit('-', 1)[1]) < last_timecode:
            last_segment = 0
            last_timecode = 0

        if last_segment == 0 and last_timecode == 0:
            last_timecode = int(URL.replace('.dash', '').rsplit('-', 1)[1])
        elif last_segment == 0:
            old_last_timecode = last_timecode
            last_timecode = int(URL.replace('.dash', '').rsplit('-', 1)[1])
            last_segment = int(last_timecode - old_last_timecode)
        else:
            old_last_timecode = last_timecode
            last_timecode = int(URL.replace('.dash', '').rsplit('-', 1)[1])

            if (last_timecode - old_last_timecode) != audio_segments[str(last_segment)]:
                temp_last_timecode = last_timecode
                last_timecode = int(old_last_timecode + int(audio_segments[str(last_segment)]))
                last_segment = int(audio_segments[str(last_segment)])

                URL = URL.replace(str(temp_last_timecode), str(last_timecode))
            else:
                last_segment = int(last_timecode - old_last_timecode)
    except:
        pass

    return URL

def check_key(object, key):
    if key in object and object[key] and len(str(object[key])) > 0:
        return True
    else:
        return False

def load_file(file, isJSON=False):
    if not os.path.isfile(file):
        return None

    with io.open(file, 'r', encoding='utf-8') as f:
        if isJSON == True:
            return json.load(f, object_pairs_hook=OrderedDict)
        else:
            return f.read()

def proxy_get_match(path, addon_name):
    if addon_name == 'betelenet' or addon_name == 'ziggo':
        if "manifest.mpd" in path or "Manifest" in path:
            return True
    else:
        if ".mpd" in path:
            return True

    return False

def proxy_get_session(proxy, addon_name):
    if addon_name == 'betelenet' or addon_name == 'ziggo':
        HEADERS = CONST_BASE_HEADERS[addon_name]

        for header in proxy.headers:
            if proxy.headers[header] is not None and header in CONST_ALLOWED_HEADERS[addon_name]:
                HEADERS[header] = proxy.headers[header]

        return Session(addon_name=addon_name, headers=HEADERS)

    else:
        return Session(addon_name=addon_name, cookies_key='cookies', save_cookies=False)

def proxy_get_url(proxy, addon_name, ADDON_PROFILE):
    global stream_url

    if addon_name == 'betelenet' or addon_name == 'ziggo':
        return stream_url[addon_name] + str(proxy.path).replace('WIDEVINETOKEN', load_file(file=ADDON_PROFILE + 'widevine_token', isJSON=False))
    else:
        return stream_url[addon_name] + str(proxy.path)

def write_file(file, data, isJSON=False):
    with io.open(file, 'w', encoding="utf-8") as f:
        if isJSON == True:
            f.write(json.dumps(data, ensure_ascii=False))
        else:
            f.write(data)

if __name__ == "__main__":
    main()