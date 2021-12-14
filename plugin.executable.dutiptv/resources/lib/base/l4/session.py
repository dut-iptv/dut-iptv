import socket, requests

from resources.lib.base.l1.constants import DEFAULT_USER_AGENT, SESSION_CHUNKSIZE
from resources.lib.base.l2.log import log
from resources.lib.base.l3.util import load_file, write_file
from resources.lib.constants import CONST_BASE_DOMAIN, CONST_BASE_DOMAIN_MOD, CONST_BASE_HEADERS, CONST_BASE_IP

dns_cache = {}

def override_dns(domain, ip):
    dns_cache[domain] = ip

prv_getaddrinfo = socket.getaddrinfo

def new_getaddrinfo(*args):
    if args[0] in dns_cache:
        return prv_getaddrinfo(dns_cache[args[0]], *args[1:])
    else:
        return prv_getaddrinfo(*args)
        
socket.getaddrinfo = new_getaddrinfo

class Session(requests.Session):
    def __init__(self, headers=None, cookies_key=None, save_cookies=True, base_url='{}', timeout=None, attempts=None):
        super(Session, self).__init__()

        base_headers = CONST_BASE_HEADERS
        base_headers.update({'User-Agent': DEFAULT_USER_AGENT})

        if headers:
            base_headers.update(headers)

        self._headers = base_headers or {}
        self._cookies_key = cookies_key
        self._save_cookies = save_cookies
        self._base_url = base_url
        self._timeout = timeout or (5, 10)
        self._attempts = attempts or 2

        self.headers.update(self._headers)

        if self._cookies_key:
            cookies = load_file(file='stream_cookies', isJSON=True)

            if not cookies:
                cookies = {}

            self.cookies.update(cookies)

    def request(self, method, url, timeout=None, attempts=None, **kwargs):
        if not url.startswith('http'):
            url = self._base_url.format(url)

        kwargs['timeout'] = timeout or self._timeout
        attempts = attempts or self._attempts

        rngattempts = list(range(1, attempts+1))

        for i in rngattempts:
            try:
                if CONST_BASE_DOMAIN_MOD:
                    override_dns(CONST_BASE_DOMAIN, CONST_BASE_IP)
                    
                data = super(Session, self).request(method, url, **kwargs)

                if self._cookies_key and self._save_cookies:
                    self.save_cookies()

                return data
            except:
                if i == attempts:
                    raise

    def save_cookies(self):
        write_file(file='stream_cookies', data=self.cookies.get_dict(), isJSON=True)

    def clear_cookies(self):
        self.cookies.clear()

    def chunked_dl(self, url, dst_path, method='GET'):
        resp = self.request(method, url, stream=True)
        resp.raise_for_status()

        with open(dst_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=SESSION_CHUNKSIZE):
                f.write(chunk)