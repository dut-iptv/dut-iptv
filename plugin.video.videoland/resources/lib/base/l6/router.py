import sys

from resources.lib.base.l1.constants import ADDON_ID
from resources.lib.base.l2.log import log
from resources.lib.base.l3.util import encode_obj
from resources.lib.base.l3.language import _
from resources.lib.base.l4.exceptions import RouterError
from resources.lib.base.l5 import signals
from urllib.parse import parse_qsl, unquote, urlencode

_routes = {}

# @router.add('_settings', settings)
def add(url, f):
    if url == None:
        url = f.__name__
    _routes[url] = f

# @router.route('_settings')
def route(url):
    def decorator(f):
        add(url, f)
        return f
    return decorator

# @router.parse_url('?_=_settings')
def parse_url(url):
    if url.startswith('?'):
        params = dict(parse_qsl(url.lstrip('?'), keep_blank_values=True))
        for key in params:
            params[key] = unquote(params[key])

        _url = params.pop('_', '')
    else:
        params = {}
        _url = url

    params['_url'] = url

    function = _routes.get(_url)

    if not function:
        raise RouterError(_(_.ROUTER_NO_FUNCTION, raw_url=url, parsed_url=_url))

    #log.debug('Router Parsed: \'{0}\' => {1} {2}'.format(url, function.__name__, params))

    return function, params

def url_for_func(func, **kwargs):
    for url in _routes:
        if _routes[url].__name__ == func.__name__:
            return build_url(url, **kwargs)

    raise RouterError(_(_.ROUTER_NO_URL, function_name=func.__name__))

def url_for(func_or_url, **kwargs):
    if callable(func_or_url):
        return url_for_func(func_or_url, **kwargs)
    else:
        return build_url(func_or_url, **kwargs)

def build_url(url, addon_id=ADDON_ID, **kwargs):
    kwargs['_'] = url
    is_live = kwargs.pop('_is_live', False)

    params = []
    for k in sorted(kwargs):
        if kwargs[k] == None:
            continue

        try: params.append((k, str(kwargs[k]).encode('utf-8')))
        except: params.append((k, kwargs[k]))

    #if is_live:
    #    params.append(('_l', '.pvr'))

    return 'plugin://{0}/?{1}'.format(addon_id, urlencode(encode_obj(params)))

# router.dispatch('?_=_settings')
def dispatch(url):
    with signals.throwable():
        function, params = parse_url(url)
        signals.emit(signals.BEFORE_DISPATCH)

        function(**params)

    signals.emit(signals.AFTER_DISPATCH)