from resources.lib.base.l3.language import _
import ipaddress, socket

def parse_dns_string(reader, data):
    res = ''
    to_resue = None
    bytes_left = 0

    for ch in data:
        if not ch:
            break

        if to_resue is not None:
            resue_pos = chr(to_resue) + chr(ch)
            res += reader.reuse(resue_pos)
            break

        if bytes_left:
            res += chr(ch)
            bytes_left -= 1
            continue

        if (ch >> 6) == 0b11 and reader is not None:
            to_resue = ch - 0b11000000
        else:
            bytes_left = ch

        if res:
            res += '.'

    return res


class StreamReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def read(self, len_):
        pos = self.pos
        if pos >= len(self.data):
            raise

        res = self.data[pos: pos+len_]
        self.pos += len_
        return res

    def reuse(self, pos):
        pos = int.from_bytes(pos.encode(), 'big')
        return parse_dns_string(None, self.data[pos:])


def make_dns_query_domain(domain):
    def f(s):
        return chr(len(s)) + s

    parts = domain.split('.')
    parts = list(map(f, parts))
    return ''.join(parts).encode()


def make_dns_request_data(dns_query):
    req = b'\xaa\xbb\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00'
    req += dns_query
    req += b'\x00\x00\x01\x00\x01'
    return req


def add_record_to_result(result, type_, data, reader):
    if type_ == 'A':
        item = str(ipaddress.IPv4Address(data))
    else:
        return

    result.setdefault(type_, []).append(item)


def parse_dns_response(res, dq_len, req):
    reader = StreamReader(res)

    def get_query(s):
        return s[12:12+dq_len]

    data = reader.read(len(req))
    assert(get_query(data) == get_query(req))

    def to_int(bytes_):
        return int.from_bytes(bytes_, 'big')

    result = {}
    res_num = to_int(data[6:8])
    for i in range(res_num):
        reader.read(2)
        type_num = to_int(reader.read(2))

        type_ = None
        if type_num == 1:
            type_ = 'A'

        reader.read(6)
        data = reader.read(2)
        data = reader.read(to_int(data))
        add_record_to_result(result, type_, data, reader)

    return result


def dns_lookup(domain, address):
    dns_query = make_dns_query_domain(domain)
    dq_len = len(dns_query)

    req = make_dns_request_data(dns_query)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)

    try:
        sock.sendto(req, (address, 53))
        res, _ = sock.recvfrom(1024 * 4)
        result = parse_dns_response(res, dq_len, req)
    except Exception:
        return
    finally:
        sock.close()

    return result

CONST_BASE_DOMAIN = 'obo-prod.oesp.telenettv.be'
CONST_BASE_DOMAIN_MOD = True
CONST_BASE_IP = dns_lookup('obo-prod.oesp.telenettv.be', "1.0.0.1")['A'][0]

base = "https://obo-prod.oesp.telenettv.be/oesp/v4"
complete_base_url = '{base_url}/BE/nld'.format(base_url=base)

CONST_API_URLS = {
    'base_url': complete_base_url + '/web',
    'clearstreams_url': 'https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/playback/clearstreams',
    'devices_url': "https://prod.spark.telenettv.be/nld/web/personalization-service/v1/customer/",
    'devices_digital_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/devices",
    'search_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/search/content",
    'session_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/session",
    'channels_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/channels",
    'token_url': '{complete_base_url}/web/license/token'.format(complete_base_url=complete_base_url),
    'widevine_url': '{complete_base_url}/web/license/eme'.format(complete_base_url=complete_base_url),
    'listings_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/listings",
    'mediaitems_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/mediaitems",
    'mediagroupsfeeds_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/mediagroups/feeds",
    'watchlist_url': "https://obo-prod.oesp.telenettv.be/oesp/v4/BE/nld/web/watchlists/later",
    'login_url': 'https://login.prd.telenet.be/openid/login.do',
    'authorization_url': '{complete_base_url}/web/authorization'.format(complete_base_url=complete_base_url),
}

CONST_ALLOWED_HEADERS = {
    'user-agent',
    'x-oesp-content-locator',
    'x-oesp-token',
    'x-client-id',
    'x-oesp-username',
    'x-oesp-drm-schemeiduri'
}

CONST_BASE_URL = 'https://www.telenettv.be'

CONST_BASE_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': CONST_BASE_URL,
    'Pragma': 'no-cache',
    'Referer': CONST_BASE_URL + '/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
}

CONST_CONTINUE_WATCH = False

CONST_DEFAULT_CLIENTID = '4.29.11'

CONST_FIRST_BOOT = True

CONST_HAS_LIVE = True

CONST_HAS_REPLAY = True

CONST_HAS_SEARCH = True

CONST_MOD_CACHE = {}

CONST_ONLINE_SEARCH = False

CONST_START_FROM_BEGINNING = True

CONST_USE_PROXY = True

CONST_USE_PROFILES = False

CONST_VOD_CAPABILITY = [
    { 'file': 'series', 'label': _.SERIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'alacarte', 'label': _.ALACARTE, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'kidsseries', 'label': _.KIDS_SERIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
    { 'file': 'kidsmovies', 'label': _.KIDS_MOVIES, 'start': 0, 'menu': 0, 'online': 0, 'search': 1, 'az': 2 },
]

CONST_WATCHLIST = False