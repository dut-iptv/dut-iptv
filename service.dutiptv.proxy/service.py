import datetime, io, json, pytz, os, re, requests, sys, threading, time, xbmc, xbmcaddon, xbmcvfs, xbmcgui
import http.server as ProxyServer

from xml.dom.minidom import parseString

PROXY_PROFILE = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))

CONST_ALLOWED_HEADERS = {}

CONST_ALLOWED_HEADERS['ziggo'] = {
    'user-agent',
    'x-oesp-content-locator',
    'x-oesp-token',
    'x-client-id',
    'x-oesp-username',
    'x-oesp-drm-schemeiduri'
}

CONST_BASE_HEADERS = {}

CONST_BASE_HEADERS['canaldigitaal'] = {
    'Accept': 'application/json, text/plain, */*',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': 'https://livetv.canaldigitaal.nl',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://livetv.canaldigitaal.nl/',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q: 0.9,nl;q: 0.8',
}

CONST_BASE_HEADERS['kpn'] = {
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'AVSSite': 'http://www.itvonline.nl',
    'Accept': '*/*',
    'Origin': 'https://tv.kpn.com',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://tv.kpn.com/',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q: 0.9,nl;q: 0.8',
}

CONST_BASE_HEADERS['nlziet'] = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': 'https://app.nlziet.nl',
    'Pragma': 'no-cache',
    'Referer': 'https://app.nlziet.nl/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

CONST_BASE_HEADERS['tmobile'] = {
    'Accept': '*/*',
    'Accept-Language': 'nl',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': 'https://t-mobiletv.nl',
    'Pragma': 'no-cache',
    'Referer': 'https://t-mobiletv.nl/inloggen/index.html',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

CONST_BASE_HEADERS['ziggo'] = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': 'https://www.ziggogo.tv',
    'Pragma': 'no-cache',
    'Referer': 'https://www.ziggogo.tv/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
}

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'

stream_url = {}
now_playing = 0
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
        global stream_url, now_playing, audio_segments, last_segment, last_timecode

        if "/status" in self.path:
            self.send_response(200)
            self.send_header('X-TEST', 'OK')
            self.end_headers()
        else:
            if "/canaldigitaal/" in self.path:
                addon_name = 'canaldigitaal'
            elif "/kpn/" in self.path:
                addon_name = 'kpn'
            elif "/nlziet/" in self.path:
                addon_name = 'nlziet'
            elif "/tmobile/" in self.path:
                addon_name = 'tmobile'
            elif "/ziggo/" in self.path:
                addon_name = 'ziggo'

            self.path = self.path.replace(addon_name + '/', '')

            ADDON = xbmcaddon.Addon(id="plugin.video." + addon_name)

            ADDON_PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

            if proxy_get_match(path=self.path, addon_name=addon_name):
                stream_url[addon_name] = load_file(file=ADDON_PROFILE + 'stream_hostname', isJSON=False)
                now_playing = int(time.time())

                URL = proxy_get_url(proxy=self, addon_name=addon_name, ADDON_PROFILE=ADDON_PROFILE)

                if addon_name == 'kpn':
                    start = load_file(file=ADDON_PROFILE + 'stream_start', isJSON=False)

                    if start:
                        startT = datetime.datetime.fromtimestamp(int(start))
                        mytz = pytz.timezone('Europe/Amsterdam')
                        startTUTC = mytz.normalize(mytz.localize(startT, is_dst=True)).astimezone(pytz.timezone('UTC'))
                        URL += '&t=' + str(startTUTC.strftime('%Y-%m-%dT%H')) + '%3A' + str(startTUTC.strftime('%M')) + '%3A' + str(startTUTC.strftime('%S.000'))

                session = proxy_get_session(proxy=self, addon_name=addon_name)
                r = session.get(URL)

                xml = r.text

                #write_file(file=ADDON_PROFILE + 'orig_xml', data=xml, isJSON=False)

                xml = sly_mpd_parse(xml=xml, base=URL.rsplit('/', 1)[0] + '/').decode('utf-8')

                #write_file(file=ADDON_PROFILE + 'after_sly_xml', data=xml, isJSON=False)

                xml = set_duration(xml=xml, addon_name=addon_name, ADDON_PROFILE=ADDON_PROFILE)

                #write_file(file=ADDON_PROFILE + 'after_set_duration_xml', data=xml, isJSON=False)

                if ADDON.getSettingBool('disable_subtitle'):
                    xml = remove_subs(xml=xml)
                    #write_file(file=ADDON_PROFILE + 'after_remove_subs_xml', data=xml, isJSON=False)

                if ADDON.getSettingBool('force_highest_bandwidth'):
                    xml = force_highest_bandwidth(xml=xml, trick=False)
                    xml = force_highest_bandwidth(xml=xml, trick=True)
                    #write_file(file=ADDON_PROFILE + 'after_force_highest_bandwidth_xml', data=xml, isJSON=False)

                xml = proxy_xml_mod(xml=xml, addon_name=addon_name)

                #write_file(file=ADDON_PROFILE + 'after_proxy_xml_mod_xml', data=xml, isJSON=False)

                if ADDON.getSettingBool("force_ac3"):
                    xml = force_ac3(xml=xml)

                #write_file(file=ADDON_PROFILE + 'after_force_surround_xml', data=xml, isJSON=False)

                if addon_name == "kpn" and 'NPO1' in URL:
                    fix_audio_start(xml)
                    last_segment = 0
                    last_timecode = 0

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

                if addon_name == "kpn" and 'NPO1-audio_dut=128000-' in URL:
                    URL = fix_audio(URL)

                now_playing = int(time.time())

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

def sly_mpd_parse(xml, base=''):
    data = xml

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
                #url = node.firstChild.nodeValue

                #if not url.startswith('http'):
                #    node.firstChild.nodeValue = base + url

                base_url_nodes.append(node)

    # Keep first base_url node
    if base_url_nodes:
        base_url_nodes.pop(0)

        for e in base_url_nodes:
            e.parentNode.removeChild(e)
    #else:
    #    base_url_node = root.createElement("BaseURL")
    #    base_url_node_text = root.createTextNode(base)
    #    base_url_node.appendChild(base_url_node_text)
    #    mpd_chidren = mpd.childNodes
    #    mpd.insertBefore(base_url_node, mpd_chidren[0])

    ####################

    ## Live mpd needs non-last periods removed
    ## https://github.com/peak3d/inputstream.adaptive/issues/574
    if 'type' in mpd.attributes.keys() and mpd.getAttribute('type').lower() == 'dynamic':
        periods = [elem for elem in root.getElementsByTagName('Period')]

        # Keep last period
        if len(periods) > 1:
            periods.pop()
            for e in periods:
                e.parentNode.removeChild(e)
    #################################################

    ## SUPPORT NEW DOLBY FORMAT
    ## PR to fix in IA: https://github.com/peak3d/inputstream.adaptive/pull/466
    for elem in root.getElementsByTagName('AudioChannelConfiguration'):
        if elem.getAttribute('schemeIdUri') == 'tag:dolby.com,2014:dash:audio_channel_configuration:2011':
            elem.setAttribute('schemeIdUri', 'urn:dolby:dash:audio_channel_configuration:2011')
    ###########################

    ## Make sure Representation are last in adaptionset
    for elem in root.getElementsByTagName('Representation'):
        parent = elem.parentNode
        parent.removeChild(elem)
        parent.appendChild(elem)

    ## SORT ADAPTION SETS BY BITRATE ##
    video_sets = []
    audio_sets = []
    trick_sets = []
    lang_adap_sets = []

    for adap_set in root.getElementsByTagName('AdaptationSet'):
        highest_bandwidth = 0
        is_video = False
        is_trick = False

        adapt_frame_rate = adap_set.getAttribute('frameRate')
        if adapt_frame_rate and '/' not in adapt_frame_rate:
            adapt_frame_rate = None

        if adapt_frame_rate:
            adap_set.removeAttribute('frameRate')

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

            if 'video' in attrib.get('mimeType', ''):
                is_video = True

            if 'maxPlayoutRate' in attrib:
                is_trick = True

        parent = adap_set.parentNode
        parent.removeChild(adap_set)

        if is_trick:
            trick_sets.append([highest_bandwidth, adap_set, parent])
        elif is_video:
            video_sets.append([highest_bandwidth, adap_set, parent])
        else:
            audio_sets.append([highest_bandwidth, adap_set, parent])

    video_sets.sort(key=lambda  x: x[0], reverse=True)
    audio_sets.sort(key=lambda  x: x[0], reverse=True)
    trick_sets.sort(key=lambda  x: x[0], reverse=True)

    for elem in video_sets:
        elem[2].appendChild(elem[1])

    for elem in audio_sets:
        elem[2].appendChild(elem[1])

    for elem in trick_sets:
        elem[2].appendChild(elem[1])
    ##################

    elems = root.getElementsByTagName('SegmentTemplate')
    elems.extend(root.getElementsByTagName('SegmentURL'))

    for e in elems:
        def process_attrib(attrib):
            if attrib not in e.attributes.keys():
                return

            url = e.getAttribute(attrib)

            if url.startswith('http'):
                e.setAttribute(attrib, PROXY_PATH + url)

        process_attrib('initialization')
        process_attrib('media')

        ## PR TO FIX: https://github.com/peak3d/inputstream.adaptive/pull/564
        if 'presentationTimeOffset' in e.attributes.keys():
            e.removeAttribute('presentationTimeOffset')
        ###################

    return root.toxml(encoding='utf-8')

def force_ac3(xml):
    try:
        found = False

        result = re.findall(r'<[aA]daptation[sS]et(?:(?!<[aA]daptation[sS]et)(?!</[aA]daptation[sS]et>)[\S\s])+</[aA]daptation[sS]et>', xml)
        result2 = []

        for match in result:
            if not 'contentType="audio"' in match:
                continue

            if 'codecs="ac-3"' in match:
                found = True

            result2.append(match)

        if found:
            for match in result2:
                if not 'codecs="ac-3"' in match:
                    xml = xml.replace(match, "")

    except:
        pass

    return xml

def fix_audio_start(xml):
    global audio_segments

    audio_segments = {}
    temp_segments = {}
    temp_audio_segments = []

    found = False

    result = re.findall(r'<[aA]daptation[sS]et(?:(?!<[aA]daptation[sS]et)(?!</[aA]daptation[sS]et>)[\S\s])+</[aA]daptation[sS]et>', xml)

    for match in result:
        if not 'contentType="audio"' in match:
            continue

        match2 = re.findall(r'<S[\sA-Za-z0-9="]*\s*d="([0-9]*)"[\s\/A-Za-z0-9="]*\/>', match)

        for match3 in match2:
            temp_segments[match3] = 1

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

def fix_audio(URL):
    global audio_segments, last_segment, last_timecode

    old_last_timecode = 0
    temp_last_timecode = 0

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
    return URL

def force_highest_bandwidth(xml, trick=False):
    results = {}
    bandwidth_regex = r"bandwidth=\"([0-9]+)\""

    result = re.findall(r'<[rR]epresentation(?:(?!<[rR]epresentation)(?!</[rR]epresentation>)[\S\s])+</[rR]epresentation>', xml)

    for match in result:
        if not 'bandwidth' in match or not 'codecs' in match or not 'width' in match or not 'height' in match:
            continue

        if trick == True and not 'trik' in match and not 'trick' in match:
            continue
        elif trick == False and ('trik' in match or 'trick' in match):
            continue

        bandwidth = 0
        match2 = re.search(bandwidth_regex, match)

        if match2:
            bandwidth = match2.group(1)

        results[bandwidth] = match

    if len(results) == 0:
        result = re.findall(r'<[rR]epresentation(?:(?!<[rR]epresentation)(?!/>)[\S\s])+/>', xml)

        for match in result:
            if not 'bandwidth' in match or not 'codecs' in match or not 'width' in match or not 'height' in match:
                continue

            if trick == True and not 'trik' in match and not 'trick' in match:
                continue
            elif trick == False and ('trik' in match or 'trick' in match):
                continue

            bandwidth = 0
            match2 = re.search(bandwidth_regex, match)

            if match2:
                bandwidth = match2.group(1)

            results[bandwidth] = match

    if len(results) > 1:
        results.pop(max(results, key=int))

    for bandwidth in results:
        xml = xml.replace(results[bandwidth], "")

    return xml

def load_file(file, isJSON=False):
    if not os.path.isfile(file):
        return None

    with io.open(file, 'r', encoding='utf-8') as f:
        if isJSON == True:
            return json.load(f, object_pairs_hook=collections.OrderedDict)
        else:
            return f.read()

def proxy_get_match(path, addon_name):
    if addon_name == 'ziggo':
        if "manifest.mpd" in path or "Manifest" in path:
            return True
    else:
        if ".mpd" in path:
            return True

    return False

def proxy_get_session(proxy, addon_name):
    if addon_name == 'ziggo':
        HEADERS = CONST_BASE_HEADERS['ziggo']

        for header in proxy.headers:
            if proxy.headers[header] is not None and header in CONST_ALLOWED_HEADERS['ziggo']:
                HEADERS[header] = proxy.headers[header]

        return Session(addon_name=addon_name, headers=HEADERS)

    else:
        return Session(addon_name=addon_name, cookies_key='cookies', save_cookies=False)

def proxy_get_url(proxy, addon_name, ADDON_PROFILE):
    global stream_url

    if addon_name == 'ziggo':
        return stream_url[addon_name] + str(proxy.path).replace('WIDEVINETOKEN', load_file(file=ADDON_PROFILE + 'widevine_token', isJSON=False))
    else:
        return stream_url[addon_name] + str(proxy.path)

def proxy_xml_mod(xml, addon_name):
    #if addon_name == 'ziggo':
    #    if xbmcaddon.Addon(id="plugin.video." + addon_name).getSettingBool("disableac3") == True:
    #        xml = remove_ac3(xml=xml)

    return xml

def remove_ac3(xml):
    try:
        result = re.findall(r'<[aA]daptation[sS]et(?:(?!</[aA]daptation[sS]et>)[\S\s])+</[aA]daptation[sS]et>', xml)

        for match in result:
            if not 'contentType="audio"' in match:
                continue

            if 'codecs="ac-3"' in match:
                xml = xml.replace(match, "")
    except:
        pass

    return xml

def remove_subs(xml):
    try:
        results = {}

        result = re.findall(r'<[aA]daptationSet(?:(?!<[aA]daptationSet)(?!</[aA]daptationSet>)[\S\s])+', xml)

        for match in result:
            if 'contentType="text"' in match:
                xml = xml.replace(match + '</AdaptationSet>', "")
    except:
        pass

    return xml

def set_duration(xml, addon_name, ADDON_PROFILE):
    try:
        duration = load_file(file=ADDON_PROFILE + 'stream_duration', isJSON=False)

        #if 'type="dynamic"' in xml and not 'mediaPresentationDuration' in xml:
        #    xml = xml.replace('minimumUpdatePeriod', 'mediaPresentationDuration="PT4H0M0S" minimumUpdatePeriod')
        #elif duration and int(duration) > 0:
        if duration and int(duration) > 0:
            duration = int(duration)
            given_duration = 0
            matched = False

            duration += xbmcaddon.Addon(id="plugin.video." + addon_name).getSettingInt("add_duration")

            regex = r"mediaPresentationDuration=\"PT([0-9]*)M([0-9]*)[0-9.]*S\""
            matches2 = re.finditer(regex, xml, re.MULTILINE)

            if len([i for i in matches2]) > 0:
                matches = re.finditer(regex, xml, re.MULTILINE)
                matched = True
            else:
                regex2 = r"mediaPresentationDuration=\"PT([0-9]*)H([0-9]*)M([0-9]*)[0-9.]*S\""
                matches3 = re.finditer(regex2, xml, re.MULTILINE)

                if len([i for i in matches3]) > 0:
                    matches = re.finditer(regex2, xml, re.MULTILINE)
                    matched = True
                else:
                    regex3 = r"mediaPresentationDuration=\"PT([0-9]*)D([0-9]*)H([0-9]*)M([0-9]*)[0-9.]*S\""
                    matches4 = re.finditer(regex3, xml, re.MULTILINE)

                    if len([i for i in matches4]) > 0:
                        matches = re.finditer(regex3, xml, re.MULTILINE)
                        matched = True

            if matched == True:
                given_day = 0
                given_hour = 0
                given_minute = 0
                given_second = 0

                for matchNum, match in enumerate(matches, start=1):
                    if len(match.groups()) == 2:
                        given_minute = int(match.group(1))
                        given_second = int(match.group(2))
                    elif len(match.groups()) == 3:
                        given_hour = int(match.group(1))
                        given_minute = int(match.group(2))
                        given_second = int(match.group(3))
                    elif len(match.groups()) == 4:
                        given_day = int(match.group(1))
                        given_hour = int(match.group(2))
                        given_minute = int(match.group(3))
                        given_second = int(match.group(4))

                given_duration = (given_day * 24* 60 * 60) + (given_hour * 60 * 60) + (given_minute * 60) + given_second

            if not given_duration > 0 or given_duration > duration:
                minute, second = divmod(duration, 60)
                hour, minute = divmod(minute, 60)

                regex4 = r"mediaPresentationDuration=\"[a-zA-Z0-9.]*\""
                subst = "mediaPresentationDuration=\"PT{hour}H{minute}M{second}S\"".format(hour=hour, minute=minute, second=second)
                regex5 = r"duration=\"[a-zA-Z0-9.]*\">"
                subst2 = "duration=\"PT{hour}H{minute}M{second}S\">".format(hour=hour, minute=minute, second=second)

                xml = re.sub(regex4, subst, xml, 0, re.MULTILINE)
                xml = re.sub(regex5, subst2, xml, 0, re.MULTILINE)

    except:
        pass

    return xml

def write_file(file, data, isJSON=False):
    with io.open(file, 'w', encoding="utf-8") as f:
        if isJSON == True:
            f.write(json.dumps(data, ensure_ascii=False))
        else:
            f.write(data)

if __name__ == "__main__":
    main()