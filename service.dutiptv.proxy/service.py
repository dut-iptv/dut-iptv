import io, json, os, re, requests, sys, threading, time, xbmc, xbmcaddon

try:
    import http.server as ProxyServer
except ImportError:
    import BaseHTTPServer as ProxyServer

try:
    unicode
except NameError:
    unicode = str

if sys.version_info < (3, 0):
    PROXY_PROFILE = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf_8')
else:
    PROXY_PROFILE = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))

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

            if sys.version_info < (3, 0):
                ADDON_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf_8')
            else:
                ADDON_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))

            try:
                self._stream_url
            except:
                self._stream_url = {}
                self._stream_url[addon_name] = load_file(file=ADDON_PROFILE + 'stream_hostname', isJSON=False)

            try:
                self._last_playing
            except:
                self._last_playing = {}
                self._last_playing[addon_name] = 0

            if proxy_get_match(path=self.path, addon_name=addon_name):
                self._stream_url[addon_name] = load_file(file=ADDON_PROFILE + 'stream_hostname', isJSON=False)

                URL = proxy_get_url(proxy=self, addon_name=addon_name, ADDON_PROFILE=ADDON_PROFILE)

                session = proxy_get_session(proxy=self, addon_name=addon_name)
                r = session.get(URL)

                xml = r.text

                xml = set_duration(xml=xml, addon_name=addon_name, ADDON_PROFILE=ADDON_PROFILE)

                if ADDON.getSettingBool('disable_subtitle'):
                    xml = remove_subs(xml=xml)

                if ADDON.getSettingBool('force_highest_bandwidth'):
                    xml = force_highest_bandwidth(xml=xml)

                xml = proxy_xml_mod(xml=xml, addon_name=addon_name)

                self.send_response(r.status_code)

                r.headers['Content-Length'] = len(xml)

                for header in r.headers:
                    if not 'Content-Encoding' in header and not 'Transfer-Encoding' in header:
                        self.send_header(header, r.headers[header])

                self.end_headers()

                try:
                    xml = xml.encode('utf-8')
                except:
                    pass

                try:
                    self.wfile.write(xml)
                except:
                    pass
            else:
                URL = proxy_get_url(proxy=self, addon_name=addon_name, ADDON_PROFILE=ADDON_PROFILE)

                try:
                    self._now_playing
                except:
                    self._now_playing = {}

                self._now_playing[addon_name] = int(time.time())

                if self._last_playing[addon_name] + 60 < self._now_playing[addon_name]:
                    self._last_playing[addon_name] = int(time.time())
                    write_file(file=ADDON_PROFILE + 'stream_playing_time', data=self._last_playing[addon_name], isJSON=False)

                self.send_response(302)
                self.send_header('Location', URL)
                self.end_headers()

    def log_message(self, format, *args):
        return

class RemoteControlBrowserService(xbmcaddon.Addon):
    def __init__(self):
        super(RemoteControlBrowserService, self).__init__()
        self.pluginId = self.getAddonInfo('id')

        if sys.version_info < (3, 0):
            self.addonFolder = xbmc.translatePath(self.getAddonInfo('path')).decode('utf_8')
            self.profileFolder = xbmc.translatePath(self.getAddonInfo('profile')).decode('utf_8')
        else:
            self.addonFolder = xbmc.translatePath(self.getAddonInfo('path'))
            self.profileFolder = xbmc.translatePath(self.getAddonInfo('profile'))

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

        if sys.version_info < (3, 0):
            self._addon_profile = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf_8')
        else:
            self._addon_profile = xbmc.translatePath(ADDON.getAddonInfo('profile'))

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
    service = RemoteControlBrowserService()
    service.clearBrowserLock()
    monitor = HTTPMonitor(service)
    service.reloadHTTPServer()

    monitor.waitForAbort()

    service.shutdownHTTPServer()

def force_ac3(xml):
    try:
        found = False

        result = re.findall(r'<[aA]daptation[sS]et content[tT]ype=\"audio\"(?:(?!<[aA]daptation[sS]et)(?!</[aA]daptation[sS]et>)[\S\s])+</[aA]daptation[sS]et>', xml)

        for match in result:
            if 'codecs="ac-3"' in match:
                found = True

        if found:
            for match in result:
                if not 'codecs="ac-3"' in match:
                    xml = xml.replace(match, "")

    except:
        pass

    return xml

def force_highest_bandwidth(xml):
    try:
        results = {}

        result = re.findall(r'<[rR]epresentation(?:(?!<[rR]epresentation)(?!</[rR]epresentation>)[\S\s])+</[rR]epresentation>', xml)
        bandwidth_regex = r"bandwidth=\"([0-9]+)\""

        for match in result:
            if not 'id="video' in match and not 'id="Video' in match:
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

    except:
        pass

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
    if addon_name == 'ziggo':
        return proxy._stream_url[addon_name] + str(proxy.path).replace('WIDEVINETOKEN', load_file(file=ADDON_PROFILE + 'widevine_token', isJSON=False))
    else:
        return proxy._stream_url[addon_name] + str(proxy.path)

def proxy_xml_mod(xml, addon_name):
    if addon_name == 'tmobile':
        if xbmcaddon.Addon(id="plugin.video." + addon_name).getSettingBool("force_ac3") == True:
            xml = force_ac3(xml=xml)
    elif addon_name == 'ziggo':
        if xbmcaddon.Addon(id="plugin.video." + addon_name).getSettingBool("disableac3") == True:
            xml = remove_ac3(xml=xml)

    return xml

def remove_ac3(xml):
    try:
        result = re.findall(r'<[aA]daptation[sS]et(?:(?!</[aA]daptation[sS]et>)[\S\s])+</[aA]daptation[sS]et>', xml)

        for match in result:
            if "codecs=\"ac-3\"" in match:
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

        if duration and duration > 0:
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
            f.write(unicode(json.dumps(data, ensure_ascii=False)))
        else:
            f.write(unicode(data))

if __name__ == "__main__":
    main()