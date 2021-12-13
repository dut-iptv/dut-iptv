import glob, hashlib, io, json, os, platform, pytz, re, requests, shutil, string, struct, time, unicodedata, xbmc, xbmcaddon, xbmcvfs

from collections import OrderedDict
from resources.lib.base.l1.constants import ADDON_ID, ADDON_PATH, ADDON_PROFILE, CONST_DUT_EPG_SETTINGS, PROVIDER_NAME, USERDATA_PATH
from resources.lib.base.l1.encrypt import Credentials
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from xml.dom.minidom import parse

def add_library_sources():
    movies_path = os.path.join(ADDON_ID, 'movies')
    shows_path = os.path.join(ADDON_ID, 'shows')

    dom1 = parse(os.path.join(USERDATA_PATH, 'sources.xml'))

    root = dom1.getElementsByTagName("video")[0]
    sources = root.getElementsByTagName("source")

    movies_found = False
    shows_found = False

    for source in sources:
        path = source.getElementsByTagName("path")[0].firstChild.nodeValue

        if movies_path in path:
            movies_found = True

        if shows_path in path:
            shows_found = True

    if movies_found == False:
        tempChild = dom1.createElement('source')

        tempChild2 = dom1.createElement('name')
        nodeText = dom1.createTextNode('{} Movies'.format(PROVIDER_NAME).title())
        tempChild2.appendChild(nodeText)
        tempChild.appendChild(tempChild2)

        tempChild3 = dom1.createElement('path')
        tempChild3.setAttribute("pathversion", '1')
        nodeText2 = dom1.createTextNode(os.path.join(ADDON_PROFILE, 'movies', ''))
        tempChild3.appendChild(nodeText2)
        tempChild.appendChild(tempChild3)

        tempChild4 = dom1.createElement('allowsharing')
        nodeText3 = dom1.createTextNode('true')
        tempChild4.appendChild(nodeText3)
        tempChild.appendChild(tempChild4)

        root.appendChild(tempChild)

    if shows_found == False:
        tempChild5 = dom1.createElement('source')

        tempChild6 = dom1.createElement('name')
        nodeText5 = dom1.createTextNode('{} Shows'.format(PROVIDER_NAME).title())
        tempChild6.appendChild(nodeText5)
        tempChild5.appendChild(tempChild6)

        tempChild7 = dom1.createElement('path')
        tempChild7.setAttribute("pathversion", '1')
        nodeText6 = dom1.createTextNode(os.path.join(ADDON_PROFILE, 'shows', ''))
        tempChild7.appendChild(nodeText6)
        tempChild5.appendChild(tempChild7)

        tempChild8 = dom1.createElement('allowsharing')
        nodeText7 = dom1.createTextNode('true')
        tempChild8.appendChild(nodeText7)
        tempChild5.appendChild(tempChild8)

        root.appendChild(tempChild5)

    if movies_found == False or shows_found == False:
        write_file(os.path.join(USERDATA_PATH, 'sources.xml'), data=dom1.toprettyxml(), ext=True, isJSON=False)

    from sqlite3 import dbapi2 as sqlite

    for file in glob.glob(os.path.join(xbmcvfs.translatePath("special://database"), "*MyVideos*.db")):
        db = sqlite.connect(file)

        query = "UPDATE path SET strContent='movies', strScraper='metadata.local', scanRecursive=0, useFolderNames=0, strSettings='', noUpdate=0, exclude=0, dateAdded=NULL, idParentPath=NULL, allAudio=0 WHERE strPath='{}';".format(os.path.join(ADDON_PROFILE, 'movies', ''))

        try:
            rows = db.execute(query)

            if rows.rowcount == 0:
                query = "INSERT INTO path (strPath, strContent, strScraper, scanRecursive, useFolderNames, strSettings, noUpdate, exclude, dateAdded, idParentPath, allAudio) VALUES ('{}', 'movies', 'metadata.local', 0, 0, '', 0, 0, NULL, NULL, 0)".format(os.path.join(ADDON_PROFILE, 'movies', ''))
                db.execute(query)
        except:
            pass

        query = "UPDATE path SET strContent='tvshows', strScraper='metadata.local', scanRecursive=0, useFolderNames=0, strSettings='', noUpdate=0, exclude=0, dateAdded=NULL, idParentPath=NULL, allAudio=0 WHERE strPath='{}';".format(os.path.join(ADDON_PROFILE, 'shows', ''))

        try:
            rows = db.execute(query)

            if rows.rowcount == 0:
                query = "INSERT INTO path (strPath, strContent, strScraper, scanRecursive, useFolderNames, strSettings, noUpdate, exclude, dateAdded, idParentPath, allAudio) VALUES ('{}', 'shows', 'metadata.local', 0, 0, '', 0, 0, NULL, NULL, 0)".format(os.path.join(ADDON_PROFILE, 'shows', ''))
                db.execute(query)
        except:
            pass

        db.commit()
        db.close()

def change_icon():
    addon_icon = os.path.join(ADDON_PATH, "icon.png")
    settings_file = os.path.join(ADDON_PROFILE, 'settings.json')

    if is_file_older_than_x_days(file=settings_file, days=14):
        r = requests.get(CONST_DUT_EPG_SETTINGS, stream=True)

        if r.status_code == 200:
            try:
                with open(settings_file, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)

                r.close()
            except:
                r.close()
        else:
            r.close()

    settingsJSON = load_file(file='settings.json', isJSON=True)

    if not settingsJSON or not check_key(settingsJSON, 'icon') or not check_key(settingsJSON['icon'], 'md5') or not check_key(settingsJSON['icon'], 'url'):
        return

    if not md5sum(addon_icon) or settingsJSON['icon']['md5'] != md5sum(addon_icon):
        r = requests.get(settingsJSON['icon']['url'], stream=True)

        if r.status_code == 200:
            try:
                with open(addon_icon, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)

                r.close()
            except:
                r.close()
        else:
            r.close()

    from sqlite3 import dbapi2 as sqlite

    for file in glob.glob(xbmcvfs.translatePath("special://database") + os.sep + "*Textures*.db"):
        db = sqlite.connect(file)
        query = "SELECT cachedurl FROM texture WHERE url LIKE '%addons%" + ADDON_ID + "%icon.png';"

        rows = db.execute(query)

        for row in rows:
            thumb = os.path.join(xbmcvfs.translatePath("special://thumbnails"), str(row[0]))

            if os.path.isfile(thumb):
                try:
                    os.remove(thumb)
                except:
                    pass

        query = "DELETE FROM texture WHERE url LIKE '%addons%{addon}%icon.png';".format(addon=ADDON_ID)

        db.execute(query)
        db.commit()
        db.close()

def check_addon(addon):
    if xbmc.getCondVisibility('System.HasAddon({addon})'.format(addon=addon)) == 1:
        try:
            VIDEO_ADDON = xbmcaddon.Addon(id=addon)

            return True
        except:
            return False

    return False

def check_key(object, key):
    if key in object and object[key] and len(str(object[key])) > 0:
        return True
    else:
        return False

def check_loggedin(addon):
    VIDEO_ADDON_PROFILE = ADDON_PROFILE.replace(ADDON_ID, addon)

    profile = load_file(os.path.join(VIDEO_ADDON_PROFILE, 'profile.json'), ext=True, isJSON=True)

    if not profile:
        return False
    else:
        try:
            if len(str(profile['pswd'])) > 0 and int(profile['last_login_success']) == 1:
                return True
            else:
                return False
        except:
            return False

def clear_cache():
    if not os.path.isdir(os.path.join(ADDON_PROFILE, "cache")):
        os.makedirs(os.path.join(ADDON_PROFILE, "cache"))

    for file in glob.glob(os.path.join(ADDON_PROFILE, "cache", "*.json")):
        if is_file_older_than_x_days(file=file, days=1):
            os.remove(file)

    if not os.path.isdir(os.path.join(ADDON_PROFILE, "tmp")):
        os.makedirs(os.path.join(ADDON_PROFILE, "tmp"))

    for file in glob.glob(os.path.join(ADDON_PROFILE, "tmp", "*.zip")):
        if is_file_older_than_x_days(file=file, days=1):
            os.remove(file)

def clear_old():
    if os.path.isfile(os.path.join(ADDON_PROFILE, 'settings.db')):
        shutil.rmtree(ADDON_PROFILE)

        if not os.path.isdir(os.path.join(ADDON_PROFILE, "tmp")):
            os.makedirs(os.path.join(ADDON_PROFILE, "tmp"))

        if not os.path.isdir(os.path.join(ADDON_PROFILE, "cache")):
            os.makedirs(os.path.join(ADDON_PROFILE, "cache"))

def convert_datetime_timezone(dt, tz1, tz2):
    tz1 = pytz.timezone(tz1)
    tz2 = pytz.timezone(tz2)

    dt = tz1.localize(dt)
    dt = dt.astimezone(tz2)

    return dt

def date_to_nl_dag(curdate):
    dag = {
        "Mon": "Maandag",
        "Tue": "Dinsdag",
        "Wed": "Woensdag",
        "Thu": "Donderdag",
        "Fri": "Vrijdag",
        "Sat": "Zaterdag",
        "Sun": "Zondag"
    }

    return dag.get(curdate.strftime("%a"), "")

def date_to_nl_maand(curdate):
    maand = {
        "January": "januari",
        "February": "februari",
        "March": "maart",
        "April": "april",
        "May": "mei",
        "June": "juni",
        "July": "juli",
        "August": "augustus",
        "September": "september",
        "October": "oktober",
        "November": "november",
        "December": "december"
    }

    return maand.get(curdate.strftime("%B"), "")

def disable_prefs(type, channels):
    prefs = load_prefs(profile_id=1)

    if type and channels:
        for currow in channels:
            row = channels[currow]

            if (type == 'minimal' and int(row['minimal']) == 0) or (type == 'erotica' and int(row['erotica']) == 1) or (type == 'regional' and int(row['regional']) == 1) or (type == 'home_only' and int(row['home_only']) == 1):
                mod_pref = {
                    'live': 0,
                    'replay': 0,
                }

                prefs[str(currow)] = mod_pref

    save_prefs(profile_id=1, prefs=prefs)

def fixBadZipfile(zipFile):
    f = open(zipFile, 'r+b')
    data = f.read()

    try:
        pos = data.find(b'\x50\x4b\x05\x06')
    except:
        pos = data.find('\x50\x4b\x05\x06')

    if (pos > 0):
        f.seek(pos + 22)
        f.truncate()
        f.close()

def get_credentials():
    profile_settings = load_profile(profile_id=1)

    if not profile_settings or not check_key(profile_settings, 'username'):
        username = ''
    else:
        username = profile_settings['username']

    if not profile_settings or not check_key(profile_settings, 'pswd'):
        password = ''
    else:
        password = profile_settings['pswd']

    if len(str(username)) < 50 and len(str(password)) < 50:
        set_credentials(username, password)

        return {'username' : username, 'password' : password }

    return Credentials().decode_credentials(username, password)

def get_kodi_version():
    try:
        return int(xbmc.getInfoLabel("System.BuildVersion").split('.')[0])
    except:
        return 0

def get_system_arch():
    if xbmc.getCondVisibility('System.Platform.UWP') or '4n2hpmxwrvr6p' in xbmcvfs.translatePath('special://xbmc/'):
        system = 'UWP'
    elif xbmc.getCondVisibility('System.Platform.Android'):
        system = 'Android'
    elif xbmc.getCondVisibility('System.Platform.IOS'):
        system = 'IOS'
    else:
        system = platform.system()

    if system == 'Windows':
        arch = platform.architecture()[0]
    else:
        try:
            arch = platform.machine()
        except:
            arch = ''

    #64bit kernel with 32bit userland
    if ('aarch64' in arch or 'arm64' in arch) and (struct.calcsize("P") * 8) == 32:
        arch = 'armv7'
    elif 'arm' in arch:
        if 'v6' in arch:
            arch = 'armv6'
        else:
            arch = 'armv7'
    elif arch == 'i686':
        arch = 'i386'

    return system, arch

def is_file_older_than_x_days(file, days=1):
    if not os.path.isfile(file):
        return True

    totaltime = int(time.time()) - int(os.path.getmtime(file))
    totalhours = float(totaltime) / float(3600)

    if totalhours > 24 * days:
        return True
    else:
        return False

def is_file_older_than_x_minutes(file, minutes=1):
    if not os.path.isfile(file):
        return True

    totaltime = int(time.time()) - int(os.path.getmtime(file))
    totalminutes = float(totaltime) / float(60)

    if totalminutes > minutes:
        return True
    else:
        return False

def json_rpc(method, params=None):
    request_data = {'jsonrpc': '2.0', 'method': method, 'id': 1,
                    'params': params or {}}
    request = json.dumps(request_data)
    raw_response = xbmc.executeJSONRPC(request)
    response = json.loads(raw_response)

    return response['result']

def load_channels(type):
    return load_file(file=os.path.join('cache', type[0], '.channels.json'), ext=False, isJSON=True)

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
            full_path = os.path.join(ADDON_PROFILE, file)

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

def set_credentials(username, password):
    profile_settings = load_profile(profile_id=1)

    encoded = Credentials().encode_credentials(username, password)

    try:
        username = encoded['username'].decode('utf-8')
    except:
        username = encoded['username']

    try:
        pswd = encoded['password'].decode('utf-8')
    except:
        pswd = encoded['password']

    profile_settings['pswd'] = pswd
    profile_settings['username'] = username

    save_profile(profile_id=1, profile=profile_settings)

def txt2filename(txt, chr_set='printable', no_ext=False):
    """Converts txt to a valid filename.

    Args:
        txt: The str to convert.
        chr_set:
            'printable':    Any printable character except those disallowed on Windows/*nix.
            'extended':     'printable' + extended ASCII character codes 128-255
            'universal':    For almost *any* file system. '-.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    """

    try:
        text = unicode(txt, 'utf-8')
    except (TypeError, NameError):
        text = txt

    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    txt = str(text)

    if no_ext == False:
        ext = '' if '.' not in txt else txt[txt.rfind('.'):]
    else:
        ext = ''

    FILLER = '-'
    MAX_LEN = 255  # Maximum length of filename is 255 bytes in Windows and some *nix flavors.

    # Step 1: Remove excluded characters.
    BLACK_LIST = set(chr(127) + r'<>:"/\|?*')                           # 127 is unprintable, the rest are illegal in Windows.
    white_lists = {
        'universal': {'-.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'},
        'printable': {chr(x) for x in range(32, 127)} - BLACK_LIST,     # 0-32, 127 are unprintable,
        'extended' : {chr(x) for x in range(32, 256)} - BLACK_LIST,
    }
    white_list = white_lists[chr_set]
    result = ''.join(x
                     if x in white_list else FILLER
                     for x in txt)

    # Step 2: Device names, '.', and '..' are invalid filenames in Windows.
    DEVICE_NAMES = 'CON,PRN,AUX,NUL,COM1,COM2,COM3,COM4,' \
                   'COM5,COM6,COM7,COM8,COM9,LPT1,LPT2,' \
                   'LPT3,LPT4,LPT5,LPT6,LPT7,LPT8,LPT9,' \
                   'CONIN$,CONOUT$,..,.'.split()  # This list is an O(n) operation.
    if result in DEVICE_NAMES:
        result = f'-{result}-'

    # Step 3: Truncate long files while preserving the file extension.
    result = result[:MAX_LEN - len(ext)] + ext

    # Step 4: Windows does not allow filenames to end with '.' or ' ' or begin with ' '.
    result = re.sub(r'^[. ]', FILLER, result)
    result = re.sub(r' $', FILLER, result)

    return result

def update_prefs(profile_id=1, channels=None):
    prefs = load_prefs(profile_id=1)

    if prefs:
        prefs2 = prefs.copy()

        for pref in prefs2:
            if not pref in channels:
                prefs.pop(pref)

    if channels:
        for currow in channels:
            row = channels[currow]

            if not prefs or not check_key(prefs, str(currow)):
                if (settings.getBool(key='minimalChannels') == True and int(row['minimal']) == 0) or (settings.getBool(key='disableErotica') == True and int(row['erotica']) == 1) or (settings.getBool(key='disableRegionalChannels') == True and int(row['regional']) == 1) or (PROVIDER_NAME == 'kpn' and settings.getBool(key='homeConnection') == False and int(row['home_only']) == 1):
                    mod_pref = {
                        'live': 0,
                        'replay': 0,
                    }
                else:
                    if int(row['replay']) == 0:
                        mod_pref = {
                            'live': 1,
                            'replay': 0,
                        }
                    else:
                        mod_pref = {
                            'live': 1,
                            'replay': 1,
                        }

                prefs[str(currow)] = mod_pref

    save_prefs(profile_id=1, prefs=prefs)

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
        full_path = os.path.join(ADDON_PROFILE, file)

    directory = os.path.dirname(full_path)

    if not os.path.exists(directory):
        os.makedirs(directory)

    with io.open(full_path, 'w', encoding="utf-8") as f:
        if isJSON == True:
            f.write(str(json.dumps(data, ensure_ascii=False)))
        else:
            f.write(str(data))