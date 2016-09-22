#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GAM
#
# Copyright 2015, LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
u"""GAM is a command line tool which allows Administrators to control their Google Apps domain and accounts.

With GAM you can programatically create users, turn on/off services for users like POP and Forwarding and much more.
For more information, see https://github.com/jay0lee/GAM
"""

__author__ = u'Ross Scroggs <ross.scroggs@gmail.com>'
__version__ = u'4.23.03'
__license__ = u'Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)'

import sys, os, time, datetime, random, socket, csv, platform, re, base64, string, codecs, StringIO, subprocess, ConfigParser, collections, logging, mimetypes

import json
import httplib2
import googleapiclient
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
import oauth2client.client
import oauth2client.service_account
from oauth2client.contrib.multiprocess_file_storage import MultiprocessFileStorage
import oauth2client.tools

# Override some oauth2client.tools strings saving us a few GAM-specific mods to oauth2client
oauth2client.tools._FAILED_START_MESSAGE = """
Failed to start a local webserver listening on either port 8080
or port 8090. Please check your firewall settings and locally
running programs that may be blocking or using those ports.

Falling back to nobrowser.txt  and continuing with
authorization.
"""

oauth2client.tools._BROWSER_OPENED_MESSAGE = """
Your browser has been opened to visit:

    {address}

If your browser is on a different machine then press CTRL+C and
create a file called nobrowser.txt in the same folder as GAM.
"""

oauth2client.tools._GO_TO_LINK_MESSAGE = """
Go to the following link in your browser:

    {address}
"""

GAM = u'GAMADV-X'
GAM_URL = u'https://github.com/taers232c/{0}'.format(GAM)
GAM_INFO = u'GAM {0} - {1} / {2} / Python {3}.{4}.{5} {6} / {7} {8} /'.format(__version__, GAM_URL,
                                                                              __author__,
                                                                              sys.version_info[0], sys.version_info[1], sys.version_info[2],
                                                                              sys.version_info[3],
                                                                              platform.platform(), platform.machine())
GAM_RELEASES = u'https://github.com/taers232c/{0}/releases'.format(GAM)
GAM_WIKI = u'https://github.com/jay0lee/GAM/wiki'
GAM_WIKI_CREATE_CLIENT_SECRETS = GAM_WIKI+u'/CreatingClientSecretsFile'
GAM_APPSPOT = u'https://gamadvx-update.appspot.com'
GAM_APPSPOT_LATEST_VERSION = GAM_APPSPOT+u'/latest-version.txt?v='+__version__
GAM_APPSPOT_LATEST_VERSION_ANNOUNCEMENT = GAM_APPSPOT+u'/latest-version-announcement.txt?v='+__version__

TRUE = u'true'
FALSE = u'false'
TRUE_VALUES = [TRUE, u'on', u'yes', u'enabled', u'1']
FALSE_VALUES = [FALSE, u'off', u'no', u'disabled', u'0']
TRUE_FALSE = [TRUE, FALSE]
ERROR = u'ERROR'
ERROR_PREFIX = ERROR+u': '
WARNING = u'WARNING'
WARNING_PREFIX = WARNING+u': '
NEVER = u'Never'
DEFAULT_CHARSET = [u'mbcs', u'utf-8'][os.name != u'nt']
ONE_KILO_BYTES = 1000
ONE_MEGA_BYTES = 1000000
ONE_GIGA_BYTES = 1000000000
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
FN_GAM_CFG = u'gam.cfg'
FN_CLIENT_SECRETS_JSON = u'client_secrets.json'
FN_EXTRA_ARGS_TXT = u'extra-args.txt'
FN_LAST_UPDATE_CHECK_TXT = u'lastupdatecheck.txt'
FN_OAUTH2SERVICE_JSON = u'oauth2service.json'
FN_OAUTH2_TXT = u'oauth2.txt'
MY_CUSTOMER = u'my_customer'

# Global variables

# CL_argv is a copy of sys.argv
# CL_argvI is an index into CL_argv
# CL_argvLen is len(CL_arvgv)
CL_argv = []
CL_argvI = 0
CL_argvLen = 0
# The following GM_XXX constants are arbitrary but must be unique
# Most errors print a message and bail out with a return code
# Some commands want to set a non-zero return code but not bail
GM_SYSEXITRC = u'sxrc'
# Path to gam
GM_GAM_PATH = u'gpth'
# Are we on Windows?
GM_WINDOWS = u'wndo'
# Encodings
GM_SYS_ENCODING = u'syen'
# Shared by batch_worker and run_batch
GM_BATCH_QUEUE = u'batq'
# Extra arguments to pass to GAPI functions
GM_EXTRA_ARGS_LIST = u'exad'
# GAM admin user
GM_ADMIN = u'admin'
# Current API user
GM_CURRENT_API_USER = u'capu'
# Current API scope
GM_CURRENT_API_SCOPES = u'scoc'
# Values retrieved from oauth2service.json
GM_OAUTH2SERVICE_JSON_DATA = u'oajd'
GM_OAUTH2_CLIENT_ID = u'oaci'
# gam.cfg parser
GM_PARSER = u'pars'
# gam.cfg file
GM_GAM_CFG_PATH = u'gcpa'
GM_GAM_CFG_FILE = u'gcfi'
# Where will CSV files be written, encoding, mode
GM_CSVFILE = u'csfi'
GM_CSVFILE_ENCODING = u'csen'
GM_CSVFILE_MODE = u'csmo'
GM_CSVFILE_WRITE_HEADER = u'cswh'
# File containing time of last GAM update check
GM_LAST_UPDATE_CHECK_TXT = u'lupc'
# Index of <UserTypeEntity> in command line
GM_ENTITY_CL_INDEX = u'enin'
# csvfile keyfield <FieldName> [delimiter <String>] (matchfield <FieldName> <MatchPattern>)* [datafield <FieldName>(:<FieldName>*) [delimiter <String>]]
# { key: [datafieldvalues]}
GM_CSV_DATA_DICT = u'csdd'
GM_CSV_KEY_FIELD = u'cskf'
GM_CSV_DATA_FIELD = u'csdf'
# printGetting... globals, set so that callGAPIpages has access to them for status messages
GM_GETTING_ENTITY_ITEM = u'gtei'
GM_GETTING_FOR_WHOM = u'gtfw'
GM_GETTING_SHOW_TOTAL = u'gtst'
# Control indented printing
GM_INDENT_LEVEL = u'inlv'
GM_INDENT_SPACES = u'insp'
INDENT_SPACES_PER_LEVEL = u'  '
# Current action
GM_ACTION_COMMAND = u'acmd'
GM_ACTION_TO_PERFORM = u'atpf'
GM_ACTION_PERFORMED = u'aper'
GM_ACTION_FAILED = u'afai'
GM_ACTION_NOT_PERFORMED = u'anpf'
# Dictionary mapping OrgUnit ID to Name
GM_MAP_ORGUNIT_ID_TO_NAME = u'oi2n'
# Dictionary mapping Role ID to Name
GM_MAP_ROLE_ID_TO_NAME = u'ri2n'
# Dictionary mapping Role Name to ID
GM_MAP_ROLE_NAME_TO_ID = u'rn2i'
# Dictionary mapping User ID to Name
GM_MAP_USER_ID_TO_NAME = u'ui2n'
# oauth2.txt.lock lockfile
GM_OAUTH2_TXT_LOCK = 'oalk'
# GAM cache directory. If no_cache is True, this variable will be set to None
GM_CACHE_DIR = u'gacd'
# Reset GAM cache directory after discovery
GM_CACHE_DISCOVERY_ONLY = u'gcdo'
#
GM_Globals = {
  GM_SYSEXITRC: 0,
  GM_GAM_PATH: os.path.dirname(os.path.realpath(__file__)) if not getattr(sys, u'frozen', False) else os.path.dirname(sys.executable),
  GM_WINDOWS: os.name == u'nt',
  GM_SYS_ENCODING: DEFAULT_CHARSET,
  GM_BATCH_QUEUE: None,
  GM_EXTRA_ARGS_LIST:  [(u'prettyPrint', False)],
  GM_ADMIN: None,
  GM_CURRENT_API_USER: None,
  GM_CURRENT_API_SCOPES: [],
  GM_OAUTH2SERVICE_JSON_DATA: None,
  GM_OAUTH2_CLIENT_ID: None,
  GM_LAST_UPDATE_CHECK_TXT: u'',
  GM_PARSER: None,
  GM_GAM_CFG_PATH: u'',
  GM_GAM_CFG_FILE: u'',
  GM_CSVFILE: None,
  GM_CSVFILE_ENCODING: DEFAULT_CHARSET,
  GM_CSVFILE_MODE: u'w',
  GM_CSVFILE_WRITE_HEADER: True,
  GM_CSV_DATA_DICT: {},
  GM_CSV_KEY_FIELD: None,
  GM_CSV_DATA_FIELD: None,
  GM_ENTITY_CL_INDEX: 1,
  GM_GETTING_ENTITY_ITEM: u'',
  GM_GETTING_FOR_WHOM: u'',
  GM_GETTING_SHOW_TOTAL: True,
  GM_INDENT_LEVEL: 0,
  GM_INDENT_SPACES: u'',
  GM_ACTION_COMMAND: u'',
  GM_ACTION_TO_PERFORM: u'',
  GM_ACTION_PERFORMED: u'',
  GM_ACTION_FAILED: u'',
  GM_ACTION_NOT_PERFORMED: u'',
  GM_MAP_ORGUNIT_ID_TO_NAME: None,
  GM_MAP_ROLE_ID_TO_NAME: None,
  GM_MAP_ROLE_NAME_TO_ID: None,
  GM_MAP_USER_ID_TO_NAME: None,
  GM_OAUTH2_TXT_LOCK: None,
  GM_CACHE_DIR: None,
  GM_CACHE_DISCOVERY_ONLY: False,
  }

# Global variables defined in gam.cfg

# The following GC_XXX constants are the names of the items in gam.cfg
# When retrieving lists of Google Drive activities from API, how many should be retrieved in each chunk
GC_ACTIVITY_MAX_RESULTS = u'activity_max_results'
# Automatically generate gam batch command if number of users specified in gam users xxx command exceeds this number
# Default: 0, don't automatically generate gam batch commands
GC_AUTO_BATCH_MIN = u'auto_batch_min'
# When processing items in batches, how many should be processed in each batch
GC_BATCH_SIZE = u'batch_size'
# GAM cache directory
GC_CACHE_DIR = u'cache_dir'
# GAM cache discovery only. If no_cache is False, only API discovery calls will be cached
GC_CACHE_DISCOVERY_ONLY = u'cache_discovery_only'
# Character set of batch, csv, data files
GC_CHARSET = u'charset'
# Path to client_secrets.json
GC_CLIENT_SECRETS_JSON = u'client_secrets_json'
# GAM config directory containing client_secrets.json, oauth2.txt, oauth2service.json, extra_args.txt
GC_CONFIG_DIR = u'config_dir'
# When retrieving lists of Google Contacts from API, how many should be retrieved in each chunk
GC_CONTACT_MAX_RESULTS = u'contact_max_results'
# custmerId from gam.cfg or retrieved from Google
GC_CUSTOMER_ID = u'customer_id'
# If debug_level > 0: extra_args[u'prettyPrint'] = True, httplib2.debuglevel = gam_debug_level, appsObj.debug = True
GC_DEBUG_LEVEL = u'debug_level'
# When retrieving lists of ChromeOS/Mobile devices from API, how many should be retrieved in each chunk
GC_DEVICE_MAX_RESULTS = u'device_max_results'
# Domain obtained from gam.cfg or oauth2.txt
GC_DOMAIN = u'domain'
# Google Drive download directory
GC_DRIVE_DIR = u'drive_dir'
# When retrieving lists of Drive files/folders from API, how many should be retrieved in each chunk
GC_DRIVE_MAX_RESULTS = u'drive_max_results'
# When processing email messages in batches, how many should be processed in each batch
GC_EMAIL_BATCH_SIZE = u'email_batch_size'
# Path to extra_args.txt
GC_EXTRA_ARGS = u'extra_args'
# If no_browser is False, writeCSVfile won't open a browser when todrive is set
# and doOAuthRequest prints a link and waits for the verification code when oauth2.txt is being created
GC_NO_BROWSER = u'no_browser'
# Disable GAM API caching
GC_NO_CACHE = u'no_cache'
# Disable GAM update check
GC_NO_UPDATE_CHECK = u'no_update_check'
# Disable SSL certificate validation
GC_NO_VERIFY_SSL = u'no_verify_ssl'
# Number of threads for gam batch
GC_NUM_THREADS = u'num_threads'
# Path to oauth2.txt
GC_OAUTH2_TXT = u'oauth2_txt'
# Path to oauth2service.json
GC_OAUTH2SERVICE_JSON = u'oauth2service_json'
# Default section to use for processing
GC_SECTION = u'section'
# Add (n/m) to end of messages if number of items to be processed exceeds this number
GC_SHOW_COUNTS_MIN = u'show_counts_min'
# Enable/disable "Getting ... " messages
GC_SHOW_GETTINGS = u'show_gettings'
# When retrieving lists of Users from API, how many should be retrieved in each chunk
GC_USER_MAX_RESULTS = u'user_max_results'

GC_Defaults = {
  GC_ACTIVITY_MAX_RESULTS: 100,
  GC_AUTO_BATCH_MIN: 0,
  GC_BATCH_SIZE: 50,
  GC_CACHE_DIR: u'',
  GC_CACHE_DISCOVERY_ONLY: FALSE,
  GC_CHARSET: DEFAULT_CHARSET,
  GC_CLIENT_SECRETS_JSON: FN_CLIENT_SECRETS_JSON,
  GC_CONFIG_DIR: u'',
  GC_CONTACT_MAX_RESULTS: 100,
  GC_CUSTOMER_ID: MY_CUSTOMER,
  GC_DEBUG_LEVEL: 0,
  GC_DEVICE_MAX_RESULTS: 500,
  GC_DOMAIN: u'',
  GC_DRIVE_DIR: u'',
  GC_DRIVE_MAX_RESULTS: 1000,
  GC_EMAIL_BATCH_SIZE: 100,
  GC_EXTRA_ARGS: u'',
  GC_NO_BROWSER: FALSE,
  GC_NO_CACHE: FALSE,
  GC_NO_UPDATE_CHECK: FALSE,
  GC_NO_VERIFY_SSL: FALSE,
  GC_NUM_THREADS: 5,
  GC_OAUTH2_TXT: FN_OAUTH2_TXT,
  GC_OAUTH2SERVICE_JSON: FN_OAUTH2SERVICE_JSON,
  GC_SECTION: u'',
  GC_SHOW_COUNTS_MIN: 1,
  GC_SHOW_GETTINGS: TRUE,
  GC_USER_MAX_RESULTS: 500,
  }

GC_Values = {GC_DEBUG_LEVEL: 0}

GC_TYPE_BOOLEAN = u'bool'
GC_TYPE_CHOICE = u'choi'
GC_TYPE_DATETIME = u'datm'
GC_TYPE_DIRECTORY = u'dire'
GC_TYPE_EMAIL = u'emai'
GC_TYPE_FILE = u'file'
GC_TYPE_INTEGER = u'inte'
GC_TYPE_LANGUAGE = u'lang'
GC_TYPE_STRING = u'stri'

GC_VAR_TYPE = u'type'
GC_VAR_ENVVAR = u'enva'
GC_VAR_LIMITS = u'lmit'
GC_VAR_SFFT = u'sfft'

GC_VAR_INFO = {
  GC_ACTIVITY_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_ENVVAR: u'GAM_ACTIVITY_MAX_RESULTS', GC_VAR_LIMITS: (1, 500)},
  GC_AUTO_BATCH_MIN: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_ENVVAR: u'GAM_AUTOBATCH', GC_VAR_LIMITS: (0, None)},
  GC_BATCH_SIZE: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_ENVVAR: u'GAM_BATCH_SIZE', GC_VAR_LIMITS: (1, 1000)},
  GC_CACHE_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY, GC_VAR_ENVVAR: u'GAMCACHEDIR'},
  GC_CACHE_DISCOVERY_ONLY: {GC_VAR_TYPE: GC_TYPE_BOOLEAN, GC_VAR_ENVVAR: u'cachediscoveryonly.txt', GC_VAR_SFFT: (FALSE, TRUE)},
  GC_CHARSET: {GC_VAR_TYPE: GC_TYPE_STRING, GC_VAR_ENVVAR: u'GAM_CHARSET'},
  GC_CLIENT_SECRETS_JSON: {GC_VAR_TYPE: GC_TYPE_FILE, GC_VAR_ENVVAR: u'CLIENTSECRETSFILE'},
  GC_CONFIG_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY, GC_VAR_ENVVAR: u'GAMUSERCONFIGDIR'},
  GC_CONTACT_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_ENVVAR: u'GAM_CONTACT_MAX_RESULTS', GC_VAR_LIMITS: (1, 10000)},
  GC_CUSTOMER_ID: {GC_VAR_TYPE: GC_TYPE_STRING, GC_VAR_ENVVAR: u'CUSTOMER_ID'},
  GC_DEBUG_LEVEL: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_ENVVAR: u'debug.gam', GC_VAR_LIMITS: (0, None), GC_VAR_SFFT: (u'0', u'4')},
  GC_DEVICE_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_ENVVAR: u'GAM_DEVICE_MAX_RESULTS', GC_VAR_LIMITS: (1, 1000)},
  GC_DOMAIN: {GC_VAR_TYPE: GC_TYPE_STRING, GC_VAR_ENVVAR: u'GA_DOMAIN'},
  GC_DRIVE_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY, GC_VAR_ENVVAR: u'GAMDRIVEDIR'},
  GC_DRIVE_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_ENVVAR: u'GAM_DRIVE_MAX_RESULTS', GC_VAR_LIMITS: (1, 1000)},
  GC_EMAIL_BATCH_SIZE: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_ENVVAR: u'GAM_EMAIL_BATCH_SIZE', GC_VAR_LIMITS: (1, 100)},
  GC_EXTRA_ARGS: {GC_VAR_TYPE: GC_TYPE_FILE, GC_VAR_ENVVAR: FN_EXTRA_ARGS_TXT, GC_VAR_SFFT: (u'', FN_EXTRA_ARGS_TXT)},
  GC_NO_BROWSER: {GC_VAR_TYPE: GC_TYPE_BOOLEAN, GC_VAR_ENVVAR: u'nobrowser.txt', GC_VAR_SFFT: (FALSE, TRUE)},
  GC_NO_CACHE: {GC_VAR_TYPE: GC_TYPE_BOOLEAN, GC_VAR_ENVVAR: u'nocache.txt', GC_VAR_SFFT: (FALSE, TRUE)},
  GC_NO_UPDATE_CHECK: {GC_VAR_TYPE: GC_TYPE_BOOLEAN, GC_VAR_ENVVAR: u'noupdatecheck.txt', GC_VAR_SFFT: (FALSE, TRUE)},
  GC_NO_VERIFY_SSL: {GC_VAR_TYPE: GC_TYPE_BOOLEAN, GC_VAR_ENVVAR: u'noverifyssl.txt', GC_VAR_SFFT: (FALSE, TRUE)},
  GC_NUM_THREADS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_ENVVAR: u'GAM_THREADS', GC_VAR_LIMITS: (1, None)},
  GC_OAUTH2_TXT: {GC_VAR_TYPE: GC_TYPE_FILE, GC_VAR_ENVVAR: u'OAUTHFILE'},
  GC_OAUTH2SERVICE_JSON: {GC_VAR_TYPE: GC_TYPE_FILE, GC_VAR_ENVVAR: u'OAUTHSERVICEFILE'},
  GC_SECTION: {GC_VAR_TYPE: GC_TYPE_STRING, GC_VAR_ENVVAR: u'GAM_SECTION'},
  GC_SHOW_COUNTS_MIN: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_ENVVAR: u'GAM_SHOW_COUNTS_MIN', GC_VAR_LIMITS: (0, None)},
  GC_SHOW_GETTINGS: {GC_VAR_TYPE: GC_TYPE_BOOLEAN, GC_VAR_ENVVAR: u'GAM_SHOW_GETTINGS'},
  GC_USER_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_ENVVAR: u'GAM_USER_MAX_RESULTS', GC_VAR_LIMITS: (1, 500)},
  }

GC_SETTABLE_VARS = [
  GC_ACTIVITY_MAX_RESULTS,
  GC_AUTO_BATCH_MIN,
  GC_BATCH_SIZE,
  GC_CACHE_DISCOVERY_ONLY,
  GC_CHARSET,
  GC_CONTACT_MAX_RESULTS,
  GC_DEBUG_LEVEL,
  GC_DEVICE_MAX_RESULTS,
  GC_DRIVE_MAX_RESULTS,
  GC_EMAIL_BATCH_SIZE,
  GC_NO_BROWSER,
  GC_NO_CACHE,
  GC_NO_UPDATE_CHECK,
  GC_NO_VERIFY_SSL,
  GC_NUM_THREADS,
  GC_SHOW_COUNTS_MIN,
  GC_SHOW_GETTINGS,
  GC_USER_MAX_RESULTS,
  ]

# Google API constants
APPLICATION_VND_GOOGLE_APPS = u'application/vnd.google-apps.'
MIMETYPE_GA_DOCUMENT = APPLICATION_VND_GOOGLE_APPS+u'document'
MIMETYPE_GA_DRAWING = APPLICATION_VND_GOOGLE_APPS+u'drawing'
MIMETYPE_GA_FOLDER = APPLICATION_VND_GOOGLE_APPS+u'folder'
MIMETYPE_GA_FORM = APPLICATION_VND_GOOGLE_APPS+u'form'
MIMETYPE_GA_FUSIONTABLE = APPLICATION_VND_GOOGLE_APPS+u'fusiontable'
MIMETYPE_GA_MAP = APPLICATION_VND_GOOGLE_APPS+u'map'
MIMETYPE_GA_PRESENTATION = APPLICATION_VND_GOOGLE_APPS+u'presentation'
MIMETYPE_GA_SCRIPT = APPLICATION_VND_GOOGLE_APPS+u'script'
MIMETYPE_GA_SITES = APPLICATION_VND_GOOGLE_APPS+u'sites'
MIMETYPE_GA_SPREADSHEET = APPLICATION_VND_GOOGLE_APPS+u'spreadsheet'

GOOGLE_NAMESERVERS = [u'8.8.8.8', u'8.8.4.4']
NEVER_TIME = u'1970-01-01T00:00:00.000Z'
NEVER_START_DATE = u'1970-01-01'
NEVER_END_DATE = u'1969-12-31'
ROLE_MANAGER = u'MANAGER'
ROLE_MEMBER = u'MEMBER'
ROLE_OWNER = u'OWNER'
ROLE_USER = u'USER'
ROLE_MANAGER_MEMBER = u','.join([ROLE_MANAGER, ROLE_MEMBER])
ROLE_MANAGER_OWNER = u','.join([ROLE_MANAGER, ROLE_OWNER])
ROLE_MANAGER_MEMBER_OWNER = u','.join([ROLE_MANAGER, ROLE_MEMBER, ROLE_OWNER])
ROLE_MEMBER_OWNER = u','.join([ROLE_MEMBER, ROLE_OWNER])
PROJECTION_CHOICES_MAP = {u'basic': u'BASIC', u'full': u'FULL',}
SORTORDER_CHOICES_MAP = {u'ascending': u'ASCENDING', u'descending': u'DESCENDING',}
# Cloudprint
CLOUDPRINT_ACCESS_URL = u'https://www.google.com/cloudprint/addpublicprinter.html?printerid={0}&key={1}'
# Valid language codes
LANGUAGE_CODES_MAP = {
  u'af': u'af', #Afrikaans
  u'am': u'am', #Amharic
  u'ar': u'ar', #Arabica
  u'az': u'az', #Azerbaijani
  u'bg': u'bg', #Bulgarian
  u'bn': u'bn', #Bengali
  u'ca': u'ca', #Catalan
  u'chr': u'chr', #Cherokee
  u'cs': u'cs', #Czech
  u'cy': u'cy', #Welsh
  u'da': u'da', #Danish
  u'de': u'de', #German
  u'el': u'el', #Greek
  u'en': u'en', #English
  u'en-gb': u'en-GB', #English (UK)
  u'en-us': u'en-US', #English (US)
  u'es': u'es', #Spanish
  u'es-419': u'es-419', #Spanish (Latin America)
  u'et': u'et', #Estonian
  u'eu': u'eu', #Basque
  u'fa': u'fa', #Persian
  u'fi': u'fi', #Finnish
  u'fr': u'fr', #French
  u'fr-ca': u'fr-ca', #French (Canada)
  u'ag': u'ga', #Irish
  u'gl': u'gl', #Galician
  u'gu': u'gu', #Gujarati
  u'he': u'he', #Hebrew
  u'hi': u'hi', #Hindi
  u'hr': u'hr', #Croatian
  u'hu': u'hu', #Hungarian
  u'hy': u'hy', #Armenian
  u'id': u'id', #Indonesian
  u'in': u'in',
  u'is': u'is', #Icelandic
  u'it': u'it', #Italian
  u'iw': u'he', #Hebrew
  u'ja': u'ja', #Japanese
  u'ka': u'ka', #Georgian
  u'km': u'km', #Khmer
  u'kn': u'kn', #Kannada
  u'ko': u'ko', #Korean
  u'lo': u'lo', #Lao
  u'lt': u'lt', #Lithuanian
  u'lv': u'lv', #Latvian
  u'ml': u'ml', #Malayalam
  u'mn': u'mn', #Mongolian
  u'mr': u'mr', #Marathi
  u'ms': u'ms', #Malay
  u'my': u'my', #Burmese
  u'ne': u'ne', #Nepali
  u'nl': u'nl', #Dutch
  u'no': u'no', #Norwegian
  u'or': u'or', #Oriya
  u'pl': u'pl', #Polish
  u'pt-br': u'pt-BR', #Portuguese (Brazil)
  u'pt-pt': u'pt-PT', #Portuguese (Portugal)
  u'ro': u'ro', #Romanian
  u'ru': u'ru', #Russian
  u'si': u'si', #Sinhala
  u'sk': u'sk', #Slovak
  u'sl': u'sl', #Slovenian
  u'sr': u'sr', #Serbian
  u'sv': u'sv', #Swedish
  u'sw': u'sw', #Swahili
  u'ta': u'ta', #Tamil
  u'te': u'te', #Telugu
  u'th': u'th', #Thai
  u'tl': u'tl', #Tagalog
  u'tr': u'tr', #Turkish
  u'uk': u'uk', #Ukrainian
  u'ur': u'ur', #Urdu
  u'vi': u'vi', #Vietnamese
  u'zh-cn': u'zh-CN', #Chinese (Simplified)
  u'zh-hk': u'zh-HK', #Chinese (Hong Kong/Traditional)
  u'zh-tw': u'zh-TW', #Chinese (Taiwan/Traditional)
  u'zu': u'zu', #Zulu
  }
# GAPI APIs
GAPI_ADMIN_SETTINGS_API = u'admin-settings'
GAPI_APPSACTIVITY_API = u'appsactivity'
GAPI_CALENDAR_API = u'calendar'
GAPI_CLASSROOM_API = u'classroom'
GAPI_CLOUDPRINT_API = u'cloudprint'
GAPI_DATATRANSFER_API = u'datatransfer'
GAPI_DIRECTORY_API = u'directory'
GAPI_DRIVE_API = u'drive'
GAPI_GMAIL_API = u'gmail'
GAPI_GPLUS_API = u'plus'
GAPI_GROUPSSETTINGS_API = u'groupssettings'
GAPI_LICENSING_API = u'licensing'
GAPI_REPORTS_API = u'reports'
GAPI_SITEVERIFICATION_API = u'siteVerification'
# GDATA APIs
GDATA_ADMIN_SETTINGS_API = GAPI_ADMIN_SETTINGS_API
GDATA_CONTACTS_API = u'contacts'
GDATA_EMAIL_AUDIT_API = u'email-audit'
GDATA_EMAIL_SETTINGS_API = u'email-settings'
GDATA_SITES_API = u'sites'
# callGData throw errors
GDATA_BAD_GATEWAY = 601
GDATA_BAD_REQUEST = 602
GDATA_DOES_NOT_EXIST = 1301
GDATA_ENTITY_EXISTS = 1300
GDATA_FORBIDDEN = 603
GDATA_INSUFFICIENT_PERMISSIONS = 604
GDATA_INTERNAL_SERVER_ERROR = 1000
GDATA_INVALID_DOMAIN = 605
GDATA_INVALID_VALUE = 1801
GDATA_NAME_NOT_VALID = 1303
GDATA_NOT_FOUND = 606
GDATA_PRECONDITION_FAILED = 607
GDATA_QUOTA_EXCEEDED = 608
GDATA_SERVICE_NOT_APPLICABLE = 1410
GDATA_SERVICE_UNAVAILABLE = 609
GDATA_TOKEN_EXPIRED = 610
GDATA_TOKEN_INVALID = 403
GDATA_UNKNOWN_ERROR = 600
#
GDATA_NON_TERMINATING_ERRORS = [GDATA_BAD_GATEWAY, GDATA_QUOTA_EXCEEDED, GDATA_SERVICE_UNAVAILABLE, GDATA_TOKEN_EXPIRED]
GDATA_EMAILSETTINGS_THROW_LIST = [GDATA_INVALID_DOMAIN, GDATA_DOES_NOT_EXIST, GDATA_SERVICE_NOT_APPLICABLE, GDATA_BAD_REQUEST, GDATA_NAME_NOT_VALID, GDATA_INTERNAL_SERVER_ERROR, GDATA_INVALID_VALUE]
# oauth errors
OAUTH2_TOKEN_ERRORS = [u'access_denied', u'invalid_grant', u'unauthorized_client: Unauthorized client or scope in request.', u'access_denied: Requested client not authorized.',
                       u'invalid_grant: Not a valid email.', u'invalid_grant: Invalid email or User ID', u'invalid_grant: Bad Request',
                       u'invalid_request: Invalid impersonation prn email address.', u'internal_failure: Backend Error']
# callGAPI throw reasons
GAPI_ABORTED = u'aborted'
GAPI_ALREADY_EXISTS = u'alreadyExists'
GAPI_AUTH_ERROR = u'authError'
GAPI_BACKEND_ERROR = u'backendError'
GAPI_BAD_REQUEST = u'badRequest'
GAPI_CANNOT_CHANGE_OWN_ACL = u'cannotChangeOwnAcl'
GAPI_CANNOT_CHANGE_OWNER_ACL = u'cannotChangeOwnerAcl'
GAPI_CANNOT_DELETE_PRIMARY_CALENDAR = u'cannotDeletePrimaryCalendar'
GAPI_CANNOT_DELETE_PRIMARY_SENDAS = u'cannotDeletePrimarySendAs'
GAPI_CONDITION_NOT_MET = u'conditionNotMet'
GAPI_CUSTOMER_NOT_FOUND = u'customerNotFound'
GAPI_CYCLIC_MEMBERSHIPS_NOT_ALLOWED = u'cyclicMembershipsNotAllowed'
GAPI_DELETED = u'deleted'
GAPI_DELETED_USER_NOT_FOUND = u'deletedUserNotFound'
GAPI_DOMAIN_ALIAS_NOT_FOUND = u'domainAliasNotFound'
GAPI_DOMAIN_NOT_FOUND = u'domainNotFound'
GAPI_DOMAIN_NOT_VERIFIED_SECONDARY = u'domainNotVerifiedSecondary'
GAPI_DUPLICATE = u'duplicate'
GAPI_FAILED_PRECONDITION = u'failedPrecondition'
GAPI_FILE_NOT_FOUND = u'fileNotFound'
GAPI_FORBIDDEN = u'forbidden'
GAPI_GROUP_NOT_FOUND = u'groupNotFound'
GAPI_INSUFFICIENT_PERMISSIONS = u'insufficientPermissions'
GAPI_INTERNAL_ERROR = u'internalError'
GAPI_INVALID = u'invalid'
GAPI_INVALID_ARGUMENT = u'invalidArgument'
GAPI_INVALID_CUSTOMER_ID = u'invalidCustomerId'
GAPI_INVALID_INPUT = u'invalidInput'
GAPI_INVALID_MEMBER = u'invalidMember'
GAPI_INVALID_ORGUNIT = u'invalidOrgunit'
GAPI_INVALID_PARENT_ORGUNIT = u'invalidParentOrgunit'
GAPI_INVALID_QUERY = u'invalidQuery'
GAPI_INVALID_RESOURCE = u'invalidResource'
GAPI_INVALID_SCHEMA_VALUE = u'invalidSchemaValue'
GAPI_INVALID_SCOPE_VALUE = u'invalidScopeValue'
GAPI_INVALID_SHARING_REQUEST = u'invalidSharingRequest'
GAPI_LOGIN_REQUIRED = u'loginRequired'
GAPI_MEMBER_NOT_FOUND = u'memberNotFound'
GAPI_NOT_FOUND = u'notFound'
GAPI_NOT_IMPLEMENTED = u'notImplemented'
GAPI_ORGUNIT_NOT_FOUND = u'orgunitNotFound'
GAPI_PERMISSION_DENIED = u'permissionDenied'
GAPI_PERMISSION_NOT_FOUND = u'permissionNotFound'
GAPI_PHOTO_NOT_FOUND = u'photoNotFound'
GAPI_QUOTA_EXCEEDED = u'quotaExceeded'
GAPI_RATE_LIMIT_EXCEEDED = u'rateLimitExceeded'
GAPI_REQUIRED = u'required'
GAPI_RESOURCE_ID_NOT_FOUND = u'resourceIdNotFound'
GAPI_RESOURCE_NOT_FOUND = u'resourceNotFound'
GAPI_SERVICE_LIMIT = u'serviceLimit'
GAPI_SERVICE_NOT_AVAILABLE = u'serviceNotAvailable'
GAPI_SYSTEM_ERROR = u'systemError'
GAPI_TIME_RANGE_EMPTY = u'timeRangeEmpty'
GAPI_UNKNOWN_ERROR = u'unknownError'
GAPI_USER_NOT_FOUND = u'userNotFound'
GAPI_USER_RATE_LIMIT_EXCEEDED = u'userRateLimitExceeded'
#
GCP_CANT_MODIFY_FINISHED_JOB = u'Can\'t modify the finished job.'
GCP_FAILED_TO_SHARE_THE_PRINTER = u'Failed to share the printer.'
GCP_NO_PRINT_JOBS = u'No print job available on specified printer.'
GCP_UNKNOWN_JOB_ID = u'Unknown job id.'
GCP_UNKNOWN_PRINTER = u'Unknown printer.'
GCP_USER_IS_NOT_AUTHORIZED = u'User is not authorized.'
#
GAPI_DEFAULT_RETRY_REASONS = [GAPI_QUOTA_EXCEEDED, GAPI_RATE_LIMIT_EXCEEDED, GAPI_USER_RATE_LIMIT_EXCEEDED, GAPI_BACKEND_ERROR, GAPI_INTERNAL_ERROR]
GAPI_ACTIVITY_THROW_REASONS = [GAPI_SERVICE_NOT_AVAILABLE]
GAPI_CALENDAR_THROW_REASONS = [GAPI_SERVICE_NOT_AVAILABLE, GAPI_AUTH_ERROR]
GAPI_DRIVE_THROW_REASONS = [GAPI_SERVICE_NOT_AVAILABLE, GAPI_AUTH_ERROR]
GAPI_GMAIL_THROW_REASONS = [GAPI_SERVICE_NOT_AVAILABLE, GAPI_BAD_REQUEST]
GAPI_GPLUS_THROW_REASONS = [GAPI_SERVICE_NOT_AVAILABLE]
GAPI_USER_GET_THROW_REASONS = [GAPI_USER_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN, GAPI_BAD_REQUEST, GAPI_BACKEND_ERROR, GAPI_SYSTEM_ERROR]
#
DRIVE_API_VERSION = u'v2'
#
DRIVE_FILE_NAME = u'title'
DRIVE_FILE_VIEW_LINK = u'alternateLink'
DRIVE_FILES_LIST = u'items'
DRIVE_CREATE_FILE = u'insert'
DRIVE_PATCH_FILE = u'patch'
DRIVE_UPDATE_FILE = u'update'
#
DRIVE_PERMISSIONS_NAME = u'name'
DRIVE_PERMISSIONS_LIST = u'items'
DRIVE_CREATE_PERMISSIONS = u'insert'
DRIVE_PATCH_PERMISSIONS = u'patch'
#
DRIVE_REVISIONS_LIST = u'items'
#
OAUTH2_GAPI_SCOPES = u'gapi'
OAUTH2_GDATA_SCOPES = u'gdata'
OAUTH2_SCOPES_LIST = [OAUTH2_GAPI_SCOPES, OAUTH2_GDATA_SCOPES]
# Object BNF names
OB_ACCESS_TOKEN = u'AccessToken'
OB_ACL_ENTITY = u'ACLEntity'
OB_ARGUMENT = u'argument'
OB_ASP_ID = u'AspID'
OB_CALENDAR_ITEM = U'CalendarItem'
OB_CHAR_SET = u'CharacterSet'
OB_CIDR_NETMASK = u'CIDRnetmask'
OB_CLIENT_ID = u'ClientID'
OB_CONTACT_EMAIL_TYPE = u'ContactEmailType'
OB_CONTACT_ENTITY = u'ContactEntity'
OB_CONTACT_GROUP_ENTITY = u'ContactGroupEntity'
OB_CONTACT_GROUP_ITEM = u'ContactGroupItem'
OB_COURSE_ALIAS = u'CourseAlias'
OB_COURSE_ALIAS_ENTITY = u'CourseAliasEntity'
OB_COURSE_ENTITY = u'CourseEntity'
OB_COURSE_ID = u'CourseID'
OB_CROS_DEVICE_ENTITY = u'CrOSDeviceEntity'
OB_CROS_ENTITY = u'CrOSEntity'
OB_CUSTOMER_ID = u'CustomerID'
OB_DOMAIN_ALIAS = u'DomainAlias'
OB_DOMAIN_NAME = u'DomainName'
OB_DOMAIN_NAME_ENTITY = u'DomainNameEntity'
OB_DRIVE_FILE_ENTITY = u'DriveFileEntity'
OB_DRIVE_FILE_ID = u'DriveFileID'
OB_DRIVE_FILE_NAME = u'DriveFileName'
OB_DRIVE_FOLDER_ID = u'DriveFolderID'
OB_DRIVE_FOLDER_NAME = u'DriveFolderName'
OB_EMAIL_ADDRESS = u'EmailAddress'
OB_EMAIL_ADDRESS_ENTITY = u'EmailAddressEntity'
OB_EMAIL_ADDRESS_OR_UID = u'EmailAaddress|UniqueID'
OB_ENTITY = u'Entity'
OB_ENTITY_TYPE = u'EntityType'
OB_EVENT_ID_ENTITY = u'EventIDEntity'
OB_FIELD_NAME = u'FieldName'
OB_FIELD_NAME_LIST = "FieldNameList"
OB_FILE_NAME = u'FileName'
OB_FILE_NAME_FIELD_NAME = OB_FILE_NAME+u'(:'+OB_FIELD_NAME+u')+'
OB_FILE_NAME_OR_URL = u'FileName|URL'
OB_FILE_PATH = u'FilePath'
OB_FILTER_ID_ENTITY = u'FilterIDEntity'
OB_FORMAT_LIST = u'FormatList'
OB_GAM_ARGUMENT_LIST = u'GAM argument list'
OB_GROUP_ENTITY = u'GroupEntity'
OB_GROUP_ITEM = u'GroupItem'
OB_GUARDIAN_ID = U'GuardianID'
OB_GUARDIAN_STATE_LIST = u'GuardianStateList'
OB_HOST_NAME = u'HostName'
OB_JOB_ID = u'JobID'
OB_JOB_OR_PRINTER_ID = u'JobID|PrinterID'
OB_LABEL_NAME = u'LabelName'
OB_LABEL_REPLACEMENT = u'LabelReplacement'
OB_MESSAGE_ID = u'MessageID'
OB_MOBILE_DEVICE_ENTITY = u'MobileDeviceEntity'
OB_MOBILE_ENTITY = u'MobileEntity'
OB_NAME = u'Name'
OB_NOTIFICATION_ID = u'NotificationID'
OB_ORGUNIT_ENTITY = u'OrgUnitEntity'
OB_ORGUNIT_PATH = u'OrgUnitPath'
OB_PARAMETER_KEY = u'ParameterKey'
OB_PARAMETER_VALUE = u'ParameterValue'
OB_PERMISSION_ID = u'PermissionID'
OB_PHOTO_FILENAME_PATTERN = u'FilenameNamePattern'
OB_PRINTER_ID = u'PrinterID'
OB_PRINTER_ID_ENTITY = u'PrinterIDEntity'
OB_PRINTJOB_AGE = u'PrintJobAge'
OB_PRINTJOB_ID = u'PrintJobID'
OB_PRODUCT_ID_LIST = u'ProductIDList'
OB_PROPERTY_KEY = u'PropertyKey'
OB_PROPERTY_VALUE = u'PropertyValue'
OB_QUERY = u'Query'
OB_RECURRENCE = u'RRULE EXRULE RDATE and EXDATE lines'
OB_REQUEST_ID = u'RequestID'
OB_RESOURCE_ENTITY = u'ResourceEntity'
OB_RESOURCE_ID = u'ResourceID'
OB_RE_PATTERN = u'REPattern'
OB_ROLE_ASSIGNMENT_ID = u'RoleAssignmentId'
OB_ROLE_ID = u'RoleId'
OB_ROLE_LIST = u'RoleList'
OB_SCHEMA_ENTITY = u'SchemaEntity'
OB_SCHEMA_NAME = u'SchemaName'
OB_SCHEMA_NAME_LIST = u'SchemaNameList'
OB_SECTION_NAME = u'SectionName'
OB_SERVICE_NAME = u'ServiceName'
OB_SITE_ENTITY = u'SiteEntity'
OB_SKU_ID = u'SKUID'
OB_SKU_ID_LIST = u'SKUIDList'
OB_STRING = u'String'
OB_STUDENT_ID = u'StudentID'
OB_TAG = u'Tag'
OB_TEACHER_ID = u'TeacherID'
OB_THREAD_ID = u'ThreadID'
OB_TRANSFER_ID = u'TransferID'
OB_URI = u'URI'
OB_URL = u'URL'
OB_USER_ENTITY = u'UserEntity'
OB_USER_ITEM = u'UserItem'
# Entity names
# Keys into ENTITY_NAMES; arbitrary values but must be unique
EN_ACCESS_TOKEN = u'atok'
EN_ACCOUNT = u'acct'
EN_ACL = u'acl '
EN_ACTION = u'actn'
EN_ACTIVITY = u'actv'
EN_ALIAS = u'alia'
EN_ALIAS_EMAIL = u'alie'
EN_ALIAS_TARGET = u'alit'
EN_APPLICATION_SPECIFIC_PASSWORD = u'aspa'
EN_ARROWS_ENABLED = u'arro'
EN_AUDIT_ACTIVITY_REQUEST = u'auda'
EN_AUDIT_EXPORT_REQUEST = u'audx'
EN_AUDIT_MONITOR_REQUEST = u'audm'
EN_BACKUP_VERIFICATION_CODE = u'buvc'
EN_CALENDAR = u'cale'
EN_CALENDAR_SETTINGS = u'cset'
EN_CONFIG_FILE = u'conf'
EN_CONTACT = u'cont'
EN_CONTACT_GROUP = u'cogr'
EN_CONTACT_GROUP_NAME = u'cogn'
EN_COURSE = u'cour'
EN_COURSE_ALIAS = u'coal'
EN_COURSE_ID = u'coid'
EN_CRITERIA = u'crit'
EN_CROS_DEVICE = u'cros'
EN_CUSTOMER_ID = u'cuid'
EN_DEFAULT_LANGUAGE = u'dfla'
EN_DELEGATE = u'dele'
EN_DELEGATOR = u'delo'
EN_DELETED_USER = u'delu'
EN_DOMAIN = u'doma'
EN_DOMAIN_ALIAS = u'doal'
EN_DRIVE_FILE = u'file'
EN_DRIVE_FILE_ID = u'fili'
EN_DRIVE_FILE_OR_FOLDER = u'fifo'
EN_DRIVE_FILE_OR_FOLDER_ACL = u'fiac'
EN_DRIVE_FILE_OR_FOLDER_ID = u'fifi'
EN_DRIVE_FOLDER = u'fold'
EN_DRIVE_FOLDER_ID = u'foli'
EN_DRIVE_PATH = u'drvp'
EN_DRIVE_SETTINGS = u'drvs'
EN_DRIVE_TRASH = u'drvt'
EN_EMAIL = u'emai'
EN_EMAIL_ALIAS = u'emal'
EN_EMAIL_SETTINGS = u'emse'
EN_ENTITY = u'enti'
EN_EVENT = u'evnt'
EN_FIELD = u'fiel'
EN_FILTER = u'filt'
EN_FORWARD_ENABLED = u'fwde'
EN_FORWARDING_ADDRESS = u'fwda'
EN_GMAIL_PROFILE = u'gmpr'
EN_GPLUS_PROFILE = u'gppr'
EN_GROUP = u'grou'
EN_GROUP_ALIAS = u'gali'
EN_GROUP_EMAIL = u'gale'
EN_GROUP_MEMBERSHIP = u'gmem'
EN_GROUP_SETTINGS = u'gset'
EN_GUARDIAN = u'guar'
EN_GUARDIAN_INVITATION = u'gari'
EN_IMAP_ENABLED = u'imap'
EN_INSTANCE = u'inst'
EN_ITEM = u'item'
EN_KEYBOARD_SHORTCUTS_ENABLED = u'kbsc'
EN_LABEL = u'labe'
EN_LANGUAGE = u'lang'
EN_LICENSE = u'lice'
EN_LOGO = u'logo'
EN_MEMBER = u'memb'
EN_MESSAGE = u'mesg'
EN_MOBILE_DEVICE = u'mobi'
EN_NOTIFICATION = u'noti'
EN_OAUTH2_TXT_FILE = u'oaut'
EN_ORGANIZATIONAL_UNIT = u'orgu'
EN_PAGE_SIZE = u'page'
EN_PARENT_ORGANIZATIONAL_UNIT = u'porg'
EN_PARTICIPANT = u'part'
EN_PERMISSIONS = u'perm'
EN_PERMISSION_ID = u'peid'
EN_PERMITTEE = u'perm'
EN_PHOTO = u'phot'
EN_POP_ENABLED = u'popa'
EN_PRINTER = u'prin'
EN_PRINTJOB = u'prjo'
EN_PRODUCT = u'prod'
EN_PROFILE_SHARING_ENABLED = u'prof'
EN_QUERY = u'quer'
EN_REQUEST_ID = u'reqi'
EN_RESOURCE_CALENDAR = u'resc'
EN_RESOURCE_ID = u'resi'
EN_REVISION_ID = u'revi'
EN_ROLE = u'role'
EN_ROLE_ASSIGNMENT_ID = u'raid'
EN_SCOPE = u'scop'
EN_SECTION = u'sect'
EN_SENDAS_ADDRESS = u'sasa'
EN_SERVICE = u'serv'
EN_SIGNATURE = u'sign'
EN_SITE = u'site'
EN_SKU = u'sku '
EN_SNIPPETS_ENABLED = u'snip'
EN_SSO_KEY = u'ssok'
EN_SSO_SETTINGS = u'ssos'
EN_SOURCE_USER = u'srcu'
EN_STUDENT = u'stud'
EN_TARGET_USER = u'tgtu'
EN_TEACHER = u'teac'
EN_THREAD = u'thre'
EN_TOKEN = u'tokn'
EN_TRANSFER_ID = u'trid'
EN_TRANSFER_REQUEST = u'trnr'
EN_UNICODE_ENCODING_ENABLED = u'unic'
EN_UNIQUE_ID = u'uniq'
EN_USER = u'user'
EN_USER_ALIAS = u'uali'
EN_USER_EMAIL = u'ual'
EN_USER_SCHEMA = u'usch'
EN_VACATION = u'vaca'
EN_VACATION_ENABLED = u'vace'
EN_VALUE = u'valu'
EN_WEBCLIPS_ENABLED = u'webc'
# ENTITY_NAMES[0] is plural, ENTITY_NAMES[1] is singular unless the item name is explicitly plural (Calendar Settings)
# For items with Boolean values, both entries are singular (Forward, POP)
# These values can be translated into other languages
ENTITY_NAMES = {
  EN_ACCESS_TOKEN: [u'Access Tokens', u'Access Token'],
  EN_ACCOUNT: [u'Accounts', u'Account'],
  EN_ACL: [u'ACLs', u'ACL'],
  EN_ACTION: [u'Actions', u'Action'],
  EN_ACTIVITY: [u'Activities', u'Activity'],
  EN_ALIAS: [u'Aliases', u'Alias'],
  EN_ALIAS_EMAIL: [u'Alias Emails', u'Alias Email'],
  EN_ALIAS_TARGET: [u'Alias Targets', u'Alias Target'],
  EN_APPLICATION_SPECIFIC_PASSWORD: [u'Application Specific Passwords', u'Application Specific Password'],
  EN_ARROWS_ENABLED: [u'Personal Indicator Arrows Enabled', u'Personal Indicator Arrows Enabled'],
  EN_AUDIT_ACTIVITY_REQUEST: [u'Audit Activity Requests', u'Audit Activity Request'],
  EN_AUDIT_EXPORT_REQUEST: [u'Audit Export Requests', u'Audit Export Request'],
  EN_AUDIT_MONITOR_REQUEST: [u'Audit Monitor Requests', u'Audit Monitor Request'],
  EN_BACKUP_VERIFICATION_CODE: [u'Backup Verification Codes', u'Backup Verification Code'],
  EN_CALENDAR: [u'Calendars', u'Calendar'],
  EN_CALENDAR_SETTINGS: [u'Calendar Settings', u'Calendar Settings'],
  EN_CONFIG_FILE: [u'Config File', u'Config File'],
  EN_CONTACT: [u'Contacts', u'Contact'],
  EN_CONTACT_GROUP: [u'Contact Groups', u'Contact Group'],
  EN_CONTACT_GROUP_NAME: [u'Contact Group Names', u'Contact Group Name'],
  EN_COURSE: [u'Courses', u'Course'],
  EN_COURSE_ALIAS: [u'Course Aliases', u'Course Alias'],
  EN_COURSE_ID: [u'Course IDs', u'Course ID'],
  EN_CRITERIA: [u'Criteria', u'Criteria'],
  EN_CROS_DEVICE: [u'CrOS Devices', u'CrOS Device'],
  EN_CUSTOMER_ID: [u'Customer IDs', u'Customer ID'],
  EN_DEFAULT_LANGUAGE: [u'Default Language', u'Default Language'],
  EN_DELEGATE: [u'Delegates', u'Delegate'],
  EN_DELEGATOR: [u'Delegators', u'Delegator'],
  EN_DELETED_USER: [u'Deleted Users', u'Deleted User'],
  EN_DOMAIN: [u'Domains', u'Domain'],
  EN_DOMAIN_ALIAS: [u'Domain Aliases', u'Domain Alias'],
  EN_DRIVE_FILE: [u'Drive Files', u'Drive File'],
  EN_DRIVE_FILE_ID: [u'Drive File IDs', u'Drive File ID'],
  EN_DRIVE_FILE_OR_FOLDER: [u'Drive Files/Folders', u'Drive File/Folder'],
  EN_DRIVE_FILE_OR_FOLDER_ACL: [u'Drive File/Folder ACLs', u'Drive File/Folder ACL'],
  EN_DRIVE_FILE_OR_FOLDER_ID: [u'Drive File/Folder IDs', u'Drive File/Folder ID'],
  EN_DRIVE_FOLDER: [u'Drive Folders', u'Drive Folder'],
  EN_DRIVE_FOLDER_ID: [u'Drive Folder IDs', u'Drive Folder ID'],
  EN_DRIVE_PATH: [u'Drive Paths', u'Drive Path'],
  EN_DRIVE_SETTINGS: [u'Drive Settings', u'Drive Settings'],
  EN_DRIVE_TRASH: [u'Drive Trash', u'Drive Trash'],
  EN_EMAIL: [u'Email Addresses', u'Email Address'],
  EN_EMAIL_ALIAS: [u'Email Aliases', u'Email Alias'],
  EN_EMAIL_SETTINGS: [u'Email Settings', u'Email Settings'],
  EN_ENTITY: [u'Entities', u'Entity'],
  EN_EVENT: [u'Events', u'Event'],
  EN_FIELD: [u'Fields', u'Field'],
  EN_FILTER: [u'Filters', u'Filter'],
  EN_FORWARD_ENABLED: [u'Forward Enabled', u'Forward Enabled'],
  EN_FORWARDING_ADDRESS: [u'Forwarding Addresses', u'Forwarding Address'],
  EN_GMAIL_PROFILE: [u'Gmail profile', u'Gmail profile'],
  EN_GPLUS_PROFILE: [u'Gplus profile', u'Gplus profile'],
  EN_GROUP: [u'Groups', u'Group'],
  EN_GROUP_ALIAS: [u'Group Aliases', u'Group Alias'],
  EN_GROUP_EMAIL: [u'Group Emails', u'Group Email'],
  EN_GROUP_MEMBERSHIP: [u'Group Memberships', u'Group Membership'],
  EN_GROUP_SETTINGS: [u'Group Settings', u'Group Settings'],
  EN_GUARDIAN: [u'Guardians', u'Guardian'],
  EN_GUARDIAN_INVITATION: [u'Guardian Invitations', u'Guardian Invitation'],
  EN_IMAP_ENABLED: [u'IMAP Enabled', u'IMAP Enabled'],
  EN_INSTANCE: [u'Instances', u'Instance'],
  EN_ITEM: [u'Items', u'Item'],
  EN_KEYBOARD_SHORTCUTS_ENABLED: [u'Keyboard Shortcuts Enabled', u'Keyboard Shortcuts Enabled'],
  EN_LABEL: [u'Labels', u'Label'],
  EN_LANGUAGE: [u'Languages', u'Language'],
  EN_LICENSE: [u'Licenses', u'License'],
  EN_LOGO: [u'Logos', u'Logo'],
  EN_MEMBER: [u'Members', u'Member'],
  EN_MESSAGE: [u'Messages', u'Message'],
  EN_MOBILE_DEVICE: [u'Mobile Devices', u'Mobile Device'],
  EN_NOTIFICATION: [u'Notifications', u'Notification'],
  EN_OAUTH2_TXT_FILE: [u'Client OAuth2 File', u'Client OAuth2 File'],
  EN_ORGANIZATIONAL_UNIT: [u'Organizational Units', u'Organizational Unit'],
  EN_PAGE_SIZE: [u'Page Size', u'Page Size'],
  EN_PARENT_ORGANIZATIONAL_UNIT: [u'Parent Organizational Units', u'Parent Organizational Unit'],
  EN_PARTICIPANT: [u'Participants', u'Participant'],
  EN_PERMISSIONS: [u'Permissions', u'Permissions'],
  EN_PERMISSION_ID: [u'Permission IDs', u'Permission ID'],
  EN_PERMITTEE: [u'Permittees', u'Permittee'],
  EN_PHOTO: [u'Photos', u'Photo'],
  EN_POP_ENABLED: [u'POP Enabled', u'POP Enabled'],
  EN_PRINTER: [u'Printers', u'Printer'],
  EN_PRINTJOB: [u'Print Jobs', u'Print Job'],
  EN_PRODUCT: [u'Products', u'Product'],
  EN_PROFILE_SHARING_ENABLED: [u'Profile Sharing Enabled', u'Profile Sharing Enabled'],
  EN_QUERY: [u'Queries', u'Query'],
  EN_REQUEST_ID: [u'Request IDs', u'Request ID'],
  EN_RESOURCE_CALENDAR: [u'Resource Calendars', u'Resource Calendar'],
  EN_RESOURCE_ID: [u'Resource IDs', u'Resource ID'],
  EN_REVISION_ID: [u'Revision IDs', u'Revision ID'],
  EN_ROLE: [u'Roles', u'Role'],
  EN_ROLE_ASSIGNMENT_ID: [u'Role Assignment IDs', u'Role Assignment ID'],
  EN_SCOPE: [u'Scopes', u'Scope'],
  EN_SECTION: [u'Sections', u'Section'],
  EN_SENDAS_ADDRESS: [u'SendAs Addresses', u'SendAs Address'],
  EN_SERVICE: [u'Services', u'Service'],
  EN_SIGNATURE: [u'Signatures', u'Signature'],
  EN_SITE: [u'Sites', u'Site'],
  EN_SKU: [u'SKUs', u'SKU'],
  EN_SNIPPETS_ENABLED: [u'Preview Snippets Enabled', u'Preview Snippets Enabled'],
  EN_SSO_KEY: [u'SSO Key', u'SSO Key'],
  EN_SSO_SETTINGS: [u'SSO Settings', u'SSO Settings'],
  EN_SOURCE_USER: [u'Source Users', u'Source User'],
  EN_STUDENT: [u'Students', u'Student'],
  EN_TARGET_USER: [u'Target Users', u'Target User'],
  EN_TEACHER: [u'Teachers', u'Teacher'],
  EN_THREAD: [u'Threads', u'Thread'],
  EN_TOKEN: [u'Tokens', u'Token'],
  EN_TRANSFER_ID: [u'Transfer IDs', u'Transfer ID'],
  EN_TRANSFER_REQUEST: [u'Transfer Requests', u'Transfer Request'],
  EN_UNICODE_ENCODING_ENABLED: [u'UTF-8 Encoding Enabled', u'UTF-8 Encoding Enabled'],
  EN_UNIQUE_ID: [u'Unique IDs', u'Unique ID'],
  EN_USER: [u'Users', u'User'],
  EN_USER_ALIAS: [u'User Aliases', u'User Alias'],
  EN_USER_EMAIL: [u'User Emails', u'User Email'],
  EN_USER_SCHEMA: [u'Schemas', u'Schema'],
  EN_VACATION: [u'Vacation', u'Vacation'],
  EN_VACATION_ENABLED: [u'Vacation Enabled', u'Vacation Enabled'],
  EN_VALUE: [u'Values', u'Value'],
  EN_WEBCLIPS_ENABLED: [u'Web Clips Enabled', u'Web Clips Enabled'],
  ROLE_MANAGER: [u'Managers', u'Manager'],
  ROLE_MANAGER_MEMBER: [u'Managers, Members', u'Manager, Member'],
  ROLE_MANAGER_MEMBER_OWNER: [u'Managers, Members, Owners', u'Manager, Member, Owners'],
  ROLE_MANAGER_OWNER: [u'Managers, Owners', u'Manager, Owner'],
  ROLE_MEMBER: [u'Members', u'Member'],
  ROLE_MEMBER_OWNER: [u'Members, Owners', u'Member, Owner'],
  ROLE_OWNER: [u'Owners', u'Owner'],
  ROLE_USER: [u'Users', u'User'],
  }
# GAM entity types as specified on the command line
CL_ENTITY_COURSEPARTICIPANTS = u'courseparticipants'
CL_ENTITY_CROS = u'cros'
CL_ENTITY_CROS_QUERY = u'crosquery'
CL_ENTITY_CROS_OU = u'cros_ou'
CL_ENTITY_CROS_OU_AND_CHILDREN = u'cros_ou_and_children'
CL_ENTITY_CROS_OUS = u'cros_ous'
CL_ENTITY_CROS_OUS_AND_CHILDREN = u'cros_ous_and_children'
CL_ENTITY_GROUP = u'group'
CL_ENTITY_GROUPS = u'groups'
CL_ENTITY_LICENSES = u'licenses'
CL_ENTITY_OU = u'ou'
CL_ENTITY_OU_AND_CHILDREN = u'ou_and_children'
CL_ENTITY_OUS = u'ous'
CL_ENTITY_OUS_AND_CHILDREN = u'ous_and_children'
CL_ENTITY_QUERY = u'query'
CL_ENTITY_STUDENTS = u'students'
CL_ENTITY_TEACHERS = u'teachers'
CL_ENTITY_USER = u'user'
CL_ENTITY_USERS = u'users'
#
CL_CROS_ENTITIES = [
  CL_ENTITY_CROS,
  CL_ENTITY_CROS_QUERY,
  CL_ENTITY_CROS_OU,
  CL_ENTITY_CROS_OU_AND_CHILDREN,
  CL_ENTITY_CROS_OUS,
  CL_ENTITY_CROS_OUS_AND_CHILDREN,
  ]
CL_USER_ENTITIES = [
  CL_ENTITY_COURSEPARTICIPANTS,
  CL_ENTITY_GROUP,
  CL_ENTITY_GROUPS,
  CL_ENTITY_LICENSES,
  CL_ENTITY_OU,
  CL_ENTITY_OU_AND_CHILDREN,
  CL_ENTITY_OUS,
  CL_ENTITY_OUS_AND_CHILDREN,
  CL_ENTITY_QUERY,
  CL_ENTITY_STUDENTS,
  CL_ENTITY_TEACHERS,
  CL_ENTITY_USER,
  CL_ENTITY_USERS,
  ]
# Aliases for CL entity types
CL_ENTITY_ALIAS_MAP = {
  u'crosorg': CL_ENTITY_CROS_OU,
  u'crosorg_and_child': CL_ENTITY_CROS_OU_AND_CHILDREN,
  u'crosorg_and_children': CL_ENTITY_CROS_OU_AND_CHILDREN,
  u'crosorgs': CL_ENTITY_CROS_OUS,
  u'crosorgs_and_child': CL_ENTITY_CROS_OUS_AND_CHILDREN,
  u'crosorgs_and_children': CL_ENTITY_CROS_OUS_AND_CHILDREN,
  u'crosou_and_child': CL_ENTITY_CROS_OU_AND_CHILDREN,
  u'crosou_and_childen': CL_ENTITY_CROS_OU_AND_CHILDREN,
  u'crosous_and_child': CL_ENTITY_CROS_OUS_AND_CHILDREN,
  u'cros_org': CL_ENTITY_CROS_OU,
  u'cros_org_and_child': CL_ENTITY_CROS_OU_AND_CHILDREN,
  u'cros_org_and_children': CL_ENTITY_CROS_OU_AND_CHILDREN,
  u'cros_orgs': CL_ENTITY_CROS_OUS,
  u'cros_orgs_and_child': CL_ENTITY_CROS_OUS_AND_CHILDREN,
  u'cros_orgs_and_children': CL_ENTITY_CROS_OUS_AND_CHILDREN,
  u'cros_ou_and_child': CL_ENTITY_CROS_OU_AND_CHILDREN,
  u'cros_ou_and_childen': CL_ENTITY_CROS_OU_AND_CHILDREN,
  u'cros_ous_and_child': CL_ENTITY_CROS_OUS_AND_CHILDREN,
  u'license': CL_ENTITY_LICENSES,
  u'licence': CL_ENTITY_LICENSES,
  u'licences': CL_ENTITY_LICENSES,
  u'org': CL_ENTITY_OU,
  u'org_and_child': CL_ENTITY_OU_AND_CHILDREN,
  u'org_and_children': CL_ENTITY_OU_AND_CHILDREN,
  u'orgs': CL_ENTITY_OUS,
  u'orgs_and_child': CL_ENTITY_OUS_AND_CHILDREN,
  u'orgs_and_children': CL_ENTITY_OUS_AND_CHILDREN,
  u'ou_and_child': CL_ENTITY_OU_AND_CHILDREN,
  u'ous_and_child': CL_ENTITY_OUS_AND_CHILDREN,
  }
# CL entity source selectors
CL_ENTITY_SELECTOR_ALL = u'all'
CL_ENTITY_SELECTOR_ARGS = u'args'
CL_ENTITY_SELECTOR_CSV = u'csv'
CL_ENTITY_SELECTOR_CSVFILE = u'csvfile'
CL_ENTITY_SELECTOR_FILE = u'file'
CL_ENTITY_SELECTOR_DATAFILE = u'datafile'
CL_ENTITY_SELECTOR_CROSCSV = u'croscsv'
CL_ENTITY_SELECTOR_CROSCSVFILE = u'croscsvfile'
CL_ENTITY_SELECTOR_CROSFILE = u'crosfile'
CL_ENTITY_SELECTOR_CSVKMD = u'csvkmd'
CL_ENTITY_SELECTOR_CSVDATA = u'csvdata'
CL_ENTITY_SELECTOR_CSVCROS = u'csvcros'
#
CL_CROS_ENTITY_SELECTORS = [
  CL_ENTITY_SELECTOR_CROSCSV,
  CL_ENTITY_SELECTOR_CROSCSVFILE,
  CL_ENTITY_SELECTOR_CROSFILE,
  ]
CL_ENTITY_SELECTORS = [
  CL_ENTITY_SELECTOR_ALL,
  CL_ENTITY_SELECTOR_ARGS,
  CL_ENTITY_SELECTOR_CSV,
  CL_ENTITY_SELECTOR_CSVFILE,
  CL_ENTITY_SELECTOR_FILE,
  CL_ENTITY_SELECTOR_DATAFILE,
  CL_ENTITY_SELECTOR_CSVKMD,
  ]
CL_CSVCROS_ENTITY_SELECTORS = [
  CL_ENTITY_SELECTOR_CSVCROS,
  ]
CL_CSVDATA_ENTITY_SELECTORS = [
  CL_ENTITY_SELECTOR_CSVDATA,
  ]
# Allowed values for CL source selector all
CL_CROS_ENTITY_SELECTOR_ALL_SUBTYPES = [
  CL_ENTITY_CROS,
  ]
CL_USER_ENTITY_SELECTOR_ALL_SUBTYPES = [
  CL_ENTITY_USERS,
  ]
#
CL_ENTITY_ALL_CROS = CL_ENTITY_SELECTOR_ALL+u' '+CL_ENTITY_CROS
CL_ENTITY_ALL_USERS = CL_ENTITY_SELECTOR_ALL+u' '+CL_ENTITY_USERS
#
CL_ENTITY_SELECTOR_ALL_SUBTYPES_MAP = {
  CL_ENTITY_CROS: CL_ENTITY_ALL_CROS,
  CL_ENTITY_USERS: CL_ENTITY_ALL_USERS,
  }
# Allowed values for CL source selector args, datafile, csvkmd
CL_CROS_ENTITY_SELECTOR_ARGS_DATAFILE_CSVKMD_SUBTYPES = [
  CL_ENTITY_CROS,
  CL_ENTITY_CROS_OUS,
  CL_ENTITY_CROS_OUS_AND_CHILDREN,
  ]
CL_USER_ENTITY_SELECTOR_ARGS_DATAFILE_CSVKMD_SUBTYPES = [
  CL_ENTITY_USERS,
  CL_ENTITY_GROUPS,
  CL_ENTITY_OUS,
  CL_ENTITY_OUS_AND_CHILDREN,
  CL_ENTITY_COURSEPARTICIPANTS,
  CL_ENTITY_STUDENTS,
  CL_ENTITY_TEACHERS,
  ]
# Command line objects
CL_OB_ADMIN = u'admin'
CL_OB_ADMINS = u'admins'
CL_OB_ADMINROLES = u'adminroles'
CL_OB_ALIAS = u'alias'
CL_OB_ALIASES = u'aliases'
CL_OB_ASP = u'asp'
CL_OB_ASPS = u'asps'
CL_OB_BACKUPCODES = u'backupcodes'
CL_OB_CALATTENDEES = u'calattendees'
CL_OB_CALENDAR = u'calendar'
CL_OB_CALENDARS = u'calendars'
CL_OB_CALSETTINGS = u'calsettings'
CL_OB_CONTACT = u'contact'
CL_OB_CONTACTS = u'contacts'
CL_OB_CONTACT_GROUP = u'contactgroup'
CL_OB_CONTACT_GROUPS = u'contactgroups'
CL_OB_COURSE = u'course'
CL_OB_COURSES = u'courses'
CL_OB_COURSE_PARTICIPANTS = u'course-participants'
CL_OB_CROS = u'cros'
CL_OB_CROSES = u'croses'
CL_OB_CUSTOMER = u'customer'
CL_OB_DATA_TRANSFER = u'datatransfer'
CL_OB_DATA_TRANSFERS = u'datatransfers'
CL_OB_DELEGATE = u'delegate'
CL_OB_DELEGATES = u'delegates'
CL_OB_DOMAIN = u'domain'
CL_OB_DOMAINS = u'domains'
CL_OB_DOMAIN_ALIAS = u'domainalias'
CL_OB_DOMAIN_ALIASES = u'domainaliases'
CL_OB_DRIVE = u'drive'
CL_OB_DRIVEACTIVITY = u'driveactivity'
CL_OB_DRIVEFILE = u'drivefile'
CL_OB_DRIVEFILEACL = u'drivefileacl'
CL_OB_DRIVESETTINGS = u'drivesettings'
CL_OB_DRIVETRASH = u'drivetrash'
CL_OB_EMPTYDRIVEFOLDERS = u'emptydrivefolders'
CL_OB_FILEINFO = u'fileinfo'
CL_OB_FILELIST = u'filelist'
CL_OB_FILEPATH = u'filepath'
CL_OB_FILEREVISIONS = u'filerevisions'
CL_OB_FILETREE = u'filetree'
CL_OB_FILTER = u'filter'
CL_OB_FILTERS = u'filters'
CL_OB_FORWARD = u'forward'
CL_OB_FORWARDINGADDRESS = u'forwardingaddress'
CL_OB_FORWARDINGADDRESSES = u'forwardingaddresses'
CL_OB_GMAILPROFILE = u'gmailprofile'
CL_OB_GPLUSPROFILE = u'gplusprofile'
CL_OB_GROUP = u'group'
CL_OB_GROUPS = u'groups'
CL_OB_GROUP_MEMBERS = u'group-members'
CL_OB_GUARDIAN = u'guardian'
CL_OB_GUARDIANS = u'guardians'
CL_OB_IMAP = u'imap'
CL_OB_INSTANCE = u'instance'
CL_OB_LABEL = u'label'
CL_OB_LABELS = u'labels'
CL_OB_LABELSETTINGS = u'labelsettings'
CL_OB_LICENSE = u'license'
CL_OB_LICENSES = u'licenses'
CL_OB_LOGO = u'logo'
CL_OB_MESSAGE = u'message'
CL_OB_MESSAGES = u'messages'
CL_OB_MOBILE = u'mobile'
CL_OB_MOBILES = u'mobiles'
CL_OB_NOTE = u'note'
CL_OB_NOTIFICATION = u'notification'
CL_OB_ORG = u'org'
CL_OB_ORGS = u'orgs'
CL_OB_OWNERSHIP = u'ownership'
CL_OB_PHOTO = u'photo'
CL_OB_POP = u'pop'
CL_OB_PRINTER = u'printer'
CL_OB_PRINTERS = u'printers'
CL_OB_PRINTJOBS = u'printjobs'
CL_OB_PROFILE = u'profile'
CL_OB_RESOURCE = u'resource'
CL_OB_RESOURCES = u'resources'
CL_OB_SCHEMA = u'schema'
CL_OB_SCHEMAS = u'schemas'
CL_OB_SECCALS = u'seccals'
CL_OB_SENDAS = u'sendas'
CL_OB_SIGNATURE = u'signature'
CL_OB_SITE = u'site'
CL_OB_SITES = u'sites'
CL_OB_SITEACL = u'siteacl'
CL_OB_SITEACLS = u'siteacls'
CL_OB_SITEACTIVITY = u'siteactivity'
CL_OB_THREAD = u'thread'
CL_OB_THREADS = u'threads'
CL_OB_TOKEN = u'token'
CL_OB_TOKENS = u'tokens'
CL_OB_TRANSFERAPPS = u'transferapps'
CL_OB_USER = u'user'
CL_OB_USERS = u'users'
CL_OB_VACATION = u'vacation'
CL_OB_VERIFY = u'verify'
# Command line batch/csv/loop keywords
GAM_CMD = u'gam'
COMMIT_BATCH_CMD = u'commit-batch'
LOOP_CMD = u'loop'
# Command line select/config/redirect arguments
SELECT_CMD = u'select'
CONFIG_CMD = u'config'
REDIRECT_CMD = u'redirect'
GAM_META_COMMANDS = [SELECT_CMD, CONFIG_CMD, REDIRECT_CMD,]
#
CLEAR_NONE_ARGUMENT = [u'clear', u'none',]
CLIENTID_ARGUMENT = [u'clientid',]
DATAFIELD_ARGUMENT = [u'datafield',]
DATA_ARGUMENT = [u'data',]
FILE_ARGUMENT = [u'file',]
FROM_ARGUMENT = [u'from',]
IDS_ARGUMENT = [u'ids',]
ID_ARGUMENT = [u'id',]
LOGO_ARGUMENT = [u'logo',]
MODE_ARGUMENT = [u'mode',]
MOVE_ADD_ARGUMENT = [u'move', u'add',]
MULTIVALUE_ARGUMENT = [u'multivalued', u'multivalue', u'value',]
NOINFO_ARGUMENT = [u'noinfo',]
NORMALIZE_ARGUMENT = [u'normalize',]
NOTSUSPENDED_ARGUMENT = [u'notsuspended',]
ORG_OU_ARGUMENT = [u'org', u'ou',]
PRIMARY_ARGUMENT = [u'primary',]
PRIMARY_NOTPRIMARY_CHOICE_MAP = {u'primary': True, u'notprimary': False}
QUERY_ARGUMENT = [u'query',]
SHOWTITLES_ARGUMENT = [u'showtitles',]
TODRIVE_ARGUMENT = [u'todrive',]
TO_ARGUMENT = [u'to',]
UNSTRUCTURED_FORMATTED_ARGUMENT = [u'unstructured', u'formatted',]

# Action names
# Keys into ACTION_NAMES; arbitrary values but must be unique
AC_ADD = u'add '
AC_BACKUP = u'back'
AC_CANCEL = u'canc'
AC_CLAIM = u'clai'
AC_CLAIM_OWNERSHIP = u'clow'
AC_COPY = u'copy'
AC_CREATE = u'crea'
AC_DELETE = u'dele'
AC_DELETE_EMPTY = u'delm'
AC_DEPROVISION = u'depr'
AC_DOWNLOAD = u'down'
AC_EMPTY = u'empt'
AC_FETCH = u'fetc'
AC_FORWARD = u'forw'
AC_INFO = u'info'
AC_INITIALIZE = u'init'
AC_INVALIDATE = u'inva'
AC_LIST = u'list'
AC_MERGE = u'merg'
AC_MODIFY = u'modi'
AC_MOVE = u'move'
AC_PERFORM = u'perf'
AC_PRINT = u'prin'
AC_PURGE = u'purg'
AC_REGISTER = u'regi'
AC_RELABEL = u'rela'
AC_REMOVE = u'remo'
AC_RENAME = u'rena'
AC_REPLACE = u'repl'
AC_REPORT = u'repo'
AC_RESTORE = u'rest'
AC_RESUBMIT = u'resu'
AC_SAVE = u'save'
AC_SET = u'set '
AC_SHOW = u'show'
AC_SPAM = u'spam'
AC_SUBMIT = u'subm'
AC_SYNC = u'sync'
AC_TRANSFER = u'tran'
AC_TRANSFER_OWNERSHIP = u'trow'
AC_TRASH = u'tras'
AC_UNDELETE = u'unde'
AC_UNTRASH = u'untr'
AC_UPDATE = u'upda'
AC_UPLOAD = u'uplo'
AC_WATCH = u'watc'
AC_WIPE = u'wipe'
# Usage:
# ACTION_NAMES[1] n Items - Delete 10 Users
# Item xxx ACTION_NAMES[0] - User xxx Deleted
# These values can be translated into other languages
ACTION_NAMES = {
  AC_ADD: [u'Added', u'Add'],
  AC_BACKUP: [u'Backed up', u'Backup'],
  AC_CANCEL: [u'Cancelled', u'Cancel'],
  AC_CLAIM: [u'Claimed', u'Claim'],
  AC_CLAIM_OWNERSHIP: [u'Ownership Claimed', u'Claim Ownership'],
  AC_COPY: [u'Copied', u'Copy'],
  AC_CREATE: [u'Created', u'Create'],
  AC_DELETE: [u'Deleted', u'Delete'],
  AC_DELETE_EMPTY: [u'Deleted', u'Delete Empty'],
  AC_DEPROVISION: [u'Deprovisioned', u'Deprovision'],
  AC_DOWNLOAD: [u'Downloaded', u'Download'],
  AC_EMPTY: [u'Emptied', u'Empty'],
  AC_FORWARD: [u'Forwarded', u'Forward'],
  AC_INFO: [u'Shown', u'Show Info'],
  AC_INITIALIZE: [u'Initialized', u'Initialize'],
  AC_INVALIDATE: [u'Invalidated', u'Invalidate'],
  AC_LIST: [u'Listed', u'List'],
  AC_MERGE: [u'Merged', u'Merge'],
  AC_MODIFY: [u'Modified', u'Modify'],
  AC_MOVE: [u'Moved', u'Move'],
  AC_PERFORM: [u'Action Performed', u'Perfrom Action'],
  AC_PRINT: [u'Printed', u'Print'],
  AC_PURGE: [u'Purged', u'Purge'],
  AC_REGISTER: [u'Registered', u'Register'],
  AC_RELABEL: [u'Relabeled', u'Relabel'],
  AC_REMOVE: [u'Removed', u'Remove'],
  AC_RENAME: [u'Renamed', u'Rename'],
  AC_REPLACE: [u'Replaced', u'Replace'],
  AC_REPORT: [u'Reported', u'Report'],
  AC_RESTORE: [u'Restored', u'Restore'],
  AC_RESUBMIT: [u'Resubmitted', u'Resubmit'],
  AC_SAVE: [u'Saved', u'Save'],
  AC_SET: [u'Set', u'Set'],
  AC_SHOW: [u'Shown', u'Show'],
  AC_SPAM: [u'Marked as Spam', u'Mark as Spam'],
  AC_SUBMIT: [u'Submitted', u'Submit'],
  AC_SYNC: [u'Synced', u'Sync'],
  AC_TRANSFER: [u'Transferred', u'Transfer'],
  AC_TRANSFER_OWNERSHIP: [u'Ownership Transferred', u'Transfer Ownership'],
  AC_TRASH: [u'Trashed', u'Trash'],
  AC_UNDELETE: [u'Undeleted', u'Undelete'],
  AC_UNTRASH: [u'Untrashed', u'Untrash'],
  AC_UPDATE: [u'Updated', u'Update'],
  AC_UPLOAD: [u'Uploaded', u'Upload'],
  AC_WATCH: [u'Watched', u'Watch'],
  AC_WIPE: [u'Wiped', u'Wipe'],
  }
#
AC_MODIFIER_TO = u'to'
AC_MODIFIER_FROM = u'from'
AC_MODIFIER_WITH = u'with'
AC_MODIFIER_WITH_CONTENT_FROM = u'with content from'
AC_PREFIX_NOT = u'Not'
AC_SUFFIX_FAILED = u'Failed'
# Keys into USER_PROPERTIES
PROPERTY_CLASS = u'clas'
PROPERTY_TITLE = u'titl'
PROPERTY_TYPE_KEYWORDS = u'tykw'
PTKW_CL_TYPE_KEYWORD = u'ctkw'
PTKW_CL_CUSTOMTYPE_KEYWORD = u'cctk'
PTKW_ATTR_TYPE_KEYWORD = u'atkw'
PTKW_ATTR_TYPE_CUSTOM_VALUE = u'atcv'
PTKW_ATTR_CUSTOMTYPE_KEYWORD = u'actk'
PTKW_KEYWORD_LIST = u'kwli'
#
PC_ADDRESSES = u'addr'
PC_ALIASES = u'alia'
PC_ARRAY = u'arry'
PC_BOOLEAN = u'bool'
PC_EMAILS = u'emai'
PC_IMS = U'ims '
PC_NAME = u'name'
PC_NOTES = u'note'
PC_SCHEMAS = u'schm'
PC_STRING = u'stri'
PC_TIME = u'time'

USER_PROPERTIES = {
  u'primaryEmail':
    {PROPERTY_CLASS: PC_STRING, PROPERTY_TITLE: u'User',},
  u'name':
    {PROPERTY_CLASS: PC_NAME, PROPERTY_TITLE: u'Name',},
  u'givenName':
    {PROPERTY_CLASS: PC_STRING, PROPERTY_TITLE: u'First Name',},
  u'familyName':
    {PROPERTY_CLASS: PC_STRING, PROPERTY_TITLE: u'Last Name',},
  u'fullName':
    {PROPERTY_CLASS: PC_STRING, PROPERTY_TITLE: u'Full Name',},
  u'password':
    {PROPERTY_CLASS: PC_STRING, PROPERTY_TITLE: u'Password',},
  u'isAdmin':
    {PROPERTY_CLASS: PC_BOOLEAN, PROPERTY_TITLE: u'Is a Super Admin',},
  u'isDelegatedAdmin':
    {PROPERTY_CLASS: PC_BOOLEAN, PROPERTY_TITLE: u'Is Delegated Admin',},
  u'agreedToTerms':
    {PROPERTY_CLASS: PC_BOOLEAN, PROPERTY_TITLE: u'Has Agreed to Terms',},
  u'ipWhitelisted':
    {PROPERTY_CLASS: PC_BOOLEAN, PROPERTY_TITLE: u'IP Whitelisted',},
  u'suspended':
    {PROPERTY_CLASS: PC_BOOLEAN, PROPERTY_TITLE: u'Account Suspended',},
  u'suspensionReason':
    {PROPERTY_CLASS: PC_STRING, PROPERTY_TITLE: u'Suspension Reason',},
  u'changePasswordAtNextLogin':
    {PROPERTY_CLASS: PC_BOOLEAN, PROPERTY_TITLE: u'Must Change Password',},
  u'id':
    {PROPERTY_CLASS: PC_STRING, PROPERTY_TITLE: u'Google Unique ID',},
  u'customerId':
    {PROPERTY_CLASS: PC_STRING, PROPERTY_TITLE: u'Customer ID',},
  u'isMailboxSetup':
    {PROPERTY_CLASS: PC_BOOLEAN, PROPERTY_TITLE: u'Mailbox is setup',},
  u'includeInGlobalAddressList':
    {PROPERTY_CLASS: PC_BOOLEAN, PROPERTY_TITLE: u'Included in GAL',},
  u'creationTime':
    {PROPERTY_CLASS: PC_TIME, PROPERTY_TITLE: u'Creation Time',},
  u'lastLoginTime':
    {PROPERTY_CLASS: PC_TIME, PROPERTY_TITLE: u'Last login time',},
  u'deletionTime':
    {PROPERTY_CLASS: PC_TIME, PROPERTY_TITLE: u'Deletion Time',},
  u'orgUnitPath':
    {PROPERTY_CLASS: PC_STRING, PROPERTY_TITLE: u'Google Org Unit Path',},
  u'thumbnailPhotoUrl':
    {PROPERTY_CLASS: PC_STRING, PROPERTY_TITLE: u'Photo URL',},
  u'addresses':
    {PROPERTY_CLASS: PC_ADDRESSES, PROPERTY_TITLE: u'Addresses',
     PROPERTY_TYPE_KEYWORDS:
       {PTKW_CL_TYPE_KEYWORD: u'type', PTKW_CL_CUSTOMTYPE_KEYWORD: u'custom',
        PTKW_ATTR_TYPE_KEYWORD: u'type', PTKW_ATTR_TYPE_CUSTOM_VALUE: u'custom', PTKW_ATTR_CUSTOMTYPE_KEYWORD: u'customType',
        PTKW_KEYWORD_LIST: [u'custom', u'home', u'other', u'work'],},},
  u'emails':
    {PROPERTY_CLASS: PC_EMAILS, PROPERTY_TITLE: u'Other Emails',
     PROPERTY_TYPE_KEYWORDS:
       {PTKW_CL_TYPE_KEYWORD: u'type', PTKW_CL_CUSTOMTYPE_KEYWORD: None,
        PTKW_ATTR_TYPE_KEYWORD: u'type', PTKW_ATTR_TYPE_CUSTOM_VALUE: u'custom', PTKW_ATTR_CUSTOMTYPE_KEYWORD: u'customType',
        PTKW_KEYWORD_LIST: [u'custom', u'home', u'other', u'work'],},},
  u'externalIds':
    {PROPERTY_CLASS: PC_ARRAY, PROPERTY_TITLE: u'External IDs',
     PROPERTY_TYPE_KEYWORDS:
       {PTKW_CL_TYPE_KEYWORD: u'type', PTKW_CL_CUSTOMTYPE_KEYWORD: None,
        PTKW_ATTR_TYPE_KEYWORD: u'type', PTKW_ATTR_TYPE_CUSTOM_VALUE: u'custom', PTKW_ATTR_CUSTOMTYPE_KEYWORD: u'customType',
        PTKW_KEYWORD_LIST: [u'account', u'customer', u'network', u'organization'],},},
  u'ims':
    {PROPERTY_CLASS: PC_IMS, PROPERTY_TITLE: u'IMs',
     PROPERTY_TYPE_KEYWORDS:
       {PTKW_CL_TYPE_KEYWORD: u'type', PTKW_CL_CUSTOMTYPE_KEYWORD: u'custom',
        PTKW_ATTR_TYPE_KEYWORD: u'type', PTKW_ATTR_TYPE_CUSTOM_VALUE: u'custom', PTKW_ATTR_CUSTOMTYPE_KEYWORD: u'customType',
        PTKW_KEYWORD_LIST: [u'custom', u'home', u'other', u'work'],},},
  u'notes':
    {PROPERTY_CLASS: PC_NOTES, PROPERTY_TITLE: u'Notes',
     PROPERTY_TYPE_KEYWORDS:
       {PTKW_CL_TYPE_KEYWORD: u'type', PTKW_CL_CUSTOMTYPE_KEYWORD: u'type',
        PTKW_ATTR_TYPE_KEYWORD: u'contentType', PTKW_ATTR_TYPE_CUSTOM_VALUE: None, PTKW_ATTR_CUSTOMTYPE_KEYWORD: None,
        PTKW_KEYWORD_LIST: [u'text_plain', u'text_html'],},},
  u'organizations':
    {PROPERTY_CLASS: PC_ARRAY, PROPERTY_TITLE: u'Organizations',
     PROPERTY_TYPE_KEYWORDS:
       {PTKW_CL_TYPE_KEYWORD: u'type', PTKW_CL_CUSTOMTYPE_KEYWORD: u'customtype',
        PTKW_ATTR_TYPE_KEYWORD: u'type', PTKW_ATTR_TYPE_CUSTOM_VALUE: u'custom', PTKW_ATTR_CUSTOMTYPE_KEYWORD: u'customType',
        PTKW_KEYWORD_LIST: [u'domain_only', u'school', u'unknown', u'work'],},},
  u'phones':
    {PROPERTY_CLASS: PC_ARRAY, PROPERTY_TITLE: u'Phones',
     PROPERTY_TYPE_KEYWORDS:
       {PTKW_CL_TYPE_KEYWORD: u'type', PTKW_CL_CUSTOMTYPE_KEYWORD: u'custom',
        PTKW_ATTR_TYPE_KEYWORD: u'type', PTKW_ATTR_TYPE_CUSTOM_VALUE: u'custom', PTKW_ATTR_CUSTOMTYPE_KEYWORD: u'customType',
        PTKW_KEYWORD_LIST: [u'custom', u'home', u'work', u'other',
                            u'home_fax', u'work_fax', u'other_fax',
                            u'mobile', u'pager',
                            u'company_main', u'assistant',
                            u'car', u'radio', u'isdn', u'callback',
                            u'telex', u'tty_tdd', u'work_mobile',
                            u'work_pager', u'main', u'grand_central'],},},
  u'relations':
    {PROPERTY_CLASS: PC_ARRAY, PROPERTY_TITLE: u'Relations',
     PROPERTY_TYPE_KEYWORDS:
       {PTKW_CL_TYPE_KEYWORD: u'type', PTKW_CL_CUSTOMTYPE_KEYWORD: None,
        PTKW_ATTR_TYPE_KEYWORD: u'type', PTKW_ATTR_TYPE_CUSTOM_VALUE: u'custom', PTKW_ATTR_CUSTOMTYPE_KEYWORD: u'customType',
        PTKW_KEYWORD_LIST: [u'spouse', u'child', u'mother',
                            u'father', u'parent', u'brother',
                            u'sister', u'friend', u'relative',
                            u'domestic_partner', u'manager', u'assistant',
                            u'referred_by', u'partner'],},},
  u'websites':
    {PROPERTY_CLASS: PC_ARRAY, PROPERTY_TITLE: u'Websites',
     PROPERTY_TYPE_KEYWORDS:
       {PTKW_CL_TYPE_KEYWORD: u'type', PTKW_CL_CUSTOMTYPE_KEYWORD: None,
        PTKW_ATTR_TYPE_KEYWORD: u'type', PTKW_ATTR_TYPE_CUSTOM_VALUE: u'custom', PTKW_ATTR_CUSTOMTYPE_KEYWORD: u'customType',
        PTKW_KEYWORD_LIST: [u'custom', u'home', u'work',
                            u'home_page', u'ftp', u'blog',
                            u'profile', u'other', u'reservations',
                            u'app_install_page'],},},
  u'customSchemas':
    {PROPERTY_CLASS: PC_SCHEMAS, PROPERTY_TITLE: u'Custom Schemas',
     PROPERTY_TYPE_KEYWORDS:
       {PTKW_CL_TYPE_KEYWORD: u'type', PTKW_CL_CUSTOMTYPE_KEYWORD: u'custom',
        PTKW_ATTR_TYPE_KEYWORD: u'type', PTKW_ATTR_TYPE_CUSTOM_VALUE: u'custom', PTKW_ATTR_CUSTOMTYPE_KEYWORD: u'customType',
        PTKW_KEYWORD_LIST: [u'custom', u'home', u'other', u'work'],},},
  u'aliases': {
    PROPERTY_CLASS: PC_ALIASES, PROPERTY_TITLE: u'Email Aliases',},
  u'nonEditableAliases': {
    PROPERTY_CLASS: PC_ALIASES, PROPERTY_TITLE: u'Non-Editable Aliases',},
  }
#
IM_PROTOCOLS = {
  PTKW_CL_TYPE_KEYWORD: u'protocol', PTKW_CL_CUSTOMTYPE_KEYWORD: u'custom_protocol',
  PTKW_ATTR_TYPE_KEYWORD: u'protocol', PTKW_ATTR_TYPE_CUSTOM_VALUE: u'custom_protocol', PTKW_ATTR_CUSTOMTYPE_KEYWORD: u'customProtocol',
  PTKW_KEYWORD_LIST: [u'custom_protocol', u'aim', u'gtalk', u'icq', u'jabber', u'msn', u'net_meeting', u'qq', u'skype', u'xmpp', u'yahoo']
  }

# These values can be translated into other languages
PHRASE_ACCESS_FORBIDDEN = u'Access Forbidden'
PHRASE_ACTION_APPLIED = u'Action Applied'
PHRASE_ADMIN_STATUS_CHANGED_TO = u'Admin Status Changed to'
PHRASE_ALL = u'All'
PHRASE_ALREADY_EXISTS_USE_MERGE_ARGUMENT = u'Already exists; use the "merge" argument to merge the labels'
PHRASE_AS = u'as'
PHRASE_AUTHORIZED = u'Authorized'
PHRASE_BAD_REQUEST = u'Bad Request'
PHRASE_CAN_NOT_BE_DOWNLOADED = u'Can not be downloaded'
PHRASE_CAN_NOT_CHANGE_OWNER_ACL = u'Can not change owner ACL'
PHRASE_CHECKING = u'Checking'
PHRASE_COMPLETE = u'Complete'
PHRASE_CONTAINS_AT_LEAST_1_ITEM = u'Contains at least 1 item'
PHRASE_COUNT_N_EXCEEDS_MAX_TO_PROCESS_M = u'Count {0} exceeds maximum to {1} {2}'
PHRASE_DATA_UPLOADED_TO_DRIVE_FILE = u'Data uploaded to Drive File'
PHRASE_DELEGATE_ACCESS_TO = u'Delegate Access to'
PHRASE_DENIED = u'DENIED'
PHRASE_DIRECTLY_IN_THE = u' directly in the {0}'
PHRASE_DOES_NOT_EXIST = u'Does not exist'
PHRASE_DOES_NOT_EXIST_OR_HAS_INVALID_FORMAT = u'Does not exist or has invalid format'
PHRASE_DOES_NOT_EXIST_OR_NOT_ALLOWED = u'Does not exist or not allowed'
PHRASE_DOMAIN_NOT_VERIFIED_SECONDARY = u'Domain is not a verified secondary domain'
PHRASE_DO_NOT_EXIST = u'Do not exist'
PHRASE_DUPLICATE = u'Duplicate'
PHRASE_EITHER = u'Either'
PHRASE_ENTITY_DOES_NOT_EXIST = u'{0} does not exist'
PHRASE_ERROR = u'error'
PHRASE_EXPECTED = u'Expected'
PHRASE_FAILED_TO_PARSE_AS_JSON = u'Failed to parse as JSON'
PHRASE_FIELD_NOT_FOUND_IN_SCHEMA = u'Field {0} not found in schema {1}'
PHRASE_FINISHED = u'Finished'
PHRASE_FOR = u'for'
PHRASE_FORMAT_NOT_AVAILABLE = u'Format ({0}) not available'
PHRASE_FORMAT_NOT_DOWNLOADABLE = u'Format not downloadable'
PHRASE_FROM = u'From'
PHRASE_GETTING = u'Getting'
PHRASE_GETTING_ALL = u'Getting all'
PHRASE_GOOGLE_EARLIEST_REPORT_TIME = u'Google earliest report time'
PHRASE_GOT = u'Got'
PHRASE_HAS_CHILD_ORGS = 'Has child {0}'
PHRASE_INVALID = u'Invalid'
PHRASE_INVALID_ALIAS = u'Invalid Alias'
PHRASE_INVALID_CUSTOMER_ID = u'Invalid Customer ID'
PHRASE_INVALID_DOMAIN = u'Invalid Domain'
PHRASE_INVALID_PATH = u'Invalid Path'
PHRASE_INVALID_QUERY = u'Invalid Query'
PHRASE_INVALID_REQUEST = u'Invalid Request'
PHRASE_INVALID_ROLE = u'Invalid Role'
PHRASE_INVALID_SCHEMA_VALUE = u'Invalid Schema Value'
PHRASE_INVALID_SCOPE = u'Invalid Scope'
PHRASE_INVALID_SITE = u'Invalid Site ({0}), must match pattern ({1})'
PHRASE_IS_REQD_TO_CHG_PWD_NO_DELEGATION = u'is required to change password at next login. You must change password or clear changepassword flag for delegation.'
PHRASE_IS_SUSPENDED_NO_DELEGATION = u'is suspended. You must unsuspend for delegation.'
PHRASE_LABELS_NOT_FOUND = u'Labels ({0}) not found'
PHRASE_LIST = u'List'
PHRASE_LOOKING_UP_GOOGLE_UNIQUE_ID = u'Looking up Google Unique ID'
PHRASE_MARKED_AS = u'Marked as'
PHRASE_MAXIMUM_OF = u'maximum of'
PHRASE_MATCHED_THE_FOLLOWING = u'Matched the following'
PHRASE_MAY_TAKE_SOME_TIME_ON_A_LARGE = u'may take some time on a large'
PHRASE_NESTED_LOOP_CMD_NOT_ALLOWED = u'Command can not be nested.'
PHRASE_NEW_OWNER_MUST_DIFFER_FROM_OLD_OWNER = u'New owner must differ from old owner'
PHRASE_NON_BLANK = u'Non-blank'
PHRASE_NON_EMPTY = u'Non-empty'
PHRASE_NOT_A = u'Not a'
PHRASE_NOT_ALLOWED = u'Not Allowed'
PHRASE_NOT_FOUND = u'Not Found'
PHRASE_NOW_THE_PRIMARY_DOMAIN = u'Now the primary domain'
PHRASE_NO_ENTITIES_MATCHED = u'No {0} matched'
PHRASE_NO_FILTER_CRITERIA = U'No {0} criteria specified'
PHRASE_NO_FILTER_ACTIONS = U'No {0} actions specified'
PHRASE_NO_LABELS_MATCH = u'No Labels match'
PHRASE_NO_MESSAGES_WITH_LABEL = u'No Messages with Label'
PHRASE_NO_PRINT_JOBS = u'No Print Jobs'
PHRASE_NOT_A_GUARDIAN_OR_INVITATION = 'Not a Guardian or Guardian Invitation'
PHRASE_NOT_A_GUARDIAN_INVITATION_NOT_PENDING = 'Not a Guardian and Guardian Invitation status is not PENDING, '
PHRASE_NOT_REQUESTED = u'Not requested'
PHRASE_ONLY_ONE_OWNER_ALLOWED = u'Only one owner allowed'
PHRASE_OR = u'or'
PHRASE_PATH_NOT_AVAILABLE = u'Path not available'
PHRASE_PLEASE_SELECT_USER_TO_UNDELETE = u'Please select the correct one to undelete and specify with "gam undelete user uid:<uid>"'
PHRASE_SCHEMA_WOULD_HAVE_NO_FIELDS = u'{0} would have no {1}'
PHRASE_SELECTED = u'Selected'
PHRASE_SERVICE_NOT_APPLICABLE = u'Service not applicable/Does not exist'
PHRASE_STARTING_N_WORKER_THREADS = u'Starting {0} worker threads...\n'
PHRASE_STARTING_THREAD = u'Starting thread'
PHRASE_THAT_MATCHED_QUERY = u'that matched query'
PHRASE_THAT_MATCH_QUERY = u'that match query'
PHRASE_TO = u'To'
PHRASE_UNKNOWN = u'Unknown'
PHRASE_UNKNOWN_COMMAND_SELECTOR = u'Unknown command or selector'
PHRASE_USE_DOIT_ARGUMENT_TO_PERFORM_ACTION = u'Use the "doit" argument to perform action'
PHRASE_USE_RECURSIVE_ARGUMENT_TO_COPY_FOLDERS = u'Use "recursive" argument to copy folders'
PHRASE_USER_IN_OTHER_DOMAIN = '{0}: {1} in other domain.'
PHRASE_WAITING_FOR_PROCESSES_TO_COMPLETE = u'Waiting for running processes to finish before proceeding...'
PHRASE_WITH = u'with'
PHRASE_WOULD_MAKE_MEMBERSHIP_CYCLE = u'Would make membership cycle'

MESSAGE_BATCH_CSV_LOOP_DASH_DEBUG_INCOMPATIBLE = u'"gam {0} - ..." is not compatible with debugging. Disable debugging by setting debug_level = 0 in gam.cfg'
MESSAGE_API_ACCESS_DENIED = u'API access Denied.\nPlease make sure the Client ID: {0} is authorized for the appropriate scopes\nSee: {1}'
MESSAGE_CSV_DATA_ALREADY_SAVED = u'CSV data already saved'
MESSAGE_GAM_EXITING_FOR_UPDATE = u'GAM is now exiting so that you can overwrite this old version with the latest release'
MESSAGE_GAM_OUT_OF_MEMORY = u'GAM has run out of memory. If this is a large Google Apps instance, you should use a 64-bit version of GAM on Windows or a 64-bit version of Python on other systems.'
MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS = u'Header "{0}" not found in CSV headers of "{1}".'
MESSAGE_HIT_CONTROL_C_TO_UPDATE = u'\n\nHit CTRL+C to visit the GAM website and download the latest release or wait 15 seconds continue with this boring old version. GAM won\'t bother you with this announcement for 1 week or you can turn off update checks by setting no_update_check = true in gam.cfg'
MESSAGE_INSUFFICIENT_PERMISSIONS_TO_PERFORM_TASK = u'Insufficient permissions to perform this task'
MESSAGE_INVALID_JSON = u'The file {0} has an invalid format.'
MESSAGE_INVALID_TIME_RANGE = u'{0} {1} must be greater than/equal to {2} {3}'
MESSAGE_DATA_FIELD_MISMATCH = u'datafield {0} does not match saved datafield {1}'
MESSAGE_NO_CSV_FILE_DATA_SAVED = u'No CSV file data saved'
MESSAGE_NO_CSV_HEADERS_IN_FILE = u'No headers found in CSV file "{0}".'
MESSAGE_NO_DISCOVERY_INFORMATION = u'No online discovery doc and {0} does not exist locally'
MESSAGE_NO_PYTHON_SSL = u'You don\'t have the Python SSL module installed so we can\'t verify SSL Certificates. You can fix this by installing the Python SSL module or you can live on the edge and turn SSL validation off by setting no_verify_ssl = true in gam.cfg'
MESSAGE_NO_SCOPES_FOR_API = u'There are no scopes authorized for the {0}'
MESSAGE_NO_TRANSFER_LACK_OF_DISK_SPACE = u'Cowardly refusing to perform migration due to lack of target drive space.'
MESSAGE_REQUEST_COMPLETED_NO_FILES = u'Request completed but no results/files were returned, try requesting again'
MESSAGE_REQUEST_NOT_COMPLETE = u'Request needs to be completed before downloading, current status is: {0}'
MESSAGE_RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET = u'Results are too large for Google Spreadsheets. Uploading as a regular CSV file.'
MESSAGE_SERVICE_NOT_APPLICABLE = u'Service not applicable for this address: {0}'
MESSAGE_CHECK_VACATION_DATES = u'Check vacation dates, end date must be greater than/equal to start date'
MESSAGE_WIKI_INSTRUCTIONS_OAUTH2SERVICE_JSON = u'Please follow the instructions at this site to setup a Service account.'

# Error message types; keys into ARGUMENT_ERROR_NAMES; arbitrary values but must be unique
ARGUMENTS_MUTUALLY_EXCLUSIVE = u'muex'
ARGUMENT_BLANK = u'blnk'
ARGUMENT_EMPTY = u'empt'
ARGUMENT_EXTRANEOUS = u'extr'
ARGUMENT_INVALID = u'inva'
ARGUMENT_MISSING = u'miss'
# ARGUMENT_ERROR_NAMES[0] is plural,ARGUMENT_ERROR_NAMES[1] is singular
# These values can be translated into other languages
ARGUMENT_ERROR_NAMES = {
  ARGUMENTS_MUTUALLY_EXCLUSIVE: [u'Mutually exclusive arguments', u'Mutually exclusive arguments'],
  ARGUMENT_BLANK: [u'Blank arguments', u'Blank argument'],
  ARGUMENT_EMPTY: [u'Empty arguments', u'Empty argument'],
  ARGUMENT_EXTRANEOUS: [u'Extra arguments', u'Extra argument'],
  ARGUMENT_INVALID: [u'Invalid arguments', u'Invalid argument'],
  ARGUMENT_MISSING: [u'Missing arguments', u'Missing argument'],
  }
# Program return codes
UNKNOWN_ERROR_RC = 1
USAGE_ERROR_RC = 2
SOCKET_ERROR_RC = 3
GOOGLE_API_ERROR_RC = 4
NETWORK_ERROR_RC = 5
FILE_ERROR_RC = 6
MEMORY_ERROR_RC = 7
KEYBOARD_INTERRUPT_RC = 8
HTTP_ERROR_RC = 9
NO_DISCOVERY_INFORMATION_RC = 11
API_ACCESS_DENIED_RC = 12
CONFIG_ERROR_RC = 13
CERTIFICATE_VALIDATION_UNSUPPORTED_RC = 14
NO_SCOPES_FOR_API_RC = 15
CLIENT_SECRETS_JSON_REQUIRED_RC = 16
OAUTH2SERVICE_JSON_REQUIRED_RC = 16
OAUTH2_TXT_REQUIRED_RC = 16
INVALID_JSON_RC = 17
AUTHENTICATION_TOKEN_REFRESH_ERROR_RC = 18
HARD_ERROR_RC = 19
# Information
ENTITY_IS_A_USER_RC = 20
ENTITY_IS_A_USER_ALIAS_RC = 21
ENTITY_IS_A_GROUP_RC = 22
ENTITY_IS_A_GROUP_ALIAS_RC = 23
# Warnings/Errors
AC_FAILED_RC = 50
AC_NOT_PERFORMED_RC = 51
BAD_REQUEST_RC = 53
DATA_NOT_AVALIABLE_RC = 55
ENTITY_DOES_NOT_EXIST_RC = 56
ENTITY_DUPLICATE_RC = 57
ENTITY_IS_NOT_AN_ALIAS_RC = 58
ENTITY_IS_UKNOWN_RC = 59
NO_ENTITIES_FOUND = 60
INVALID_DOMAIN_RC = 61
INVALID_DOMAIN_VALUE_RC = 62
INVALID_TOKEN_RC = 63
JSON_LOADS_ERROR_RC = 64
MULTIPLE_DELETED_USERS_FOUND_RC = 65
NO_CSV_HEADERS_ERROR_RC = 66
INSUFFICIENT_PERMISSIONS_RC = 67
REQUEST_COMPLETED_NO_RESULTS_RC = 71
REQUEST_NOT_COMPLETED_RC = 72
SERVICE_NOT_APPLICABLE_RC = 73
TARGET_DRIVE_SPACE_ERROR_RC = 74
USER_REQUIRED_TO_CHANGE_PASSWORD_ERROR_RC = 75
USER_SUSPENDED_ERROR_RC = 76
#
def convertUTF8(data):
  if isinstance(data, str):
    return data
  if isinstance(data, unicode):
    return data.encode(GM_Globals[GM_SYS_ENCODING], 'replace')
  if isinstance(data, collections.Mapping):
    return dict(map(convertUTF8, data.iteritems()))
  if isinstance(data, collections.Iterable):
    return type(data)(map(convertUTF8, data))
  return data

from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint

class _DeHTMLParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.__text = []

  def handle_data(self, data):
    self.__text.append(data)

  def handle_charref(self, name):
    self.__text.append(unichr(int(name[1:], 16)) if name.startswith('x') else unichr(int(name)))

  def handle_entityref(self, name):
    self.__text.append(unichr(name2codepoint[name]))

  def handle_starttag(self, tag, attrs):
    if tag == 'p':
      self.__text.append('\n\n')
    elif tag == 'br':
      self.__text.append('\n')
    elif tag == 'a':
      for attr in attrs:
        if attr[0] == 'href':
          self.__text.append('({0}) '.format(attr[1]))
          break
    elif tag == 'div':
      if not attrs:
        self.__text.append('\n')
    elif tag in ['http:', 'https']:
      self.__text.append(' ({0}//{1}) '.format(tag, attrs[0][0]))

  def handle_startendtag(self, tag, attrs):
    if tag == 'br':
      self.__text.append('\n\n')

  def text(self):
    return re.sub(r'\n{2}\n+', '\n\n', re.sub(r'\n +', '\n', ''.join(self.__text))).strip()

def dehtml(text):
  try:
    parser = _DeHTMLParser()
    parser.feed(text.encode(u'utf-8'))
    parser.close()
    return parser.text()
  except:
    from traceback import print_exc
    print_exc(file=sys.stderr)
    return text

# Concatenate list members, any item containing spaces is enclosed in ''
def makeQuotedList(items):
  qstr = u''
  for item in items:
    if item and (item.find(u' ') == -1) and (item.find(u',') == -1):
      qstr += item
    else:
      qstr += u"'"+item+u"'"
    qstr += u' '
  return qstr[:-1] if len(qstr) > 0 else u''

# Format a key value list
#   key, value	-> "key: value" + ", " if not last item
#   key, ''	-> "key:" + ", " if not last item
#   key, None	-> "key" + " " if not last item
def formatKeyValueList(prefixStr, kvList, suffixStr):
  msg = prefixStr
  i = 0
  l = len(kvList)
  while i < l:
    if isinstance(kvList[i], (bool, int)):
      msg += str(kvList[i])
    else:
      msg += kvList[i]
    i += 1
    if i < l:
      val = kvList[i]
      if (val is not None) or (i == l-1):
        msg += u':'
        if (val is not None) and val != u'':
          msg += u' '
          if isinstance(val, (bool, int)):
            msg += str(val)
          else:
            msg += val
        i += 1
        if i < l:
          msg += u', '
      else:
        i += 1
        if i < l:
          msg += u' '
  msg += suffixStr
  return msg.encode(GM_Globals[GM_SYS_ENCODING], 'replace')

def indentMultiLineText(message, n=0):
  n += GM_Globals[GM_INDENT_LEVEL]
  return message.replace(u'\n', u'\n{0}'.format(INDENT_SPACES_PER_LEVEL*n)).rstrip()

def resetIndentLevel():
  GM_Globals[GM_INDENT_LEVEL] = 0
  GM_Globals[GM_INDENT_SPACES] = INDENT_SPACES_PER_LEVEL*GM_Globals[GM_INDENT_LEVEL]

def incrementIndentLevel():
  GM_Globals[GM_INDENT_LEVEL] += 1
  GM_Globals[GM_INDENT_SPACES] = INDENT_SPACES_PER_LEVEL*GM_Globals[GM_INDENT_LEVEL]

def decrementIndentLevel():
  GM_Globals[GM_INDENT_LEVEL] -= 1
  GM_Globals[GM_INDENT_SPACES] = INDENT_SPACES_PER_LEVEL*GM_Globals[GM_INDENT_LEVEL]

# Error exits
def setSysExitRC(sysRC):
  GM_Globals[GM_SYSEXITRC] = sysRC

def printErrorMessage(sysRC, message):
  setSysExitRC(sysRC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES], [ERROR, message], u'\n'))

def stderrErrorMsg(message):
  sys.stderr.write(convertUTF8(u'\n{0}{1}\n'.format(ERROR_PREFIX, message)))

def stderrWarningMsg(message):
  sys.stderr.write(convertUTF8(u'\n{0}{1}\n'.format(WARNING_PREFIX, message)))

def systemErrorExit(sysRC, message):
  if message:
    stderrErrorMsg(message)
  sys.exit(sysRC)

# Something's wrong with CustomerID
def accessErrorMessage(cd):
  try:
    callGAPI(cd.customers(), u'get',
             throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
             customerKey=GC_Values[GC_CUSTOMER_ID], fields=u'id')
  except GAPI_badRequest:
    return formatKeyValueList(u'',
                              [singularEntityName(EN_CUSTOMER_ID), GC_Values[GC_CUSTOMER_ID],
                               PHRASE_INVALID],
                              u'')
  except GAPI_resourceNotFound:
    return formatKeyValueList(u'',
                              [singularEntityName(EN_CUSTOMER_ID), GC_Values[GC_CUSTOMER_ID],
                               PHRASE_DOES_NOT_EXIST],
                              u'')
  except GAPI_forbidden:
    return formatKeyValueList(u'',
                              [singularEntityName(EN_CUSTOMER_ID), GC_Values[GC_CUSTOMER_ID],
                               singularEntityName(EN_DOMAIN), GC_Values[GC_DOMAIN],
                               singularEntityName(EN_USER), GM_Globals[GM_ADMIN],
                               PHRASE_ACCESS_FORBIDDEN],
                              u'')
  return None

def accessErrorExit(cd):
  systemErrorExit(INVALID_DOMAIN_RC, accessErrorMessage(cd or buildGAPIObject(GAPI_DIRECTORY_API)))

def APIAccessDeniedExit():
#  systemErrorExit(API_ACCESS_DENIED_RC, MESSAGE_API_ACCESS_DENIED.format(GM_Globals[GM_OAUTH2_CLIENT_ID],
#                                                                         u','.join(GM_Globals[GM_CURRENT_API_SCOPES])))
  systemErrorExit(API_ACCESS_DENIED_RC, MESSAGE_API_ACCESS_DENIED.format(GM_Globals[GM_OAUTH2_CLIENT_ID], GAM_WIKI_CREATE_CLIENT_SECRETS))

def checkEntityDNEorAccessErrorExit(cd, entityType, entityName, i=0, count=0):
  message = accessErrorMessage(cd)
  if message:
    systemErrorExit(INVALID_DOMAIN_RC, message)
  entityDoesNotExistWarning(entityType, entityName, i, count)

def checkEntityAFDNEorAccessErrorExit(cd, entityType, entityName, i=0, count=0):
  message = accessErrorMessage(cd)
  if message:
    systemErrorExit(INVALID_DOMAIN_RC, message)
  entityActionFailedWarning(entityType, entityName, PHRASE_DOES_NOT_EXIST, i, count)

def checkEntityItemValueAFDNEorAccessErrorExit(cd, entityType, entityName, itemType, itemValue, i=0, count=0):
  message = accessErrorMessage(cd)
  if message:
    systemErrorExit(INVALID_DOMAIN_RC, message)
  entityItemValueActionFailedWarning(entityType, entityName, itemType, itemValue, PHRASE_DOES_NOT_EXIST, i, count)

def invalidJSONExit(fileName):
  systemErrorExit(INVALID_JSON_RC, MESSAGE_INVALID_JSON.format(fileName))

def noPythonSSLExit():
  systemErrorExit(CERTIFICATE_VALIDATION_UNSUPPORTED_RC, MESSAGE_NO_PYTHON_SSL)

def usageErrorExit(message, extraneous=False):
  if extraneous:
    sys.stderr.write(convertUTF8(u'Command: {0} >>>{1}<<<\n'.format(makeQuotedList(CL_argv[:CL_argvI]),
                                                                    makeQuotedList(CL_argv[CL_argvI:]))))
  elif CL_argvI < CL_argvLen:
    sys.stderr.write(convertUTF8(u'Command: {0} >>>{1}<<< {2}\n'.format(makeQuotedList(CL_argv[:CL_argvI]),
                                                                        makeQuotedList([CL_argv[CL_argvI]]),
                                                                        makeQuotedList(CL_argv[CL_argvI+1:]))))
  else:
    sys.stderr.write(convertUTF8(u'Command: {0} >>><<<\n'.format(makeQuotedList(CL_argv))))
  stderrErrorMsg(message)
  sys.stderr.write(u'Help: Documentation is at {0}\n'.format(GAM_WIKI))
  sys.exit(USAGE_ERROR_RC)

def badEntitiesExit(entityType, count, phraseList, backupArg=False):
  if backupArg:
    putArgumentBack()
  usageErrorExit(u'{0} {1} {2}'.format(count, chooseEntityName(entityType, count), phraseList[count == 1]))

def csvFieldErrorExit(fieldName, fieldNames, backupArg=False, checkForCharset=False):
  if backupArg:
    putArgumentBack()
    if checkForCharset and CL_argv[CL_argvI-1] == u'charset':
      putArgumentBack()
      putArgumentBack()
  usageErrorExit(MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS.format(fieldName, u','.join(fieldNames)))

def csvDataAlreadySavedErrorExit():
  putArgumentBack()
  usageErrorExit(MESSAGE_CSV_DATA_ALREADY_SAVED)

# The last thing shown is unknown
def unknownArgumentExit():
  putArgumentBack()
  usageErrorExit(ARGUMENT_ERROR_NAMES[ARGUMENT_INVALID][1])

# Argument describes what's expected
def expectedArgumentExit(problem, argument):
  usageErrorExit(u'{0}: {1} <{2}>'.format(problem, PHRASE_EXPECTED, argument))

def blankArgumentExit(argument):
  expectedArgumentExit(ARGUMENT_ERROR_NAMES[ARGUMENT_BLANK][1], u'{0} {1}'.format(PHRASE_NON_BLANK, argument))

def emptyArgumentExit(argument):
  expectedArgumentExit(ARGUMENT_ERROR_NAMES[ARGUMENT_EMPTY][1], u'{0} {1}'.format(PHRASE_NON_EMPTY, argument))

def invalidArgumentExit(argument):
  expectedArgumentExit(ARGUMENT_ERROR_NAMES[ARGUMENT_INVALID][1], argument)

def missingArgumentExit(argument):
  expectedArgumentExit(ARGUMENT_ERROR_NAMES[ARGUMENT_MISSING][1], argument)

# Choices is the valid set of choices that was expected
def formatChoiceList(choices):
  choiceList = choices.keys() if isinstance(choices, dict) else choices
  if len(choiceList) <= 5:
    return u'|'.join(choiceList)
  else:
    return u'|'.join(sorted(choiceList))

def invalidChoiceExit(choices):
  expectedArgumentExit(ARGUMENT_ERROR_NAMES[ARGUMENT_INVALID][1], formatChoiceList(choices))

def missingChoiceExit(choices):
  expectedArgumentExit(ARGUMENT_ERROR_NAMES[ARGUMENT_MISSING][1], formatChoiceList(choices))

def mutuallyExclusiveChoiceExit(choices):
  expectedArgumentExit(ARGUMENT_ERROR_NAMES[ARGUMENTS_MUTUALLY_EXCLUSIVE][1], formatChoiceList(choices))

# Initialize arguments
def initializeArguments(args):
  global CL_argv, CL_argvI, CL_argvLen
  CL_argv = args[:]
  CL_argvI = 1
  CL_argvLen = len(CL_argv)

# Put back last argument
def putArgumentBack():
  global CL_argvI
  CL_argvI -= 1

# Check if argument present
def checkArgumentPresent(choices, required=False):
  global CL_argvI
  if CL_argvI < CL_argvLen:
    choice = CL_argv[CL_argvI].strip().lower()
    if choice:
      if choice in choices:
        CL_argvI += 1
        return choice
    if not required:
      return False
    invalidChoiceExit(choices)
  elif not required:
    return False
  missingChoiceExit(choices)

# Peek to see if argument present, do not advance
def peekArgumentPresent(choices):
  if CL_argvI < CL_argvLen:
    choice = CL_argv[CL_argvI].strip().lower()
    if choice and choice in choices:
      return True
  return False

# Check that there are no extraneous arguments at the end of the command line
def checkForExtraneousArguments():
  if CL_argvI < CL_argvLen:
    usageErrorExit(ARGUMENT_ERROR_NAMES[ARGUMENT_EXTRANEOUS][[0, 1][CL_argvI+1 == CL_argvLen]], extraneous=True)

# Get an argument, downshift, delete underscores
def getArgument():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    argument = CL_argv[CL_argvI].lower()
    if argument:
      CL_argvI += 1
      return argument.replace(u'_', u'')
  missingArgumentExit(OB_ARGUMENT)

def getBoolean():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    boolean = CL_argv[CL_argvI].strip().lower()
    if boolean in TRUE_VALUES:
      CL_argvI += 1
      return True
    if boolean in FALSE_VALUES:
      CL_argvI += 1
      return False
    invalidChoiceExit(TRUE_FALSE)
  missingChoiceExit(TRUE_FALSE)

DEFAULT_CHOICE = u'defaultChoice'
CHOICE_ALIASES = u'choiceAliases'
MAP_CHOICE = u'mapChoice'
NO_DEFAULT = u'NoDefault'

def getChoice(choices, **opts):
  global CL_argvI
  if CL_argvI < CL_argvLen:
    choice = CL_argv[CL_argvI].strip().lower()
    if choice:
      if choice in opts.get(CHOICE_ALIASES, []):
        choice = opts[CHOICE_ALIASES][choice]
      if choice not in choices:
        choice = choice.replace(u'_', u'')
        if choice in opts.get(CHOICE_ALIASES, []):
          choice = opts[CHOICE_ALIASES][choice]
      if choice in choices:
        CL_argvI += 1
        return choice if not opts.get(MAP_CHOICE, False) else choices[choice]
    if opts.get(DEFAULT_CHOICE, NO_DEFAULT) != NO_DEFAULT:
      return opts[DEFAULT_CHOICE]
    invalidChoiceExit(choices)
  elif opts.get(DEFAULT_CHOICE, NO_DEFAULT) != NO_DEFAULT:
    return opts[DEFAULT_CHOICE]
  missingChoiceExit(choices)

COLORHEX_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')
COLORHEX_FORMAT_REQUIRED = u'#ffffff'

def getColorHexAttribute():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    tg = COLORHEX_PATTERN.match(CL_argv[CL_argvI].strip())
    if tg:
      CL_argvI += 1
      return tg.group(0)
    invalidArgumentExit(COLORHEX_FORMAT_REQUIRED)
  missingArgumentExit(COLORHEX_FORMAT_REQUIRED)

def removeCourseIdScope(courseId):
  if courseId.startswith(u'd:'):
    return courseId[2:]
  return courseId

def addCourseIdScope(courseId):
  if not courseId.isdigit() and courseId[:2] != u'd:':
    return u'd:{0}'.format(courseId)
  return courseId

def getCourseId():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    courseId = CL_argv[CL_argvI]
    if courseId:
      CL_argvI += 1
      return addCourseIdScope(courseId)
  missingArgumentExit(OB_COURSE_ID)

def getCourseAlias():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    courseAlias = CL_argv[CL_argvI]
    if courseAlias:
      CL_argvI += 1
      if courseAlias[:2] != u'd:':
        return u'd:{0}'.format(courseAlias)
      return courseAlias
  missingArgumentExit(OB_COURSE_ALIAS)

UID_PATTERN = re.compile(r'u?id: ?(.*)')

def validateEmailAddressOrUID(emailAddressOrUID):
  cg = UID_PATTERN.match(emailAddressOrUID)
  if cg:
    return cg.group(1)
  return emailAddressOrUID.find(u'@') != 0 and emailAddressOrUID.count(u'@') <= 1

# Normalize user/group email address/uid
# uid:12345abc -> 12345abc
# foo -> foo@domain
# foo@ -> foo@domain
# foo@bar.com -> foo@bar.com
# @domain -> domain
def normalizeEmailAddressOrUID(emailAddressOrUID, noUid=False):
  if not noUid:
    cg = UID_PATTERN.match(emailAddressOrUID)
    if cg:
      return cg.group(1)
  atLoc = emailAddressOrUID.find(u'@')
  if atLoc == 0:
    return emailAddressOrUID[1:].lower()
  if (atLoc == -1) or (atLoc == len(emailAddressOrUID)-1) and GC_Values[GC_DOMAIN]:
    if atLoc == -1:
      emailAddressOrUID = u'{0}@{1}'.format(emailAddressOrUID, GC_Values[GC_DOMAIN])
    else:
      emailAddressOrUID = u'{0}{1}'.format(emailAddressOrUID, GC_Values[GC_DOMAIN])
  return emailAddressOrUID.lower()

def getEmailAddress(noUid=False, emptyOK=False, optional=False):
  global CL_argvI
  if CL_argvI < CL_argvLen:
    emailAddress = CL_argv[CL_argvI].strip().lower()
    if emailAddress:
      cg = UID_PATTERN.match(emailAddress)
      if cg:
        if not noUid:
          if cg.group(1):
            CL_argvI += 1
            return cg.group(1)
        else:
          invalidArgumentExit(u'name@domain')
      else:
        atLoc = emailAddress.find(u'@')
        if atLoc == -1:
          if GC_Values[GC_DOMAIN]:
            emailAddress = u'{0}@{1}'.format(emailAddress, GC_Values[GC_DOMAIN])
          CL_argvI += 1
          return emailAddress
        if atLoc != 0:
          if (atLoc == len(emailAddress)-1) and GC_Values[GC_DOMAIN]:
            emailAddress = u'{0}{1}'.format(emailAddress, GC_Values[GC_DOMAIN])
          CL_argvI += 1
          return emailAddress
        invalidArgumentExit(u'name@domain')
    if optional:
      CL_argvI += 1
      return None
    elif emptyOK:
      CL_argvI += 1
      return u''
  elif optional:
    return None
  missingArgumentExit([OB_EMAIL_ADDRESS_OR_UID, OB_EMAIL_ADDRESS][noUid])

def getPermissionId():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    emailAddress = CL_argv[CL_argvI].strip().lower()
    if emailAddress:
      if emailAddress[:3] == u'id:':
        CL_argvI += 1
        return (False, CL_argv[CL_argvI-1].strip()[3:])
      atLoc = emailAddress.find(u'@')
      if atLoc == -1:
        if emailAddress == u'anyone':
          CL_argvI += 1
          return (False, emailAddress)
        if emailAddress == u'anyonewithlink':
          CL_argvI += 1
          return (False, u'anyoneWithLink')
        if GC_Values[GC_DOMAIN]:
          emailAddress = u'{0}@{1}'.format(emailAddress, GC_Values[GC_DOMAIN])
        CL_argvI += 1
        return (True, emailAddress)
      if atLoc != 0:
        if (atLoc == len(emailAddress)-1) and GC_Values[GC_DOMAIN]:
          emailAddress = u'{0}{1}'.format(emailAddress, GC_Values[GC_DOMAIN])
        CL_argvI += 1
        return (True, emailAddress)
      invalidArgumentExit(u'name@domain')
  missingArgumentExit(OB_PERMISSION_ID)

# Products/SKUs
#
GOOGLE_APPS_PRODUCT = u'Google-Apps'
GOOGLE_COORDINATE_PRODUCT = u'Google-Coordinate'
GOOGLE_DRIVE_STORAGE_PRODUCT = u'Google-Drive-storage'
GOOGLE_VAULT_PRODUCT = u'Google-Vault'

GOOGLE_PRODUCTS = [
  GOOGLE_APPS_PRODUCT,
  GOOGLE_COORDINATE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_VAULT_PRODUCT,
  ]

GOOGLE_APPS_FOR_BUSINESS_SKU = GOOGLE_APPS_PRODUCT+u'-For-Business'
GOOGLE_APPS_FOR_POSTINI_SKU = GOOGLE_APPS_PRODUCT+u'-For-Postini'
GOOGLE_APPS_LITE_SKU = GOOGLE_APPS_PRODUCT+u'-Lite'
GOOGLE_APPS_UNLIMITED_SKU = GOOGLE_APPS_PRODUCT+u'-Unlimited'
GOOGLE_COORDINATE_SKU = GOOGLE_COORDINATE_PRODUCT
GOOGLE_VAULT_SKU = GOOGLE_VAULT_PRODUCT
GOOGLE_VAULT_FORMER_EMPLOYEE_SKU = GOOGLE_VAULT_PRODUCT+u'-Former-Employee'
GOOGLE_DRIVE_STORAGE_20GB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-20GB'
GOOGLE_DRIVE_STORAGE_50GB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-50GB'
GOOGLE_DRIVE_STORAGE_200GB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-200GB'
GOOGLE_DRIVE_STORAGE_400GB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-400GB'
GOOGLE_DRIVE_STORAGE_1TB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-1TB'
GOOGLE_DRIVE_STORAGE_2TB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-2TB'
GOOGLE_DRIVE_STORAGE_4TB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-4TB'
GOOGLE_DRIVE_STORAGE_8TB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-8TB'
GOOGLE_DRIVE_STORAGE_16TB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-16TB'

GOOGLE_USER_SKUS = {
  GOOGLE_APPS_FOR_BUSINESS_SKU: GOOGLE_APPS_PRODUCT,
  GOOGLE_APPS_FOR_POSTINI_SKU: GOOGLE_APPS_PRODUCT,
  GOOGLE_APPS_LITE_SKU: GOOGLE_APPS_PRODUCT,
  GOOGLE_APPS_UNLIMITED_SKU: GOOGLE_APPS_PRODUCT,
  GOOGLE_VAULT_SKU: GOOGLE_VAULT_PRODUCT,
  GOOGLE_VAULT_FORMER_EMPLOYEE_SKU: GOOGLE_VAULT_PRODUCT,
  }
GOOGLE_SKUS = {
  GOOGLE_APPS_FOR_BUSINESS_SKU: GOOGLE_APPS_PRODUCT,
  GOOGLE_APPS_FOR_POSTINI_SKU: GOOGLE_APPS_PRODUCT,
  GOOGLE_APPS_LITE_SKU: GOOGLE_APPS_PRODUCT,
  GOOGLE_APPS_UNLIMITED_SKU: GOOGLE_APPS_PRODUCT,
  GOOGLE_COORDINATE_SKU: GOOGLE_COORDINATE_PRODUCT,
  GOOGLE_VAULT_SKU: GOOGLE_VAULT_PRODUCT,
  GOOGLE_VAULT_FORMER_EMPLOYEE_SKU: GOOGLE_VAULT_PRODUCT,
  GOOGLE_DRIVE_STORAGE_20GB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_50GB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_200GB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_400GB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_1TB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_2TB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_4TB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_8TB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_16TB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  }

GOOGLE_SKU_CHOICES_MAP = {
  u'apps': GOOGLE_APPS_FOR_BUSINESS_SKU,
  u'gafb': GOOGLE_APPS_FOR_BUSINESS_SKU,
  u'gafw': GOOGLE_APPS_FOR_BUSINESS_SKU,
  u'gams': GOOGLE_APPS_FOR_POSTINI_SKU,
  u'lite': GOOGLE_APPS_LITE_SKU,
  u'gau': GOOGLE_APPS_UNLIMITED_SKU,
  u'unlimited': GOOGLE_APPS_UNLIMITED_SKU,
  u'd4w': GOOGLE_APPS_UNLIMITED_SKU,
  u'dfw': GOOGLE_APPS_UNLIMITED_SKU,
  u'coordinate': GOOGLE_COORDINATE_SKU,
  u'vault': GOOGLE_VAULT_SKU,
  u'vfe': GOOGLE_VAULT_FORMER_EMPLOYEE_SKU,
  u'drive-20gb': GOOGLE_DRIVE_STORAGE_20GB_SKU,
  u'drive20gb': GOOGLE_DRIVE_STORAGE_20GB_SKU,
  u'20gb': GOOGLE_DRIVE_STORAGE_20GB_SKU,
  u'drive-50gb': GOOGLE_DRIVE_STORAGE_50GB_SKU,
  u'drive50gb': GOOGLE_DRIVE_STORAGE_50GB_SKU,
  u'50gb': GOOGLE_DRIVE_STORAGE_50GB_SKU,
  u'drive-200gb': GOOGLE_DRIVE_STORAGE_200GB_SKU,
  u'drive200gb': GOOGLE_DRIVE_STORAGE_200GB_SKU,
  u'200gb': GOOGLE_DRIVE_STORAGE_200GB_SKU,
  u'drive-400gb': GOOGLE_DRIVE_STORAGE_400GB_SKU,
  u'drive400gb': GOOGLE_DRIVE_STORAGE_400GB_SKU,
  u'400gb': GOOGLE_DRIVE_STORAGE_400GB_SKU,
  u'drive-1tb': GOOGLE_DRIVE_STORAGE_1TB_SKU,
  u'drive1tb': GOOGLE_DRIVE_STORAGE_1TB_SKU,
  u'1tb': GOOGLE_DRIVE_STORAGE_1TB_SKU,
  u'drive-2tb': GOOGLE_DRIVE_STORAGE_2TB_SKU,
  u'drive2tb': GOOGLE_DRIVE_STORAGE_2TB_SKU,
  u'2tb': GOOGLE_DRIVE_STORAGE_2TB_SKU,
  u'drive-4tb': GOOGLE_DRIVE_STORAGE_4TB_SKU,
  u'drive4tb': GOOGLE_DRIVE_STORAGE_4TB_SKU,
  u'4tb': GOOGLE_DRIVE_STORAGE_4TB_SKU,
  u'drive-8tb': GOOGLE_DRIVE_STORAGE_8TB_SKU,
  u'drive8tb': GOOGLE_DRIVE_STORAGE_8TB_SKU,
  u'8tb': GOOGLE_DRIVE_STORAGE_8TB_SKU,
  u'drive-16tb': GOOGLE_DRIVE_STORAGE_16TB_SKU,
  u'drive16tb': GOOGLE_DRIVE_STORAGE_16TB_SKU,
  u'16tb': GOOGLE_DRIVE_STORAGE_16TB_SKU,
  }

def getGoogleProductListMap():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    productsOK = True
    products = CL_argv[CL_argvI].replace(u',', u' ').split()
    productsMapped = []
    for product in products:
      if product in GOOGLE_PRODUCTS:
        productsMapped.append(product)
      else:
        product = product.lower()
        if product in GOOGLE_SKU_CHOICES_MAP:
          productsMapped.append(GOOGLE_SKUS[GOOGLE_SKU_CHOICES_MAP[product]])
        else:
          productsOK = False
    if productsOK:
      CL_argvI += 1
      return productsMapped
    invalidChoiceExit(GOOGLE_SKU_CHOICES_MAP)
  missingArgumentExit(OB_PRODUCT_ID_LIST)

def getGoogleSKUMap(matchProduct=None):
  global CL_argvI
  if CL_argvI < CL_argvLen:
    skuOK = True
    sku = CL_argv[CL_argvI].strip()
    if sku:
      if sku not in GOOGLE_SKUS:
        sku = sku.lower()
        if sku in GOOGLE_SKU_CHOICES_MAP:
          sku = GOOGLE_SKU_CHOICES_MAP[sku]
        else:
          skuOK = False
      if skuOK:
        if (not matchProduct) or (GOOGLE_SKUS[sku] == matchProduct):
          CL_argvI += 1
          return sku
      invalidChoiceExit(GOOGLE_SKU_CHOICES_MAP)
  missingArgumentExit(OB_SKU_ID)

def getGoogleSKUListMap():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    skusOK = True
    skus = CL_argv[CL_argvI].replace(u',', u' ').split()
    skusMapped = []
    for sku in skus:
      if sku in GOOGLE_SKUS:
        skusMapped.append(GOOGLE_SKU_CHOICES_MAP[sku])
      else:
        sku = sku.lower()
        if sku in GOOGLE_SKU_CHOICES_MAP:
          skusMapped.append(GOOGLE_SKU_CHOICES_MAP[sku])
        else:
          skusOK = False
    if skusOK:
      CL_argvI += 1
      return skusMapped
    invalidChoiceExit(GOOGLE_SKU_CHOICES_MAP)
  missingArgumentExit(OB_SKU_ID_LIST)

def integerLimits(minVal, maxVal):
  if (minVal != None) and (maxVal != None):
    return u'integer {0}<=x<={1}'.format(minVal, maxVal)
  if minVal != None:
    return u'integer x>={0}'.format(minVal)
  if maxVal != None:
    return u'integer x<={0}'.format(maxVal)
  return u'integer x'

def getInteger(minVal=None, maxVal=None):
  global CL_argvI
  if CL_argvI < CL_argvLen:
    try:
      number = int(CL_argv[CL_argvI].strip())
      if (not minVal or (number >= minVal)) and (not maxVal or (number <= maxVal)):
        CL_argvI += 1
        return number
    except ValueError:
      pass
    invalidArgumentExit(integerLimits(minVal, maxVal))
  missingArgumentExit(integerLimits(minVal, maxVal))

# a|b|c|(custom_type <String>)
# if argument == CUSTOM_TYPE_EXPLICIT[PTKW_CL_TYPE_KEYWORD]:
#   getKeywordAttribute(CUSTOM_TYPE_EXPLICIT, attrdict)

#CUSTOM_TYPE_EXPLICIT = {
#    PTKW_CL_TYPE_KEYWORD: u'type',
#    PTKW_CL_CUSTOMTYPE_KEYWORD: u'custom_type',
#    PTKW_ATTR_TYPE_KEYWORD: u'type',
#    PTKW_ATTR_TYPE_CUSTOM_VALUE: u'custom',
#    PTKW_ATTR_CUSTOMTYPE_KEYWORD: u'customType',
#    PTKW_KEYWORD_LIST: [u'custom_type', u'a', u'b', u'c']
#    }

# a|b|c
# if argument == CUSTOM_TYPE_NOCUSTOM[PTKW_CL_TYPE_KEYWORD]:
#   getKeywordAttribute(CUSTOM_TYPE_NOCUSTOM, attrdict)

#CUSTOM_TYPE_NOCUSTOM = {
#    PTKW_CL_TYPE_KEYWORD: u'type',
#    PTKW_CL_CUSTOMTYPE_KEYWORD: u'type',
#    PTKW_ATTR_TYPE_KEYWORD: u'type',
#    PTKW_ATTR_TYPE_CUSTOM_VALUE: None,
#    PTKW_ATTR_CUSTOMTYPE_KEYWORD: None,
#    PTKW_KEYWORD_LIST: [u'a', u'b', u'c']
#    }

# a|b|c|<String>
# if argument == CUSTOM_TYPE_IMPLICIT[PTKW_CL_TYPE_KEYWORD]:
#   getKeywordAttribute(CUSTOM_TYPE_IMPLICIT, attrdict)

#CUSTOM_TYPE_IMPLICIT = {
#    PTKW_CL_TYPE_KEYWORD: u'type',
#    PTKW_CL_CUSTOMTYPE_KEYWORD: None,
#    PTKW_ATTR_TYPE_KEYWORD: u'type',
#    PTKW_ATTR_TYPE_CUSTOM_VALUE: u'custom',
#    PTKW_ATTR_CUSTOMTYPE_KEYWORD: u'customType',
#    PTKW_KEYWORD_LIST: [u'a', u'b', u'c']
#    }

# (a|b|c) | (custom_type <String>)
# if argument == CUSTOM_TYPE_IMPLICIT[PTKW_CL_TYPE_KEYWORD]:
#   getKeywordAttribute(CUSTOM_TYPE_IMPLICIT, attrdict)
# elif argument == CUSTOM_TYPE_IMPLICIT[PTKW_CL_CUSTOMTYPE_KEYWORD]:
#   attrdict[CUSTOM_TYPE_DIFFERENT_KEYWORD[PTKW_ATTR_TYPE_KEYWORD] = CUSTOM_TYPE_DIFFERENT_KEYWORD[PTKW_ATTR_CUSTOMTYPE_KEYWORD]
#   attrdict[CUSTOM_TYPE_DIFFERENT_KEYWORD[PTKW_ATTR_CUSTOMTYPE_KEYWORD]] = getValue()

#CUSTOM_TYPE_DIFFERENT_KEYWORD = {
#    PTKW_CL_TYPE_KEYWORD: u'type',
#    PTKW_CL_CUSTOMTYPE_KEYWORD: u'custom_type',
#    PTKW_ATTR_TYPE_KEYWORD: u'type',
#    PTKW_ATTR_TYPE_CUSTOM_VALUE: u'custom',
#    PTKW_ATTR_CUSTOMTYPE_KEYWORD: u'customType',
#    PTKW_KEYWORD_LIST: [u'a', u'b', u'c']
#    }
def getKeywordAttribute(keywords, attrdict, **opts):
  global CL_argvI
  if CL_argvI < CL_argvLen:
    keyword = CL_argv[CL_argvI].strip().lower()
    if keyword in keywords[PTKW_KEYWORD_LIST]:
      CL_argvI += 1
      attrdict[keywords[PTKW_ATTR_TYPE_KEYWORD]] = keyword
      if keyword != keywords[PTKW_CL_CUSTOMTYPE_KEYWORD]:
        return
      if CL_argvI < CL_argvLen:
        customType = CL_argv[CL_argvI].strip()
        if customType:
          CL_argvI += 1
          attrdict[keywords[PTKW_ATTR_TYPE_KEYWORD]] = keywords[PTKW_ATTR_TYPE_CUSTOM_VALUE]
          attrdict[keywords[PTKW_ATTR_CUSTOMTYPE_KEYWORD]] = customType
          return
      missingArgumentExit(u'custom attribute type')
    elif DEFAULT_CHOICE in opts:
      attrdict[keywords[PTKW_ATTR_TYPE_KEYWORD]] = opts[DEFAULT_CHOICE]
      return
    elif not keywords[PTKW_CL_CUSTOMTYPE_KEYWORD]:
      attrdict[keywords[PTKW_ATTR_TYPE_KEYWORD]] = keywords[PTKW_ATTR_TYPE_CUSTOM_VALUE]
      attrdict[keywords[PTKW_ATTR_CUSTOMTYPE_KEYWORD]] = CL_argv[CL_argvI]
      CL_argvI += 1
      return
    invalidChoiceExit(keywords[PTKW_KEYWORD_LIST])
  elif DEFAULT_CHOICE in opts:
    attrdict[keywords[PTKW_ATTR_TYPE_KEYWORD]] = opts[DEFAULT_CHOICE]
    return
  missingChoiceExit(keywords[PTKW_KEYWORD_LIST])

def orgUnitPathQuery(path):
  return u"orgUnitPath='{0}'".format(path.replace(u"'", u"\'"))

def makeOrgUnitPathAbsolute(path):
  if path == u'/':
    return path
  if path.startswith(u'/'):
    return path.rstrip(u'/')
  if path.startswith(u'id:'):
    return path
  if path.startswith(u'uid:'):
    return path[1:]
  return u'/'+path.rstrip(u'/')

def makeOrgUnitPathRelative(path):
  if path == u'/':
    return path
  if path.startswith(u'/'):
    return path[1:].rstrip(u'/')
  if path.startswith(u'id:'):
    return path
  if path.startswith(u'uid:'):
    return path[1:]
  return path.rstrip(u'/')

def getOrgUnitPath(absolutePath=True):
  global CL_argvI
  if CL_argvI < CL_argvLen:
    path = CL_argv[CL_argvI].strip()
    if path:
      CL_argvI += 1
      if absolutePath:
        return makeOrgUnitPathAbsolute(path)
      return makeOrgUnitPathRelative(path)
  missingArgumentExit(OB_ORGUNIT_PATH)

def getREPattern():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    patstr = CL_argv[CL_argvI]
    if patstr:
      try:
        pattern = re.compile(patstr)
        CL_argvI += 1
        return pattern
      except re.error as e:
        usageErrorExit(u'{0} {1}: {2}'.format(OB_RE_PATTERN, PHRASE_ERROR, e))
  missingArgumentExit(OB_RE_PATTERN)

SITENAME_PATTERN = re.compile(r'^[a-z0-9\-_]+$')
SITENAME_FORMAT_REQUIRED = u'[a-z,0-9,-_]+'

def validateSplitSiteName(fullSite):
  siteParts = fullSite.lower().split(u'/', 1)
  if (len(siteParts) == 1) or (len(siteParts[1]) == 0):
    domain = GC_Values[GC_DOMAIN]
    site = siteParts[0]
  elif len(siteParts[0]) == 0:
    domain = GC_Values[GC_DOMAIN]
    site = siteParts[1]
  else:
    domain = siteParts[0]
    site = siteParts[1]
  if SITENAME_PATTERN.match(site):
    return (domain, site, u'{0}/{1}'.format(domain, site))
  return (domain, site, None)

def getSiteName():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    domain, site, domainSite = validateSplitSiteName(CL_argv[CL_argvI])
    if domainSite:
      CL_argvI += 1
      return (domain, site, domainSite)
    invalidArgumentExit(SITENAME_FORMAT_REQUIRED)
  missingArgumentExit(SITENAME_FORMAT_REQUIRED)

def getString(item, checkBlank=False, emptyOK=False, optional=False):
  global CL_argvI
  if CL_argvI < CL_argvLen:
    argstr = CL_argv[CL_argvI]
    if argstr:
      if checkBlank:
        if argstr.isspace():
          blankArgumentExit(item)
      CL_argvI += 1
      return argstr
    if emptyOK or optional:
      CL_argvI += 1
      return u''
    emptyArgumentExit(item)
  elif optional:
    return u''
  missingArgumentExit(item)

def getStringReturnInList(item):
  argstr = getString(item, emptyOK=True)
  if argstr:
    return [argstr]
  return []

YYYYMMDD_FORMAT = u'%Y-%m-%d'
YYYYMMDD_FORMAT_REQUIRED = u'yyyy-mm-dd'

def getYYYYMMDD(emptyOK=False, returnTimeStamp=False):
  global CL_argvI
  if CL_argvI < CL_argvLen:
    argstr = CL_argv[CL_argvI].strip()
    if argstr:
      try:
        timeStamp = time.mktime(datetime.datetime.strptime(argstr, YYYYMMDD_FORMAT).timetuple())*1000
        CL_argvI += 1
        if not returnTimeStamp:
          return argstr
        return timeStamp
      except ValueError:
        invalidArgumentExit(YYYYMMDD_FORMAT_REQUIRED)
    elif emptyOK:
      CL_argvI += 1
      return u''
  missingArgumentExit(YYYYMMDD_FORMAT_REQUIRED)

YYYYMMDD_HHMM_FORMAT = u'%Y-%m-%d %H:%M'
YYYYMMDD_HHMM_FORMAT_REQUIRED = u'yyyy-mm-dd hh:mm'

def getYYYYMMDD_HHMM():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    argstr = CL_argv[CL_argvI].strip().upper().replace(u'T', u' ')
    if argstr:
      try:
        datetime.datetime.strptime(argstr, YYYYMMDD_HHMM_FORMAT)
        CL_argvI += 1
        return argstr
      except ValueError:
        invalidArgumentExit(YYYYMMDD_HHMM_FORMAT_REQUIRED)
  missingArgumentExit(YYYYMMDD_HHMM_FORMAT_REQUIRED)

YYYYMMDDTHHMMSS_FORMAT_REQUIRED = u'yyyy-mm-ddThh:mm:ss[.fff](Z|+hh:mm|-hh:mm)'

def getFullTime(returnDateTime=False):
  from iso8601 import iso8601
  global CL_argvI
  if CL_argvI < CL_argvLen:
    argstr = CL_argv[CL_argvI].strip().upper()
    if argstr:
      try:
        fullDateTime, tz = iso8601.parse_date(argstr)
        CL_argvI += 1
        if not returnDateTime:
          return argstr.replace(u' ', u'T')
        return (fullDateTime, tz, argstr.replace(u' ', u'T'))
      except iso8601.ParseError:
        pass
      invalidArgumentExit(YYYYMMDDTHHMMSS_FORMAT_REQUIRED)
  missingArgumentExit(YYYYMMDDTHHMMSS_FORMAT_REQUIRED)

EVENT_TIME_FORMAT_REQUIRED = u'allday yyyy-mm-dd | '+YYYYMMDDTHHMMSS_FORMAT_REQUIRED

def getEventTime():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    if CL_argv[CL_argvI].strip().lower() == u'allday':
      CL_argvI += 1
      return {u'date': getYYYYMMDD()}
    return {u'dateTime': getFullTime()}
  missingArgumentExit(EVENT_TIME_FORMAT_REQUIRED)

AGE_TIME_PATTERN = re.compile(r'^(\d+)([mhd]?)$')
AGE_TIME_FORMAT_REQUIRED = u'<Number>[m|h|d]'

def getAgeTime():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    tg = AGE_TIME_PATTERN.match(CL_argv[CL_argvI].strip().lower())
    if tg:
      tgg = tg.groups(u'0')
      age = int(tgg[0])
      age_unit = tgg[1]
      now = int(time.time())
      if age_unit == u'm':
        age = now-(age*SECONDS_PER_MINUTE)
      elif age_unit == u'h':
        age = now-(age*SECONDS_PER_HOUR)
      else: # age_unit == u'd':
        age = now-(age*SECONDS_PER_DAY)
      CL_argvI += 1
      return age
    invalidArgumentExit(AGE_TIME_FORMAT_REQUIRED)
  missingArgumentExit(AGE_TIME_FORMAT_REQUIRED)

CALENDAR_REMINDER_METHODS = [u'email', u'sms', u'popup',]

def getCalendarReminder(allowClearNone=False):
  methods = CALENDAR_REMINDER_METHODS
  if allowClearNone:
    methods += CLEAR_NONE_ARGUMENT
  if CL_argvI < CL_argvLen:
    method = CL_argv[CL_argvI].strip()
    if not method.isdigit():
      method = getChoice(methods)
      minutes = getInteger(minVal=0, maxVal=40320)
    else:
      minutes = getInteger(minVal=0, maxVal=40320)
      method = getChoice(methods)
    return {u'method': method, u'minutes': minutes}
  missingChoiceExit(methods)

def getCharSet():
  if checkArgumentPresent([u'charset',]):
    return getString(OB_CHAR_SET)
  return GC_Values.get(GC_CHARSET, GM_Globals[GM_SYS_ENCODING])

def getDelimiter():
  if checkArgumentPresent([u'delimiter',]):
    return getString(OB_STRING)
  return None

def getMatchFields(fieldNames):
  matchFields = {}
  while checkArgumentPresent([u'matchfield',]):
    matchField = getString(OB_FIELD_NAME).strip(u'~')
    if (not matchField) or (matchField not in fieldNames):
      csvFieldErrorExit(matchField, fieldNames, backupArg=True)
    matchFields[matchField] = getREPattern()
  return matchFields

def checkMatchFields(row, matchFields):
  for matchField, matchPattern in matchFields.items():
    if (matchField not in row) or not matchPattern.search(row[matchField]):
      return False
  return True

def checkDataField():
  if not GM_Globals[GM_CSV_DATA_DICT]:
    putArgumentBack()
    usageErrorExit(MESSAGE_NO_CSV_FILE_DATA_SAVED)
  chkDataField = getString(OB_FIELD_NAME, checkBlank=True)
  if chkDataField != GM_Globals[GM_CSV_DATA_FIELD]:
    putArgumentBack()
    usageErrorExit(MESSAGE_DATA_FIELD_MISMATCH.format(chkDataField, GM_Globals[GM_CSV_DATA_FIELD]))

MAX_MESSAGE_BYTES_PATTERN = re.compile(r'^(\d+)([mkb]?)$')
MAX_MESSAGE_BYTES_FORMAT_REQUIRED = u'<Number>[m|k|b]'

def getMaxMessageBytes():
  global CL_argvI
  if CL_argvI < CL_argvLen:
    tg = MAX_MESSAGE_BYTES_PATTERN.match(CL_argv[CL_argvI].strip().lower())
    if tg:
      tgg = tg.groups(u'0')
      mmb = int(tgg[0])
      mmb_unit = tgg[1]
      if mmb_unit == u'm':
        mmb *= ONE_MEGA_BYTES
      elif mmb_unit == u'k':
        mmb *= ONE_KILO_BYTES
      CL_argvI += 1
      return mmb
    invalidArgumentExit(MAX_MESSAGE_BYTES_FORMAT_REQUIRED)
  missingArgumentExit(MAX_MESSAGE_BYTES_FORMAT_REQUIRED)

# Get domain from email address
def getEmailAddressDomain(emailAddress):
  atLoc = emailAddress.find(u'@')
  if atLoc == -1:
    return GC_Values[GC_DOMAIN].lower()
  return emailAddress[atLoc+1:].lower()

# Get user name from email address
def getEmailAddressUsername(emailAddress):
  atLoc = emailAddress.find(u'@')
  if atLoc == -1:
    return emailAddress.lower()
  return emailAddress[:atLoc].lower()

# Split email address unto user and domain
def splitEmailAddress(emailAddress):
  atLoc = emailAddress.find(u'@')
  if atLoc == -1:
    return (emailAddress.lower(), GC_Values[GC_DOMAIN].lower())
  return (emailAddress[:atLoc].lower(), emailAddress[atLoc+1:].lower())

# Get names of entities
def chooseEntityName(entityId, count):
  return ENTITY_NAMES[entityId][[0, 1][count == 1]]

def pluralEntityName(entityId):
  return ENTITY_NAMES[entityId][0]

def singularEntityName(entityId):
  return ENTITY_NAMES[entityId][1]

# Get action names
def setActionName(action):
  GM_Globals[GM_ACTION_COMMAND] = action
  GM_Globals[GM_ACTION_TO_PERFORM] = ACTION_NAMES[action][1]
  GM_Globals[GM_ACTION_PERFORMED] = ACTION_NAMES[action][0]
  GM_Globals[GM_ACTION_FAILED] = u'{0} {1}'.format(GM_Globals[GM_ACTION_TO_PERFORM], AC_SUFFIX_FAILED)
  GM_Globals[GM_ACTION_NOT_PERFORMED] = u'{0} {1}'.format(AC_PREFIX_NOT, GM_Globals[GM_ACTION_PERFORMED])

def formatFileSize(fileSize):
  if fileSize == 0:
    return u'0kb'
  if fileSize < ONE_KILO_BYTES:
    return u'1kb'
  if fileSize < ONE_MEGA_BYTES:
    return u'{0}kb'.format(fileSize / ONE_KILO_BYTES)
  if fileSize < ONE_GIGA_BYTES:
    return u'{0}mb'.format(fileSize / ONE_MEGA_BYTES)
  return u'{0}gb'.format(fileSize / ONE_GIGA_BYTES)

def formatMaxMessageBytes(maxMessageBytes):
  if maxMessageBytes < ONE_KILO_BYTES:
    return maxMessageBytes
  if maxMessageBytes < ONE_MEGA_BYTES:
    return u'{0}K'.format(maxMessageBytes / ONE_KILO_BYTES)
  return u'{0}M'.format(maxMessageBytes / ONE_MEGA_BYTES)

def formatMilliSeconds(millis):
  seconds, millis = divmod(millis, 1000)
  minutes, seconds = divmod(seconds, 60)
  hours, minutes = divmod(minutes, 60)
  return u'%02d:%02d:%02d' % (hours, minutes, seconds)

def currentCount(i, count):
  return u' ({0}/{1})'.format(i, count) if (count > GC_Values[GC_SHOW_COUNTS_MIN]) else u''

def currentCountNL(i, count):
  return u' ({0}/{1})\n'.format(i, count) if (count > GC_Values[GC_SHOW_COUNTS_MIN]) else u'\n'

def getPhraseDNEorSNA(email):
  return [PHRASE_SERVICE_NOT_APPLICABLE, PHRASE_DOES_NOT_EXIST][getEmailAddressDomain(email) == GC_Values[GC_DOMAIN]]

def formatHTTPError(http_status, reason, message):
  return u'{0}: {1} - {2}'.format(http_status, reason, message)

def getHTTPError(responses, http_status, reason, message):
  if reason in responses:
    return responses[reason]
  return formatHTTPError(http_status, reason, message)

# Warnings
def printWarningMessage(sysRC, errMessage):
  setSysExitRC(sysRC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES], [WARNING, errMessage], u'\n'))

def badRequestWarning(entityType, itemType, itemValue):
  printWarningMessage(BAD_REQUEST_RC, u'{0} 0 {1}: {2} {3} - {4}'.format(PHRASE_GOT, pluralEntityName(entityType),
                                                                         PHRASE_INVALID, singularEntityName(itemType),
                                                                         itemValue))

def invalidQuery(query):
  return u'{0}: ({1}) {2}'.format(singularEntityName(EN_QUERY), query, PHRASE_INVALID)

def entityTypeName(entityType, entityName):
  return u'{0}: {1}'.format(singularEntityName(entityType), entityName)

def entityTypeNameMessage(entityType, entityName, message):
  return u'{0}: {1} {2}'.format(singularEntityName(entityType), entityName, message)

def entityServiceNotApplicableWarning(entityType, entityName, i=0, count=0):
  setSysExitRC(SERVICE_NOT_APPLICABLE_RC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName, PHRASE_SERVICE_NOT_APPLICABLE],
                                      currentCountNL(i, count)))

def entityDoesNotExistWarning(entityType, entityName, i=0, count=0):
  setSysExitRC(ENTITY_DOES_NOT_EXIST_RC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName, PHRASE_DOES_NOT_EXIST],
                                      currentCountNL(i, count)))

def entityUnknownWarning(entityType, entityName, i=0, count=0):
  domain = getEmailAddressDomain(entityName)
  if (domain == GC_Values[GC_DOMAIN]) or (domain.endswith(u'google.com')):
    entityDoesNotExistWarning(entityType, entityName, i, count)
  else:
    entityServiceNotApplicableWarning(entityType, entityName, i, count)

def entityOrEntityUnknownWarning(entity1Type, entity1Name, entity2Type, entity2Name, i=0, count=0):
  setSysExitRC(ENTITY_DOES_NOT_EXIST_RC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [u'{0} {1}'.format(PHRASE_EITHER, singularEntityName(entity1Type)), entity1Name, getPhraseDNEorSNA(entity1Name), None,
                                       u'{0} {1}'.format(PHRASE_OR, singularEntityName(entity2Type)), entity2Name, getPhraseDNEorSNA(entity2Name)],
                                      currentCountNL(i, count)))

def entityDuplicateWarning(entityType, entityName, i=0, count=0):
  setSysExitRC(ENTITY_DUPLICATE_RC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       PHRASE_DUPLICATE],
                                      currentCountNL(i, count)))

def entityDoesNotHaveItemValueWarning(entityType, entityName, itemType, itemValue, i=0, count=0):
  setSysExitRC(ENTITY_DOES_NOT_EXIST_RC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(itemType), itemValue,
                                       PHRASE_DOES_NOT_EXIST],
                                      currentCountNL(i, count)))

def entityDoesNotHaveItemValueSubitemValueWarning(entityType, entityName, itemType, itemValue, subItemType, subItemValue, i=0, count=0):
  setSysExitRC(ENTITY_DOES_NOT_EXIST_RC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(itemType), itemValue,
                                       singularEntityName(subItemType), subItemValue,
                                       PHRASE_DOES_NOT_EXIST],
                                      currentCountNL(i, count)))

def entityActionFailedWarning(entityType, entityName, errMessage, i=0, count=0):
  setSysExitRC(AC_FAILED_RC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       GM_Globals[GM_ACTION_FAILED], errMessage],
                                      currentCountNL(i, count)))

def entityItemValueActionFailedWarning(entityType, entityName, itemType, itemValue, errMessage, i=0, count=0):
  setSysExitRC(AC_FAILED_RC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(itemType), itemValue,
                                       GM_Globals[GM_ACTION_FAILED], errMessage],
                                      currentCountNL(i, count)))

def entityItemValueItemValueActionFailedWarning(entityType, entityName, item1Type, item1Value, item2Type, item2Value, errMessage, i=0, count=0):
  setSysExitRC(AC_FAILED_RC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(item1Type), item1Value,
                                       singularEntityName(item2Type), item2Value,
                                       GM_Globals[GM_ACTION_FAILED], errMessage],
                                      currentCountNL(i, count)))

def entityItemValueModifierNewValueActionFailedWarning(entityType, entityName, itemType, itemValue, modifier, newValue, errMessage, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(itemType), itemValue,
                                       u'{0} {1}'.format(GM_Globals[GM_ACTION_TO_PERFORM], modifier), newValue,
                                       GM_Globals[GM_ACTION_FAILED], errMessage],
                                      currentCountNL(i, count)))

def entityActionNotPerformedWarning(entityType, entityName, errMessage, i=0, count=0):
  setSysExitRC(AC_NOT_PERFORMED_RC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       GM_Globals[GM_ACTION_NOT_PERFORMED], errMessage],
                                      currentCountNL(i, count)))

def entityItemValueActionNotPerformedWarning(entityType, entityName, itemType, itemValue, errMessage, i=0, count=0):
  setSysExitRC(AC_NOT_PERFORMED_RC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(itemType), itemValue,
                                       GM_Globals[GM_ACTION_NOT_PERFORMED], errMessage],
                                      currentCountNL(i, count)))

def entityNumEntitiesActionNotPerformedWarning(entityType, entityName, itemType, itemCount, errMessage, i=0, count=0):
  setSysExitRC(AC_NOT_PERFORMED_RC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       chooseEntityName(itemType, itemCount), itemCount,
                                       GM_Globals[GM_ACTION_NOT_PERFORMED], errMessage],
                                      currentCountNL(i, count)))

def entityBadRequestWarning(entityType, entityName, itemType, itemValue, errMessage, i=0, count=0):
  setSysExitRC(BAD_REQUEST_RC)
  sys.stderr.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(itemType), itemValue,
                                       ERROR, errMessage],
                                      currentCountNL(i, count)))

# Getting ... utilities
def mayTakeTime(entityType):
  if entityType:
    return u', {0} {1}...'.format(PHRASE_MAY_TAKE_SOME_TIME_ON_A_LARGE, singularEntityName(entityType))
  return u''

def queryQualifier(query):
  if query:
    return u' {0} ({1})'.format(PHRASE_THAT_MATCH_QUERY, query)
  return u''

def printGettingAccountEntitiesInfo(entityType, qualifier=u''):
  if GC_Values[GC_SHOW_GETTINGS]:
    GM_Globals[GM_GETTING_ENTITY_ITEM] = ENTITY_NAMES[entityType]
    sys.stderr.write(u'{0} {1}{2}{3}\n'.format(PHRASE_GETTING_ALL, GM_Globals[GM_GETTING_ENTITY_ITEM][0], qualifier, mayTakeTime(EN_ACCOUNT)))

def printGettingAccountEntitiesDoneInfo(count, qualifier=u''):
  if GC_Values[GC_SHOW_GETTINGS]:
    sys.stderr.write(u'{0} {1} {2}{3}\n'.format(PHRASE_GOT, count, GM_Globals[GM_GETTING_ENTITY_ITEM][[0, 1][count == 1]], qualifier))

def setGettingEntityItem(entityItem):
  GM_Globals[GM_GETTING_ENTITY_ITEM] = ENTITY_NAMES.get(entityItem, [entityItem, entityItem])

def printGettingEntityItemsInfo(entityType, entityItem):
  if GC_Values[GC_SHOW_GETTINGS]:
    setGettingEntityItem(entityItem)
    sys.stderr.write(u'{0} {1}{2}\n'.format(PHRASE_GETTING_ALL, GM_Globals[GM_GETTING_ENTITY_ITEM][0], mayTakeTime(entityType)))

def printGettingEntityItemsDoneInfo(count, qualifier=u''):
  if GC_Values[GC_SHOW_GETTINGS]:
    sys.stderr.write(u'{0} {1} {2}{3}\n'.format(PHRASE_GOT, count, GM_Globals[GM_GETTING_ENTITY_ITEM][[0, 1][count == 1]], qualifier))

def printGettingEntityItemForWhom(entityItem, forWhom, i=0, count=0):
  if GC_Values[GC_SHOW_GETTINGS]:
    setGettingEntityItem(entityItem)
    GM_Globals[GM_GETTING_FOR_WHOM] = forWhom
    sys.stderr.write(u'{0} {1} {2} {3}{4}'.format(PHRASE_GETTING, GM_Globals[GM_GETTING_ENTITY_ITEM][0], PHRASE_FOR, forWhom, currentCountNL(i, count)))

def printGettingAllEntityItemsForWhom(entityItem, forWhom, i=0, count=0, qualifier=u'', entityType=None):
  if GC_Values[GC_SHOW_GETTINGS]:
    setGettingEntityItem(entityItem)
    GM_Globals[GM_GETTING_FOR_WHOM] = forWhom
    sys.stderr.write(u'{0} {1}{2} {3} {4}{5}{6}'.format(PHRASE_GETTING_ALL, GM_Globals[GM_GETTING_ENTITY_ITEM][0], qualifier, PHRASE_FOR, forWhom, mayTakeTime(entityType), currentCountNL(i, count)))

def printGettingEntityItemsForWhomDoneInfo(count, qualifier=u''):
  if GC_Values[GC_SHOW_GETTINGS]:
    sys.stderr.write(u'{0} {1} {2}{3} {4} {5}...\n'.format(PHRASE_GOT, count, GM_Globals[GM_GETTING_ENTITY_ITEM][[0, 1][count == 1]], qualifier, PHRASE_FOR, GM_Globals[GM_GETTING_FOR_WHOM]))

FIRST_ITEM_MARKER = u'%%first_item%%'
LAST_ITEM_MARKER = u'%%last_item%%'
NUM_ITEMS_MARKER = u'%%num_items%%'
TOTAL_ITEMS_MARKER = u'%%total_items%%'

def getPageMessage(showTotal=True, showFirstLastItems=False, noNL=False):
  if not GC_Values[GC_SHOW_GETTINGS]:
    return None
  GM_Globals[GM_GETTING_SHOW_TOTAL] = showTotal
  pageMessage = u'{0} {1} {{0}}'.format(PHRASE_GOT, [NUM_ITEMS_MARKER, TOTAL_ITEMS_MARKER][showTotal])
  if showFirstLastItems:
    pageMessage += u': {0} - {1}'.format(FIRST_ITEM_MARKER, LAST_ITEM_MARKER)
  else:
    pageMessage += u'...'
  if not noNL:
    pageMessage += u'\n'
  return pageMessage

def getPageMessageForWhom(forWhom=None, showTotal=True, showFirstLastItems=False, noNL=False):
  if not GC_Values[GC_SHOW_GETTINGS]:
    return None
  GM_Globals[GM_GETTING_SHOW_TOTAL] = showTotal
  if forWhom:
    GM_Globals[GM_GETTING_FOR_WHOM] = forWhom
  pageMessage = u'{0} {1} {{0}} {2} {3}'.format(PHRASE_GOT, [NUM_ITEMS_MARKER, TOTAL_ITEMS_MARKER][showTotal], PHRASE_FOR, GM_Globals[GM_GETTING_FOR_WHOM])
  if showFirstLastItems:
    pageMessage += u': {0} - {1}'.format(FIRST_ITEM_MARKER, LAST_ITEM_MARKER)
  else:
    pageMessage += u'...'
  if not noNL:
    pageMessage += u'\n'
  return pageMessage

def printLine(message):
  sys.stdout.write(convertUTF8(message+u'\n'))

def printBlankLine():
  sys.stdout.write(u'\n')

def printKeyValueList(kvList):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES], kvList, u'\n'))

def printKeyValueListWithCount(kvList, i, count):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES], kvList, currentCountNL(i, count)))

def printKeyValueDict(kvDict):
  for key, value in kvDict.iteritems():
    sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES], [key, value], u'\n'))

def printJSONKey(key):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES], [key, u''], u''))

def printJSONValue(value):
  sys.stdout.write(formatKeyValueList(u' ', [value], u'\n'))

def printEntityName(entityType, entityName, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName],
                                      currentCountNL(i, count)))

def printEntityItemValue(entityType, entityName, itemType, itemValue, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(itemType), itemValue],
                                      currentCountNL(i, count)))

def printEntityKVList(entityType, entityName, infoKVList, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName]+infoKVList,
                                      currentCountNL(i, count)))

def performActionNumItems(itemCount, itemType, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [u'{0} {1} {2}'.format(GM_Globals[GM_ACTION_TO_PERFORM], itemCount, chooseEntityName(itemType, itemCount))],
                                      currentCountNL(i, count)))

def entityPerformActionNumItems(entityType, entityName, itemCount, itemType, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       u'{0} {1} {2}'.format(GM_Globals[GM_ACTION_TO_PERFORM], itemCount, chooseEntityName(itemType, itemCount))],
                                      currentCountNL(i, count)))

def entityPerformActionItemValueNumItems(entityType, entityName, itemType, itemValue, subItemCount, subItemType, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(itemType), itemValue,
                                       u'{0} {1} {2}'.format(GM_Globals[GM_ACTION_TO_PERFORM], subItemCount, chooseEntityName(subItemType, subItemCount))],
                                      currentCountNL(i, count)))

def entityPerformActionModifierNumItems(entityType, entityName, modifier, itemCount, itemType, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       u'{0} {1} {2} {3}'.format(GM_Globals[GM_ACTION_TO_PERFORM], modifier, itemCount, chooseEntityName(itemType, itemCount))],
                                      currentCountNL(i, count)))

def entityPerformActionNumItemsModifier(entityType, entityName, itemCount, itemType, modifier, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       u'{0} {1} {2} {3}'.format(GM_Globals[GM_ACTION_TO_PERFORM], itemCount, chooseEntityName(itemType, itemCount), modifier)],
                                      currentCountNL(i, count)))

def entityPerformActionModifierNumItemsModifier(entityType, entityName, modifier1, itemCount, itemType, modifier2, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       u'{0} {1} {2} {3} {4}'.format(GM_Globals[GM_ACTION_TO_PERFORM], modifier1, itemCount, chooseEntityName(itemType, itemCount), modifier2)],
                                      currentCountNL(i, count)))

def entityPerformActionItemValueModifierNewValue(entityType, entityName, itemType, itemValue, modifier, newValue, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(itemType), itemValue,
                                       u'{0} {1}'.format(GM_Globals[GM_ACTION_TO_PERFORM], modifier), newValue],
                                      currentCountNL(i, count)))

def entityPerformActionItemValueInfo(entityType, entityName, itemType, itemValue, infoValue, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(itemType), itemValue,
                                       GM_Globals[GM_ACTION_TO_PERFORM], infoValue],
                                      currentCountNL(i, count)))

def entityActionPerformed(entityType, entityName, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       GM_Globals[GM_ACTION_PERFORMED]],
                                      currentCountNL(i, count)))

def entityActionPerformedMessage(entityType, entityName, message, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       GM_Globals[GM_ACTION_PERFORMED], message],
                                      currentCountNL(i, count)))

def entityItemValueActionPerformed(entityType, entityName, itemType, itemValue, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(itemType), itemValue,
                                       GM_Globals[GM_ACTION_PERFORMED]],
                                      currentCountNL(i, count)))

def entityItemValueItemValueActionPerformed(entityType, entityName, item1Type, item1Value, item2Type, item2Value, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(item1Type), item1Value,
                                       singularEntityName(item2Type), item2Value,
                                       GM_Globals[GM_ACTION_PERFORMED]],
                                      currentCountNL(i, count)))

def entityItemValueModifierNewValueActionPerformed(entityType, entityName, itemType, itemValue, modifier, newValue, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(itemType), itemValue,
                                       u'{0} {1}'.format(GM_Globals[GM_ACTION_PERFORMED], modifier), newValue],
                                      currentCountNL(i, count)))

def entityItemValueModifierNewValueInfoActionPerformed(entityType, entityName, itemType, itemValue, modifier, newValue, infoKey, infoValue, i=0, count=0):
  sys.stdout.write(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(entityType), entityName,
                                       singularEntityName(itemType), itemValue,
                                       u'{0} {1}'.format(GM_Globals[GM_ACTION_PERFORMED], modifier), newValue,
                                       infoKey, infoValue],
                                      currentCountNL(i, count)))

#SAFE_FILENAME_CHARS = u'-_.() {0}{1}'.format(string.ascii_letters, string.digits)
#def cleanFilename(filename):
#  return u''.join(c for c in filename if c in SAFE_FILENAME_CHARS)
#
UNSAFE_FILENAME_CHARS = u'\\/:'

def cleanFilename(filename, cleanDiacriticals=False):
  if cleanDiacriticals:
    import unicodedata
    nkfd_form = unicodedata.normalize(u'NFKD', filename)
    filename = u''.join([c for c in nkfd_form if not unicodedata.combining(c)])
  for ch in UNSAFE_FILENAME_CHARS:
    filename = filename.replace(ch, u'_')
  return filename

# Open a file
def openFile(filename, mode=u'rU'):
  try:
    if filename != u'-':
      return open(os.path.expanduser(filename), mode)
    if mode.startswith(u'r'):
      return StringIO.StringIO(unicode(sys.stdin.read()))
    return sys.stdout
  except IOError as e:
    systemErrorExit(FILE_ERROR_RC, e)

# Close a file
def closeFile(f):
  try:
    f.close()
    return True
  except IOError as e:
    stderrErrorMsg(e)
    setSysExitRC(FILE_ERROR_RC)
    return False

# Read a file
def readFile(filename, mode=u'rb', continueOnError=False, displayError=True, encoding=None):
  try:
    if filename != u'-':
      if not encoding:
        with open(os.path.expanduser(filename), mode) as f:
          return f.read()
      with codecs.open(os.path.expanduser(filename), mode, encoding) as f:
        content = f.read()
        if not content.startswith(codecs.BOM_UTF8):
          return content
        return content.replace(codecs.BOM_UTF8, u'', 1)
    return unicode(sys.stdin.read())
  except IOError as e:
    if continueOnError:
      if displayError:
        stderrWarningMsg(e)
        setSysExitRC(FILE_ERROR_RC)
      return None
    systemErrorExit(FILE_ERROR_RC, e)
  except LookupError as e:
    putArgumentBack()
    usageErrorExit(e)

# Write a file
def writeFile(filename, data, mode=u'wb', continueOnError=False, displayError=True):
  try:
    with open(os.path.expanduser(filename), mode) as f:
      f.write(data)
    return True
  except IOError as e:
    if continueOnError:
      if displayError:
        stderrErrorMsg(e)
      setSysExitRC(FILE_ERROR_RC)
      return False
    systemErrorExit(FILE_ERROR_RC, e)

# Write a file, return error
def writeFileReturnError(filename, data, mode=u'wb'):
  try:
    with open(os.path.expanduser(filename), mode) as f:
      f.write(data)
    return (True, None)
  except IOError as e:
    return (False, e)
#
class UTF8Recoder(object):
  """
  Iterator that reads an encoded stream and reencodes the input to UTF-8
  """
  def __init__(self, f, encoding):
    self.reader = codecs.getreader(encoding)(f)

  def __iter__(self):
    return self

  def next(self):
    return self.reader.next().encode(u'utf-8')

class UnicodeDictReader(object):
  """
  A CSV reader which will iterate over lines in the CSV file "f",
  which is encoded in the given encoding.
  """

  def __init__(self, f, dialect=csv.excel, encoding=u'utf-8', fieldnames=None, **kwds):
    self.encoding = encoding
    try:
      self.reader = csv.reader(UTF8Recoder(f, encoding) if self.encoding != u'utf-8' else f, dialect=dialect, **kwds)
      if not fieldnames:
        self.fieldnames = self.reader.next()
        if len(self.fieldnames) > 0 and self.fieldnames[0].startswith(codecs.BOM_UTF8):
          self.fieldnames[0] = self.fieldnames[0].replace(codecs.BOM_UTF8, u'', 1)
      else:
        self.fieldnames = fieldnames
    except (csv.Error, StopIteration):
      self.fieldnames = []
    except LookupError as e:
      putArgumentBack()
      usageErrorExit(e)
    self.numfields = len(self.fieldnames)

  def __iter__(self):
    return self

  def next(self):
    row = self.reader.next()
    l = len(row)
    if l < self.numfields:
      row += ['']*(self.numfields-l) # Must be '', not u''
    return dict((self.fieldnames[x], unicode(row[x], u'utf-8')) for x in range(self.numfields))
#
class UnicodeWriter(object):
  """
  A CSV writer which will write rows to CSV file "f",
  which is encoded in the given encoding.
  """

  def __init__(self, f, dialect=csv.excel, **kwds):
    # Redirect output to a queue
    import cStringIO
    self.queue = cStringIO.StringIO()
    self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
    self.stream = f
    self.encoder = codecs.getincrementalencoder(GM_Globals[GM_CSVFILE_ENCODING])()

  def writerow(self, row):
    self.writer.writerow([unicode(s).encode(u'utf-8') for s in row])
    if GM_Globals[GM_CSVFILE_ENCODING] != u'utf-8':
      # Fetch UTF-8 output from the queue, reencode it into the target encoding and write to the target stream
      self.stream.write(self.encoder.encode(self.queue.getvalue().decode(u'utf-8')))
    else:
      # Fetch UTF-8 output from the queue and write to the target stream
      self.stream.write(self.queue.getvalue())
    # empty queue
    self.queue.truncate(0)

  def writerows(self, rows):
    for row in rows:
      self.writerow(row)
#
class UnicodeDictWriter(csv.DictWriter, object):
  def __init__(self, f, fieldnames, dialect=u'nixstdout', *args, **kwds):
    super(UnicodeDictWriter, self).__init__(f, fieldnames, dialect=u'nixstdout', *args, **kwds)
    self.writer = UnicodeWriter(f, dialect, **kwds)

# Open a CSV file, get optional arguments [charset <String>] [fields <FieldNameList>]
def openCSVFileReader(filename):
  encoding = getCharSet()
  if checkArgumentPresent([u'fields',]):
    fieldnames = shlexSplitList(getString(OB_FIELD_NAME_LIST))
  else:
    fieldnames = None
  f = openFile(filename)
  csvFile = UnicodeDictReader(f, encoding=encoding, fieldnames=fieldnames)
  return (f, csvFile)

# Set global variables from config file
# Check for GAM updates based on status of no_update_check in config file
# Return True if there are additional commands on the command line
def SetGlobalVariables():

  def _getDefault(itemName, itemEntry, oldGamPath):
    if GC_VAR_SFFT in itemEntry:
      GC_Defaults[itemName] = itemEntry[GC_VAR_SFFT][os.path.isfile(os.path.join(oldGamPath, itemEntry[GC_VAR_ENVVAR]))]
    else:
      value = os.environ.get(itemEntry[GC_VAR_ENVVAR], GC_Defaults[itemName])
      if itemEntry[GC_VAR_TYPE] == GC_TYPE_INTEGER:
        try:
          number = int(value)
          minVal, maxVal = itemEntry[GC_VAR_LIMITS]
          if number < minVal:
            number = minVal
          elif maxVal and (number > maxVal):
            number = maxVal
        except ValueError:
          number = GC_Defaults[itemName]
        value = str(number)
      GC_Defaults[itemName] = value

  def _selectSection():
    value = getString(OB_SECTION_NAME, emptyOK=True)
    if (not value) or (value.upper() == ConfigParser.DEFAULTSECT):
      return ConfigParser.DEFAULTSECT
    if GM_Globals[GM_PARSER].has_section(value):
      return value
    putArgumentBack()
    usageErrorExit(formatKeyValueList(u'', [singularEntityName(EN_SECTION), value, PHRASE_NOT_FOUND], u''))

  def _checkMakeDir(itemName):
    if not os.path.isdir(GC_Defaults[itemName]):
      try:
        os.makedirs(GC_Defaults[itemName])
        printKeyValueList([ACTION_NAMES[AC_CREATE][0], GC_Defaults[itemName]])
      except OSError as e:
        if not os.path.isdir(GC_Defaults[itemName]):
          systemErrorExit(FILE_ERROR_RC, e)

  def _copyCfgFile(srcFile, targetDir, oldGamPath):
    if (not srcFile) or os.path.isabs(srcFile):
      return
    dstFile = os.path.join(GC_Defaults[targetDir], srcFile)
    if os.path.isfile(dstFile):
      return
    srcFile = os.path.join(oldGamPath, srcFile)
    if not os.path.isfile(srcFile):
      return
    data = readFile(srcFile, mode=u'rU', continueOnError=True, displayError=False)
    if (data != None) and writeFile(dstFile, data, continueOnError=True):
      printKeyValueList([ACTION_NAMES[AC_COPY][0], srcFile, PHRASE_TO, dstFile])

  def _getCfgBoolean(sectionName, itemName):
    value = GM_Globals[GM_PARSER].get(sectionName, itemName, raw=True)
    if value in TRUE_VALUES:
      return True
    if value in FALSE_VALUES:
      return False
    printErrorMessage(CONFIG_ERROR_RC,
                      formatKeyValueList(u'',
                                         [singularEntityName(EN_CONFIG_FILE), GM_Globals[GM_GAM_CFG_FILE],
                                          singularEntityName(EN_SECTION), sectionName,
                                          singularEntityName(EN_ITEM), itemName,
                                          singularEntityName(EN_VALUE), value,
                                          PHRASE_EXPECTED, formatChoiceList(TRUE_FALSE)],
                                         u''))
    status[u'errors'] = True
    return False

  def _getCfgInteger(sectionName, itemName):
    value = GM_Globals[GM_PARSER].get(sectionName, itemName, raw=True)
    minVal, maxVal = GC_VAR_INFO[itemName][GC_VAR_LIMITS]
    try:
      number = int(value)
      if (number >= minVal) and (not maxVal or (number <= maxVal)):
        return number
    except ValueError:
      pass
    printErrorMessage(CONFIG_ERROR_RC,
                      formatKeyValueList(u'',
                                         [singularEntityName(EN_CONFIG_FILE), GM_Globals[GM_GAM_CFG_FILE],
                                          singularEntityName(EN_SECTION), sectionName,
                                          singularEntityName(EN_ITEM), itemName,
                                          singularEntityName(EN_VALUE), value,
                                          PHRASE_EXPECTED, integerLimits(minVal, maxVal)],
                                         u''))
    status[u'errors'] = True
    return 0

  def _getCfgSection(sectionName, itemName):
    value = GM_Globals[GM_PARSER].get(sectionName, itemName, raw=True)
    if (not value) or (value.upper() == ConfigParser.DEFAULTSECT):
      return ConfigParser.DEFAULTSECT
    if GM_Globals[GM_PARSER].has_section(value):
      return value
    printErrorMessage(CONFIG_ERROR_RC,
                      formatKeyValueList(u'',
                                         [singularEntityName(EN_CONFIG_FILE), GM_Globals[GM_GAM_CFG_FILE],
                                          singularEntityName(EN_SECTION), sectionName,
                                          singularEntityName(EN_ITEM), itemName,
                                          singularEntityName(EN_VALUE), value,
                                          PHRASE_NOT_FOUND],
                                         u''))
    status[u'errors'] = True
    return ConfigParser.DEFAULTSECT

  def _getCfgString(sectionName, itemName):
    return GM_Globals[GM_PARSER].get(sectionName, itemName, raw=True)

  def _getCfgDirectory(sectionName, itemName):
    dirPath = os.path.expanduser(GM_Globals[GM_PARSER].get(sectionName, itemName, raw=True))
    if (not dirPath) or (not os.path.isabs(dirPath)):
      if (sectionName != ConfigParser.DEFAULTSECT) and (GM_Globals[GM_PARSER].has_option(sectionName, itemName)):
        dirPath = os.path.join(os.path.expanduser(GM_Globals[GM_PARSER].get(ConfigParser.DEFAULTSECT, itemName, raw=True)), dirPath)
      if not os.path.isabs(dirPath):
        dirPath = os.path.join(GM_Globals[GM_GAM_CFG_PATH], dirPath)
    return dirPath

  def _getCfgFile(sectionName, itemName):
    value = os.path.expanduser(GM_Globals[GM_PARSER].get(sectionName, itemName, raw=True))
    if value and not os.path.isabs(value):
      value = os.path.expanduser(os.path.join(_getCfgDirectory(sectionName, GC_CONFIG_DIR), value))
    return value

  def _readGamCfgFile(config, fileName, action=None):
    try:
      with open(fileName, u'rb') as f:
        config.readfp(f)
      if action:
        printKeyValueList([singularEntityName(EN_CONFIG_FILE), fileName, action])
    except (ConfigParser.MissingSectionHeaderError, ConfigParser.ParsingError) as e:
      systemErrorExit(CONFIG_ERROR_RC, formatKeyValueList(u'',
                                                          [singularEntityName(EN_CONFIG_FILE), fileName,
                                                           PHRASE_INVALID, e.message],
                                                          u''))
    except IOError as e:
      systemErrorExit(FILE_ERROR_RC, e)

  def _writeGamCfgFile(config, fileName, action=None):
    try:
      with open(fileName, u'wb') as f:
        config.write(f)
      if action:
        printKeyValueList([singularEntityName(EN_CONFIG_FILE), fileName, action])
    except IOError as e:
      stderrErrorMsg(e)

  def _verifyValues(sectionName):
    printKeyValueList([singularEntityName(EN_SECTION), sectionName])
    incrementIndentLevel()
    for itemName in sorted(GC_VAR_INFO):
      cfgValue = GM_Globals[GM_PARSER].get(sectionName, itemName, raw=True)
      if GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_FILE:
        expdValue = _getCfgFile(sectionName, itemName)
        if cfgValue != expdValue:
          cfgValue = u'{0} ; {1}'.format(cfgValue, expdValue)
      elif GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_DIRECTORY:
        expdValue = _getCfgDirectory(sectionName, itemName)
        if cfgValue != expdValue:
          cfgValue = u'{0} ; {1}'.format(cfgValue, expdValue)
      elif (itemName == GC_SECTION) and (sectionName != ConfigParser.DEFAULTSECT):
        continue
      printLine(u'{0}{1} = {2}'.format(GM_Globals[GM_INDENT_SPACES], itemName, cfgValue))
    decrementIndentLevel()

  def _chkCfgDirectories(sectionName):
    for itemName in GC_VAR_INFO:
      if GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_DIRECTORY:
        dirPath = GC_Values[itemName]
        if not os.path.isdir(dirPath):
          sys.stderr.write(formatKeyValueList(WARNING_PREFIX,
                                              [singularEntityName(EN_CONFIG_FILE), GM_Globals[GM_GAM_CFG_FILE],
                                               singularEntityName(EN_SECTION), sectionName,
                                               singularEntityName(EN_ITEM), itemName,
                                               singularEntityName(EN_VALUE), dirPath,
                                               PHRASE_INVALID_PATH],
                                              u'\n'))

  def _chkCfgFiles(sectionName):
    for itemName in GC_VAR_INFO:
      if GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_FILE:
        fileName = GC_Values[itemName]
        if (not fileName) and (itemName == GC_EXTRA_ARGS):
          continue
        if not os.path.isfile(fileName):
          sys.stderr.write(formatKeyValueList(WARNING_PREFIX,
                                              [singularEntityName(EN_CONFIG_FILE), GM_Globals[GM_GAM_CFG_FILE],
                                               singularEntityName(EN_SECTION), sectionName,
                                               singularEntityName(EN_ITEM), itemName,
                                               singularEntityName(EN_VALUE), fileName,
                                               PHRASE_NOT_FOUND],
                                              u'\n'))

  def _setCSVFile(filename, mode, encoding):
    if filename != u'-':
      if filename.startswith(u'./') or filename.startswith(u'.\\'):
        filename = os.path.join(os.getcwd(), filename[2:])
      else:
        filename = os.path.expanduser(filename)
      if not os.path.isabs(filename):
        filename = os.path.join(GC_Values[GC_DRIVE_DIR], filename)
    GM_Globals[GM_CSVFILE] = filename
    GM_Globals[GM_CSVFILE_MODE] = mode
    GM_Globals[GM_CSVFILE_ENCODING] = encoding
    GM_Globals[GM_CSVFILE_WRITE_HEADER] = True

  def _setSTDFile(filename, mode):
    filename = os.path.expanduser(filename)
    if not os.path.isabs(filename):
      filename = os.path.join(GC_Values[GC_DRIVE_DIR], filename)
    return openFile(filename, mode)

  if not GM_Globals[GM_PARSER]:
    homePath = os.path.expanduser(u'~')
    GM_Globals[GM_GAM_CFG_PATH] = os.environ.get(u'GAMCFGDIR', None)
    if GM_Globals[GM_GAM_CFG_PATH]:
      GM_Globals[GM_GAM_CFG_PATH] = os.path.expanduser(GM_Globals[GM_GAM_CFG_PATH])
    else:
      GM_Globals[GM_GAM_CFG_PATH] = os.path.join(homePath, u'.gam')
    GC_Defaults[GC_CONFIG_DIR] = GM_Globals[GM_GAM_CFG_PATH]
    GC_Defaults[GC_CACHE_DIR] = os.path.join(GM_Globals[GM_GAM_CFG_PATH], u'gamcache')
    GC_Defaults[GC_DRIVE_DIR] = os.path.join(homePath, u'Downloads')
    GM_Globals[GM_GAM_CFG_FILE] = os.path.join(GM_Globals[GM_GAM_CFG_PATH], FN_GAM_CFG)
    if not os.path.isfile(GM_Globals[GM_GAM_CFG_FILE]):
      for itemName, itemEntry in GC_VAR_INFO.items():
        if itemEntry[GC_VAR_TYPE] == GC_TYPE_DIRECTORY:
          _getDefault(itemName, itemEntry, None)
      oldGamPath = os.environ.get(u'OLDGAMPATH', GC_Defaults[GC_CONFIG_DIR])
      for itemName, itemEntry in GC_VAR_INFO.items():
        if itemEntry[GC_VAR_TYPE] != GC_TYPE_DIRECTORY:
          _getDefault(itemName, itemEntry, oldGamPath)
      if GC_Defaults[GC_OAUTH2SERVICE_JSON].find(u'.') == -1:
        GC_Defaults[GC_OAUTH2SERVICE_JSON] += u'.json'
      GM_Globals[GM_PARSER] = ConfigParser.SafeConfigParser(defaults=collections.OrderedDict(sorted(GC_Defaults.items(), key=lambda t: t[0])))
      _checkMakeDir(GC_CONFIG_DIR)
      _checkMakeDir(GC_CACHE_DIR)
      for itemName in GC_VAR_INFO:
        if GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_FILE:
          srcFile = os.path.expanduser(GM_Globals[GM_PARSER].get(ConfigParser.DEFAULTSECT, itemName, raw=True))
          _copyCfgFile(srcFile, GC_CONFIG_DIR, oldGamPath)
      _writeGamCfgFile(GM_Globals[GM_PARSER], GM_Globals[GM_GAM_CFG_FILE], action=ACTION_NAMES[AC_INITIALIZE][0])
    else:
      GM_Globals[GM_PARSER] = ConfigParser.SafeConfigParser(defaults=collections.OrderedDict(sorted(GC_Defaults.items(), key=lambda t: t[0])))
      _readGamCfgFile(GM_Globals[GM_PARSER], GM_Globals[GM_GAM_CFG_FILE])
    GM_Globals[GM_LAST_UPDATE_CHECK_TXT] = os.path.join(_getCfgDirectory(ConfigParser.DEFAULTSECT, GC_CONFIG_DIR), FN_LAST_UPDATE_CHECK_TXT)
    if not GM_Globals[GM_PARSER].get(ConfigParser.DEFAULTSECT, GC_NO_UPDATE_CHECK, raw=True):
      doGAMCheckForUpdates()
  status = {u'errors': False}
  sectionName = _getCfgSection(ConfigParser.DEFAULTSECT, GC_SECTION)
# select <SectionName> [save] [verify]
  if checkArgumentPresent([SELECT_CMD,]):
    sectionName = _selectSection()
    while CL_argvI < CL_argvLen:
      if checkArgumentPresent([u'save',]):
        GM_Globals[GM_PARSER].set(ConfigParser.DEFAULTSECT, GC_SECTION, sectionName)
        _writeGamCfgFile(GM_Globals[GM_PARSER], GM_Globals[GM_GAM_CFG_FILE], action=ACTION_NAMES[AC_SAVE][0])
      elif checkArgumentPresent([u'verify',]):
        _verifyValues(sectionName)
      else:
        break
# config (<VariableName> <Value>)* [save] [verify]
  if checkArgumentPresent([CONFIG_CMD,]):
    while CL_argvI < CL_argvLen:
      if checkArgumentPresent([u'save',]):
        _writeGamCfgFile(GM_Globals[GM_PARSER], GM_Globals[GM_GAM_CFG_FILE], action=ACTION_NAMES[AC_SAVE][0])
      elif checkArgumentPresent([u'verify',]):
        _verifyValues(sectionName)
      else:
        itemName = getChoice(GC_SETTABLE_VARS, defaultChoice=None)
        if not itemName:
          itemName = getChoice(GC_Defaults, defaultChoice=None)
          if itemName:
            invalidChoiceExit(GC_SETTABLE_VARS)
          break
        if GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_BOOLEAN:
          value = [FALSE, TRUE][getBoolean()]
        elif GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_INTEGER:
          minVal, maxVal = GC_VAR_INFO[itemName][GC_VAR_LIMITS]
          value = str(getInteger(minVal=minVal, maxVal=maxVal))
        else:
          value = getString(OB_STRING)
        GM_Globals[GM_PARSER].set(sectionName, itemName, value)
  prevExtraArgsTxt = GC_Values.get(GC_EXTRA_ARGS, None)
  prevOauth2serviceJson = GC_Values.get(GC_OAUTH2SERVICE_JSON, None)
# Assign directories first
  for itemName in GC_VAR_INFO:
    if GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_DIRECTORY:
      GC_Values[itemName] = _getCfgDirectory(sectionName, itemName)
# Everything else
  for itemName in GC_VAR_INFO:
    varType = GC_VAR_INFO[itemName][GC_VAR_TYPE]
    if varType == GC_TYPE_BOOLEAN:
      GC_Values[itemName] = _getCfgBoolean(sectionName, itemName)
    elif varType == GC_TYPE_INTEGER:
      GC_Values[itemName] = _getCfgInteger(sectionName, itemName)
    elif varType == GC_TYPE_STRING:
      GC_Values[itemName] = _getCfgString(sectionName, itemName)
    elif varType == GC_TYPE_FILE:
      GC_Values[itemName] = _getCfgFile(sectionName, itemName)
  if status[u'errors']:
    sys.exit(CONFIG_ERROR_RC)
# Create/set mode for oauth2.txt.lock
  if not GM_Globals[GM_OAUTH2_TXT_LOCK]:
    fileName = u'{0}.lock'.format(GC_Values[GC_OAUTH2_TXT])
    if not os.path.isfile(fileName):
      closeFile(openFile(fileName, mode=u'a'))
      os.chmod(fileName, 0666)
    GM_Globals[GM_OAUTH2_TXT_LOCK] = fileName
# Reset global variables if required
  httplib2.debuglevel = GC_Values[GC_DEBUG_LEVEL]
  if prevExtraArgsTxt != GC_Values[GC_EXTRA_ARGS]:
    GM_Globals[GM_EXTRA_ARGS_LIST] = [(u'prettyPrint', GC_Values[GC_DEBUG_LEVEL] > 0)]
    if GC_Values[GC_EXTRA_ARGS]:
      ea_config = ConfigParser.ConfigParser()
      ea_config.optionxform = str
      ea_config.read(GC_Values[GC_EXTRA_ARGS])
      GM_Globals[GM_EXTRA_ARGS_LIST].extend(ea_config.items(u'extra-args'))
  if prevOauth2serviceJson != GC_Values[GC_OAUTH2SERVICE_JSON]:
    GM_Globals[GM_OAUTH2SERVICE_JSON_DATA] = None
    GM_Globals[GM_OAUTH2_CLIENT_ID] = None
# redirect [csv <FileName> [append] [charset <CharSet>]] [stdout <FileName> [append]] [stderr <FileName> [append]]
  if checkArgumentPresent([REDIRECT_CMD,]):
    while CL_argvI < CL_argvLen:
      myarg = getChoice([u'csv', u'stdout', u'stderr'], defaultChoice=None)
      if not myarg:
        break
      filename = re.sub(r'{{Section}}', sectionName, getString(OB_FILE_NAME))
      if myarg == u'csv':
        mode = [u'wb', u'ab'][checkArgumentPresent([u'append',])]
        encoding = getCharSet()
        _setCSVFile(filename, mode, encoding)
      elif myarg == u'stdout':
        sys.stdout = _setSTDFile(filename, [u'w', u'a'][checkArgumentPresent([u'append',])])
        if GM_Globals[GM_CSVFILE] == u'-':
          GM_Globals[GM_CSVFILE] = None
      else:
        sys.stderr = _setSTDFile(filename, [u'w', u'a'][checkArgumentPresent([u'append',])])
  if not GM_Globals[GM_CSVFILE]:
    _setCSVFile(u'-', u'a', GC_Values[GC_CHARSET])
# If no select/options commands were executed or some were and there are more arguments on the command line,
# warn if the json files are missing and return True
  if (CL_argvI == 1) or (CL_argvI < CL_argvLen):
    _chkCfgDirectories(sectionName)
    _chkCfgFiles(sectionName)
    if GC_Values[GC_NO_CACHE]:
      GM_Globals[GM_CACHE_DIR] = None
      GM_Globals[GM_CACHE_DISCOVERY_ONLY] = False
    else:
      GM_Globals[GM_CACHE_DIR] = GC_Values[GC_CACHE_DIR]
      GM_Globals[GM_CACHE_DISCOVERY_ONLY] = GC_Values[GC_CACHE_DISCOVERY_ONLY]
    return True
# We're done, nothing else to do
  return False

def doGAMCheckForUpdates(forceCheck=False):
  import urllib2, calendar
  current_version = __version__
  now_time = calendar.timegm(time.gmtime())
  if not forceCheck:
    last_check_time = readFile(GM_Globals[GM_LAST_UPDATE_CHECK_TXT], continueOnError=True, displayError=forceCheck)
    if last_check_time == None:
      last_check_time = 0
    if last_check_time > now_time-604800:
      return
  try:
    c = urllib2.urlopen(GAM_APPSPOT_LATEST_VERSION)
    latest_version = c.read().strip()
    if forceCheck or (latest_version > current_version):
      printKeyValueList([u'Version', u'Check', u'Current', u'{0}'.format(current_version), u'Latest', u'{0}'.format(latest_version)])
    if latest_version <= current_version:
      writeFile(GM_Globals[GM_LAST_UPDATE_CHECK_TXT], str(now_time), continueOnError=True, displayError=forceCheck)
      return
    a = urllib2.urlopen(GAM_APPSPOT_LATEST_VERSION_ANNOUNCEMENT)
    announcement = a.read()
    sys.stderr.write(announcement)
    try:
      printLine(MESSAGE_HIT_CONTROL_C_TO_UPDATE)
      time.sleep(15)
    except KeyboardInterrupt:
      import webbrowser
      webbrowser.open(GAM_RELEASES)
      printLine(MESSAGE_GAM_EXITING_FOR_UPDATE)
      sys.exit(0)
    writeFile(GM_Globals[GM_LAST_UPDATE_CHECK_TXT], str(now_time), continueOnError=True, displayError=forceCheck)
    return
  except (urllib2.HTTPError, urllib2.URLError):
    return

def handleOAuthTokenError(e, soft_errors):
  if e.message in OAUTH2_TOKEN_ERRORS:
    if soft_errors:
      return None
    if not GM_Globals[GM_CURRENT_API_USER]:
      APIAccessDeniedExit()
    systemErrorExit(SERVICE_NOT_APPLICABLE_RC, MESSAGE_SERVICE_NOT_APPLICABLE.format(GM_Globals[GM_CURRENT_API_USER]))
  stderrErrorMsg(u'Authentication Token Error - {0}'.format(e))
  APIAccessDeniedExit()

def getCredentialsForScope(oauth2Scope, storageOnly=False):
  try:
    storage = MultiprocessFileStorage(GC_Values[GC_OAUTH2_TXT], oauth2Scope)
    if storageOnly:
      return storage
    return storage.get()
  except IOError as e:
    systemErrorExit(FILE_ERROR_RC, e)

def getClientCredentials(oauth2Scope):
  credentials = getCredentialsForScope(oauth2Scope)
  if not credentials or credentials.invalid:
    systemErrorExit(OAUTH2_TXT_REQUIRED_RC, u'{0}: {1} {2}'.format(singularEntityName(EN_OAUTH2_TXT_FILE), GC_Values[GC_OAUTH2_TXT], PHRASE_DOES_NOT_EXIST_OR_HAS_INVALID_FORMAT))
  credentials.user_agent = GAM_INFO
  return credentials

def getSvcAcctCredentials(scopes, act_as):
  try:
    if not GM_Globals[GM_OAUTH2SERVICE_JSON_DATA]:
      json_string = readFile(GC_Values[GC_OAUTH2SERVICE_JSON], continueOnError=True, displayError=True)
      if not json_string:
        printLine(MESSAGE_WIKI_INSTRUCTIONS_OAUTH2SERVICE_JSON)
        printLine(GAM_WIKI_CREATE_CLIENT_SECRETS)
        systemErrorExit(OAUTH2SERVICE_JSON_REQUIRED_RC, None)
      GM_Globals[GM_OAUTH2SERVICE_JSON_DATA] = json.loads(json_string)
    credentials = oauth2client.service_account.ServiceAccountCredentials.from_json_keyfile_dict(GM_Globals[GM_OAUTH2SERVICE_JSON_DATA], scopes)
    credentials = credentials.create_delegated(act_as)
    credentials.user_agent = GAM_INFO
    serialization_data = credentials.serialization_data
    GM_Globals[GM_ADMIN] = serialization_data[u'client_email']
    GM_Globals[GM_OAUTH2_CLIENT_ID] = serialization_data[u'client_id']
    return credentials
  except (ValueError, KeyError):
    printLine(MESSAGE_WIKI_INSTRUCTIONS_OAUTH2SERVICE_JSON)
    printLine(GAM_WIKI_CREATE_CLIENT_SECRETS)
    invalidJSONExit(GC_Values[GC_OAUTH2SERVICE_JSON])

def getGDataOAuthToken(gdataObj, credentials=None):
  if not credentials:
    credentials = getClientCredentials(OAUTH2_GDATA_SCOPES)
  try:
    credentials.refresh(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL]))
  except httplib2.ServerNotFoundError as e:
    systemErrorExit(NETWORK_ERROR_RC, e)
  except oauth2client.client.AccessTokenRefreshError as e:
    return handleOAuthTokenError(e, False)
  gdataObj.additional_headers[u'Authorization'] = u'Bearer {0}'.format(credentials.access_token)
  if not GC_Values[GC_DOMAIN]:
    GC_Values[GC_DOMAIN] = credentials.id_token.get(u'hd', u'UNKNOWN').lower()
  if not GC_Values[GC_CUSTOMER_ID]:
    GC_Values[GC_CUSTOMER_ID] = MY_CUSTOMER
  GM_Globals[GM_ADMIN] = credentials.id_token.get(u'email', u'UNKNOWN').lower()
  GM_Globals[GM_OAUTH2_CLIENT_ID] = credentials.client_id
  gdataObj.domain = GC_Values[GC_DOMAIN]
  gdataObj.source = GAM_INFO
  return True

def checkGDataError(e, service):
  # First check for errors that need special handling
  if e[0].get(u'reason', u'') in [u'Token invalid - Invalid token: Stateless token expired', u'Token invalid - Invalid token: Token not found']:
    keep_domain = service.domain
    getGDataOAuthToken(service)
    service.domain = keep_domain
    return (GDATA_TOKEN_EXPIRED, e[0][u'reason'])
  if e.error_code == 600:
    if e[0][u'body'].startswith(u'Quota exceeded for the current request'):
      return (GDATA_QUOTA_EXCEEDED, e[0][u'body'])
    if e[0][u'body'].startswith(u'Request rate higher than configured'):
      return (GDATA_QUOTA_EXCEEDED, e[0][u'body'])
    if e[0][u'reason'] == u'Bad Gateway':
      return (GDATA_BAD_GATEWAY, e[0][u'reason'])
    if e[0][u'reason'] == u'Service Unavailable':
      return (GDATA_SERVICE_UNAVAILABLE, e[0][u'reason'])
    if e[0][u'reason'] == u'Internal Server Error':
      return (GDATA_INTERNAL_SERVER_ERROR, e[0][u'reason'])
    if e[0][u'reason'] == u'Token invalid - Invalid token: Token disabled, revoked, or expired.':
      return (GDATA_TOKEN_INVALID, u'Token disabled, revoked, or expired. Please delete and re-create oauth.txt')
    if e[0][u'reason'] == u'Token invalid - AuthSub token has wrong scope':
      return (GDATA_INSUFFICIENT_PERMISSIONS, e[0][u'reason'])
    if e[0][u'reason'].startswith(u'Only administrators can request entries belonging to'):
      return (GDATA_INSUFFICIENT_PERMISSIONS, e[0][u'reason'])
    if e[0][u'reason'] == u'You are not authorized to access this API':
      return (GDATA_INSUFFICIENT_PERMISSIONS, e[0][u'reason'])
    if e[0][u'reason'] == u'Invalid domain.':
      return (GDATA_INVALID_DOMAIN, e[0][u'reason'])
    if e[0][u'reason'].startswith(u'You are not authorized to perform operations on the domain'):
      return (GDATA_INVALID_DOMAIN, e[0][u'reason'])
    if e[0][u'reason'] == u'Bad Request':
      if u'already exists' in e[0][u'body']:
        return (GDATA_ENTITY_EXISTS, e[0][u'body'])
      return (GDATA_BAD_REQUEST, e[0][u'body'])
    if e[0][u'reason'] == u'Forbidden':
      return (GDATA_FORBIDDEN, e[0][u'body'])
    if e[0][u'reason'] == u'Not Found':
      return (GDATA_NOT_FOUND, e[0][u'body'])
    if e[0][u'reason'] == u'Precondition Failed':
      return (GDATA_PRECONDITION_FAILED, e[0][u'reason'])
  elif e.error_code == 602:
    if e[0][u'reason'] == u'Bad Request':
      return (GDATA_BAD_REQUEST, e[0][u'body'])

  # We got a "normal" error, define the mapping below
  error_code_map = {
    1000: e[0][u'reason'],
    1001: e[0][u'reason'],
    1002: u'Unauthorized and forbidden',
    1100: u'User deleted recently',
    1200: u'Domain user limit exceeded',
    1201: u'Domain alias limit exceeded',
    1202: u'Domain suspended',
    1203: u'Domain feature unavailable',
    1300: u'Entity %s exists' % getattr(e, u'invalidInput', u'<unknown>'),
    1301: u'Entity %s Does Not Exist' % getattr(e, u'invalidInput', u'<unknown>'),
    1302: u'Entity Name Is Reserved',
    1303: u'Entity %s name not valid' % getattr(e, u'invalidInput', u'<unknown>'),
    1306: u'%s has members. Cannot delete.' % getattr(e, u'invalidInput', u'<unknown>'),
    1400: u'Invalid Given Name',
    1401: u'Invalid Family Name',
    1402: u'Invalid Password',
    1403: u'Invalid Username',
    1404: u'Invalid Hash Function Name',
    1405: u'Invalid Hash Digest Length',
    1406: u'Invalid Email Address',
    1407: u'Invalid Query Parameter Value',
    1408: u'Invalid SSO Signing Key',
    1409: u'Invalid Encryption Public Key',
    1410: u'Feature Unavailable For User',
    1500: u'Too Many Recipients On Email List',
    1501: u'Too Many Aliases For User',
    1502: u'Too Many Delegates For User',
    1601: u'Duplicate Destinations',
    1602: u'Too Many Destinations',
    1603: u'Invalid Route Address',
    1700: u'Group Cannot Contain Cycle',
    1800: u'Group Cannot Contain Cycle',
    1801: u'Invalid value %s' % getattr(e, u'invalidInput', u'<unknown>'),
  }
  return (e.error_code, error_code_map.get(e.error_code, u'Unknown Error: {0}'.format(str(e))))

def waitOnFailure(n, retries, error_code, error_message):
  wait_on_fail = min(2 ** n, 60) + float(random.randint(1, 1000)) / 1000
  if n > 3:
    sys.stderr.write(u'Temporary error: {0} - {1}. Backing off {2} seconds...'.format(error_code, error_message, int(wait_on_fail)))
  time.sleep(wait_on_fail)
  if n > 3:
    sys.stderr.write(u'attempt {0}/{1}\n'.format(n+1, retries))

class GData_badRequest(Exception): pass
class GData_doesNotExist(Exception): pass
class GData_entityExists(Exception): pass
class GData_forbidden(Exception): pass
class GData_insufficientPermissions(Exception): pass
class GData_internalServerError(Exception): pass
class GData_invalidDomain(Exception): pass
class GData_invalidValue(Exception): pass
class GData_nameNotValid(Exception): pass
class GData_notFound(Exception): pass
class GData_preconditionFailed(Exception): pass
class GData_serviceNotApplicable(Exception): pass

GDATA_ERROR_CODE_EXCEPTION_MAP = {
  GDATA_BAD_REQUEST: GData_badRequest,
  GDATA_DOES_NOT_EXIST: GData_doesNotExist,
  GDATA_ENTITY_EXISTS: GData_entityExists,
  GDATA_FORBIDDEN: GData_forbidden,
  GDATA_INSUFFICIENT_PERMISSIONS: GData_insufficientPermissions,
  GDATA_INTERNAL_SERVER_ERROR: GData_internalServerError,
  GDATA_INVALID_DOMAIN: GData_invalidDomain,
  GDATA_INVALID_VALUE: GData_invalidValue,
  GDATA_NAME_NOT_VALID: GData_nameNotValid,
  GDATA_NOT_FOUND: GData_notFound,
  GDATA_PRECONDITION_FAILED: GData_preconditionFailed,
  GDATA_SERVICE_NOT_APPLICABLE: GData_serviceNotApplicable,
  }

def callGData(service, function,
              soft_errors=False, throw_errors=[], retry_errors=[],
              **kwargs):
  import gdata.apps.service
  method = getattr(service, function)
  retries = 10
  for n in range(1, retries+1):
    try:
      return method(**kwargs)
    except gdata.apps.service.AppsForYourDomainException as e:
      error_code, error_message = checkGDataError(e, service)
      if error_code in throw_errors:
        if error_code in GDATA_ERROR_CODE_EXCEPTION_MAP:
          raise GDATA_ERROR_CODE_EXCEPTION_MAP[error_code](error_message)
        raise
      if (n != retries) and (error_code in GDATA_NON_TERMINATING_ERRORS+retry_errors):
        waitOnFailure(n, retries, error_code, error_message)
        continue
      if soft_errors:
        stderrErrorMsg(u'{0} - {1}{2}'.format(error_code, error_message, [u'', u': Giving up.\n'][n > 1]))
        return None
      if error_code == GDATA_INSUFFICIENT_PERMISSIONS:
        APIAccessDeniedExit()
      systemErrorExit(GOOGLE_API_ERROR_RC, u'{0} - {1}'.format(error_code, error_message))
    except oauth2client.client.AccessTokenRefreshError as e:
      handleOAuthTokenError(e, GDATA_SERVICE_NOT_APPLICABLE in throw_errors)
      raise GDATA_ERROR_CODE_EXCEPTION_MAP[GDATA_SERVICE_NOT_APPLICABLE](e.message)
    except socket.error as e:
      if n != retries:
        waitOnFailure(n, retries, e.errno, e.strerror)
        continue
      if soft_errors:
        stderrErrorMsg(u'{0} - {1}{2}'.format(e.errno, e.strerror, [u'', u': Giving up.\n'][n > 1]))
        return None
      systemErrorExit(SOCKET_ERROR_RC, e.strerror)

def callGDataPages(service, function,
                   page_message=None,
                   soft_errors=False, throw_errors=[], retry_errors=[],
                   uri=None,
                   **kwargs):
  nextLink = None
  allResults = []
  totalItems = 0
  while True:
    this_page = callGData(service, function,
                          soft_errors=soft_errors, throw_errors=throw_errors, retry_errors=retry_errors,
                          uri=uri,
                          **kwargs)
    if this_page:
      nextLink = this_page.GetNextLink()
      pageItems = len(this_page.entry)
      totalItems += pageItems
      allResults.extend(this_page.entry)
    else:
      nextLink = None
      pageItems = 0
    if page_message:
      if GM_Globals[GM_GETTING_SHOW_TOTAL]:
        show_message = page_message.replace(TOTAL_ITEMS_MARKER, str(totalItems))
        count = totalItems
      else:
        show_message = page_message.replace(NUM_ITEMS_MARKER, str(pageItems))
        count = pageItems if nextLink else totalItems
      sys.stderr.write(u'\r')
      sys.stderr.flush()
      gettingItemInfo = GM_Globals[GM_GETTING_ENTITY_ITEM][[0, 1][count == 1]]
      sys.stderr.write(show_message.format(gettingItemInfo))
    if nextLink is None:
      if page_message and (page_message[-1] != u'\n'):
        sys.stderr.write(u'\r\n')
        sys.stderr.flush()
      return allResults
    uri = nextLink.href

def checkGAPIError(e, soft_errors=False, silent_errors=False, retryOnHttpError=False, service=None):
  try:
    error = json.loads(e.content)
  except ValueError:
    if (e.resp[u'status'] == u'503') and (e.content.startswith(u'Quota exceeded for the current request')):
      return (e.resp[u'status'], GAPI_QUOTA_EXCEEDED, e.content)
    if (e.resp[u'status'] == u'403') and (e.content.startswith(u'Request rate higher than configured')):
      return (e.resp[u'status'], GAPI_QUOTA_EXCEEDED, e.content)
    if (e.resp[u'status'] == u'403') and (u'Invalid domain.' in e.content):
      error = {u'error': {u'code': 403, u'errors': [{u'reason': GAPI_NOT_FOUND, u'message': u'Domain not found'}]}}
    elif (e.resp[u'status'] == u'400') and (u'InvalidSsoSigningKey' in e.content):
      error = {u'error': {u'code': 400, u'errors': [{u'reason': GAPI_INVALID, u'message': u'InvalidSsoSigningKey'}]}}
    elif (e.resp[u'status'] == u'400') and (u'UnknownError' in e.content):
      error = {u'error': {u'code': 400, u'errors': [{u'reason': GAPI_INVALID, u'message': u'UnknownError'}]}}
    elif retryOnHttpError:
      service._http.request.credentials.refresh(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL]))
      return (-1, None, None)
    elif soft_errors:
      if not silent_errors:
        stderrErrorMsg(e.content)
      return (0, None, None)
    else:
      systemErrorExit(HTTP_ERROR_RC, e.content)
  if u'error' in error:
    http_status = error[u'error'][u'code']
    try:
      message = error[u'error'][u'errors'][0][u'message']
    except KeyError:
      message = error[u'error'][u'message']
    if http_status == 500:
      if not message:
        message = PHRASE_UNKNOWN
        error = {u'error': {u'errors': [{u'reason': GAPI_UNKNOWN_ERROR, u'message': message}]}}
      elif u'Backend Error' in message:
        error = {u'error': {u'errors': [{u'reason': GAPI_BACKEND_ERROR, u'message': message}]}}
  else:
    if u'error_description' in error:
      if error[u'error_description'] == u'Invalid Value':
        message = error[u'error_description']
        http_status = 400
        error = {u'error': {u'errors': [{u'reason': GAPI_INVALID, u'message': message}]}}
      else:
        systemErrorExit(GOOGLE_API_ERROR_RC, str(error))
    else:
      systemErrorExit(GOOGLE_API_ERROR_RC, str(error))
  try:
    reason = error[u'error'][u'errors'][0][u'reason']
    if reason == GAPI_NOT_FOUND:
      if u'userKey' in message:
        reason = GAPI_USER_NOT_FOUND
      elif u'groupKey' in message:
        reason = GAPI_GROUP_NOT_FOUND
      elif u'memberKey' in message:
        reason = GAPI_MEMBER_NOT_FOUND
      elif u'Org unit not found' in message:
        reason = GAPI_ORGUNIT_NOT_FOUND
      elif u'File not found' in message:
        reason = GAPI_FILE_NOT_FOUND
      elif u'Permission not found' in message:
        reason = GAPI_PERMISSION_NOT_FOUND
      elif u'resource_id' in message:
        reason = GAPI_RESOURCE_ID_NOT_FOUND
      elif u'resourceId' in message:
        reason = GAPI_RESOURCE_ID_NOT_FOUND
      elif (u'Domain not found' in message) or (u'domain' in message):
        reason = GAPI_DOMAIN_NOT_FOUND
      elif u'Domain alias does not exist' in message:
        reason = GAPI_DOMAIN_ALIAS_NOT_FOUND
      elif u'photo' in message:
        reason = GAPI_PHOTO_NOT_FOUND
      elif u'Resource Not Found' in message:
        reason = GAPI_RESOURCE_NOT_FOUND
      elif u'Customer doesn\'t exist' in message:
        reason = GAPI_CUSTOMER_NOT_FOUND
    elif reason == GAPI_RESOURCE_NOT_FOUND:
      if u'resourceId' in message:
        reason = GAPI_RESOURCE_ID_NOT_FOUND
    elif reason == GAPI_INVALID:
      if u'userId' in message:
        reason = GAPI_USER_NOT_FOUND
      elif u'memberKey' in message:
        reason = GAPI_INVALID_MEMBER
      elif u'Invalid Ou Id' in message:
        reason = GAPI_INVALID_ORGUNIT
      elif u'Invalid Input: INVALID_OU_ID' in message:
        reason = GAPI_INVALID_ORGUNIT
      elif u'Invalid Parent Orgunit Id' in message:
        reason = GAPI_INVALID_PARENT_ORGUNIT
      elif u'Invalid scope value' in message:
        reason = GAPI_INVALID_SCOPE_VALUE
      elif u'A system error has occurred' in message:
        reason = GAPI_SYSTEM_ERROR
      elif u'Invalid Input: custom_schema' in message:
        reason = GAPI_INVALID_SCHEMA_VALUE
      elif u'New domain name is not a verified secondary domain' in message:
        reason = GAPI_DOMAIN_NOT_VERIFIED_SECONDARY
      elif u'Invalid query' in message:
        reason = GAPI_INVALID_QUERY
      elif u'Invalid Customer Id' in message:
        reason = GAPI_INVALID_CUSTOMER_ID
      elif u'Invalid Input: resource' in message:
        reason = GAPI_INVALID_RESOURCE
      elif u'Invalid Input:' in message:
        reason = GAPI_INVALID_INPUT
    elif reason == GAPI_REQUIRED:
      if u'memberKey' in message:
        reason = GAPI_MEMBER_NOT_FOUND
      elif u'Login Required' in message:
        reason = GAPI_LOGIN_REQUIRED
    elif reason == GAPI_CONDITION_NOT_MET:
      if u'undelete' in message:
        reason = GAPI_DELETED_USER_NOT_FOUND
      elif u'Cyclic memberships not allowed' in message:
        reason = GAPI_CYCLIC_MEMBERSHIPS_NOT_ALLOWED
    elif reason == GAPI_INVALID_SHARING_REQUEST:
      loc = message.find(u'User message: ')
      if loc != 1:
        message = message[loc+15:]
    elif reason == GAPI_ABORTED:
      if u'Label name exists or conflicts' in message:
        reason = GAPI_DUPLICATE
    elif reason == GAPI_FAILED_PRECONDITION:
      if u'Bad Request' in message:
        reason = GAPI_BAD_REQUEST
      elif u'Mail service not enabled' in message:
        reason = GAPI_SERVICE_NOT_AVAILABLE
    elif reason == GAPI_INVALID_ARGUMENT:
      if u'Cannot delete primary send-as' in message:
        reason = GAPI_CANNOT_DELETE_PRIMARY_SENDAS
  except KeyError:
    reason = http_status
  return (http_status, reason, message)

class GAPI_aborted(Exception): pass
class GAPI_alreadyExists(Exception): pass
class GAPI_authError(Exception): pass
class GAPI_backendError(Exception): pass
class GAPI_badRequest(Exception): pass
class GAPI_cannotChangeOwnAcl(Exception): pass
class GAPI_cannotChangeOwnerAcl(Exception): pass
class GAPI_cannotDeletePrimaryCalendar(Exception): pass
class GAPI_cannotDeletePrimarySendAs(Exception): pass
class GAPI_conditionNotMet(Exception): pass
class GAPI_customerNotFound(Exception): pass
class GAPI_cyclicMembershipsNotAllowed(Exception): pass
class GAPI_deleted(Exception): pass
class GAPI_deletedUserNotFound(Exception): pass
class GAPI_domainNotFound(Exception): pass
class GAPI_domainNotVerifiedSecondary(Exception): pass
class GAPI_domainAliasNotFound(Exception): pass
class GAPI_duplicate(Exception): pass
class GAPI_failedPrecondition(Exception): pass
class GAPI_fileNotFound(Exception): pass
class GAPI_forbidden(Exception): pass
class GAPI_groupNotFound(Exception): pass
class GAPI_insufficientPermissions(Exception): pass
class GAPI_internalError(Exception): pass
class GAPI_invalid(Exception): pass
class GAPI_invalidArgument(Exception): pass
class GAPI_invalidCustomerId(Exception): pass
class GAPI_invalidInput(Exception): pass
class GAPI_invalidMember(Exception): pass
class GAPI_invalidOrgunit(Exception): pass
class GAPI_invalidParentOrgunit(Exception): pass
class GAPI_invalidQuery(Exception): pass
class GAPI_invalidResource(Exception): pass
class GAPI_invalidSchemaValue(Exception): pass
class GAPI_invalidScopeValue(Exception): pass
class GAPI_invalidSharingRequest(Exception): pass
class GAPI_loginRequired(Exception): pass
class GAPI_memberNotFound(Exception): pass
class GAPI_notFound(Exception): pass
class GAPI_notImplemented(Exception): pass
class GAPI_orgunitNotFound(Exception): pass
class GAPI_permissionDenied(Exception): pass
class GAPI_permissionNotFound(Exception): pass
class GAPI_photoNotFound(Exception): pass
class GAPI_required(Exception): pass
class GAPI_resourceNotFound(Exception): pass
class GAPI_resourceIdNotFound(Exception): pass
class GAPI_serviceLimit(Exception): pass
class GAPI_serviceNotAvailable(Exception): pass
class GAPI_systemError(Exception): pass
class GAPI_timeRangeEmpty(Exception): pass
class GAPI_unknownError(Exception): pass
class GAPI_userNotFound(Exception): pass

GAPI_REASON_EXCEPTION_MAP = {
  GAPI_ABORTED: GAPI_aborted,
  GAPI_ALREADY_EXISTS: GAPI_alreadyExists,
  GAPI_AUTH_ERROR: GAPI_authError,
  GAPI_BACKEND_ERROR: GAPI_backendError,
  GAPI_BAD_REQUEST: GAPI_badRequest,
  GAPI_CANNOT_CHANGE_OWN_ACL: GAPI_cannotChangeOwnAcl,
  GAPI_CANNOT_CHANGE_OWNER_ACL: GAPI_cannotChangeOwnerAcl,
  GAPI_CANNOT_DELETE_PRIMARY_CALENDAR: GAPI_cannotDeletePrimaryCalendar,
  GAPI_CANNOT_DELETE_PRIMARY_SENDAS: GAPI_cannotDeletePrimarySendAs,
  GAPI_CONDITION_NOT_MET: GAPI_conditionNotMet,
  GAPI_CUSTOMER_NOT_FOUND: GAPI_customerNotFound,
  GAPI_CYCLIC_MEMBERSHIPS_NOT_ALLOWED: GAPI_cyclicMembershipsNotAllowed,
  GAPI_DELETED: GAPI_deleted,
  GAPI_DELETED_USER_NOT_FOUND: GAPI_deletedUserNotFound,
  GAPI_DOMAIN_ALIAS_NOT_FOUND: GAPI_domainAliasNotFound,
  GAPI_DOMAIN_NOT_FOUND: GAPI_domainNotFound,
  GAPI_DOMAIN_NOT_VERIFIED_SECONDARY: GAPI_domainNotVerifiedSecondary,
  GAPI_DUPLICATE: GAPI_duplicate,
  GAPI_FAILED_PRECONDITION: GAPI_failedPrecondition,
  GAPI_FILE_NOT_FOUND: GAPI_fileNotFound,
  GAPI_FORBIDDEN: GAPI_forbidden,
  GAPI_GROUP_NOT_FOUND: GAPI_groupNotFound,
  GAPI_INSUFFICIENT_PERMISSIONS: GAPI_insufficientPermissions,
  GAPI_INTERNAL_ERROR: GAPI_internalError,
  GAPI_INVALID: GAPI_invalid,
  GAPI_INVALID_ARGUMENT: GAPI_invalidArgument,
  GAPI_INVALID_CUSTOMER_ID: GAPI_invalidCustomerId,
  GAPI_INVALID_INPUT: GAPI_invalidInput,
  GAPI_INVALID_MEMBER: GAPI_invalidMember,
  GAPI_INVALID_ORGUNIT: GAPI_invalidOrgunit,
  GAPI_INVALID_PARENT_ORGUNIT: GAPI_invalidParentOrgunit,
  GAPI_INVALID_QUERY: GAPI_invalidQuery,
  GAPI_INVALID_RESOURCE: GAPI_invalidResource,
  GAPI_INVALID_SCHEMA_VALUE: GAPI_invalidSchemaValue,
  GAPI_INVALID_SCOPE_VALUE: GAPI_invalidScopeValue,
  GAPI_INVALID_SHARING_REQUEST: GAPI_invalidSharingRequest,
  GAPI_LOGIN_REQUIRED: GAPI_loginRequired,
  GAPI_MEMBER_NOT_FOUND: GAPI_memberNotFound,
  GAPI_NOT_FOUND: GAPI_notFound,
  GAPI_NOT_IMPLEMENTED: GAPI_notImplemented,
  GAPI_ORGUNIT_NOT_FOUND: GAPI_orgunitNotFound,
  GAPI_PERMISSION_DENIED: GAPI_permissionDenied,
  GAPI_PERMISSION_NOT_FOUND: GAPI_permissionNotFound,
  GAPI_PHOTO_NOT_FOUND: GAPI_photoNotFound,
  GAPI_REQUIRED: GAPI_required,
  GAPI_RESOURCE_ID_NOT_FOUND: GAPI_resourceIdNotFound,
  GAPI_RESOURCE_NOT_FOUND: GAPI_resourceNotFound,
  GAPI_SERVICE_LIMIT: GAPI_serviceLimit,
  GAPI_SERVICE_NOT_AVAILABLE: GAPI_serviceNotAvailable,
  GAPI_SYSTEM_ERROR: GAPI_systemError,
  GAPI_TIME_RANGE_EMPTY: GAPI_timeRangeEmpty,
  GAPI_UNKNOWN_ERROR: GAPI_unknownError,
  GAPI_USER_NOT_FOUND: GAPI_userNotFound,
  }

def callGAPI(service, function,
             silent_errors=False, soft_errors=False, throw_reasons=[], retry_reasons=[],
             **kwargs):
  method = getattr(service, function)
  retries = 10
  parameters = dict(kwargs.items()+GM_Globals[GM_EXTRA_ARGS_LIST])
  for n in range(1, retries+1):
    try:
      return method(**parameters).execute()
    except googleapiclient.errors.HttpError as e:
      http_status, reason, message = checkGAPIError(e, soft_errors=soft_errors, silent_errors=silent_errors, retryOnHttpError=n < 3, service=service)
      if http_status == -1:
        continue
      if http_status == 0:
        return None
      if reason in throw_reasons:
        if reason in GAPI_REASON_EXCEPTION_MAP:
          raise GAPI_REASON_EXCEPTION_MAP[reason](message)
        raise e
      if (n != retries) and (reason in GAPI_DEFAULT_RETRY_REASONS+retry_reasons):
        waitOnFailure(n, retries, reason, message)
        continue
      if soft_errors:
        stderrErrorMsg(u'{0}: {1} - {2}{3}'.format(http_status, reason, message, [u'', u': Giving up.\n'][n > 1]))
        return None
      if reason == GAPI_INSUFFICIENT_PERMISSIONS:
        APIAccessDeniedExit()
      systemErrorExit(HTTP_ERROR_RC, formatHTTPError(http_status, reason, message))
    except oauth2client.client.AccessTokenRefreshError as e:
      handleOAuthTokenError(e, GAPI_SERVICE_NOT_AVAILABLE in throw_reasons)
      raise GAPI_REASON_EXCEPTION_MAP[GAPI_SERVICE_NOT_AVAILABLE](e.message)
    except httplib2.CertificateValidationUnsupported:
      noPythonSSLExit()
    except socket.error as e:
      if n != retries:
        waitOnFailure(n, retries, e.errno, e.strerror)
        continue
      if soft_errors:
        stderrErrorMsg(u'{0} - {1}{2}'.format(e.errno, e.strerror, [u'', u': Giving up.\n'][n > 1]))
        return None
      systemErrorExit(SOCKET_ERROR_RC, e.strerror)
    except TypeError as e:
      systemErrorExit(GOOGLE_API_ERROR_RC, e)

def callGAPIpages(service, function, items,
                  page_message=None, message_attribute=None, maxItems=0,
                  throw_reasons=[], retry_reasons=[],
                  **kwargs):
  pageToken = None
  allResults = []
  totalItems = 0
  maxResults = kwargs.get(u'maxResults', 0)
  tweakMaxResults = maxItems and maxResults
  while True:
    if tweakMaxResults and maxItems-totalItems < maxResults:
      kwargs[u'maxResults'] = maxItems-totalItems
    results = callGAPI(service, function,
                       throw_reasons=throw_reasons, retry_reasons=retry_reasons,
                       pageToken=pageToken,
                       **kwargs)
    if results:
      pageToken = results.get(u'nextPageToken')
      if items in results:
        pageItems = len(results[items])
        totalItems += pageItems
        allResults.extend(results[items])
      else:
        results = {items: []}
        pageItems = 0
    else:
      pageToken = None
      results = {items: []}
      pageItems = 0
    if page_message:
      if GM_Globals[GM_GETTING_SHOW_TOTAL]:
        show_message = page_message.replace(TOTAL_ITEMS_MARKER, str(totalItems))
        count = totalItems
      else:
        show_message = page_message.replace(NUM_ITEMS_MARKER, str(pageItems))
        count = pageItems if pageToken else totalItems
      if message_attribute:
        try:
          show_message = show_message.replace(FIRST_ITEM_MARKER, str(results[items][0][message_attribute]))
          show_message = show_message.replace(LAST_ITEM_MARKER, str(results[items][-1][message_attribute]))
        except (IndexError, KeyError):
          show_message = show_message.replace(FIRST_ITEM_MARKER, u'')
          show_message = show_message.replace(LAST_ITEM_MARKER, u'')
      sys.stderr.write(u'\r')
      sys.stderr.flush()
      gettingItemInfo = GM_Globals[GM_GETTING_ENTITY_ITEM][[0, 1][count == 1]]
      sys.stderr.write(show_message.format(gettingItemInfo))
    if not pageToken or maxItems and totalItems >= maxItems:
      if page_message and (page_message[-1] != u'\n'):
        sys.stderr.write(u'\r\n')
        sys.stderr.flush()
      return allResults

def callGAPIitems(service, function, items,
                  throw_reasons=[], retry_reasons=[],
                  **kwargs):
  results = callGAPI(service, function,
                     throw_reasons=throw_reasons, retry_reasons=retry_reasons,
                     **kwargs)
  if results:
    return results.get(items, [])
  return []

class GCP_cantModifyFinishedJob(Exception): pass
class GCP_failedToShareThePrinter(Exception): pass
class GCP_noPrintJobs(Exception): pass
class GCP_unknownJobId(Exception): pass
class GCP_unknownPrinter(Exception): pass
class GCP_userIsNotAuthorized(Exception): pass

GCP_MESSAGE_EXCEPTION_MAP = {
  GCP_CANT_MODIFY_FINISHED_JOB: GCP_cantModifyFinishedJob,
  GCP_FAILED_TO_SHARE_THE_PRINTER: GCP_failedToShareThePrinter,
  GCP_NO_PRINT_JOBS: GCP_noPrintJobs,
  GCP_UNKNOWN_JOB_ID: GCP_unknownJobId,
  GCP_UNKNOWN_PRINTER: GCP_unknownPrinter,
  GCP_USER_IS_NOT_AUTHORIZED: GCP_userIsNotAuthorized,
  }

def checkCloudPrintResult(result, throw_messages=[]):
  if isinstance(result, str):
    try:
      result = json.loads(result)
    except ValueError:
      systemErrorExit(JSON_LOADS_ERROR_RC, result)
  if not result[u'success']:
    message = result[u'message']
    if message in throw_messages:
      if message in GCP_MESSAGE_EXCEPTION_MAP:
        raise GCP_MESSAGE_EXCEPTION_MAP[message](message)
    systemErrorExit(AC_FAILED_RC, u'{0}: {1}'.format(result[u'errorCode'], result[u'message']))
  return result

def callGCP(service, function,
            throw_messages=[],
            **kwargs):
  result = callGAPI(service, function,
                    **kwargs)
  return checkCloudPrintResult(result, throw_messages=throw_messages)

API_VER_MAPPING = {
  GAPI_ADMIN_SETTINGS_API: u'v2',
  GAPI_APPSACTIVITY_API: u'v1',
  GAPI_CALENDAR_API: u'v3',
  GAPI_CLASSROOM_API: u'v1',
  GAPI_CLOUDPRINT_API: u'v2',
  GDATA_CONTACTS_API: u'v3',
  GAPI_DATATRANSFER_API: u'datatransfer_v1',
  GAPI_DIRECTORY_API: u'directory_v1',
  GAPI_DRIVE_API: DRIVE_API_VERSION,
  GDATA_EMAIL_AUDIT_API: u'v1',
  GDATA_EMAIL_SETTINGS_API: u'v2',
  GAPI_GMAIL_API: u'v1',
  GAPI_GPLUS_API: u'v1',
  GAPI_GROUPSSETTINGS_API: u'v1',
  GAPI_LICENSING_API: u'v1',
  GAPI_REPORTS_API: u'reports_v1',
  GDATA_SITES_API: u'v1',
  GAPI_SITEVERIFICATION_API: u'v1',
  }

def getAPIVersion(api):
  version = API_VER_MAPPING.get(api, u'v1')
  if api in [GAPI_DIRECTORY_API, GAPI_REPORTS_API, GAPI_DATATRANSFER_API]:
    api = u'admin'
  return (api, version, u'{0}-{1}'.format(api, version))

def readDiscoveryFile(api_version):
  disc_filename = u'%s.json' % (api_version)
  disc_file = os.path.join(GM_Globals[GM_GAM_PATH], disc_filename)
  if hasattr(sys, u'_MEIPASS'):
    pyinstaller_disc_file = os.path.join(sys._MEIPASS, disc_filename)
  else:
    pyinstaller_disc_file = None
  if os.path.isfile(disc_file):
    json_string = readFile(disc_file)
  elif pyinstaller_disc_file:
    json_string = readFile(pyinstaller_disc_file)
  else:
    systemErrorExit(NO_DISCOVERY_INFORMATION_RC, MESSAGE_NO_DISCOVERY_INFORMATION.format(disc_file))
  try:
    discovery = json.loads(json_string)
    return (disc_file, discovery)
  except ValueError:
    invalidJSONExit(disc_file)

def getAPIversionHttpService(api):
  api, version, api_version = getAPIVersion(api)
  http = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL],
                       cache=GM_Globals[GM_CACHE_DIR])
  try:
    service = googleapiclient.discovery.build(api, version, http=http, cache_discovery=False)
    if GM_Globals[GM_CACHE_DISCOVERY_ONLY]:
      http.cache = None
    return (api_version, http, service)
  except httplib2.ServerNotFoundError as e:
    systemErrorExit(NETWORK_ERROR_RC, e)
  except googleapiclient.errors.UnknownApiNameOrVersion:
    pass
  disc_file, discovery = readDiscoveryFile(api_version)
  try:
    service = googleapiclient.discovery.build_from_document(discovery, http=http)
    if GM_Globals[GM_CACHE_DISCOVERY_ONLY]:
      http.cache = None
    return (api_version, http, service)
  except (ValueError, KeyError):
    invalidJSONExit(disc_file)

def buildGAPIObject(api):
  GM_Globals[GM_CURRENT_API_USER] = None
  _, http, service = getAPIversionHttpService(api)
  credentials = getClientCredentials(OAUTH2_GAPI_SCOPES)
  GM_Globals[GM_CURRENT_API_SCOPES] = list(set(service._rootDesc[u'auth'][u'oauth2'][u'scopes'].keys()).intersection(credentials.scopes))
  if not GM_Globals[GM_CURRENT_API_SCOPES]:
    systemErrorExit(NO_SCOPES_FOR_API_RC, MESSAGE_NO_SCOPES_FOR_API.format(service._rootDesc[u'title']))
  try:
    service._http = credentials.authorize(http)
  except httplib2.ServerNotFoundError as e:
    systemErrorExit(NETWORK_ERROR_RC, e)
  except oauth2client.client.AccessTokenRefreshError as e:
    return handleOAuthTokenError(e, False)
  if not GC_Values[GC_DOMAIN]:
    GC_Values[GC_DOMAIN] = credentials.id_token.get(u'hd', u'UNKNOWN').lower()
  if not GC_Values[GC_CUSTOMER_ID]:
    GC_Values[GC_CUSTOMER_ID] = MY_CUSTOMER
  GM_Globals[GM_ADMIN] = credentials.id_token.get(u'email', u'UNKNOWN').lower()
  GM_Globals[GM_OAUTH2_CLIENT_ID] = credentials.client_id
  return service

API_SCOPE_MAPPING = {
  GAPI_APPSACTIVITY_API: [u'https://www.googleapis.com/auth/activity',
                          u'https://www.googleapis.com/auth/drive'],
  GAPI_CALENDAR_API: [u'https://www.googleapis.com/auth/calendar',],
  GAPI_DRIVE_API: [u'https://www.googleapis.com/auth/drive',],
  GAPI_GMAIL_API: [u'https://mail.google.com/',
                   u'https://www.googleapis.com/auth/gmail.settings.basic',
                   u'https://www.googleapis.com/auth/gmail.settings.sharing',],
  GAPI_GPLUS_API: [u'https://www.googleapis.com/auth/plus.me',
                   u'https://www.googleapis.com/auth/plus.login',
                   u'https://www.googleapis.com/auth/userinfo.email',
                   u'https://www.googleapis.com/auth/userinfo.profile'],
  }

def buildGAPIServiceObject(api, act_as):
  _, http, service = getAPIversionHttpService(api)
  GM_Globals[GM_CURRENT_API_USER] = act_as
  GM_Globals[GM_CURRENT_API_SCOPES] = API_SCOPE_MAPPING[api]
  credentials = getSvcAcctCredentials(GM_Globals[GM_CURRENT_API_SCOPES], act_as)
  try:
    service._http = credentials.authorize(http)
  except httplib2.ServerNotFoundError as e:
    systemErrorExit(NETWORK_ERROR_RC, e)
  except oauth2client.client.AccessTokenRefreshError as e:
    return handleOAuthTokenError(e, True)
  return service

def buildActivityGAPIObject(user):
  userEmail = convertUserUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject(GAPI_APPSACTIVITY_API, userEmail))

def buildCalendarGAPIObject(calname):
  calendarId = convertUserUIDtoEmailAddress(calname)
  return (calendarId, buildGAPIServiceObject(GAPI_CALENDAR_API, calendarId))

def buildDriveGAPIObject(user):
  userEmail = convertUserUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject(GAPI_DRIVE_API, userEmail))

def buildGmailGAPIObject(user):
  userEmail = convertUserUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject(GAPI_GMAIL_API, userEmail))

def buildGplusGAPIObject(user):
  userEmail = convertUserUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject(GAPI_GPLUS_API, userEmail))

def initGDataObject(gdataObj, api):
  _, _, api_version = getAPIVersion(api)
  disc_file, discovery = readDiscoveryFile(api_version)
  GM_Globals[GM_CURRENT_API_USER] = None
  credentials = getClientCredentials(OAUTH2_GDATA_SCOPES)
  try:
    GM_Globals[GM_CURRENT_API_SCOPES] = list(set(discovery[u'auth'][u'oauth2'][u'scopes'].keys()).intersection(credentials.scopes))
  except KeyError:
    invalidJSONExit(disc_file)
  if not GM_Globals[GM_CURRENT_API_SCOPES]:
    systemErrorExit(NO_SCOPES_FOR_API_RC, MESSAGE_NO_SCOPES_FOR_API.format(discovery.get(u'title', api_version)))
  getGDataOAuthToken(gdataObj, credentials)
  if GC_Values[GC_DEBUG_LEVEL] > 0:
    gdataObj.debug = True
  return gdataObj

def getGDataUserCredentials(api, user, i=0, count=0):
  userEmail = convertUserUIDtoEmailAddress(user)
  _, _, api_version = getAPIVersion(api)
  disc_file, discovery = readDiscoveryFile(api_version)
  GM_Globals[GM_CURRENT_API_USER] = userEmail
  credentials = getClientCredentials(OAUTH2_GDATA_SCOPES)
  try:
    GM_Globals[GM_CURRENT_API_SCOPES] = list(set(discovery[u'auth'][u'oauth2'][u'scopes'].keys()).intersection(credentials.scopes))
  except KeyError:
    invalidJSONExit(disc_file)
  if not GM_Globals[GM_CURRENT_API_SCOPES]:
    systemErrorExit(NO_SCOPES_FOR_API_RC, MESSAGE_NO_SCOPES_FOR_API.format(discovery.get(u'title', api_version)))
  credentials = getSvcAcctCredentials(GM_Globals[GM_CURRENT_API_SCOPES], userEmail)
  try:
    credentials.refresh(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL]))
    return (userEmail, credentials)
  except httplib2.ServerNotFoundError as e:
    systemErrorExit(NETWORK_ERROR_RC, e)
  except oauth2client.client.AccessTokenRefreshError as e:
    handleOAuthTokenError(e, True)
    entityUnknownWarning(EN_USER, userEmail, i, count)
    return (userEmail, None)

def getAdminSettingsObject():
  import gdata.apps.adminsettings.service
  return initGDataObject(gdata.apps.adminsettings.service.AdminSettingsService(), GDATA_ADMIN_SETTINGS_API)

def getAuditObject():
  import gdata.apps.audit.service
  return initGDataObject(gdata.apps.audit.service.AuditService(), GDATA_EMAIL_AUDIT_API)

def getContactsObject(entityType=EN_DOMAIN, entityName=None, i=0, count=0):
  import gdata.apps.contacts.service
  if entityType == EN_DOMAIN:
    contactsObject = initGDataObject(gdata.apps.contacts.service.ContactsService(),
                                     GDATA_CONTACTS_API)
    return (entityName or GC_Values[GC_DOMAIN], contactsObject)
  userEmail, credentials = getGDataUserCredentials(GDATA_CONTACTS_API, entityName, i=i, count=count)
  if not credentials:
    return (userEmail, None)
  contactsObject = gdata.apps.contacts.service.ContactsService(source=GAM_INFO,
                                                               additional_headers={u'Authorization': u'Bearer {0}'.format(credentials.access_token)})
  if GC_Values[GC_DEBUG_LEVEL] > 0:
    contactsObject.debug = True
  return (userEmail, contactsObject)

def getContactsQuery(**kwargs):
  import gdata.apps.contacts.service
  return gdata.apps.contacts.service.ContactsQuery(**kwargs)

def getEmailSettingsObject():
  import gdata.apps.emailsettings.service
  return initGDataObject(gdata.apps.emailsettings.service.EmailSettingsService(), GDATA_EMAIL_SETTINGS_API)

def getSitesObject(entityType=EN_DOMAIN, entityName=None, i=0, count=0):
  import gdata.apps.sites.service
  if entityType == EN_DOMAIN:
    sitesObject = initGDataObject(gdata.apps.sites.service.SitesService(), GDATA_SITES_API)
    return (entityName or GC_Values[GC_DOMAIN], sitesObject)
  userEmail, credentials = getGDataUserCredentials(GDATA_SITES_API, entityName, i=i, count=count)
  if not credentials:
    return (userEmail, None)
  sitesObject = gdata.apps.sites.service.SitesService(source=GAM_INFO,
                                                      additional_headers={u'Authorization': u'Bearer {0}'.format(credentials.access_token)})
  if GC_Values[GC_DEBUG_LEVEL] > 0:
    sitesObject.debug = True
  return (userEmail, sitesObject)

def getSitesQuery(**kwargs):
  import gdata.apps.sites.service
  return gdata.apps.sites.service.SitesQuery(**kwargs)

def geturl(url, dst):
  import urllib2
  u = urllib2.urlopen(url)
  f = openFile(dst, u'wb')
  meta = u.info()
  try:
    file_size = int(meta.getheaders(u'Content-Length')[0])
  except IndexError:
    file_size = -1
  file_size_dl = 0
  block_sz = 8192
  while True:
    filebuff = u.read(block_sz)
    if not filebuff:
      break
    file_size_dl += len(filebuff)
    f.write(filebuff)
    if file_size != -1:
      status = u'{0:010d}  [{1:.2%}]'.format(file_size_dl, file_size_dl*1.0/file_size)
    else:
      status = u'{0:010d} [unknown size]'.format(file_size_dl)
    status = status + chr(8)*(len(status)+1)
    sys.stdout.write(status)
  closeFile(f)

# Convert User UID to email address
def convertUserUIDtoEmailAddress(emailAddressOrUID):
  normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID)
  if normalizedEmailAddressOrUID.find(u'@') > 0:
    return normalizedEmailAddressOrUID
  try:
    cd = buildGAPIObject(GAPI_DIRECTORY_API)
    result = callGAPI(cd.users(), u'get',
                      throw_reasons=GAPI_USER_GET_THROW_REASONS,
                      userKey=normalizedEmailAddressOrUID, fields=u'primaryEmail')
    if u'primaryEmail' in result:
      return result[u'primaryEmail'].lower()
  except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden, GAPI_badRequest, GAPI_backendError, GAPI_systemError):
    pass
  return normalizedEmailAddressOrUID

# Convert Group UID to email address
def convertGroupUIDtoEmailAddress(emailAddressOrUID):
  normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID)
  if normalizedEmailAddressOrUID.find(u'@') > 0:
    return normalizedEmailAddressOrUID
  try:
    cd = buildGAPIObject(GAPI_DIRECTORY_API)
    result = callGAPI(cd.groups(), u'get',
                      throw_reasons=[GAPI_GROUP_NOT_FOUND],
                      groupKey=normalizedEmailAddressOrUID, fields=u'email')
    if u'email' in result:
      return result[u'email'].lower()
  except GAPI_groupNotFound:
    pass
  return normalizedEmailAddressOrUID

# Validate User UID/Convert email address to User UID; called immediately after getting email address from command line
def convertEmailToUserID(user):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  try:
    return callGAPI(cd.users(), u'get',
                    throw_reasons=GAPI_USER_GET_THROW_REASONS,
                    userKey=user, fields=u'id')[u'id']
  except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden, GAPI_badRequest, GAPI_backendError, GAPI_systemError):
    putArgumentBack()
    usageErrorExit(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(EN_USER), user,
                                       getPhraseDNEorSNA(user)],
                                      u'\n'))

# Convert User UID from API call to email address
def convertUserIDtoEmail(uid):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  try:
    return callGAPI(cd.users(), u'get',
                    throw_reasons=GAPI_USER_GET_THROW_REASONS,
                    userKey=uid, fields=u'primaryEmail')[u'primaryEmail']
  except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden, GAPI_badRequest, GAPI_backendError, GAPI_systemError):
    return u'uid:{0}'.format(uid)

# Convert UID to split email address
# Return (foo@bar.com, foo, bar.com)
def splitEmailAddressOrUID(emailAddressOrUID):
  normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID)
  atLoc = normalizedEmailAddressOrUID.find(u'@')
  if atLoc > 0:
    return (normalizedEmailAddressOrUID, normalizedEmailAddressOrUID[:atLoc], normalizedEmailAddressOrUID[atLoc+1:])
  try:
    cd = buildGAPIObject(GAPI_DIRECTORY_API)
    result = callGAPI(cd.users(), u'get',
                      throw_reasons=GAPI_USER_GET_THROW_REASONS,
                      userKey=normalizedEmailAddressOrUID, fields=u'primaryEmail')
    if u'primaryEmail' in result:
      normalizedEmailAddressOrUID = result[u'primaryEmail'].lower()
      atLoc = normalizedEmailAddressOrUID.find(u'@')
      return (normalizedEmailAddressOrUID, normalizedEmailAddressOrUID[:atLoc], normalizedEmailAddressOrUID[atLoc+1:])
  except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden, GAPI_badRequest, GAPI_backendError, GAPI_systemError):
    pass
  return (normalizedEmailAddressOrUID, normalizedEmailAddressOrUID, GC_Values[GC_DOMAIN])

# Add domain to foo or convert uid:xxx to foo
# Return foo@bar.com
def addDomainToEmailAddressOrUID(emailAddressOrUID, addDomain):
  cg = UID_PATTERN.match(emailAddressOrUID)
  if cg:
    try:
      cd = buildGAPIObject(GAPI_DIRECTORY_API)
      result = callGAPI(cd.users(), u'get',
                        throw_reasons=GAPI_USER_GET_THROW_REASONS,
                        userKey=cg.group(1), fields=u'primaryEmail')
      if u'primaryEmail' in result:
        return result[u'primaryEmail'].lower()
    except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden, GAPI_badRequest, GAPI_backendError, GAPI_systemError):
      pass
    return None
  atLoc = emailAddressOrUID.find(u'@')
  if atLoc == -1:
    return u'{0}@{1}'.format(emailAddressOrUID, addDomain)
  if atLoc == len(emailAddressOrUID)-1:
    return u'{0}{1}'.format(emailAddressOrUID, addDomain)
  return emailAddressOrUID

def shlexSplitList(entity, dataDelimiter=' ,'):
  import shlex
  lexer = shlex.shlex(entity, posix=True)
  lexer.whitespace = dataDelimiter
  lexer.whitespace_split = True
  return list(lexer)

def convertEntityToList(entity, shlexSplit=False, nonListEntityType=False):
  if not entity:
    return []
  if isinstance(entity, list):
    return entity
  if isinstance(entity, set):
    return list(entity)
  if isinstance(entity, dict):
    return entity.keys()
  if nonListEntityType:
    return [entity,]
  if not shlexSplit:
    return entity.replace(u',', u' ').split()
  return shlexSplitList(entity)

# Add entries in members to usersList if conditions are met
def addMembersToUsers(usersList, usersSet, emailField, members, checkNotSuspended=False, checkOrgUnit=None):
  for member in members:
    email = member.get(emailField, None)
    if email:
      if checkNotSuspended and member[u'suspended']:
        continue
      if checkOrgUnit and (checkOrgUnit != member[u'orgUnitPath'].lower()):
        continue
      if email not in usersSet:
        usersSet.add(email)
        usersList.append(email)

# Turn the entity into a list of Users/CrOS devices
def getUsersToModify(entityType, entity, memberRole=None, checkNotSuspended=False):
  def _showInvalidEntity(entityType, entityName):
    printErrorMessage(USAGE_ERROR_RC, formatKeyValueList(u'', [singularEntityName(entityType), entityName, PHRASE_INVALID], u''))

  doNotExist = invalid = 0
  usersList = []
  usersSet = set()
  if entityType in [CL_ENTITY_USER, CL_ENTITY_USERS]:
    buildGAPIObject(GAPI_DIRECTORY_API)
    members = convertEntityToList(entity, nonListEntityType=entityType == CL_ENTITY_USER)
    for user in members:
      if validateEmailAddressOrUID(user):
        if user not in usersSet:
          usersSet.add(user)
          usersList.append(user)
      else:
        _showInvalidEntity(EN_USER, user)
        invalid += 1
  elif entityType == CL_ENTITY_ALL_USERS:
    cd = buildGAPIObject(GAPI_DIRECTORY_API)
    try:
      printGettingAccountEntitiesInfo(EN_USER)
      page_message = getPageMessage(noNL=True)
      members = callGAPIpages(cd.users(), u'list', u'users',
                              page_message=page_message,
                              throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                              customer=GC_Values[GC_CUSTOMER_ID],
                              fields=u'nextPageToken,users(primaryEmail,suspended)',
                              maxResults=GC_Values[GC_USER_MAX_RESULTS])
      addMembersToUsers(usersList, usersSet, u'primaryEmail', members, checkNotSuspended=True)
      printGettingAccountEntitiesDoneInfo(len(usersSet))
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      accessErrorExit(cd)
  elif entityType in [CL_ENTITY_GROUP, CL_ENTITY_GROUPS]:
    cd = buildGAPIObject(GAPI_DIRECTORY_API)
    groups = convertEntityToList(entity, nonListEntityType=entityType == CL_ENTITY_GROUP)
    for group in groups:
      if validateEmailAddressOrUID(group):
        try:
          group = normalizeEmailAddressOrUID(group)
          printGettingAllEntityItemsForWhom(memberRole if memberRole else ROLE_MEMBER, group, entityType=EN_GROUP)
          page_message = getPageMessageForWhom(noNL=True)
          members = callGAPIpages(cd.members(), u'list', u'members',
                                  page_message=page_message,
                                  throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_INVALID, GAPI_FORBIDDEN],
                                  groupKey=group, roles=memberRole, fields=u'nextPageToken,members(email)')
          addMembersToUsers(usersList, usersSet, u'email', members)
        except (GAPI_groupNotFound, GAPI_invalid, GAPI_forbidden):
          entityUnknownWarning(EN_GROUP, group)
          doNotExist += 1
      else:
        _showInvalidEntity(EN_GROUP, group)
        invalid += 1
  elif entityType in [CL_ENTITY_OU, CL_ENTITY_OUS, CL_ENTITY_OU_AND_CHILDREN, CL_ENTITY_OUS_AND_CHILDREN]:
    cd = buildGAPIObject(GAPI_DIRECTORY_API)
    ous = convertEntityToList(entity, shlexSplit=True, nonListEntityType=entityType in [CL_ENTITY_OU, CL_ENTITY_OU_AND_CHILDREN])
    directlyInOU = entityType in [CL_ENTITY_OU, CL_ENTITY_OUS]
    qualifier = [u'', PHRASE_DIRECTLY_IN_THE.format(singularEntityName(EN_ORGANIZATIONAL_UNIT))][directlyInOU]
    prevLen = 0
    for ou in ous:
      try:
        ou = makeOrgUnitPathAbsolute(ou)
        if ou.startswith(u'id:'):
          result = callGAPI(cd.orgunits(), u'get',
                            throw_reasons=[GAPI_BAD_REQUEST, GAPI_INVALID_ORGUNIT, GAPI_ORGUNIT_NOT_FOUND, GAPI_BACKEND_ERROR, GAPI_INVALID_CUSTOMER_ID, GAPI_LOGIN_REQUIRED],
                            customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=ou)
          ou = result[u'orgUnitPath']
        checkOrgUnit = [u'', ou.lower()][directlyInOU]
        printGettingAllEntityItemsForWhom(EN_USER, ou, entityType=EN_ORGANIZATIONAL_UNIT)
        page_message = getPageMessageForWhom(noNL=True)
        members = callGAPIpages(cd.users(), u'list', u'users',
                                page_message=page_message,
                                throw_reasons=[GAPI_INVALID_ORGUNIT, GAPI_ORGUNIT_NOT_FOUND, GAPI_BACKEND_ERROR, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                                customer=GC_Values[GC_CUSTOMER_ID], query=orgUnitPathQuery(ou),
                                fields=u'nextPageToken,users(primaryEmail,suspended,orgUnitPath)',
                                maxResults=GC_Values[GC_USER_MAX_RESULTS])
        addMembersToUsers(usersList, usersSet, u'primaryEmail', members, checkOrgUnit=checkOrgUnit, checkNotSuspended=checkNotSuspended)
        totalLen = len(usersSet)
        printGettingEntityItemsDoneInfo(totalLen-prevLen, qualifier=qualifier)
        prevLen = totalLen
      except (GAPI_badRequest, GAPI_invalidOrgunit, GAPI_orgunitNotFound, GAPI_backendError, GAPI_invalidCustomerId, GAPI_loginRequired, GAPI_resourceNotFound, GAPI_forbidden):
        checkEntityDNEorAccessErrorExit(cd, EN_ORGANIZATIONAL_UNIT, ou, 0, 0)
        doNotExist += 1
  elif entityType == CL_ENTITY_QUERY:
    cd = buildGAPIObject(GAPI_DIRECTORY_API)
    try:
      printGettingAccountEntitiesInfo(EN_USER, queryQualifier(entity))
      page_message = getPageMessage(noNL=True)
      members = callGAPIpages(cd.users(), u'list', u'users',
                              page_message=page_message,
                              throw_reasons=[GAPI_INVALID_INPUT, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                              customer=GC_Values[GC_CUSTOMER_ID], query=entity,
                              fields=u'nextPageToken,users(primaryEmail,suspended)',
                              maxResults=GC_Values[GC_USER_MAX_RESULTS])
      addMembersToUsers(usersList, usersSet, u'primaryEmail', members, checkNotSuspended=checkNotSuspended)
      printGettingAccountEntitiesDoneInfo(len(usersSet), u' {0}'.format(PHRASE_THAT_MATCHED_QUERY))
    except GAPI_invalidInput:
      putArgumentBack()
      usageErrorExit(PHRASE_INVALID_QUERY)
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      accessErrorExit(cd)
  elif entityType == CL_ENTITY_LICENSES:
    licenses = doPrintLicenses(return_list=True, skus=entity.replace(u',', u' ').split())
    addMembersToUsers(usersList, usersSet, u'userId', licenses)
  elif entityType in [CL_ENTITY_COURSEPARTICIPANTS, CL_ENTITY_TEACHERS, CL_ENTITY_STUDENTS]:
    croom = buildGAPIObject(GAPI_CLASSROOM_API)
    courses = convertEntityToList(entity)
    for course in courses:
      courseId = addCourseIdScope(course)
      try:
        if entityType in [CL_ENTITY_COURSEPARTICIPANTS, CL_ENTITY_TEACHERS]:
          printGettingAllEntityItemsForWhom(EN_TEACHER, removeCourseIdScope(courseId), entityType=EN_COURSE)
          page_message = getPageMessageForWhom(noNL=True)
          teachers = callGAPIpages(croom.courses().teachers(), u'list', u'teachers',
                                   page_message=page_message,
                                   throw_reasons=[GAPI_NOT_FOUND, GAPI_FORBIDDEN, GAPI_BAD_REQUEST],
                                   courseId=courseId)
          for teacher in teachers:
            email = teacher[u'profile'].get(u'emailAddress', None)
            if email and (email not in usersSet):
              usersSet.add(email)
              usersList.append(email)
        if entityType in [CL_ENTITY_COURSEPARTICIPANTS, CL_ENTITY_STUDENTS]:
          printGettingAllEntityItemsForWhom(EN_STUDENT, removeCourseIdScope(courseId), entityType=EN_COURSE)
          page_message = getPageMessageForWhom(noNL=True)
          students = callGAPIpages(croom.courses().students(), u'list', u'students',
                                   page_message=page_message,
                                   throw_reasons=[GAPI_NOT_FOUND, GAPI_FORBIDDEN, GAPI_BAD_REQUEST],
                                   courseId=courseId)
          for student in students:
            email = student[u'profile'].get(u'emailAddress', None)
            if email and (email not in usersSet):
              usersSet.add(email)
              usersList.append(email)
      except GAPI_notFound:
        entityDoesNotExistWarning(EN_COURSE, removeCourseIdScope(courseId))
        doNotExist += 1
      except (GAPI_forbidden, GAPI_badRequest):
        APIAccessDeniedExit()
  elif entityType == CL_ENTITY_CROS:
    buildGAPIObject(GAPI_DIRECTORY_API)
    members = convertEntityToList(entity)
    for user in members:
      if user not in usersSet:
        usersSet.add(user)
        usersList.append(user)
  elif entityType == CL_ENTITY_ALL_CROS:
    cd = buildGAPIObject(GAPI_DIRECTORY_API)
    try:
      printGettingAccountEntitiesInfo(EN_CROS_DEVICE)
      page_message = getPageMessage(noNL=True)
      members = callGAPIpages(cd.chromeosdevices(), u'list', u'chromeosdevices',
                              page_message=page_message,
                              throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                              customerId=GC_Values[GC_CUSTOMER_ID],
                              fields=u'nextPageToken,chromeosdevices(deviceId)',
                              maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
      addMembersToUsers(usersList, usersSet, u'deviceId', members)
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      accessErrorExit(cd)
  elif entityType == CL_ENTITY_CROS_QUERY:
    cd = buildGAPIObject(GAPI_DIRECTORY_API)
    try:
      printGettingAccountEntitiesInfo(EN_CROS_DEVICE, queryQualifier(entity))
      page_message = getPageMessage(noNL=True)
      members = callGAPIpages(cd.chromeosdevices(), u'list', u'chromeosdevices',
                              page_message=page_message,
                              throw_reasons=[GAPI_INVALID_INPUT, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                              customerId=GC_Values[GC_CUSTOMER_ID], query=entity,
                              fields=u'nextPageToken,chromeosdevices(deviceId)',
                              maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
      addMembersToUsers(usersList, usersSet, u'deviceId', members)
      printGettingAccountEntitiesDoneInfo(len(usersSet), u' {0}'.format(PHRASE_THAT_MATCHED_QUERY))
    except GAPI_invalidInput:
      putArgumentBack()
      usageErrorExit(PHRASE_INVALID_QUERY)
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      accessErrorExit(cd)
  elif entityType in [CL_ENTITY_CROS_OU, CL_ENTITY_CROS_OU_AND_CHILDREN, CL_ENTITY_CROS_OUS, CL_ENTITY_CROS_OUS_AND_CHILDREN]:
    cd = buildGAPIObject(GAPI_DIRECTORY_API)
    ous = convertEntityToList(entity, shlexSplit=True, nonListEntityType=entityType in [CL_ENTITY_CROS_OU, CL_ENTITY_CROS_OU_AND_CHILDREN])
    directlyInOU = entityType in [CL_ENTITY_CROS_OU, CL_ENTITY_CROS_OUS]
    qualifier = [u'', PHRASE_DIRECTLY_IN_THE.format(chooseEntityName(EN_ORGANIZATIONAL_UNIT, len(ous)))][directlyInOU]
    ouDict = {}
    for ou in ous:
      try:
        ou = makeOrgUnitPathAbsolute(ou)
        if ou.startswith(u'id:'):
          result = callGAPI(cd.orgunits(), u'get',
                            throw_reasons=[GAPI_BAD_REQUEST, GAPI_INVALID_ORGUNIT, GAPI_ORGUNIT_NOT_FOUND, GAPI_BACKEND_ERROR, GAPI_INVALID_CUSTOMER_ID, GAPI_LOGIN_REQUIRED],
                            customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=ou)
          ou = result[u'orgUnitPath']
        ouDict[ou.lower()] = True
      except (GAPI_badRequest, GAPI_invalidOrgunit, GAPI_orgunitNotFound, GAPI_backendError, GAPI_invalidCustomerId, GAPI_loginRequired, GAPI_resourceNotFound, GAPI_forbidden):
        checkEntityDNEorAccessErrorExit(cd, EN_ORGANIZATIONAL_UNIT, ou, 0, 0)
        doNotExist += 1
    try:
      printGettingAccountEntitiesInfo(EN_CROS_DEVICE)
      page_message = getPageMessage(noNL=True)
      members = callGAPIpages(cd.chromeosdevices(), u'list', u'chromeosdevices',
                              page_message=page_message,
                              throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                              customerId=GC_Values[GC_CUSTOMER_ID],
                              fields=u'nextPageToken,chromeosdevices(deviceId,orgUnitPath)',
                              maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
      if directlyInOU:
        for cros in members:
          if cros[u'orgUnitPath'].lower() in ouDict:
            usersSet.add(cros[u'deviceId'])
            usersList.append(cros[u'deviceId'])
      else:
        for cros in members:
          crosOu = cros[u'orgUnitPath'].lower()
          for ou in ouDict:
            if crosOu.startswith(ou):
              usersSet.add(cros[u'deviceId'])
              usersList.append(cros[u'deviceId'])
              break
      printGettingEntityItemsDoneInfo(len(usersSet), qualifier=qualifier)
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      accessErrorExit(cd)
  else:
    systemErrorExit(UNKNOWN_ERROR_RC, u'getUsersToModify coding error')
  if doNotExist == 0 and invalid == 0:
    return usersList
  if doNotExist > 0:
    badEntitiesExit(EN_ENTITY, doNotExist, [PHRASE_DO_NOT_EXIST, PHRASE_DOES_NOT_EXIST], backupArg=True)
  if invalid > 0:
    badEntitiesExit(EN_ENTITY, invalid, [PHRASE_INVALID, PHRASE_INVALID], backupArg=True)

def getEntitiesFromArgs():
  marker = getString(OB_STRING)
  entitySet = set()
  entityList = []
  while CL_argvI < CL_argvLen:
    item = getString(singularEntityName(EN_ENTITY))
    if item == marker:
      break
    if item not in entitySet:
      entitySet.add(item)
      entityList.append(item)
  return entityList

def splitEntityList(entity, dataDelimiter, shlexSplit):
  if not entity:
    return []
  if not dataDelimiter:
    return [entity,]
  if not shlexSplit:
    return entity.split(dataDelimiter)
  return shlexSplitList(entity, dataDelimiter)

# <FileName> [charset <String>] [delimiter <String>]
def getEntitiesFromFile(shlexSplit):
  filename = getString(OB_FILE_NAME)
  encoding = getCharSet()
  dataDelimiter = getDelimiter()
  entitySet = set()
  entityList = []
  f = openFile(filename)
  uf = UTF8Recoder(f, encoding) if encoding != u'utf-8' else f
  for row in uf:
    for item in splitEntityList(row.strip(), dataDelimiter, shlexSplit):
      item = item.strip()
      if item and (item not in entitySet):
        entitySet.add(item)
        entityList.append(item)
  closeFile(f)
  return entityList

# <FileName>(:<FieldName>)+ [charset <String>] [fields <FieldNameList>] (matchfield <FieldName> <RegularExpression>)* [delimiter <String>]
def getEntitiesFromCSVFile(shlexSplit):
  try:
    fileFieldNameList = getString(OB_FILE_NAME_FIELD_NAME).split(u':')
  except ValueError:
    fileFieldNameList = []
  if len(fileFieldNameList) < 2:
    putArgumentBack()
    invalidArgumentExit(OB_FILE_NAME_FIELD_NAME)
  f, csvFile = openCSVFileReader(fileFieldNameList[0])
  for fieldName in fileFieldNameList[1:]:
    if fieldName not in csvFile.fieldnames:
      csvFieldErrorExit(fieldName, csvFile.fieldnames, backupArg=True, checkForCharset=True)
  matchFields = getMatchFields(csvFile.fieldnames)
  dataDelimiter = getDelimiter()
  entitySet = set()
  entityList = []
  for row in csvFile:
    if not matchFields or checkMatchFields(row, matchFields):
      for fieldName in fileFieldNameList[1:]:
        for item in splitEntityList(row[fieldName].strip(), dataDelimiter, shlexSplit):
          item = item.strip()
          if item and (item not in entitySet):
            entitySet.add(item)
            entityList.append(item)
  closeFile(f)
  return entityList

# <FileName> [charset <String>] [fields <FieldNameList>] keyfield <FieldName> [keypattern <RegularExpression>] [keyvalue <String>] [delimiter <String>] (matchfield <FieldName> <RegularExpression>)* [datafield <FieldName>(:<FieldName>)* [delimiter <String>]]
def getEntitiesFromCSVbyField():
  filename = getString(OB_FILE_NAME)
  f, csvFile = openCSVFileReader(filename)
  checkArgumentPresent([u'keyfield',], required=True)
  keyField = GM_Globals[GM_CSV_KEY_FIELD] = getString(OB_FIELD_NAME)
  if keyField not in csvFile.fieldnames:
    csvFieldErrorExit(keyField, csvFile.fieldnames, backupArg=True)
  if checkArgumentPresent([u'keypattern',]):
    keyPattern = getREPattern()
  else:
    keyPattern = keyField
  if checkArgumentPresent([u'keyvalue',]):
    keyValue = getString(OB_STRING)
  else:
    keyValue = keyField
  keyDelimiter = getDelimiter()
  matchFields = getMatchFields(csvFile.fieldnames)
  if checkArgumentPresent(DATAFIELD_ARGUMENT):
    if GM_Globals[GM_CSV_DATA_DICT]:
      csvDataAlreadySavedErrorExit()
    GM_Globals[GM_CSV_DATA_FIELD] = getString(OB_FIELD_NAME, checkBlank=True)
    dataFields = GM_Globals[GM_CSV_DATA_FIELD].split(u':')
    for dataField in dataFields:
      if dataField not in csvFile.fieldnames:
        csvFieldErrorExit(dataField, csvFile.fieldnames, backupArg=True)
    dataDelimiter = getDelimiter()
  else:
    GM_Globals[GM_CSV_DATA_FIELD] = None
    dataFields = []
    dataDelimiter = None
  entitySet = set()
  entityList = []
  csvDataKeys = {}
  GM_Globals[GM_CSV_DATA_DICT] = {}
  for row in csvFile:
    item = row[keyField].strip()
    if not item:
      continue
    if matchFields and not checkMatchFields(row, matchFields):
      continue
    if isinstance(keyPattern, str):
      keyList = [re.sub(keyPattern, keyItem.strip(), keyValue) for keyItem in splitEntityList(item, keyDelimiter, False)]
    else:
      keyList = [keyPattern.sub(keyValue, keyItem.strip()) for keyItem in splitEntityList(item, keyDelimiter, False)]
    for key in keyList:
      if key and (key not in entitySet):
        entitySet.add(key)
        entityList.append(key)
        if GM_Globals[GM_CSV_DATA_FIELD]:
          csvDataKeys[key] = set()
          GM_Globals[GM_CSV_DATA_DICT][key] = []
    for dataField in dataFields:
      if dataField in row:
        dataList = splitEntityList(row[dataField].strip(), dataDelimiter, False)
        for dataValue in dataList:
          dataValue = dataValue.strip()
          if not dataValue:
            continue
          for key in keyList:
            if dataValue not in csvDataKeys[key]:
              csvDataKeys[key].add(dataValue)
              GM_Globals[GM_CSV_DATA_DICT][key].append(dataValue)
  closeFile(f)
  return entityList

# Typically used to map courseparticipants to students or teachers
def mapEntityType(entityType, typeMap):
  if (typeMap != None) and (entityType in typeMap):
    return typeMap[entityType]
  return entityType

def getEntityToModify(defaultEntityType=None, returnOnError=False, crosAllowed=False, userAllowed=True, typeMap=None, checkNotSuspended=False):
  selectorChoices = CL_ENTITY_SELECTORS[:]
  if userAllowed:
    selectorChoices += CL_CSVDATA_ENTITY_SELECTORS
  if crosAllowed:
    selectorChoices += CL_CROS_ENTITY_SELECTORS+CL_CSVCROS_ENTITY_SELECTORS
  entitySelector = getChoice(selectorChoices, defaultChoice=None)
  if entitySelector:
    choices = []
    if entitySelector == CL_ENTITY_SELECTOR_ALL:
      if userAllowed:
        choices += CL_USER_ENTITY_SELECTOR_ALL_SUBTYPES
      if crosAllowed:
        choices += CL_CROS_ENTITY_SELECTOR_ALL_SUBTYPES
      entityType = CL_ENTITY_SELECTOR_ALL_SUBTYPES_MAP[getChoice(choices)]
      return ([CL_ENTITY_CROS, CL_ENTITY_USERS][entityType == CL_ENTITY_ALL_USERS],
              getUsersToModify(entityType, None))
    if entitySelector == CL_ENTITY_SELECTOR_ARGS:
      if userAllowed:
        choices += CL_USER_ENTITY_SELECTOR_ARGS_DATAFILE_CSVKMD_SUBTYPES
      if crosAllowed:
        choices += CL_CROS_ENTITY_SELECTOR_ARGS_DATAFILE_CSVKMD_SUBTYPES
      entityType = mapEntityType(getChoice(choices, choiceAliases=CL_ENTITY_ALIAS_MAP), typeMap)
      return ([CL_ENTITY_CROS, CL_ENTITY_USERS][entityType != CL_ENTITY_CROS],
              getUsersToModify(entityType, getEntitiesFromArgs()))
    if userAllowed:
      if entitySelector == CL_ENTITY_SELECTOR_FILE:
        return (CL_ENTITY_USERS,
                getUsersToModify(CL_ENTITY_USERS, getEntitiesFromFile(False)))
      if entitySelector in [CL_ENTITY_SELECTOR_CSV, CL_ENTITY_SELECTOR_CSVFILE]:
        return (CL_ENTITY_USERS,
                getUsersToModify(CL_ENTITY_USERS, getEntitiesFromCSVFile(False)))
    if crosAllowed:
      if entitySelector == CL_ENTITY_SELECTOR_CROSFILE:
        return (CL_ENTITY_CROS,
                getUsersToModify(CL_ENTITY_CROS, getEntitiesFromFile(False)))
      if entitySelector in [CL_ENTITY_SELECTOR_CROSCSV, CL_ENTITY_SELECTOR_CROSCSVFILE]:
        return (CL_ENTITY_CROS,
                getUsersToModify(CL_ENTITY_CROS, getEntitiesFromCSVFile(False)))
    if entitySelector == CL_ENTITY_SELECTOR_DATAFILE:
      if userAllowed:
        choices += CL_USER_ENTITY_SELECTOR_ARGS_DATAFILE_CSVKMD_SUBTYPES
      if crosAllowed:
        choices += CL_CROS_ENTITY_SELECTOR_ARGS_DATAFILE_CSVKMD_SUBTYPES
      entityType = mapEntityType(getChoice(choices), typeMap)
      return ([CL_ENTITY_CROS, CL_ENTITY_USERS][entityType not in [CL_ENTITY_CROS, CL_ENTITY_CROS_OUS, CL_ENTITY_CROS_OUS_AND_CHILDREN]],
              getUsersToModify(entityType, getEntitiesFromFile(shlexSplit=entityType in [CL_ENTITY_OUS, CL_ENTITY_OUS_AND_CHILDREN, CL_ENTITY_CROS_OUS, CL_ENTITY_CROS_OUS_AND_CHILDREN])))
    if entitySelector == CL_ENTITY_SELECTOR_CSVKMD:
      if userAllowed:
        choices += CL_USER_ENTITY_SELECTOR_ARGS_DATAFILE_CSVKMD_SUBTYPES
      if crosAllowed:
        choices += CL_CROS_ENTITY_SELECTOR_ARGS_DATAFILE_CSVKMD_SUBTYPES
      entityType = mapEntityType(getChoice(choices, choiceAliases=CL_ENTITY_ALIAS_MAP), typeMap)
      return ([CL_ENTITY_CROS, CL_ENTITY_USERS][entityType != CL_ENTITY_CROS],
              getUsersToModify(entityType, getEntitiesFromCSVbyField()))
    if entitySelector in [CL_ENTITY_SELECTOR_CSVDATA, CL_ENTITY_SELECTOR_CSVCROS]:
      checkDataField()
      return ([CL_ENTITY_CROS, CL_ENTITY_USERS][entitySelector == CL_ENTITY_SELECTOR_CSVDATA],
              GM_Globals[GM_CSV_DATA_DICT])
  entityChoices = []
  if userAllowed:
    entityChoices += CL_USER_ENTITIES
  if crosAllowed:
    entityChoices += CL_CROS_ENTITIES
  entityType = mapEntityType(getChoice(entityChoices, choiceAliases=CL_ENTITY_ALIAS_MAP, defaultChoice=defaultEntityType), typeMap)
  if entityType:
    if entityType not in CL_CROS_ENTITIES:
      return (CL_ENTITY_USERS,
              getUsersToModify(entityType, getString(OB_USER_ENTITY, emptyOK=True), checkNotSuspended=checkNotSuspended))
    else:
      return (CL_ENTITY_CROS,
              getUsersToModify(entityType, getString(OB_CROS_ENTITY, emptyOK=True)))
  if returnOnError:
    return (None, None)
  invalidChoiceExit(selectorChoices+entityChoices)

def getEntitySelector():
  selectorChoices = CL_ENTITY_SELECTORS[:]
  selectorChoices.remove(CL_ENTITY_SELECTOR_ALL)
  selectorChoices.remove(CL_ENTITY_SELECTOR_DATAFILE)
  selectorChoices += CL_CSVDATA_ENTITY_SELECTORS
  return getChoice(selectorChoices, defaultChoice=None)

def getEntitySelection(entitySelector, shlexSplit):
  if entitySelector in [CL_ENTITY_SELECTOR_FILE]:
    return getEntitiesFromFile(shlexSplit)
  if entitySelector in [CL_ENTITY_SELECTOR_CSV, CL_ENTITY_SELECTOR_CSVFILE]:
    return getEntitiesFromCSVFile(shlexSplit)
  if entitySelector == CL_ENTITY_SELECTOR_CSVKMD:
    return getEntitiesFromCSVbyField()
  if entitySelector in [CL_ENTITY_SELECTOR_CSVDATA]:
    checkDataField()
    return GM_Globals[GM_CSV_DATA_DICT]
  return getEntitiesFromArgs()

def getEntityList(item, listOptional=False, shlexSplit=False):
  entitySelector = getEntitySelector()
  if entitySelector:
    return getEntitySelection(entitySelector, shlexSplit)
  return convertEntityToList(getString(item, optional=listOptional, emptyOK=True), shlexSplit=shlexSplit)

# Write a CSV file
def addTitleToCSVfile(title, titles):
  titles[u'set'].add(title)
  titles[u'list'].append(title)

def addTitlesToCSVfile(addTitles, titles):
  for title in addTitles:
    if title not in titles[u'set']:
      addTitleToCSVfile(title, titles)

def removeTitlesFromCSVfile(removeTitles, titles):
  for title in removeTitles:
    if title in titles[u'set']:
      titles[u'set'].remove(title)
      titles[u'list'].remove(title)

def addRowTitlesToCSVfile(row, csvRows, titles):
  csvRows.append(row)
  for title in row:
    if title not in titles[u'set']:
      addTitleToCSVfile(title, titles)

# fieldName is command line argument
# fieldNameMap maps fieldName to API field names; CSV file header will be API field name
#ARGUMENT_TO_PROPERTY_MAP = {
#  u'admincreated': [u'adminCreated'],
#  u'aliases': [u'aliases', u'nonEditableAliases'],
#  }
# fieldsList is the list of API fields
# fieldsTitles maps the API field name to the CSV file header
def addFieldToCSVfile(fieldName, fieldNameMap, fieldsList, fieldsTitles, titles):
  for ftList in fieldNameMap[fieldName]:
    if ftList not in fieldsTitles:
      fieldsList.append(ftList)
      fieldsTitles[ftList] = ftList
      addTitlesToCSVfile([ftList], titles)

# fieldName is command line argument
# fieldNameTitleMap maps fieldName to API field name and CSV file header
#ARGUMENT_TO_PROPERTY_TITLE_MAP = {
#  u'admincreated': [u'adminCreated', u'Admin_Created'],
#  u'aliases': [u'aliases', u'Aliases', u'nonEditableAliases', u'NonEditableAliases'],
#  }
# fieldsList is the list of API fields
# fieldsTitles maps the API field name to the CSV file header
def addFieldTitleToCSVfile(fieldName, fieldNameTitleMap, fieldsList, fieldsTitles, titles):
  ftList = fieldNameTitleMap[fieldName]
  for i in range(0, len(ftList), 2):
    if ftList[i] not in fieldsTitles:
      fieldsList.append(ftList[i])
      fieldsTitles[ftList[i]] = ftList[i+1]
      addTitlesToCSVfile([ftList[i+1]], titles)

def initializeTitlesCSVfile(baseTitles):
  titles = {u'set': set(), u'list': []}
  csvRows = []
  if baseTitles is not None:
    addTitlesToCSVfile(baseTitles, titles)
  return (titles, csvRows)

def sortCSVTitles(firstTitle, titles):
  restoreTitles = []
  for title in firstTitle:
    if title in titles[u'set']:
      titles[u'list'].remove(title)
      restoreTitles.append(title)
  titles[u'list'].sort()
  for title in restoreTitles[::-1]:
    titles[u'list'].insert(0, title)

def writeCSVfile(csvRows, titles, list_type, todrive):
  csv.register_dialect(u'nixstdout', lineterminator=u'\n')
  if todrive:
    csvFile = StringIO.StringIO()
    writer = csv.DictWriter(csvFile, fieldnames=titles[u'list'],
                            dialect=u'nixstdout', quoting=csv.QUOTE_MINIMAL)
  else:
    csvFile = openFile(GM_Globals[GM_CSVFILE], GM_Globals[GM_CSVFILE_MODE])
    writer = UnicodeDictWriter(csvFile, fieldnames=titles[u'list'],
                               dialect=u'nixstdout', quoting=csv.QUOTE_MINIMAL)
  try:
    if GM_Globals[GM_CSVFILE_WRITE_HEADER]:
      writer.writerow(dict((item, item) for item in writer.fieldnames))
      if GM_Globals[GM_CSVFILE_MODE] == u'ab':
        GM_Globals[GM_CSVFILE_WRITE_HEADER] = False
    writer.writerows(csvRows)
  except IOError as e:
    systemErrorExit(FILE_ERROR_RC, e)
  if todrive:
    columns = len(titles[u'list'])
    rows = len(csvRows)
    cell_count = rows * columns
    if cell_count > 500000 or columns > 256:
      printKeyValueList([WARNING, MESSAGE_RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET])
      convert = False
    else:
      convert = True
    drive = buildGAPIObject(GAPI_DRIVE_API)
    try:
      result = callGAPI(drive.files(), DRIVE_CREATE_FILE,
                        throw_reasons=[GAPI_INSUFFICIENT_PERMISSIONS],
                        convert=convert, body={u'description': u' '.join(CL_argv), DRIVE_FILE_NAME: u'{0} - {1}'.format(GC_Values[GC_DOMAIN], list_type), u'mimeType': u'text/csv'},
                        media_body=googleapiclient.http.MediaIoBaseUpload(csvFile, mimetype=u'text/csv', resumable=True))
      file_url = result[DRIVE_FILE_VIEW_LINK]
      if GC_Values[GC_NO_BROWSER]:
        msg_txt = u'{0}:\n{1}'.format(PHRASE_DATA_UPLOADED_TO_DRIVE_FILE, file_url)
        msg_subj = u'{0} - {1}'.format(GC_Values[GC_DOMAIN], list_type)
        send_email(msg_subj, msg_txt)
        printKeyValueList([msg_txt])
      else:
        import webbrowser
        webbrowser.open(file_url)
    except GAPI_insufficientPermissions:
      printWarningMessage(INSUFFICIENT_PERMISSIONS_RC, MESSAGE_INSUFFICIENT_PERMISSIONS_TO_PERFORM_TASK)
  if GM_Globals[GM_CSVFILE] != u'-':
    closeFile(csvFile)

# Flatten a JSON object
def flattenJSON(structure, key=u'', path=u'', flattened=None, listLimit=None):
  if flattened == None:
    flattened = {}
  if not isinstance(structure, (dict, list)):
    flattened[((path + u'.') if path else u'') + key] = structure
  elif isinstance(structure, list):
    for i, item in enumerate(structure):
      if listLimit and (i >= listLimit):
        break
      flattenJSON(item, u'{0}'.format(i), u'.'.join([item for item in [path, key] if item]), flattened=flattened, listLimit=listLimit)
  else:
    for new_key, value in structure.items():
      if new_key in [u'kind', u'etag']:
        continue
      if value == NEVER_TIME:
        value = NEVER
      flattenJSON(value, new_key, u'.'.join([item for item in [path, key] if item]), flattened=flattened, listLimit=listLimit)
  return flattened

# Show a json object
def showJSON(object_name, object_value, skip_objects=[], level=0):
  if object_name in [u'kind', u'etag', u'etags'] or object_name in skip_objects:
    return
  if object_name != None:
    printJSONKey(object_name)
  if isinstance(object_value, list):
    if len(object_value) == 1 and isinstance(object_value[0], (str, unicode, int, bool)):
      if object_name != None:
        printJSONValue(object_value[0])
      else:
        printKeyValueList([object_value[0]])
      return
    if object_name != None:
      printBlankLine()
      incrementIndentLevel()
    for sub_value in object_value:
      if isinstance(sub_value, (str, unicode, int, bool)):
        printKeyValueList([sub_value])
      else:
        showJSON(None, sub_value, skip_objects=skip_objects, level=level+1)
    if object_name != None:
      decrementIndentLevel()
  elif isinstance(object_value, dict):
    indentAfterFirst = unindentAfterLast = False
    if object_name != None:
      printBlankLine()
      incrementIndentLevel()
    elif level > 0:
      indentAfterFirst = unindentAfterLast = True
    for sub_object in sorted(object_value):
      if sub_object not in skip_objects:
        showJSON(sub_object, object_value[sub_object], skip_objects=skip_objects, level=level+1)
        if indentAfterFirst:
          incrementIndentLevel()
          indentAfterFirst = False
    if object_name != None or unindentAfterLast:
      decrementIndentLevel()
  else:
    printJSONValue(object_value)

# Batch processing request_id fields
RI_ENTITY = 0
RI_I = 1
RI_COUNT = 2
RI_J = 3
RI_JCOUNT = 4
RI_ITEM = 5
RI_ROLE = 6

def batchRequestID(entityName, i, count, j, jcount, item, role=u''):
  return u'{0}\n{1}\n{2}\n{3}\n{4}\n{5}\n{6}'.format(entityName, i, count, j, jcount, item, role)

# Send an email
def send_email(msg_subj, msg_txt, msg_rcpt=None):
  from email.mime.text import MIMEText
  gmail = buildGAPIObject(GAPI_GMAIL_API)
  sender_email = gmail._http.request.credentials.id_token[u'email']
  if not msg_rcpt:
    msg_rcpt = sender_email
  msg = MIMEText(msg_txt)
  msg[u'Subject'] = msg_subj
  msg[u'From'] = sender_email
  msg[u'To'] = msg_rcpt
  callGAPI(gmail.users().messages(), u'send',
           userId=sender_email, body={u'raw': base64.urlsafe_b64encode(msg.as_string())})

# gam version
def doVersion(checkForCheck=True):
  import struct
  printKeyValueList([u'GAM {0} - {1}\n{2}\nPython {3}.{4}.{5} {6}-bit {7}\ngoogle-api-python-client {8}\n{9} {10}\nPath: {11}'.format(__version__, GAM_URL,
                                                                                                                                      __author__,
                                                                                                                                      sys.version_info[0], sys.version_info[1], sys.version_info[2],
                                                                                                                                      struct.calcsize(u'P')*8, sys.version_info[3],
                                                                                                                                      googleapiclient.__version__,
                                                                                                                                      platform.platform(), platform.machine(),
                                                                                                                                      GM_Globals[GM_GAM_PATH])])
  if checkForCheck:
    while CL_argvI < CL_argvLen:
      myarg = getArgument()
      if myarg == u'check':
        doGAMCheckForUpdates(forceCheck=True)
      else:
        unknownArgumentExit()

# gam help
def doUsage():
  printBlankLine()
  doVersion(checkForCheck=False)
  printLine(u'''
Usage: gam [OPTIONS]...

GAM. Retrieve or set Google Apps domain,
user, group and alias settings. Exhaustive list of commands
can be found at: {0}

Examples:
gam info domain
gam create user jsmith firstname John lastname Smith password secretpass
gam update user jsmith suspended on
gam.exe update group announcements add member jsmith
...
'''.format(GAM_WIKI))

# Utilities for batch/csv
def batch_worker():
  while True:
    item = GM_Globals[GM_BATCH_QUEUE].get()
    subprocess.call(item, stderr=subprocess.STDOUT)
    GM_Globals[GM_BATCH_QUEUE].task_done()

def run_batch(items, total_items):
  import Queue, threading
  current_item = 0
  python_cmd = [sys.executable.lower(),]
  if not getattr(sys, u'frozen', False): # we're not frozen
    python_cmd.append(os.path.realpath(CL_argv[0]))
  num_worker_threads = min(total_items, GC_Values[GC_NUM_THREADS])
  GM_Globals[GM_BATCH_QUEUE] = Queue.Queue(maxsize=num_worker_threads) # GM_Globals[GM_BATCH_QUEUE].put() gets blocked when trying to create more items than there are workers
  sys.stderr.write(PHRASE_STARTING_N_WORKER_THREADS.format(num_worker_threads))
  for _ in range(num_worker_threads):
    t = threading.Thread(target=batch_worker)
    t.daemon = True
    t.start()
  for item in items:
    current_item += 1
    if not current_item % 100:
      sys.stderr.write(u'{0} {1} / {2}\n'.format(PHRASE_STARTING_THREAD, current_item, total_items))
    if item[0] == COMMIT_BATCH_CMD:
      sys.stderr.write(u'{0} - {1}\n'.format(COMMIT_BATCH_CMD, PHRASE_WAITING_FOR_PROCESSES_TO_COMPLETE))
      GM_Globals[GM_BATCH_QUEUE].join()
      sys.stderr.write(u'{0} - {1}\n'.format(COMMIT_BATCH_CMD, PHRASE_COMPLETE))
      continue
    GM_Globals[GM_BATCH_QUEUE].put(python_cmd+item)
  GM_Globals[GM_BATCH_QUEUE].join()

# gam batch <FileName>|- [charset <Charset>]
def doBatch():
  import shlex
  filename = getString(OB_FILE_NAME)
  if (filename == u'-') and (GC_Values[GC_DEBUG_LEVEL] > 0):
    putArgumentBack()
    usageErrorExit(MESSAGE_BATCH_CSV_LOOP_DASH_DEBUG_INCOMPATIBLE.format(u'batch'))
  encoding = getCharSet()
  checkForExtraneousArguments()
  items = []
  cmdCount = 0
  f = openFile(filename)
  batchFile = UTF8Recoder(f, encoding) if encoding != u'utf-8' else f
  try:
    for line in batchFile:
      argv = shlex.split(line)
      if len(argv) > 0:
        cmd = argv[0].strip().lower()
        if (not cmd) or cmd.startswith(u'#') or ((len(argv) == 1) and (cmd != COMMIT_BATCH_CMD)):
          continue
        if cmd == GAM_CMD:
          items.append([arg.encode(GM_Globals[GM_SYS_ENCODING]) for arg in argv[1:]])
          cmdCount += 1
        elif cmd == COMMIT_BATCH_CMD:
          items.append([cmd])
        else:
          sys.stderr.write(u'Command: >>>{0}<<< {1}\n'.format(makeQuotedList([argv[0]]), makeQuotedList(argv[1:])))
          stderrErrorMsg(u'{0}: {1} <{2}>'.format(ARGUMENT_ERROR_NAMES[ARGUMENT_INVALID][1],
                                                  PHRASE_EXPECTED,
                                                  formatChoiceList([GAM_CMD, COMMIT_BATCH_CMD])))
  except IOError as e:
    systemErrorExit(FILE_ERROR_RC, e)
  closeFile(f)
  run_batch(items, cmdCount)

def doAutoBatch(CL_entityType, CL_entityList, CL_command):
  items = [[CL_entityType, entity, CL_command]+CL_argv[CL_argvI:] for entity in CL_entityList]
  run_batch(items, len(items))

# Process command line arguments, find substitutions
# An argument containing instances of ~~xxx~!~pattern~!~replacement~~ has ~~...~~ replaced by re.sub(pattern, replacement, value of field xxx from the CSV file)
# For example, ~~primaryEmail~!~^(.+)@(.+)$~!~\1 AT \2~~ would replace foo@bar.com (from the primaryEmail column) with foo AT bar.com
# An argument containing instances of ~~xxx~~ has xxx replaced by the value of field xxx from the CSV file
# An argument containing exactly ~xxx is replaced by the value of field xxx from the CSV file
# Otherwise, the argument is preserved as is

SUB_PATTERN = re.compile(r'~~(.+?)~~')
RE_PATTERN = re.compile(r'~~(.+?)~!~(.+?)~!~(.+?)~~')
SUB_TYPE = u'sub'
RE_TYPE = u're'

# SubFields is a dictionary; the key is the argument number, the value is a list of tuples that mark
# the substition (type, fieldname, start, end). Type is 'sub' for simple substitution, 're' for regex substitution.
# Example: update user '~User' address type work unstructured '~~Street~~, ~~City~~, ~~State~~ ~~ZIP~~' primary
# {2: [('sub', 'User', 0, 5)], 7: [('sub', 'Street', 0, 10), ('sub', 'City', 12, 20), ('sub', 'State', 22, 31), ('sub', 'ZIP', 32, 39)]}
def getSubFields(initial_argv, fieldNames):
  global CL_argvI
  subFields = {}
  GAM_argv = initial_argv[:]
  GAM_argvI = len(GAM_argv)
  while CL_argvI < CL_argvLen:
    myarg = CL_argv[CL_argvI]
    if not myarg:
      GAM_argv.append(myarg)
    elif SUB_PATTERN.search(myarg):
      pos = 0
      subFields.setdefault(GAM_argvI, [])
      while True:
        submatch = SUB_PATTERN.search(myarg, pos)
        if not submatch:
          break
        rematch = RE_PATTERN.match(submatch.group(0))
        if not rematch:
          fieldName = submatch.group(1)
          if fieldName not in fieldNames:
            csvFieldErrorExit(fieldName, fieldNames)
          subFields[GAM_argvI].append((SUB_TYPE, fieldName, submatch.start(), submatch.end()))
        else:
          fieldName = rematch.group(1)
          if fieldName not in fieldNames:
            csvFieldErrorExit(fieldName, fieldNames)
          try:
            re.compile(rematch.group(2))
            subFields[GAM_argvI].append((RE_TYPE, fieldName, submatch.start(), submatch.end(), rematch.group(2), rematch.group(3)))
          except re.error as e:
            usageErrorExit(u'{0} {1}: {2}'.format(OB_RE_PATTERN, PHRASE_ERROR, e))
        pos = submatch.end()
      GAM_argv.append(myarg)
    elif myarg[0] == u'~':
      fieldName = myarg[1:]
      if fieldName in fieldNames:
        subFields[GAM_argvI] = [(SUB_TYPE, fieldName, 0, len(myarg))]
        GAM_argv.append(myarg)
      else:
        csvFieldErrorExit(fieldName, fieldNames)
    else:
      GAM_argv.append(myarg.encode(GM_Globals[GM_SYS_ENCODING]))
    GAM_argvI += 1
    CL_argvI += 1
  return(GAM_argv, subFields)

def processSubFields(GAM_argv, row, subFields):
  argv = GAM_argv[:]
  for GAM_argvI, fields in subFields.iteritems():
    oargv = argv[GAM_argvI][:]
    argv[GAM_argvI] = u''
    pos = 0
    for field in fields:
      argv[GAM_argvI] += oargv[pos:field[2]]
      if field[0] == SUB_TYPE:
        if row[field[1]]:
          argv[GAM_argvI] += row[field[1]]
      else:
        if row[field[1]]:
          argv[GAM_argvI] += re.sub(field[4], field[5], row[field[1]])
      pos = field[3]
    argv[GAM_argvI] += oargv[pos:]
    argv[GAM_argvI] = argv[GAM_argvI].encode(GM_Globals[GM_SYS_ENCODING])
  return argv

# gam csv <FileName>|- [charset <Charset>] [fields <FieldNameList>] (matchfield <FieldName> <RegularExpression>)* gam <GAM argument list>
def doCSV():
  filename = getString(OB_FILE_NAME)
  if (filename == u'-') and (GC_Values[GC_DEBUG_LEVEL] > 0):
    putArgumentBack()
    usageErrorExit(MESSAGE_BATCH_CSV_LOOP_DASH_DEBUG_INCOMPATIBLE.format(u'csv'))
  f, csvFile = openCSVFileReader(filename)
  matchFields = getMatchFields(csvFile.fieldnames)
  checkArgumentPresent([GAM_CMD,], required=True)
  if CL_argvI == CL_argvLen:
    missingArgumentExit(OB_GAM_ARGUMENT_LIST)
  GAM_argv, subFields = getSubFields([], csvFile.fieldnames)
  items = []
  for row in csvFile:
    if (not matchFields) or checkMatchFields(row, matchFields):
      items.append(processSubFields(GAM_argv, row, subFields))
  closeFile(f)
  run_batch(items, len(items))

# gam list [todrive] <EntityList> [data <CrOSTypeEntity>|<UserTypeEntity> [delimiter <String>]]
def doListType():
  doList(None, None)

# gam <CrOSTypeEntity> list [todrive] [data <EntityList> [delimiter <String>]]
def doListCrOS(entityList):
  doList(entityList, CL_ENTITY_CROS)

# gam <UserTypeEntity> list [todrive] [data <EntityList> [delimiter <String>]]
def doListUser(entityList):
  doList(entityList, CL_ENTITY_USERS)

def doList(entityList, entityType):
  buildGAPIObject(GAPI_DIRECTORY_API)
  todrive = checkArgumentPresent(TODRIVE_ARGUMENT)
  if not entityList:
    entityList = getEntityList(OB_ENTITY)
  if GM_Globals[GM_CSV_DATA_DICT]:
    keyField = GM_Globals[GM_CSV_KEY_FIELD]
    dataField = GM_Globals[GM_CSV_DATA_FIELD]
  else:
    keyField = u'Entity'
    dataField = u'Data'
  titles, csvRows = initializeTitlesCSVfile([keyField])
  showData = checkArgumentPresent(DATA_ARGUMENT)
  if showData:
    if not entityType:
      itemType, itemList = getEntityToModify(crosAllowed=True)
    else:
      itemType = None
      itemList = getEntityList(OB_ENTITY)
    entityItemLists = itemList if isinstance(itemList, dict) else None
    addTitleToCSVfile(dataField, titles)
  else:
    entityItemLists = None
  dataDelimiter = getDelimiter()
  checkForExtraneousArguments()
  for entity in entityList:
    entityEmail = normalizeEmailAddressOrUID(entity)
    if showData:
      if entityItemLists:
        if entity not in entityItemLists:
          csvRows.append({keyField: entityEmail})
          continue
        itemList = entityItemLists[entity]
        if itemType == CL_ENTITY_USERS:
          for i in range(len(itemList)):
            itemList[i] = normalizeEmailAddressOrUID(itemList[i])
      if dataDelimiter:
        csvRows.append({keyField: entityEmail, dataField: dataDelimiter.join(itemList)})
      else:
        for item in itemList:
          csvRows.append({keyField: entityEmail, dataField: item})
    else:
      csvRows.append({keyField: entityEmail})
  writeCSVfile(csvRows, titles, u'Entity', todrive)

class cmd_flags(object):
  def __init__(self, noLocalWebserver):
    self.short_url = True
    self.noauth_local_webserver = noLocalWebserver
    self.logging_level = u'ERROR'
    self.auth_host_name = u'localhost'
    self.auth_host_port = [8080, 9090]

OAUTH2_SCOPES = [
  u'https://apps-apis.google.com/a/feeds/domain/',                     #  0:Admin Settings API
  u'https://mail.google.com/',                                         #  1:Admin User - Email upload report document notifications
  u'https://www.googleapis.com/auth/drive.file',                       #  2:Admin User - Upload report documents to Google Drive
  u'https://www.googleapis.com/auth/calendar',                         #  3:Calendar API (RO)
  u'https://www.googleapis.com/auth/classroom.courses',                #  4:Classroom API - Courses (RO)
  u'https://www.googleapis.com/auth/classroom.guardianlinks.students', #  5:Classroom API - Student Graudians (RO)
  u'https://www.googleapis.com/auth/classroom.profile.emails',         #  6:Classroom API - Profile Emails
  u'https://www.googleapis.com/auth/classroom.profile.photos',         #  7:Classroom API - Profile Photos
  u'https://www.googleapis.com/auth/classroom.rosters',                #  8:Classroom API - Rosters (RO)
  u'https://www.googleapis.com/auth/cloudprint',                       #  9:Cloudprint API
  u'https://www.google.com/m8/feeds/contacts',                         # 10:Contacts API - Domain Shared and Users
  u'https://www.googleapis.com/auth/admin.datatransfer',               # 11:Data Transfer API (RO)
  u'https://www.googleapis.com/auth/admin.directory.device.chromeos',  # 12:Directory API - Chrome OS Devices (RO)
  u'https://www.googleapis.com/auth/admin.directory.customer',         # 13:Directory API - Customers (RO)
  u'https://www.googleapis.com/auth/admin.directory.domain',           # 14:Directory API - Domains (RO)
  u'https://www.googleapis.com/auth/admin.directory.group',            # 15:Directory API - Groups (RO)
  u'https://www.googleapis.com/auth/admin.directory.device.mobile',    # 16:Directory API - Mobile Devices Directory (RO,AO)
  u'https://www.googleapis.com/auth/admin.directory.notifications',    # 17:Directory API - Notifications
  u'https://www.googleapis.com/auth/admin.directory.orgunit',          # 18:Directory API - Organizational Units (RO)
  u'https://www.googleapis.com/auth/admin.directory.resource.calendar',# 19:Directory API - Resource Calendars (RO)
  u'https://www.googleapis.com/auth/admin.directory.rolemanagement',   # 20:Directory API - Roles (RO)
  u'https://www.googleapis.com/auth/admin.directory.userschema',       # 21:Directory API - User Schemas (RO)
  u'https://www.googleapis.com/auth/admin.directory.user.security',    # 22:Directory API - User Security
  u'https://www.googleapis.com/auth/admin.directory.user',             # 23:Directory API - Users (RO)
  u'https://apps-apis.google.com/a/feeds/compliance/audit/',           # 24:Email Audit API
  u'https://apps-apis.google.com/a/feeds/emailsettings/2.0/',          # 25:Email Settings API - Users
  u'https://www.googleapis.com/auth/apps.groups.settings',             # 26:Group Settings API
  u'https://www.googleapis.com/auth/apps.licensing',                   # 27:License Manager API
  u'https://www.googleapis.com/auth/admin.reports.audit.readonly',     # 28:Reports API - Audit Reports
  u'https://www.googleapis.com/auth/admin.reports.usage.readonly',     # 29:Reports API - Usage Reports
  u'https://www.googleapis.com/auth/siteverification',                 # 30:Site Verification API
  u'https://sites.google.com/feeds',                                   # 31:Sites API
  ]
OAUTH2_RO_SCOPES = [3, 4, 8, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 23]
OAUTH2_AO_SCOPES = [16]
OAUTH2_SCOPES_MAP = {
  OAUTH2_GAPI_SCOPES: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 26, 27, 28, 29, 30],
  OAUTH2_GDATA_SCOPES: [0, 10, 24, 25, 31]
  }
OAUTH2_MENU = u'''
Select the authorized scopes by entering a number.
Append an 'r' to grant read-only access or an 'a' to grant action-only access.

[%%s]  %2d)  Admin Settings API
[%%s]  %2d)  Admin User - Email upload report document notifications
[%%s]  %2d)  Admin User - Upload report documents to Google Drive
[%%s]  %2d)  Calendar API (supports read-only)
[%%s]  %2d)  Classroom API - Courses (supports read-only)
[%%s]  %2d)  Classroom API - Student Guardians (supports read-only)
[%%s]  %2d)  Classroom API - Profile Emails
[%%s]  %2d)  Classroom API - Profile Photos
[%%s]  %2d)  Classroom API - Rosters (supports read-only)
[%%s]  %2d)  Cloud Print API
[%%s]  %2d)  Contacts API - Domain Shared and Users
[%%s]  %2d)  Data Transfer API (supports read-only)
[%%s]  %2d)  Directory API - Chrome OS Devices (supports read-only)
[%%s]  %2d)  Directory API - Customers (supports read-only)
[%%s]  %2d)  Directory API - Domains (supports read-only)
[%%s]  %2d)  Directory API - Groups (supports read-only)
[%%s]  %2d)  Directory API - Mobile Devices (supports read-only and action-only)
[%%s]  %2d)  Directory API - Notifications
[%%s]  %2d)  Directory API - Organizational Units (supports read-only)
[%%s]  %2d)  Directory API - Resource Calendars (supports read-only)
[%%s]  %2d)  Directory API - Roles (supports read-only)
[%%s]  %2d)  Directory API - User Schemas (supports read-only)
[%%s]  %2d)  Directory API - User Security
[%%s]  %2d)  Directory API - Users (supports read-only)
[%%s]  %2d)  Email Audit API - Monitors, Activity and Mailbox Exports
[%%s]  %2d)  Email Settings API - Users
[%%s]  %2d)  Groups Settings API
[%%s]  %2d)  License Manager API
[%%s]  %2d)  Reports API - Audit Reports
[%%s]  %2d)  Reports API - Usage Reports
[%%s]  %2d)  Site Verification API
[%%s]  %2d)  Sites API

      s)  Select all scopes
      u)  Unselect all scopes
      e)  Exit without changes
      c)  Continue to authorization
'''
OAUTH2_CMDS = [u's', u'u', u'e', u'c']

def revokeCredentials():
  http = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
  for oauth2Scope in OAUTH2_SCOPES_LIST:
    credentials = getCredentialsForScope(oauth2Scope)
    if credentials and not credentials.invalid:
      credentials.revoke_uri = oauth2client.GOOGLE_REVOKE_URI
      try:
        credentials.revoke(http)
        time.sleep(2)
      except oauth2client.client.TokenRevokeError as e:
        printErrorMessage(INVALID_TOKEN_RC, e.message)

# gam oauth|oauth2 create|request
def doOAuthRequest():
  MISSING_CLIENT_SECRETS_MESSAGE = u"""Please configure OAuth 2.0

To make GAM run you will need to populate the {0} file found at:
{1}
with information from the APIs Console <https://console.developers.google.com>.

See this site for instructions:
{2}

""".format(FN_CLIENT_SECRETS_JSON, GC_Values[GC_CLIENT_SECRETS_JSON], GAM_WIKI_CREATE_CLIENT_SECRETS)

  checkForExtraneousArguments()
  num_scopes = len(OAUTH2_SCOPES)
  menu = OAUTH2_MENU % tuple(range(num_scopes))
  selected_scopes = [u' '] * num_scopes
  for oauth2Scope in OAUTH2_SCOPES_LIST:
    credentials = getCredentialsForScope(oauth2Scope)
    if credentials and not credentials.invalid:
      currentScopes = sorted(credentials.scopes)
      for i in OAUTH2_SCOPES_MAP[oauth2Scope]:
        selected_scopes[i] = u' '
        possibleScope = OAUTH2_SCOPES[i]
        for currentScope in currentScopes:
          if currentScope == possibleScope:
            selected_scopes[i] = u'*'
            break
          if i in OAUTH2_RO_SCOPES:
            if currentScope == possibleScope+u'.readonly':
              selected_scopes[i] = u'R'
              break
          if i in OAUTH2_AO_SCOPES:
            if currentScope == possibleScope+u'.action':
              selected_scopes[i] = u'A'
              break
    else:
      for i in OAUTH2_SCOPES_MAP[oauth2Scope]:
        selected_scopes[i] = u'*'
  prompt = u'Please enter 0-{0}[a|r] or {1}: '.format(num_scopes-1, u'|'.join(OAUTH2_CMDS))
  while True:
    os.system([u'clear', u'cls'][GM_Globals[GM_WINDOWS]])
    sys.stdout.write(menu % tuple(selected_scopes))
    while True:
      choice = raw_input(prompt)
      if choice:
        selection = choice.lower()
        if selection.find(u'r') >= 0:
          mode = u'R'
          selection = selection.replace(u'r', u'')
        elif selection.find(u'a') >= 0:
          mode = u'A'
          selection = selection.replace(u'a', u'')
        else:
          mode = u' '
        if selection and selection.isdigit():
          selection = int(selection)
        if isinstance(selection, int) and selection < num_scopes:
          if mode == u'R':
            if selection not in OAUTH2_RO_SCOPES:
              sys.stdout.write(u'{0}Scope {1} does not support read-only mode!\n'.format(ERROR_PREFIX, selection))
              continue
          elif mode == u'A':
            if selection not in OAUTH2_AO_SCOPES:
              sys.stdout.write(u'{0}Scope {1} does not support action-only mode!\n'.format(ERROR_PREFIX, selection))
              continue
          elif selected_scopes[selection] != u'*':
            mode = u'*'
          else:
            mode = u' '
          selected_scopes[selection] = mode
          break
        elif isinstance(selection, str) and selection in OAUTH2_CMDS:
          if selection == u's':
            for i in range(num_scopes):
              selected_scopes[i] = u'*'
          elif selection == u'u':
            for i in range(num_scopes):
              selected_scopes[i] = u' '
          elif selection == u'e':
            return
          break
        sys.stdout.write(u'{0}Invalid input "{1}"\n'.format(ERROR_PREFIX, choice))
    if selection == u'c':
      break
  revokeCredentials()
  flags = cmd_flags(noLocalWebserver=GC_Values[GC_NO_BROWSER])
  http = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
  for oauth2Scope in OAUTH2_SCOPES_LIST:
    scopes = [u'email',] # Email Display Scope, always included for client
    for i in OAUTH2_SCOPES_MAP[oauth2Scope]:
      if selected_scopes[i] == u'*':
        scopes.append(OAUTH2_SCOPES[i])
      elif selected_scopes[i] == u'R':
        scopes.append(u'{0}.readonly'.format(OAUTH2_SCOPES[i]))
      elif selected_scopes[i] == u'A':
        scopes.append(u'{0}.action'.format(OAUTH2_SCOPES[i]))
    storage = getCredentialsForScope(oauth2Scope, storageOnly=True)
    try:
      FLOW = oauth2client.client.flow_from_clientsecrets(GC_Values[GC_CLIENT_SECRETS_JSON], scope=scopes)
    except oauth2client.client.clientsecrets.InvalidClientSecretsError:
      systemErrorExit(CLIENT_SECRETS_JSON_REQUIRED_RC, MISSING_CLIENT_SECRETS_MESSAGE)
    try:
      oauth2client.tools.run_flow(flow=FLOW, storage=storage, flags=flags, http=http)
      time.sleep(3)
    except httplib2.CertificateValidationUnsupported:
      noPythonSSLExit()
    except SystemExit as e:
      entityActionFailedWarning(EN_OAUTH2_TXT_FILE, GC_Values[GC_OAUTH2_TXT], e.message)
      systemErrorExit(OAUTH2_TXT_REQUIRED_RC, None)
  entityActionPerformed(EN_OAUTH2_TXT_FILE, GC_Values[GC_OAUTH2_TXT])

# gam oauth|oauth2 delete|revoke
def doOAuthDelete():
  checkForExtraneousArguments()
  if os.path.isfile(GC_Values[GC_OAUTH2_TXT]):
    sys.stdout.write(u'{0}: {1}, will be Deleted in 3...'.format(singularEntityName(EN_OAUTH2_TXT_FILE), GC_Values[GC_OAUTH2_TXT]))
    sys.stdout.flush()
    time.sleep(1)
    sys.stdout.write(u'2...')
    sys.stdout.flush()
    time.sleep(1)
    sys.stdout.write(u'1...')
    sys.stdout.flush()
    time.sleep(1)
    sys.stdout.write(u'boom!\n')
    sys.stdout.flush()
    revokeCredentials()
    if os.path.isfile(GC_Values[GC_OAUTH2_TXT]):
      try:
        os.remove(GC_Values[GC_OAUTH2_TXT])
      except OSError as e:
        stderrWarningMsg(e)
    entityActionPerformed(EN_OAUTH2_TXT_FILE, GC_Values[GC_OAUTH2_TXT])

# gam oauth|oauth2 info [<AccessToken>]
def doOAuthInfo():

  def _printCredentials(credentials):
    if not credentials or credentials.invalid:
      return
    printKeyValueList([u'Client ID', credentials.client_id])
    printKeyValueList([u'Secret', credentials.client_secret])
    printKeyValueList([u'Scopes', u''])
    incrementIndentLevel()
    for scope in sorted(credentials.scopes):
      if scope != u'email':
        printKeyValueList([scope])
    decrementIndentLevel()
    printKeyValueList([u'Google Apps Admin', credentials.id_token.get('email', u'Unknown')])
    printBlankLine()

  access_token = getString(OB_ACCESS_TOKEN, optional=True)
  checkForExtraneousArguments()
  if access_token:
    for oauth2Scope in OAUTH2_SCOPES_LIST:
      credentials = getClientCredentials(oauth2Scope)
      if credentials.access_token == access_token:
        _printCredentials(credentials)
        break
    else:
      entityActionFailedWarning(EN_ACCESS_TOKEN, access_token, PHRASE_DOES_NOT_EXIST)
  else:
    if os.path.isfile(GC_Values[GC_OAUTH2_TXT]):
      printKeyValueList([singularEntityName(EN_OAUTH2_TXT_FILE), GC_Values[GC_OAUTH2_TXT]])
      gapiCredentials = getCredentialsForScope(OAUTH2_GAPI_SCOPES)
      gdataCredentials = getCredentialsForScope(OAUTH2_GDATA_SCOPES)
      if (gapiCredentials and not gapiCredentials.invalid and
          gdataCredentials and not gdataCredentials.invalid and
          gapiCredentials.client_id == gdataCredentials.client_id and
          gapiCredentials.client_secret == gdataCredentials.client_secret and
          gapiCredentials.id_token.get(u'email') == gdataCredentials.id_token.get(u'email')):
        gapiCredentials.scopes = gapiCredentials.scopes.union(gdataCredentials.scopes)
        _printCredentials(gapiCredentials)
      else:
        _printCredentials(gapiCredentials)
        _printCredentials(gdataCredentials)

# gam whatis <EmailItem> [noinfo]
def doWhatIs():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  email = getEmailAddress()
  show_info = not checkArgumentPresent(NOINFO_ARGUMENT)
  if not show_info:
    checkForExtraneousArguments()
  try:
    result = callGAPI(cd.users(), u'get',
                      throw_reasons=GAPI_USER_GET_THROW_REASONS,
                      userKey=email, fields=u'primaryEmail,id')
    if (result[u'primaryEmail'].lower() == email) or (result[u'id'] == email):
      printKeyValueList([u'{0} is a {1}'.format(email, singularEntityName(EN_USER))])
      if show_info:
        infoUsers(entityList=[email])
      setSysExitRC(ENTITY_IS_A_USER_RC)
    else:
      printKeyValueList([u'{0} is a {1}'.format(email, singularEntityName(EN_USER_ALIAS))])
      if show_info:
        infoAliases(entityList=[email])
      setSysExitRC(ENTITY_IS_A_USER_ALIAS_RC)
    return
  except (GAPI_userNotFound, GAPI_badRequest):
    pass
  except (GAPI_domainNotFound, GAPI_forbidden, GAPI_backendError, GAPI_systemError):
    entityUnknownWarning(EN_USER, email)
    setSysExitRC(ENTITY_IS_UKNOWN_RC)
    return
  try:
    result = callGAPI(cd.groups(), u'get',
                      throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
                      groupKey=email, fields=u'email,id')
    if (result[u'email'].lower() == email) or (result[u'id'] == email):
      printKeyValueList([u'{0} is a {1}'.format(email, singularEntityName(EN_GROUP))])
      if show_info:
        infoGroups(entityList=[email])
      setSysExitRC(ENTITY_IS_A_GROUP_RC)
    else:
      printKeyValueList([u'{0} is a {1}'.format(email, singularEntityName(EN_GROUP_ALIAS))])
      if show_info:
        infoAliases(entityList=[email])
      setSysExitRC(ENTITY_IS_A_GROUP_ALIAS_RC)
    return
  except (GAPI_groupNotFound, GAPI_badRequest):
    pass
  except (GAPI_domainNotFound, GAPI_forbidden):
    entityUnknownWarning(EN_USER, email)
    setSysExitRC(ENTITY_IS_UKNOWN_RC)
    return
  printKeyValueList([u'{0} Doesn\'t seem to exist!'.format(email)])
  setSysExitRC(ENTITY_IS_UKNOWN_RC)

# Report choices
#
NL_SPACES_PATTERN = re.compile(r'\n +')

REPORTS_PARAMETERS_SIMPLE_TYPES = [u'intValue', u'boolValue', u'datetimeValue', u'stringValue',]

REPORT_CHOICES_MAP = {
  u'admin': u'admin',
  u'calendar': u'calendar',
  u'calendars': u'calendar',
  u'customer': u'customer',
  u'customers': u'customer',
  u'doc': u'drive',
  u'docs': u'drive',
  u'domain': u'customer',
  u'drive': u'drive',
  u'group': u'groups',
  u'groups': u'groups',
  u'login': u'login',
  u'logins': u'login',
  u'mobile': u'mobile',
  u'token': u'token',
  u'tokens': u'token',
  u'user': u'user',
  u'users': u'user',
  }

# gam report <users|user> [todrive] [nodatechange] [maxresults <Number>]
#	[date <Date>] [user all|<UserItem>] [select <UserTypeEntity>] [filter|filters <String>] [fields|parameters <String>]
# gam report <customers|customer|domain> [todrive] [nodatechange]
#	[date <Date>] [fields|parameters <String>]
# gam report <admin|calendar|calendars|drive|docs|doc|groups|group|logins|login|mobile|tokens|token> [todrive] [maxresults <Number>]
#	[start <Time>] [end <Time>] [user all|<UserItem>] [select <UserTypeEntity>] [event <String>] [filter|filters <String>] [fields|parameters <String>] [ip <String>]
def doReport():

  def _adjustDate(errMsg):
    match_date = re.match(u'Data for dates later than (.*) is not yet available. Please check back later', errMsg)
    if not match_date:
      match_date = re.match(u'Start date can not be later than (.*)', errMsg)
    if (not match_date) or noDateChange:
      printWarningMessage(DATA_NOT_AVALIABLE_RC, errMsg)
      return None
    return str(match_date.group(1))

  report = getChoice(REPORT_CHOICES_MAP, mapChoice=True)
  rep = buildGAPIObject(GAPI_REPORTS_API)
  customerId = GC_Values[GC_CUSTOMER_ID]
  if customerId == MY_CUSTOMER:
    customerId = None
  maxResults = try_date = filters = parameters = actorIpAddress = startTime = endTime = startDateTime = endDateTime = eventName = None
  exitUserLoop = noDateChange = normalizeUsers = select = to_drive = False
  userKey = u'all'
  filtersUserValid = report != u'customer'
  usageReports = report in [u'customer', u'user']
  activityReports = not usageReports
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      to_drive = True
    elif usageReports and myarg == u'date':
      try_date = getYYYYMMDD()
    elif usageReports and myarg == u'nodatechange':
      noDateChange = True
    elif usageReports and myarg in [u'fields', u'parameters']:
      parameters = getString(OB_STRING)
    elif activityReports and myarg == u'start':
      startDateTime, tzinfo, startTime = getFullTime(True)
      earliestDateTime = datetime.datetime.now(tzinfo)-datetime.timedelta(days=180)
      if startDateTime < earliestDateTime:
        putArgumentBack()
        usageErrorExit(MESSAGE_INVALID_TIME_RANGE.format(u'start', startTime, PHRASE_GOOGLE_EARLIEST_REPORT_TIME, earliestDateTime.isoformat()))
      if endDateTime and endDateTime < startDateTime:
        putArgumentBack()
        usageErrorExit(MESSAGE_INVALID_TIME_RANGE.format(u'end', endTime, u'start', startTime))
    elif activityReports and myarg == u'end':
      endDateTime, _, endTime = getFullTime(True)
      if startDateTime and endDateTime < startDateTime:
        putArgumentBack()
        usageErrorExit(MESSAGE_INVALID_TIME_RANGE.format(u'end', endTime, u'start', startTime))
    elif activityReports and myarg == u'event':
      eventName = getString(OB_STRING)
    elif activityReports and myarg == u'ip':
      actorIpAddress = getString(OB_STRING)
    elif filtersUserValid and myarg == u'maxresults':
      maxResults = getInteger(minVal=1, maxVal=1000)
    elif filtersUserValid and myarg == u'user':
      userKey = getString(OB_EMAIL_ADDRESS)
    elif filtersUserValid and myarg == u'select':
      _, users = getEntityToModify(defaultEntityType=CL_ENTITY_USERS)
      select = True
    elif filtersUserValid and myarg in [u'filter', u'filters']:
      filters = getString(OB_STRING)
    else:
      unknownArgumentExit()
  if try_date == None:
    try_date = str(datetime.date.today())
  if report == u'user':
    if select:
      page_message = None
      normalizeUsers = True
    elif userKey == u'all':
      printGettingAccountEntitiesInfo(EN_USER)
      page_message = getPageMessage(showTotal=False)
      users = [u'all']
    else:
      setGettingEntityItem(EN_USER)
      page_message = getPageMessage(showTotal=False)
      users = [normalizeEmailAddressOrUID(userKey)]
    titles, csvRows = initializeTitlesCSVfile([u'email', u'date'])
    i = 0
    count = len(users)
    for user in users:
      i += 1
      if normalizeUsers:
        user = normalizeEmailAddressOrUID(user)
      while True:
        try:
          usage = callGAPIpages(rep.userUsageReport(), u'get', u'usageReports',
                                page_message=page_message,
                                throw_reasons=[GAPI_INVALID, GAPI_BAD_REQUEST, GAPI_FORBIDDEN],
                                date=try_date, userKey=user, customerId=customerId, filters=filters, parameters=parameters,
                                maxResults=maxResults)
          for user_report in usage:
            row = {u'email': user_report[u'entity'][u'userEmail'], u'date': try_date}
            for item in user_report.get(u'parameters', {}):
              name = item[u'name']
              if name not in titles[u'set']:
                addTitleToCSVfile(name, titles)
              for ptype in REPORTS_PARAMETERS_SIMPLE_TYPES:
                if ptype in item:
                  row[name] = item[ptype]
                  break
              else:
                row[name] = u''
            csvRows.append(row)
          break
        except GAPI_invalid as e:
          try_date = _adjustDate(e.message)
          if not try_date:
            return
        except GAPI_badRequest:
          if user != u'all':
            entityUnknownWarning(EN_USER, user, i, count)
          else:
            printErrorMessage(BAD_REQUEST_RC, PHRASE_BAD_REQUEST)
            exitUserLoop = True
          break
        except GAPI_forbidden:
          accessErrorExit(None)
      if exitUserLoop:
        break
    writeCSVfile(csvRows, titles, u'User Reports - {0}'.format(try_date), to_drive)
  elif report == u'customer':
    titles, csvRows = initializeTitlesCSVfile([u'name', u'value', u'client_id'])
    auth_apps = []
    while True:
      try:
        usage = callGAPIpages(rep.customerUsageReports(), u'get', u'usageReports',
                              throw_reasons=[GAPI_INVALID, GAPI_FORBIDDEN],
                              customerId=customerId, date=try_date, parameters=parameters)
        for item in usage[0][u'parameters']:
          name = item[u'name']
          for ptype in REPORTS_PARAMETERS_SIMPLE_TYPES:
            if ptype in item:
              csvRows.append({u'name': name, u'value': item[ptype]})
              break
          else:
            if u'msgValue' in item:
              if name == u'accounts:authorized_apps':
                for subitem in item[u'msgValue']:
                  app = {}
                  for an_item in subitem:
                    if an_item == u'client_name':
                      app[u'name'] = u'App: {0}'.format(subitem[an_item])
                    elif an_item == u'num_users':
                      app[u'value'] = u'{0} users'.format(subitem[an_item])
                    elif an_item == u'client_id':
                      app[u'client_id'] = subitem[an_item]
                  auth_apps.append(app)
        for app in auth_apps: # put apps at bottom
          csvRows.append(app)
        break
      except GAPI_invalid as e:
        try_date = _adjustDate(e.message)
        if not try_date:
          return
      except GAPI_forbidden:
        accessErrorExit(None)
    writeCSVfile(csvRows, titles, u'Customer Report - {0}'.format(try_date), to_drive)
  else:     # admin, calendar, drive, groups, login, mobile, token
    if select:
      page_message = None
      normalizeUsers = True
    elif userKey == u'all':
      printGettingAccountEntitiesInfo(EN_ACTIVITY)
      page_message = getPageMessage(showTotal=False)
      users = [u'all']
    else:
      setGettingEntityItem(EN_ACTIVITY)
      page_message = getPageMessage(showTotal=False)
      users = [normalizeEmailAddressOrUID(userKey)]
    titles, csvRows = initializeTitlesCSVfile(None)
    i = 0
    count = len(users)
    for user in users:
      i += 1
      if normalizeUsers:
        user = normalizeEmailAddressOrUID(user)
      try:
        activities = callGAPIpages(rep.activities(), u'list', u'items',
                                   page_message=page_message,
                                   throw_reasons=[GAPI_BAD_REQUEST, GAPI_INVALID, GAPI_AUTH_ERROR],
                                   applicationName=report, userKey=user, customerId=customerId,
                                   actorIpAddress=actorIpAddress, startTime=startTime, endTime=endTime, eventName=eventName, filters=filters,
                                   maxResults=maxResults)
        for activity in activities:
          events = activity[u'events']
          del activity[u'events']
          activity_row = flattenJSON(activity)
          for event in events:
            for item in event.get(u'parameters', []):
              if u'value' in item:
                item[u'value'] = NL_SPACES_PATTERN.sub(u'', item[u'value'])
            row = flattenJSON(event)
            row.update(activity_row)
            addRowTitlesToCSVfile(row, csvRows, titles)
      except GAPI_badRequest:
        if user != u'all':
          entityUnknownWarning(EN_USER, user, i, count)
        else:
          printErrorMessage(BAD_REQUEST_RC, PHRASE_BAD_REQUEST)
          break
      except GAPI_invalid as e:
        systemErrorExit(GOOGLE_API_ERROR_RC, e.message)
      except GAPI_authError:
        accessErrorExit(None)
    sortCSVTitles([u'name',], titles)
    writeCSVfile(csvRows, titles, u'{0} Activity Report'.format(report.capitalize()), to_drive)

# gam create domainalias|aliasdomain <DomainAlias> <DomainName>
def doCreateDomainAlias():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  body = {u'domainAliasName': getString(OB_DOMAIN_ALIAS)}
  body[u'parentDomainName'] = getString(OB_DOMAIN_NAME)
  checkForExtraneousArguments()
  try:
    callGAPI(cd.domainAliases(), u'insert',
             throw_reasons=[GAPI_DOMAIN_NOT_FOUND, GAPI_DUPLICATE, GAPI_BAD_REQUEST, GAPI_NOT_FOUND, GAPI_FORBIDDEN],
             customer=GC_Values[GC_CUSTOMER_ID], body=body)
    entityItemValueActionPerformed(EN_DOMAIN, body[u'parentDomainName'], EN_DOMAIN_ALIAS, body[u'domainAliasName'])
  except GAPI_domainNotFound:
    entityActionFailedWarning(EN_DOMAIN, body[u'parentDomainName'], PHRASE_DOES_NOT_EXIST)
  except GAPI_duplicate:
    entityItemValueActionFailedWarning(EN_DOMAIN, body[u'parentDomainName'], EN_DOMAIN_ALIAS, body[u'domainAliasName'], PHRASE_DUPLICATE)
  except (GAPI_badRequest, GAPI_notFound, GAPI_forbidden):
    accessErrorExit(cd)

# gam delete domainalias|aliasdomain <DomainAlias>
def doDeleteDomainAlias():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  domainAliasName = getString(OB_DOMAIN_ALIAS)
  checkForExtraneousArguments()
  try:
    callGAPI(cd.domainAliases(), u'delete',
             throw_reasons=[GAPI_DOMAIN_ALIAS_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_NOT_FOUND, GAPI_FORBIDDEN],
             customer=GC_Values[GC_CUSTOMER_ID], domainAliasName=domainAliasName)
    entityActionPerformed(EN_DOMAIN_ALIAS, domainAliasName)
  except GAPI_domainAliasNotFound:
    entityActionFailedWarning(EN_DOMAIN_ALIAS, domainAliasName, PHRASE_DOES_NOT_EXIST)
  except (GAPI_badRequest, GAPI_notFound, GAPI_forbidden):
    accessErrorExit(cd)

DOMAIN_ALIAS_PRINT_ORDER = [u'parentDomainName', u'creationTime', u'verified',]

def _showDomainAlias(alias, alias_skip_objects):
  printEntityName(EN_DOMAIN_ALIAS, alias[u'domainAliasName'])
  incrementIndentLevel()
  if u'creationTime' in alias:
    alias[u'creationTime'] = unicode(datetime.datetime.fromtimestamp(int(alias[u'creationTime'])/1000))
  for field in DOMAIN_ALIAS_PRINT_ORDER:
    if field in alias:
      printKeyValueList([field, alias[field]])
      alias_skip_objects.append(field)
  showJSON(None, alias, skip_objects=alias_skip_objects)
  decrementIndentLevel()

# gam info domainalias|aliasdomain <DomainAlias>
def doInfoDomainAlias():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  domainAliasName = getString(OB_DOMAIN_ALIAS)
  checkForExtraneousArguments()
  try:
    result = callGAPI(cd.domainAliases(), u'get',
                      throw_reasons=[GAPI_DOMAIN_ALIAS_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_NOT_FOUND, GAPI_FORBIDDEN],
                      customer=GC_Values[GC_CUSTOMER_ID], domainAliasName=domainAliasName)
    alias_skip_objects = [u'domainAliasName',]
    _showDomainAlias(result, alias_skip_objects)
  except GAPI_domainAliasNotFound:
    entityActionFailedWarning(EN_DOMAIN_ALIAS, domainAliasName, PHRASE_DOES_NOT_EXIST)
  except (GAPI_badRequest, GAPI_notFound, GAPI_forbidden):
    accessErrorExit(cd)

# gam print domainaliases [todrive]
def doPrintDomainAliases():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'domainAliasName',])
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    else:
      unknownArgumentExit()
  try:
    result = callGAPI(cd.domainAliases(), u'list',
                      throw_reasons=[GAPI_BAD_REQUEST, GAPI_NOT_FOUND, GAPI_FORBIDDEN],
                      customer=GC_Values[GC_CUSTOMER_ID])
    for domainAlias in result.get(u'domainAliases', []):
      domainAlias_attributes = {}
      for attr in domainAlias:
        if attr in [u'kind', u'etag']:
          continue
        if attr == u'creationTime':
          domainAlias[attr] = unicode(datetime.datetime.fromtimestamp(int(domainAlias[attr])/1000))
        domainAlias_attributes[attr] = domainAlias[attr]
        if attr not in titles[u'set']:
          addTitleToCSVfile(attr, titles)
      csvRows.append(domainAlias_attributes)
  except (GAPI_badRequest, GAPI_notFound, GAPI_forbidden):
    accessErrorExit(cd)
  writeCSVfile(csvRows, titles, u'Domain Aliases', todrive)

# gam create domain <DomainName>
def doCreateDomain():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  body = {u'domainName': getString(OB_DOMAIN_NAME)}
  checkForExtraneousArguments()
  try:
    callGAPI(cd.domains(), u'insert',
             throw_reasons=[GAPI_DUPLICATE, GAPI_BAD_REQUEST, GAPI_NOT_FOUND, GAPI_FORBIDDEN],
             customer=GC_Values[GC_CUSTOMER_ID], body=body)
    printEntityKVList(EN_DOMAIN, body[u'domainName'], [ACTION_NAMES[AC_ADD][0]])
  except GAPI_duplicate:
    entityActionFailedWarning(EN_DOMAIN, body[u'domainName'], PHRASE_DUPLICATE)
  except (GAPI_badRequest, GAPI_notFound, GAPI_forbidden):
    accessErrorExit(cd)

# gam update domain <DomainName> primary
def doUpdateDomain():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  domainName = getString(OB_DOMAIN_NAME)
  body = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'primary':
      body[u'customerDomain'] = domainName
    else:
      unknownArgumentExit()
  if not body:
    missingArgumentExit(u'primary')
  try:
    callGAPI(cd.customers(), u'update',
             throw_reasons=[GAPI_DOMAIN_NOT_VERIFIED_SECONDARY, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
             customerKey=GC_Values[GC_CUSTOMER_ID], body=body)
    entityActionPerformedMessage(EN_DOMAIN, domainName, PHRASE_NOW_THE_PRIMARY_DOMAIN)
  except GAPI_domainNotVerifiedSecondary:
    entityActionFailedWarning(EN_DOMAIN, domainName, PHRASE_DOMAIN_NOT_VERIFIED_SECONDARY)
  except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
    accessErrorExit(cd)

# gam delete domain <DomainName>
def doDeleteDomain():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  domainName = getString(OB_DOMAIN_NAME)
  checkForExtraneousArguments()
  try:
    callGAPI(cd.domains(), u'delete',
             throw_reasons=[GAPI_BAD_REQUEST, GAPI_NOT_FOUND, GAPI_FORBIDDEN],
             customer=GC_Values[GC_CUSTOMER_ID], domainName=domainName)
    entityActionPerformed(EN_DOMAIN, domainName)
  except (GAPI_badRequest, GAPI_notFound, GAPI_forbidden):
    accessErrorExit(cd)

DOMAIN_PRINT_ORDER = [u'customerDomain', u'creationTime', u'isPrimary', u'verified',]

# gam info domain [<DomainName>]
def doInfoDomain():
  if (CL_argvI == CL_argvLen) or (CL_argv[CL_argvI].lower() == u'logo'):
    doInfoInstance()
    return
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  domainName = getString(OB_DOMAIN_NAME)
  checkForExtraneousArguments()
  try:
    result = callGAPI(cd.domains(), u'get',
                      throw_reasons=[GAPI_DOMAIN_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_NOT_FOUND, GAPI_FORBIDDEN],
                      customer=GC_Values[GC_CUSTOMER_ID], domainName=domainName)
    skip_objects = [u'domainName', u'domainAliases']
    printEntityName(EN_DOMAIN, result[u'domainName'])
    incrementIndentLevel()
    if u'creationTime' in result:
      result[u'creationTime'] = unicode(datetime.datetime.fromtimestamp(int(result[u'creationTime'])/1000))
    for field in DOMAIN_PRINT_ORDER:
      if field in result:
        printKeyValueList([field, result[field]])
        skip_objects.append(field)
    field = u'domainAliases'
    aliases = result.get(field)
    if aliases:
      skip_objects.append(field)
      alias_skip_objects = [u'domainAliasName',]
      for alias in aliases:
        _showDomainAlias(alias, alias_skip_objects)
        showJSON(None, alias, skip_objects=alias_skip_objects)
    showJSON(None, result, skip_objects=skip_objects)
    decrementIndentLevel()
  except GAPI_domainNotFound:
    entityActionFailedWarning(EN_DOMAIN, domainName, PHRASE_DOES_NOT_EXIST)
  except (GAPI_badRequest, GAPI_notFound, GAPI_forbidden):
    accessErrorExit(cd)

# gam print domains [todrive]
def doPrintDomains():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'domainName',])
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    else:
      unknownArgumentExit()
  try:
    domains = callGAPI(cd.domains(), u'list',
                       throw_reasons=[GAPI_BAD_REQUEST, GAPI_NOT_FOUND, GAPI_FORBIDDEN],
                       customer=GC_Values[GC_CUSTOMER_ID])
    for domain in domains[u'domains']:
      domain_attributes = {}
      domain[u'type'] = [u'secondary', u'primary'][domain[u'isPrimary']]
      for attr in domain:
        if attr in [u'kind', u'etag', u'domainAliases', u'isPrimary']:
          continue
        if attr == u'creationTime':
          domain[attr] = unicode(datetime.datetime.fromtimestamp(int(domain[attr])/1000))
        domain_attributes[attr] = domain[attr]
        if attr not in titles[u'set']:
          addTitleToCSVfile(attr, titles)
      csvRows.append(domain_attributes)
      if u'domainAliases' in domain:
        for aliasdomain in domain[u'domainAliases']:
          aliasdomain[u'domainName'] = aliasdomain[u'domainAliasName']
          del aliasdomain[u'domainAliasName']
          aliasdomain[u'type'] = u'alias'
          aliasdomain_attributes = {}
          for attr in aliasdomain:
            if attr in [u'kind', u'etag']:
              continue
            if attr == u'creationTime':
              aliasdomain[attr] = unicode(datetime.datetime.fromtimestamp(int(aliasdomain[attr])/1000))
            aliasdomain_attributes[attr] = aliasdomain[attr]
            if attr not in titles[u'set']:
              addTitleToCSVfile(attr, titles)
          csvRows.append(aliasdomain_attributes)
  except (GAPI_badRequest, GAPI_notFound, GAPI_forbidden):
    accessErrorExit(cd)
  writeCSVfile(csvRows, titles, u'Domains', todrive)

# gam print adminroles|roles [todrive]
def doPrintAdminRoles():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'roleId', u'roleName', u'roleDescription', u'isSuperAdminRole', u'isSystemRole'])
  fields = u'nextPageToken,items({0})'.format(u','.join(titles[u'list']))
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    else:
      unknownArgumentExit()
  try:
    roles = callGAPIpages(cd.roles(), u'list', u'items',
                          throw_reasons=[GAPI_BAD_REQUEST, GAPI_CUSTOMER_NOT_FOUND, GAPI_FORBIDDEN],
                          customer=GC_Values[GC_CUSTOMER_ID], fields=fields)
    for role in roles:
      role_attrib = {}
      for attr, value in role.items():
        role_attrib[attr] = value
      csvRows.append(role_attrib)
  except (GAPI_badRequest, GAPI_customerNotFound, GAPI_forbidden):
    accessErrorExit(cd)
  writeCSVfile(csvRows, titles, u'Admin Roles', todrive)

def buildOrgUnitIdToNameMap():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  try:
    result = callGAPI(cd.orgunits(), u'list',
                      throw_reasons=[GAPI_BAD_REQUEST, GAPI_INVALID_CUSTOMER_ID, GAPI_LOGIN_REQUIRED],
                      customerId=GC_Values[GC_CUSTOMER_ID],
                      fields=u'organizationUnits(orgUnitPath,orgUnitId)', type=u'all')
    GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME] = {}
    for orgUnit in result[u'organizationUnits']:
      GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME][orgUnit[u'orgUnitId']] = orgUnit[u'orgUnitPath']
  except (GAPI_badRequest, GAPI_invalidCustomerId, GAPI_loginRequired):
    accessErrorExit(cd)

def orgunit_from_orgunitid(orgunitid):
  if not GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME]:
    buildOrgUnitIdToNameMap()
  return GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME].get(orgunitid, orgunitid)

def buildRoleIdToNameToIdMap():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  try:
    result = callGAPIpages(cd.roles(), u'list', u'items',
                           throw_reasons=[GAPI_BAD_REQUEST, GAPI_CUSTOMER_NOT_FOUND, GAPI_FORBIDDEN],
                           customer=GC_Values[GC_CUSTOMER_ID],
                           fields=u'nextPageToken,items(roleId,roleName)',
                           maxResults=100)
    GM_Globals[GM_MAP_ROLE_ID_TO_NAME] = {}
    GM_Globals[GM_MAP_ROLE_NAME_TO_ID] = {}
    for role in result:
      GM_Globals[GM_MAP_ROLE_ID_TO_NAME][role[u'roleId']] = role[u'roleName']
      GM_Globals[GM_MAP_ROLE_NAME_TO_ID][role[u'roleName']] = role[u'roleId']
  except (GAPI_badRequest, GAPI_customerNotFound, GAPI_forbidden):
    accessErrorExit(cd)

def role_from_roleid(roleid):
  if not GM_Globals[GM_MAP_ROLE_ID_TO_NAME]:
    buildRoleIdToNameToIdMap()
  return GM_Globals[GM_MAP_ROLE_ID_TO_NAME].get(roleid, roleid)

def roleid_from_role(role):
  if not GM_Globals[GM_MAP_ROLE_NAME_TO_ID]:
    buildRoleIdToNameToIdMap()
  return GM_Globals[GM_MAP_ROLE_NAME_TO_ID].get(role, None)

def buildUserIdToNameMap():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  try:
    result = callGAPIpages(cd.users(), u'list', u'users',
                           customer=GC_Values[GC_CUSTOMER_ID],
                           throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                           fields=u'nextPageToken,users(id,primaryEmail)',
                           maxResults=GC_Values[GC_USER_MAX_RESULTS])
    GM_Globals[GM_MAP_USER_ID_TO_NAME] = {}
    for user in result:
      GM_Globals[GM_MAP_USER_ID_TO_NAME][user[u'id']] = user[u'primaryEmail']
  except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
    accessErrorExit(cd)

def user_from_userid(userid):
  if not GM_Globals[GM_MAP_USER_ID_TO_NAME]:
    buildUserIdToNameMap()
  return GM_Globals[GM_MAP_USER_ID_TO_NAME].get(userid, u'')

def getRoleId():
  role = getString(OB_ROLE_ID)
  if role[:4].lower() == u'uid:':
    roleId = role[4:]
  else:
    roleId = roleid_from_role(role)
    if not roleId:
      putArgumentBack()
      invalidChoiceExit(GM_Globals[GM_MAP_ROLE_NAME_TO_ID])
  return (role, roleId)

def getOrgUnitId(cd):
  orgUnit = getOrgUnitPath()
  if orgUnit[:3] == u'id:':
    return (orgUnit, orgUnit[3:])
  try:
    result = callGAPI(cd.orgunits(), u'get',
                      throw_reasons=[GAPI_INVALID_ORGUNIT, GAPI_ORGUNIT_NOT_FOUND, GAPI_BACKEND_ERROR, GAPI_BAD_REQUEST, GAPI_INVALID_CUSTOMER_ID, GAPI_LOGIN_REQUIRED],
                      customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=makeOrgUnitPathRelative(orgUnit),
                      fields=u'orgUnitId')
    return (orgUnit, result[u'orgUnitId'][3:])
  except (GAPI_invalidOrgunit, GAPI_orgunitNotFound, GAPI_backendError):
    putArgumentBack()
    usageErrorExit(formatKeyValueList(GM_Globals[GM_INDENT_SPACES],
                                      [singularEntityName(EN_ORGANIZATIONAL_UNIT), orgUnit,
                                       PHRASE_DOES_NOT_EXIST],
                                      u'\n'))
  except (GAPI_badRequest, GAPI_invalidCustomerId, GAPI_loginRequired):
    accessErrorExit(cd)

ADMIN_SCOPE_TYPE_CHOICE_MAP = {u'customer': u'CUSTOMER', u'orgunit': u'ORG_UNIT', u'org': u'ORG_UNIT', u'ou': u'ORG_UNIT'}

# gam create admin <UserItem> <RoleItem> customer|(org_unit <OrgUnitItem>)
def doCreateAdmin():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  user = getEmailAddress()
  body = {u'assignedTo': convertEmailToUserID(user)}
  role, roleId = getRoleId()
  body[u'roleId'] = roleId
  body[u'scopeType'] = getChoice(ADMIN_SCOPE_TYPE_CHOICE_MAP, mapChoice=True)
  if body[u'scopeType'] == u'ORG_UNIT':
    orgUnit, body[u'orgUnitId'] = getOrgUnitId(cd)
    scope = u'ORG_UNIT {0}'.format(orgUnit)
  else:
    scope = u'CUSTOMER'
  checkForExtraneousArguments()
  try:
    result = callGAPI(cd.roleAssignments(), u'insert',
                      throw_reasons=[GAPI_INTERNAL_ERROR, GAPI_BAD_REQUEST, GAPI_CUSTOMER_NOT_FOUND, GAPI_FORBIDDEN],
                      customer=GC_Values[GC_CUSTOMER_ID], body=body)
    entityActionPerformedMessage(EN_ROLE_ASSIGNMENT_ID, result[u'roleAssignmentId'],
                                 u'{0} {1}, {2} {3}, {4} {5}'.format(singularEntityName(EN_USER), user,
                                                                     singularEntityName(EN_ROLE), role,
                                                                     singularEntityName(EN_SCOPE), scope))
  except GAPI_internalError:
    pass
  except (GAPI_badRequest, GAPI_customerNotFound, GAPI_forbidden):
    accessErrorExit(cd)

# gam delete admin <RoleAssignmentId>
def doDeleteAdmin():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  roleAssignmentId = getString(OB_ROLE_ASSIGNMENT_ID)
  checkForExtraneousArguments()
  try:
    callGAPI(cd.roleAssignments(), u'delete',
             throw_reasons=[GAPI_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_CUSTOMER_NOT_FOUND, GAPI_FORBIDDEN],
             customer=GC_Values[GC_CUSTOMER_ID], roleAssignmentId=roleAssignmentId)
    entityActionPerformed(EN_ROLE_ASSIGNMENT_ID, roleAssignmentId)
  except GAPI_notFound:
    entityActionFailedWarning(EN_ROLE_ASSIGNMENT_ID, roleAssignmentId, PHRASE_DOES_NOT_EXIST)
  except (GAPI_badRequest, GAPI_customerNotFound, GAPI_forbidden):
    accessErrorExit(cd)

# gam print admins [todrive] [user <UserItem>] [role <RoleItem>]
def doPrintAdmins():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  roleId = None
  userKey = None
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'roleAssignmentId', u'roleId', u'role', u'assignedTo', u'assignedToUser', u'scopeType', u'orgUnitId', u'orgUnit'])
  fields = u'nextPageToken,items({0})'.format(u','.join([u'roleAssignmentId', u'roleId', u'assignedTo', u'scopeType', u'orgUnitId']))
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'user':
      userKey = getEmailAddress()
    elif myarg == u'role':
      _, roleId = getRoleId()
    else:
      unknownArgumentExit()
  try:
    result = callGAPIpages(cd.roleAssignments(), u'list', u'items',
                           throw_reasons=[GAPI_INVALID, GAPI_BAD_REQUEST, GAPI_CUSTOMER_NOT_FOUND, GAPI_FORBIDDEN],
                           customer=GC_Values[GC_CUSTOMER_ID], userKey=userKey, roleId=roleId, fields=fields)
    for admin in result:
      admin_attrib = {}
      for attr, value in admin.items():
        if attr == u'assignedTo':
          admin_attrib[u'assignedToUser'] = user_from_userid(value)
        elif attr == u'roleId':
          admin_attrib[u'role'] = role_from_roleid(value)
        elif attr == u'orgUnitId':
          value = u'id:{0}'.format(value)
          admin_attrib[u'orgUnit'] = orgunit_from_orgunitid(value)
        admin_attrib[attr] = value
      csvRows.append(admin_attrib)
    writeCSVfile(csvRows, titles, u'Admins', todrive)
  except GAPI_invalid:
    entityUnknownWarning(EN_USER, userKey)
  except (GAPI_badRequest, GAPI_customerNotFound, GAPI_forbidden):
    accessErrorExit(cd)

ADDRESS_FIELDS_PRINT_ORDER = [u'contactName', u'organizationName', u'addressLine1', u'addressLine2', u'addressLine3', u'locality', u'region', u'postalCode', u'countryCode']

# gam info customer
def doInfoCustomer():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  try:
    customer_info = callGAPI(cd.customers(), u'get',
                             throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                             customerKey=GC_Values[GC_CUSTOMER_ID])
    printKeyValueList([u'Customer ID', customer_info[u'id']])
    printKeyValueList([u'Primary Domain', customer_info[u'customerDomain']])
    printKeyValueList([u'Customer Creation Time', customer_info[u'customerCreationTime']])
    verified = callGAPI(cd.domains(), u'get',
                        customer=customer_info[u'id'], domainName=customer_info[u'customerDomain'], fields=u'verified')[u'verified']
    printKeyValueList([u'Primary Domain Verified', verified])
    printKeyValueList([u'Default Language', customer_info[u'language']])
    if u'postalAddress' in customer_info:
      printKeyValueList([u'Address', u''])
      incrementIndentLevel()
      for field in ADDRESS_FIELDS_PRINT_ORDER:
        if field in customer_info[u'postalAddress']:
          printKeyValueList([field, customer_info[u'postalAddress'][field]])
      decrementIndentLevel()
    if u'phoneNumber' in customer_info:
      printKeyValueList([u'Phone', customer_info[u'phoneNumber']])
    printKeyValueList([u'Admin Secondary Email', customer_info[u'alternateEmail']])
  except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
    accessErrorExit(cd)

ADDRESS_FIELDS_ARGUMENT_MAP = {
  u'contact': u'contactName', u'contactname': u'contactName',
  u'name': u'organizationName', u'organizationname': u'organizationName',
  u'address1': u'addressLine1', u'addressline1': u'addressLine1',
  u'address2': u'addressLine2', u'addressline2': u'addressLine2',
  u'address3': u'addressLine3', u'addressline3': u'addressLine3',
  u'locality': u'locality',
  u'region': u'region',
  u'postalcode': u'postalCode',
  u'country': u'countryCode', u'countrycode': u'countryCode',
  }

# gam update customer [primary <DomainName>] [adminsecondaryemail|alternateemail <EmailAddress>] [language <LanguageCode] [phone|phonenumber <String>]
#	[contact|contactname <String>] [name|organizationname <String>]
#	[address1|addressline1 <String>] [address2|addressline2 <String>] [address3|addressline3 <String>]
#	[locality <String>] [region <String>] [postalcode <String>] [country|countrycode <String>]
def doUpdateCustomer():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  body = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg in ADDRESS_FIELDS_ARGUMENT_MAP:
      body.setdefault(u'postalAddress', {})
      body[u'postalAddress'][ADDRESS_FIELDS_ARGUMENT_MAP[myarg]] = getString(OB_STRING, emptyOK=True)
    elif myarg == u'primary':
      body[u'customerDomain'] = getString(OB_DOMAIN_NAME)
    elif myarg in [u'adminsecondaryemail', u'alternateemail']:
      body[u'alternateEmail'] = getEmailAddress(noUid=True)
    elif myarg in [u'phone', u'phonenumber']:
      body[u'phoneNumber'] = getString(OB_STRING, emptyOK=True)
    elif myarg == u'language':
      body[u'language'] = getChoice(LANGUAGE_CODES_MAP, mapChoice=True)
    else:
      unknownArgumentExit()
  if body:
    try:
      callGAPI(cd.customers(), u'update',
               throw_reasons=[GAPI_DOMAIN_NOT_VERIFIED_SECONDARY, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
               customerKey=GC_Values[GC_CUSTOMER_ID], body=body)
      entityActionPerformed(EN_CUSTOMER_ID, GC_Values[GC_CUSTOMER_ID])
    except GAPI_domainNotVerifiedSecondary:
      entityItemValueActionFailedWarning(EN_CUSTOMER_ID, GC_Values[GC_CUSTOMER_ID], EN_DOMAIN, body[u'customerDomain'], PHRASE_DOMAIN_NOT_VERIFIED_SECONDARY)
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      accessErrorExit(cd)

SERVICE_NAME_TO_ID_MAP = {u'Drive': u'55656082996', u'Google+': u'553547912911',}

def appID2app(dt, appID):
  for serviceName, serviceID in SERVICE_NAME_TO_ID_MAP.items():
    if appID == serviceID:
      return serviceName
  try:
    online_services = callGAPIpages(dt.applications(), u'list', u'applications',
                                    throw_reasons=[GAPI_UNKNOWN_ERROR, GAPI_FORBIDDEN],
                                    customerId=GC_Values[GC_CUSTOMER_ID])
    for online_service in online_services:
      if appID == online_service[u'id']:
        return online_service[u'name']
    return u'applicationId: {0}'.format(appID)
  except (GAPI_unknownError, GAPI_forbidden):
    accessErrorExit(None)

SERVICE_NAME_CHOICES_MAP = {
  u'googleplus': u'Google+',
  u'google+': u'Google+',
  u'gplus': u'Google+',
  u'g+': u'Google+',
  u'drive': u'Drive',
  u'googledrive': u'Drive',
  u'gdrive': u'Drive',
  }

def getService(dt):
  serviceName = getString(OB_SERVICE_NAME).lower()
  if serviceName in SERVICE_NAME_CHOICES_MAP:
    return (SERVICE_NAME_CHOICES_MAP[serviceName], SERVICE_NAME_TO_ID_MAP[SERVICE_NAME_CHOICES_MAP[serviceName]])
  try:
    online_services = callGAPIpages(dt.applications(), u'list', u'applications',
                                    throw_reasons=[GAPI_UNKNOWN_ERROR, GAPI_FORBIDDEN],
                                    customerId=GC_Values[GC_CUSTOMER_ID])
    serviceNameList = []
    for online_service in online_services:
      if serviceName == online_service[u'name'].lower():
        return (online_service[u'name'], online_service[u'id'])
      serviceNameList.append(online_service[u'name'].lower())
    putArgumentBack()
    invalidChoiceExit(serviceNameList)
  except (GAPI_unknownError, GAPI_forbidden):
    accessErrorExit(None)

# gam create datatransfer|transfer <OldOwnerID> <Service> <NewOwnerID> (<ParameterKey> <ParameterValue>)*
def doCreateDataTransfer():
  dt = buildGAPIObject(GAPI_DATATRANSFER_API)
  old_owner = getEmailAddress()
  body = {u'oldOwnerUserId': convertEmailToUserID(old_owner)}
  serviceName, serviceID = getService(dt)
  new_owner = getEmailAddress()
  body[u'newOwnerUserId'] = convertEmailToUserID(new_owner)
  if body[u'oldOwnerUserId'] == body[u'newOwnerUserId']:
    putArgumentBack()
    usageErrorExit(PHRASE_NEW_OWNER_MUST_DIFFER_FROM_OLD_OWNER)
  parameters = {}
  while CL_argvI < CL_argvLen:
    key = getString(OB_PARAMETER_KEY).upper()
    parameters[key] = getString(OB_PARAMETER_VALUE).upper().split(u',')
  body[u'applicationDataTransfers'] = [{u'applicationId': serviceID}]
  for key in parameters:
    body[u'applicationDataTransfers'][0].setdefault(u'applicationTransferParams', [])
    body[u'applicationDataTransfers'][0][u'applicationTransferParams'].append({u'key': key, u'value': parameters[key]})
  result = callGAPI(dt.transfers(), u'insert',
                    body=body, fields=u'id')
  entityActionPerformed(EN_TRANSFER_REQUEST, None)
  incrementIndentLevel()
  printKeyValueList([singularEntityName(EN_TRANSFER_ID), result[u'id']])
  printKeyValueList([singularEntityName(EN_SERVICE), serviceName])
  printKeyValueList([PHRASE_FROM, old_owner])
  printKeyValueList([PHRASE_TO, new_owner])
  decrementIndentLevel()

# gam info datatransfer|transfer <TransferID>
def doInfoDataTransfer():
  dt = buildGAPIObject(GAPI_DATATRANSFER_API)
  dtId = getString(OB_TRANSFER_ID)
  checkForExtraneousArguments()
  try:
    transfer = callGAPI(dt.transfers(), u'get',
                        throw_reasons=[GAPI_NOT_FOUND],
                        dataTransferId=dtId)
    printEntityName(EN_TRANSFER_ID, transfer[u'id'])
    incrementIndentLevel()
    printKeyValueList([u'Old Owner', convertUserIDtoEmail(transfer[u'oldOwnerUserId'])])
    printKeyValueList([u'New Owner', convertUserIDtoEmail(transfer[u'newOwnerUserId'])])
    printKeyValueList([u'Request Time', transfer[u'requestTime']])
    for app in transfer[u'applicationDataTransfers']:
      printKeyValueList([u'Application', appID2app(dt, app[u'applicationId'])])
      incrementIndentLevel()
      printKeyValueList([u'Status', app[u'applicationTransferStatus']])
      printKeyValueList([u'Parameters', u''])
      incrementIndentLevel()
      if u'applicationTransferParams' in app:
        for param in app[u'applicationTransferParams']:
          printKeyValueList([param[u'key'], u','.join(param[u'value'])])
      else:
        printKeyValueList([u'None', None])
      decrementIndentLevel()
      decrementIndentLevel()
    decrementIndentLevel()
    printBlankLine()
  except GAPI_notFound:
    entityActionFailedWarning(EN_TRANSFER_ID, dtId, PHRASE_DOES_NOT_EXIST)

DATA_TRANSFER_STATUS_MAP = {
  u'completed': u'completed',
  u'failed': u'failed',
  u'pending': u'pending',
  u'inprogress': u'inProgress',
  }

# gam print datatransfers|transfers [todrive] [olduser|oldowner <UserItem>] [newuser|newowner <UserItem>] [status <String>]
def doPrintDataTransfers():
  dt = buildGAPIObject(GAPI_DATATRANSFER_API)
  newOwnerUserId = None
  oldOwnerUserId = None
  status = None
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'id',])
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg in [u'olduser', u'oldowner']:
      oldOwnerUserId = convertEmailToUserID(getEmailAddress())
    elif myarg in [u'newuser', u'newowner']:
      newOwnerUserId = convertEmailToUserID(getEmailAddress())
    elif myarg == u'status':
      status = getChoice(DATA_TRANSFER_STATUS_MAP, mapChoice=True)
    else:
      unknownArgumentExit()
  try:
    transfers = callGAPIpages(dt.transfers(), u'list', u'dataTransfers',
                              throw_reasons=[GAPI_UNKNOWN_ERROR, GAPI_FORBIDDEN],
                              customerId=GC_Values[GC_CUSTOMER_ID], status=status,
                              newOwnerUserId=newOwnerUserId, oldOwnerUserId=oldOwnerUserId)
    for transfer in transfers:
      for i in range(len(transfer[u'applicationDataTransfers'])):
        a_transfer = {}
        a_transfer[u'oldOwnerUserEmail'] = convertUserIDtoEmail(transfer[u'oldOwnerUserId'])
        a_transfer[u'newOwnerUserEmail'] = convertUserIDtoEmail(transfer[u'newOwnerUserId'])
        a_transfer[u'requestTime'] = transfer[u'requestTime']
        a_transfer[u'applicationId'] = transfer[u'applicationDataTransfers'][i][u'applicationId']
        a_transfer[u'application'] = appID2app(dt, a_transfer[u'applicationId'])
        a_transfer[u'status'] = transfer[u'applicationDataTransfers'][i][u'applicationTransferStatus']
        a_transfer[u'id'] = transfer[u'id']
        for param in transfer[u'applicationDataTransfers'][i].get(u'applicationTransferParams', []):
          a_transfer[param[u'key']] = u','.join(param[u'value'])
      addRowTitlesToCSVfile(a_transfer, csvRows, titles)
  except (GAPI_unknownError, GAPI_forbidden):
    accessErrorExit(None)
  writeCSVfile(csvRows, titles, u'Data Transfers', todrive)

# gam print transferapps
def doPrintTransferApps():
  dt = buildGAPIObject(GAPI_DATATRANSFER_API)
  checkForExtraneousArguments()
  try:
    apps = callGAPIpages(dt.applications(), u'list', u'applications',
                         throw_reasons=[GAPI_UNKNOWN_ERROR, GAPI_FORBIDDEN],
                         customerId=GC_Values[GC_CUSTOMER_ID])
    for app in apps:
      showJSON(None, app)
      printBlankLine()
  except (GAPI_unknownError, GAPI_forbidden):
    accessErrorExit(None)

UPDATE_INSTANCE_CHOICES = [u'logo', u'ssokey', u'ssosettings',]

# gam update instance
def doUpdateInstance():
  adminSettingsObject = getAdminSettingsObject()
  command = getChoice(UPDATE_INSTANCE_CHOICES)
  try:
    if command == u'logo':
# gam update instance logo <FileName>
      logoFile = getString(OB_FILE_NAME)
      checkForExtraneousArguments()
      logoImage = readFile(logoFile)
      callGData(adminSettingsObject, u'UpdateDomainLogo',
                throw_errors=[GDATA_INVALID_DOMAIN, GDATA_INVALID_VALUE],
                logoImage=logoImage)
      entityItemValueActionPerformed(EN_INSTANCE, u'', EN_LOGO, logoFile)
    elif command == u'ssosettings':
# gam update instance sso_settings [enabled <Boolean>] [sign_on_uri <URI>] [sign_out_uri <URI>] [password_uri <URI>] [whitelist <CIDRnetmask>] [use_domain_specific_issuer <Boolean>]
      enableSSO = samlSignonUri = samlLogoutUri = changePasswordUri = ssoWhitelist = useDomainSpecificIssuer = None
      while CL_argvI < CL_argvLen:
        myarg = getArgument()
        if myarg == u'enabled':
          enableSSO = getBoolean()
        elif myarg == u'signonuri':
          samlSignonUri = getString(OB_URI)
        elif myarg == u'signouturi':
          samlLogoutUri = getString(OB_URI)
        elif myarg == u'passworduri':
          changePasswordUri = getString(OB_URI)
        elif myarg == u'whitelist':
          ssoWhitelist = getString(OB_CIDR_NETMASK)
        elif myarg == u'usedomainspecificissuer':
          useDomainSpecificIssuer = getBoolean()
        else:
          unknownArgumentExit()
      callGData(adminSettingsObject, u'UpdateSSOSettings',
                throw_errors=[GDATA_INVALID_DOMAIN, GDATA_INVALID_VALUE],
                enableSSO=enableSSO, samlSignonUri=samlSignonUri, samlLogoutUri=samlLogoutUri, changePasswordUri=changePasswordUri,
                ssoWhitelist=ssoWhitelist, useDomainSpecificIssuer=useDomainSpecificIssuer)
      entityItemValueActionPerformed(EN_INSTANCE, u'', EN_SSO_SETTINGS, u'')
    elif command == u'ssokey':
# gam update instance sso_key <FileName>
      keyFile = getString(OB_FILE_NAME)
      checkForExtraneousArguments()
      keyData = readFile(keyFile)
      callGData(adminSettingsObject, u'UpdateSSOKey',
                throw_errors=[GDATA_INVALID_DOMAIN, GDATA_INVALID_VALUE],
                signingKey=keyData)
      entityItemValueActionPerformed(EN_INSTANCE, u'', EN_SSO_KEY, keyFile)
  except GData_invalidDomain as e:
    printErrorMessage(INVALID_DOMAIN_RC, e.message)
  except GData_invalidValue as e:
    printErrorMessage(INVALID_DOMAIN_VALUE_RC, e.message)
#
MAXIMUM_USERS_MAP = [u'maximumNumberOfUsers', u'Maximum Users']
CURRENT_USERS_MAP = [u'currentNumberOfUsers', u'Current Users']
DOMAIN_EDITION_MAP = [u'edition', u'Domain Edition']
CUSTOMER_PIN_MAP = [u'customerPIN', u'Customer PIN']
SINGLE_SIGN_ON_SETTINGS_MAP = [u'enableSSO', u'SSO Enabled',
                               u'samlSignonUri', u'SSO Signon Page',
                               u'samlLogoutUri', u'SSO Logout Page',
                               u'changePasswordUri', u'SSO Password Page',
                               u'ssoWhitelist', u'SSO Whitelist IPs',
                               u'useDomainSpecificIssuer', u'SSO Use Domain Specific Issuer']
SINGLE_SIGN_ON_SIGNING_KEY_MAP = [u'algorithm', u'SSO Key Algorithm',
                                  u'format', u'SSO Key Format',
                                  u'modulus', u'SSO Key Modulus',
                                  u'exponent', u'SSO Key Exponent',
                                  u'yValue', u'SSO Key yValue',
                                  u'signingKey', u'Full SSO Key']

# gam info instance [logo <FileName>]
def doInfoInstance():
  def _printAdminSetting(service, propertyTitleMap):
    try:
      result = callGAPI(service, u'get',
                        throw_reasons=[GAPI_DOMAIN_NOT_FOUND, GAPI_INVALID],
                        domainName=GC_Values[GC_DOMAIN])
      if result and (u'entry' in result) and (u'apps$property' in result[u'entry']):
        for i in range(0, len(propertyTitleMap), 2):
          asProperty = propertyTitleMap[i]
          for entry in result[u'entry'][u'apps$property']:
            if entry[u'name'] == asProperty:
              printKeyValueList([propertyTitleMap[i+1], entry[u'value']])
              break
    except GAPI_domainNotFound:
      systemErrorExit(INVALID_DOMAIN_RC, formatKeyValueList(u'', [singularEntityName(EN_DOMAIN), GC_Values[GC_DOMAIN], PHRASE_DOES_NOT_EXIST], u''))
    except GAPI_invalid:
      pass

  if checkArgumentPresent(LOGO_ARGUMENT):
    setActionName(AC_DOWNLOAD)
    logoFile = getString(OB_FILE_NAME)
    checkForExtraneousArguments()
    url = u'http://www.google.com/a/cpanel/%s/images/logo.gif' % (GC_Values[GC_DOMAIN])
    geturl(url, logoFile)
    entityItemValueActionPerformed(EN_INSTANCE, u'', EN_LOGO, logoFile)
    return
  checkForExtraneousArguments()
  doInfoCustomer()
  adm = buildGAPIObject(GAPI_ADMIN_SETTINGS_API)
  _printAdminSetting(adm.maximumNumberOfUsers(), MAXIMUM_USERS_MAP)
  _printAdminSetting(adm.currentNumberOfUsers(), CURRENT_USERS_MAP)
  _printAdminSetting(adm.edition(), DOMAIN_EDITION_MAP)
  _printAdminSetting(adm.customerPIN(), CUSTOMER_PIN_MAP)
  _printAdminSetting(adm.ssoGeneral(), SINGLE_SIGN_ON_SETTINGS_MAP)
  _printAdminSetting(adm.ssoSigningKey(), SINGLE_SIGN_ON_SIGNING_KEY_MAP)

# gam create org|ou <Name> [description <String>] [parent <OrgUnitPath>] [inherit] [noinherit]
def doCreateOrg():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  name = getOrgUnitPath(absolutePath=False)
  parent = u''
  body = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'description':
      body[u'description'] = getString(OB_STRING)
    elif myarg == u'parent':
      parent = getOrgUnitPath()
    elif myarg == u'noinherit':
      body[u'blockInheritance'] = True
    elif myarg == u'inherit':
      body[u'blockInheritance'] = False
    else:
      unknownArgumentExit()
  if parent.startswith(u'id:'):
    body[u'parentOrgUnitId'] = parent
    body[u'name'] = name
    orgUnitPath = parent+u'/'+name
  else:
    if parent == u'/':
      orgUnitPath = parent+name
    else:
      orgUnitPath = parent+u'/'+name
    if orgUnitPath.count(u'/') > 1:
      body[u'parentOrgUnitPath'], body[u'name'] = orgUnitPath.rsplit(u'/', 1)
    else:
      body[u'parentOrgUnitPath'] = u'/'
      body[u'name'] = orgUnitPath[1:]
    parent = body[u'parentOrgUnitPath']
  try:
    callGAPI(cd.orgunits(), u'insert',
             throw_reasons=[GAPI_INVALID_PARENT_ORGUNIT, GAPI_INVALID_ORGUNIT, GAPI_BACKEND_ERROR, GAPI_BAD_REQUEST, GAPI_INVALID_CUSTOMER_ID, GAPI_LOGIN_REQUIRED],
             customerId=GC_Values[GC_CUSTOMER_ID], body=body)
    entityActionPerformed(EN_ORGANIZATIONAL_UNIT, orgUnitPath)
  except GAPI_invalidParentOrgunit:
    entityItemValueActionFailedWarning(EN_ORGANIZATIONAL_UNIT, orgUnitPath, EN_PARENT_ORGANIZATIONAL_UNIT, parent, PHRASE_ENTITY_DOES_NOT_EXIST.format(singularEntityName(EN_PARENT_ORGANIZATIONAL_UNIT)))
  except (GAPI_invalidOrgunit, GAPI_backendError):
    entityDuplicateWarning(EN_ORGANIZATIONAL_UNIT, orgUnitPath)
  except (GAPI_badRequest, GAPI_invalidCustomerId, GAPI_loginRequired):
    accessErrorExit(cd)

def checkOrgUnitPathExists(cd, orgUnitPath, i=0, count=0):
  if orgUnitPath == u'/':
    return orgUnitPath
  orgUnitPath = makeOrgUnitPathRelative(orgUnitPath)
  try:
    result = callGAPI(cd.orgunits(), u'get',
                      throw_reasons=[GAPI_INVALID_ORGUNIT, GAPI_ORGUNIT_NOT_FOUND, GAPI_BACKEND_ERROR, GAPI_BAD_REQUEST, GAPI_INVALID_CUSTOMER_ID, GAPI_LOGIN_REQUIRED],
                      customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=orgUnitPath, fields=u'orgUnitPath')
    return result[u'orgUnitPath']
  except (GAPI_invalidOrgunit, GAPI_orgunitNotFound, GAPI_backendError):
    entityActionFailedWarning(EN_ORGANIZATIONAL_UNIT, orgUnitPath, PHRASE_DOES_NOT_EXIST, i, count)
    return None
  except (GAPI_badRequest, GAPI_invalidCustomerId, GAPI_loginRequired):
    accessErrorExit(cd)

# gam update orgs|ous <OrgUnitEntity> [<Name>] [description <String>] [parent <OrgUnitPath>] [inherit|noinherit]
# gam update orgs|ous <OrgUnitEntity> add|move <CrosTypeEntity>|<UserTypeEntity>
def doUpdateOrgs():
  updateOrgs(getEntityList(OB_ORGUNIT_ENTITY, shlexSplit=True))

# gam update org|ou <OrgUnitPath> [<Name>] [description <String>]  [parent <OrgUnitPath>] [inherit|noinherit]
# gam update org|ou <OrgUnitPath> add|move <CrosTypeEntity>|<UserTypeEntity>
def doUpdateOrg():
  updateOrgs([getOrgUnitPath()])

def updateOrgs(entityList):
  def _callbackMoveCrOSesToOrgUnit(request_id, response, exception):
    REASON_TO_MESSAGE_MAP = {GAPI_RESOURCE_NOT_FOUND: PHRASE_DOES_NOT_EXIST}
    ri = request_id.splitlines()
    if exception is None:
      entityItemValueActionPerformed(EN_ORGANIZATIONAL_UNIT, ri[RI_ENTITY], EN_CROS_DEVICE, ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
      entityItemValueActionFailedWarning(EN_ORGANIZATIONAL_UNIT, ri[RI_ENTITY], EN_CROS_DEVICE, ri[RI_ITEM], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _batchMoveCrOSesToOrgUnit(cd, orgUnitPath, i, count, CrOSList):
    setActionName(AC_ADD)
    jcount = len(CrOSList)
    entityPerformActionNumItems(EN_ORGANIZATIONAL_UNIT, orgUnitPath, jcount, EN_CROS_DEVICE, i, count)
    incrementIndentLevel()
    body = {u'orgUnitPath': orgUnitPath}
    bcount = 0
    bsize = GC_Values[GC_BATCH_SIZE]
    if bsize > 1:
      dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackMoveCrOSesToOrgUnit)
    j = 0
    for deviceId in CrOSList:
      j += 1
      if bsize > 1:
        parameters = dict([(u'customerId', GC_Values[GC_CUSTOMER_ID]), (u'deviceId', deviceId), (u'body', body)]+GM_Globals[GM_EXTRA_ARGS_LIST])
        dbatch.add(cd.chromeosdevices().patch(**parameters), request_id=batchRequestID(orgUnitPath, i, count, j, jcount, deviceId))
        bcount += 1
        if bcount == bsize:
          dbatch.execute()
          dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackMoveCrOSesToOrgUnit)
          bcount = 0
      else:
        try:
          callGAPI(cd.chromeosdevices(), u'patch',
                   throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN, GAPI_INVALID],
                   customerId=GC_Values[GC_CUSTOMER_ID], deviceId=deviceId, body=body)
          entityItemValueActionPerformed(EN_ORGANIZATIONAL_UNIT, orgUnitPath, EN_CROS_DEVICE, deviceId, j, jcount)
        except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
          checkEntityItemValueAFDNEorAccessErrorExit(cd, EN_ORGANIZATIONAL_UNIT, orgUnitPath, EN_CROS_DEVICE, deviceId, j, jcount)
        except GAPI_invalid as e:
          entityItemValueActionFailedWarning(EN_ORGANIZATIONAL_UNIT, orgUnitPath, EN_CROS_DEVICE, deviceId, e.message, j, jcount)
    if bcount > 0:
      dbatch.execute()
    decrementIndentLevel()

  def _callbackMoveUsersToOrgUnit(request_id, response, exception):
    REASON_TO_MESSAGE_MAP = {GAPI_USER_NOT_FOUND: PHRASE_DOES_NOT_EXIST}
    ri = request_id.splitlines()
    if exception is None:
      entityItemValueActionPerformed(EN_ORGANIZATIONAL_UNIT, ri[RI_ENTITY], EN_USER, ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
      entityItemValueActionFailedWarning(EN_ORGANIZATIONAL_UNIT, ri[RI_ENTITY], EN_USER, ri[RI_ITEM], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _batchMoveUsersToOrgUnit(cd, orgUnitPath, i, count, UserList):
    setActionName(AC_ADD)
    jcount = len(UserList)
    entityPerformActionNumItems(EN_ORGANIZATIONAL_UNIT, orgUnitPath, jcount, EN_USER, i, count)
    incrementIndentLevel()
    body = {u'orgUnitPath': orgUnitPath}
    bcount = 0
    bsize = GC_Values[GC_BATCH_SIZE]
    if bsize > 1:
      dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackMoveUsersToOrgUnit)
    j = 0
    for user in UserList:
      j += 1
      user = normalizeEmailAddressOrUID(user)
      if bsize > 1:
        parameters = dict([(u'userKey', user), (u'body', body)]+GM_Globals[GM_EXTRA_ARGS_LIST])
        dbatch.add(cd.users().patch(**parameters), request_id=batchRequestID(orgUnitPath, i, count, j, jcount, user))
        bcount += 1
        if bcount == bsize:
          dbatch.execute()
          dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackMoveUsersToOrgUnit)
          bcount = 0
      else:
        try:
          callGAPI(cd.users(), u'patch',
                   throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN, GAPI_INVALID],
                   userKey=user, body=body)
          entityItemValueActionPerformed(EN_ORGANIZATIONAL_UNIT, orgUnitPath, EN_USER, user, j, jcount)
        except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden):
          entityItemValueActionFailedWarning(EN_ORGANIZATIONAL_UNIT, orgUnitPath, EN_USER, user, PHRASE_SERVICE_NOT_APPLICABLE, j, jcount)
        except GAPI_invalid as e:
          entityItemValueActionFailedWarning(EN_ORGANIZATIONAL_UNIT, orgUnitPath, EN_USER, user, e.message, j, jcount)
    if bcount > 0:
      dbatch.execute()
    decrementIndentLevel()

  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  if checkArgumentPresent(MOVE_ADD_ARGUMENT):
    entityType, items = getEntityToModify(defaultEntityType=CL_ENTITY_USERS, crosAllowed=True)
    orgItemLists = items if isinstance(items, dict) else None
    checkForExtraneousArguments()
    setActionName(AC_ADD)
    i = 0
    count = len(entityList)
    for orgUnitPath in entityList:
      i += 1
      if orgItemLists:
        items = orgItemLists[orgUnitPath]
      orgUnitPath = checkOrgUnitPathExists(cd, orgUnitPath, i, count)
      if orgUnitPath:
        if entityType == CL_ENTITY_USERS:
          _batchMoveUsersToOrgUnit(cd, orgUnitPath, i, count, items)
        else:
          _batchMoveCrOSesToOrgUnit(cd, orgUnitPath, i, count, items)
  else:
    body = {}
    while CL_argvI < CL_argvLen:
      myarg = getArgument()
      if myarg == u'name':
        body[u'name'] = getString(OB_STRING)
      elif myarg == u'description':
        body[u'description'] = getString(OB_STRING)
      elif myarg == u'parent':
        parent = getOrgUnitPath()
        if parent.startswith(u'id:'):
          body[u'parentOrgUnitId'] = parent
        else:
          body[u'parentOrgUnitPath'] = parent
      elif myarg == u'noinherit':
        body[u'blockInheritance'] = True
      elif myarg == u'inherit':
        body[u'blockInheritance'] = False
      else:
        unknownArgumentExit()
    i = 0
    count = len(entityList)
    for orgUnitPath in entityList:
      i += 1
      try:
        callGAPI(cd.orgunits(), u'update',
                 throw_reasons=[GAPI_INVALID_ORGUNIT, GAPI_ORGUNIT_NOT_FOUND, GAPI_BACKEND_ERROR, GAPI_BAD_REQUEST, GAPI_INVALID_CUSTOMER_ID, GAPI_LOGIN_REQUIRED],
                 customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=makeOrgUnitPathRelative(orgUnitPath), body=body)
        entityActionPerformed(EN_ORGANIZATIONAL_UNIT, orgUnitPath, i, count)
      except (GAPI_invalidOrgunit, GAPI_orgunitNotFound, GAPI_backendError):
        entityActionFailedWarning(EN_ORGANIZATIONAL_UNIT, orgUnitPath, PHRASE_DOES_NOT_EXIST, i, count)
      except (GAPI_badRequest, GAPI_invalidCustomerId, GAPI_loginRequired):
        accessErrorExit(cd)

# gam delete orgs|ous <OrgUnitEntity>
def doDeleteOrgs():
  deleteOrgs(getEntityList(OB_ORGUNIT_ENTITY, shlexSplit=True))

# gam delete org|ou <OrgUnitPath>
def doDeleteOrg():
  deleteOrgs([getOrgUnitPath()])

def deleteOrgs(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for orgUnitPath in entityList:
    i += 1
    try:
      orgUnitPath = makeOrgUnitPathAbsolute(orgUnitPath)
      callGAPI(cd.orgunits(), u'delete',
               throw_reasons=[GAPI_CONDITION_NOT_MET, GAPI_INVALID_ORGUNIT, GAPI_ORGUNIT_NOT_FOUND, GAPI_BACKEND_ERROR, GAPI_BAD_REQUEST, GAPI_INVALID_CUSTOMER_ID, GAPI_LOGIN_REQUIRED],
               customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=makeOrgUnitPathRelative(orgUnitPath))
      entityActionPerformed(EN_ORGANIZATIONAL_UNIT, orgUnitPath, i, count)
    except GAPI_conditionNotMet:
      entityActionFailedWarning(EN_ORGANIZATIONAL_UNIT, orgUnitPath, PHRASE_HAS_CHILD_ORGS.format(pluralEntityName(EN_ORGANIZATIONAL_UNIT)), i, count)
    except (GAPI_invalidOrgunit, GAPI_orgunitNotFound, GAPI_backendError):
      entityActionFailedWarning(EN_ORGANIZATIONAL_UNIT, orgUnitPath, PHRASE_DOES_NOT_EXIST, i, count)
    except (GAPI_badRequest, GAPI_invalidCustomerId, GAPI_loginRequired):
      accessErrorExit(cd)

# gam info orgs|ous <OrgUnitEntity> [nousers] [children|child]
def doInfoOrgs():
  infoOrgs(getEntityList(OB_ORGUNIT_ENTITY, shlexSplit=True))

# gam info org|ou <OrgUnitPath> [nousers] [children|child]
def doInfoOrg():
  infoOrgs([getOrgUnitPath()])

def infoOrgs(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  get_users = True
  show_children = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'nousers':
      get_users = False
    elif myarg in [u'children', u'child']:
      show_children = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(entityList)
  for orgUnitPath in entityList:
    i += 1
    try:
      if orgUnitPath == u'/':
        orgs = callGAPI(cd.orgunits(), u'list',
                        throw_reasons=[GAPI_BAD_REQUEST, GAPI_INVALID_CUSTOMER_ID, GAPI_LOGIN_REQUIRED],
                        customerId=GC_Values[GC_CUSTOMER_ID], type=u'children',
                        fields=u'organizationUnits(parentOrgUnitId)')
        orgUnitPath = orgs[u'organizationUnits'][0][u'parentOrgUnitId']
      else:
        orgUnitPath = makeOrgUnitPathRelative(orgUnitPath)
      result = callGAPI(cd.orgunits(), u'get',
                        throw_reasons=[GAPI_INVALID_ORGUNIT, GAPI_ORGUNIT_NOT_FOUND, GAPI_BACKEND_ERROR, GAPI_BAD_REQUEST, GAPI_INVALID_CUSTOMER_ID, GAPI_LOGIN_REQUIRED],
                        customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=orgUnitPath)
      printEntityName(EN_ORGANIZATIONAL_UNIT, result[u'name'], i, count)
      incrementIndentLevel()
      for key, value in result.iteritems():
        if key in [u'kind', u'etag']:
          continue
        printKeyValueList([key, value])
      if get_users:
        orgUnitPath = result[u'orgUnitPath']
        setGettingEntityItem(EN_USER)
        page_message = getPageMessage(showFirstLastItems=True)
        users = callGAPIpages(cd.users(), u'list', u'users',
                              page_message=page_message, message_attribute=u'primaryEmail',
                              throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                              customer=GC_Values[GC_CUSTOMER_ID], query=orgUnitPathQuery(orgUnitPath),
                              fields=u'nextPageToken,users(primaryEmail,orgUnitPath)',
                              maxResults=GC_Values[GC_USER_MAX_RESULTS])
        printKeyValueList([pluralEntityName(EN_USER), u''])
        incrementIndentLevel()
        orgUnitPath = orgUnitPath.lower()
        for user in users:
          if orgUnitPath == user[u'orgUnitPath'].lower():
            printKeyValueList([user[u'primaryEmail']])
          elif show_children:
            printKeyValueList([u'{0} (child)'.format(user[u'primaryEmail'])])
        decrementIndentLevel()
      decrementIndentLevel()
    except (GAPI_invalidOrgunit, GAPI_orgunitNotFound, GAPI_backendError):
      entityActionFailedWarning(EN_ORGANIZATIONAL_UNIT, orgUnitPath, PHRASE_DOES_NOT_EXIST, i, count)
    except (GAPI_badRequest, GAPI_invalidCustomerId, GAPI_loginRequired, GAPI_resourceNotFound, GAPI_forbidden):
      accessErrorExit(cd)

# CL argument: [API field name, CSV field title]
#
ORG_ARGUMENT_TO_PROPERTY_TITLE_MAP = {
  u'description': [u'description', u'Description'],
  u'id': [u'orgUnitId', u'ID'],
  u'inherit': [u'blockInheritance', u'InheritanceBlocked'],
  u'orgunitpath': [u'orgUnitPath', u'Path'],
  u'path': [u'orgUnitPath', u'Path'],
  u'name': [u'name', u'Name'],
  u'parent': [u'parentOrgUnitPath', u'Parent'],
  u'parentid': [u'parentOrgUnitId', u'ParentID'],
  }
ORG_FIELD_PRINT_ORDER = [u'orgunitpath', u'id', u'name', u'description', u'parent', u'parentid', u'inherit']

# gam print orgs|ous [todrive] [from_parent <OrgUnitPath>] [toplevelonly] [allfields|<OrgUnitFieldName>*]
def doPrintOrgs():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  listType = u'all'
  orgUnitPath = u'/'
  todrive = False
  fieldsList = []
  fieldsTitles = {}
  titles, csvRows = initializeTitlesCSVfile(None)
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'toplevelonly':
      listType = u'children'
    elif myarg == u'fromparent':
      orgUnitPath = getOrgUnitPath()
    elif myarg == u'allfields':
      fieldsList = []
      fieldsTitles = {}
      titles, csvRows = initializeTitlesCSVfile(None)
      for field in ORG_FIELD_PRINT_ORDER:
        addFieldTitleToCSVfile(field, ORG_ARGUMENT_TO_PROPERTY_TITLE_MAP, fieldsList, fieldsTitles, titles)
    elif myarg in ORG_ARGUMENT_TO_PROPERTY_TITLE_MAP:
      addFieldTitleToCSVfile(myarg, ORG_ARGUMENT_TO_PROPERTY_TITLE_MAP, fieldsList, fieldsTitles, titles)
    else:
      unknownArgumentExit()
  if not fieldsList:
    addFieldTitleToCSVfile(u'orgunitpath', ORG_ARGUMENT_TO_PROPERTY_TITLE_MAP, fieldsList, fieldsTitles, titles)
  printGettingAccountEntitiesInfo(EN_ORGANIZATIONAL_UNIT)
  try:
    orgs = callGAPI(cd.orgunits(), u'list',
                    throw_reasons=[GAPI_ORGUNIT_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_INVALID_CUSTOMER_ID, GAPI_LOGIN_REQUIRED],
                    customerId=GC_Values[GC_CUSTOMER_ID], type=listType, orgUnitPath=orgUnitPath, fields=u'organizationUnits({0})'.format(u','.join(set(fieldsList))))
  except GAPI_orgunitNotFound:
    entityActionFailedWarning(EN_ORGANIZATIONAL_UNIT, orgUnitPath, PHRASE_DOES_NOT_EXIST)
    orgs = []
  except (GAPI_badRequest, GAPI_invalidCustomerId, GAPI_loginRequired):
    accessErrorExit(cd)
  if (not orgs) or (u'organizationUnits' not in orgs):
    printGettingAccountEntitiesDoneInfo(0)
    return
  printGettingAccountEntitiesDoneInfo(len(orgs[u'organizationUnits']))
  for orgEntity in orgs[u'organizationUnits']:
    orgUnit = {}
    for field in fieldsList:
      orgUnit[fieldsTitles[field]] = orgEntity.get(field, u'')
    csvRows.append(orgUnit)
  writeCSVfile(csvRows, titles, u'Orgs', todrive)

ALIAS_TARGET_TYPES = [u'user', u'group', u'target',]

# gam create aliases|nicknames <EmailAddressEntity> user|group|target <UniqueID>|<EmailAddress>
def doCreateAliases():
  createUpdateAliases(False, getEntityList(OB_EMAIL_ADDRESS_ENTITY))

# gam create alias|nickname <EmailAddress> user|group|target <UniqueID>|<EmailAddress>
def doCreateAlias():
  createUpdateAliases(False, getStringReturnInList(OB_EMAIL_ADDRESS))

# gam update aliases|nicknames <EmailAddressEntity> user|group|target <UniqueID>|<EmailAddress>
def doUpdateAliases():
  createUpdateAliases(True, getEntityList(OB_EMAIL_ADDRESS_ENTITY))

# gam update alias|nickname <EmailAddress> user|group|target <UniqueID>|<EmailAddress>
def doUpdateAlias():
  createUpdateAliases(True, getStringReturnInList(OB_EMAIL_ADDRESS))

def createUpdateAliases(doUpdate, aliasList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  targetType = getChoice(ALIAS_TARGET_TYPES)
  targetEmails = getEntityList(OB_GROUP_ENTITY, listOptional=True)
  entityLists = targetEmails if isinstance(targetEmails, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(aliasList)
  for aliasEmail in aliasList:
    i += 1
    if entityLists:
      targetEmails = entityLists[aliasEmail]
    aliasEmail = normalizeEmailAddressOrUID(aliasEmail, noUid=True)
    body = {u'alias': aliasEmail}
    jcount = len(targetEmails)
    if jcount > 0:
# Only process first target
      targetEmail = normalizeEmailAddressOrUID(targetEmails[0])
      if doUpdate:
        try:
          callGAPI(cd.users().aliases(), u'delete',
                   throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_INVALID, GAPI_FORBIDDEN],
                   userKey=aliasEmail, alias=aliasEmail)
          printEntityKVList(EN_USER_ALIAS, aliasEmail, [ACTION_NAMES[AC_DELETE][0]], i, count)
        except (GAPI_userNotFound, GAPI_badRequest, GAPI_invalid, GAPI_forbidden):
          try:
            callGAPI(cd.groups().aliases(), u'delete',
                     throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_INVALID, GAPI_FORBIDDEN],
                     groupKey=aliasEmail, alias=aliasEmail)
          except GAPI_forbidden:
            entityUnknownWarning(EN_GROUP_ALIAS, aliasEmail, i, count)
            continue
          except (GAPI_groupNotFound, GAPI_badRequest, GAPI_invalid):
            entityUnknownWarning(EN_ALIAS, aliasEmail, i, count)
      if targetType != u'group':
        try:
          callGAPI(cd.users().aliases(), u'insert',
                   throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_INVALID, GAPI_INVALID_INPUT, GAPI_FORBIDDEN, GAPI_DUPLICATE],
                   userKey=targetEmail, body=body)
          entityItemValueActionPerformed(EN_USER_ALIAS, aliasEmail, EN_USER, targetEmail, i, count)
          continue
        except GAPI_duplicate:
          entityItemValueActionFailedWarning(EN_USER_ALIAS, aliasEmail, EN_USER, targetEmail, PHRASE_DUPLICATE, i, count)
          continue
        except (GAPI_invalid, GAPI_invalidInput):
          entityItemValueActionFailedWarning(EN_USER_ALIAS, aliasEmail, EN_USER, targetEmail, PHRASE_INVALID_ALIAS, i, count)
          continue
        except (GAPI_userNotFound, GAPI_badRequest, GAPI_forbidden):
          if targetType == u'user':
            entityUnknownWarning(EN_ALIAS_TARGET, targetEmail, i, count)
            continue
      try:
        callGAPI(cd.groups().aliases(), u'insert',
                 throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_USER_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_INVALID, GAPI_INVALID_INPUT, GAPI_FORBIDDEN, GAPI_DUPLICATE],
                 groupKey=targetEmail, body=body)
        entityItemValueActionPerformed(EN_GROUP_ALIAS, aliasEmail, EN_GROUP, targetEmail, i, count)
      except GAPI_duplicate:
        entityItemValueActionFailedWarning(EN_GROUP_ALIAS, aliasEmail, EN_GROUP, targetEmail, PHRASE_DUPLICATE, i, count)
      except (GAPI_invalid, GAPI_invalidInput):
        entityItemValueActionFailedWarning(EN_GROUP_ALIAS, aliasEmail, EN_GROUP, targetEmail, PHRASE_INVALID_ALIAS, i, count)
      except (GAPI_groupNotFound, GAPI_userNotFound, GAPI_badRequest, GAPI_forbidden):
        entityUnknownWarning(EN_ALIAS_TARGET, targetEmail, i, count)

# gam delete aliases|nicknames [user|group|target] <EmailAddressEntity>
def doDeleteAliases():
  targetType = getChoice(ALIAS_TARGET_TYPES, defaultChoice=u'target')
  entityList = getEntityList(OB_EMAIL_ADDRESS_ENTITY)
  checkForExtraneousArguments()
  deleteAliases(targetType, entityList)

# gam delete alias|nickname [user|group|target] <UniqueID>|<EmailAddress>
def doDeleteAlias():
  targetType = getChoice(ALIAS_TARGET_TYPES, defaultChoice=u'target')
  entityList = getStringReturnInList(OB_EMAIL_ADDRESS)
  checkForExtraneousArguments()
  deleteAliases(targetType, entityList)

def deleteAliases(targetType, entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  i = 0
  count = len(entityList)
  for aliasEmail in entityList:
    i += 1
    aliasEmail = normalizeEmailAddressOrUID(aliasEmail, noUid=True)
    if targetType != u'group':
      try:
        callGAPI(cd.users().aliases(), u'delete',
                 throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_INVALID, GAPI_FORBIDDEN],
                 userKey=aliasEmail, alias=aliasEmail)
        entityActionPerformed(EN_USER_ALIAS, aliasEmail, i, count)
        continue
      except (GAPI_userNotFound, GAPI_badRequest, GAPI_invalid, GAPI_forbidden):
        if targetType == u'user':
          entityUnknownWarning(EN_USER_ALIAS, aliasEmail, i, count)
          continue
    try:
      callGAPI(cd.groups().aliases(), u'delete',
               throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_USER_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_INVALID, GAPI_FORBIDDEN],
               groupKey=aliasEmail, alias=aliasEmail)
      entityActionPerformed(EN_GROUP_ALIAS, aliasEmail, i, count)
      continue
    except (GAPI_groupNotFound, GAPI_userNotFound, GAPI_badRequest, GAPI_invalid, GAPI_forbidden):
      if targetType == u'group':
        entityUnknownWarning(EN_GROUP_ALIAS, aliasEmail, i, count)
        continue
    entityUnknownWarning(EN_ALIAS, aliasEmail, i, count)

# gam info aliases|nicknames <EmailAddressEntity>
def doInfoAliases():
  infoAliases(getEntityList(OB_EMAIL_ADDRESS_ENTITY))

# gam info alias|nickname <EmailAddress>
def doInfoAlias():
  infoAliases(getStringReturnInList(OB_EMAIL_ADDRESS))

def infoAliases(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
# Ignore info group/user arguments that may have come from whatis
    if (myarg in INFO_GROUP_OPTIONS) or (myarg in INFO_USER_OPTIONS):
      if myarg == u'schemas':
        getString(OB_SCHEMA_NAME_LIST)
    else:
      unknownArgumentExit()
  i = 0
  count = len(entityList)
  for aliasEmail in entityList:
    i += 1
    aliasEmail = normalizeEmailAddressOrUID(aliasEmail, noUid=True)
    try:
      result = callGAPI(cd.users(), u'get',
                        throw_reasons=GAPI_USER_GET_THROW_REASONS,
                        userKey=aliasEmail)
      if result[u'primaryEmail'].lower() != aliasEmail:
        printEntityName(EN_ALIAS_EMAIL, aliasEmail, i, count)
        incrementIndentLevel()
        printEntityName(EN_USER_EMAIL, result[u'primaryEmail'])
        printEntityName(EN_UNIQUE_ID, result[u'id'])
        decrementIndentLevel()
      else:
        setSysExitRC(ENTITY_IS_NOT_AN_ALIAS_RC)
        printEntityKVList(EN_ALIAS_EMAIL, aliasEmail,
                          [u'Is a {0} primary email address, not a {1}'.format(singularEntityName(EN_USER),
                                                                               singularEntityName(EN_USER_ALIAS))],
                          i, count)
      continue
    except (GAPI_domainNotFound, GAPI_forbidden, GAPI_backendError, GAPI_systemError):
      entityUnknownWarning(EN_USER_ALIAS, aliasEmail, i, count)
      continue
    except (GAPI_userNotFound, GAPI_invalid, GAPI_badRequest):
      pass
    try:
      result = callGAPI(cd.groups(), u'get',
                        throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_INVALID, GAPI_BAD_REQUEST, GAPI_FORBIDDEN],
                        groupKey=aliasEmail)
      if result[u'email'].lower() != aliasEmail:
        printEntityName(EN_ALIAS_EMAIL, aliasEmail, i, count)
        incrementIndentLevel()
        printEntityName(EN_GROUP_EMAIL, result[u'email'])
        printEntityName(EN_UNIQUE_ID, result[u'id'])
        decrementIndentLevel()
      else:
        setSysExitRC(ENTITY_IS_NOT_AN_ALIAS_RC)
        printEntityKVList(EN_ALIAS_EMAIL, aliasEmail,
                          [u'Is a {0} email address, not a {1}'.format(singularEntityName(EN_GROUP),
                                                                       singularEntityName(EN_GROUP_ALIAS))],
                          i, count)
      continue
    except GAPI_forbidden:
      entityUnknownWarning(EN_GROUP_ALIAS, aliasEmail, i, count)
      continue
    except (GAPI_groupNotFound, GAPI_invalid, GAPI_badRequest):
      pass
    entityUnknownWarning(EN_ALIAS_EMAIL, aliasEmail, i, count)

# gam print aliases|nicknames [todrive]
def doPrintAliases():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'Alias', u'Target', u'TargetType'])
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    else:
      unknownArgumentExit()
  printGettingAccountEntitiesInfo(EN_USER_ALIAS)
  page_message = getPageMessage(showTotal=False, showFirstLastItems=True)
  try:
    entityList = callGAPIpages(cd.users(), u'list', u'users',
                               page_message=page_message, message_attribute=u'primaryEmail',
                               throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                               customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,aliases)', maxResults=GC_Values[GC_USER_MAX_RESULTS])
    for user in entityList:
      for alias in user.get(u'aliases', []):
        csvRows.append({u'Alias': alias, u'Target': user[u'primaryEmail'], u'TargetType': u'User'})
  except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
    accessErrorExit(cd)
  printGettingAccountEntitiesInfo(EN_GROUP_ALIAS)
  page_message = getPageMessage(showTotal=False, showFirstLastItems=True)
  try:
    entityList = callGAPIpages(cd.groups(), u'list', u'groups',
                               page_message=page_message, message_attribute=u'email',
                               throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                               customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,groups(email,aliases)')
    for group in entityList:
      for alias in group.get(u'aliases', []):
        csvRows.append({u'Alias': alias, u'Target': group[u'email'], u'TargetType': u'Group'})
  except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
    accessErrorExit(cd)
  writeCSVfile(csvRows, titles, u'Aliases', todrive)

# gam audit uploadkey <ValueReadFromStdin>
def doUploadAuditKey():
  auditObject = getAuditObject()
  checkForExtraneousArguments()
  auditkey = sys.stdin.read()
  callGData(auditObject, u'updatePGPKey',
            pgpkey=auditkey)

# Utiities for audit/export commands
def checkDownloadResults(results):
  if results[u'status'] != u'COMPLETED':
    printWarningMessage(REQUEST_NOT_COMPLETED_RC, MESSAGE_REQUEST_NOT_COMPLETE.format(results[u'status']))
    return False
  if int(results.get(u'numberOfFiles', u'0') >= 1):
    return True
  printWarningMessage(REQUEST_COMPLETED_NO_RESULTS_RC, MESSAGE_REQUEST_COMPLETED_NO_FILES)
  return False

# Utilities for audit command
def getAuditParameters(emailAddressRequired=True, requestIdRequired=True, destUserRequired=False):
  auditObject = getAuditObject()
  emailAddress = getEmailAddress(noUid=True, optional=not emailAddressRequired)
  parameters = {}
  if emailAddress:
    parameters[u'auditUser'] = emailAddress
    parameters[u'auditUserName'], auditObject.domain = splitEmailAddress(emailAddress)
    if requestIdRequired:
      parameters[u'requestId'] = getString(OB_REQUEST_ID)
    if destUserRequired:
      destEmailAddress = getEmailAddress(noUid=True)
      parameters[u'auditDestUser'] = destEmailAddress
      parameters[u'auditDestUserName'], destDomain = splitEmailAddress(destEmailAddress)
      if auditObject.domain != destDomain:
        putArgumentBack()
        invalidArgumentExit(u'{0}@{1}'.format(parameters[u'auditDestUserName'], auditObject.domain))
  return (auditObject, parameters)

def _showFileURLs(request):
  if u'numberOfFiles' in request:
    printKeyValueList([u'Number Of Files', request[u'numberOfFiles']])
    incrementIndentLevel()
    for i in range(int(request[u'numberOfFiles'])):
      printKeyValueList([u'Url{0}'.format(i), request[u'fileUrl'+str(i)]])
    decrementIndentLevel()

def _showMailboxActivityRequestStatus(request, i, count, showFiles=False):
  printEntityName(EN_REQUEST_ID, request[u'requestId'], i, count)
  incrementIndentLevel()
  printKeyValueList([singularEntityName(EN_USER), request[u'userEmailAddress']])
  printKeyValueList([u'Status', request[u'status']])
  printKeyValueList([u'Request Date', request[u'requestDate']])
  printKeyValueList([u'Requested By', request[u'adminEmailAddress']])
  if showFiles:
    _showFileURLs(request)
  decrementIndentLevel()

# gam audit activity request <EmailAddress>
def doSubmitActivityRequest():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=False, destUserRequired=False)
  checkForExtraneousArguments()
  try:
    request = callGData(auditObject, u'createAccountInformationRequest',
                        throw_errors=[GDATA_INVALID_DOMAIN, GDATA_DOES_NOT_EXIST],
                        user=parameters[u'auditUserName'])
    entityItemValueActionPerformed(EN_USER, parameters[u'auditUser'], EN_AUDIT_ACTIVITY_REQUEST, None)
    incrementIndentLevel()
    _showMailboxActivityRequestStatus(request, 0, 0, showFiles=False)
    decrementIndentLevel()
  except (GData_invalidDomain, GData_doesNotExist):
    entityUnknownWarning(EN_USER, parameters[u'auditUser'])

# gam audit activity delete <EmailAddress> <RequestID>
def doDeleteActivityRequest():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=True, destUserRequired=False)
  checkForExtraneousArguments()
  try:
    callGData(auditObject, u'deleteAccountInformationRequest',
              throw_errors=[GDATA_INVALID_DOMAIN, GDATA_DOES_NOT_EXIST, GDATA_INVALID_VALUE],
              user=parameters[u'auditUserName'], request_id=parameters[u'requestId'])
    entityItemValueActionPerformed(EN_USER, parameters[u'auditUser'], EN_AUDIT_ACTIVITY_REQUEST, parameters[u'requestId'])
  except (GData_invalidDomain, GData_doesNotExist):
    entityUnknownWarning(EN_USER, parameters[u'auditUser'])
  except GData_invalidValue:
    entityItemValueActionFailedWarning(EN_USER, parameters[u'auditUser'], EN_AUDIT_ACTIVITY_REQUEST, parameters[u'requestId'], PHRASE_INVALID_REQUEST)

# gam audit activity download <EmailAddress> <RequestID>
def doDownloadActivityRequest():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=True, destUserRequired=False)
  checkForExtraneousArguments()
  try:
    results = callGData(auditObject, u'getAccountInformationRequestStatus',
                        throw_errors=[GDATA_INVALID_DOMAIN, GDATA_DOES_NOT_EXIST, GDATA_INVALID_VALUE],
                        user=parameters[u'auditUserName'], request_id=parameters[u'requestId'])
    if not checkDownloadResults(results):
      return
    count = int(results[u'numberOfFiles'])
    for i in range(count):
      url = results[u'fileUrl'+str(i)]
      filename = u'activity-{0}-{1}-{2}.txt.gpg'.format(parameters[u'auditUserName'], parameters[u'requestId'], i)
      entityPerformActionItemValueInfo(EN_USER, parameters[u'auditUser'], EN_AUDIT_ACTIVITY_REQUEST, parameters[u'requestId'], filename, i+1, count)
      geturl(url, filename)
  except (GData_invalidDomain, GData_doesNotExist):
    entityUnknownWarning(EN_USER, parameters[u'auditUser'])
  except GData_invalidValue:
    entityItemValueActionFailedWarning(EN_USER, parameters[u'auditUser'], EN_AUDIT_ACTIVITY_REQUEST, parameters[u'requestId'], PHRASE_INVALID_REQUEST)

# gam audit activity status [<EmailAddress> <RequestID>]
def doStatusActivityRequests():
  auditObject, parameters = getAuditParameters(emailAddressRequired=False, requestIdRequired=True, destUserRequired=False)
  checkForExtraneousArguments()
  if parameters:
    try:
      results = [callGData(auditObject, u'getAccountInformationRequestStatus',
                           throw_errors=[GDATA_INVALID_DOMAIN, GDATA_DOES_NOT_EXIST, GDATA_INVALID_VALUE],
                           user=parameters[u'auditUserName'], request_id=parameters[u'requestId'])]
      jcount = 1 if (results) else 0
      entityPerformActionNumItems(EN_USER, parameters[u'auditUser'], jcount, EN_AUDIT_ACTIVITY_REQUEST)
    except (GData_invalidDomain, GData_doesNotExist):
      entityUnknownWarning(EN_USER, parameters[u'auditUser'])
      return
    except GData_invalidValue:
      entityItemValueActionFailedWarning(EN_USER, parameters[u'auditUser'], EN_AUDIT_ACTIVITY_REQUEST, parameters[u'requestId'], PHRASE_INVALID_REQUEST)
      return
  else:
    results = callGData(auditObject, u'getAllAccountInformationRequestsStatus')
    jcount = len(results) if (results) else 0
    entityPerformActionNumItems(EN_DOMAIN, GC_Values[GC_DOMAIN], jcount, EN_AUDIT_ACTIVITY_REQUEST)
  if jcount == 0:
    setSysExitRC(NO_ENTITIES_FOUND)
    return
  incrementIndentLevel()
  j = 0
  for request in results:
    j += 1
    _showMailboxActivityRequestStatus(request, j, jcount, showFiles=True)
  decrementIndentLevel()

# Utilities for audit export command
def _showMailboxExportRequestStatus(request, i, count, showFilter=False, showDates=False, showFiles=False):
  printEntityName(EN_REQUEST_ID, request[u'requestId'], i, count)
  incrementIndentLevel()
  printKeyValueList([singularEntityName(EN_USER), request[u'userEmailAddress']])
  printKeyValueList([u'Status', request[u'status']])
  printKeyValueList([u'Request Date', request[u'requestDate']])
  printKeyValueList([u'Requested By', request[u'adminEmailAddress']])
  printKeyValueList([u'Requested Parts', request[u'packageContent']])
  if showFilter:
    printKeyValueList([u'Request Filter', request.get(u'searchQuery', u'None')])
  printKeyValueList([u'Include Deleted', request[u'includeDeleted']])
  if showDates:
    printKeyValueList([u'Begin', request.get(u'beginDate', u'Account creation date')])
    printKeyValueList([u'End', request.get(u'endDate', u'Export request date')])
  if showFiles:
    _showFileURLs(request)
  decrementIndentLevel()

# gam audit export request <EmailAddress> [begin <DateTime>] [end <DateTime>] [search <QueryGmail>] [headersonly] [includedeleted]
def doSubmitExportRequest():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=False, destUserRequired=False)
  begin_date = end_date = search_query = None
  headers_only = include_deleted = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'begin':
      begin_date = getYYYYMMDD_HHMM()
    elif myarg == u'end':
      end_date = getYYYYMMDD_HHMM()
    elif myarg == u'search':
      search_query = getString(OB_QUERY)
    elif myarg == u'headersonly':
      headers_only = True
    elif myarg == u'includedeleted':
      include_deleted = True
    else:
      unknownArgumentExit()
  try:
    request = callGData(auditObject, u'createMailboxExportRequest',
                        throw_errors=[GDATA_INVALID_DOMAIN, GDATA_DOES_NOT_EXIST],
                        user=parameters[u'auditUserName'], begin_date=begin_date, end_date=end_date, include_deleted=include_deleted,
                        search_query=search_query, headers_only=headers_only)
    entityItemValueActionPerformed(EN_USER, parameters[u'auditUser'], EN_AUDIT_EXPORT_REQUEST, None)
    incrementIndentLevel()
    _showMailboxExportRequestStatus(request, 0, 0, showFilter=False, showDates=True, showFiles=False)
    decrementIndentLevel()
  except (GData_invalidDomain, GData_doesNotExist):
    entityUnknownWarning(EN_USER, parameters[u'auditUser'])

# gam audit export delete <EmailAddress> <RequestID>
def doDeleteExportRequest():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=True, destUserRequired=False)
  checkForExtraneousArguments()
  try:
    callGData(auditObject, u'deleteMailboxExportRequest',
              throw_errors=[GDATA_INVALID_DOMAIN, GDATA_DOES_NOT_EXIST, GDATA_INVALID_VALUE],
              user=parameters[u'auditUserName'], request_id=parameters[u'requestId'])
    entityItemValueActionPerformed(EN_USER, parameters[u'auditUser'], EN_AUDIT_EXPORT_REQUEST, parameters[u'requestId'])
  except (GData_invalidDomain, GData_doesNotExist):
    entityUnknownWarning(EN_USER, parameters[u'auditUser'])
  except GData_invalidValue:
    entityItemValueActionFailedWarning(EN_USER, parameters[u'auditUser'], EN_AUDIT_EXPORT_REQUEST, parameters[u'requestId'], PHRASE_INVALID_REQUEST)

# gam audit export download <EmailAddress> <RequestID>
def doDownloadExportRequest():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=True, destUserRequired=False)
  checkForExtraneousArguments()
  try:
    results = callGData(auditObject, u'getMailboxExportRequestStatus',
                        throw_errors=[GDATA_INVALID_DOMAIN, GDATA_DOES_NOT_EXIST, GDATA_INVALID_VALUE],
                        user=parameters[u'auditUserName'], request_id=parameters[u'requestId'])
    if not checkDownloadResults(results):
      return
    count = int(results[u'numberOfFiles'])
    for i in range(count):
      url = results[u'fileUrl'+str(i)]
      filename = u'export-{0}-{1}-{2}.mbox.gpg'.format(parameters[u'auditUserName'], parameters[u'requestId'], i)
      #don't download existing files. This does not check validity of existing local
      #file so partial/corrupt downloads will need to be deleted manually.
      if not os.path.isfile(filename):
        entityPerformActionItemValueInfo(EN_USER, parameters[u'auditUser'], EN_AUDIT_EXPORT_REQUEST, parameters[u'requestId'], filename, i+1, count)
        geturl(url, filename)
  except (GData_invalidDomain, GData_doesNotExist):
    entityUnknownWarning(EN_USER, parameters[u'auditUser'])
  except GData_invalidValue:
    entityItemValueActionFailedWarning(EN_USER, parameters[u'auditUser'], EN_AUDIT_EXPORT_REQUEST, parameters[u'requestId'], PHRASE_INVALID_REQUEST)

# gam audit export status [<EmailAddress> <RequestID>]
def doStatusExportRequests():
  auditObject, parameters = getAuditParameters(emailAddressRequired=False, requestIdRequired=True, destUserRequired=False)
  checkForExtraneousArguments()
  if parameters:
    try:
      results = [callGData(auditObject, u'getMailboxExportRequestStatus',
                           throw_errors=[GDATA_INVALID_DOMAIN, GDATA_DOES_NOT_EXIST, GDATA_INVALID_VALUE],
                           user=parameters[u'auditUserName'], request_id=parameters[u'requestId'])]
      jcount = 1 if (results) else 0
      entityPerformActionNumItems(EN_USER, parameters[u'auditUser'], jcount, EN_AUDIT_EXPORT_REQUEST)
    except (GData_invalidDomain, GData_doesNotExist):
      entityUnknownWarning(EN_USER, parameters[u'auditUser'])
      return
    except GData_invalidValue:
      entityItemValueActionFailedWarning(EN_USER, parameters[u'auditUser'], EN_AUDIT_EXPORT_REQUEST, parameters[u'requestId'], PHRASE_INVALID_REQUEST)
      return
  else:
    results = callGData(auditObject, u'getAllMailboxExportRequestsStatus')
    jcount = len(results) if (results) else 0
    entityPerformActionNumItems(EN_DOMAIN, GC_Values[GC_DOMAIN], jcount, EN_AUDIT_EXPORT_REQUEST)
  if jcount == 0:
    setSysExitRC(NO_ENTITIES_FOUND)
    return
  incrementIndentLevel()
  j = 0
  for request in results:
    j += 1
    _showMailboxExportRequestStatus(request, j, jcount, showFilter=True, showDates=False, showFiles=True)
  decrementIndentLevel()

# gam audit export watch <EmailAddress> <RequestID>
def doWatchExportRequest():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=True, destUserRequired=False)
  checkForExtraneousArguments()
  while True:
    try:
      results = callGData(auditObject, u'getMailboxExportRequestStatus',
                          throw_errors=[GDATA_INVALID_DOMAIN, GDATA_DOES_NOT_EXIST, GDATA_INVALID_VALUE],
                          user=parameters[u'auditUserName'], request_id=parameters[u'requestId'])
    except (GData_invalidDomain, GData_doesNotExist):
      entityUnknownWarning(EN_USER, parameters[u'auditUser'])
      break
    except GData_invalidValue:
      entityItemValueActionFailedWarning(EN_USER, parameters[u'auditUser'], EN_AUDIT_EXPORT_REQUEST, parameters[u'requestId'], PHRASE_INVALID_REQUEST)
      break
    if results[u'status'] != u'PENDING':
      printKeyValueList([u'Status is', results[u'status'], u'Sending email.'])
      msg_txt = u'\n'
      msg_txt += u'  {0}: {1}\n'.format(singularEntityName(EN_REQUEST_ID), results[u'requestId'])
      msg_txt += u'  {0}: {1}\n'.format(singularEntityName(EN_USER), results[u'userEmailAddress'])
      msg_txt += u'  Status: {0}\n'.format(results[u'status'])
      msg_txt += u'  Request Date: {0}\n'.format(results[u'requestDate'])
      msg_txt += u'  Requested By: {0}\n'.format(results[u'adminEmailAddress'])
      msg_txt += u'  Requested Parts: {0}\n'.format(results[u'packageContent'])
      msg_txt += u'  Request Filter: {0}\n'.format(results.get(u'searchQuery', u'None'))
      msg_txt += u'  Include Deleted: {0}\n'.format(results[u'includeDeleted'])
      if u'numberOfFiles' in results:
        msg_txt += u'  Number Of Files: {0}\n'.format(results[u'numberOfFiles'])
        for i in range(int(results[u'numberOfFiles'])):
          msg_txt += u'  Url{0}: {1}\n'.format(i, results[u'fileUrl'+str(i)])
      msg_subj = u'Export #{0} for {1} status is {2}'.format(results[u'requestId'], results[u'userEmailAddress'], results[u'status'])
      send_email(msg_subj, msg_txt)
      break
    else:
      printKeyValueList([u'Status still PENDING, will check again in 5 minutes...'])
      time.sleep(300)

# Utilities for audit monitor command
def _showMailboxMonitorRequestStatus(request, i=0, count=0):
  printKeyValueListWithCount([u'Destination', normalizeEmailAddressOrUID(request[u'destUserName'])], i, count)
  incrementIndentLevel()
  printKeyValueList([u'Begin', request.get(u'beginDate', u'immediately')])
  printKeyValueList([u'End', request[u'endDate']])
  printKeyValueList([u'Monitor Incoming', request[u'outgoingEmailMonitorLevel']])
  printKeyValueList([u'Monitor Outgoing', request[u'incomingEmailMonitorLevel']])
  printKeyValueList([u'Monitor Chats', request[u'chatMonitorLevel']])
  printKeyValueList([u'Monitor Drafts', request[u'draftMonitorLevel']])
  decrementIndentLevel()

# gam audit monitor create <EmailAddress> <DestEmailAddress> [begin <DateTime>] [end <DateTime>] [incoming_headers] [outgoing_headers] [nochats] [nodrafts] [chat_headers] [draft_headers]
def doCreateMonitor():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=False, destUserRequired=True)
  #end_date defaults to 30 days in the future...
  end_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime(u'%Y-%m-%d %H:%M')
  begin_date = None
  incoming_headers_only = outgoing_headers_only = drafts_headers_only = chats_headers_only = False
  drafts = chats = True
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'begin':
      begin_date = getYYYYMMDD_HHMM()
    elif myarg == u'end':
      end_date = getYYYYMMDD_HHMM()
    elif myarg == u'incomingheaders':
      incoming_headers_only = True
    elif myarg == u'outgoingheaders':
      outgoing_headers_only = True
    elif myarg == u'nochats':
      chats = False
    elif myarg == u'nodrafts':
      drafts = False
    elif myarg == u'chatheaders':
      chats_headers_only = True
    elif myarg == u'draftheaders':
      drafts_headers_only = True
    else:
      unknownArgumentExit()
  try:
    request = callGData(auditObject, u'createEmailMonitor',
                        throw_errors=[GDATA_INVALID_VALUE, GDATA_INVALID_DOMAIN, GDATA_DOES_NOT_EXIST],
                        source_user=parameters[u'auditUserName'], destination_user=parameters[u'auditDestUserName'], end_date=end_date, begin_date=begin_date,
                        incoming_headers_only=incoming_headers_only, outgoing_headers_only=outgoing_headers_only,
                        drafts=drafts, drafts_headers_only=drafts_headers_only, chats=chats, chats_headers_only=chats_headers_only)
    entityItemValueActionPerformed(EN_USER, parameters[u'auditUser'], EN_AUDIT_MONITOR_REQUEST, None)
    incrementIndentLevel()
    _showMailboxMonitorRequestStatus(request)
    decrementIndentLevel()
  except GData_invalidValue as e:
    entityItemValueActionFailedWarning(EN_USER, parameters[u'auditUser'], EN_AUDIT_MONITOR_REQUEST, None, e.message)
  except (GData_invalidDomain, GData_doesNotExist):
    entityUnknownWarning(EN_USER, parameters[u'auditUser'])

# gam audit monitor delete <EmailAddress> <DestEmailAddress>
def doDeleteMonitor():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=False, destUserRequired=True)
  checkForExtraneousArguments()
  try:
    callGData(auditObject, u'deleteEmailMonitor',
              throw_errors=[GDATA_INVALID_DOMAIN, GDATA_DOES_NOT_EXIST],
              source_user=parameters[u'auditUserName'], destination_user=parameters[u'auditDestUserName'])
    entityItemValueActionPerformed(EN_USER, parameters[u'auditUser'], EN_AUDIT_MONITOR_REQUEST, parameters[u'auditDestUser'])
  except (GData_invalidDomain, GData_doesNotExist):
    entityUnknownWarning(EN_USER, parameters[u'auditUser'])

# gam audit monitor list <EmailAddress>
def doShowMonitors():
  auditObject, parameters = getAuditParameters(emailAddressRequired=True, requestIdRequired=False, destUserRequired=False)
  checkForExtraneousArguments()
  try:
    results = callGData(auditObject, u'getEmailMonitors',
                        throw_errors=[GDATA_INVALID_DOMAIN, GDATA_DOES_NOT_EXIST],
                        user=parameters[u'auditUserName'])
    jcount = len(results) if (results) else 0
    entityPerformActionNumItems(EN_USER, parameters[u'auditUser'], jcount, EN_AUDIT_MONITOR_REQUEST)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      return
    incrementIndentLevel()
    j = 0
    for request in results:
      j += 1
      _showMailboxMonitorRequestStatus(request, j, jcount)
    decrementIndentLevel()
  except (GData_invalidDomain, GData_doesNotExist):
    entityUnknownWarning(EN_USER, parameters[u'auditUser'])

# Utilities for calendar command
def checkCalendarExists(cal, calendarId):
  try:
    callGAPI(cal.calendars(), u'get',
             throw_reasons=[GAPI_NOT_FOUND],
             calendarId=calendarId)
    return True
  except GAPI_notFound:
    return None

ACL_SCOPE_CHOICES = [u'default', u'user', u'group', u'domain',]

def getACLScope():
  scopeType = getChoice(ACL_SCOPE_CHOICES, defaultChoice=u'user')
  if scopeType == u'domain':
    entity = getString(OB_DOMAIN_NAME, optional=True)
    if entity:
      scopeValue = entity.lower()
    else:
      scopeValue = GC_Values[GC_DOMAIN]
  elif scopeType != u'default':
    scopeValue = getEmailAddress(noUid=True)
  else:
    scopeValue = None
  return (scopeType, scopeValue)

def getACLRuleId():
  scopeType, scopeValue = getACLScope()
  if scopeType != u'default':
    ruleId = u'{0}:{1}'.format(scopeType, scopeValue)
  else:
    ruleId = scopeType
  return ruleId

def formatACLScopeRole(scope, role):
  if role:
    return formatKeyValueList(u'(', [u'Scope', scope, u'Role', role], u')')
  else:
    return formatKeyValueList(u'(', [u'Scope', scope], u')')

def formatACLRule(rule):
  if rule[u'scope'][u'type'] != u'default':
    return formatKeyValueList(u'(', [u'Scope', u'{0}:{1}'.format(rule[u'scope'][u'type'], rule[u'scope'][u'value']), u'Role', rule[u'role']], u')')
  else:
    return formatKeyValueList(u'(', [u'Scope', u'{0}'.format(rule[u'scope'][u'type']), u'Role', rule[u'role']], u')')

def convertRuleId(role, ruleId):
  ruleIdParts = ruleId.split(u':')
  if len(ruleIdParts) == 1:
    if ruleIdParts[0] == u'default':
      return {u'role': role, u'scope': {u'type': ruleIdParts[0]}}
    if ruleIdParts[0] == u'domain':
      return {u'role': role, u'scope': {u'type': ruleIdParts[0], u'value': GC_Values[GC_DOMAIN]}}
    return {u'role': role, u'scope': {u'type': u'user', u'value': ruleIdParts[0]}}
  return {u'role': role, u'scope': {u'type': ruleIdParts[0], u'value': ruleIdParts[1]}}

def normalizeRuleId(ruleId):
  ruleIdParts = ruleId.split(u':')
  if (len(ruleIdParts) == 1) or (len(ruleIdParts[1]) == 0):
    if ruleIdParts[0] == u'default':
      return ruleId
    if ruleIdParts[0] == u'domain':
      return u'{0}:{1}'.format(u'domain', GC_Values[GC_DOMAIN])
    return u'{0}:{1}'.format(u'user', normalizeEmailAddressOrUID(ruleIdParts[0], noUid=True))
  if ruleIdParts[0] in [u'user', u'group']:
    return u'{0}:{1}'.format(ruleIdParts[0], normalizeEmailAddressOrUID(ruleIdParts[1], noUid=True))
  return ruleId

CALENDAR_ACL_ROLES_MAP = {
  u'editor': u'writer',
  u'freebusy': u'freeBusyReader',
  u'freebusyreader': u'freeBusyReader',
  u'owner': u'owner',
  u'read': u'reader',
  u'reader': u'reader',
  u'writer': u'writer',
  u'none': u'none',
  }

def _processCalendarAddACL(calendarId, i, count, j, jcount, cal, body):
  result = True
  try:
    callGAPI(cal.acl(), u'insert',
             throw_reasons=[GAPI_NOT_FOUND, GAPI_INVALID_SCOPE_VALUE, GAPI_CANNOT_CHANGE_OWNER_ACL],
             calendarId=calendarId, body=body)
    entityItemValueActionPerformed(EN_CALENDAR, calendarId, EN_ACL, formatACLRule(body), j, jcount)
  except GAPI_notFound:
    if not checkCalendarExists(cal, calendarId):
      entityUnknownWarning(EN_CALENDAR, calendarId, i, count)
      result = False
    else:
      entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_ACL, formatACLRule(body), PHRASE_DOES_NOT_EXIST, j, jcount)
  except GAPI_invalidScopeValue:
    entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_ACL, formatACLRule(body), PHRASE_INVALID_SCOPE, j, jcount)
  except GAPI_cannotChangeOwnerAcl:
    entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_ACL, formatACLRule(body), PHRASE_CAN_NOT_CHANGE_OWNER_ACL, j, jcount)
  return result

# gam calendars <CalendarEntity> add acl <CalendarACLRole> ([user] <EmailAddress>)|(group <EmailAddress>)|(domain [<DomainName>])|default
# gam calendar <CalendarItem> add <CalendarACLRole> ([user] <EmailAddress>)|(group <EmailAddress>)|(domain [<DomainName>])|default
def doCalendarAddACL(cal, calendarList):
  role = getChoice(CALENDAR_ACL_ROLES_MAP, mapChoice=True)
  scopeType, scopeValue = getACLScope()
  body = {u'role': role, u'scope': {u'type': scopeType}}
  if scopeType != u'default':
    body[u'scope'][u'value'] = scopeValue
  checkForExtraneousArguments()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    calendarId = convertUserUIDtoEmailAddress(calendarId)
    _processCalendarAddACL(calendarId, i, count, i, count, cal, body)

# gam calendars <CalendarEntity> add acls <CalendarACLRole> <ACLEntity>
def doCalendarAddACLs(cal, calendarList):
  role = getChoice(CALENDAR_ACL_ROLES_MAP, mapChoice=True)
  ruleIds = getEntityList(OB_ACL_ENTITY)
  ruleIdLists = ruleIds if isinstance(ruleIds, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    if ruleIdLists:
      ruleIds = ruleIdLists[calendarId]
    calendarId = convertUserUIDtoEmailAddress(calendarId)
    jcount = len(ruleIds)
    entityPerformActionNumItems(EN_CALENDAR, calendarId, jcount, EN_ACL, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for ruleId in ruleIds:
      j += 1
      ruleId = normalizeRuleId(ruleId)
      body = convertRuleId(role, ruleId)
      if not _processCalendarAddACL(calendarId, i, count, j, jcount, cal, body):
        break
    decrementIndentLevel()

def _processCalendarUpdateACL(calendarId, i, count, j, jcount, cal, ruleId, body):
  result = True
  try:
    callGAPI(cal.acl(), u'patch',
             throw_reasons=[GAPI_NOT_FOUND, GAPI_INVALID, GAPI_CANNOT_CHANGE_OWNER_ACL],
             calendarId=calendarId, ruleId=ruleId, body=body)
    entityItemValueActionPerformed(EN_CALENDAR, calendarId, EN_ACL, formatACLScopeRole(ruleId, body[u'role']), j, jcount)
  except (GAPI_notFound, GAPI_invalid):
    if not checkCalendarExists(cal, calendarId):
      entityUnknownWarning(EN_CALENDAR, calendarId, i, count)
      result = False
    else:
      entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_ACL, formatACLScopeRole(ruleId, body[u'role']), PHRASE_DOES_NOT_EXIST, j, jcount)
  except GAPI_cannotChangeOwnerAcl:
    entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_ACL, formatACLScopeRole(ruleId, body[u'role']), PHRASE_CAN_NOT_CHANGE_OWNER_ACL, j, jcount)
  return result

# gam calendars <CalendarEntity> update acl <CalendarACLRole> ([user] <EmailAddress>)|(group <EmailAddress>)|(domain [<DomainName>])|default
# gam calendar <CalendarItem> update <CalendarACLRole> ([user] <EmailAddress>)|(group <EmailAddress>)|(domain [<DomainName>])|default
def doCalendarUpdateACL(cal, calendarList):
  body = {u'role': getChoice(CALENDAR_ACL_ROLES_MAP, mapChoice=True)}
  ruleId = getACLRuleId()
  checkForExtraneousArguments()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    calendarId = convertUserUIDtoEmailAddress(calendarId)
    _processCalendarUpdateACL(calendarId, i, count, i, count, cal, ruleId, body)

# gam calendars <CalendarEntity> update acls <CalendarACLRole> <ACLEntity>
def doCalendarUpdateACLs(cal, calendarList):
  body = {u'role': getChoice(CALENDAR_ACL_ROLES_MAP, mapChoice=True)}
  ruleIds = getEntityList(OB_ACL_ENTITY)
  ruleIdLists = ruleIds if isinstance(ruleIds, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    if ruleIdLists:
      ruleIds = ruleIdLists[calendarId]
    calendarId = convertUserUIDtoEmailAddress(calendarId)
    jcount = len(ruleIds)
    entityPerformActionNumItems(EN_CALENDAR, calendarId, jcount, EN_ACL, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for ruleId in ruleIds:
      j += 1
      ruleId = normalizeRuleId(ruleId)
      if not _processCalendarUpdateACL(calendarId, i, count, j, jcount, cal, ruleId, body):
        break
    decrementIndentLevel()

def _processCalendarDeleteACL(calendarId, i, count, j, jcount, cal, ruleId):
  result = True
  try:
    callGAPI(cal.acl(), u'delete',
             throw_reasons=[GAPI_NOT_FOUND, GAPI_INVALID_SCOPE_VALUE, GAPI_CANNOT_CHANGE_OWNER_ACL],
             calendarId=calendarId, ruleId=ruleId)
    entityItemValueActionPerformed(EN_CALENDAR, calendarId, EN_ACL, formatACLScopeRole(ruleId, None), j, jcount)
  except GAPI_notFound:
    entityUnknownWarning(EN_CALENDAR, calendarId, i, count)
    result = False
  except GAPI_invalidScopeValue:
    entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_ACL, formatACLScopeRole(ruleId, None), PHRASE_DOES_NOT_EXIST, j, jcount)
  except GAPI_cannotChangeOwnerAcl:
    entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_ACL, formatACLScopeRole(ruleId, None), PHRASE_CAN_NOT_CHANGE_OWNER_ACL, j, jcount)
  return result

# gam calendars <CalendarEntity> del|delete acl [<CalendarACLRole>] ([user] <EmailAddress>)|(group <EmailAddress>)|(domain [<DomainName>])|default
# gam calendar <CalendarItem> del|delete <CalendarACLRole> ([user] <EmailAddress>)|(group <EmailAddress>)|(domain [<DomainName>])|default
def doCalendarDeleteACL(cal, calendarList):
  getChoice(CALENDAR_ACL_ROLES_MAP, defaultChoice=None, mapChoice=True)
  ruleId = getACLRuleId()
  checkForExtraneousArguments()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    calendarId = convertUserUIDtoEmailAddress(calendarId)
    _processCalendarDeleteACL(calendarId, i, count, i, count, cal, ruleId)

# gam calendars <CalendarEntity> del|delete acls <ACLEntity>
def doCalendarDeleteACLs(cal, calendarList):
  ruleIds = getEntityList(OB_ACL_ENTITY)
  ruleIdLists = ruleIds if isinstance(ruleIds, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    if ruleIdLists:
      ruleIds = ruleIdLists[calendarId]
    calendarId = convertUserUIDtoEmailAddress(calendarId)
    jcount = len(ruleIds)
    entityPerformActionNumItems(EN_CALENDAR, calendarId, jcount, EN_ACL, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for ruleId in ruleIds:
      j += 1
      ruleId = normalizeRuleId(ruleId)
      if not _processCalendarDeleteACL(calendarId, i, count, j, jcount, cal, ruleId):
        break
    decrementIndentLevel()

# gam calendars <CalendarEntity> info acl|acls <ACLEntity>
def doCalendarInfoACLs(cal, calendarList):
  ruleIds = getEntityList(OB_ACL_ENTITY)
  ruleIdLists = ruleIds if isinstance(ruleIds, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    if ruleIdLists:
      ruleIds = ruleIdLists[calendarId]
    calendarId = convertUserUIDtoEmailAddress(calendarId)
    jcount = len(ruleIds)
    entityPerformActionNumItems(EN_CALENDAR, calendarId, jcount, EN_ACL, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for ruleId in ruleIds:
      j += 1
      ruleId = normalizeRuleId(ruleId)
      try:
        result = callGAPI(cal.acl(), u'get',
                          throw_reasons=[GAPI_NOT_FOUND, GAPI_INVALID],
                          calendarId=calendarId, ruleId=ruleId, fields=u'id,role')
        printEntityItemValue(EN_CALENDAR, calendarId, EN_ACL, formatACLScopeRole(result[u'id'], result[u'role']), j, jcount)
      except (GAPI_notFound, GAPI_invalid):
        if not checkCalendarExists(cal, calendarId):
          entityUnknownWarning(EN_CALENDAR, calendarId, i, count)
          break
        else:
          entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_ACL, formatACLScopeRole(ruleId, None), PHRASE_DOES_NOT_EXIST, j, jcount)
    decrementIndentLevel()

# gam calendars <CalendarEntity> show acls
# gam calendar <CalendarItem> showacl
def doCalendarShowACLs(cal, calendarList):
  checkForExtraneousArguments()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    calendarId = convertUserUIDtoEmailAddress(calendarId)
    try:
      acls = callGAPIpages(cal.acl(), u'list', u'items',
                           throw_reasons=[GAPI_NOT_FOUND],
                           calendarId=calendarId, fields=u'nextPageToken,items')
      jcount = len(acls)
      entityPerformActionNumItems(EN_CALENDAR, calendarId, jcount, EN_ACL, i, count)
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
        continue
      incrementIndentLevel()
      j = 0
      for rule in acls:
        j += 1
        printEntityItemValue(EN_CALENDAR, calendarId, EN_ACL, formatACLRule(rule), j, jcount)
      decrementIndentLevel()
    except GAPI_notFound:
      entityUnknownWarning(EN_CALENDAR, calendarId, i, count)

# gam calendars <CalendarEntity> wipe acls
def doCalendarWipeACLs(cal, calendarList):
  checkForExtraneousArguments()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    calendarId = convertUserUIDtoEmailAddress(calendarId)
    try:
      acls = callGAPIpages(cal.acl(), u'list', u'items',
                           throw_reasons=[GAPI_NOT_FOUND],
                           calendarId=calendarId, fields=u'nextPageToken,items')
      jcount = len(acls)
      entityPerformActionNumItems(EN_CALENDAR, calendarId, jcount, EN_ACL, i, count)
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
        continue
      incrementIndentLevel()
      j = 0
      for rule in acls:
        j += 1
        try:
          callGAPI(cal.acl(), u'delete',
                   throw_reasons=[GAPI_NOT_FOUND, GAPI_CANNOT_CHANGE_OWNER_ACL],
                   calendarId=calendarId, ruleId=rule[u'id'])
          entityItemValueActionPerformed(EN_CALENDAR, calendarId, EN_ACL, rule[u'id'], j, jcount)
        except GAPI_notFound:
          entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_ACL, rule[u'id'], PHRASE_DOES_NOT_EXIST, j, jcount)
        except GAPI_cannotChangeOwnerAcl:
          entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_ACL, rule[u'id'], PHRASE_CAN_NOT_CHANGE_OWNER_ACL, j, jcount)
      decrementIndentLevel()
    except GAPI_notFound:
      entityUnknownWarning(EN_CALENDAR, calendarId, i, count)
#
EVENT_PRINT_ORDER = [u'id', u'summary', u'description', u'location',
                     u'start', u'end', u'endTimeUnspecified',
                     u'creator', u'organizer', u'status', u'created', u'updated',]

def _showCalendarEvent(event, j, jcount):
  printEntityName(EN_EVENT, event[u'id'], j, jcount)
  skip_objects = [u'id',]
  incrementIndentLevel()
  for field in EVENT_PRINT_ORDER:
    if field in event:
      showJSON(field, event[field], skip_objects=skip_objects)
      skip_objects.append(field)
  showJSON(None, event, skip_objects=skip_objects)
  decrementIndentLevel()
#
CALENDAR_MIN_COLOR_INDEX = 1
CALENDAR_MAX_COLOR_INDEX = 24

CALENDAR_EVENT_MIN_COLOR_INDEX = 1
CALENDAR_EVENT_MAX_COLOR_INDEX = 11

CALENDAR_EVENT_VISIBILITY_CHOICES = [u'default', u'public', u'private',]

def getCalendarEventAttributes():
  body = {}
  parameters = {u'sendNotifications': None, u'timeZone': None}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'notifyattendees':
      parameters[u'sendNotifications'] = True
    elif myarg == u'attendee':
      body.setdefault(u'attendees', [])
      body[u'attendees'].append({u'email': getEmailAddress(noUid=True)})
    elif myarg == u'optionalattendee':
      body.setdefault(u'attendees', [])
      body[u'attendees'].append({u'email': getEmailAddress(noUid=True), u'optional': True})
    elif myarg == u'anyonecanaddself':
      body[u'anyoneCanAddSelf'] = True
    elif myarg == u'description':
      body[u'description'] = getString(OB_STRING)
    elif myarg == u'start':
      body[u'start'] = getEventTime()
    elif myarg == u'end':
      body[u'end'] = getEventTime()
    elif myarg == u'guestscantinviteothers':
      body[u'guestsCanInviteOthers'] = False
    elif myarg == u'guestscantseeothers':
      body[u'guestsCanSeeOtherGuests'] = False
    elif myarg == u'id':
      body[u'id'] = getString(OB_STRING)
    elif myarg == u'summary':
      body[u'summary'] = getString(OB_STRING)
    elif myarg == u'location':
      body[u'location'] = getString(OB_STRING)
    elif myarg == u'available':
      body[u'transparency'] = u'transparent'
    elif myarg == u'visibility':
      body[u'visibility'] = getChoice(CALENDAR_EVENT_VISIBILITY_CHOICES)
    elif myarg == u'tentative':
      body[u'status'] = u'tentative'
    elif myarg == u'source':
      body[u'source'] = {u'title': getString(OB_STRING), u'url': getString(OB_URL)}
    elif myarg == u'noreminders':
      body[u'reminders'] = {u'useDefault': False}
    elif myarg == u'reminder':
      body.setdefault(u'reminders', {u'overrides': [], u'useDefault': False})
      body[u'reminders'][u'overrides'].append(getCalendarReminder())
      body[u'reminders'][u'useDefault'] = False
    elif myarg == u'recurrence':
      body.setdefault(u'recurrence', [])
      body[u'recurrence'].append(getString(OB_RECURRENCE))
    elif myarg == u'timezone':
      parameters[u'timeZone'] = getString(OB_STRING)
    elif myarg == u'privateproperty':
      body.setdefault(u'extendedProperties', {u'private': {}, u'shared': {}})
      key = getString(OB_PROPERTY_KEY)
      body[u'extendedProperties'][u'private'][key] = getString(OB_PROPERTY_VALUE)
    elif myarg == u'sharedproperty':
      body.setdefault(u'extendedProperties', {u'private': {}, u'shared': {}})
      key = getString(OB_PROPERTY_KEY)
      body[u'extendedProperties'][u'shared'][key] = getString(OB_PROPERTY_VALUE)
    elif myarg in [u'colorindex', u'colorid']:
      body[u'colorId'] = str(getInteger(CALENDAR_EVENT_MIN_COLOR_INDEX, CALENDAR_EVENT_MAX_COLOR_INDEX))
    else:
      unknownArgumentExit()
  return (body, parameters)

# gam calendars <CalendarEntity> add event <EventAttributes>
# gam calendar <CalendarItem> addevent <EventAttributes>
def doCalendarAddEvent(cal, calendarList):
  body, parameters = getCalendarEventAttributes()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    calendarId, cal = buildCalendarGAPIObject(calendarId)
    if not cal:
      continue
    try:
      if u'recurrence' in body:
        if not parameters[u'timeZone']:
          parameters[u'timeZone'] = callGAPI(cal.calendars(), u'get',
                                             throw_reasons=GAPI_CALENDAR_THROW_REASONS,
                                             calendarId=calendarId, fields=u'timeZone')[u'timeZone']
        if u'start' in body:
          body[u'start'][u'timeZone'] = parameters[u'timeZone']
        if u'end' in body:
          body[u'end'][u'timeZone'] = parameters[u'timeZone']
      event = callGAPI(cal.events(), u'insert',
                       throw_reasons=GAPI_CALENDAR_THROW_REASONS+[GAPI_INVALID, GAPI_REQUIRED, GAPI_TIME_RANGE_EMPTY],
                       calendarId=calendarId, sendNotifications=parameters[u'sendNotifications'], body=body)
      entityItemValueActionPerformed(EN_CALENDAR, calendarId, EN_EVENT, event[u'id'], i, count)
      incrementIndentLevel()
      _showCalendarEvent(event, i, count)
      decrementIndentLevel()
    except (GAPI_invalid, GAPI_required, GAPI_timeRangeEmpty) as e:
      entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_EVENT, u'', e.message, i, count)
      break
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_CALENDAR, calendarId, i, count)

# gam calendars <CalendarEntity> update event <EventIDEntity> <EventAttributes>
def doCalendarUpdateEvent(cal, calendarList):
  eventIds = getEntityList(OB_EVENT_ID_ENTITY)
  eventIdLists = eventIds if isinstance(eventIds, dict) else None
  body, parameters = getCalendarEventAttributes()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    if eventIdLists:
      eventIds = eventIdLists[calendarId]
    calendarId, cal = buildCalendarGAPIObject(calendarId)
    if not cal:
      continue
    jcount = len(eventIds)
    entityPerformActionNumItems(EN_CALENDAR, calendarId, jcount, EN_EVENT, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for eventId in eventIds:
      j += 1
      try:
        if u'recurrence' in body:
          if not parameters[u'timeZone']:
            parameters[u'timeZone'] = callGAPI(cal.calendars(), u'get',
                                               throw_reasons=GAPI_CALENDAR_THROW_REASONS,
                                               calendarId=calendarId, fields=u'timeZone')[u'timeZone']
          if u'start' in body:
            body[u'start'][u'timeZone'] = parameters[u'timeZone']
          if u'end' in body:
            body[u'end'][u'timeZone'] = parameters[u'timeZone']
        event = callGAPI(cal.events(), u'patch',
                         throw_reasons=GAPI_CALENDAR_THROW_REASONS+[GAPI_NOT_FOUND, GAPI_INVALID, GAPI_REQUIRED, GAPI_TIME_RANGE_EMPTY],
                         calendarId=calendarId, eventId=eventId, sendNotifications=parameters[u'sendNotifications'], body=body)
        entityItemValueActionPerformed(EN_CALENDAR, calendarId, EN_EVENT, eventId, j, jcount)
        incrementIndentLevel()
        _showCalendarEvent(event, j, jcount)
        decrementIndentLevel()
      except GAPI_notFound:
        entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_EVENT, eventId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_invalid, GAPI_required, GAPI_timeRangeEmpty) as e:
        entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_EVENT, eventId, e.message, j, jcount)
        return
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_CALENDAR, calendarId, i, count)
        break

# gam calendars <CalendarEntity> delete event <EventIDEntity>
def doCalendarDeleteEvent(cal, calendarList):
  eventIds = getEntityList(OB_EVENT_ID_ENTITY)
  eventIdLists = eventIds if isinstance(eventIds, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    if eventIdLists:
      eventIds = eventIdLists[calendarId]
    calendarId, cal = buildCalendarGAPIObject(calendarId)
    if not cal:
      continue
    jcount = len(eventIds)
    entityPerformActionNumItems(EN_CALENDAR, calendarId, jcount, EN_EVENT, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for eventId in eventIds:
      j += 1
      try:
        callGAPI(cal.events(), u'delete',
                 throw_reasons=GAPI_CALENDAR_THROW_REASONS+[GAPI_NOT_FOUND, GAPI_DELETED],
                 calendarId=calendarId, eventId=eventId)
        entityItemValueActionPerformed(EN_CALENDAR, calendarId, EN_EVENT, eventId, j, jcount)
      except (GAPI_notFound, GAPI_deleted):
        entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_EVENT, eventId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_CALENDAR, calendarId, i, count)
        break
    decrementIndentLevel()

# gam calendars <CalendarEntity> info event <EventIDEntity>
def doCalendarInfoEvent(cal, calendarList):
  eventIds = getEntityList(OB_EVENT_ID_ENTITY)
  eventIdLists = eventIds if isinstance(eventIds, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    if eventIdLists:
      eventIds = eventIdLists[calendarId]
    calendarId, cal = buildCalendarGAPIObject(calendarId)
    if not cal:
      continue
    jcount = len(eventIds)
    entityPerformActionNumItems(EN_CALENDAR, calendarId, jcount, EN_EVENT, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for eventId in eventIds:
      j += 1
      try:
        event = callGAPI(cal.events(), u'get',
                         throw_reasons=GAPI_CALENDAR_THROW_REASONS+[GAPI_NOT_FOUND, GAPI_DELETED],
                         calendarId=calendarId, eventId=eventId)
        printEntityItemValue(EN_CALENDAR, calendarId, EN_EVENT, eventId, j, jcount)
        incrementIndentLevel()
        _showCalendarEvent(event, j, jcount)
        decrementIndentLevel()
      except (GAPI_notFound, GAPI_deleted):
        entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_EVENT, eventId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_CALENDAR, calendarId, i, count)
        break
    decrementIndentLevel()

# gam calendars <CalendarEntity> move event <EventIDEntity> to <CalendarItem>
def doCalendarMoveEvent(cal, calendarList):
  eventIds = getEntityList(OB_EVENT_ID_ENTITY)
  eventIdLists = eventIds if isinstance(eventIds, dict) else None
  checkArgumentPresent(TO_ARGUMENT)
  newCalendarId = convertUserUIDtoEmailAddress(getString(OB_CALENDAR_ITEM))
  checkForExtraneousArguments()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    if eventIdLists:
      eventIds = eventIdLists[calendarId]
    calendarId, cal = buildCalendarGAPIObject(calendarId)
    if not cal:
      continue
    jcount = len(eventIds)
    entityPerformActionNumItems(EN_CALENDAR, calendarId, jcount, EN_EVENT, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for eventId in eventIds:
      j += 1
      try:
        callGAPI(cal.events(), u'move',
                 throw_reasons=GAPI_CALENDAR_THROW_REASONS+[GAPI_NOT_FOUND, GAPI_FORBIDDEN],
                 calendarId=calendarId, eventId=eventId, destination=newCalendarId)
        entityItemValueModifierNewValueActionPerformed(EN_CALENDAR, calendarId, EN_EVENT, eventId, AC_MODIFIER_TO, u'{0}: {1}'.format(singularEntityName(EN_CALENDAR), newCalendarId), j, jcount)
      except GAPI_notFound:
        entityItemValueItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_EVENT, eventId, EN_CALENDAR, newCalendarId, entityTypeNameMessage(EN_EVENT, eventId, PHRASE_DOES_NOT_EXIST), j, jcount)
      except GAPI_forbidden:
        entityItemValueActionFailedWarning(EN_CALENDAR, calendarId, EN_EVENT, eventId, entityTypeNameMessage(EN_CALENDAR, newCalendarId, PHRASE_NOT_ALLOWED), j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_CALENDAR, calendarId, i, count)
        break
    decrementIndentLevel()

SHOW_EVENTS_ATTRIBUTES = {
  u'alwaysincludeemail': [u'alwaysIncludeEmail', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'endtime': [u'timeMax', {GC_VAR_TYPE: GC_TYPE_DATETIME}],
  u'icaluid': [u'iCalUID', {GC_VAR_TYPE: GC_TYPE_STRING}],
  u'maxattendees': [u'maxAttendees', {GC_VAR_TYPE: GC_TYPE_INTEGER}],
  u'orderby': [u'orderBy', {GC_VAR_TYPE: GC_TYPE_CHOICE, u'choices': {u'starttime': u'startTime', u'updated': u'updated'}}],
  u'privateextendedproperty': [u'privateExtendedProperty', {GC_VAR_TYPE: GC_TYPE_STRING}],
  u'query': [u'q', {GC_VAR_TYPE: GC_TYPE_STRING}],
  u'q': [u'q', {GC_VAR_TYPE: GC_TYPE_STRING}],
  u'sharedextendedproperty': [u'sharedExtendedProperty', {GC_VAR_TYPE: GC_TYPE_STRING}],
  u'showdeleted': [u'showDeleted', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'showhiddeninvitations': [u'showHiddenInvitations', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'singleevents': [u'singleEvents', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'starttime': [u'timeMin', {GC_VAR_TYPE: GC_TYPE_DATETIME}],
  u'timemax': [u'timeMax', {GC_VAR_TYPE: GC_TYPE_DATETIME}],
  u'timemin': [u'timeMin', {GC_VAR_TYPE: GC_TYPE_DATETIME}],
  u'timezone': [u'timeZone', {GC_VAR_TYPE: GC_TYPE_STRING}],
  u'updatedmin': [u'updatedMin', {GC_VAR_TYPE: GC_TYPE_DATETIME}],
  }

# gam calendars <CalendarEntity> print events [todrive] [alwaysincludeemail] [showdeleted] [showhiddeninvitations] [singleevents]
#	[icaluid <String>] (privateextendedproperty <String)* (sharedextendedproperty <String>)* [q|query <String>] [maxattendees <Integer>]
#	[starttime|timemin <Time>] [endtime|timemax <Time>] [updatedmin <Time>] [orderby starttime|updated]
def doCalendarPrintEvents(cal, calendarList):
  calendarPrintShowEvents(cal, calendarList, True)

# gam calendars <CalendarEntity> show events [alwaysincludeemail] [showdeleted] [showhiddeninvitations] [singleevents]
#	[icaluid <String>] (privateextendedproperty <String)* (sharedextendedproperty <String>)* [q|query <String>] [maxattendees <Integer>]
#	[starttime|timemin <Time>] [endtime|timemax <Time>] [updatedmin <Time>] [orderby starttime|updated]
def doCalendarShowEvents(cal, calendarList):
  calendarPrintShowEvents(cal, calendarList, False)

def calendarPrintShowEvents(cal, calendarList, csvFormat):
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile(None)
  kwargs = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    else:
      attrProperties = SHOW_EVENTS_ATTRIBUTES.get(myarg)
      if not attrProperties:
        unknownArgumentExit()
      attrName = attrProperties[0]
      attribute = attrProperties[1]
      attrType = attribute[GC_VAR_TYPE]
      if attrType == GC_TYPE_BOOLEAN:
        kwargs[attrName] = True
      elif attrType == GC_TYPE_STRING:
        kwargs[attrName] = getString(OB_STRING)
      elif attrType == GC_TYPE_CHOICE:
        kwargs[attrName] = getChoice(attribute[u'choices'], mapChoice=True)
      elif attrType == GC_TYPE_DATETIME:
        kwargs[attrName] = getFullTime()
      else: # GC_TYPE_INTEGER
        kwargs[attrName] = getInteger()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    calendarId, cal = buildCalendarGAPIObject(calendarId)
    if not cal:
      continue
    try:
      events = callGAPIpages(cal.events(), u'list', u'items',
                             throw_reasons=GAPI_CALENDAR_THROW_REASONS,
                             calendarId=calendarId, fields=u'nextPageToken,items', **kwargs)
      jcount = len(events)
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
      if not csvFormat:
        entityPerformActionNumItems(EN_CALENDAR, calendarId, jcount, EN_EVENT, i, count)
        if jcount > 0:
          incrementIndentLevel()
          j = 0
          for event in events:
            j += 1
            _showCalendarEvent(event, j, jcount)
          decrementIndentLevel()
      else:
        if jcount > 0:
          for event in events:
            row = {u'calendarId': calendarId}
            addRowTitlesToCSVfile(flattenJSON(event, flattened=row), csvRows, titles)
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_CALENDAR, calendarId, i, count)
  if csvFormat:
    sortCSVTitles([u'calendarId']+EVENT_PRINT_ORDER, titles)
    writeCSVfile(csvRows, titles, u'Calendar Events', todrive)

# gam calendars <CalendarEntity> wipe events
# gam calendar <CalendarItem> wipe
def doCalendarWipeEvents(cal, calendarList):
  checkForExtraneousArguments()
  i = 0
  count = len(calendarList)
  for calendarId in calendarList:
    i += 1
    calendarId, cal = buildCalendarGAPIObject(calendarId)
    if not cal:
      continue
    try:
      callGAPI(cal.calendars(), u'clear',
               throw_reasons=GAPI_CALENDAR_THROW_REASONS,
               calendarId=calendarId)
      entityActionPerformed(EN_CALENDAR, calendarId, i, count)
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_CALENDAR, calendarId, i, count)

# Contacts utilities
#
CONTACT_ID = u'ContactID'
CONTACT_UPDATED = u'Updated'
CONTACT_NAME_PREFIX = u'Name Prefix'
CONTACT_GIVEN_NAME = u'Given Name'
CONTACT_ADDITIONAL_NAME = u'Additional Name'
CONTACT_FAMILY_NAME = u'Family Name'
CONTACT_NAME_SUFFIX = u'Name Suffix'
CONTACT_NAME = u'Name'
CONTACT_NICKNAME = u'Nickname'
CONTACT_MAIDENNAME = u'Maiden Name'
CONTACT_SHORTNAME = u'Short Name'
CONTACT_INITIALS = u'Initials'
CONTACT_BIRTHDAY = u'Birthday'
CONTACT_GENDER = u'Gender'
CONTACT_LOCATION = u'Location'
CONTACT_PRIORITY = u'Priority'
CONTACT_SENSITIVITY = u'Sensitivity'
CONTACT_SUBJECT = u'Subject'
CONTACT_LANGUAGE = u'Language'
CONTACT_NOTES = u'Notes'
CONTACT_OCCUPATION = u'Occupation'
CONTACT_BILLING_INFORMATION = u'Billing Information'
CONTACT_MILEAGE = u'Mileage'
CONTACT_DIRECTORY_SERVER = u'Directory Server'
CONTACT_ADDRESSES = u'Addresses'
CONTACT_CALENDARS = u'Calendars'
CONTACT_EMAILS = u'Emails'
CONTACT_EXTERNALIDS = u'External IDs'
CONTACT_EVENTS = u'Events'
CONTACT_HOBBIES = u'Hobbies'
CONTACT_IMS = u'IMs'
CONTACT_JOTS = u'Jots'
CONTACT_ORGANIZATIONS = u'Organizations'
CONTACT_PHONES = u'Phones'
CONTACT_RELATIONS = u'Relations'
CONTACT_USER_DEFINED_FIELDS = u'User Defined Fields'
CONTACT_WEBSITES = u'Websites'
CONTACT_GROUPS = u'ContactGroups'
CONTACT_GROUPS_LIST = u'ContactGroupsList'
#
CONTACT_GROUP_ID = u'ContactGroupID'
CONTACT_GROUP_UPDATED = u'Updated'
CONTACT_GROUP_NAME = u'ContactGroupName'
#
class ContactsManager(object):
  import gdata.apps.contacts

  CONTACT_ARGUMENT_TO_PROPERTY_MAP = {
    u'name': CONTACT_NAME,
    u'prefix': CONTACT_NAME_PREFIX,
    u'givenname': CONTACT_GIVEN_NAME,
    u'additionalname': CONTACT_ADDITIONAL_NAME,
    u'familyname': CONTACT_FAMILY_NAME,
    u'firstname': CONTACT_GIVEN_NAME,
    u'middlename': CONTACT_ADDITIONAL_NAME,
    u'lastname': CONTACT_FAMILY_NAME,
    u'suffix': CONTACT_NAME_SUFFIX,
    u'nickname': CONTACT_NICKNAME,
    u'maidenname': CONTACT_MAIDENNAME,
    u'shortname': CONTACT_SHORTNAME,
    u'initials': CONTACT_INITIALS,
    u'birthday': CONTACT_BIRTHDAY,
    u'gender': CONTACT_GENDER,
    u'location': CONTACT_LOCATION,
    u'priority': CONTACT_PRIORITY,
    u'sensitivity': CONTACT_SENSITIVITY,
    u'subject': CONTACT_SUBJECT,
    u'language': CONTACT_LANGUAGE,
    u'note': CONTACT_NOTES,
    u'notes': CONTACT_NOTES,
    u'occupation': CONTACT_OCCUPATION,
    u'billinginfo': CONTACT_BILLING_INFORMATION,
    u'mileage': CONTACT_MILEAGE,
    u'directoryserver': CONTACT_DIRECTORY_SERVER,
    u'address': CONTACT_ADDRESSES,
    u'addresses': CONTACT_ADDRESSES,
    u'calendar': CONTACT_CALENDARS,
    u'calendars': CONTACT_CALENDARS,
    u'email': CONTACT_EMAILS,
    u'emails': CONTACT_EMAILS,
    u'externalid': CONTACT_EXTERNALIDS,
    u'externalids': CONTACT_EXTERNALIDS,
    u'event': CONTACT_EVENTS,
    u'events': CONTACT_EVENTS,
    u'hobby': CONTACT_HOBBIES,
    u'hobbies': CONTACT_HOBBIES,
    u'im': CONTACT_IMS,
    u'ims': CONTACT_IMS,
    u'jot': CONTACT_JOTS,
    u'jots': CONTACT_JOTS,
    u'organization': CONTACT_ORGANIZATIONS,
    u'organizations': CONTACT_ORGANIZATIONS,
    u'phone': CONTACT_PHONES,
    u'phones': CONTACT_PHONES,
    u'relation': CONTACT_RELATIONS,
    u'relations': CONTACT_RELATIONS,
    u'userdefinedfield': CONTACT_USER_DEFINED_FIELDS,
    u'userdefinedfields': CONTACT_USER_DEFINED_FIELDS,
    u'website': CONTACT_WEBSITES,
    u'websites': CONTACT_WEBSITES,
    u'contactgroup': CONTACT_GROUPS,
    u'contactgroups': CONTACT_GROUPS,
    }

  GENDER_CHOICE_MAP = {u'male': u'male', u'female': u'female',}

  PRIORITY_CHOICE_MAP = {u'low': u'low', u'normal': u'normal', u'high': u'high',}

  SENSITIVITY_CHOICE_MAP = {
    u'confidential': u'confidential',
    u'normal': u'normal',
    u'personal': u'personal',
    u'private': u'private',
    }

  PRIMARY_NOTPRIMARY_CHOICE_MAP = {u'primary': u'true', u'notprimary': u'false',}

  CONTACT_NAME_FIELDS = (
    CONTACT_NAME_PREFIX,
    CONTACT_GIVEN_NAME,
    CONTACT_ADDITIONAL_NAME,
    CONTACT_FAMILY_NAME,
    CONTACT_NAME_SUFFIX,
    )

  ADDRESS_TYPE_ARGUMENT_TO_REL = {
    u'work': gdata.apps.contacts.REL_WORK,
    u'home': gdata.apps.contacts.REL_HOME,
    u'other': gdata.apps.contacts.REL_OTHER,
    }

  ADDRESS_REL_TO_TYPE_ARGUMENT = {
    gdata.apps.contacts.REL_WORK: u'work',
    gdata.apps.contacts.REL_HOME: u'home',
    gdata.apps.contacts.REL_OTHER: u'other',
    }

  ADDRESS_ARGUMENT_TO_FIELD_MAP = {
    u'streetaddress': u'street',
    u'pobox': u'pobox',
    u'neighborhood': u'neighborhood',
    u'locality': u'city',
    u'region': u'region',
    u'postalcode': u'postcode',
    u'country': u'country',
    u'formatted': u'value', u'unstructured': u'value',
    }

  ADDRESS_FIELD_TO_ARGUMENT_MAP = {
    u'street': u'streetaddress',
    u'pobox': u'pobox',
    u'neighborhood': u'neighborhood',
    u'city': u'locality',
    u'region': u'region',
    u'postcode': u'postalcode',
    u'country': u'country',
    }

  ADDRESS_FIELD_PRINT_ORDER = [
    u'street',
    u'pobox',
    u'neighborhood',
    u'city',
    u'region',
    u'postcode',
    u'country',
    ]

  CALENDAR_TYPE_ARGUMENT_TO_REL = {
    u'work': u'work',
    u'home': u'home',
    u'free-busy': u'free-busy',
    }

  CALENDAR_REL_TO_TYPE_ARGUMENT = {
    u'work': u'work',
    u'home': u'home',
    u'free-busy': u'free-busy',
    }

  EMAIL_TYPE_ARGUMENT_TO_REL = {
    u'work': gdata.apps.contacts.REL_WORK,
    u'home': gdata.apps.contacts.REL_HOME,
    u'other': gdata.apps.contacts.REL_OTHER,
    }

  EMAIL_REL_TO_TYPE_ARGUMENT = {
    gdata.apps.contacts.REL_WORK: u'work',
    gdata.apps.contacts.REL_HOME: u'home',
    gdata.apps.contacts.REL_OTHER: u'other',
    }

  EVENT_TYPE_ARGUMENT_TO_REL = {
    u'anniversary': u'anniversary',
    u'other': u'other',
    }

  EVENT_REL_TO_TYPE_ARGUMENT = {
    u'anniversary': u'anniversary',
    u'other': u'other',
    }

  EXTERNALID_TYPE_ARGUMENT_TO_REL = {
    u'account': u'account',
    u'customer': u'customer',
    u'network': u'network',
    u'organization': u'organization',
    }

  EXTERNALID_REL_TO_TYPE_ARGUMENT = {
    u'account': u'account',
    u'customer': u'customer',
    u'network': u'network',
    u'organization': u'organization',
    }

  IM_TYPE_ARGUMENT_TO_REL = {
    u'work': gdata.apps.contacts.REL_WORK,
    u'home': gdata.apps.contacts.REL_HOME,
    u'other': gdata.apps.contacts.REL_OTHER,
    }

  IM_REL_TO_TYPE_ARGUMENT = {
    gdata.apps.contacts.REL_WORK: u'work',
    gdata.apps.contacts.REL_HOME: u'home',
    gdata.apps.contacts.REL_OTHER: u'other',
    }

  IM_PROTOCOL_TO_REL_MAP = {
    u'aim': gdata.apps.contacts.IM_AIM,
    u'gtalk': gdata.apps.contacts.IM_GOOGLE_TALK,
    u'icq': gdata.apps.contacts.IM_ICQ,
    u'jabber': gdata.apps.contacts.IM_JABBER,
    u'msn': gdata.apps.contacts.IM_MSN,
    u'netmeeting': gdata.apps.contacts.IM_NETMEETING,
    u'qq': gdata.apps.contacts.IM_QQ,
    u'skype': gdata.apps.contacts.IM_SKYPE,
    u'xmpp': gdata.apps.contacts.IM_JABBER,
    u'yahoo': gdata.apps.contacts.IM_YAHOO,
    }

  IM_REL_TO_PROTOCOL_MAP = {
    gdata.apps.contacts.IM_AIM: u'aim',
    gdata.apps.contacts.IM_GOOGLE_TALK: u'gtalk',
    gdata.apps.contacts.IM_ICQ: u'icq',
    gdata.apps.contacts.IM_JABBER: u'jabber',
    gdata.apps.contacts.IM_MSN: u'msn',
    gdata.apps.contacts.IM_NETMEETING: u'netmeeting',
    gdata.apps.contacts.IM_QQ: u'qq',
    gdata.apps.contacts.IM_SKYPE: u'skype',
    gdata.apps.contacts.IM_YAHOO: u'yahoo',
    }

  JOT_TYPE_ARGUMENT_TO_REL = {
    u'work': u'work',
    u'home': u'home',
    u'other': u'other',
    u'keywords': u'keywords',
    u'user': u'user',
    }

  JOT_REL_TO_TYPE_ARGUMENT = {
    u'work': u'work',
    u'home': u'home',
    u'other': u'other',
    u'keywords': u'keywords',
    u'user': u'user',
    }

  ORGANIZATION_TYPE_ARGUMENT_TO_REL = {
    u'work': gdata.apps.contacts.REL_WORK,
    u'other': gdata.apps.contacts.REL_OTHER,
    }

  ORGANIZATION_REL_TO_TYPE_ARGUMENT = {
    gdata.apps.contacts.REL_WORK: u'work',
    gdata.apps.contacts.REL_OTHER: u'other',
    }

  ORGANIZATION_ARGUMENT_TO_FIELD_MAP = {
    u'location': u'where',
    u'department': u'department',
    u'title': u'title',
    u'jobdescription': u'jobdescription',
    u'symbol': u'symbol',
    }

  ORGANIZATION_FIELD_TO_ARGUMENT_MAP = {
    u'where': u'location',
    u'department': u'department',
    u'title': u'title',
    u'jobdescription': u'jobdescription',
    u'symbol': u'symbol',
    }

  ORGANIZATION_FIELD_PRINT_ORDER = [
    u'where',
    u'department',
    u'title',
    u'jobdescription',
    u'symbol',
    ]

  PHONE_TYPE_ARGUMENT_TO_REL = {
    u'work': gdata.apps.contacts.PHONE_WORK,
    u'home': gdata.apps.contacts.PHONE_HOME,
    u'other': gdata.apps.contacts.PHONE_OTHER,
    u'fax': gdata.apps.contacts.PHONE_HOME_FAX,
    u'home_fax': gdata.apps.contacts.PHONE_HOME_FAX,
    u'work_fax': gdata.apps.contacts.PHONE_WORK_FAX,
    u'other_fax': gdata.apps.contacts.PHONE_OTHER_FAX,
    u'main': gdata.apps.contacts.PHONE_MAIN,
    u'company_main': gdata.apps.contacts.PHONE_COMPANY_MAIN,
    u'assistant': gdata.apps.contacts.PHONE_ASSISTANT,
    u'mobile': gdata.apps.contacts.PHONE_MOBILE,
    u'work_mobile': gdata.apps.contacts.PHONE_WORK_MOBILE,
    u'pager': gdata.apps.contacts.PHONE_PAGER,
    u'work_pager': gdata.apps.contacts.PHONE_WORK_PAGER,
    u'car': gdata.apps.contacts.PHONE_CAR,
    u'radio': gdata.apps.contacts.PHONE_RADIO,
    u'callback': gdata.apps.contacts.PHONE_CALLBACK,
    u'isdn': gdata.apps.contacts.PHONE_ISDN,
    u'telex': gdata.apps.contacts.PHONE_TELEX,
    u'tty_tdd': gdata.apps.contacts.PHONE_TTY_TDD,
    }

  PHONE_REL_TO_TYPE_ARGUMENT = {
    gdata.apps.contacts.PHONE_WORK: u'work',
    gdata.apps.contacts.PHONE_HOME: u'home',
    gdata.apps.contacts.PHONE_OTHER: u'other',
    gdata.apps.contacts.PHONE_HOME_FAX: u'fax',
    gdata.apps.contacts.PHONE_HOME_FAX: u'home_fax',
    gdata.apps.contacts.PHONE_WORK_FAX: u'work_fax',
    gdata.apps.contacts.PHONE_OTHER_FAX: u'other_fax',
    gdata.apps.contacts.PHONE_MAIN: u'main',
    gdata.apps.contacts.PHONE_COMPANY_MAIN: u'company_main',
    gdata.apps.contacts.PHONE_ASSISTANT: u'assistant',
    gdata.apps.contacts.PHONE_MOBILE: u'mobile',
    gdata.apps.contacts.PHONE_WORK_MOBILE: u'work_mobile',
    gdata.apps.contacts.PHONE_PAGER: u'pager',
    gdata.apps.contacts.PHONE_WORK_PAGER: u'work_pager',
    gdata.apps.contacts.PHONE_CAR: u'car',
    gdata.apps.contacts.PHONE_RADIO: u'radio',
    gdata.apps.contacts.PHONE_CALLBACK: u'callback',
    gdata.apps.contacts.PHONE_ISDN: u'isdn',
    gdata.apps.contacts.PHONE_TELEX: u'telex',
    gdata.apps.contacts.PHONE_TTY_TDD: u'tty_tdd',
    }

  RELATION_TYPE_ARGUMENT_TO_REL = {
    u'spouse': u'spouse',
    u'child': u'child',
    u'mother': u'mother',
    u'father': u'father',
    u'parent': u'parent',
    u'brother': u'brother',
    u'sister': u'sister',
    u'friend': u'friend',
    u'relative': u'relative',
    u'manager': u'manager',
    u'assistant': u'assistant',
    u'referredby': u'referred-by',
    u'partner': u'partner',
    u'domesticpartner': u'domestic-partner',
    }

  RELATION_REL_TO_TYPE_ARGUMENT = {
    u'spouse' : u'spouse',
    u'child' : u'child',
    u'mother' : u'mother',
    u'father' : u'father',
    u'parent' : u'parent',
    u'brother' : u'brother',
    u'sister' : u'sister',
    u'friend' : u'friend',
    u'relative' : u'relative',
    u'manager' : u'manager',
    u'assistant' : u'assistant',
    u'referred-by' : u'referred_by',
    u'partner' : u'partner',
    u'domestic-partner' : u'domestic_partner',
    }

  WEBSITE_TYPE_ARGUMENT_TO_REL = {
    u'home-page': u'home-page',
    u'blog': u'blog',
    u'profile': u'profile',
    u'work': u'work',
    u'home': u'home',
    u'other': u'other',
    u'ftp': u'ftp',
    u'reservations': u'reservations',
    u'app-install-page': u'app-install-page',
    }

  WEBSITE_REL_TO_TYPE_ARGUMENT = {
    u'home-page': u'home-page',
    u'blog': u'blog',
    u'profile': u'profile',
    u'work': u'work',
    u'home': u'home',
    u'other': u'other',
    u'ftp': u'ftp',
    u'reservations': u'reservations',
    u'app-install-page': u'app-install-page',
    }

  CONTACT_NAME_PROPERTY_PRINT_ORDER = [
    CONTACT_UPDATED,
    CONTACT_NAME,
    CONTACT_NAME_PREFIX,
    CONTACT_GIVEN_NAME,
    CONTACT_ADDITIONAL_NAME,
    CONTACT_FAMILY_NAME,
    CONTACT_NAME_SUFFIX,
    CONTACT_NICKNAME,
    CONTACT_MAIDENNAME,
    CONTACT_SHORTNAME,
    CONTACT_INITIALS,
    CONTACT_BIRTHDAY,
    CONTACT_GENDER,
    CONTACT_LOCATION,
    CONTACT_PRIORITY,
    CONTACT_SENSITIVITY,
    CONTACT_SUBJECT,
    CONTACT_LANGUAGE,
    CONTACT_NOTES,
    CONTACT_OCCUPATION,
    CONTACT_BILLING_INFORMATION,
    CONTACT_MILEAGE,
    CONTACT_DIRECTORY_SERVER,
    ]

  CONTACT_ARRAY_PROPERTY_PRINT_ORDER = [
    CONTACT_ADDRESSES,
    CONTACT_EMAILS,
    CONTACT_IMS,
    CONTACT_PHONES,
    CONTACT_CALENDARS,
    CONTACT_ORGANIZATIONS,
    CONTACT_EXTERNALIDS,
    CONTACT_EVENTS,
    CONTACT_HOBBIES,
    CONTACT_JOTS,
    CONTACT_RELATIONS,
    CONTACT_WEBSITES,
    CONTACT_USER_DEFINED_FIELDS,
    ]

  CONTACT_ARRAY_PROPERTIES = {
    CONTACT_ADDRESSES: {u'relMap': ADDRESS_REL_TO_TYPE_ARGUMENT, u'infoTitle': u'formatted', u'primary': True},
    CONTACT_EMAILS: {u'relMap': EMAIL_REL_TO_TYPE_ARGUMENT, u'infoTitle': u'address', u'primary': True},
    CONTACT_IMS: {u'relMap': IM_REL_TO_TYPE_ARGUMENT, u'infoTitle': u'address', u'primary': True},
    CONTACT_PHONES: {u'relMap': PHONE_REL_TO_TYPE_ARGUMENT, u'infoTitle': u'value', u'primary': True},
    CONTACT_CALENDARS: {u'relMap': CALENDAR_REL_TO_TYPE_ARGUMENT, u'infoTitle': u'address', u'primary': True},
    CONTACT_ORGANIZATIONS: {u'relMap': ORGANIZATION_REL_TO_TYPE_ARGUMENT, u'infoTitle': u'name', u'primary': True},
    CONTACT_EXTERNALIDS: {u'relMap': EXTERNALID_REL_TO_TYPE_ARGUMENT, u'infoTitle': u'value', u'primary': False},
    CONTACT_EVENTS: {u'relMap': EVENT_REL_TO_TYPE_ARGUMENT, u'infoTitle': u'date', u'primary': False},
    CONTACT_HOBBIES: {u'relMap': None, u'infoTitle': u'value', u'primary': False},
    CONTACT_JOTS: {u'relMap': JOT_REL_TO_TYPE_ARGUMENT, u'infoTitle': u'value', u'primary': False},
    CONTACT_RELATIONS: {u'relMap': RELATION_REL_TO_TYPE_ARGUMENT, u'infoTitle': u'value', u'primary': False},
    CONTACT_USER_DEFINED_FIELDS: {u'relMap': None, u'infoTitle': u'value', u'primary': False},
    CONTACT_WEBSITES: {u'relMap': WEBSITE_REL_TO_TYPE_ARGUMENT, u'infoTitle': u'value', u'primary': True},
    }

  CONTACT_GROUP_ARGUMENT_TO_PROPERTY_MAP = {
    u'name': CONTACT_GROUP_NAME,
    }

  @staticmethod
  def GetContactShortId(contactEntry):
    full_id = contactEntry.id.text
    return full_id[full_id.rfind(u'/') + 1:]

  @staticmethod
  def GetContactFields(entityType):

    fields = {}

    def ClearFieldsList(fieldName):
      if fieldName in fields:
        del fields[fieldName]
      fields.setdefault(fieldName, [])

    def InitArrayItem(choices):
      item = {}
      rel = getChoice(choices, mapChoice=True, defaultChoice=None)
      if rel:
        item[u'rel'] = rel
        item[u'label'] = None
      else:
        item[u'rel'] = None
        item[u'label'] = getString(OB_STRING)
      return item

    def AppendItemToFieldsList(fieldName, fieldValue):
      fields.setdefault(fieldName, [])
      fields[fieldName].append(fieldValue)

    while CL_argvI < CL_argvLen:
      fieldName = getChoice(ContactsManager.CONTACT_ARGUMENT_TO_PROPERTY_MAP, mapChoice=True)
      if fieldName == CONTACT_BIRTHDAY:
        fields[fieldName] = getYYYYMMDD(emptyOK=True)
      elif fieldName == CONTACT_GENDER:
        fields[fieldName] = getChoice(ContactsManager.GENDER_CHOICE_MAP, mapChoice=True)
      elif fieldName == CONTACT_PRIORITY:
        fields[fieldName] = getChoice(ContactsManager.PRIORITY_CHOICE_MAP, mapChoice=True)
      elif fieldName == CONTACT_SENSITIVITY:
        fields[fieldName] = getChoice(ContactsManager.SENSITIVITY_CHOICE_MAP, mapChoice=True)
      elif fieldName == CONTACT_LANGUAGE:
        fields[fieldName] = getChoice(LANGUAGE_CODES_MAP, mapChoice=True)
      elif fieldName == CONTACT_NOTES:
        if checkArgumentPresent(FILE_ARGUMENT):
          fields[fieldName] = readFile(getString(OB_FILE_NAME), encoding=GM_Globals[GM_SYS_ENCODING])
        else:
          fields[fieldName] = getString(OB_STRING, emptyOK=True)
      elif fieldName == CONTACT_ADDRESSES:
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          ClearFieldsList(fieldName)
          continue
        address = InitArrayItem(ContactsManager.ADDRESS_TYPE_ARGUMENT_TO_REL)
        address[u'primary'] = u'false'
        while CL_argvI < CL_argvLen:
          argument = getArgument()
          if argument in ContactsManager.ADDRESS_ARGUMENT_TO_FIELD_MAP:
            address[ContactsManager.ADDRESS_ARGUMENT_TO_FIELD_MAP[argument]] = getString(OB_STRING, emptyOK=True)
          elif argument in ContactsManager.PRIMARY_NOTPRIMARY_CHOICE_MAP:
            address[u'primary'] = ContactsManager.PRIMARY_NOTPRIMARY_CHOICE_MAP[argument]
            break
          else:
            unknownArgumentExit()
        AppendItemToFieldsList(fieldName, address)
      elif fieldName == CONTACT_CALENDARS:
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          ClearFieldsList(fieldName)
          continue
        calendarLink = InitArrayItem(ContactsManager.CALENDAR_TYPE_ARGUMENT_TO_REL)
        calendarLink[u'value'] = getString(OB_STRING)
        calendarLink[u'primary'] = getChoice(ContactsManager.PRIMARY_NOTPRIMARY_CHOICE_MAP, mapChoice=True)
        AppendItemToFieldsList(fieldName, calendarLink)
      elif fieldName == CONTACT_EMAILS:
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          ClearFieldsList(fieldName)
          continue
        email = InitArrayItem(ContactsManager.EMAIL_TYPE_ARGUMENT_TO_REL)
        email[u'value'] = getEmailAddress(noUid=True)
        email[u'primary'] = getChoice(ContactsManager.PRIMARY_NOTPRIMARY_CHOICE_MAP, mapChoice=True)
        AppendItemToFieldsList(fieldName, email)
      elif fieldName == CONTACT_EVENTS:
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          ClearFieldsList(fieldName)
          continue
        event = InitArrayItem(ContactsManager.EVENT_TYPE_ARGUMENT_TO_REL)
        event[u'value'] = getYYYYMMDD()
        AppendItemToFieldsList(fieldName, event)
      elif fieldName == CONTACT_EXTERNALIDS:
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          ClearFieldsList(fieldName)
          continue
        externalid = InitArrayItem(ContactsManager.EXTERNALID_TYPE_ARGUMENT_TO_REL)
        externalid[u'value'] = getString(OB_STRING)
        AppendItemToFieldsList(fieldName, externalid)
      elif fieldName == CONTACT_HOBBIES:
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          ClearFieldsList(fieldName)
          continue
        hobby = {u'value': getString(OB_STRING)}
        AppendItemToFieldsList(fieldName, hobby)
      elif fieldName == CONTACT_IMS:
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          ClearFieldsList(fieldName)
          continue
        im = InitArrayItem(ContactsManager.IM_TYPE_ARGUMENT_TO_REL)
        im[u'protocol'] = getChoice(ContactsManager.IM_PROTOCOL_TO_REL_MAP, mapChoice=True)
        im[u'value'] = getString(OB_STRING)
        im[u'primary'] = getChoice(ContactsManager.PRIMARY_NOTPRIMARY_CHOICE_MAP, mapChoice=True)
        AppendItemToFieldsList(fieldName, im)
      elif fieldName == CONTACT_JOTS:
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          ClearFieldsList(fieldName)
          continue
        jot = {u'rel': getChoice(ContactsManager.JOT_TYPE_ARGUMENT_TO_REL, mapChoice=True)}
        jot[u'value'] = getString(OB_STRING)
        AppendItemToFieldsList(fieldName, jot)
      elif fieldName == CONTACT_ORGANIZATIONS:
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          ClearFieldsList(fieldName)
          continue
        organization = InitArrayItem(ContactsManager.ORGANIZATION_TYPE_ARGUMENT_TO_REL)
        organization[u'primary'] = u'false'
        organization[u'value'] = getString(OB_STRING)
        while CL_argvI < CL_argvLen:
          argument = getArgument()
          if argument in ContactsManager.ORGANIZATION_ARGUMENT_TO_FIELD_MAP:
            organization[ContactsManager.ORGANIZATION_ARGUMENT_TO_FIELD_MAP[argument]] = getString(OB_STRING, emptyOK=True)
          elif argument in ContactsManager.PRIMARY_NOTPRIMARY_CHOICE_MAP:
            organization[u'primary'] = ContactsManager.PRIMARY_NOTPRIMARY_CHOICE_MAP[argument]
            break
          else:
            unknownArgumentExit()
        AppendItemToFieldsList(fieldName, organization)
      elif fieldName == CONTACT_PHONES:
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          ClearFieldsList(fieldName)
          continue
        phone = InitArrayItem(ContactsManager.PHONE_TYPE_ARGUMENT_TO_REL)
        phone[u'value'] = getString(OB_STRING)
        phone[u'primary'] = getChoice(ContactsManager.PRIMARY_NOTPRIMARY_CHOICE_MAP, mapChoice=True)
        AppendItemToFieldsList(fieldName, phone)
      elif fieldName == CONTACT_RELATIONS:
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          ClearFieldsList(fieldName)
          continue
        relation = InitArrayItem(ContactsManager.RELATION_TYPE_ARGUMENT_TO_REL)
        relation[u'value'] = getString(OB_STRING)
        AppendItemToFieldsList(fieldName, relation)
      elif fieldName == CONTACT_USER_DEFINED_FIELDS:
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          ClearFieldsList(fieldName)
          continue
        userdefinedfield = {u'rel': getString(OB_STRING), u'value': getString(OB_STRING, emptyOK=True)}
        AppendItemToFieldsList(fieldName, userdefinedfield)
      elif fieldName == CONTACT_WEBSITES:
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          ClearFieldsList(fieldName)
          continue
        website = InitArrayItem(ContactsManager.WEBSITE_TYPE_ARGUMENT_TO_REL)
        website[u'value'] = getString(OB_STRING)
        website[u'primary'] = getChoice(ContactsManager.PRIMARY_NOTPRIMARY_CHOICE_MAP, mapChoice=True)
        AppendItemToFieldsList(fieldName, website)
      elif fieldName == CONTACT_GROUPS:
        if entityType != EN_USER:
          putArgumentBack()
          unknownArgumentExit()
        AppendItemToFieldsList(CONTACT_GROUPS_LIST, getString(OB_STRING))
      else:
        fields[fieldName] = getString(OB_STRING, emptyOK=True)
    return fields

  @staticmethod
  def FieldsToContact(fields):
    import gdata.apps.contacts

    def GetField(fieldName):
      return fields.get(fieldName)

    def SetClassAttribute(value, fieldClass, processNLs, attr):
      if value:
        if processNLs:
          value = value.replace(u'\\n', u'\n')
        if attr == u'text':
          return fieldClass(text=value)
        if attr == u'code':
          return fieldClass(code=value)
        if attr == u'rel':
          return fieldClass(rel=value)
        if attr == u'value':
          return fieldClass(value=value)
        if attr == u'value_string':
          return fieldClass(value_string=value)
        if attr == u'when':
          return fieldClass(when=value)
      return None

    def GetContactField(fieldName, fieldClass, processNLs=False, attr=u'text'):
      return SetClassAttribute(fields.get(fieldName), fieldClass, processNLs, attr)

    def GetListEntryField(entry, fieldName, fieldClass, processNLs=False, attr=u'text'):
      return SetClassAttribute(entry.get(fieldName), fieldClass, processNLs, attr)

    contactEntry = gdata.apps.contacts.ContactEntry()
    value = GetField(CONTACT_NAME)
    if not value:
      value = u' '.join([fields[fieldName] for fieldName in ContactsManager.CONTACT_NAME_FIELDS if fieldName in fields])
    contactEntry.name = gdata.apps.contacts.Name(full_name=gdata.apps.contacts.FullName(text=value))
    contactEntry.name.name_prefix = GetContactField(CONTACT_NAME_PREFIX, gdata.apps.contacts.NamePrefix)
    contactEntry.name.given_name = GetContactField(CONTACT_GIVEN_NAME, gdata.apps.contacts.GivenName)
    contactEntry.name.additional_name = GetContactField(CONTACT_ADDITIONAL_NAME, gdata.apps.contacts.AdditionalName)
    contactEntry.name.family_name = GetContactField(CONTACT_FAMILY_NAME, gdata.apps.contacts.FamilyName)
    contactEntry.name.name_suffix = GetContactField(CONTACT_NAME_SUFFIX, gdata.apps.contacts.NameSuffix)
    contactEntry.nickname = GetContactField(CONTACT_NICKNAME, gdata.apps.contacts.Nickname)
    contactEntry.maidenName = GetContactField(CONTACT_MAIDENNAME, gdata.apps.contacts.MaidenName)
    contactEntry.shortName = GetContactField(CONTACT_SHORTNAME, gdata.apps.contacts.ShortName)
    contactEntry.initials = GetContactField(CONTACT_INITIALS, gdata.apps.contacts.Initials)
    contactEntry.birthday = GetContactField(CONTACT_BIRTHDAY, gdata.apps.contacts.Birthday, attr=u'when')
    contactEntry.gender = GetContactField(CONTACT_GENDER, gdata.apps.contacts.Gender, attr=u'value')
    contactEntry.where = GetContactField(CONTACT_LOCATION, gdata.apps.contacts.Where, attr=u'value_string')
    contactEntry.priority = GetContactField(CONTACT_PRIORITY, gdata.apps.contacts.Priority, attr=u'rel')
    contactEntry.sensitivity = GetContactField(CONTACT_SENSITIVITY, gdata.apps.contacts.Sensitivity, attr=u'rel')
    contactEntry.subject = GetContactField(CONTACT_SUBJECT, gdata.apps.contacts.Subject)
    contactEntry.language = GetContactField(CONTACT_LANGUAGE, gdata.apps.contacts.Language, attr=u'code')
    contactEntry.content = GetContactField(CONTACT_NOTES, gdata.apps.contacts.Content, processNLs=True)
    contactEntry.occupation = GetContactField(CONTACT_OCCUPATION, gdata.apps.contacts.Occupation)
    contactEntry.billingInformation = GetContactField(CONTACT_BILLING_INFORMATION, gdata.apps.contacts.BillingInformation, processNLs=True)
    contactEntry.mileage = GetContactField(CONTACT_MILEAGE, gdata.apps.contacts.Mileage)
    contactEntry.directoryServer = GetContactField(CONTACT_DIRECTORY_SERVER, gdata.apps.contacts.DirectoryServer)
    value = GetField(CONTACT_ADDRESSES)
    if value:
      for address in value:
        street = GetListEntryField(address, u'street', gdata.apps.contacts.Street)
        pobox = GetListEntryField(address, u'pobox', gdata.apps.contacts.PoBox)
        neighborhood = GetListEntryField(address, u'neighborhood', gdata.apps.contacts.Neighborhood)
        city = GetListEntryField(address, u'city', gdata.apps.contacts.City)
        region = GetListEntryField(address, u'region', gdata.apps.contacts.Region)
        postcode = GetListEntryField(address, u'postcode', gdata.apps.contacts.Postcode)
        country = GetListEntryField(address, u'country', gdata.apps.contacts.Country)
        formatted_address = GetListEntryField(address, u'value', gdata.apps.contacts.FormattedAddress, processNLs=True)
        contactEntry.structuredPostalAddress.append(gdata.apps.contacts.StructuredPostalAddress(street=street, pobox=pobox, neighborhood=neighborhood,
                                                                                                city=city, region=region,
                                                                                                postcode=postcode, country=country,
                                                                                                formatted_address=formatted_address,
                                                                                                rel=address[u'rel'], label=address[u'label'], primary=address[u'primary']))
    value = GetField(CONTACT_CALENDARS)
    if value:
      for calendarLink in value:
        contactEntry.calendarLink.append(gdata.apps.contacts.CalendarLink(href=calendarLink[u'value'], rel=calendarLink[u'rel'], label=calendarLink[u'label'], primary=calendarLink[u'primary']))
    value = GetField(CONTACT_EMAILS)
    if value:
      for email in value:
        contactEntry.email.append(gdata.apps.contacts.Email(address=email[u'value'], rel=email[u'rel'], label=email[u'label'], primary=email[u'primary']))
    value = GetField(CONTACT_EXTERNALIDS)
    if value:
      for externalid in value:
        contactEntry.externalId.append(gdata.apps.contacts.ExternalId(value=externalid[u'value'], rel=externalid[u'rel'], label=externalid[u'label']))
    value = GetField(CONTACT_EVENTS)
    if value:
      for event in value:
        contactEntry.event.append(gdata.apps.contacts.Event(rel=event[u'rel'], label=event[u'label'],
                                                            when=gdata.apps.contacts.When(startTime=event[u'value'])))
    value = GetField(CONTACT_HOBBIES)
    if value:
      for hobby in value:
        contactEntry.hobby.append(gdata.apps.contacts.Hobby(text=hobby[u'value']))
    value = GetField(CONTACT_IMS)
    if value:
      for im in value:
        contactEntry.im.append(gdata.apps.contacts.IM(address=im[u'value'], protocol=im[u'protocol'], rel=im[u'rel'], label=im[u'label'], primary=im[u'primary']))
    value = GetField(CONTACT_JOTS)
    if value:
      for jot in value:
        contactEntry.jot.append(gdata.apps.contacts.Jot(text=jot[u'value'], rel=jot[u'rel']))
    value = GetField(CONTACT_ORGANIZATIONS)
    if value:
      for organization in value:
        org_name = gdata.apps.contacts.OrgName(text=organization[u'value'])
        department = GetListEntryField(organization, u'department', gdata.apps.contacts.OrgDepartment)
        title = GetListEntryField(organization, u'title', gdata.apps.contacts.OrgTitle)
        job_description = GetListEntryField(organization, u'jobdescription', gdata.apps.contacts.OrgJobDescription)
        symbol = GetListEntryField(organization, u'symbol', gdata.apps.contacts.OrgSymbol)
        where = GetListEntryField(organization, u'where', gdata.apps.contacts.Where, attr=u'value_string')
        contactEntry.organization.append(gdata.apps.contacts.Organization(name=org_name, department=department,
                                                                          title=title, job_description=job_description,
                                                                          symbol=symbol, where=where,
                                                                          rel=organization[u'rel'], label=organization[u'label'], primary=organization[u'primary']))
    value = GetField(CONTACT_PHONES)
    if value:
      for phone in value:
        contactEntry.phoneNumber.append(gdata.apps.contacts.PhoneNumber(text=phone[u'value'], rel=phone[u'rel'], label=phone[u'label'], primary=phone[u'primary']))
    value = GetField(CONTACT_RELATIONS)
    if value:
      for relation in value:
        contactEntry.relation.append(gdata.apps.contacts.Relation(text=relation[u'value'], rel=relation[u'rel'], label=relation[u'label']))
    value = GetField(CONTACT_USER_DEFINED_FIELDS)
    if value:
      for userdefinedfield in value:
        contactEntry.userDefinedField.append(gdata.apps.contacts.UserDefinedField(key=userdefinedfield[u'rel'], value=userdefinedfield[u'value']))
    value = GetField(CONTACT_WEBSITES)
    if value:
      for website in value:
        contactEntry.website.append(gdata.apps.contacts.Website(href=website[u'value'], rel=website[u'rel'], label=website[u'label'], primary=website[u'primary']))
    return contactEntry

  @staticmethod
  def AddContactGroupsToContact(contactsObject, contactEntry, contactGroupsList, user):
    import gdata.apps.contacts

    contactEntry.groupMembershipInfo = []
    for groupId in contactGroupsList:
      if groupId != u'clear':
        contactEntry.groupMembershipInfo.append(gdata.apps.contacts.GroupMembershipInfo(deleted=u'false',
                                                                                        href=contactsObject.GetContactGroupFeedUri(contact_list=user, projection=u'base', groupId=groupId)))
      else:
        contactEntry.groupMembershipInfo = []

  @staticmethod
  def ContactToFields(contactEntry):
    fields = {}

    def GetContactField(fieldName, attrlist):
      objAttr = contactEntry
      for attr in attrlist:
        objAttr = getattr(objAttr, attr)
        if not objAttr:
          return
      fields[fieldName] = objAttr

    def GetListEntryField(entry, attrlist):
      objAttr = entry
      for attr in attrlist:
        objAttr = getattr(objAttr, attr)
        if not objAttr:
          return None
      return objAttr

    def AppendItemToFieldsList(fieldName, fieldValue):
      fields.setdefault(fieldName, [])
      fields[fieldName].append(fieldValue)

    fields[CONTACT_ID] = ContactsManager.GetContactShortId(contactEntry)
    GetContactField(CONTACT_UPDATED, [u'updated', u'text'])
    if not contactEntry.deleted:
      GetContactField(CONTACT_NAME, [u'title', u'text'])
    else:
      fields[CONTACT_NAME] = u'Deleted'
    GetContactField(CONTACT_NAME_PREFIX, [u'name', u'name_prefix', u'text'])
    GetContactField(CONTACT_GIVEN_NAME, [u'name', u'given_name', u'text'])
    GetContactField(CONTACT_ADDITIONAL_NAME, [u'name', u'additional_name', u'text'])
    GetContactField(CONTACT_FAMILY_NAME, [u'name', u'family_name', u'text'])
    GetContactField(CONTACT_NAME_SUFFIX, [u'name', u'name_suffix', u'text'])
    GetContactField(CONTACT_NICKNAME, [u'nickname', u'text'])
    GetContactField(CONTACT_MAIDENNAME, [u'maidenName', u'text'])
    GetContactField(CONTACT_SHORTNAME, [u'shortName', u'text'])
    GetContactField(CONTACT_INITIALS, [u'initials', u'text'])
    GetContactField(CONTACT_BIRTHDAY, [u'birthday', u'when'])
    GetContactField(CONTACT_GENDER, [u'gender', u'value'])
    GetContactField(CONTACT_SUBJECT, [u'subject', u'text'])
    GetContactField(CONTACT_LANGUAGE, [u'language', u'code'])
    GetContactField(CONTACT_PRIORITY, [u'priority', u'rel'])
    GetContactField(CONTACT_SENSITIVITY, [u'sensitivity', u'rel'])
    GetContactField(CONTACT_NOTES, [u'content', u'text'])
    GetContactField(CONTACT_LOCATION, [u'where', u'value_string'])
    GetContactField(CONTACT_OCCUPATION, [u'occupation', u'text'])
    GetContactField(CONTACT_BILLING_INFORMATION, [u'billingInformation', u'text'])
    GetContactField(CONTACT_MILEAGE, [u'mileage', u'text'])
    GetContactField(CONTACT_DIRECTORY_SERVER, [u'directoryServer', u'text'])
    for address in contactEntry.structuredPostalAddress:
      AppendItemToFieldsList(CONTACT_ADDRESSES,
                             {u'rel': address.rel,
                              u'label': address.label,
                              u'value': GetListEntryField(address, [u'formatted_address', u'text']),
                              u'street': GetListEntryField(address, [u'street', u'text']),
                              u'pobox': GetListEntryField(address, [u'pobox', u'text']),
                              u'neighborhood': GetListEntryField(address, [u'neighborhood', u'text']),
                              u'city': GetListEntryField(address, [u'city', u'text']),
                              u'region': GetListEntryField(address, [u'region', u'text']),
                              u'postcode': GetListEntryField(address, [u'postcode', u'text']),
                              u'country': GetListEntryField(address, [u'country', u'text']),
                              u'primary': address.primary})
    for calendarLink in contactEntry.calendarLink:
      AppendItemToFieldsList(CONTACT_CALENDARS,
                             {u'rel': calendarLink.rel,
                              u'label': calendarLink.label,
                              u'value': calendarLink.href,
                              u'primary': calendarLink.primary})
    for email in contactEntry.email:
      AppendItemToFieldsList(CONTACT_EMAILS,
                             {u'rel': email.rel,
                              u'label': email.label,
                              u'value': email.address,
                              u'primary': email.primary})
    for externalid in contactEntry.externalId:
      AppendItemToFieldsList(CONTACT_EXTERNALIDS,
                             {u'rel': externalid.rel,
                              u'label': externalid.label,
                              u'value': externalid.value})
    for event in contactEntry.event:
      AppendItemToFieldsList(CONTACT_EVENTS,
                             {u'rel': event.rel,
                              u'label': event.label,
                              u'value': GetListEntryField(event, [u'when', u'startTime'])})
    for hobby in contactEntry.hobby:
      AppendItemToFieldsList(CONTACT_HOBBIES,
                             {u'value': hobby.text})
    for im in contactEntry.im:
      AppendItemToFieldsList(CONTACT_IMS,
                             {u'rel': im.rel,
                              u'label': im.label,
                              u'value': im.address,
                              u'protocol': im.protocol,
                              u'primary': im.primary})
    for jot in contactEntry.jot:
      AppendItemToFieldsList(CONTACT_JOTS,
                             {u'rel': jot.rel,
                              u'value': jot.text})
    for organization in contactEntry.organization:
      AppendItemToFieldsList(CONTACT_ORGANIZATIONS,
                             {u'rel': organization.rel,
                              u'label': organization.label,
                              u'value': GetListEntryField(organization, [u'name', u'text']),
                              u'department': GetListEntryField(organization, [u'department', u'text']),
                              u'title': GetListEntryField(organization, [u'title', u'text']),
                              u'symbol': GetListEntryField(organization, [u'symbol', u'text']),
                              u'jobdescription': GetListEntryField(organization, [u'job_description', u'text']),
                              u'where': GetListEntryField(organization, [u'where', u'value_string']),
                              u'primary': organization.primary})
    for phone in contactEntry.phoneNumber:
      AppendItemToFieldsList(CONTACT_PHONES,
                             {u'rel': phone.rel,
                              u'label': phone.label,
                              u'value': phone.text,
                              u'primary': phone.primary})
    for relation in contactEntry.relation:
      AppendItemToFieldsList(CONTACT_RELATIONS,
                             {u'rel': relation.rel,
                              u'label': relation.label,
                              u'value': relation.text})
    for userdefinedfield in contactEntry.userDefinedField:
      AppendItemToFieldsList(CONTACT_USER_DEFINED_FIELDS,
                             {u'rel': userdefinedfield.key,
                              u'value': userdefinedfield.value})
    for website in contactEntry.website:
      AppendItemToFieldsList(CONTACT_WEBSITES,
                             {u'rel': website.rel,
                              u'label': website.label,
                              u'value': website.href,
                              u'primary': website.primary})
    for group in contactEntry.groupMembershipInfo:
      AppendItemToFieldsList(CONTACT_GROUPS, group.href[group.href.rfind(u'/')+1:])
    return fields

  @staticmethod
  def GetContactGroupFields():

    fields = {}
    while CL_argvI < CL_argvLen:
      fieldName = getChoice(ContactsManager.CONTACT_GROUP_ARGUMENT_TO_PROPERTY_MAP, mapChoice=True)
      if fieldName == CONTACT_GROUP_NAME:
        fields[fieldName] = getString(OB_STRING)
      else:
        fields[fieldName] = getString(OB_STRING, emptyOK=True)
    if not fields.get(CONTACT_GROUP_NAME):
      missingArgumentExit(u'name')
    return fields

  @staticmethod
  def FieldsToContactGroup(fields):
    import atom
    import gdata.apps.contacts

    groupEntry = gdata.apps.contacts.GroupEntry(title=atom.Title(text=fields[CONTACT_GROUP_NAME]))
    return groupEntry

  @staticmethod
  def ContactGroupToFields(groupEntry):
    fields = {}

    def GetGroupField(fieldName, attrlist):
      objAttr = groupEntry
      for attr in attrlist:
        objAttr = getattr(objAttr, attr)
        if not objAttr:
          return
      fields[fieldName] = objAttr

    fields[CONTACT_GROUP_ID] = ContactsManager.GetContactShortId(groupEntry)
    GetGroupField(CONTACT_GROUP_UPDATED, [u'updated', u'text'])
    if not groupEntry.deleted:
      GetGroupField(CONTACT_GROUP_NAME, [u'title', u'text'])
    else:
      fields[CONTACT_GROUP_NAME] = u'Deleted'
    return fields

CONTACTS_PROJECTION_CHOICES_MAP = {u'basic': u'thin', u'thin': u'thin', u'full': u'full',}
CONTACTS_ORDERBY_CHOICES_MAP = {u'lastmodified': u'lastmodified',}

def normalizeContactId(contactId):
  if contactId.startswith(u'id:'):
    return contactId[3:]
  return contactId

def _initContactQueryAttributes():
  return {u'query': None, u'projection': u'full', u'url_params': {u'max-results': str(GC_Values[GC_CONTACT_MAX_RESULTS])}, u'contactGroup': None, u'group': None, u'emailMatchPattern': None, u'emailMatchType': None}

def _getContactQueryAttributes(contactQuery, myarg, entityType, allowOutputAttributes):
  if myarg == u'query':
    contactQuery[u'query'] = getString(OB_QUERY)
  elif myarg == u'contactgroup':
    if entityType == EN_USER:
      contactQuery[u'contactGroup'] = getString(OB_CONTACT_GROUP_ITEM)
    else:
      unknownArgumentExit()
  elif myarg == u'emailmatchpattern':
    contactQuery[u'emailMatchPattern'] = getREPattern()
  elif myarg == u'emailmatchtype':
    contactQuery[u'emailMatchType'] = getString(OB_CONTACT_EMAIL_TYPE)
  elif myarg == u'updatedmin':
    contactQuery[u'url_params'][u'updated-min'] = getYYYYMMDD()
  elif not allowOutputAttributes:
    unknownArgumentExit()
  elif myarg == u'orderby':
    contactQuery[u'url_params'][u'orderby'] = getChoice(CONTACTS_ORDERBY_CHOICES_MAP, mapChoice=True)
    contactQuery[u'url_params'][u'sortorder'] = getChoice(SORTORDER_CHOICES_MAP, defaultChoice=u'ascending')
  elif myarg in CONTACTS_PROJECTION_CHOICES_MAP:
    contactQuery[u'projection'] = CONTACTS_PROJECTION_CHOICES_MAP[myarg]
  elif myarg == u'showdeleted':
    contactQuery[u'url_params'][u'showdeleted'] = u'true'
  else:
    unknownArgumentExit()

def queryContacts(contactsObject, contactQuery, entityType, user, i=0, count=0):
  if contactQuery[u'query'] or contactQuery[u'group']:
    uri = getContactsQuery(feed=contactsObject.GetContactFeedUri(contact_list=user, projection=contactQuery[u'projection']),
                           text_query=contactQuery[u'query'], group=contactQuery[u'group']).ToUri()
  else:
    uri = contactsObject.GetContactFeedUri(contact_list=user, projection=contactQuery[u'projection'])
  printGettingAllEntityItemsForWhom(EN_CONTACT, user, i, count, qualifier=queryQualifier(contactQuery[u'query']))
  page_message = getPageMessage()
  try:
    entityList = callGDataPages(contactsObject, u'GetContactsFeed',
                                page_message=page_message,
                                throw_errors=[GDATA_BAD_REQUEST, GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                                retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                                uri=uri, url_params=contactQuery[u'url_params'])
    return entityList
  except GData_badRequest:
    entityItemValueActionFailedWarning(entityType, user, EN_CONTACT, u'', PHRASE_BAD_REQUEST, i, count)
  except GData_forbidden:
    entityServiceNotApplicableWarning(entityType, user, i, count)
  except GData_serviceNotApplicable:
    entityUnknownWarning(entityType, user, i, count)
  return None

def contactEmailAddressMatches(contactsManager, contactQuery, fields):
  emailMatchType = contactQuery[u'emailMatchType']
  for item in fields.get(CONTACT_EMAILS, []):
    if contactQuery[u'emailMatchPattern'].match(item[u'value']):
      if not emailMatchType or emailMatchType == item.get(u'label') or emailMatchType == contactsManager.CONTACT_ARRAY_PROPERTIES[CONTACT_EMAILS][u'relMap'].get(item[u'rel'], u'custom'):
        return True
  return False

def getContactGroupsInfo(contactsManager, contactsObject, entityType, entityName, i, count):
  uri = contactsObject.GetContactGroupFeedUri(contact_list=entityName)
  contactGroupIDs = {}
  contactGroupNames = {}
  try:
    groups = callGDataPages(contactsObject, u'GetGroupsFeed',
                            throw_errors=[GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                            retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                            uri=uri)
    if groups:
      for group in groups:
        fields = contactsManager.ContactGroupToFields(group)
        contactGroupIDs[fields[CONTACT_GROUP_ID]] = fields[CONTACT_GROUP_NAME]
        contactGroupNames.setdefault(fields[CONTACT_GROUP_NAME], [])
        contactGroupNames[fields[CONTACT_GROUP_NAME]].append(fields[CONTACT_GROUP_ID])
  except GData_forbidden:
    entityServiceNotApplicableWarning(entityType, entityName, i, count)
    return (contactGroupIDs, False)
  except GData_serviceNotApplicable:
    entityUnknownWarning(entityType, entityName, i, count)
    return (contactGroupIDs, False)
  return (contactGroupIDs, contactGroupNames)

def validateContactGroup(contactsManager, contactsObject, contactGroupName, contactGroupIDs, contactGroupNames, entityType, entityName, i, count):
  if not contactGroupNames:
    contactGroupIDs, contactGroupNames = getContactGroupsInfo(contactsManager, contactsObject, entityType, entityName, i, count)
    if contactGroupNames == False:
      return (None, contactGroupIDs, contactGroupNames)
  if contactGroupName == u'clear':
    return (contactGroupName, contactGroupIDs, contactGroupNames)
  cg = UID_PATTERN.match(contactGroupName)
  if cg:
    if cg.group(1) in contactGroupIDs:
      return (cg.group(1), contactGroupIDs, contactGroupNames)
  else:
    if contactGroupName in contactGroupNames:
      return (contactGroupNames[contactGroupName][0], contactGroupIDs, contactGroupNames)
  return (None, contactGroupIDs, contactGroupNames)

def validateContactGroupsList(contactsManager, contactsObject, contactId, fields, entityType, entityName, i, count):
  result = True
  contactGroupIDs = contactGroupNames = None
  contactGroupsList = []
  for contactGroup in fields[CONTACT_GROUPS_LIST]:
    groupId, contactGroupIDs, contactGroupNames = validateContactGroup(contactsManager, contactsObject, contactGroup, contactGroupIDs, contactGroupNames, entityType, entityName, i, count)
    if groupId:
      contactGroupsList.append(groupId)
    else:
      if contactGroupNames:
        entityItemValueActionNotPerformedWarning(entityType, entityName, EN_CONTACT, contactId, entityTypeNameMessage(EN_CONTACT_GROUP, contactGroup, PHRASE_DOES_NOT_EXIST))
      result = False
  return (result, contactGroupsList)

# gam <UserTypeEntity> create contact <ContactAttributes>+
def createUserContact(users):
  doCreateContact(users, EN_USER)

# gam create contact <ContactAttributes>+
def doCreateDomainContact():
  doCreateContact([GC_Values[GC_DOMAIN],], EN_DOMAIN)

def doCreateContact(users, entityType):
  contactsManager = ContactsManager()
  fields = contactsManager.GetContactFields(entityType)
  contactEntry = contactsManager.FieldsToContact(fields)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, contactsObject = getContactsObject(entityType, user, i, count)
    if not contactsObject:
      continue
    if fields.get(CONTACT_GROUPS_LIST):
      result, contactGroupsList = validateContactGroupsList(contactsManager, contactsObject, u'', fields, entityType, user, i, count)
      if not result:
        continue
      contactsManager.AddContactGroupsToContact(contactsObject, contactEntry, contactGroupsList, user)
    try:
      contact = callGData(contactsObject, u'CreateContact',
                          throw_errors=[GDATA_BAD_REQUEST, GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                          retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                          new_contact=contactEntry, insert_uri=contactsObject.GetContactFeedUri(contact_list=user))
      entityItemValueActionPerformed(entityType, user, EN_CONTACT, contactsManager.GetContactShortId(contact), i, count)
    except GData_badRequest:
      entityItemValueActionFailedWarning(entityType, user, EN_CONTACT, u'', PHRASE_BAD_REQUEST, i, count)
    except GData_forbidden:
      entityServiceNotApplicableWarning(entityType, user, i, count)
    except GData_serviceNotApplicable:
      entityUnknownWarning(entityType, user, i, count)

# gam <UserTypeEntity> update contacts <ContactEntity> [contactgroup <ContactGroupItem>] <ContactAttributes>+
def updateUserContacts(users):
  doUpdateContacts(users, EN_USER)

# gam update contacts <ContactEntity> <ContactAttributes>+
def doUpdateDomainContacts():
  doUpdateContacts([GC_Values[GC_DOMAIN],], EN_DOMAIN)

def doUpdateContacts(users, entityType):
  contactsManager = ContactsManager()
  entityList = getEntityList(OB_CONTACT_ENTITY)
  update_fields = contactsManager.GetContactFields(entityType)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, contactsObject = getContactsObject(entityType, user, i, count)
    if not contactsObject:
      continue
    j = 0
    jcount = len(entityList)
    entityPerformActionNumItems(entityType, user, jcount, EN_CONTACT, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    contactGroupsList = None
    incrementIndentLevel()
    for contactId in entityList:
      j += 1
      contactId = normalizeContactId(contactId)
      if update_fields.get(CONTACT_GROUPS_LIST) and not contactGroupsList:
        result, contactGroupsList = validateContactGroupsList(contactsManager, contactsObject, contactId, update_fields, entityType, user, i, count)
        if not result:
          break
      try:
        contact = callGData(contactsObject, u'GetContact',
                            throw_errors=[GDATA_NOT_FOUND, GDATA_BAD_REQUEST, GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                            retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                            uri=contactsObject.GetContactFeedUri(contact_list=user, contactId=contactId))
        fields = contactsManager.ContactToFields(contact)
        for field in update_fields:
          fields[field] = update_fields[field]
        contactEntry = contactsManager.FieldsToContact(fields)
        if contactGroupsList:
          contactsManager.AddContactGroupsToContact(contactsObject, contactEntry, contactGroupsList, user)
        elif fields.get(CONTACT_GROUPS):
          contactsManager.AddContactGroupsToContact(contactsObject, contactEntry, fields[CONTACT_GROUPS], user)
        contactEntry.category = contact.category
        contactEntry.link = contact.link
        contactEntry.etag = contact.etag
        contactEntry.id = contact.id
        callGData(contactsObject, u'UpdateContact',
                  throw_errors=[GDATA_NOT_FOUND, GDATA_BAD_REQUEST, GDATA_PRECONDITION_FAILED, GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                  edit_uri=contactsObject.GetContactFeedUri(contact_list=user, contactId=contactId), updated_contact=contactEntry, extra_headers={u'If-Match': contact.etag})
        entityItemValueActionPerformed(entityType, user, EN_CONTACT, contactId, j, jcount)
      except GData_notFound:
        entityItemValueActionFailedWarning(entityType, user, EN_CONTACT, contactId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except GData_badRequest:
        entityItemValueActionFailedWarning(entityType, user, EN_CONTACT, contactId, PHRASE_BAD_REQUEST, j, jcount)
      except GData_preconditionFailed as e:
        entityItemValueActionFailedWarning(entityType, user, EN_CONTACT, contactId, e.message, j, jcount)
      except GData_forbidden:
        entityServiceNotApplicableWarning(entityType, user, i, count)
        break
      except GData_serviceNotApplicable:
        entityUnknownWarning(entityType, user, i, count)
        break
    decrementIndentLevel()

# gam <UserTypeEntity> delete contacts <ContactEntity>|([query <QueryContact>] [contactgroup <ContactGroupItem>] [emailmatchpattern <RegularExpression>] [updated_min yyyy-mm-dd])
def deleteUserContacts(users):
  doDeleteContacts(users, EN_USER)

# gam delete contacts <ContactEntity>|([query <QueryContact>] [emailmatchpattern <RegularExpression>] [updated_min yyyy-mm-dd])
def doDeleteDomainContacts():
  doDeleteContacts([GC_Values[GC_DOMAIN],], EN_DOMAIN)

def doDeleteContacts(users, entityType):
  contactsManager = ContactsManager()
  contactQuery = _initContactQueryAttributes()
  if peekArgumentPresent([u'query', u'contactgroup', u'emailmatchpattern', u'updated_min']):
    entityList = None
    while CL_argvI < CL_argvLen:
      myarg = getArgument()
      _getContactQueryAttributes(contactQuery, myarg, entityType, False)
  else:
    entityList = getEntityList(OB_CONTACT_ENTITY)
  contactIdLists = entityList if isinstance(entityList, dict) else None
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if contactIdLists:
      entityList = contactIdLists[user]
    user, contactsObject = getContactsObject(entityType, user, i, count)
    if not contactsObject:
      continue
    if contactQuery[u'contactGroup']:
      groupId, _, contactGroupNames = validateContactGroup(contactsManager, contactsObject, contactQuery[u'contactGroup'], None, None, entityType, user, i, count)
      if not groupId:
        if contactGroupNames:
          entityItemValueActionFailedWarning(entityType, user, EN_CONTACT_GROUP, contactQuery[u'contactGroup'], PHRASE_DOES_NOT_EXIST, i, count)
        continue
      contactQuery[u'group'] = contactsObject.GetContactGroupFeedUri(contact_list=user, projection=u'base', groupId=groupId)
    if contactQuery[u'query'] or contactQuery[u'group']:
      entityList = queryContacts(contactsObject, contactQuery, entityType, user, i, count)
      if entityList == None:
        continue
    j = 0
    jcount = len(entityList)
    entityPerformActionModifierNumItems(entityType, user, PHRASE_MAXIMUM_OF, jcount, EN_CONTACT, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    for contact in entityList:
      j += 1
      try:
        if not contactQuery[u'query'] and not contactQuery[u'group']:
          contactId = normalizeContactId(contact)
          contact = callGData(contactsObject, u'GetContact',
                              throw_errors=[GDATA_NOT_FOUND, GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                              retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                              uri=contactsObject.GetContactFeedUri(contact_list=user, contactId=contactId))
        else:
          contactId = contactsManager.GetContactShortId(contact)
          fields = contactsManager.ContactToFields(contact)
          if contactQuery[u'emailMatchPattern'] and not contactEmailAddressMatches(contactsManager, contactQuery, fields):
            continue
        callGData(contactsObject, u'DeleteContact',
                  throw_errors=[GDATA_NOT_FOUND, GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                  edit_uri=contactsObject.GetContactFeedUri(contact_list=user, contactId=contactId), extra_headers={u'If-Match': contact.etag})
        entityItemValueActionPerformed(entityType, user, EN_CONTACT, contactId, j, jcount)
      except GData_notFound:
        entityItemValueActionFailedWarning(entityType, user, EN_CONTACT, contactId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except GData_forbidden:
        entityServiceNotApplicableWarning(entityType, user, i, count)
        break
      except GData_serviceNotApplicable:
        entityUnknownWarning(entityType, user, i, count)
        break
    decrementIndentLevel()

def _showContact(contactsManager, fields, displayFieldsList, contactGroupIDs, j, jcount):
  printEntityName(EN_CONTACT, fields[CONTACT_ID], j, jcount)
  incrementIndentLevel()
  for key in contactsManager.CONTACT_NAME_PROPERTY_PRINT_ORDER:
    if displayFieldsList and key not in displayFieldsList:
      continue
    if key in fields:
      if (key != CONTACT_NOTES) and (key != CONTACT_BILLING_INFORMATION):
        printKeyValueList([key, fields[key]])
      else:
        printKeyValueList([key, u''])
        incrementIndentLevel()
        printKeyValueList([indentMultiLineText(fields[key])])
        decrementIndentLevel()
  for key in contactsManager.CONTACT_ARRAY_PROPERTY_PRINT_ORDER:
    if displayFieldsList and key not in displayFieldsList:
      continue
    if key in fields:
      keymap = contactsManager.CONTACT_ARRAY_PROPERTIES[key]
      printKeyValueList([key, u''])
      incrementIndentLevel()
      for item in fields[key]:
        fn = item.get(u'label')
        if keymap[u'relMap']:
          if not fn:
            fn = keymap[u'relMap'].get(item[u'rel'], u'custom')
          printKeyValueList([u'type', fn])
          incrementIndentLevel()
        if keymap[u'primary']:
          printKeyValueList([u'rank', [u'notprimary', u'primary'][item[u'primary'] == u'true']])
        value = item[u'value']
        if value == None:
          value = u''
        if key == CONTACT_IMS:
          printKeyValueList([u'protocol', contactsManager.IM_REL_TO_PROTOCOL_MAP.get(item[u'protocol'], item[u'protocol'])])
          printKeyValueList([keymap[u'infoTitle'], value])
        elif key == CONTACT_ADDRESSES:
          printKeyValueList([keymap[u'infoTitle'], u''])
          incrementIndentLevel()
          printKeyValueList([indentMultiLineText(value)])
          decrementIndentLevel()
          for org_key in contactsManager.ADDRESS_FIELD_PRINT_ORDER:
            if item[org_key]:
              printKeyValueList([contactsManager.ADDRESS_FIELD_TO_ARGUMENT_MAP[org_key], item[org_key].replace(u'\n', u'\\n')])
        elif key == CONTACT_ORGANIZATIONS:
          printKeyValueList([keymap[u'infoTitle'], value])
          for org_key in contactsManager.ORGANIZATION_FIELD_PRINT_ORDER:
            if item[org_key]:
              printKeyValueList([contactsManager.ORGANIZATION_FIELD_TO_ARGUMENT_MAP[org_key], item[org_key]])
        elif key == CONTACT_USER_DEFINED_FIELDS:
          printKeyValueList([item.get(u'rel', u'custom'), value])
        else:
          printKeyValueList([keymap[u'infoTitle'], value])
        if keymap[u'relMap']:
          decrementIndentLevel()
      decrementIndentLevel()
  if contactGroupIDs != None and CONTACT_GROUPS in fields:
    printKeyValueList([pluralEntityName(EN_CONTACT_GROUP), u''])
    incrementIndentLevel()
    for group in fields[CONTACT_GROUPS]:
      if group in contactGroupIDs:
        printKeyValueList([contactGroupIDs[group]])
        incrementIndentLevel()
        printKeyValueList([u'id', group])
        decrementIndentLevel()
      else:
        printKeyValueList([u'id', group])
    decrementIndentLevel()
  decrementIndentLevel()

# gam <UserTypeEntity> info contacts <ContactEntity> [basic|full] [showgroups] [fields <ContactFieldNameList>]
def infoUserContacts(users):
  doInfoContacts(users, EN_USER)

# gam info contacts <ContactEntity> [basic|full] [showgroups] [fields <ContactFieldNameList>]
def doInfoDomainContacts():
  doInfoContacts([GC_Values[GC_DOMAIN],], EN_DOMAIN)

def doInfoContacts(users, entityType):
  contactsManager = ContactsManager()
  entityList = getEntityList(OB_CONTACT_ENTITY)
  contactIdLists = entityList if isinstance(entityList, dict) else None
  contactQuery = _initContactQueryAttributes()
  showContactGroups = False
  displayFieldsList = []
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'showgroups':
      showContactGroups = True
    elif myarg in CONTACTS_PROJECTION_CHOICES_MAP:
      contactQuery[u'projection'] = CONTACTS_PROJECTION_CHOICES_MAP[myarg]
    elif myarg == u'fields':
      fieldNameList = getString(OB_FIELD_NAME_LIST)
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in contactsManager.CONTACT_ARGUMENT_TO_PROPERTY_MAP:
          displayFieldsList.append(contactsManager.CONTACT_ARGUMENT_TO_PROPERTY_MAP[field])
        else:
          putArgumentBack()
          invalidChoiceExit(contactsManager.CONTACT_ARGUMENT_TO_PROPERTY_MAP)
      if CONTACT_GROUPS in displayFieldsList:
        showContactGroups = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if contactIdLists:
      entityList = contactIdLists[user]
    user, contactsObject = getContactsObject(entityType, user, i, count)
    if not contactsObject:
      continue
    contactGroupIDs = None
    j = 0
    jcount = len(entityList)
    entityPerformActionNumItems(entityType, user, jcount, EN_CONTACT, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    for contact in entityList:
      j += 1
      try:
        contactId = normalizeContactId(contact)
        contact = callGData(contactsObject, u'GetContact',
                            throw_errors=[GDATA_NOT_FOUND, GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                            retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                            uri=contactsObject.GetContactFeedUri(contact_list=user, contactId=contactId, projection=contactQuery[u'projection']))
        fields = contactsManager.ContactToFields(contact)
        if showContactGroups and CONTACT_GROUPS in fields and not contactGroupIDs:
          contactGroupIDs, _ = getContactGroupsInfo(contactsManager, contactsObject, entityType, user, i, count)
        _showContact(contactsManager, fields, displayFieldsList, [None, contactGroupIDs][showContactGroups], j, jcount)
      except GData_notFound:
        entityItemValueActionFailedWarning(entityType, user, EN_CONTACT, contactId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except GData_forbidden:
        entityServiceNotApplicableWarning(entityType, user, i, count)
        break
      except GData_serviceNotApplicable:
        entityUnknownWarning(entityType, user, i, count)
        break
    decrementIndentLevel()

# gam <UserTypeEntity> print contacts [todrive] [query <QueryContact>] [contactgroup <ContactGroupItem>] [emailmatchpattern <RegularExpression>] [updated_min yyyy-mm-dd]
#	[basic|full] [showgroups] [showdeleted] [orderby <ContactOrderByFieldName> [ascending|descending]] [fields <ContactFieldNameList>]
def printUserContacts(users):
  printShowContacts(users, EN_USER, True)

# gam <UserTypeEntity> show contacts [query <QueryContact>] [contactgroup <ContactGroupItem>] [emailmatchpattern <RegularExpression>] [updated_min yyyy-mm-dd]
#	[basic|full] [showgroups] [showdeleted] [orderby <ContactOrderByFieldName> [ascending|descending]] [fields <ContactFieldNameList>]
def showUserContacts(users):
  printShowContacts(users, EN_USER, False)

# gam print contacts [todrive] [query <QueryContact>] [emailmatchpattern <RegularExpression>] [updated_min yyyy-mm-dd]
#	[basic|full] [showgroups] [showdeleted] [orderby <ContactOrderByFieldName> [ascending|descending]] [fields <ContactFieldNameList>]
def doPrintDomainContacts():
  printShowContacts([GC_Values[GC_DOMAIN],], EN_DOMAIN, True)

# gam show contacts [query <QueryContact>] [emailmatchpattern <RegularExpression>] [updated_min yyyy-mm-dd]
#	[basic|full] [showgroups] [showdeleted] [orderby <ContactOrderByFieldName> [ascending|descending]] [fields <ContactFieldNameList>]
def doShowDomainContacts():
  printShowContacts([GC_Values[GC_DOMAIN],], EN_DOMAIN, False)

def printShowContacts(users, entityType, csvFormat):
  contactsManager = ContactsManager()
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile([singularEntityName(entityType), CONTACT_ID, CONTACT_NAME])
  contactQuery = _initContactQueryAttributes()
  showContactGroups = False
  displayFieldsList = []
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    elif myarg == u'showgroups':
      showContactGroups = True
    elif myarg == u'fields':
      fieldNameList = getString(OB_FIELD_NAME_LIST)
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in contactsManager.CONTACT_ARGUMENT_TO_PROPERTY_MAP:
          displayFieldsList.append(contactsManager.CONTACT_ARGUMENT_TO_PROPERTY_MAP[field])
        else:
          putArgumentBack()
          invalidChoiceExit(contactsManager.CONTACT_ARGUMENT_TO_PROPERTY_MAP)
      if CONTACT_GROUPS in displayFieldsList:
        showContactGroups = True
    else:
      _getContactQueryAttributes(contactQuery, myarg, entityType, True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, contactsObject = getContactsObject(entityType, user, i, count)
    if not contactsObject:
      continue
    contactGroupIDs = contactGroupNames = None
    if contactQuery[u'contactGroup']:
      groupId, contactGroupIDs, contactGroupNames = validateContactGroup(contactsManager, contactsObject, contactQuery[u'contactGroup'], contactGroupIDs, contactGroupNames, entityType, user, i, count)
      if not groupId:
        if contactGroupNames:
          entityItemValueActionFailedWarning(entityType, user, EN_CONTACT_GROUP, contactQuery[u'contactGroup'], PHRASE_DOES_NOT_EXIST, i, count)
        continue
      contactQuery[u'group'] = contactsObject.GetContactGroupFeedUri(contact_list=user, projection=u'base', groupId=groupId)
    contacts = queryContacts(contactsObject, contactQuery, entityType, user, i, count)
    jcount = len(contacts) if (contacts) else 0
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
    if not csvFormat:
      entityPerformActionModifierNumItems(entityType, user, PHRASE_MAXIMUM_OF, jcount, EN_CONTACT, i, count)
      if jcount == 0:
        continue
      incrementIndentLevel()
      j = 0
      for contact in contacts:
        j += 1
        fields = contactsManager.ContactToFields(contact)
        if contactQuery[u'emailMatchPattern'] and not contactEmailAddressMatches(contactsManager, contactQuery, fields):
          continue
        if showContactGroups and CONTACT_GROUPS in fields and not contactGroupIDs:
          contactGroupIDs, _ = getContactGroupsInfo(contactsManager, contactsObject, entityType, user, i, count)
        _showContact(contactsManager, fields, displayFieldsList, [None, contactGroupIDs][showContactGroups], j, jcount)
      decrementIndentLevel()
    else:
      if jcount == 0:
        continue
      for contact in contacts:
        fields = contactsManager.ContactToFields(contact)
        if contactQuery[u'emailMatchPattern'] and not contactEmailAddressMatches(contactsManager, contactQuery, fields):
          continue
        if showContactGroups and CONTACT_GROUPS in fields and not contactGroupIDs:
          contactGroupIDs, _ = getContactGroupsInfo(contactsManager, contactsObject, entityType, user, i, count)
        contactRow = {singularEntityName(entityType): user, CONTACT_ID: fields[CONTACT_ID]}
        for key in contactsManager.CONTACT_NAME_PROPERTY_PRINT_ORDER:
          if displayFieldsList and key not in displayFieldsList:
            continue
          if key in fields:
            if (key != CONTACT_NOTES) and (key != CONTACT_BILLING_INFORMATION):
              contactRow[key] = fields[key]
            else:
              contactRow[key] = fields[key].replace(u'\n', u'\\n')
        for key in contactsManager.CONTACT_ARRAY_PROPERTY_PRINT_ORDER:
          if displayFieldsList and key not in displayFieldsList:
            continue
          if key in fields:
            keymap = contactsManager.CONTACT_ARRAY_PROPERTIES[key]
            contactRow[u'{0}.0.count'.format(key)] = len(fields[key])
            j = 0
            for item in fields[key]:
              j += 1
              fn = u'{0}.{1}.'.format(key, j)
              fnt = item.get(u'label')
              if fnt:
                contactRow[fn+u'type'] = fnt
              elif keymap[u'relMap']:
                contactRow[fn+u'type'] = keymap[u'relMap'].get(item[u'rel'], u'custom')
              if keymap[u'primary']:
                contactRow[fn+u'rank'] = [u'notprimary', u'primary'][item[u'primary'] == u'true']
              value = item[u'value']
              if value == None:
                value = u''
              if key == CONTACT_IMS:
                contactRow[fn+u'protocol'] = contactsManager.IM_REL_TO_PROTOCOL_MAP.get(item[u'protocol'], item[u'protocol'])
                contactRow[fn+keymap[u'infoTitle']] = value
              elif key == CONTACT_ADDRESSES:
                contactRow[fn+keymap[u'infoTitle']] = value.replace(u'\n', u'\\n')
                for org_key in contactsManager.ADDRESS_FIELD_PRINT_ORDER:
                  if item[org_key]:
                    contactRow[fn+contactsManager.ADDRESS_FIELD_TO_ARGUMENT_MAP[org_key]] = item[org_key].replace(u'\n', u'\\n')
              elif key == CONTACT_ORGANIZATIONS:
                contactRow[fn+keymap[u'infoTitle']] = value
                for org_key in contactsManager.ORGANIZATION_FIELD_PRINT_ORDER:
                  if item[org_key]:
                    contactRow[fn+contactsManager.ORGANIZATION_FIELD_TO_ARGUMENT_MAP[org_key]] = item[org_key]
              elif key == CONTACT_USER_DEFINED_FIELDS:
                contactRow[fn+u'type'] = item.get(u'rel', u'custom')
                contactRow[fn+keymap[u'infoTitle']] = value
              else:
                contactRow[fn+keymap[u'infoTitle']] = value
        if showContactGroups and CONTACT_GROUPS in fields:
          contactRow[u'{0}.0.Count'.format(CONTACT_GROUPS)] = len(fields[CONTACT_GROUPS])
          j = 0
          for group in fields[CONTACT_GROUPS]:
            j += 1
            fn = u'{0}.{1}.'.format(CONTACT_GROUPS, j)
            contactRow[fn+CONTACT_GROUP_ID] = u'id:{0}'.format(group)
            if group in contactGroupIDs:
              contactRow[fn+CONTACT_GROUP_NAME] = contactGroupIDs[group]
        addRowTitlesToCSVfile(contactRow, csvRows, titles)
  if csvFormat:
    sortCSVTitles([singularEntityName(entityType), CONTACT_ID, CONTACT_NAME], titles)
    writeCSVfile(csvRows, titles, u'Contacts', todrive)

# gam <UserTypeEntity> create contactgroup <ContactGroupAttributes>+
def createUserContactGroup(users):
  doCreateContactGroup(users, EN_USER)

def doCreateContactGroup(users, entityType):
  contactsManager = ContactsManager()
  fields = contactsManager.GetContactGroupFields()
  contactGroup = contactsManager.FieldsToContactGroup(fields)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, contactsObject = getContactsObject(entityType, user, i, count)
    if not contactsObject:
      continue
    _, contactGroupNames = getContactGroupsInfo(contactsManager, contactsObject, entityType, user, i, count)
    if contactGroupNames == False:
      continue
    if fields[CONTACT_GROUP_NAME] in contactGroupNames:
      entityActionFailedWarning(entityType, user, entityTypeNameMessage(EN_CONTACT_GROUP_NAME, fields[CONTACT_GROUP_NAME], PHRASE_DUPLICATE), i, count)
      continue
    try:
      group = callGData(contactsObject, u'CreateGroup',
                        throw_errors=[GDATA_BAD_REQUEST, GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                        retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                        new_group=contactGroup, insert_uri=contactsObject.GetContactGroupFeedUri(contact_list=user))
      entityItemValueActionPerformed(entityType, user, EN_CONTACT_GROUP, contactsManager.GetContactShortId(group), i, count)
    except GData_badRequest:
      entityItemValueActionFailedWarning(entityType, user, EN_CONTACT_GROUP, u'', PHRASE_BAD_REQUEST, i, count)
    except GData_forbidden:
      entityServiceNotApplicableWarning(entityType, user, i, count)
    except GData_serviceNotApplicable:
      entityUnknownWarning(entityType, user, i, count)

# gam <UserTypeEntity> update contactgroups <ContactGroupItem> <ContactAttributes>+
def updateUserContactGroup(users):
  doUpdateContactGroup(users, EN_USER)

def doUpdateContactGroup(users, entityType):
  contactsManager = ContactsManager()
  entityList = getStringReturnInList(OB_CONTACT_GROUP_ITEM)
  update_fields = contactsManager.GetContactGroupFields()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, contactsObject = getContactsObject(entityType, user, i, count)
    if not contactsObject:
      continue
    contactGroupIDs = contactGroupNames = None
    j = 0
    jcount = len(entityList)
    entityPerformActionNumItems(entityType, user, jcount, EN_CONTACT_GROUP, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    for contactGroup in entityList:
      j += 1
      groupId, contactGroupIDs, contactGroupNames = validateContactGroup(contactsManager, contactsObject, contactGroup, contactGroupIDs, contactGroupNames, entityType, user, i, count)
      if not groupId:
        if contactGroupNames:
          entityItemValueActionFailedWarning(entityType, user, EN_CONTACT_GROUP, contactGroup, PHRASE_DOES_NOT_EXIST, j, jcount)
          continue
        break
      if update_fields[CONTACT_GROUP_NAME] in contactGroupNames and groupId not in contactGroupNames[update_fields[CONTACT_GROUP_NAME]]:
        entityItemValueActionFailedWarning(entityType, user, EN_CONTACT_GROUP, contactGroup, entityTypeNameMessage(EN_CONTACT_GROUP_NAME, update_fields[CONTACT_GROUP_NAME], PHRASE_DUPLICATE), i, count)
        continue
      contactGroup = contactGroupIDs.get(groupId, contactGroup)
      try:
        group = callGData(contactsObject, u'GetGroup',
                          throw_errors=[GDATA_NOT_FOUND, GDATA_BAD_REQUEST, GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                          retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                          uri=contactsObject.GetContactGroupFeedUri(contact_list=user, groupId=groupId))
        fields = contactsManager.ContactGroupToFields(group)
        for field in update_fields:
          fields[field] = update_fields[field]
        groupEntry = contactsManager.FieldsToContactGroup(fields)
        groupEntry.category = group.category
        groupEntry.link = group.link
        groupEntry.etag = group.etag
        groupEntry.id = group.id
        callGData(contactsObject, u'UpdateGroup',
                  throw_errors=[GDATA_NOT_FOUND, GDATA_BAD_REQUEST, GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                  edit_uri=contactsObject.GetContactGroupFeedUri(contact_list=user, groupId=groupId), updated_group=groupEntry, extra_headers={u'If-Match': group.etag})
        entityItemValueActionPerformed(entityType, user, EN_CONTACT_GROUP, contactGroup, j, jcount)
      except GData_notFound:
        entityItemValueActionFailedWarning(entityType, user, EN_CONTACT_GROUP, contactGroup, PHRASE_DOES_NOT_EXIST, j, jcount)
      except GData_badRequest:
        entityItemValueActionFailedWarning(entityType, user, EN_CONTACT_GROUP, contactGroup, PHRASE_BAD_REQUEST, j, jcount)
      except GData_forbidden:
        entityServiceNotApplicableWarning(entityType, user, i, count)
        break
      except GData_serviceNotApplicable:
        entityUnknownWarning(entityType, user, i, count)
        break
    decrementIndentLevel()

# gam <UserTypeEntity> delete contactgroups <ContactGroupEntity>
def deleteUserContactGroups(users):
  doDeleteContactGroups(users, EN_USER)

def doDeleteContactGroups(users, entityType):
  contactsManager = ContactsManager()
  entityList = getEntityList(OB_CONTACT_GROUP_ENTITY, shlexSplit=True)
  contactGroupIdLists = entityList if isinstance(entityList, dict) else None
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if contactGroupIdLists:
      entityList = contactGroupIdLists[user]
    user, contactsObject = getContactsObject(entityType, user, i, count)
    if not contactsObject:
      continue
    contactGroupIDs = contactGroupNames = None
    j = 0
    jcount = len(entityList)
    entityPerformActionNumItems(entityType, user, jcount, EN_CONTACT_GROUP, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    for contactGroup in entityList:
      j += 1
      try:
        groupId, contactGroupIDs, contactGroupNames = validateContactGroup(contactsManager, contactsObject, contactGroup, contactGroupIDs, contactGroupNames, entityType, user, i, count)
        if not groupId:
          if contactGroupNames:
            entityItemValueActionFailedWarning(entityType, user, EN_CONTACT_GROUP, contactGroup, PHRASE_DOES_NOT_EXIST, j, jcount)
            continue
          break
        contactGroup = contactGroupIDs.get(groupId, contactGroup)
        group = callGData(contactsObject, u'GetGroup',
                          throw_errors=[GDATA_NOT_FOUND, GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                          retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                          uri=contactsObject.GetContactGroupFeedUri(contact_list=user, groupId=groupId))
        callGData(contactsObject, u'DeleteGroup',
                  throw_errors=[GDATA_NOT_FOUND, GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                  edit_uri=contactsObject.GetContactGroupFeedUri(contact_list=user, groupId=groupId), extra_headers={u'If-Match': group.etag})
        entityItemValueActionPerformed(entityType, user, EN_CONTACT_GROUP, contactGroup, j, jcount)
      except GData_notFound:
        entityItemValueActionFailedWarning(entityType, user, EN_CONTACT_GROUP, contactGroup, PHRASE_DOES_NOT_EXIST, j, jcount)
      except GData_forbidden:
        entityServiceNotApplicableWarning(entityType, user, i, count)
        break
      except GData_serviceNotApplicable:
        entityUnknownWarning(entityType, user, i, count)
        break
    decrementIndentLevel()

def _showContactGroup(contactsManager, group, j, jcount):
  fields = contactsManager.ContactGroupToFields(group)
  printEntityName(EN_CONTACT_GROUP, fields[CONTACT_GROUP_NAME], j, jcount)
  incrementIndentLevel()
  printKeyValueList([u'updated', [NEVER, fields[CONTACT_GROUP_UPDATED]][fields[CONTACT_GROUP_UPDATED] != NEVER_TIME]])
  printKeyValueList([u'id', fields[CONTACT_GROUP_ID]])
  decrementIndentLevel()

# gam <UserTypeEntity> info contactgroups <ContactGroupEntity>
def infoUserContactGroups(users):
  doInfoContactGroups(users, EN_USER)

def doInfoContactGroups(users, entityType):
  contactsManager = ContactsManager()
  entityList = getEntityList(OB_CONTACT_GROUP_ENTITY, shlexSplit=True)
  contactGroupIdLists = entityList if isinstance(entityList, dict) else None
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if contactGroupIdLists:
      entityList = contactGroupIdLists[user]
    user, contactsObject = getContactsObject(entityType, user, i, count)
    if not contactsObject:
      continue
    contactGroupIDs = contactGroupNames = None
    j = 0
    jcount = len(entityList)
    entityPerformActionNumItems(entityType, user, jcount, EN_CONTACT_GROUP, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    for contactGroup in entityList:
      j += 1
      try:
        groupId, contactGroupIDs, contactGroupNames = validateContactGroup(contactsManager, contactsObject, contactGroup, contactGroupIDs, contactGroupNames, entityType, user, i, count)
        if not groupId:
          if contactGroupNames:
            entityItemValueActionFailedWarning(entityType, user, EN_CONTACT_GROUP, contactGroup, PHRASE_DOES_NOT_EXIST, j, jcount)
            continue
          break
        contactGroup = contactGroupIDs.get(groupId, contactGroup)
        group = callGData(contactsObject, u'GetGroup',
                          throw_errors=[GDATA_NOT_FOUND, GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                          retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                          uri=contactsObject.GetContactGroupFeedUri(contact_list=user, groupId=groupId))
        _showContactGroup(contactsManager, group, j, jcount)
      except GData_notFound:
        entityItemValueActionFailedWarning(entityType, user, EN_CONTACT_GROUP, contactGroup, PHRASE_DOES_NOT_EXIST, j, jcount)
      except GData_forbidden:
        entityServiceNotApplicableWarning(entityType, user, i, count)
        break
      except GData_serviceNotApplicable:
        entityUnknownWarning(entityType, user, i, count)
        break
    decrementIndentLevel()

# gam <UserTypeEntity> print contactgroups [todrive] [updated_min yyyy-mm-dd]
#	[basic|full] [showdeleted] [orderby <ContactOrderByFieldName> [ascending|descending]]
def printUserContactGroups(users):
  printShowContactGroups(users, EN_USER, True)

# gam <UserTypeEntity> show contactgroups [updated_min yyyy-mm-dd]
#	[basic|full] [showdeleted] [orderby <ContactOrderByFieldName> [ascending|descending]]
def showUserContactGroups(users):
  printShowContactGroups(users, EN_USER, False)

def printShowContactGroups(users, entityType, csvFormat):
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile([singularEntityName(entityType), CONTACT_GROUP_ID, CONTACT_GROUP_NAME])
  projection = u'full'
  url_params = {u'max-results': str(GC_Values[GC_CONTACT_MAX_RESULTS])}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    elif myarg == u'orderby':
      url_params[u'orderby'] = getChoice(CONTACTS_ORDERBY_CHOICES_MAP, mapChoice=True)
      url_params[u'sortorder'] = getChoice(SORTORDER_CHOICES_MAP, defaultChoice=u'ascending')
    elif myarg in CONTACTS_PROJECTION_CHOICES_MAP:
      projection = CONTACTS_PROJECTION_CHOICES_MAP[myarg]
    elif myarg == u'showdeleted':
      url_params[u'showdeleted'] = u'true'
    elif myarg == u'updatedmin':
      url_params[u'updated-min'] = getYYYYMMDD()
    else:
      unknownArgumentExit()
  contactsManager = ContactsManager()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, contactsObject = getContactsObject(entityType, user, i, count)
    if not contactsObject:
      continue
    printGettingAllEntityItemsForWhom(EN_CONTACT_GROUP, user, i, count)
    uri = contactsObject.GetContactGroupFeedUri(contact_list=user, projection=projection)
    try:
      page_message = getPageMessage()
      groups = callGDataPages(contactsObject, u'GetGroupsFeed',
                              page_message=page_message,
                              throw_errors=[GDATA_SERVICE_NOT_APPLICABLE, GDATA_FORBIDDEN],
                              retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                              uri=uri, url_params=url_params)
      jcount = len(groups)
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
      if not csvFormat:
        entityPerformActionNumItems(EN_USER, user, jcount, EN_CONTACT_GROUP, i, count)
        if jcount == 0:
          continue
        incrementIndentLevel()
        j = 0
        for group in groups:
          j += 1
          _showContactGroup(contactsManager, group, j, jcount)
        decrementIndentLevel()
      else:
        if jcount == 0:
          continue
        for group in groups:
          fields = contactsManager.ContactGroupToFields(group)
          groupRow = {singularEntityName(entityType): user, CONTACT_GROUP_ID: u'id:{0}'.format(fields[CONTACT_GROUP_ID]),
                      CONTACT_GROUP_NAME: fields[CONTACT_GROUP_NAME], CONTACT_GROUP_UPDATED: [NEVER, fields[CONTACT_GROUP_UPDATED]][fields[CONTACT_GROUP_UPDATED] != NEVER_TIME]}
          addRowTitlesToCSVfile(groupRow, csvRows, titles)
    except GData_forbidden:
      entityServiceNotApplicableWarning(entityType, user, i, count)
    except GData_serviceNotApplicable:
      entityUnknownWarning(entityType, user, i, count)
  if csvFormat:
    writeCSVfile(csvRows, titles, u'Contact Groups', todrive)

# Utilities for cros commands
def getCrOSDeviceEntity():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  if checkArgumentPresent(QUERY_ARGUMENT):
    query = getString(OB_QUERY)
  else:
    deviceId = getString(OB_CROS_DEVICE_ENTITY)
    if deviceId[:6].lower() == u'query:':
      query = deviceId[6:]
    else:
      putArgumentBack()
      query = None
  if not query:
    return (getEntityList(OB_CROS_ENTITY), cd)
  try:
    devices = callGAPIpages(cd.chromeosdevices(), u'list', u'chromeosdevices',
                            throw_reasons=[GAPI_INVALID_INPUT, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                            customerId=GC_Values[GC_CUSTOMER_ID], query=query,
                            fields=u'nextPageToken,chromeosdevices(deviceId)')
    return ([cros[u'deviceId'] for cros in devices], cd)
  except GAPI_invalidInput:
    putArgumentBack()
    usageErrorExit(PHRASE_INVALID_QUERY)
  except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
    accessErrorExit(cd)

UPDATE_CROS_ARGUMENT_TO_PROPERTY_MAP = {
  u'annotatedassetid': u'annotatedAssetId',
  u'annotatedlocation': u'annotatedLocation',
  u'annotateduser': u'annotatedUser',
  u'asset': u'annotatedAssetId',
  u'assetid': u'annotatedAssetId',
  u'location': u'annotatedLocation',
  u'notes': u'notes',
  u'org': u'orgUnitPath',
  u'orgunitpath': u'orgUnitPath',
  u'ou': u'orgUnitPath',
  u'status': u'status',
  u'tag': u'annotatedAssetId',
  u'user': u'annotatedUser',
  }

CROS_STATUS_CHOICES_MAP = {
  u'active': u'ACTIVE',
  u'deprovisioned': u'DEPROVISIONED',
  u'inactive': u'INACTIVE',
  u'returnapproved': u'RETURN_APPROVED',
  u'returnrequested': u'RETURN_REQUESTED',
  u'shipped': u'SHIPPED',
  u'unknown': u'UNKNOWN',
  }

# gam update cros|croses <CrOSEntity> <CrOSAttributes>
def doUpdateCrOSDevices():
  updateCrOSDevices(*getCrOSDeviceEntity())

# gam <CrOSTypeEntity> update <CrOSAttributes>
def updateCrOSDevices(entityList, cd=None):
  if not cd:
    cd = buildGAPIObject(GAPI_DIRECTORY_API)
  body = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg in UPDATE_CROS_ARGUMENT_TO_PROPERTY_MAP:
      up = UPDATE_CROS_ARGUMENT_TO_PROPERTY_MAP[myarg]
      if up == u'orgUnitPath':
        body[up] = getOrgUnitPath()
      elif up == u'status':
        body[up] = getChoice(CROS_STATUS_CHOICES_MAP, mapChoice=True)
      elif up == u'notes':
        body[up] = getString(OB_STRING, emptyOK=True)
      else:
        body[up] = getString(OB_STRING)
    else:
      unknownArgumentExit()
  i = 0
  count = len(entityList)
  for deviceId in entityList:
    i += 1
    try:
      callGAPI(cd.chromeosdevices(), u'patch',
               throw_reasons=[GAPI_INVALID, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
               customerId=GC_Values[GC_CUSTOMER_ID], deviceId=deviceId, body=body)
      entityActionPerformed(EN_CROS_DEVICE, deviceId, i, count)
    except GAPI_invalid as e:
      entityActionFailedWarning(EN_CROS_DEVICE, deviceId, e.message, i, count)
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, EN_CROS_DEVICE, deviceId, i, count)

CROS_ARGUMENT_TO_PROPERTY_MAP = {
  u'activetimeranges': [u'activeTimeRanges.activeTime', u'activeTimeRanges.date'],
  u'annotatedassetid': [u'annotatedAssetId',],
  u'annotatedlocation': [u'annotatedLocation',],
  u'annotateduser': [u'annotatedUser',],
  u'asset': [u'annotatedAssetId',],
  u'assetid': [u'annotatedAssetId',],
  u'bootmode': [u'bootMode',],
  u'deviceid': [u'deviceId',],
  u'ethernetmacaddress': [u'ethernetMacAddress',],
  u'firmwareversion': [u'firmwareVersion',],
  u'lastenrollmenttime': [u'lastEnrollmentTime',],
  u'lastsync': [u'lastSync',],
  u'location': [u'annotatedLocation',],
  u'macaddress': [u'macAddress',],
  u'meid': [u'meid',],
  u'model': [u'model',],
  u'notes': [u'notes',],
  u'ordernumber': [u'orderNumber',],
  u'org': [u'orgUnitPath',],
  u'orgunitpath': [u'orgUnitPath',],
  u'osversion': [u'osVersion',],
  u'ou': [u'orgUnitPath',],
  u'platformversion': [u'platformVersion',],
  u'recentusers': [u'recentUsers.email', u'recentUsers.type'],
  u'serialnumber': [u'serialNumber',],
  u'status': [u'status',],
  u'supportenddate': [u'supportEndDate',],
  u'tag': [u'annotatedAssetId',],
  u'timeranges': [u'activeTimeRanges.activeTime', u'activeTimeRanges.date'],
  u'user': [u'annotatedUser',],
  u'willautorenew': [u'willAutoRenew',],
  }

CROS_BASIC_FIELDS_LIST = [u'deviceId', u'annotatedAssetId', u'annotatedLocation', u'annotatedUser', u'lastSync', u'notes', u'serialNumber', u'status']

CROS_SCALAR_PROPERTY_PRINT_ORDER = [
  u'orgUnitPath',
  u'annotatedAssetId',
  u'annotatedLocation',
  u'annotatedUser',
  u'lastSync',
  u'notes',
  u'serialNumber',
  u'status',
  u'model',
  u'firmwareVersion',
  u'platformVersion',
  u'osVersion',
  u'bootMode',
  u'meid',
  u'ethernetMacAddress',
  u'macAddress',
  u'lastEnrollmentTime',
  u'orderNumber',
  u'supportEndDate',
  u'willAutoRenew',
  ]

# gam info cros|croses <CrOSEntity> [nolists] [listlimit <Number>]
#	[basic|full|allfields] <CrOSFieldName>* [fields <CrOSFieldNameList>]
def doInfoCrOSDevices():
  infoCrOSDevices(*getCrOSDeviceEntity())

# gam <CrOSTypeEntity> info [nolists] [listlimit <Number>]
#	[basic|full|allfields] <CrOSFieldName>* [fields <CrOSFieldNameList>]
def infoCrOSDevices(entityList, cd=None):
  if not cd:
    cd = buildGAPIObject(GAPI_DIRECTORY_API)
  projection = None
  fieldsList = []
  noLists = False
  listLimit = 0
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'nolists':
      noLists = True
    elif myarg == u'listlimit':
      listLimit = getInteger(minVal=0)
    elif myarg == u'allfields':
      projection = u'FULL'
      fieldsList = []
    elif myarg in PROJECTION_CHOICES_MAP:
      projection = PROJECTION_CHOICES_MAP[myarg]
      if projection == u'FULL':
        fieldsList = []
      else:
        fieldsList = CROS_BASIC_FIELDS_LIST[:]
    elif myarg in CROS_ARGUMENT_TO_PROPERTY_MAP:
      if not fieldsList:
        fieldsList = [u'deviceId',]
      fieldsList.extend(CROS_ARGUMENT_TO_PROPERTY_MAP[myarg])
    elif myarg == u'fields':
      if not fieldsList:
        fieldsList = [u'deviceId',]
      fieldNameList = getString(OB_FIELD_NAME_LIST)
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in CROS_ARGUMENT_TO_PROPERTY_MAP:
          fieldsList.extend(CROS_ARGUMENT_TO_PROPERTY_MAP[field])
          if field in [u'recentusers', u'timeranges', u'activetimeranges']:
            projection = u'FULL'
            noLists = False
        else:
          putArgumentBack()
          invalidChoiceExit(CROS_ARGUMENT_TO_PROPERTY_MAP)
    else:
      unknownArgumentExit()
  if fieldsList:
    fieldsList = u','.join(set(fieldsList)).replace(u'.', u'/')
  else:
    fieldsList = None
  i = 0
  count = len(entityList)
  for deviceId in entityList:
    i += 1
    try:
      cros = callGAPI(cd.chromeosdevices(), u'get',
                      throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                      customerId=GC_Values[GC_CUSTOMER_ID], deviceId=deviceId, projection=projection, fields=fieldsList)
      printEntityName(EN_CROS_DEVICE, deviceId, i, count)
      incrementIndentLevel()
      for up in CROS_SCALAR_PROPERTY_PRINT_ORDER:
        if up in cros:
          printKeyValueList([up, cros[up]])
      if not noLists:
        activeTimeRanges = cros.get(u'activeTimeRanges', [])
        lenATR = len(activeTimeRanges)
        if lenATR:
          printKeyValueList([u'activeTimeRanges'])
          incrementIndentLevel()
          for i in xrange(min(listLimit, lenATR) if listLimit else lenATR):
            printKeyValueList([u'date', activeTimeRanges[i][u'date']])
            incrementIndentLevel()
            printKeyValueList([u'activeTime', str(activeTimeRanges[i][u'activeTime'])])
            printKeyValueList([u'duration', formatMilliSeconds(activeTimeRanges[i][u'activeTime'])])
            decrementIndentLevel()
          decrementIndentLevel()
        recentUsers = cros.get(u'recentUsers', [])
        lenRU = len(recentUsers)
        if lenRU:
          printKeyValueList([u'recentUsers'])
          incrementIndentLevel()
          for i in xrange(min(listLimit, lenRU) if listLimit else lenRU):
            printKeyValueList([u'type', recentUsers[i][u'type']])
            incrementIndentLevel()
            printKeyValueList([u'email', recentUsers[i].get(u'email', u'')])
            decrementIndentLevel()
          decrementIndentLevel()
      decrementIndentLevel()
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, EN_CROS_DEVICE, deviceId, i, count)

CROS_ORDERBY_CHOICES_MAP = {
  u'lastsync': u'lastSync',
  u'location': u'annotatedLocation',
  u'notes': u'notes',
  u'serialnumber': u'serialNumber',
  u'status': u'status',
  u'supportenddate': u'supportEndDate',
  u'user': u'annotatedUser',
  }

# gam <CrOSTypeEntity> print
def doPrintCrOSEntity(entityList):
  getChoice([CL_OB_CROS, CL_OB_CROSES], defaultChoice=None)
  if CL_argvI == CL_argvLen:
    for entity in entityList:
      printLine(entity)
    return
  doPrintCrOSDevices(entityList)

# gam [<CrOSTypeEntity>] print cros [todrive] [query <QueryCrOS>]|[select <CrOSTypeEntity>]
#	[orderby <CrOSOrderByFieldName> [ascending|descending]] [nolists|recentusers|timeranges] [listlimit <Number>]
#	[basic|full|allfields] <CrOSFieldName>* [fields <CrOSFieldNameList>]
def doPrintCrOSDevices(entityList=None):
  def _printCrOS(cros):
    if (not noLists) and (not selectActiveTimeRanges) and (not selectRecentUsers):
      addRowTitlesToCSVfile(flattenJSON(cros, listLimit=listLimit), csvRows, titles)
      return
    row = {}
    for attrib in cros:
      if attrib in [u'kind', u'etag', u'recentUsers', u'activeTimeRanges']:
        continue
      if attrib not in titles[u'set']:
        addTitleToCSVfile(attrib, titles)
      row[attrib] = cros[attrib]
    activeTimeRanges = cros.get(selectActiveTimeRanges, []) if selectActiveTimeRanges else []
    recentUsers = cros.get(selectRecentUsers, []) if selectRecentUsers else []
    if noLists or (not activeTimeRanges and not recentUsers):
      csvRows.append(row)
      return
    lenATR = len(activeTimeRanges)
    lenRU = len(recentUsers)
    for i in xrange(min(listLimit, max(lenATR, lenRU)) if listLimit else max(lenATR, lenRU)):
      new_row = row.copy()
      if i < lenATR:
        new_row[u'activeTimeRanges.activeTime'] = str(activeTimeRanges[i][u'activeTime'])
        new_row[u'activeTimeRanges.duration'] = formatMilliSeconds(activeTimeRanges[i][u'activeTime'])
        new_row[u'activeTimeRanges.date'] = activeTimeRanges[i][u'date']
      if i < lenRU:
        new_row[u'recentUsers.email'] = recentUsers[i].get(u'email', u'')
        new_row[u'recentUsers.type'] = recentUsers[i][u'type']
      csvRows.append(new_row)

  def _callbackPrintCrOS(request_id, response, exception):
    REASON_TO_MESSAGE_MAP = {GAPI_RESOURCE_NOT_FOUND: PHRASE_DOES_NOT_EXIST}
    ri = request_id.splitlines()
    if exception is None:
      _printCrOS(response)
    else:
      http_status, reason, message = checkGAPIError(exception)
      errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
      entityActionFailedWarning(EN_CROS_DEVICE, ri[RI_ITEM], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _batchPrintCrOS(deviceIds):
    jcount = len(deviceIds)
    bcount = 0
    bsize = GC_Values[GC_BATCH_SIZE]
    if bsize > 1:
      dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackPrintCrOS)
    j = 0
    for deviceId in deviceIds:
      j += 1
      if bsize > 1:
        parameters = dict([(u'customerId', GC_Values[GC_CUSTOMER_ID]), (u'deviceId', deviceId), (u'projection', projection), (u'fields', fields)]+GM_Globals[GM_EXTRA_ARGS_LIST])
        dbatch.add(cd.chromeosdevices().get(**parameters), request_id=batchRequestID(u'', 0, 0, j, jcount, deviceId))
        bcount += 1
        if bcount == GC_Values[GC_BATCH_SIZE]:
          dbatch.execute()
          dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackPrintCrOS)
          bcount = 0
      else:
        try:
          cros = callGAPI(cd.chromeosdevices(), u'get',
                          throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                          customerId=GC_Values[GC_CUSTOMER_ID], deviceId=deviceId, projection=projection, fields=fields)
          _printCrOS(cros)
        except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
          checkEntityAFDNEorAccessErrorExit(cd, EN_CROS_DEVICE, deviceId, j, jcount)
    if bcount > 0:
      dbatch.execute()

  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  todrive = False
  fieldsList = []
  fieldsTitles = {}
  titles, csvRows = initializeTitlesCSVfile(None)
  addFieldToCSVfile(u'deviceid', CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
  sortHeaders = False
  query = projection = orderBy = sortOrder = None
  noLists = False
  listLimit = 0
  selectActiveTimeRanges = selectRecentUsers = None
  select = selectLookup = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'query':
      query = getString(OB_QUERY)
    elif myarg == u'select':
      _, entityList = getEntityToModify(defaultEntityType=CL_ENTITY_CROS, crosAllowed=True, userAllowed=False)
      select = True
    elif myarg == u'nolists':
      noLists = True
      selectActiveTimeRanges = selectRecentUsers = None
    elif myarg == u'listlimit':
      listLimit = getInteger(minVal=0)
    elif myarg == u'recentusers':
      projection = u'FULL'
      selectRecentUsers = u'recentUsers'
      addFieldToCSVfile(myarg, CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
      noLists = False
    elif myarg in [u'timeranges', u'activetimeranges']:
      projection = u'FULL'
      selectActiveTimeRanges = u'activeTimeRanges'
      addFieldToCSVfile(myarg, CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
      addTitlesToCSVfile([u'activeTimeRanges.duration'], titles)
      noLists = False
    elif myarg == u'orderby':
      orderBy = getChoice(CROS_ORDERBY_CHOICES_MAP, mapChoice=True)
      sortOrder = getChoice(SORTORDER_CHOICES_MAP, defaultChoice=u'ascending', mapChoice=True)
    elif myarg in PROJECTION_CHOICES_MAP:
      projection = PROJECTION_CHOICES_MAP[myarg]
      sortHeaders = True
      if projection == u'FULL':
        fieldsList = []
      else:
        fieldsList = CROS_BASIC_FIELDS_LIST[:]
    elif myarg == u'allfields':
      projection = u'FULL'
      sortHeaders = True
      fieldsList = []
    elif myarg in CROS_ARGUMENT_TO_PROPERTY_MAP:
      if not fieldsList:
        fieldsList = [u'deviceId',]
      addFieldToCSVfile(myarg, CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
    elif myarg == u'fields':
      if not fieldsList:
        fieldsList = [u'deviceId',]
      fieldNameList = getString(OB_FIELD_NAME_LIST)
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in CROS_ARGUMENT_TO_PROPERTY_MAP:
          addFieldToCSVfile(field, CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
          if field == u'recentusers':
            projection = u'FULL'
            selectRecentUsers = u'recentUsers'
            noLists = False
          elif field in [u'timeranges', u'activetimeranges']:
            projection = u'FULL'
            selectActiveTimeRanges = u'activeTimeRanges'
            noLists = False
        else:
          putArgumentBack()
          invalidChoiceExit(CROS_ARGUMENT_TO_PROPERTY_MAP)
    else:
      unknownArgumentExit()
  if entityList == None:
    if fieldsList:
      fields = u'nextPageToken,chromeosdevices({0})'.format(u','.join(fieldsList)).replace(u'.', u'/')
    else:
      fields = None
    printGettingAccountEntitiesInfo(EN_CROS_DEVICE, qualifier=queryQualifier(query))
    page_message = getPageMessage()
    try:
      entityList = callGAPIpages(cd.chromeosdevices(), u'list', u'chromeosdevices',
                                 page_message=page_message,
                                 throw_reasons=[GAPI_INVALID_INPUT, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                                 customerId=GC_Values[GC_CUSTOMER_ID], query=query, projection=projection,
                                 orderBy=orderBy, sortOrder=sortOrder, fields=fields, maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
      for cros in entityList:
        _printCrOS(cros)
    except GAPI_invalidInput:
      entityActionFailedWarning(EN_CROS_DEVICE, PHRASE_LIST, invalidQuery(query))
      return
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      accessErrorExit(cd)
  else:
    if fieldsList:
      fields = u','.join(set(fieldsList)).replace(u'.', u'/')
      selectLookup = len(fieldsList) > 1
    else:
      fields = None
      selectLookup = True
    if selectLookup:
      _batchPrintCrOS(entityList)
    else:
      for cros in entityList:
        _printCrOS({u'deviceId': cros})
  if sortHeaders:
    sortCSVTitles([u'deviceId',], titles)
  if select and orderBy:
    import operator
    csvRows.sort(key=operator.itemgetter(orderBy), reverse=sortOrder == u'DESCENDING')
  writeCSVfile(csvRows, titles, u'CrOS', todrive)

# Utilities for mobile commands
#
MOBILE_ACTION_CHOICE_MAP = {
  u'accountwipe': u'admin_account_wipe',
  u'adminaccountwipe': u'admin_account_wipe',
  u'wipeaccount': u'admin_account_wipe',
  u'adminremotewipe': u'admin_remote_wipe',
  u'wipe': u'admin_remote_wipe',
  u'approve': u'approve',
  u'block': u'action_block',
  u'cancelremotewipethenactivate': u'cancel_remote_wipe_then_activate',
  u'cancelremotewipethenblock': u'cancel_remote_wipe_then_block',
  }

def getMobileDeviceEntity():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  if checkArgumentPresent(QUERY_ARGUMENT):
    query = getString(OB_QUERY)
  else:
    resourceId = getString(OB_MOBILE_DEVICE_ENTITY)
    if resourceId[:6].lower() == u'query:':
      query = resourceId[6:]
    else:
      putArgumentBack()
      query = None
  if not query:
    return (getEntityList(OB_MOBILE_ENTITY), cd)
  try:
    devices = callGAPIpages(cd.mobiledevices(), u'list', u'mobiledevices',
                            throw_reasons=[GAPI_INVALID_INPUT, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                            customerId=GC_Values[GC_CUSTOMER_ID], query=query,
                            fields=u'nextPageToken,mobiledevices(resourceId)')
    return ([mobile[u'resourceId'] for mobile in devices], cd)
  except GAPI_invalidInput:
    putArgumentBack()
    usageErrorExit(PHRASE_INVALID_QUERY)
  except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
    accessErrorExit(cd)

# gam update mobile|mobiles <MobileDeviceEntity> <MobileAttributes>
def doUpdateMobileDevices():
  entityList, cd = getMobileDeviceEntity()
  action_body = {}
  patch_body = {}
  doPatch = doAction = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'action':
      action_body[u'action'] = getChoice(MOBILE_ACTION_CHOICE_MAP, mapChoice=True)
      doAction = True
    elif myarg == u'model':
      patch_body[u'model'] = getString(OB_STRING)
      doPatch = True
    elif myarg == u'os':
      patch_body[u'os'] = getString(OB_STRING)
      doPatch = True
    elif myarg == u'useragent':
      patch_body[u'userAgent'] = getString(OB_STRING)
      doPatch = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(entityList)
  for resourceId in entityList:
    i += 1
    try:
      if doPatch:
        callGAPI(cd.mobiledevices(), u'patch',
                 throw_reasons=[GAPI_RESOURCE_ID_NOT_FOUND, GAPI_INTERNAL_ERROR, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                 customerId=GC_Values[GC_CUSTOMER_ID], resourceId=resourceId, body=patch_body)
        entityActionPerformed(EN_MOBILE_DEVICE, resourceId, i, count)
      if doAction:
        callGAPI(cd.mobiledevices(), u'action',
                 throw_reasons=[GAPI_RESOURCE_ID_NOT_FOUND, GAPI_INTERNAL_ERROR, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                 customerId=GC_Values[GC_CUSTOMER_ID], resourceId=resourceId, body=action_body)
        printEntityKVList(EN_MOBILE_DEVICE, resourceId,
                          [PHRASE_ACTION_APPLIED, action_body[u'action']],
                          i, count)
    except GAPI_resourceIdNotFound:
      entityActionFailedWarning(EN_MOBILE_DEVICE, resourceId, PHRASE_DOES_NOT_EXIST, i, count)
    except (GAPI_internalError, GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      accessErrorExit(cd)

# gam delete mobile|mobiles <MobileDeviceEntity>
def doDeleteMobileDevices():
  entityList, cd = getMobileDeviceEntity()
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for resourceId in entityList:
    i += 1
    try:
      callGAPI(cd.mobiledevices(), u'delete',
               throw_reasons=[GAPI_RESOURCE_ID_NOT_FOUND, GAPI_INTERNAL_ERROR, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
               customerId=GC_Values[GC_CUSTOMER_ID], resourceId=resourceId)
      entityActionPerformed(EN_MOBILE_DEVICE, resourceId, i, count)
    except GAPI_resourceIdNotFound:
      entityActionFailedWarning(EN_MOBILE_DEVICE, resourceId, PHRASE_DOES_NOT_EXIST, i, count)
    except (GAPI_internalError, GAPI_badRequest, GAPI_resourceIdNotFound, GAPI_forbidden):
      accessErrorExit(cd)

# gam info mobile|mobiles <MobileDeviceEntity>
def doInfoMobileDevices():
  entityList, cd = getMobileDeviceEntity()
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for resourceId in entityList:
    i += 1
    try:
      info = callGAPI(cd.mobiledevices(), u'get',
                      throw_reasons=[GAPI_RESOURCE_ID_NOT_FOUND, GAPI_INTERNAL_ERROR, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                      customerId=GC_Values[GC_CUSTOMER_ID], resourceId=resourceId)
      printEntityName(EN_MOBILE_DEVICE, resourceId, i, count)
      incrementIndentLevel()
      showJSON(None, info)
      decrementIndentLevel()
    except GAPI_resourceIdNotFound:
      entityActionFailedWarning(EN_MOBILE_DEVICE, resourceId, PHRASE_DOES_NOT_EXIST, i, count)
    except (GAPI_internalError, GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      accessErrorExit(cd)
    printBlankLine()

MOBILE_ORDERBY_CHOICES_MAP = {
  u'deviceid': u'deviceId',
  u'email': u'email',
  u'lastsync': u'lastSync',
  u'model': u'model',
  u'name': u'name',
  u'os': u'os',
  u'status': u'status',
  u'type': u'type',
  }

# gam print mobile [todrive] [query <QueryMobile>] [basic|full]
#	[orderby <MobileOrderByFieldName> [ascending|descending]]
def doPrintMobileDevices():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'resourceId',])
  query = projection = orderBy = sortOrder = None
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'query':
      query = getString(OB_QUERY)
    elif myarg == u'orderby':
      orderBy = getChoice(MOBILE_ORDERBY_CHOICES_MAP, mapChoice=True)
      sortOrder = getChoice(SORTORDER_CHOICES_MAP, defaultChoice=u'ascending', mapChoice=True)
    elif myarg in PROJECTION_CHOICES_MAP:
      projection = PROJECTION_CHOICES_MAP[myarg]
    else:
      unknownArgumentExit()
  try:
    printGettingAccountEntitiesInfo(EN_MOBILE_DEVICE, qualifier=queryQualifier(query))
    page_message = getPageMessage()
    devices = callGAPIpages(cd.mobiledevices(), u'list', u'mobiledevices',
                            page_message=page_message,
                            throw_reasons=[GAPI_INVALID_INPUT, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                            customerId=GC_Values[GC_CUSTOMER_ID], query=query, projection=projection,
                            orderBy=orderBy, sortOrder=sortOrder, maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
    for mobile in devices:
      mobiledevice = {}
      for attrib in mobile:
        if attrib in [u'kind', u'etag', u'applications']:
          continue
        if attrib not in titles[u'set']:
          addTitleToCSVfile(attrib, titles)
        if attrib in [u'name', u'email']:
          if mobile[attrib]:
            mobiledevice[attrib] = mobile[attrib][0]
        else:
          mobiledevice[attrib] = mobile[attrib]
      csvRows.append(mobiledevice)
  except GAPI_invalidInput:
    entityActionFailedWarning(EN_MOBILE_DEVICE, PHRASE_LIST, invalidQuery(query))
  except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
    accessErrorExit(cd)
  writeCSVfile(csvRows, titles, u'Mobile', todrive)

GROUP_ATTRIBUTES = {
  u'allowexternalmembers': [u'allowExternalMembers', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'allowgooglecommunication': [u'allowGoogleCommunication', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'allowwebposting': [u'allowWebPosting', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'archiveonly': [u'archiveOnly', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'customfootertext': [u'customFooterText', {GC_VAR_TYPE: GC_TYPE_STRING}],
  u'customreplyto': [u'customReplyTo', {GC_VAR_TYPE: GC_TYPE_EMAIL}],
  u'defaultmessagedenynotificationtext': [u'defaultMessageDenyNotificationText', {GC_VAR_TYPE: GC_TYPE_STRING}],
  u'description': [u'description', {GC_VAR_TYPE: GC_TYPE_STRING}],
  u'gal': [u'includeInGlobalAddressList', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'includecustomfooter': [u'includeCustomFooter', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'includeinglobaladdresslist': [u'includeInGlobalAddressList', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'isarchived': [u'isArchived', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'maxmessagebytes': [u'maxMessageBytes', {GC_VAR_TYPE: GC_TYPE_INTEGER}],
  u'memberscanpostasthegroup': [u'membersCanPostAsTheGroup', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'messagedisplayfont': [u'messageDisplayFont', {GC_VAR_TYPE: GC_TYPE_CHOICE,
                                                  u'choices': {u'defaultfont': u'DEFAULT_FONT', u'fixedwidthfont': u'FIXED_WIDTH_FONT',}}],
  u'messagemoderationlevel': [u'messageModerationLevel', {GC_VAR_TYPE: GC_TYPE_CHOICE,
                                                          u'choices': {u'moderateallmessages': u'MODERATE_ALL_MESSAGES', u'moderatenonmembers': u'MODERATE_NON_MEMBERS',
                                                                       u'moderatenewmembers': u'MODERATE_NEW_MEMBERS', u'moderatenone': u'MODERATE_NONE',}}],
  u'name': [u'name', {GC_VAR_TYPE: GC_TYPE_STRING}],
  u'primarylanguage': [u'primaryLanguage', {GC_VAR_TYPE: GC_TYPE_LANGUAGE}],
  u'replyto': [u'replyTo', {GC_VAR_TYPE: GC_TYPE_CHOICE,
                            u'choices': {u'replytocustom': u'REPLY_TO_CUSTOM', u'replytosender': u'REPLY_TO_SENDER', u'replytolist': u'REPLY_TO_LIST',
                                         u'replytoowner': u'REPLY_TO_OWNER', u'replytoignore': u'REPLY_TO_IGNORE', u'replytomanagers': u'REPLY_TO_MANAGERS',}}],
  u'sendmessagedenynotification': [u'sendMessageDenyNotification', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'showingroupdirectory': [u'showInGroupDirectory', {GC_VAR_TYPE: GC_TYPE_BOOLEAN}],
  u'spammoderationlevel': [u'spamModerationLevel', {GC_VAR_TYPE: GC_TYPE_CHOICE,
                                                    u'choices': {u'allow': u'ALLOW', u'moderate': u'MODERATE', u'silentlymoderate': u'SILENTLY_MODERATE', u'reject': u'REJECT',}}],
  u'whocanadd': [u'whoCanAdd', {GC_VAR_TYPE: GC_TYPE_CHOICE,
                                u'choices': {u'allmemberscanadd': u'ALL_MEMBERS_CAN_ADD', u'allmanagerscanadd': u'ALL_MANAGERS_CAN_ADD', u'nonecanadd': u'NONE_CAN_ADD',}}],
  u'whocancontactowner': [u'whoCanContactOwner', {GC_VAR_TYPE: GC_TYPE_CHOICE,
                                                  u'choices': {u'anyonecancontact': u'ANYONE_CAN_CONTACT', u'allindomaincancontact': u'ALL_IN_DOMAIN_CAN_CONTACT',
                                                               u'allmemberscancontact': u'ALL_MEMBERS_CAN_CONTACT', u'allmanagerscancontact': u'ALL_MANAGERS_CAN_CONTACT',}}],
  u'whocaninvite': [u'whoCanInvite', {GC_VAR_TYPE: GC_TYPE_CHOICE,
                                      u'choices': {u'allmemberscaninvite': u'ALL_MEMBERS_CAN_INVITE', u'allmanagerscaninvite': u'ALL_MANAGERS_CAN_INVITE', u'nonecaninvite': u'NONE_CAN_INVITE',}}],
  u'whocanjoin': [u'whoCanJoin', {GC_VAR_TYPE: GC_TYPE_CHOICE,
                                  u'choices': {u'anyonecanjoin': u'ANYONE_CAN_JOIN', u'allindomaincanjoin': u'ALL_IN_DOMAIN_CAN_JOIN',
                                               u'invitedcanjoin': u'INVITED_CAN_JOIN', u'canrequesttojoin': u'CAN_REQUEST_TO_JOIN',}}],
  u'whocanleavegroup': [u'whoCanLeaveGroup', {GC_VAR_TYPE: GC_TYPE_CHOICE,
                                              u'choices': {u'allmanagerscanleave': u'ALL_MANAGERS_CAN_LEAVE', u'allmemberscanleave': u'ALL_MEMBERS_CAN_LEAVE', u'nonecanleave': u'NONE_CAN_LEAVE',}}],
  u'whocanpostmessage': [u'whoCanPostMessage', {GC_VAR_TYPE: GC_TYPE_CHOICE,
                                                u'choices': {u'nonecanpost': u'NONE_CAN_POST', u'allmanagerscanpost': u'ALL_MANAGERS_CAN_POST', u'allmemberscanpost': u'ALL_MEMBERS_CAN_POST',
                                                             u'allindomaincanpost': u'ALL_IN_DOMAIN_CAN_POST', u'anyonecanpost': u'ANYONE_CAN_POST',}}],
  u'whocanviewgroup': [u'whoCanViewGroup', {GC_VAR_TYPE: GC_TYPE_CHOICE,
                                            u'choices': {u'anyonecanview': u'ANYONE_CAN_VIEW', u'allindomaincanview': u'ALL_IN_DOMAIN_CAN_VIEW',
                                                         u'allmemberscanview': u'ALL_MEMBERS_CAN_VIEW', u'allmanagerscanview': u'ALL_MANAGERS_CAN_VIEW',}}],
  u'whocanviewmembership': [u'whoCanViewMembership', {GC_VAR_TYPE: GC_TYPE_CHOICE,
                                                      u'choices': {u'allindomaincanview': u'ALL_IN_DOMAIN_CAN_VIEW', u'allmemberscanview': u'ALL_MEMBERS_CAN_VIEW',
                                                                   u'allmanagerscanview': u'ALL_MANAGERS_CAN_VIEW',}}],
  }

def getGroupAttrValue(argument, gs_body):
  attrProperties = GROUP_ATTRIBUTES.get(argument)
  if not attrProperties:
    unknownArgumentExit()
  attrName = attrProperties[0]
  attribute = attrProperties[1]
  attrType = attribute[GC_VAR_TYPE]
  if attrType == GC_TYPE_BOOLEAN:
    gs_body[attrName] = getBoolean()
  elif attrType == GC_TYPE_STRING:
    gs_body[attrName] = getString(OB_STRING)
  elif attrType == GC_TYPE_CHOICE:
    gs_body[attrName] = getChoice(attribute[u'choices'], mapChoice=True)
  elif attrType == GC_TYPE_EMAIL:
    gs_body[attrName] = getEmailAddress(noUid=True)
  elif attrType == GC_TYPE_LANGUAGE:
    gs_body[attrName] = getChoice(LANGUAGE_CODES_MAP, mapChoice=True)
  else: # GC_TYPE_INTEGER
    if attrName == u'maxMessageBytes':
      gs_body[attrName] = getMaxMessageBytes()
    else:
      gs_body[attrName] = getInteger()

# gam create group <EmailAddress> <GroupAttributes>
def doCreateGroup():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  body = {u'email': getEmailAddress(noUid=True)}
  gs_body = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'name':
      body[u'name'] = getString(OB_STRING)
    elif myarg == u'description':
      body[u'description'] = getString(OB_STRING)
    else:
      getGroupAttrValue(myarg, gs_body)
  body.setdefault(u'name', body[u'email'])
  try:
    callGAPI(cd.groups(), u'insert',
             throw_reasons=[GAPI_DUPLICATE, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
             body=body, fields=u'email')
    entityActionPerformed(EN_GROUP, body[u'email'])
    if gs_body:
      gs = buildGAPIObject(GAPI_GROUPSSETTINGS_API)
      callGAPI(gs.groups(), u'patch', retry_reasons=[GAPI_SERVICE_LIMIT],
               groupUniqueId=body[u'email'], body=gs_body)
  except GAPI_duplicate:
    entityDuplicateWarning(EN_GROUP, body[u'email'])
  except (GAPI_domainNotFound, GAPI_forbidden):
    entityUnknownWarning(EN_GROUP, body[u'email'])

def checkGroupExists(cd, group, i=0, count=0):
  group = normalizeEmailAddressOrUID(group)
  try:
    result = callGAPI(cd.groups(), u'get',
                      throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_DOMAIN_NOT_FOUND, GAPI_BACKEND_ERROR, GAPI_SYSTEM_ERROR, GAPI_FORBIDDEN],
                      groupKey=group, fields=u'email')
    return result[u'email']
  except (GAPI_groupNotFound, GAPI_badRequest, GAPI_domainNotFound, GAPI_backendError, GAPI_systemError, GAPI_forbidden):
    entityUnknownWarning(EN_GROUP, group, i, count)
    return None

UPDATE_GROUP_SUBCMDS = [u'add', u'clear', u'delete', u'remove', u'sync', u'update']

UPDATE_GROUP_ROLES_MAP = {
  u'owner': ROLE_OWNER,
  u'owners': ROLE_OWNER,
  u'manager': ROLE_MANAGER,
  u'managers': ROLE_MANAGER,
  u'member': ROLE_MEMBER,
  u'members': ROLE_MEMBER,
  }

# gam update groups <GroupEntity> [admincreated <Boolean>] [email <EmailAddress>] <GroupAttributes>
# gam update groups <GroupEntity> add [owner|manager|member] [notsuspended] <UserTypeEntity>
# gam update groups <GroupEntity> delete|remove [owner|manager|member] <UserTypeEntity>
# gam update groups <GroupEntity> sync [owner|manager|member] [notsuspended] <UserTypeEntity>
# gam update groups <GroupEntity> update [owner|manager|member] <UserTypeEntity>
# gam update groups <GroupEntity> clear [owner] [manager] [member]
def doUpdateGroups():
  updateGroups(getEntityList(OB_GROUP_ENTITY))

# gam update group <GroupItem> add [owner|manager|member] [notsuspended] <UserTypeEntity>
# gam update group <GroupItem> [admincreated <Boolean>] [email <EmailAddress>] <GroupAttributes>
# gam update group <GroupItem> delete|remove [owner|manager|member] <UserTypeEntity>
# gam update group <GroupItem> sync [owner|manager|member] [notsuspended] <UserTypeEntity>
# gam update group <GroupItem> update [owner|manager|member] <UserTypeEntity>
# gam update group <GroupItem> clear [owner] [manager] [member]
def doUpdateGroup():
  updateGroups(getStringReturnInList(OB_GROUP_ITEM))

def updateGroups(entityList):
  def _callbackAddMembersToGroup(request_id, response, exception):
    REASON_TO_MESSAGE_MAP = {GAPI_DUPLICATE: PHRASE_DUPLICATE, GAPI_MEMBER_NOT_FOUND: PHRASE_DOES_NOT_EXIST,
                             GAPI_RESOURCE_NOT_FOUND: PHRASE_DOES_NOT_EXIST, GAPI_INVALID_MEMBER: PHRASE_INVALID_ROLE,
                             GAPI_CYCLIC_MEMBERSHIPS_NOT_ALLOWED: PHRASE_WOULD_MAKE_MEMBERSHIP_CYCLE}
    ri = request_id.splitlines()
    if exception is None:
      member = response.get(u'email', None)
      if member:
        member = member.lower()
      else:
        member = response[u'id']
      entityItemValueActionPerformed(EN_GROUP, ri[RI_ENTITY], ri[RI_ROLE], member, int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
      entityItemValueActionFailedWarning(EN_GROUP, ri[RI_ENTITY], ri[RI_ROLE], ri[RI_ITEM], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _batchAddMembersToGroup(cd, group, i, count, addMembers, role):
    setActionName(AC_ADD)
    jcount = len(addMembers)
    entityPerformActionNumItems(EN_GROUP, group, jcount, role, i, count)
    incrementIndentLevel()
    bcount = 0
    bsize = GC_Values[GC_BATCH_SIZE]
    if bsize > 1:
      dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackAddMembersToGroup)
    j = 0
    for member in addMembers:
      j += 1
      member = normalizeEmailAddressOrUID(member)
      if member.find(u'@') != -1:
        body = {u'role': role, u'email': member}
      else:
        body = {u'role': role, u'id': member}
      if bsize > 1:
        parameters = dict([(u'groupKey', group), (u'body', body)]+GM_Globals[GM_EXTRA_ARGS_LIST])
        dbatch.add(cd.members().insert(**parameters), request_id=batchRequestID(group, i, count, j, jcount, member, role))
        bcount += 1
        if bcount == bsize:
          dbatch.execute()
          dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackAddMembersToGroup)
          bcount = 0
      else:
        try:
          callGAPI(cd.members(), u'insert',
                   throw_reasons=[GAPI_DUPLICATE, GAPI_MEMBER_NOT_FOUND, GAPI_INVALID_MEMBER, GAPI_CYCLIC_MEMBERSHIPS_NOT_ALLOWED],
                   groupKey=group, body=body)
          entityItemValueActionPerformed(EN_GROUP, group, role, member, j, jcount)
        except GAPI_duplicate:
          entityItemValueActionFailedWarning(EN_GROUP, group, role, member, PHRASE_DUPLICATE, j, jcount)
        except GAPI_memberNotFound:
          entityItemValueActionFailedWarning(EN_GROUP, group, role, member, PHRASE_DOES_NOT_EXIST, j, jcount)
        except GAPI_invalidMember:
          entityItemValueActionFailedWarning(EN_GROUP, group, role, member, PHRASE_INVALID_ROLE, j, jcount)
        except GAPI_cyclicMembershipsNotAllowed:
          entityItemValueActionFailedWarning(EN_GROUP, group, role, member, PHRASE_WOULD_MAKE_MEMBERSHIP_CYCLE, j, jcount)
    if bcount > 0:
      dbatch.execute()
    decrementIndentLevel()

  def _callbackRemoveMembersFromGroup(request_id, response, exception):
    REASON_TO_MESSAGE_MAP = {GAPI_MEMBER_NOT_FOUND: u'{0} {1}'.format(PHRASE_NOT_A, singularEntityName(EN_MEMBER)),
                             GAPI_INVALID_MEMBER: PHRASE_DOES_NOT_EXIST}
    ri = request_id.splitlines()
    if exception is None:
      entityItemValueActionPerformed(EN_GROUP, ri[RI_ENTITY], ri[RI_ROLE], ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
      entityItemValueActionFailedWarning(EN_GROUP, ri[RI_ENTITY], ri[RI_ROLE], ri[RI_ITEM], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _batchRemoveMembersFromGroup(cd, group, i, count, removeMembers, role):
    setActionName(AC_REMOVE)
    jcount = len(removeMembers)
    entityPerformActionNumItems(EN_GROUP, group, jcount, role, i, count)
    incrementIndentLevel()
    bcount = 0
    bsize = GC_Values[GC_BATCH_SIZE]
    if bsize > 1:
      dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackRemoveMembersFromGroup)
    j = 0
    for member in removeMembers:
      j += 1
      member = normalizeEmailAddressOrUID(member)
      if bsize > 1:
        parameters = dict([(u'groupKey', group), (u'memberKey', member)]+GM_Globals[GM_EXTRA_ARGS_LIST])
        dbatch.add(cd.members().delete(**parameters), request_id=batchRequestID(group, i, count, j, jcount, member, role))
        bcount += 1
        if bcount == GC_Values[GC_BATCH_SIZE]:
          dbatch.execute()
          dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackRemoveMembersFromGroup)
          bcount = 0
      else:
        try:
          callGAPI(cd.members(), u'delete',
                   throw_reasons=[GAPI_MEMBER_NOT_FOUND, GAPI_INVALID_MEMBER],
                   groupKey=group, memberKey=member)
          entityItemValueActionPerformed(EN_GROUP, group, role, member, j, jcount)
        except GAPI_memberNotFound:
          entityItemValueActionFailedWarning(EN_GROUP, group, role, member, u'{0} {1}'.format(PHRASE_NOT_A, singularEntityName(EN_MEMBER)), j, jcount)
        except GAPI_invalidMember:
          entityItemValueActionFailedWarning(EN_GROUP, group, role, member, PHRASE_DOES_NOT_EXIST, j, jcount)
    if bcount > 0:
      dbatch.execute()
    decrementIndentLevel()

  def _callbackUpdateMembersInGroup(request_id, response, exception):
    REASON_TO_MESSAGE_MAP = {GAPI_MEMBER_NOT_FOUND: u'{0} {1}'.format(PHRASE_NOT_A, singularEntityName(EN_MEMBER)),
                             GAPI_INVALID_MEMBER: PHRASE_DOES_NOT_EXIST}
    ri = request_id.splitlines()
    if exception is None:
      entityItemValueActionPerformed(EN_GROUP, ri[RI_ENTITY], ri[RI_ROLE], response[u'email'], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
      entityItemValueActionFailedWarning(EN_GROUP, ri[RI_ENTITY], ri[RI_ROLE], ri[RI_ITEM], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _batchUpdateMembersInGroup(cd, group, i, count, updateMembers, role):
    setActionName(AC_UPDATE)
    body = {u'role': role}
    jcount = len(updateMembers)
    entityPerformActionNumItems(EN_GROUP, group, jcount, role, i, count)
    incrementIndentLevel()
    bcount = 0
    bsize = GC_Values[GC_BATCH_SIZE]
    if bsize > 1:
      dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackUpdateMembersInGroup)
    j = 0
    for member in updateMembers:
      j += 1
      member = normalizeEmailAddressOrUID(member)
      if bsize > 1:
        parameters = dict([(u'groupKey', group), (u'memberKey', member), (u'body', body)]+GM_Globals[GM_EXTRA_ARGS_LIST])
        dbatch.add(cd.members().update(**parameters), request_id=batchRequestID(group, i, count, j, jcount, member, role))
        bcount += 1
        if bcount == bsize:
          dbatch.execute()
          dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackUpdateMembersInGroup)
          bcount = 0
      else:
        try:
          callGAPI(cd.members(), u'update',
                   throw_reasons=[GAPI_MEMBER_NOT_FOUND, GAPI_INVALID_MEMBER],
                   groupKey=group, memberKey=member, body=body)
          entityItemValueActionPerformed(EN_GROUP, group, role, member, j, jcount)
        except GAPI_memberNotFound:
          entityItemValueActionFailedWarning(EN_GROUP, group, role, member, u'{0} {1}'.format(PHRASE_NOT_A, singularEntityName(EN_MEMBER)), j, jcount)
        except GAPI_invalidMember:
          entityItemValueActionFailedWarning(EN_GROUP, group, role, member, PHRASE_DOES_NOT_EXIST, j, jcount)
    if bcount > 0:
      dbatch.execute()
    decrementIndentLevel()

  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  CL_subCommand = getChoice(UPDATE_GROUP_SUBCMDS, defaultChoice=None)
  if not CL_subCommand:
    body = {}
    gs_body = {}
    while CL_argvI < CL_argvLen:
      myarg = getArgument()
      if myarg == u'email':
        body[u'email'] = getEmailAddress(noUid=True)
      elif myarg == u'admincreated':
        body[u'adminCreated'] = getBoolean()
      else:
        getGroupAttrValue(myarg, gs_body)
    setActionName(AC_UPDATE)
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      group = normalizeEmailAddressOrUID(group)
      if body or (group.find(u'@') == -1): # group settings API won't take uid so we make sure cd API is used so that we can grab real email.
        try:
          cd_result = callGAPI(cd.groups(), u'patch',
                               throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND,
                                              GAPI_BACKEND_ERROR, GAPI_SYSTEM_ERROR, GAPI_FORBIDDEN],
                               groupKey=group, body=body, fields=u'email')
          group = cd_result[u'email']
        except (GAPI_groupNotFound, GAPI_domainNotFound, GAPI_backendError, GAPI_systemError, GAPI_forbidden):
          entityUnknownWarning(EN_GROUP, group, i, count)
          continue
      if gs_body:
        gs = buildGAPIObject(GAPI_GROUPSSETTINGS_API)
        try:
          callGAPI(gs.groups(), u'patch',
                   throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND,
                                  GAPI_BACKEND_ERROR, GAPI_SYSTEM_ERROR, GAPI_FORBIDDEN],
                   retry_reasons=[GAPI_SERVICE_LIMIT],
                   groupUniqueId=group, body=gs_body)
        except (GAPI_groupNotFound, GAPI_domainNotFound, GAPI_backendError, GAPI_systemError, GAPI_forbidden):
          entityUnknownWarning(EN_GROUP, group, i, count)
          continue
      entityActionPerformed(EN_GROUP, group, i, count)
  elif CL_subCommand == u'add':
    role = getChoice(UPDATE_GROUP_ROLES_MAP, defaultChoice=ROLE_MEMBER, mapChoice=True)
    checkNotSuspended = checkArgumentPresent(NOTSUSPENDED_ARGUMENT)
    _, addMembers = getEntityToModify(defaultEntityType=CL_ENTITY_USERS, checkNotSuspended=checkNotSuspended)
    groupMemberLists = addMembers if isinstance(addMembers, dict) else None
    checkForExtraneousArguments()
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      if groupMemberLists:
        addMembers = groupMemberLists[group]
      group = checkGroupExists(cd, group, i, count)
      if group:
        _batchAddMembersToGroup(cd, group, i, count, addMembers, role)
  elif CL_subCommand in [u'delete', u'remove']:
    role = getChoice(UPDATE_GROUP_ROLES_MAP, defaultChoice=ROLE_MEMBER, mapChoice=True) # Argument ignored
    _, removeMembers = getEntityToModify(defaultEntityType=CL_ENTITY_USERS)
    groupMemberLists = removeMembers if isinstance(removeMembers, dict) else None
    checkForExtraneousArguments()
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      if groupMemberLists:
        removeMembers = groupMemberLists[group]
      group = checkGroupExists(cd, group, i, count)
      if group:
        _batchRemoveMembersFromGroup(cd, group, i, count, removeMembers, role)
  elif CL_subCommand == u'sync':
    role = getChoice(UPDATE_GROUP_ROLES_MAP, defaultChoice=ROLE_MEMBER, mapChoice=True)
    checkNotSuspended = checkArgumentPresent(NOTSUSPENDED_ARGUMENT)
    _, syncMembers = getEntityToModify(defaultEntityType=CL_ENTITY_USERS, checkNotSuspended=checkNotSuspended)
    groupMemberLists = syncMembers if isinstance(syncMembers, dict) else None
    if not groupMemberLists:
      syncMembersSet = set()
      for member in syncMembers:
        syncMembersSet.add(convertUserUIDtoEmailAddress(member))
    checkForExtraneousArguments()
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      if groupMemberLists:
        syncMembersSet = set()
        for member in groupMemberLists[group]:
          syncMembersSet.add(convertUserUIDtoEmailAddress(member))
      group = checkGroupExists(cd, group, i, count)
      if group:
        currentMembersSet = set(getUsersToModify(CL_ENTITY_GROUP, group, memberRole=role))
        _batchAddMembersToGroup(cd, group, i, count, list(syncMembersSet-currentMembersSet), role)
        _batchRemoveMembersFromGroup(cd, group, i, count, list(currentMembersSet-syncMembersSet), role)
  elif CL_subCommand == u'update':
    role = getChoice(UPDATE_GROUP_ROLES_MAP, defaultChoice=ROLE_MEMBER, mapChoice=True)
    _, updateMembers = getEntityToModify(defaultEntityType=CL_ENTITY_USERS)
    groupMemberLists = updateMembers if isinstance(updateMembers, dict) else None
    checkForExtraneousArguments()
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      if groupMemberLists:
        updateMembers = groupMemberLists[group]
      group = checkGroupExists(cd, group, i, count)
      if group:
        _batchUpdateMembersInGroup(cd, group, i, count, updateMembers, role)
  else: #clear
    roles = []
    while CL_argvI < CL_argvLen:
      roles.append(getChoice(UPDATE_GROUP_ROLES_MAP, mapChoice=True))
    setActionName(AC_REMOVE)
    if roles:
      roles = u','.join(sorted(set(roles)))
    else:
      roles = ROLE_MEMBER
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      group = checkGroupExists(cd, group, i, count)
      if group:
        removeMembers = getUsersToModify(CL_ENTITY_GROUP, group, memberRole=roles)
        _batchRemoveMembersFromGroup(cd, group, i, count, removeMembers, ROLE_MEMBER)

# gam delete groups <GroupEntity>
def doDeleteGroups():
  deleteGroups(getEntityList(OB_GROUP_ENTITY))

# gam delete group <GroupItem>
def doDeleteGroup():
  deleteGroups(getStringReturnInList(OB_GROUP_ITEM))

def deleteGroups(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for group in entityList:
    i += 1
    group = normalizeEmailAddressOrUID(group)
    try:
      callGAPI(cd.groups(), u'delete',
               throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
               groupKey=group)
      entityActionPerformed(EN_GROUP, group, i, count)
    except (GAPI_groupNotFound, GAPI_domainNotFound, GAPI_forbidden):
      entityUnknownWarning(EN_GROUP, group, i, count)
#
# CL argument: [API field name, CSV field title]
GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP = {
  u'admincreated': [u'adminCreated', u'Admin_Created'],
  u'aliases': [u'aliases', u'Aliases', u'nonEditableAliases', u'NonEditableAliases'],
  u'description': [u'description', u'Description'],
  u'email': [u'email', u'Email'],
  u'id': [u'id', u'ID'],
  u'name': [u'name', u'Name'],
  }

INFO_GROUP_OPTIONS = [u'nousers', u'groups',]

# gam info groups <GroupEntity> [noaliases] [nousers] [groups] <GroupFieldName>* [fields <GroupFieldNameList>]
def doInfoGroups():
  infoGroups(getEntityList(OB_GROUP_ENTITY))

# gam info group <GroupItem> [noaliases] [nousers] [groups] <GroupFieldName>* [fields <GroupFieldNameList>]
def doInfoGroup():
  infoGroups(getStringReturnInList(OB_GROUP_ITEM))

def infoGroups(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  gs = buildGAPIObject(GAPI_GROUPSSETTINGS_API)
  getAliases = getUsers = True
  getGroups = getSettings = False
  cdfieldsList = gsfieldsList = None
  settings = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'nousers':
      getUsers = False
    elif myarg == u'noaliases':
      getAliases = False
    elif myarg == u'groups':
      getGroups = True
    elif myarg in GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP:
      if not cdfieldsList:
        cdfieldsList = [u'email',]
      cdfieldsList.extend([GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP[myarg][0],])
    elif myarg in GROUP_ATTRIBUTES:
      if not gsfieldsList:
        gsfieldsList = []
      gsfieldsList.extend([GROUP_ATTRIBUTES[myarg][0],])
    elif myarg == u'fields':
      if not cdfieldsList:
        cdfieldsList = [u'email',]
      if not gsfieldsList:
        gsfieldsList = []
      fieldNameList = getString(OB_FIELD_NAME_LIST)
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP:
          cdfieldsList.extend([GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP[field][0],])
        elif field in GROUP_ATTRIBUTES:
          gsfieldsList.extend([GROUP_ATTRIBUTES[field][0],])
        else:
          putArgumentBack()
          invalidChoiceExit(GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP.keys()+GROUP_ATTRIBUTES.keys())
# Ignore info user arguments that may have come from whatis
    elif myarg in INFO_USER_OPTIONS:
      if myarg == u'schemas':
        getString(OB_SCHEMA_NAME_LIST)
    else:
      unknownArgumentExit()
  if cdfieldsList:
    cdfieldsList = u','.join(set(cdfieldsList))
  if gsfieldsList == None:
    getSettings = True
  elif len(gsfieldsList) > 0:
    getSettings = True
    gsfieldsList = u','.join(set(gsfieldsList))
  i = 0
  count = len(entityList)
  for group in entityList:
    i += 1
    group = normalizeEmailAddressOrUID(group)
    try:
      basic_info = callGAPI(cd.groups(), u'get',
                            throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
                            groupKey=group, fields=cdfieldsList)
      group = basic_info[u'email']
      if getSettings:
        settings = callGAPI(gs.groups(), u'get',
                            throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
                            retry_reasons=[GAPI_SERVICE_LIMIT],
                            groupUniqueId=group, fields=gsfieldsList) # Use email address retrieved from cd since GS API doesn't support uid
      printEntityName(EN_GROUP, group, i, count)
      incrementIndentLevel()
      printKeyValueList([singularEntityName(EN_GROUP_SETTINGS), u''])
      incrementIndentLevel()
      for key, value in basic_info.items():
        if key in [u'kind', u'etag', u'email', u'aliases']:
          continue
        if isinstance(value, list):
          printKeyValueList([key, u''])
          incrementIndentLevel()
          for val in value:
            printKeyValueList([val])
          decrementIndentLevel()
        else:
          printKeyValueList([key, value])
      for key, value in settings.items():
        if key in [u'kind', u'etag', u'email', u'name', u'description']:
          continue
        if key == u'maxMessageBytes':
          value = formatMaxMessageBytes(value)
        printKeyValueList([key, value])
      decrementIndentLevel()
      if getAliases:
        aliases = basic_info.get(u'aliases', [])
        if aliases:
          printKeyValueList([pluralEntityName(EN_EMAIL_ALIAS), u''])
          incrementIndentLevel()
          for alias in aliases:
            printKeyValueList([alias])
          decrementIndentLevel()
      if getGroups:
        groups = callGAPIpages(cd.groups(), u'list', u'groups',
                               throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
                               userKey=group, fields=u'nextPageToken,groups(name,email)')
        printKeyValueList([pluralEntityName(EN_GROUP), u'({0})'.format(len(groups))])
        incrementIndentLevel()
        for groupm in groups:
          printKeyValueList([groupm[u'name'], groupm[u'email']])
        decrementIndentLevel()
      if getUsers:
        members = callGAPIpages(cd.members(), u'list', u'members',
                                throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
                                groupKey=group)
        printKeyValueList([pluralEntityName(EN_MEMBER), u''])
        incrementIndentLevel()
        for member in members:
          try:
            printKeyValueList([member[u'role'].lower(), u'{0} ({1})'.format(member[u'email'], member[u'type'].lower())])
          except KeyError:
            try:
              printKeyValueList([u'Member', u'{0} ({1})'.format(member[u'email'], member[u'type'].lower())])
            except KeyError:
              printKeyValueList([u'Member', u' {0} ({1})'.format(member[u'id'], member[u'type'].lower())])
        decrementIndentLevel()
        printKeyValueList([u'Total users in group', len(members)])
      decrementIndentLevel()
    except (GAPI_groupNotFound, GAPI_domainNotFound, GAPI_forbidden):
      entityUnknownWarning(EN_GROUP, group, i, count)

def groupQuery(domain, usemember):
  if domain:
    if usemember:
      return'{0}={1}, {2}={3}'.format(singularEntityName(EN_DOMAIN), domain, singularEntityName(EN_MEMBER), usemember)
    return u'{0}={1}'.format(singularEntityName(EN_DOMAIN), domain)
  if usemember:
    return u'{0}={1}'.format(singularEntityName(EN_MEMBER), usemember)
  return u''

# gam print groups [todrive] ([domain <DomainName>] [member <UserItem>])|[select <GroupEntity>]
#	[maxresults <Number>] [delimiter <String>]
#	[members] [owners] [managers] <GroupFieldName>* [fields <GroupFieldNameList>] [settings]
def doPrintGroups():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  members = owners = managers = False
  customer = GC_Values[GC_CUSTOMER_ID]
  domain = usemember = None
  aliasDelimiter = u' '
  memberDelimiter = u'\n'
  todrive = False
  maxResults = None
  cdfieldsList = []
  gsfieldsList = []
  fieldsTitles = {}
  titles, csvRows = initializeTitlesCSVfile(None)
  addFieldTitleToCSVfile(u'email', GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP, cdfieldsList, fieldsTitles, titles)
  roles = []
  getSettings = False
  entityList = None
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'domain':
      domain = getString(OB_DOMAIN_NAME).lower()
      customer = None
    elif myarg == u'member':
      usemember = getEmailAddress()
      customer = None
    elif myarg == u'select':
      entityList = getEntityList(OB_GROUP_ENTITY)
    elif myarg == u'maxresults':
      maxResults = getInteger(minVal=1)
    elif myarg == u'delimiter':
      aliasDelimiter = memberDelimiter = getString(OB_STRING)
    elif myarg in GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP:
      addFieldTitleToCSVfile(myarg, GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP, cdfieldsList, fieldsTitles, titles)
    elif myarg in GROUP_ATTRIBUTES:
      addFieldToCSVfile(myarg, {myarg: [GROUP_ATTRIBUTES[myarg][0]]}, gsfieldsList, fieldsTitles, titles)
    elif myarg == u'fields':
      fieldNameList = getString(OB_FIELD_NAME_LIST)
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP:
          addFieldTitleToCSVfile(field, GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP, cdfieldsList, fieldsTitles, titles)
        elif field in GROUP_ATTRIBUTES:
          addFieldToCSVfile(field, {field: [GROUP_ATTRIBUTES[field][0]]}, gsfieldsList, fieldsTitles, titles)
        else:
          putArgumentBack()
          invalidChoiceExit(GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP.keys()+GROUP_ATTRIBUTES.keys())
    elif myarg == u'members':
      if myarg not in roles:
        roles.append(ROLE_MEMBER)
        addTitleToCSVfile(u'Members', titles)
        members = True
    elif myarg == u'owners':
      if myarg not in roles:
        roles.append(ROLE_OWNER)
        addTitleToCSVfile(u'Owners', titles)
        owners = True
    elif myarg == u'managers':
      if myarg not in roles:
        roles.append(ROLE_MANAGER)
        addTitleToCSVfile(u'Managers', titles)
        managers = True
    elif myarg == u'settings':
      getSettings = True
    else:
      unknownArgumentExit()
  cdfields = u','.join(set(cdfieldsList))
  if len(gsfieldsList) > 0:
    getSettings = True
    gsfields = u','.join(set(gsfieldsList))
  elif getSettings:
    gsfields = None
  roles = u','.join(sorted(set(roles)))
  if entityList == None:
    printGettingAccountEntitiesInfo(EN_GROUP, qualifier=queryQualifier(groupQuery(domain, usemember)))
    page_message = getPageMessage(showTotal=False, showFirstLastItems=True)
    try:
      entityList = callGAPIpages(cd.groups(), u'list', u'groups',
                                 page_message=page_message, message_attribute=u'email',
                                 throw_reasons=[GAPI_INVALID_MEMBER, GAPI_DOMAIN_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                                 customer=customer, domain=domain, userKey=usemember,
                                 fields=u'nextPageToken,groups({0})'.format(cdfields),
                                 maxResults=maxResults)
    except GAPI_invalidMember:
      badRequestWarning(EN_GROUP, EN_MEMBER, usemember)
      entityList = []
    except GAPI_domainNotFound:
      badRequestWarning(EN_GROUP, EN_DOMAIN, domain)
      entityList = []
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      if domain:
        badRequestWarning(EN_GROUP, EN_DOMAIN, domain)
        entityList = []
      else:
        accessErrorExit(cd)
  i = 0
  count = len(entityList)
  for groupEntity in entityList:
    i += 1
    try:
      if not isinstance(groupEntity, dict):
        groupEmail = normalizeEmailAddressOrUID(groupEntity)
        groupEntity = callGAPI(cd.groups(), u'get',
                               throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
                               groupKey=groupEmail, fields=cdfields)
      groupEmail = groupEntity[u'email']
      group = {}
      for field in cdfieldsList:
        if field in groupEntity:
          if isinstance(groupEntity[field], list):
            group[fieldsTitles[field]] = aliasDelimiter.join(groupEntity[field])
          else:
            group[fieldsTitles[field]] = groupEntity[field]
      if roles:
        printGettingAllEntityItemsForWhom(roles, groupEmail, i, count)
        page_message = getPageMessageForWhom(showTotal=False, showFirstLastItems=True)
        groupMembers = callGAPIpages(cd.members(), u'list', u'members',
                                     page_message=page_message, message_attribute=u'email',
                                     throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
                                     groupKey=groupEmail, roles=roles, fields=u'nextPageToken,members(email,id,role)')
        if members:
          allMembers = []
        if managers:
          allManagers = []
        if owners:
          allOwners = []
        for member in groupMembers:
          member_email = member.get(u'email', member.get(u'id', None))
          if not member_email:
            sys.stderr.write(u' Not sure what to do with: {0}\n'.format(member))
            continue
          role = member.get(u'role', None)
          if role:
            if role == ROLE_MEMBER:
              if members:
                allMembers.append(member_email)
            elif role == ROLE_MANAGER:
              if managers:
                allManagers.append(member_email)
            elif role == ROLE_OWNER:
              if owners:
                allOwners.append(member_email)
            elif members:
              allMembers.append(member_email)
          elif members:
            allMembers.append(member_email)
        if members:
          group[u'Members'] = memberDelimiter.join(allMembers)
        if managers:
          group[u'Managers'] = memberDelimiter.join(allManagers)
        if owners:
          group[u'Owners'] = memberDelimiter.join(allOwners)
      if getSettings:
        printGettingAllEntityItemsForWhom(EN_GROUP_SETTINGS, groupEmail, i, count)
        gs = buildGAPIObject(GAPI_GROUPSSETTINGS_API)
        settings = callGAPI(gs.groups(), u'get',
                            throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
                            retry_reasons=[GAPI_SERVICE_LIMIT],
                            groupUniqueId=groupEmail, fields=gsfields)
        for key in settings:
          if key in [u'kind', u'etag', u'email', u'name', u'description']:
            continue
          setting_value = settings[key]
          if setting_value == None:
            setting_value = u''
          if key not in titles[u'set']:
            addTitleToCSVfile(key, titles)
          group[key] = setting_value
      csvRows.append(group)
    except (GAPI_groupNotFound, GAPI_domainNotFound, GAPI_forbidden):
      entityUnknownWarning(EN_GROUP, groupEmail, i, count)
  writeCSVfile(csvRows, titles, u'Groups', todrive)

def getGroupMembers(cd, groupEmail, membersList, membersSet, i, count, noduplicates, recursive, level):
  try:
    printGettingAllEntityItemsForWhom(EN_MEMBER, groupEmail, i, count)
    groupMembers = callGAPIpages(cd.members(), u'list', u'members',
                                 message_attribute=u'email',
                                 throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
                                 groupKey=groupEmail)
    if not recursive:
      if noduplicates:
        for member in groupMembers:
          if member[u'id'] in membersSet:
            continue
          membersSet.add(member[u'id'])
          membersList.append(member)
      else:
        membersList.extend(groupMembers)
    else:
      for member in groupMembers:
        if member[u'type'] == u'USER':
          if noduplicates:
            if member[u'id'] in membersSet:
              continue
            membersSet.add(member[u'id'])
          member[u'level'] = level
          member[u'subgroup'] = groupEmail
          membersList.append(member)
        else:
          getGroupMembers(cd, member[u'email'], membersList, membersSet, i, count, noduplicates, recursive, level+1)
  except (GAPI_groupNotFound, GAPI_domainNotFound, GAPI_forbidden):
    entityUnknownWarning(EN_GROUP, groupEmail, i, count)

GROUPMEMBERS_FIELD_NAMES_MAP = {
  u'email': u'email',
  u'groupemail': u'group',
  u'id': u'id',
  u'name': u'name',
  u'role': u'role',
  u'status': u'status',
  u'type': u'type',
  u'useremail': u'email',
  }

GROUPMEMBERS_DEFAULT_FIELDS = [u'id', u'role', u'group', u'email', u'type', u'status']

# gam print group-members|groups-members [todrive] ([domain <DomainName>] [member <UserItem>])|[group <GroupItem>]|[select <GroupEntity>]
#	[membernames] <MemberFiledName>* [fields <MembersFieldNameList>] [noduplicates] [recursive]
def doPrintGroupMembers():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  todrive = groupname = membernames = noduplicates = recursive = False
  customer = GC_Values[GC_CUSTOMER_ID]
  domain = usemember = None
  subTitle = u'{0} {1}'.format(PHRASE_ALL, pluralEntityName(EN_GROUP))
  fieldsList = []
  fieldsTitles = {}
  titles, csvRows = initializeTitlesCSVfile(None)
  entityList = None
  userFieldsList = []
  userFieldsTitles = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'domain':
      domain = getString(OB_DOMAIN_NAME).lower()
      customer = None
      subTitle = u'{0}={1}'.format(singularEntityName(EN_DOMAIN), domain)
    elif myarg == u'member':
      usemember = getEmailAddress()
      customer = None
      subTitle = u'{0}={1}'.format(singularEntityName(EN_MEMBER), usemember)
    elif myarg == u'group':
      entityList = getStringReturnInList(OB_GROUP_ITEM)
      subTitle = u'{0}={1}'.format(singularEntityName(EN_GROUP), entityList[0])
    elif myarg == u'select':
      entityList = getEntityList(OB_GROUP_ENTITY)
      subTitle = u'{0} {1}'.format(PHRASE_SELECTED, pluralEntityName(EN_GROUP))
    elif myarg in GROUPMEMBERS_FIELD_NAMES_MAP:
      myarg = GROUPMEMBERS_FIELD_NAMES_MAP[myarg]
      addFieldToCSVfile(myarg, {myarg: [myarg]}, fieldsList, fieldsTitles, titles)
    elif myarg == u'fields':
      fieldNameList = getString(OB_FIELD_NAME_LIST)
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in GROUPMEMBERS_FIELD_NAMES_MAP:
          field = GROUPMEMBERS_FIELD_NAMES_MAP[field]
          addFieldToCSVfile(field, {field: [field]}, fieldsList, fieldsTitles, titles)
        else:
          putArgumentBack()
          invalidChoiceExit(GROUPMEMBERS_FIELD_NAMES_MAP)
    elif myarg == u'membernames':
      membernames = True
    elif myarg == u'userfields':
      fieldNameList = getString(OB_FIELD_NAME_LIST)
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in USER_ARGUMENT_TO_PROPERTY_MAP:
          addFieldToCSVfile(field, USER_ARGUMENT_TO_PROPERTY_MAP, userFieldsList, userFieldsTitles, titles)
        else:
          putArgumentBack()
          invalidChoiceExit(USER_ARGUMENT_TO_PROPERTY_MAP)
    elif myarg == u'noduplicates':
      noduplicates = True
    elif myarg == u'recursive':
      recursive = True
    else:
      unknownArgumentExit()
  if entityList == None:
    printGettingAccountEntitiesInfo(EN_GROUP, qualifier=queryQualifier(groupQuery(domain, usemember)))
    page_message = getPageMessage(showTotal=False, showFirstLastItems=True)
    try:
      entityList = callGAPIpages(cd.groups(), u'list', u'groups',
                                 page_message=page_message, message_attribute=u'email',
                                 throw_reasons=[GAPI_INVALID_MEMBER, GAPI_DOMAIN_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                                 customer=customer, domain=domain, userKey=usemember,
                                 fields=u'nextPageToken,groups(email)')
    except GAPI_invalidMember:
      badRequestWarning(EN_GROUP, EN_MEMBER, usemember)
      entityList = []
    except GAPI_domainNotFound:
      badRequestWarning(EN_GROUP, EN_DOMAIN, domain)
      entityList = []
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      if domain:
        badRequestWarning(EN_GROUP, EN_DOMAIN, domain)
        entityList = []
      else:
        accessErrorExit(cd)
  if not fieldsList:
    for field in GROUPMEMBERS_DEFAULT_FIELDS:
      addFieldToCSVfile(field, {field: [field]}, fieldsList, fieldsTitles, titles)
  else:
    if u'name'in fieldsList:
      membernames = True
      fieldsList.remove(u'name')
  if u'group' in fieldsList:
    groupname = True
    fieldsList.remove(u'group')
  if userFieldsList:
    if not membernames and u'name.fullName' in userFieldsList:
      membernames = True
  if membernames:
    if u'name.fullName' not in userFieldsList:
      userFieldsList.append(u'name.fullName')
    addTitlesToCSVfile([u'name'], titles)
    removeTitlesFromCSVfile([u'name.fullName'], titles)
  if userFieldsList:
    userFieldsList = u','.join(set(userFieldsList)).replace(u'.', u'/')
  membersSet = set()
  level = 0
  i = 0
  count = len(entityList)
  for group in entityList:
    i += 1
    if isinstance(group, dict):
      groupEmail = group[u'email']
    else:
      groupEmail = convertGroupUIDtoEmailAddress(group)
    membersList = []
    getGroupMembers(cd, groupEmail, membersList, membersSet, i, count, noduplicates, recursive, level)
    for member in membersList:
      row = {}
      if groupname:
        row[u'group'] = groupEmail
      if recursive:
        row[u'level'] = member[u'level']
        row[u'subgroup'] = member[u'subgroup']
      for title in fieldsList:
        row[title] = member[title]
      if userFieldsList:
        if membernames:
          row[u'name'] = u'Unknown'
        memberType = member.get(u'type')
        if memberType == u'USER':
          try:
            mbinfo = callGAPI(cd.users(), u'get',
                              throw_reasons=GAPI_USER_GET_THROW_REASONS,
                              userKey=member[u'id'], fields=userFieldsList)
            if membernames:
              row[u'name'] = mbinfo[u'name'][u'fullName']
              del mbinfo[u'name'][u'fullName']
            addRowTitlesToCSVfile(flattenJSON(mbinfo, flattened=row), csvRows, titles)
          except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden, GAPI_badRequest, GAPI_backendError, GAPI_systemError):
            csvRows.append(row)
        else:
          if membernames and memberType == u'GROUP':
            try:
              mbinfo = callGAPI(cd.groups(), u'get',
                                throw_reasons=[GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
                                groupKey=member[u'id'], fields=u'name')
              row[u'name'] = mbinfo[u'name']
            except (GAPI_groupNotFound, GAPI_domainNotFound, GAPI_forbidden):
              pass
          csvRows.append(row)
      else:
        csvRows.append(row)
  sortCSVTitles(GROUPMEMBERS_DEFAULT_FIELDS, titles)
  if recursive:
    removeTitlesFromCSVfile([u'level', u'subgroup'], titles)
    addTitlesToCSVfile([u'level', u'subgroup'], titles)
  writeCSVfile(csvRows, titles, u'Group Members ({0})'.format(subTitle), todrive)

# gam print licenses [todrive] [(products|product <ProductIDList>)|(skus|sku <SKUIDList>)]
def doPrintLicenses(return_list=False, skus=None):
  lic = buildGAPIObject(GAPI_LICENSING_API)
  products = [GOOGLE_APPS_PRODUCT, GOOGLE_VAULT_PRODUCT]
  licenses = []
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'userId', u'productId', u'skuId'])
  if not return_list:
    while CL_argvI < CL_argvLen:
      myarg = getArgument()
      if myarg == u'todrive':
        todrive = True
      elif myarg in [u'products', u'product']:
        products = getGoogleProductListMap()
        skus = []
      elif myarg in [u'sku', u'skus']:
        skus = getGoogleSKUListMap()
        products = []
      else:
        unknownArgumentExit()
  if skus:
    for skuId in skus:
      setGettingEntityItem(EN_LICENSE)
      page_message = getPageMessageForWhom(forWhom=skuId)
      try:
        licenses += callGAPIpages(lic.licenseAssignments(), u'listForProductAndSku', u'items',
                                  page_message=page_message,
                                  throw_reasons=[GAPI_INVALID, GAPI_FORBIDDEN],
                                  customerId=GC_Values[GC_DOMAIN], productId=GOOGLE_SKUS[skuId], skuId=skuId, fields=u'nextPageToken,items(productId,skuId,userId)')
      except (GAPI_invalid, GAPI_forbidden):
        pass
  else:
    for productId in products:
      setGettingEntityItem(EN_LICENSE)
      page_message = getPageMessageForWhom(forWhom=productId)
      try:
        licenses += callGAPIpages(lic.licenseAssignments(), u'listForProduct', u'items',
                                  page_message=page_message,
                                  throw_reasons=[GAPI_INVALID, GAPI_FORBIDDEN],
                                  customerId=GC_Values[GC_DOMAIN], productId=productId, fields=u'nextPageToken,items(productId,skuId,userId)')
      except (GAPI_invalid, GAPI_forbidden):
        pass
  for u_license in licenses:
    a_license = {}
    for title in u_license:
      if title in [u'kind', u'etags', u'selfLink']:
        continue
      a_license[title] = u_license[title]
      if title not in titles[u'set']:
        addTitleToCSVfile(title, titles)
    csvRows.append(a_license)
  if return_list:
    return csvRows
  writeCSVfile(csvRows, titles, u'Licenses', todrive)

# Utilities for notification commands
READ_UNREAD_CHOICES = [u'read', u'unread',]

def getNotificationParameters(function):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  selected = False
  isUnread = None
  ids = []
  get_all = True
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg in [u'unreadonly', u'unread']:
      isUnread = True
      selected = True
    elif myarg == u'read':
      isUnread = False
      selected = True
    elif myarg == u'id':
      notificationId = getString(OB_NOTIFICATION_ID)
      if notificationId.lower() == u'all':
        get_all = True
        isUnread = None
        selected = False
        ids = []
      else:
        get_all = False
        ids.append(notificationId)
    else:
      unknownArgumentExit()
  if not selected:
    if function == u'update':
      missingChoiceExit(READ_UNREAD_CHOICES)
  if get_all:
    if function != u'info':
      fields = u'nextPageToken,items(notificationId,isUnread)'
    else:
      fields = None
    try:
      notifications = callGAPIpages(cd.notifications(), u'list', u'items',
                                    throw_reasons=[GAPI_DOMAIN_NOT_FOUND, GAPI_BAD_REQUEST, GAPI_FORBIDDEN],
                                    customer=GC_Values[GC_CUSTOMER_ID], fields=fields)
      for notification in notifications:
        if function == u'update':
          if notification[u'isUnread'] != isUnread:
            ids.append(notification[u'notificationId'])
        elif (not selected) or (notification[u'isUnread'] == isUnread):
          ids.append(notification[u'notificationId'])
    except (GAPI_domainNotFound, GAPI_badRequest, GAPI_forbidden):
      accessErrorExit(cd)
  else:
    notifications = None
  return (cd, isUnread, ids, notifications)

# gam update notification|notifications (id all)|(id <NotificationID>)* unreadonly|unread|read
def doUpdateNotification():
  cd, isUnread, notificationIds, _ = getNotificationParameters(u'update')
  printKeyValueList([u'Marking', len(notificationIds), u'Notification(s) as', u'UNREAD' if isUnread else u'READ'])
  body = {u'isUnread': isUnread}
  i = 0
  count = len(notificationIds)
  for notificationId in notificationIds:
    i += 1
    try:
      result = callGAPI(cd.notifications(), u'patch',
                        throw_reasons=[GAPI_DOMAIN_NOT_FOUND, GAPI_INTERNAL_ERROR, GAPI_BAD_REQUEST, GAPI_FORBIDDEN],
                        customer=GC_Values[GC_CUSTOMER_ID], notificationId=notificationId,
                        body=body, fields=u'notificationId,isUnread')
      printEntityKVList(EN_NOTIFICATION, result[u'notificationId'],
                        [PHRASE_MARKED_AS, [u'read', u'unread'][result[u'isUnread']]],
                        i, count)
    except (GAPI_domainNotFound, GAPI_internalError, GAPI_badRequest, GAPI_forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, EN_NOTIFICATION, notificationId, i, count)

# gam delete notification|notifications (id all)|(id <NotificationID>)* [unreadonly|unread|read]
def doDeleteNotification():
  cd, _, notificationIds, _ = getNotificationParameters(u'delete')
  printKeyValueList([u'Deleting', len(notificationIds), u'Notification(s)'])
  i = 0
  count = len(notificationIds)
  for notificationId in notificationIds:
    i += 1
    try:
      callGAPI(cd.notifications(), u'delete',
               throw_reasons=[GAPI_DOMAIN_NOT_FOUND, GAPI_INTERNAL_ERROR, GAPI_BAD_REQUEST, GAPI_FORBIDDEN],
               customer=GC_Values[GC_CUSTOMER_ID], notificationId=notificationId)
      entityActionPerformed(EN_NOTIFICATION, notificationId, i, count)
    except (GAPI_domainNotFound, GAPI_internalError, GAPI_badRequest, GAPI_forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, EN_NOTIFICATION, notificationId, i, count)

# gam info notification|notifications (id all)|(id <NotificationID>)* [unreadonly|unread|read]
def doInfoNotifications():
  cd, _, notificationIds, notifications = getNotificationParameters(u'info')
  i = 0
  count = len(notificationIds)
  for notificationId in notificationIds:
    i += 1
    if not notifications:
      try:
        notification = callGAPI(cd.notifications(), u'get',
                                throw_reasons=[GAPI_DOMAIN_NOT_FOUND, GAPI_INTERNAL_ERROR, GAPI_BAD_REQUEST, GAPI_FORBIDDEN],
                                customer=GC_Values[GC_CUSTOMER_ID], notificationId=notificationId)
      except (GAPI_domainNotFound, GAPI_internalError, GAPI_badRequest, GAPI_forbidden):
        checkEntityAFDNEorAccessErrorExit(cd, EN_NOTIFICATION, notificationId, i, count)
        continue
    else:
      for notification in notifications:
        if notification[u'notificationId'] == notificationId:
          break
    printEntityName(EN_NOTIFICATION, notification[u'notificationId'], i, count)
    incrementIndentLevel()
    printKeyValueList([u'From', notification[u'fromAddress']])
    printKeyValueList([u'Subject', notification[u'subject']])
    printKeyValueList([u'Date', [NEVER, notification[u'sendTime']][notification[u'sendTime'] != NEVER_TIME]])
    printKeyValueList([u'Read Status', [u'READ', u'UNREAD'][notification[u'isUnread']]])
    decrementIndentLevel()
    printBlankLine()
    printKeyValueList([dehtml(notification[u'body'])])
    printBlankLine()
    printKeyValueList([u'--------------'])
    printBlankLine()

# gam create resource <ResourceID> <Name> [description <String>] [type <String>]
def doCreateResourceCalendar():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  body = {u'resourceId': getString(OB_RESOURCE_ID),
          u'resourceName': getString(OB_NAME)}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'description':
      body[u'resourceDescription'] = getString(OB_STRING)
    elif myarg == u'type':
      body[u'resourceType'] = getString(OB_STRING)
    else:
      unknownArgumentExit()
  try:
    callGAPI(cd.resources().calendars(), u'insert',
             throw_reasons=[GAPI_INVALID, GAPI_DUPLICATE, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
             customer=GC_Values[GC_CUSTOMER_ID],
             body=body)
    entityActionPerformed(EN_RESOURCE_CALENDAR, body[u'resourceId'])
  except GAPI_invalid as e:
    entityActionFailedWarning(EN_RESOURCE_CALENDAR, body[u'resourceId'], e.message)
  except GAPI_duplicate:
    entityDuplicateWarning(EN_RESOURCE_CALENDAR, body[u'resourceId'])
  except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
    accessErrorExit(cd)

# gam update resources <ResourceEntity> [name <Name>] [description <String>] [type <String>]
def doUpdateResourceCalendars():
  updateResourceCalendars(getEntityList(OB_RESOURCE_ENTITY))

# gam update resource <ResourceID> [name <Name>] [description <String>] [type <String>]
def doUpdateResourceCalendar():
  updateResourceCalendars(getStringReturnInList(OB_RESOURCE_ID))

def updateResourceCalendars(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  body = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'name':
      body[u'resourceName'] = getString(OB_STRING)
    elif myarg == u'description':
      body[u'resourceDescription'] = getString(OB_STRING)
    elif myarg == u'type':
      body[u'resourceType'] = getString(OB_STRING)
    else:
      unknownArgumentExit()
  i = 0
  count = len(entityList)
  for resourceId in entityList:
    i += 1
    try:
      callGAPI(cd.resources().calendars(), u'patch',
               throw_reasons=[GAPI_INVALID, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
               customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resourceId,
               body=body)
      entityActionPerformed(EN_RESOURCE_CALENDAR, resourceId, i, count)
    except GAPI_invalid as e:
      entityActionFailedWarning(EN_RESOURCE_CALENDAR, resourceId, e.message, i, count)
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, EN_RESOURCE_CALENDAR, resourceId, i, count)

# gam delete resources <ResourceEntity>
def doDeleteResourceCalendars():
  deleteResourceCalendars(getEntityList(OB_RESOURCE_ENTITY))

# gam delete resource <ResourceID>
def doDeleteResourceCalendar():
  deleteResourceCalendars(getStringReturnInList(OB_RESOURCE_ID))

def deleteResourceCalendars(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for resourceId in entityList:
    i += 1
    try:
      callGAPI(cd.resources().calendars(), u'delete',
               throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
               customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resourceId)
      entityActionPerformed(EN_RESOURCE_CALENDAR, resourceId, i, count)
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, EN_RESOURCE_CALENDAR, resourceId, i, count)

# gam info resources <ResourceEntity>
# gam info resource <ResourceID>
def doInfoResourceCalendars():
  infoResourceCalendars(getEntityList(OB_RESOURCE_ENTITY))

def doInfoResourceCalendar():
  infoResourceCalendars(getStringReturnInList(OB_RESOURCE_ID))

def infoResourceCalendars(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for resourceId in entityList:
    i += 1
    try:
      resource = callGAPI(cd.resources().calendars(), u'get',
                          throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                          customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resourceId)
      printEntityName(EN_RESOURCE_ID, resource[u'resourceId'], i, count)
      incrementIndentLevel()
      printKeyValueList([u'Name', resource[u'resourceName']])
      printKeyValueList([u'Email', resource[u'resourceEmail']])
      printKeyValueList([u'Type', resource.get(u'resourceType', u'')])
      printKeyValueList([u'Description', resource.get(u'resourceDescription', u'')])
      decrementIndentLevel()
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, EN_RESOURCE_CALENDAR, resourceId, i, count)

RESCAL_DFLTFIELDS = [u'id', u'name', u'email',]
RESCAL_ALLFIELDS = [u'id', u'name', u'email', u'description', u'type',]

RESCAL_ARGUMENT_TO_PROPERTY_MAP = {
  u'description': [u'resourceDescription'],
  u'email': [u'resourceEmail'],
  u'id': [u'resourceId'],
  u'name': [u'resourceName'],
  u'type': [u'resourceType'],
  }

# gam print resources [todrive] [allfields] [id] [name] [description] [email] [type]
def doPrintResourceCalendars():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  todrive = False
  fieldsList = []
  fieldsTitles = {}
  titles, csvRows = initializeTitlesCSVfile(None)
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'allfields':
      fieldsList = []
      fieldsTitles = {}
      titles, csvRows = initializeTitlesCSVfile(None)
      for field in RESCAL_ALLFIELDS:
        addFieldToCSVfile(field, RESCAL_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
    elif myarg in RESCAL_ARGUMENT_TO_PROPERTY_MAP:
      addFieldToCSVfile(myarg, RESCAL_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
    else:
      unknownArgumentExit()
  if not fieldsList:
    for field in RESCAL_DFLTFIELDS:
      addFieldToCSVfile(field, RESCAL_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
  printGettingAccountEntitiesInfo(EN_RESOURCE_CALENDAR)
  try:
    page_message = getPageMessage(showTotal=False, showFirstLastItems=True)
    resources = callGAPIpages(cd.resources().calendars(), u'list', u'items',
                              page_message=page_message, message_attribute=u'resourceName',
                              throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                              customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,items({0})'.format(u','.join(set(fieldsList))))
    for resource in resources:
      resUnit = {}
      for field in fieldsList:
        resUnit[fieldsTitles[field]] = resource.get(field, u'')
      csvRows.append(resUnit)
  except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
    accessErrorExit(cd)
  writeCSVfile(csvRows, titles, u'Resources', todrive)

def _showSchema(schema, i=0, count=0):
  printEntityName(EN_USER_SCHEMA, schema[u'schemaName'], i, count)
  incrementIndentLevel()
  for a_key in schema:
    if a_key not in [u'kind', u'etag', u'schemaName', u'fields']:
      printKeyValueList([a_key, schema[a_key]])
  for field in schema[u'fields']:
    printKeyValueList([u'Field', field[u'fieldName']])
    incrementIndentLevel()
    for a_key in field:
      if a_key not in [u'kind', u'etag', u'fieldName']:
        printKeyValueList([a_key, field[a_key]])
    decrementIndentLevel()
  decrementIndentLevel()

SCHEMA_FIELDTYPE_CHOICES_MAP = {
  u'bool': u'BOOL',
  u'date': u'DATE',
  u'double': u'DOUBLE',
  u'email': u'EMAIL',
  u'int64': u'INT64',
  u'phone': u'PHONE',
  u'string': u'STRING',
  }

# gam create schema|schemas <SchemaName> <SchemaFieldDefinition>+
def doCreateUserSchema():
  createUpdateUserSchemas(False, getStringReturnInList(OB_SCHEMA_NAME))

# gam update schemas <SchemaEntity> <SchemaFieldDefinition>+
def doUpdateUserSchemas():
  createUpdateUserSchemas(True, getEntityList(OB_SCHEMA_ENTITY))

# gam update schema <SchemaName> <SchemaFieldDefinition>+
def doUpdateUserSchema():
  createUpdateUserSchemas(True, getStringReturnInList(OB_SCHEMA_NAME))

def createUpdateUserSchemas(updateCmd, entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  addBody = {u'schemaName': u'', u'fields': []}
  deleteFields = []
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'field':
      a_field = {u'fieldName': getString(OB_FIELD_NAME), u'fieldType': u'STRING'}
      while CL_argvI < CL_argvLen:
        argument = getArgument()
        if argument == u'type':
          a_field[u'fieldType'] = getChoice(SCHEMA_FIELDTYPE_CHOICES_MAP, mapChoice=True)
        elif argument in [u'multivalued', u'multivalue']:
          a_field[u'multiValued'] = True
        elif argument == u'indexed':
          a_field[u'indexed'] = True
        elif argument == u'restricted':
          a_field[u'readAccessType'] = u'ADMINS_AND_SELF'
        elif argument == u'range':
          a_field[u'numericIndexingSpec'] = {u'minValue': getInteger(), u'maxValue': getInteger()}
        elif argument == u'endfield':
          break
        elif argument == u'field':
          putArgumentBack()
          break
        else:
          unknownArgumentExit()
      addBody[u'fields'].append(a_field)
    elif updateCmd and myarg == u'deletefield':
      deleteFields.append(getString(OB_FIELD_NAME))
    else:
      unknownArgumentExit()
  if not updateCmd and not addBody[u'fields']:
    missingArgumentExit(u'SchemaFieldDefinition')
  i = 0
  count = len(entityList)
  for schemaName in entityList:
    i += 1
    try:
      if updateCmd:
        oldBody = callGAPI(cd.schemas(), u'get',
                           throw_reasons=[GAPI_INVALID, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                           customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaName, fields=u'schemaName,fields')
        for field in oldBody[u'fields']:
          field.pop(u'etag', None)
          field.pop(u'kind', None)
          field.pop(u'fieldId', None)
        badDelete = False
        for delField in deleteFields:
          fieldNameLower = delField.lower()
          for n, field in enumerate(oldBody[u'fields']):
            if field[u'fieldName'].lower() == fieldNameLower:
              del oldBody[u'fields'][n]
              break
          else:
            entityItemValueActionNotPerformedWarning(EN_USER_SCHEMA, schemaName, EN_FIELD, delField, PHRASE_DOES_NOT_EXIST)
            badDelete = True
        if badDelete:
          continue
        for addField in addBody[u'fields']:
          fieldNameLower = addField[u'fieldName'].lower()
          for n, field in enumerate(oldBody[u'fields']):
            if field[u'fieldName'].lower() == fieldNameLower:
              del oldBody[u'fields'][n]
              break
        oldBody[u'fields'].extend(addBody[u'fields'])
        if not oldBody[u'fields']:
          entityActionNotPerformedWarning(EN_USER_SCHEMA, schemaName, PHRASE_SCHEMA_WOULD_HAVE_NO_FIELDS.format(singularEntityName(EN_USER_SCHEMA), pluralEntityName(EN_FIELD)))
          continue
        result = callGAPI(cd.schemas(), u'update',
                          throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                          customerId=GC_Values[GC_CUSTOMER_ID], body=oldBody, schemaKey=schemaName)
        entityActionPerformed(EN_USER_SCHEMA, result[u'schemaName'], i, count)
      else:
        addBody[u'schemaName'] = schemaName
        result = callGAPI(cd.schemas(), u'insert',
                          throw_reasons=[GAPI_DUPLICATE, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                          customerId=GC_Values[GC_CUSTOMER_ID], body=addBody)
        entityActionPerformed(EN_USER_SCHEMA, result[u'schemaName'], i, count)
    except GAPI_duplicate:
      entityDuplicateWarning(EN_USER_SCHEMA, schemaName, i, count)
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, EN_USER_SCHEMA, schemaName, i, count)

# gam delete schemas <SchemaEntity>
def doDeleteUserSchemas():
  deleteUserSchemas(getEntityList(OB_SCHEMA_ENTITY))

# gam delete schema <SchemaName>
def doDeleteUserSchema():
  deleteUserSchemas(getStringReturnInList(OB_SCHEMA_NAME))

def deleteUserSchemas(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for schemaKey in entityList:
    i += 1
    try:
      callGAPI(cd.schemas(), u'delete',
               throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
               customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
      entityActionPerformed(EN_USER_SCHEMA, schemaKey, i, count)
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, EN_USER_SCHEMA, schemaKey, i, count)

# gam info schemas <SchemaEntity>
def doInfoUserSchemas():
  infoUserSchemas(getEntityList(OB_SCHEMA_ENTITY))

# gam info schema <SchemaName>
def doInfoUserSchema():
  infoUserSchemas(getStringReturnInList(OB_SCHEMA_NAME))

def infoUserSchemas(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for schemaKey in entityList:
    i += 1
    try:
      schema = callGAPI(cd.schemas(), u'get',
                        throw_reasons=[GAPI_INVALID, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                        customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
      _showSchema(schema, i, count)
    except (GAPI_invalid, GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, EN_USER_SCHEMA, schemaKey, i, count)

# gam print schema|schemas [todrive]
def doPrintUserSchemas():
  printShowUserSchemas(True)

# gam show schema|schemas
def doShowUserSchemas():
  printShowUserSchemas(False)

# gam print schema|schemas
def printShowUserSchemas(csvFormat):
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile(None)
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    else:
      unknownArgumentExit()
  try:
    result = callGAPI(cd.schemas(), u'list',
                      throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                      customerId=GC_Values[GC_CUSTOMER_ID])
    jcount = len(result.get(u'schemas', [])) if (result) else 0
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
    if not csvFormat:
      performActionNumItems(jcount, EN_USER_SCHEMA)
      if jcount > 0:
        incrementIndentLevel()
        j = 0
        for schema in result[u'schemas']:
          j += 1
          _showSchema(schema, j, jcount)
        decrementIndentLevel()
    else:
      if jcount > 0:
        for schema in result[u'schemas']:
          row = {u'fields.Count': len(schema[u'fields'])}
          addRowTitlesToCSVfile(flattenJSON(schema, flattened=row), csvRows, titles)
  except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
    accessErrorExit(cd)
  if csvFormat:
    sortCSVTitles([u'schemaId', u'schemaName', u'fields.Count'], titles)
    writeCSVfile(csvRows, titles, u'User Schemas', todrive)

def checkSiteExists(sitesObject, domain, site):
  try:
    callGData(sitesObject, u'GetSite',
              throw_errors=[GDATA_NOT_FOUND],
              retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
              domain=domain, site=site)
    return True
  except GData_notFound:
    return None

SITE_ACLS = 'ACLs'
SITE_CATEGORIES = u'Categories'
SITE_LINK = u'Link'
SITE_NAME = u'Name'
SITE_SITE = u'Site'
SITE_SOURCELINK = u'SourceLink'
SITE_SUMMARY = u'Summary'
SITE_THEME = u'Theme'
SITE_UPDATED = u'Updated'
SITE_WEB_ADDRESS_MAPPINGS = 'WebAddressMappings'

SITE_DATA_DOMAIN = u'domain'
SITE_DATA_SITE = u'site'
SITE_DATA_DOMAIN_SITE = u'domainSite'
SITE_DATA_FIELDS = u'fields'

class SitesManager(object):

  SITE_ARGUMENT_TO_PROPERTY_MAP = {
    u'categories': SITE_CATEGORIES,
    u'name': SITE_NAME,
    u'sourcelink': SITE_SOURCELINK,
    u'summary': SITE_SUMMARY,
    u'theme': SITE_THEME,
    }

  @staticmethod
  def AclEntryToFields(acl_entry):

    def GetAclAttr(attrlist):
      objAttr = acl_entry
      for attr in attrlist:
        objAttr = getattr(objAttr, attr)
        if not objAttr:
          return None
      return objAttr

    fields = {}
    fields[u'role'] = GetAclAttr([u'role', u'value'])
    if not fields[u'role']:
      fields[u'role'] = GetAclAttr([u'withKey', u'role', u'value']) + u' (with link)'
    fields[u'scope'] = {u'type': GetAclAttr([u'scope', u'type']),
                        u'value': GetAclAttr([u'scope', u'value'])}
    link = acl_entry.FindInviteLink()
    if link:
      fields[u'inviteLink'] = link
    return fields

  @staticmethod
  def FieldsToAclEntry(fields):
    import gdata.apps.sites

    acl_entry = gdata.apps.sites.AclEntry()
    acl_entry.role = gdata.apps.sites.AclRole(value=fields[u'role'])
    acl_entry.scope = gdata.apps.sites.AclScope(stype=fields[u'scope'][u'type'], value=fields[u'scope'].get(u'value'))
    return acl_entry

  @staticmethod
  def ActivityEntryToFields(activity_entry):
    fields = {}

    def GetActivityField(fieldName, attrlist):
      objAttr = activity_entry
      for attr in attrlist:
        objAttr = getattr(objAttr, attr)
        if not objAttr:
          return
      fields[fieldName] = objAttr

    def GetActivityFieldData(objAttr, attrlist, default):
      for attr in attrlist:
        objAttr = getattr(objAttr, attr)
        if not objAttr:
          return default
      return  objAttr

    def AppendItemToFieldsList(fieldName, fieldValue):
      fields.setdefault(fieldName, [])
      fields[fieldName].append(fieldValue)


    GetActivityField(u'Summary', [u'title', u'text'])
    GetActivityField(u'Updated', [u'updated', u'text'])
    for author in activity_entry.author:
      AppendItemToFieldsList('Authors', u'{0}/{1}'.format(GetActivityFieldData(author, [u'name', u'text'], u'Unknown Name'), GetActivityFieldData(author, [u'email', u'text'], u'Unknown Email')))
    fields[u'Operation'] = activity_entry.Kind()
    return fields

  @staticmethod
  def SiteToFields(site_entry):
    fields = {}

    def GetSiteField(fieldName, attrlist):
      objAttr = site_entry
      for attr in attrlist:
        objAttr = getattr(objAttr, attr)
        if not objAttr:
          return
      fields[fieldName] = objAttr

    def AppendItemToFieldsList(fieldName, fieldValue):
      fields.setdefault(fieldName, [])
      fields[fieldName].append(fieldValue)

    GetSiteField(SITE_SITE, [u'siteName', u'text'])
    GetSiteField(SITE_NAME, [u'title', u'text'])
    GetSiteField(SITE_SUMMARY, [u'summary', u'text'])
    GetSiteField(SITE_THEME, [u'theme', u'text'])
    GetSiteField(SITE_UPDATED, [u'updated', u'text'])
    if len(site_entry.category) > 0:
      for category in site_entry.category:
        AppendItemToFieldsList(SITE_CATEGORIES, category.term)
    link = site_entry.FindAlternateLink()
    if link:
      fields[SITE_LINK] = link
    link = site_entry.FindSourceLink()
    if link:
      fields[SITE_SOURCELINK] = link
    for link in site_entry.FindWebAddressMappings():
      AppendItemToFieldsList(SITE_WEB_ADDRESS_MAPPINGS, link)
    return fields

  @staticmethod
  def GetSiteFields():

    fields = {}
    while CL_argvI < CL_argvLen:
      myarg = getArgument()
      if myarg in SitesManager.SITE_ARGUMENT_TO_PROPERTY_MAP:
        fieldName = SitesManager.SITE_ARGUMENT_TO_PROPERTY_MAP[myarg]
        if fieldName == SITE_NAME:
          fields[fieldName] = getString(OB_STRING)
        elif fieldName == SITE_SOURCELINK:
          fields[fieldName] = getString(OB_URI)
        elif fieldName == SITE_SUMMARY:
          fields[fieldName] = getString(OB_STRING, emptyOK=True).replace(u'\\n', u'\n')
        elif fieldName == SITE_THEME:
          fields[fieldName] = getString(OB_STRING)
        elif fieldName == SITE_CATEGORIES:
          fields[fieldName] = getString(OB_STRING, emptyOK=True).split(u',')
      else:
        unknownArgumentExit()
    return fields

  @staticmethod
  def FieldsToSite(fields):
    import atom
    import gdata.apps.sites

    def GetField(fieldName):
      return fields.get(fieldName)

    def GetSiteField(fieldName, fieldClass):
      value = fields.get(fieldName)
      if value:
        return fieldClass(text=value)
      return None

    site_entry = gdata.apps.sites.SiteEntry(sourceSite=GetField(SITE_SOURCELINK))
    site_entry.siteName = GetSiteField(SITE_SITE, gdata.apps.sites.SiteName)
    site_entry.title = GetSiteField(SITE_NAME, atom.Title)
    site_entry.summary = GetSiteField(SITE_SUMMARY, atom.Summary)
    site_entry.theme = GetSiteField(SITE_THEME, gdata.apps.sites.Theme)
    value = GetField(SITE_CATEGORIES)
    if value:
      for category in value:
        site_entry.category.append(atom.Category(term=category, scheme=gdata.apps.sites.TAG_KIND_TERM))
    return site_entry

def validateSite(fullSite, i, count):
  domain, site, domainSite = validateSplitSiteName(fullSite)
  if domainSite:
    return (domain, site, domainSite)
  entityActionNotPerformedWarning(EN_SITE, site, PHRASE_INVALID_SITE.format(site, SITENAME_FORMAT_REQUIRED), i=i, count=count)
  return (domain, site, None)

# gam [<UserTypeEntity>] create site <SiteName> [name <String>] [summary <String>] [theme <String>] [categories <String>] [sourcelink <URI>]
def createUserSite(users):
  doCreateSite(users, EN_USER)

def doCreateDomainSite():
  doCreateSite([GC_Values[GC_DOMAIN],], EN_DOMAIN)

def doCreateSite(users, entityType):
  sitesManager = SitesManager()
  domain, site, domainSite = getSiteName()
  fields = sitesManager.GetSiteFields()
  if not fields.get(SITE_NAME):
    fields[SITE_NAME] = site
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, sitesObject = getSitesObject(entityType, user, i, count)
    if not sitesObject:
      continue
    try:
      siteEntry = sitesManager.FieldsToSite(fields)
      callGData(sitesObject, u'CreateSite',
                throw_errors=[GDATA_NOT_FOUND, GDATA_ENTITY_EXISTS, GDATA_BAD_REQUEST, GDATA_FORBIDDEN],
                retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                siteentry=siteEntry, domain=domain, site=None)
      entityActionPerformed(EN_SITE, domainSite)
    except GData_notFound:
      entityActionFailedWarning(EN_DOMAIN, domain, PHRASE_DOES_NOT_EXIST)
    except GData_entityExists:
      entityActionFailedWarning(EN_SITE, domainSite, PHRASE_DUPLICATE)
    except (GData_badRequest, GData_forbidden) as e:
      entityActionFailedWarning(EN_SITE, domainSite, e.message)

# gam [<UserTypeEntity>] update site <SiteEntity> [name <String>] [summary <String>] [theme <String>] [categories <String>]
def updateUserSites(users):
  doUpdateSites(users, EN_USER)

def doUpdateDomainSites():
  doUpdateSites([GC_Values[GC_DOMAIN],], EN_DOMAIN)

def doUpdateSites(users, entityType):
  sitesManager = SitesManager()
  sites = getEntityList(OB_SITE_ENTITY)
  siteLists = sites if isinstance(sites, dict) else None
  updateFields = sitesManager.GetSiteFields()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if siteLists:
      sites = siteLists[user]
    user, sitesObject = getSitesObject(entityType, user, i, count)
    if not sitesObject:
      continue
    jcount = len(sites)
    entityPerformActionNumItems(EN_USER, user, jcount, EN_SITE, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for site in sites:
      j += 1
      domain, site, domainSite = validateSite(site, j, jcount)
      if not domainSite:
        continue
      try:
        siteEntry = callGData(sitesObject, u'GetSite',
                              throw_errors=[GDATA_NOT_FOUND, GDATA_FORBIDDEN],
                              retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                              domain=domain, site=site)
        fields = sitesManager.SiteToFields(siteEntry)
        for field in updateFields:
          if field != SITE_SOURCELINK:
            fields[field] = updateFields[field]
        newSiteEntry = sitesManager.FieldsToSite(fields)
        callGData(sitesObject, u'UpdateSite',
                  throw_errors=[GDATA_NOT_FOUND, GDATA_BAD_REQUEST, GDATA_FORBIDDEN],
                  retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                  siteentry=newSiteEntry, domain=domain, site=site, extra_headers={u'If-Match': siteEntry.etag})
        entityActionPerformed(EN_SITE, domainSite)
      except GData_notFound:
        entityActionFailedWarning(EN_SITE, domainSite, PHRASE_DOES_NOT_EXIST)
      except (GData_badRequest, GData_forbidden) as e:
        entityActionFailedWarning(EN_SITE, domainSite, e.message)

SITE_FIELD_PRINT_ORDER = [
  SITE_UPDATED,
  SITE_NAME,
  SITE_SUMMARY,
  SITE_THEME,
  SITE_SOURCELINK,
  SITE_CATEGORIES,
  SITE_LINK,
  ]

def _showSite(sitesManager, sitesObject, domain, site, roles, j, jcount):
  fields = sitesManager.SiteToFields(site)
  domainSite = u'{0}/{1}'.format(domain, fields[SITE_SITE])
  printKeyValueListWithCount([SITE_SITE, domainSite], j, jcount)
  incrementIndentLevel()
  for field in SITE_FIELD_PRINT_ORDER:
    if field in fields:
      if not isinstance(fields[field], list):
        if field != SITE_SUMMARY:
          printKeyValueList([field, fields[field]])
        else:
          printKeyValueList([field, None])
          incrementIndentLevel()
          printKeyValueList([indentMultiLineText(fields[field])])
          decrementIndentLevel()
      else:
        printKeyValueList([field, u','.join(fields[field])])
  if fields.get(SITE_WEB_ADDRESS_MAPPINGS):
    printKeyValueList([SITE_WEB_ADDRESS_MAPPINGS, None])
    incrementIndentLevel()
    for link in fields[SITE_WEB_ADDRESS_MAPPINGS]:
      printKeyValueList([link, None])
    decrementIndentLevel()
  if roles:
    try:
      acls = callGDataPages(sitesObject, u'GetAclFeed',
                            throw_errors=[GDATA_NOT_FOUND, GDATA_FORBIDDEN],
                            retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                            domain=domain, site=fields[SITE_SITE])
      printKeyValueList([SITE_ACLS, None])
      incrementIndentLevel()
      for acl in acls:
        fields = sitesManager.AclEntryToFields(acl)
        if fields[u'role'] in roles:
          printKeyValueList([formatACLRule(fields)])
      decrementIndentLevel()
    except GData_notFound:
      entityActionFailedWarning(EN_SITE, domainSite, PHRASE_DOES_NOT_EXIST)
    except GData_forbidden as e:
      entityActionFailedWarning(EN_SITE, domainSite, e.message)
  decrementIndentLevel()

SITE_ACL_ROLES_MAP = {
  u'editor': u'writer',
  u'invite': u'invite',
  u'owner': u'owner',
  u'reader': u'reader',
  u'writer': u'writer',
  }

def getACLRoles(aclRolesMap):
  roles = []
  for role in getString(OB_ROLE_LIST, emptyOK=True).strip().lower().replace(u',', u' ').split():
    if role == u'all':
      for role in aclRolesMap:
        roles.append(aclRolesMap[role])
    elif role in aclRolesMap:
      roles.append(aclRolesMap[role])
    else:
      putArgumentBack()
      invalidChoiceExit(aclRolesMap)
  return list(set(roles))

# gam [<UserTypeEntity>] info site <SiteEntity> [withmappings] [role|roles all|<SiteACLRoleList>]
def infoUserSites(users):
  doInfoSites(users, EN_USER)

def doInfoDomainSites():
  doInfoSites([GC_Values[GC_DOMAIN],], EN_DOMAIN)

def doInfoSites(users, entityType):
  sites = getEntityList(OB_SITE_ENTITY)
  siteLists = sites if isinstance(sites, dict) else None
  url_params = {}
  roles = None
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'withmappings':
      url_params[u'with-mappings'] = u'true'
    elif myarg in [u'role', u'roles']:
      roles = getACLRoles(SITE_ACL_ROLES_MAP)
    else:
      unknownArgumentExit()
  sitesManager = SitesManager()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if siteLists:
      sites = siteLists[user]
    user, sitesObject = getSitesObject(entityType, user, i, count)
    if not sitesObject:
      continue
    jcount = len(sites)
    entityPerformActionNumItems(EN_USER, user, jcount, EN_SITE, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for site in sites:
      j += 1
      domain, site, domainSite = validateSite(site, j, jcount)
      if not domainSite:
        continue
      try:
        result = callGData(sitesObject, u'GetSite',
                           throw_errors=[GDATA_NOT_FOUND, GDATA_FORBIDDEN],
                           retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                           domain=domain, site=site, url_params=url_params)
        if result:
          _showSite(sitesManager, sitesObject, domain, result, roles, j, jcount)
      except GData_notFound:
        entityActionFailedWarning(EN_SITE, domainSite, PHRASE_DOES_NOT_EXIST)
      except GData_forbidden as e:
        entityActionFailedWarning(EN_SITE, domainSite, e.message)
    decrementIndentLevel()

# gam [<UserTypeEntity>] print sites [todrive] [domain|domains <DomainNameEntity>] [includeallsites] [withmappings] [role|roles all|<SiteACLRoleList>] [maxresults <Number>] [convertsummarynl]
def printUserSites(users):
  printShowSites(users, EN_USER, True)

# gam [<UserTypeEntity>] show sites [domain|domains <DomainNameEntity>] [includeallsites] [withmappings] [role|roles all|<SiteACLRoleList>] [maxresults <Number>] [convertsummarynl]
def showUserSites(users):
  printShowSites(users, EN_USER, False)

# gam print sites [todrive] [domain|domains <DomainNameEntity>] [includeallsites] [withmappings] [role|roles all|<SiteACLRoleList>] [maxresults <Number>] [convertsummarynl]
def doPrintDomainSites():
  printShowSites([GC_Values[GC_DOMAIN],], EN_DOMAIN, True)

# gam show sites [domain|domains <DomainNameEntity>] [includeallsites] [withmappings] [role|roles all|<SiteACLRoleList>] [maxresults <Number>] [convertsummarynl]
def doShowDomainSites():
  printShowSites([GC_Values[GC_DOMAIN],], EN_DOMAIN, False)

def printShowSites(entityList, entityType, csvFormat):
  def _getSites(domain, i, count):
    try:
      page_message = getPageMessage()
      return callGDataPages(sitesObject, u'GetSiteFeed',
                            page_message=page_message,
                            throw_errors=[GDATA_NOT_FOUND, GDATA_FORBIDDEN],
                            retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                            domain=domain, url_params=url_params)
    except GData_notFound:
      entityActionFailedWarning(EN_DOMAIN, domain, PHRASE_DOES_NOT_EXIST, i, count)
    except GData_forbidden as e:
      entityActionFailedWarning(EN_DOMAIN, domain, e.message, i, count)
    return []

  def _printSites(entity, i, count, domain, sites):
    for site in sites:
      fields = sitesManager.SiteToFields(site)
      if fields[SITE_SITE] in sitesSet:
        continue
      sitesSet.add(fields[SITE_SITE])
      domainSite = u'{0}/{1}'.format(domain, fields[SITE_SITE])
      siteRow = {singularEntityName(entityType): entity, SITE_SITE: domainSite}
      for field in fields:
        if field != SITE_SITE:
          if not isinstance(fields[field], list):
            if field != SITE_SUMMARY or not convertSummaryNL:
              siteRow[field] = fields[field]
            else:
              siteRow[field] = fields[field].replace(u'\n', u'\\n')
          else:
            siteRow[field] = u','.join(fields[field])
      rowShown = False
      if roles:
        try:
          acls = callGDataPages(sitesObject, u'GetAclFeed',
                                throw_errors=[GDATA_NOT_FOUND, GDATA_FORBIDDEN],
                                retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                                domain=domain, site=fields[SITE_SITE])
          for acl in acls:
            fields = sitesManager.AclEntryToFields(acl)
            if fields[u'role'] in roles:
              siteACLRow = siteRow.copy()
              siteACLRow[u'Role'] = fields[u'role']
              if fields[u'scope'][u'type'] != u'default':
                siteACLRow[u'Scope'] = u'{0}:{1}'.format(fields[u'scope'][u'type'], fields[u'scope'][u'value'])
              else:
                siteACLRow[u'Scope'] = fields[u'scope'][u'type']
              rowShown = True
              addRowTitlesToCSVfile(siteACLRow, csvRows, titles)
        except GData_notFound:
          entityActionFailedWarning(EN_SITE, domainSite, PHRASE_DOES_NOT_EXIST, i, count)
        except GData_forbidden as e:
          entityActionFailedWarning(EN_SITE, domainSite, e.message, i, count)
      if not rowShown:
        addRowTitlesToCSVfile(siteRow, csvRows, titles)

  def _showSites(entity, i, count, domain, sites):
    jcount = len(sites)
    if entityType == EN_USER:
      entityPerformActionItemValueNumItems(entityType, entity, EN_DOMAIN, domain, jcount, EN_SITE, i, count)
    else:
      entityPerformActionNumItems(entityType, entity, jcount, EN_SITE, i, count)
    incrementIndentLevel()
    j = 0
    for site in sites:
      j += 1
      _showSite(sitesManager, sitesObject, domain, site, roles, j, jcount)
    decrementIndentLevel()

  domains = []
  domainLists = []
  url_params = {}
  includeAllSites = [u'false', u'true'][entityType == EN_DOMAIN]
  roles = None
  if csvFormat:
    convertSummaryNL = todrive = False
    titles, csvRows = initializeTitlesCSVfile([singularEntityName(entityType), SITE_SITE, SITE_NAME])
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    elif myarg in [u'domain', u'domains']:
      if entityType == EN_DOMAIN:
        entityList = getEntityList(OB_DOMAIN_NAME_ENTITY)
      else:
        domains = getEntityList(OB_DOMAIN_NAME_ENTITY)
        domainLists = domains if isinstance(domains, dict) else None
    elif myarg == u'includeallsites':
      includeAllSites = u'true'
    elif myarg == u'maxresults':
      url_params[u'max-results'] = getInteger(minVal=1)
    elif myarg == u'withmappings':
      url_params[u'with-mappings'] = u'true'
    elif myarg in [u'role', u'roles']:
      roles = getACLRoles(SITE_ACL_ROLES_MAP)
    elif myarg == u'convertsummarynl':
      convertSummaryNL = True
    else:
      unknownArgumentExit()
  sitesManager = SitesManager()
  sitesSet = set()
  i = 0
  count = len(entityList)
  if entityType == EN_USER:
    for user in entityList:
      i += 1
      if domainLists:
        domainList = domainLists[user]
      elif domains:
        domainList = domains
      else:
        _, domain = splitEmailAddress(user)
        domainList = [domain]
      user, sitesObject = getSitesObject(entityType, user, i, count)
      if not sitesObject:
        continue
      jcount = len(domainList)
      j = 0
      for domain in domainList:
        j += 1
        if domain != u'site':
          url_params[u'include-all-sites'] = includeAllSites
        else:
          url_params.pop(u'include-all-sites', None)
        printGettingAllEntityItemsForWhom(EN_SITE, u'{0}: {1}, {2}: {3}'.format(singularEntityName(EN_USER), user, singularEntityName(EN_DOMAIN), domain))
        sites = _getSites(domain, i, count)
        if not csvFormat:
          _showSites(domain, j, jcount, domain, sites)
        else:
          _printSites(user, j, jcount, domain, sites)
  else:
    for domain in entityList:
      i += 1
      domain, sitesObject = getSitesObject(entityType, domain, i, count)
      if not sitesObject:
        continue
      if domain != u'site':
        url_params[u'include-all-sites'] = includeAllSites
      else:
        url_params.pop(u'include-all-sites', None)
      printGettingAllEntityItemsForWhom(EN_SITE, u'{0}: {1}'.format(singularEntityName(EN_DOMAIN), domain))
      sites = _getSites(domain, i, count)
      if not csvFormat:
        _showSites(domain, i, count, domain, sites)
      else:
        _printSites(domain, i, count, domain, sites)
  if csvFormat:
    if roles:
      removeTitlesFromCSVfile([u'Scope', u'Role'], titles)
      addTitlesToCSVfile([u'Scope', u'Role'], titles)
    writeCSVfile(csvRows, titles, u'Sites', todrive)

# gam [<UserTypeEntity>] add siteacls <SiteEntity> <SiteACLRole> <ACLEntity>
# gam [<UserTypeEntity>] update siteacls <SiteEntity> <SiteACLRole> <ACLEntity>
# gam [<UserTypeEntity>] delete siteacls <SiteEntity> <ACLEntity>
# gam [<UserTypeEntity>] info siteacls <SiteEntity> <ACLEntity>
# gam [<UserTypeEntity>] show siteacls <SiteEntity>
def processUserSiteACLs(users):
  doProcessSiteACLs(users, EN_USER)

def doProcessDomainSiteACLs():
  doProcessSiteACLs([GC_Values[GC_DOMAIN],], EN_DOMAIN)

def doProcessSiteACLs(users, entityType):
  action = GM_Globals[GM_ACTION_COMMAND]
  sites = getEntityList(OB_SITE_ENTITY)
  siteLists = sites if isinstance(sites, dict) else None
  if action in [AC_ADD, AC_UPDATE]:
    role = getChoice(SITE_ACL_ROLES_MAP, mapChoice=True)
  else:
    role = None
  if action != AC_SHOW:
    ruleIds = getEntityList(OB_ACL_ENTITY)
    ruleIdLists = ruleIds if isinstance(ruleIds, dict) else None
  checkForExtraneousArguments()
  sitesManager = SitesManager()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if siteLists:
      sites = siteLists[user]
    user, sitesObject = getSitesObject(entityType, user, i, count)
    if not sitesObject:
      continue
    jcount = len(sites)
    entityPerformActionModifierNumItems(entityType, user, u'{0} {1}'.format(pluralEntityName(EN_ACL), PHRASE_FOR), jcount, EN_SITE, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for site in sites:
      j += 1
      domain, site, domainSite = validateSite(site, j, jcount)
      if not domainSite:
        continue
      if action != AC_SHOW:
        if ruleIdLists:
          ruleIds = ruleIdLists[site]
        kcount = len(ruleIds)
        entityPerformActionNumItems(EN_SITE, domainSite, kcount, EN_ACL, j, jcount)
        if kcount == 0:
          continue
        incrementIndentLevel()
        k = 0
        for ruleId in ruleIds:
          k += 1
          ruleId = normalizeRuleId(ruleId)
          try:
            if action == AC_ADD:
              fields = convertRuleId(role, ruleId)
              acl = sitesManager.FieldsToAclEntry(fields)
              acl = callGData(sitesObject, u'CreateAclEntry',
                              throw_errors=[GDATA_NOT_FOUND, GDATA_ENTITY_EXISTS, GDATA_BAD_REQUEST, GDATA_FORBIDDEN],
                              retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                              aclentry=acl, domain=domain, site=site)
              fields = sitesManager.AclEntryToFields(acl)
              if not fields.get(u'inviteLink'):
                entityItemValueActionPerformed(EN_SITE, domainSite, EN_ACL, formatACLRule(fields), k, kcount)
              else:
                entityItemValueActionPerformed(EN_SITE, domainSite, EN_ACL, u'{0} (Link: {1})'.format(formatACLRule(fields), fields[u'inviteLink']), k, kcount)
            elif action == AC_UPDATE:
              acl = callGData(sitesObject, u'GetAclEntry',
                              throw_errors=[GDATA_NOT_FOUND, GDATA_FORBIDDEN],
                              retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                              domain=domain, site=site, ruleId=ruleId)
              acl.role.value = role
              acl = callGData(sitesObject, u'UpdateAclEntry',
                              throw_errors=[GDATA_NOT_FOUND, GDATA_FORBIDDEN],
                              retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                              aclentry=acl, domain=domain, site=site, ruleId=ruleId, extra_headers={u'If-Match': acl.etag})
              fields = sitesManager.AclEntryToFields(acl)
              entityItemValueActionPerformed(EN_SITE, domainSite, EN_ACL, formatACLRule(fields), k, kcount)
            elif action == AC_DELETE:
              acl = callGData(sitesObject, u'GetAclEntry',
                              throw_errors=[GDATA_NOT_FOUND, GDATA_FORBIDDEN],
                              retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                              domain=domain, site=site, ruleId=ruleId)
              callGData(sitesObject, u'DeleteAclEntry',
                        throw_errors=[GDATA_NOT_FOUND, GDATA_FORBIDDEN],
                        retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                        domain=domain, site=site, ruleId=ruleId, extra_headers={u'If-Match': acl.etag})
              entityItemValueActionPerformed(EN_SITE, domainSite, EN_ACL, formatACLScopeRole(ruleId, None), k, kcount)
            elif action == AC_INFO:
              acl = callGData(sitesObject, u'GetAclEntry',
                              throw_errors=[GDATA_NOT_FOUND, GDATA_FORBIDDEN],
                              retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                              domain=domain, site=site, ruleId=ruleId)
              fields = sitesManager.AclEntryToFields(acl)
              printEntityItemValue(EN_SITE, domainSite, EN_ACL, formatACLRule(fields), k, kcount)
          except GData_notFound:
            if not checkSiteExists(sitesObject, domain, site):
              entityUnknownWarning(EN_SITE, domainSite, j, jcount)
              break
            entityItemValueActionFailedWarning(EN_SITE, domainSite, EN_ACL, formatACLScopeRole(ruleId, role), PHRASE_DOES_NOT_EXIST, k, kcount)
          except GData_entityExists:
            entityItemValueActionFailedWarning(EN_SITE, domainSite, EN_ACL, formatACLScopeRole(ruleId, role), PHRASE_DUPLICATE, k, kcount)
          except (GData_badRequest, GData_forbidden) as e:
            entityItemValueActionFailedWarning(EN_SITE, domainSite, EN_ACL, formatACLScopeRole(ruleId, role), e.message, k, kcount)
        decrementIndentLevel()
      else:
        try:
          acls = callGDataPages(sitesObject, u'GetAclFeed',
                                throw_errors=[GDATA_NOT_FOUND, GDATA_FORBIDDEN],
                                retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                                domain=domain, site=site)
          kcount = len(acls)
          entityPerformActionNumItems(EN_SITE, domainSite, kcount, EN_ACL, j, jcount)
          if kcount == 0:
            continue
          incrementIndentLevel()
          k = 0
          for acl in acls:
            k += 1
            fields = sitesManager.AclEntryToFields(acl)
            printEntityItemValue(EN_SITE, domainSite, EN_ACL, formatACLRule(fields), k, kcount)
          decrementIndentLevel()
        except GData_notFound:
          entityUnknownWarning(EN_SITE, domainSite, j, jcount)
        except GData_forbidden as e:
          entityActionFailedWarning(EN_SITE, domainSite, e.message, j, jcount)
    decrementIndentLevel()

# gam [<UserTypeEntity>] print siteactivity <SiteEntity> [todrive] [maxresults <Number>] [updated_min yyyy-mm-dd] [updated_max yyyy-mm-dd]
def printUserSiteActivity(users):
  doPrintSiteActivity(users, EN_USER)

def doPrintDomainSiteActivity():
  doPrintSiteActivity([GC_Values[GC_DOMAIN],], EN_DOMAIN)

def doPrintSiteActivity(users, entityType):
  sitesManager = SitesManager()
  todrive = False
  url_params = {}
  titles, csvRows = initializeTitlesCSVfile([SITE_SITE])
  sites = getEntityList(OB_SITE_ENTITY)
  siteLists = sites if isinstance(sites, dict) else None
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'maxresults':
      url_params[u'max-results'] = getInteger(minVal=1)
    elif myarg == u'updatedmin':
      url_params[u'updated-min'] = getYYYYMMDD()
    elif myarg == u'updatedmax':
      url_params[u'updated-max'] = getYYYYMMDD()
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if siteLists:
      sites = siteLists[user]
    user, sitesObject = getSitesObject(entityType, user, i, count)
    if not sitesObject:
      continue
    jcount = len(sites)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for site in sites:
      j += 1
      domain, site, domainSite = validateSite(site, j, jcount)
      if not domainSite:
        continue
      printGettingAllEntityItemsForWhom(EN_ACTIVITY, domainSite)
      try:
        page_message = getPageMessage()
        activities = callGDataPages(sitesObject, u'GetActivityFeed',
                                    page_message=page_message,
                                    throw_errors=[GDATA_NOT_FOUND, GDATA_FORBIDDEN],
                                    retry_errors=[GDATA_INTERNAL_SERVER_ERROR],
                                    domain=domain, site=site, url_params=url_params)
        for activity in activities:
          fields = sitesManager.ActivityEntryToFields(activity)
          activityRow = {SITE_SITE: domainSite}
          for key in fields:
            if not isinstance(fields[key], list):
              activityRow[key] = fields[key]
            else:
              activityRow[key] = u','.join(fields[key])
          addRowTitlesToCSVfile(activityRow, csvRows, titles)
      except GData_notFound:
        entityUnknownWarning(EN_SITE, domainSite, j, jcount)
      except GData_forbidden as e:
        entityActionFailedWarning(EN_SITE, domainSite, e.message, j, jcount)
  writeCSVfile(csvRows, titles, u'Site Activities', todrive)

# Utilities for user commands
#
UPDATE_USER_ARGUMENT_TO_PROPERTY_MAP = {
  u'address': u'addresses',
  u'addresses': u'addresses',
  u'agreed2terms': u'agreedToTerms',
  u'agreedtoterms': u'agreedToTerms',
  u'changepassword': u'changePasswordAtNextLogin',
  u'changepasswordatnextlogin': u'changePasswordAtNextLogin',
  u'crypt': u'hashFunction',
  u'customerid': u'customerId',
  u'email': u'primaryEmail',
  u'emails': u'emails',
  u'externalid': u'externalIds',
  u'externalids': u'externalIds',
  u'familyname': u'familyName',
  u'firstname': u'givenName',
  u'gal': u'includeInGlobalAddressList',
  u'givenname': u'givenName',
  u'im': u'ims',
  u'ims': u'ims',
  u'includeinglobaladdresslist': u'includeInGlobalAddressList',
  u'ipwhitelisted': u'ipWhitelisted',
  u'lastname': u'familyName',
  u'md5': u'hashFunction',
  u'note': u'notes',
  u'notes': u'notes',
  u'org': u'orgUnitPath',
  u'organization': u'organizations',
  u'organizations': u'organizations',
  u'orgunitpath': u'orgUnitPath',
  u'otheremail': u'emails',
  u'otheremails': u'emails',
  u'ou': u'orgUnitPath',
  u'password': u'password',
  u'phone': u'phones',
  u'phones': u'phones',
  u'primaryemail': u'primaryEmail',
  u'relation': u'relations',
  u'relations': u'relations',
  u'sha': u'hashFunction',
  u'sha-1': u'hashFunction',
  u'sha1': u'hashFunction',
  u'suspended': u'suspended',
  u'username': u'primaryEmail',
  u'website': u'websites',
  u'websites': u'websites',
  }

HASH_FUNCTION_MAP = {
  u'sha': u'SHA-1',
  u'sha1': u'SHA-1',
  u'sha-1': u'SHA-1',
  u'md5': u'MD5',
  u'crypt': u'crypt',
  }

ADDRESS_ARGUMENT_TO_FIELD_MAP = {
  u'country': u'country',
  u'countrycode': u'countryCode',
  u'extendedaddress': u'extendedAddress',
  u'locality': u'locality',
  u'pobox': u'poBox',
  u'postalcode': u'postalCode',
  u'region': u'region',
  u'streetaddress': u'streetAddress',
  }

ORGANIZATION_ARGUMENT_TO_FIELD_MAP = {
  u'costcenter': u'costCenter',
  u'department': u'department',
  u'description': u'description',
  u'domain': u'domain',
  u'location': u'location',
  u'name': u'name',
  u'symbol': u'symbol',
  u'title': u'title',
  }

def clearBodyList(body, itemName):
  if itemName in body:
    del body[itemName]
  body.setdefault(itemName, None)

def appendItemToBodyList(body, itemName, itemValue):
  if (itemName in body) and (body[itemName] == None):
    del body[itemName]
  body.setdefault(itemName, [])
  body[itemName].append(itemValue)

def gen_sha512_hash(password):
  from passlib.handlers.sha2_crypt import sha512_crypt
  return sha512_crypt.encrypt(password, rounds=5000)

def getUserAttributes(updateCmd=False, noUid=False):
  if updateCmd:
    body = {}
    need_password = False
  else:
    body = {u'name': {u'givenName': u'Unknown', u'familyName': u'Unknown'}}
    body[u'primaryEmail'] = getEmailAddress(noUid=noUid)
    need_password = True
  need_to_hash_password = True
  admin_body = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'admin':
      admin_body[u'status'] = getBoolean()
    elif myarg == u'nohash':
      need_to_hash_password = False
    elif myarg in UPDATE_USER_ARGUMENT_TO_PROPERTY_MAP:
      up = UPDATE_USER_ARGUMENT_TO_PROPERTY_MAP[myarg]
      userProperty = USER_PROPERTIES[up]
      propertyClass = userProperty[PROPERTY_CLASS]
      if PROPERTY_TYPE_KEYWORDS in userProperty:
        typeKeywords = userProperty[PROPERTY_TYPE_KEYWORDS]
        clTypeKeyword = typeKeywords[PTKW_CL_TYPE_KEYWORD]
      if up == u'givenName':
        body.setdefault(u'name', {})
        body[u'name'][up] = getString(OB_STRING)
      elif up == u'familyName':
        body.setdefault(u'name', {})
        body[u'name'][up] = getString(OB_STRING)
      elif up == u'password':
        need_password = False
        body[up] = getString(OB_STRING)
        if body[up].lower() == u'random':
          need_password = True
      elif propertyClass == PC_BOOLEAN:
        body[up] = getBoolean()
      elif up == u'hashFunction':
        body[up] = HASH_FUNCTION_MAP[myarg]
        need_to_hash_password = False
      elif up == u'primaryEmail' and updateCmd:
        body[up] = getEmailAddress(noUid=True)
      elif up == u'customerId' and updateCmd:
        body[up] = getString(OB_STRING)
      elif up == u'orgUnitPath':
        body[up] = getOrgUnitPath()
      elif up == u'addresses':
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          clearBodyList(body, up)
          continue
        address = {}
        getChoice([clTypeKeyword,])
        getKeywordAttribute(typeKeywords, address)
        if checkArgumentPresent(UNSTRUCTURED_FORMATTED_ARGUMENT):
          address[u'sourceIsStructured'] = False
          address[u'formatted'] = getString(OB_STRING)
        while CL_argvI < CL_argvLen:
          argument = getArgument()
          if argument in ADDRESS_ARGUMENT_TO_FIELD_MAP:
            address[ADDRESS_ARGUMENT_TO_FIELD_MAP[argument]] = getString(OB_STRING)
          elif argument == u'notprimary':
            break
          elif argument == u'primary':
            address[u'primary'] = True
            break
          else:
            unknownArgumentExit()
        appendItemToBodyList(body, up, address)
      elif up == u'ims':
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          clearBodyList(body, up)
          continue
        im = {}
        getChoice([clTypeKeyword,])
        getKeywordAttribute(typeKeywords, im)
        getChoice([IM_PROTOCOLS[PTKW_CL_TYPE_KEYWORD],])
        getKeywordAttribute(IM_PROTOCOLS, im)
        # Backwards compatability: notprimary|primary on either side of IM address
        im[u'primary'] = getChoice(PRIMARY_NOTPRIMARY_CHOICE_MAP, defaultChoice=False, mapChoice=True)
        im[u'im'] = getString(OB_STRING)
        im[u'primary'] = getChoice(PRIMARY_NOTPRIMARY_CHOICE_MAP, defaultChoice=im[u'primary'], mapChoice=True)
        appendItemToBodyList(body, up, im)
      elif up == u'notes':
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          clearBodyList(body, up)
          continue
        note = {}
        getKeywordAttribute(typeKeywords, note, defaultChoice=u'text_plain')
        if checkArgumentPresent(FILE_ARGUMENT):
          note[u'value'] = readFile(getString(OB_FILE_NAME), encoding=GM_Globals[GM_SYS_ENCODING])
        else:
          note[u'value'] = getString(OB_STRING, emptyOK=True).replace(u'\\n', u'\n')
        body[up] = note
      elif up == u'organizations':
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          clearBodyList(body, up)
          continue
        organization = {}
        while CL_argvI < CL_argvLen:
          argument = getArgument()
          if argument == clTypeKeyword:
            getKeywordAttribute(typeKeywords, organization)
          elif argument == typeKeywords[PTKW_CL_CUSTOMTYPE_KEYWORD]:
#            organization[typeKeywords[PTKW_ATTR_TYPE_KEYWORD]] = typeKeywords[PTKW_ATTR_TYPE_CUSTOM_VALUE]
            organization[typeKeywords[PTKW_ATTR_CUSTOMTYPE_KEYWORD]] = getString(OB_STRING)
          elif argument in ORGANIZATION_ARGUMENT_TO_FIELD_MAP:
            organization[ORGANIZATION_ARGUMENT_TO_FIELD_MAP[argument]] = getString(OB_STRING)
          elif argument == u'notprimary':
            break
          elif argument == u'primary':
            organization[u'primary'] = True
            break
          else:
            unknownArgumentExit()
        appendItemToBodyList(body, up, organization)
      elif up == u'phones':
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          clearBodyList(body, up)
          continue
        phone = {}
        while CL_argvI < CL_argvLen:
          argument = getArgument()
          if argument == clTypeKeyword:
            getKeywordAttribute(typeKeywords, phone)
          elif argument == u'value':
            phone[u'value'] = getString(OB_STRING)
          elif argument == u'notprimary':
            break
          elif argument == u'primary':
            phone[u'primary'] = True
            break
          else:
            unknownArgumentExit()
        appendItemToBodyList(body, up, phone)
      elif up == u'relations':
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          clearBodyList(body, up)
          continue
        relation = {}
        getKeywordAttribute(typeKeywords, relation)
        relation[u'value'] = getString(OB_STRING)
        appendItemToBodyList(body, up, relation)
      elif up == u'emails':
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          clearBodyList(body, up)
          continue
        an_email = {}
        getKeywordAttribute(typeKeywords, an_email)
        an_email[u'address'] = getEmailAddress(noUid=True)
        appendItemToBodyList(body, up, an_email)
      elif up == u'externalIds':
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          clearBodyList(body, up)
          continue
        externalid = {}
        getKeywordAttribute(typeKeywords, externalid)
        externalid[u'value'] = getString(OB_STRING)
        appendItemToBodyList(body, up, externalid)
      elif up == u'websites':
        if checkArgumentPresent(CLEAR_NONE_ARGUMENT):
          clearBodyList(body, up)
          continue
        website = {}
        getKeywordAttribute(typeKeywords, website)
        website[u'value'] = getString(OB_URL)
        website[u'primary'] = getChoice(PRIMARY_NOTPRIMARY_CHOICE_MAP, defaultChoice=False, mapChoice=True)
        appendItemToBodyList(body, up, website)
    elif myarg.find(u'.') > 0:
      try:
        (schemaName, fieldName) = CL_argv[CL_argvI-1].split(u'.')
      except ValueError:
        unknownArgumentExit()
      up = u'customSchemas'
      body.setdefault(up, {})
      body[up].setdefault(schemaName, {})
      if checkArgumentPresent(MULTIVALUE_ARGUMENT):
        body[up][schemaName].setdefault(fieldName, [])
        typeKeywords = USER_PROPERTIES[up][PROPERTY_TYPE_KEYWORDS]
        clTypeKeyword = typeKeywords[PTKW_CL_TYPE_KEYWORD]
        schemaValue = {}
        if checkArgumentPresent([clTypeKeyword,]):
          getKeywordAttribute(typeKeywords, schemaValue)
        schemaValue[u'value'] = getString(OB_STRING)
        body[up][schemaName][fieldName].append(schemaValue)
      else:
        body[up][schemaName][fieldName] = getString(OB_STRING)
    else:
      unknownArgumentExit()
  if need_password:
    body[u'password'] = u''.join(random.sample(u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789~`!@#$%^&*()-=_+:;"\'{}[]\\|', 25))
  if u'password' in body and need_to_hash_password:
    body[u'password'] = gen_sha512_hash(body[u'password'])
    body[u'hashFunction'] = u'crypt'
  return (body, admin_body)

def changeAdminStatus(cd, user, admin_body, i=0, count=0):
  try:
    callGAPI(cd.users(), u'makeAdmin',
             throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
             userKey=user, body=admin_body)
    printEntityKVList(EN_USER, user, [PHRASE_ADMIN_STATUS_CHANGED_TO, admin_body[u'status']], i, count)
  except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden):
    entityUnknownWarning(EN_USER, user, i, count)

# gam create user <EmailAddress> <UserAttributes>
def doCreateUser():
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  body, admin_body = getUserAttributes(updateCmd=False, noUid=True)
  try:
    callGAPI(cd.users(), u'insert',
             throw_reasons=[GAPI_DUPLICATE, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN, GAPI_INVALID_SCHEMA_VALUE],
             body=body, fields=u'primaryEmail')
    entityActionPerformed(EN_USER, body[u'primaryEmail'])
    if admin_body:
      changeAdminStatus(cd, body[u'primaryEmail'], admin_body)
  except GAPI_duplicate:
    entityDuplicateWarning(EN_USER, body[u'primaryEmail'])
  except (GAPI_domainNotFound, GAPI_forbidden):
    entityUnknownWarning(EN_USER, body[u'primaryEmail'])
  except GAPI_invalidSchemaValue:
    entityActionFailedWarning(EN_USER, body[u'primaryEmail'], PHRASE_INVALID_SCHEMA_VALUE)

# gam update users <UserTypeEntity> <UserAttributes>
def doUpdateUsers():
  updateUsers(getEntityToModify(defaultEntityType=CL_ENTITY_USERS)[1])

# gam update user <UserItem> <UserAttributes>
def doUpdateUser():
  updateUsers(getStringReturnInList(OB_USER_ITEM))

# gam <UserTypeEntity> update user <UserAttributes>
def updateUsers(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  body, admin_body = getUserAttributes(updateCmd=True)
  i = 0
  count = len(entityList)
  for user in entityList:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      if (u'primaryEmail' in body) and (body[u'primaryEmail'][:4].lower() == u'vfe@'):
        user_primary = callGAPI(cd.users(), u'get',
                                throw_reasons=GAPI_USER_GET_THROW_REASONS,
                                userKey=user, fields=u'primaryEmail,id')
        user = user_primary[u'id']
        user_primary = user_primary[u'primaryEmail']
        user_name, user_domain = splitEmailAddress(user_primary)
        body[u'primaryEmail'] = u'vfe.{0}.{1:05}@{2}'.format(user_name, random.randint(1, 99999), user_domain)
        body[u'emails'] = [{u'type': u'custom',
                            u'customType': u'former_employee',
                            u'primary': False, u'address': user_primary}]
      if body:
        callGAPI(cd.users(), u'update',
                 throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN, GAPI_INVALID, GAPI_INVALID_SCHEMA_VALUE],
                 userKey=user, body=body)
        entityActionPerformed(EN_USER, user, i, count)
      if admin_body:
        changeAdminStatus(cd, user, admin_body, i, count)
    except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden, GAPI_badRequest, GAPI_backendError, GAPI_systemError):
      entityUnknownWarning(EN_USER, user, i, count)
    except GAPI_invalidSchemaValue:
      entityActionFailedWarning(EN_USER, user, PHRASE_INVALID_SCHEMA_VALUE, i, count)
    except GAPI_invalid as e:
      entityActionFailedWarning(EN_USER, user, e.message, i, count)

# gam delete users <UserTypeEntity>
# gam delete user <UserItem>
def doDeleteUsers():
  deleteUsers(getEntityToModify(defaultEntityType=CL_ENTITY_USERS)[1])

def doDeleteUser():
  deleteUsers(getStringReturnInList(OB_USER_ITEM))

def deleteUsers(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for user in entityList:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      callGAPI(cd.users(), u'delete',
               throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
               userKey=user)
      entityActionPerformed(EN_USER, user, i, count)
    except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden):
      entityUnknownWarning(EN_USER, user, i, count)

# gam undelete users <UserEntity> [org|ou <OrgUnitPath>]
def doUndeleteUsers():
  undeleteUsers(getEntityList(OB_USER_ENTITY))

# gam undelete user <UserItem> [org|ou <OrgUnitPath>]
def doUndeleteUser():
  undeleteUsers(getStringReturnInList(OB_USER_ITEM))

def undeleteUsers(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  if checkArgumentPresent(ORG_OU_ARGUMENT):
    orgUnitPaths = getEntityList(OB_ORGUNIT_ENTITY, shlexSplit=True)
    userOrgUnitLists = orgUnitPaths if isinstance(orgUnitPaths, dict) else None
  else:
    orgUnitPaths = [u'/']
    userOrgUnitLists = None
  checkForExtraneousArguments()
  body = {u'orgUnitPath': u''}
  i = 0
  count = len(entityList)
  for user in entityList:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    user_uid = user if user.find(u'@') == -1 else None
    if not user_uid:
      printEntityKVList(EN_DELETED_USER, user,
                        [PHRASE_LOOKING_UP_GOOGLE_UNIQUE_ID, None],
                        i, count)
      try:
        deleted_users = callGAPIpages(cd.users(), u'list', u'users',
                                      throw_reasons=[GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                                      customer=GC_Values[GC_CUSTOMER_ID], showDeleted=True, maxResults=GC_Values[GC_USER_MAX_RESULTS])
      except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
        accessErrorExit(cd)
      matching_users = []
      for deleted_user in deleted_users:
        if str(deleted_user[u'primaryEmail']).lower() == user:
          matching_users.append(deleted_user)
      jcount = len(matching_users)
      if jcount == 0:
        entityUnknownWarning(EN_DELETED_USER, user, i, count)
        setSysExitRC(NO_ENTITIES_FOUND)
        continue
      if jcount > 1:
        printEntityKVList(EN_DELETED_USER, user,
                          [u'{0} {1} {2}'.format(PHRASE_MATCHED_THE_FOLLOWING, jcount, pluralEntityName(EN_DELETED_USER)),
                           PHRASE_PLEASE_SELECT_USER_TO_UNDELETE])
        printBlankLine()
        incrementIndentLevel()
        j = 0
        for matching_user in matching_users:
          printEntityName(EN_UNIQUE_ID, matching_user[u'id'], j, jcount)
          incrementIndentLevel()
          for attr_name in [u'creationTime', u'lastLoginTime', u'deletionTime']:
            if attr_name in matching_user:
              if matching_user[attr_name] == NEVER_TIME:
                matching_user[attr_name] = NEVER
              printKeyValueList([attr_name, matching_user[attr_name]])
          decrementIndentLevel()
          printBlankLine()
        decrementIndentLevel()
        setSysExitRC(MULTIPLE_DELETED_USERS_FOUND_RC)
        continue
      user_uid = matching_users[0][u'id']
    if userOrgUnitLists:
      orgUnitPaths = userOrgUnitLists[user]
    body[u'orgUnitPath'] = makeOrgUnitPathAbsolute(orgUnitPaths[0])
    try:
      callGAPI(cd.users(), u'undelete',
               throw_reasons=[GAPI_BAD_REQUEST, GAPI_INVALID, GAPI_DELETED_USER_NOT_FOUND],
               userKey=user_uid, body=body)
      entityActionPerformed(EN_DELETED_USER, user, i, count)
    except (GAPI_badRequest, GAPI_invalid, GAPI_deletedUserNotFound):
      entityUnknownWarning(EN_DELETED_USER, user, i, count)
#
USER_NAME_PROPERTY_PRINT_ORDER = [
  u'givenName',
  u'familyName',
  u'fullName',
  ]
USER_SCALAR_PROPERTY_PRINT_ORDER = [
  u'isAdmin',
  u'isDelegatedAdmin',
  u'agreedToTerms',
  u'ipWhitelisted',
  u'suspended',
  u'suspensionReason',
  u'changePasswordAtNextLogin',
  u'id',
  u'customerId',
  u'isMailboxSetup',
  u'includeInGlobalAddressList',
  u'creationTime',
  u'lastLoginTime',
  u'deletionTime',
  u'orgUnitPath',
  u'thumbnailPhotoUrl',
  ]
USER_ARRAY_PROPERTY_PRINT_ORDER = [
  u'notes',
  u'addresses',
  u'organizations',
  u'relations',
  u'emails',
  u'ims',
  u'phones',
  u'externalIds',
  u'websites',
  ]

USER_ADDRESSES_PROPERTY_PRINT_ORDER = [
  u'sourceIsStructured',
  u'formatted',
  u'extendedAddress',
  u'streetAddress',
  u'poBox',
  u'locality',
  u'region',
  u'postalCode',
  u'country',
  u'countryCode',
  ]

def _showType(up, row, typeKey, typeCustomValue, customTypeKey):
  if typeKey in row:
    if (row[typeKey] != typeCustomValue) or (not customTypeKey in row) or (not row[customTypeKey]):
      printKeyValueList([typeKey, row[typeKey]])
    elif up in [u'emails', u'externalIds', u'relations', u'websites']:
      printKeyValueList([typeKey, row[customTypeKey]])
    else:
      printKeyValueList([typeKey, row[typeKey]])
      incrementIndentLevel()
      printKeyValueList([customTypeKey, row[customTypeKey]])
      decrementIndentLevel()
    return True
  elif customTypeKey in row:
    printKeyValueList([customTypeKey, row[customTypeKey]])
    return True
  return False
#
USER_ARGUMENT_TO_PROPERTY_MAP = {
  u'address': [u'addresses',],
  u'addresses': [u'addresses',],
  u'admin': [u'isAdmin', u'isDelegatedAdmin',],
  u'agreed2terms': [u'agreedToTerms',],
  u'agreedtoterms': [u'agreedToTerms',],
  u'aliases': [u'aliases', u'nonEditableAliases',],
  u'changepassword': [u'changePasswordAtNextLogin',],
  u'changepasswordatnextlogin': [u'changePasswordAtNextLogin',],
  u'creationtime': [u'creationTime',],
  u'deletiontime': [u'deletionTime',],
  u'email': [u'emails',],
  u'emails': [u'emails',],
  u'externalid': [u'externalIds',],
  u'externalids': [u'externalIds',],
  u'familyname': [u'name.familyName',],
  u'firstname': [u'name.givenName',],
  u'fullname': [u'name.fullName',],
  u'gal': [u'includeInGlobalAddressList',],
  u'givenname': [u'name.givenName',],
  u'id': [u'id',],
  u'im': [u'ims',],
  u'ims': [u'ims',],
  u'includeinglobaladdresslist': [u'includeInGlobalAddressList',],
  u'ipwhitelisted': [u'ipWhitelisted',],
  u'isadmin': [u'isAdmin', u'isDelegatedAdmin',],
  u'isdelegatedadmin': [u'isAdmin', u'isDelegatedAdmin',],
  u'ismailboxsetup': [u'isMailboxSetup',],
  u'lastlogintime': [u'lastLoginTime',],
  u'lastname': [u'name.familyName',],
  u'name': [u'name.givenName', u'name.familyName', u'name.fullName',],
  u'nicknames': [u'aliases', u'nonEditableAliases',],
  u'noneditablealiases': [u'aliases', u'nonEditableAliases',],
  u'note': [u'notes',],
  u'notes': [u'notes',],
  u'org': [u'orgUnitPath',],
  u'organization': [u'organizations',],
  u'organizations': [u'organizations',],
  u'orgunitpath': [u'orgUnitPath',],
  u'otheremail': [u'emails',],
  u'otheremails': [u'emails',],
  u'ou': [u'orgUnitPath',],
  u'phone': [u'phones',],
  u'phones': [u'phones',],
  u'photo': [u'thumbnailPhotoUrl',],
  u'photourl': [u'thumbnailPhotoUrl',],
  u'primaryemail': [u'primaryEmail',],
  u'relation': [u'relations',],
  u'relations': [u'relations',],
  u'suspended': [u'suspended', u'suspensionReason',],
  u'thumbnailphotourl': [u'thumbnailPhotoUrl',],
  u'username': [u'primaryEmail',],
  u'website': [u'websites',],
  u'websites': [u'websites',],
  }

INFO_USER_OPTIONS = [u'noaliases', u'nogroups', u'nolicenses', u'nolicences', u'noschemas', u'schemas', u'userview',]

# gam info users <UserTypeEntity> [noaliases] [nogroups] [nolicenses|nolicences] [noschemas] [schemas <SchemaNameList>] [userview] [fields <UserFieldNameList>] [products|product <ProductIDList>] [skus|sku <SKUIDList>]
def doInfoUsers():
  infoUsers(getEntityToModify(defaultEntityType=CL_ENTITY_USERS)[1])

# gam info user <UserItem> [noaliases] [nogroups] [nolicenses|nolicences] [noschemas] [schemas <SchemaNameList>] [userview] [fields <UserFieldNameList>] [products|product <ProductIDList>] [skus|sku <SKUIDList>]
# gam info user
def doInfoUser():
  if CL_argvI < CL_argvLen:
    infoUsers(getStringReturnInList(OB_USER_ITEM))
  else:
    credentials = getClientCredentials(OAUTH2_GAPI_SCOPES)
    infoUsers([credentials.id_token[u'email']])

def infoUsers(entityList):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  getSchemas = getAliases = getGroups = getLicenses = True
  projection = u'full'
  customFieldMask = viewType = None
  fieldsList = []
  skus = sorted(GOOGLE_USER_SKUS)
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'noaliases':
      getAliases = False
    elif myarg == u'nogroups':
      getGroups = False
    elif myarg in [u'nolicenses', u'nolicences']:
      getLicenses = False
    elif myarg in [u'products', u'product']:
      skus = []
      for productId in getGoogleProductListMap():
        skus += [skuId for skuId in GOOGLE_SKUS if GOOGLE_SKUS[skuId] == productId]
    elif myarg in [u'sku', u'skus']:
      skus = getGoogleSKUListMap()
    elif myarg == u'noschemas':
      getSchemas = False
      projection = u'basic'
    elif myarg == u'schemas':
      getSchemas = True
      projection = u'custom'
      customFieldMask = getString(OB_SCHEMA_NAME_LIST)
    elif myarg == u'userview':
      viewType = u'domain_public'
      getGroups = getLicenses = False
    elif myarg in USER_ARGUMENT_TO_PROPERTY_MAP:
      if not fieldsList:
        fieldsList = [u'primaryEmail',]
      fieldsList.extend(USER_ARGUMENT_TO_PROPERTY_MAP[myarg])
    elif myarg == u'fields':
      if not fieldsList:
        fieldsList.append(u'primaryEmail')
      fieldNameList = getString(OB_FIELD_NAME_LIST)
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in USER_ARGUMENT_TO_PROPERTY_MAP:
          fieldsList.extend(USER_ARGUMENT_TO_PROPERTY_MAP[field])
        else:
          putArgumentBack()
          invalidChoiceExit(USER_ARGUMENT_TO_PROPERTY_MAP)
# Ignore info group arguments that may have come from whatis
    elif myarg in INFO_GROUP_OPTIONS:
      pass
    else:
      unknownArgumentExit()
  if fieldsList:
    fieldsList = u','.join(set(fieldsList)).replace(u'.', u'/')
  else:
    fieldsList = None
  i = 0
  count = len(entityList)
  for userEmail in entityList:
    i += 1
    userEmail = normalizeEmailAddressOrUID(userEmail)
    try:
      user = callGAPI(cd.users(), u'get',
                      throw_reasons=GAPI_USER_GET_THROW_REASONS,
                      userKey=userEmail, projection=projection, customFieldMask=customFieldMask, viewType=viewType, fields=fieldsList)
      printEntityName(EN_USER, user[u'primaryEmail'], i, count)
      incrementIndentLevel()
      printKeyValueList([u'Settings', u''])
      incrementIndentLevel()
      if u'name' in user:
        for up in USER_NAME_PROPERTY_PRINT_ORDER:
          if up in user[u'name']:
            printKeyValueList([USER_PROPERTIES[up][PROPERTY_TITLE], user[u'name'][up]])
      for up in USER_SCALAR_PROPERTY_PRINT_ORDER:
        if up in user:
          if USER_PROPERTIES[up][PROPERTY_CLASS] != PC_TIME:
            printKeyValueList([USER_PROPERTIES[up][PROPERTY_TITLE], user[up]])
          else:
            printKeyValueList([USER_PROPERTIES[up][PROPERTY_TITLE], [NEVER, user[up]][user[up] != NEVER_TIME]])
      decrementIndentLevel()
      for up in USER_ARRAY_PROPERTY_PRINT_ORDER:
        if up not in user:
          continue
        propertyValue = user[up]
        userProperty = USER_PROPERTIES[up]
        propertyClass = userProperty[PROPERTY_CLASS]
        propertyTitle = userProperty[PROPERTY_TITLE]
        typeKey = userProperty[PROPERTY_TYPE_KEYWORDS][PTKW_ATTR_TYPE_KEYWORD]
        typeCustomValue = userProperty[PROPERTY_TYPE_KEYWORDS][PTKW_ATTR_TYPE_CUSTOM_VALUE]
        customTypeKey = userProperty[PROPERTY_TYPE_KEYWORDS][PTKW_ATTR_CUSTOMTYPE_KEYWORD]
        if propertyClass == PC_ARRAY:
          if len(propertyValue) > 0:
            printKeyValueList([propertyTitle, u''])
            incrementIndentLevel()
            if isinstance(propertyValue, list):
              for row in propertyValue:
                _showType(up, row, typeKey, typeCustomValue, customTypeKey)
                incrementIndentLevel()
                for key in row:
                  if key in [typeKey, customTypeKey]:
                    continue
                  printKeyValueList([key, row[key]])
                decrementIndentLevel()
            else:
              printKeyValueList([propertyClass, propertyValue])
            decrementIndentLevel()
        elif propertyClass == PC_ADDRESSES:
          if len(propertyValue) > 0:
            printKeyValueList([propertyTitle, u''])
            incrementIndentLevel()
            if isinstance(propertyValue, list):
              for row in propertyValue:
                _showType(up, row, typeKey, typeCustomValue, customTypeKey)
                incrementIndentLevel()
                for key in USER_ADDRESSES_PROPERTY_PRINT_ORDER:
                  if key in row:
                    printKeyValueList([key, row[key]])
                decrementIndentLevel()
            else:
              printKeyValueList([propertyClass, propertyValue])
            decrementIndentLevel()
        elif propertyClass == PC_EMAILS:
          if len(propertyValue) > 0:
            needTitle = True
            if isinstance(propertyValue, list):
              for row in propertyValue:
                if row[u'address'].lower() == user[u'primaryEmail'].lower():
                  continue
                if needTitle:
                  needTitle = False
                  printKeyValueList([propertyTitle, u''])
                  incrementIndentLevel()
                if not _showType(up, row, typeKey, typeCustomValue, customTypeKey):
                  if not getAliases:
                    continue
                  printKeyValueList([typeKey, u'alias'])
                incrementIndentLevel()
                for key in row:
                  if key in [typeKey, customTypeKey]:
                    continue
                  printKeyValueList([key, row[key]])
                decrementIndentLevel()
            else:
              printKeyValueList([propertyClass, propertyValue])
            if not needTitle:
              decrementIndentLevel()
        elif propertyClass == PC_IMS:
          if len(propertyValue) > 0:
            printKeyValueList([propertyTitle, u''])
            incrementIndentLevel()
            if isinstance(propertyValue, list):
              protocolKey = IM_PROTOCOLS[PTKW_ATTR_TYPE_KEYWORD]
              protocolCustomValue = IM_PROTOCOLS[PTKW_ATTR_TYPE_CUSTOM_VALUE]
              customProtocolKey = IM_PROTOCOLS[PTKW_ATTR_CUSTOMTYPE_KEYWORD]
              for row in propertyValue:
                _showType(up, row, typeKey, typeCustomValue, customTypeKey)
                incrementIndentLevel()
                _showType(up, row, protocolKey, protocolCustomValue, customProtocolKey)
                for key in row:
                  if key in [typeKey, customTypeKey, protocolKey, customProtocolKey]:
                    continue
                  printKeyValueList([key, row[key]])
                decrementIndentLevel()
            else:
              printKeyValueList([propertyClass, propertyValue])
            decrementIndentLevel()
        elif propertyClass == PC_NOTES:
          if len(propertyValue) > 0:
            printKeyValueList([propertyTitle, u''])
            incrementIndentLevel()
            if isinstance(propertyValue, dict):
              typeVal = propertyValue.get(typeKey, u'text_plain')
              printKeyValueList([typeKey, typeVal])
              incrementIndentLevel()
              if typeVal == u'text_html':
                printKeyValueList([u'value', indentMultiLineText(dehtml(propertyValue[u'value']), n=1)])
              else:
                printKeyValueList([u'value', indentMultiLineText(propertyValue[u'value'], n=1)])
              decrementIndentLevel()
            else:
              printKeyValueList([indentMultiLineText(propertyValue)])
            decrementIndentLevel()
      if getSchemas:
        up = u'customSchemas'
        if up in user:
          propertyValue = user[up]
          userProperty = USER_PROPERTIES[up]
          propertyTitle = userProperty[PROPERTY_TITLE]
          typeKey = userProperty[PROPERTY_TYPE_KEYWORDS][PTKW_ATTR_TYPE_KEYWORD]
          typeCustomValue = userProperty[PROPERTY_TYPE_KEYWORDS][PTKW_ATTR_TYPE_CUSTOM_VALUE]
          customTypeKey = userProperty[PROPERTY_TYPE_KEYWORDS][PTKW_ATTR_CUSTOMTYPE_KEYWORD]
          printKeyValueList([USER_PROPERTIES[up][PROPERTY_TITLE], u''])
          incrementIndentLevel()
          for schema in propertyValue:
            printKeyValueList([u'Schema', schema])
            incrementIndentLevel()
            for field in propertyValue[schema]:
              if isinstance(propertyValue[schema][field], list):
                printKeyValueList([field])
                incrementIndentLevel()
                for an_item in propertyValue[schema][field]:
                  _showType(up, an_item, typeKey, typeCustomValue, customTypeKey)
                  incrementIndentLevel()
                  printKeyValueList([u'value', an_item[u'value']])
                  decrementIndentLevel()
                decrementIndentLevel()
              else:
                printKeyValueList([field, propertyValue[schema][field]])
            decrementIndentLevel()
          decrementIndentLevel()
      if getAliases:
        for up in [u'aliases', u'nonEditableAliases',]:
          if up in user:
            propertyValue = user[up]
            printKeyValueList([USER_PROPERTIES[up][PROPERTY_TITLE], u''])
            incrementIndentLevel()
            for alias in propertyValue:
              printKeyValueList([alias])
            decrementIndentLevel()
      if getGroups:
        groups = callGAPIpages(cd.groups(), u'list', u'groups',
                               throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
                               userKey=user[u'primaryEmail'], fields=u'nextPageToken,groups(name,email)')
        if groups:
          printKeyValueList([pluralEntityName(EN_GROUP), u'({0})'.format(len(groups))])
          incrementIndentLevel()
          for group in groups:
            printKeyValueList([group[u'name'], group[u'email']])
          decrementIndentLevel()
      if getLicenses:
        lic = buildGAPIObject(GAPI_LICENSING_API)
        licenses = []
        for skuId in skus:
          try:
            result = callGAPI(lic.licenseAssignments(), u'get',
                              throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_FORBIDDEN, GAPI_NOT_FOUND],
                              userId=user[u'primaryEmail'], productId=GOOGLE_SKUS[skuId], skuId=skuId)
            if result:
              licenses.append(result[u'skuId'])
          except GAPI_notFound:
            continue
          except (GAPI_userNotFound, GAPI_forbidden):
            entityUnknownWarning(EN_USER, userEmail, i, count)
            break
        if len(licenses) > 0:
          printKeyValueList([u'Licenses', u''])
          incrementIndentLevel()
          for u_license in licenses:
            printKeyValueList([u_license])
          decrementIndentLevel()
      decrementIndentLevel()
    except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden, GAPI_badRequest, GAPI_backendError, GAPI_systemError):
      entityUnknownWarning(EN_USER, userEmail, i, count)

USERS_ORDERBY_CHOICES_MAP = {
  u'familyname': u'familyName',
  u'lastname': u'familyName',
  u'givenname': u'givenName',
  u'firstname': u'givenName',
  u'email': u'email',
  }

# gam <UserTypeEntity> print
def doPrintUserEntity(entityList):
  if CL_argvI == CL_argvLen:
    for entity in entityList:
      printLine(entity)
    return
  doPrintUsers(entityList)

# gam [<UserTypeEntity>] print users [todrive] ([domain <DomainName>] [query <QueryUsers>] [deleted_only|only_deleted])|[select <UserTypeEntity>]
#	[delimiter <String>]
#	[groups] [license|licenses|licence|licences] [emailpart|emailparts|username]
#	[orderby <UserOrderByFieldName> [ascending|descending]] [userview]
#	[basic|full|allfields | <UserFieldName>* | fields <UserFieldNameList>]
def doPrintUsers(entityList=None):
  def _printUser(userEntity):
    if email_parts and (u'primaryEmail' in userEntity):
      userEmail = userEntity[u'primaryEmail']
      if userEmail.find(u'@') != -1:
        userEntity[u'primaryEmailLocal'], userEntity[u'primaryEmailDomain'] = splitEmailAddress(userEmail)
    addRowTitlesToCSVfile(flattenJSON(userEntity), csvRows, titles)

  def _callbackPrintUser(request_id, response, exception):
    REASON_TO_MESSAGE_MAP = {GAPI_RESOURCE_NOT_FOUND: PHRASE_DOES_NOT_EXIST}
    ri = request_id.splitlines()
    if exception is None:
      _printUser(response)
    else:
      http_status, reason, message = checkGAPIError(exception)
      if reason in [GAPI_USER_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN]:
        entityUnknownWarning(EN_USER, ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
        printKeyValueList([ERROR, errMsg])

  def _batchPrintUser(entityList):
    jcount = len(entityList)
    bcount = 0
    bsize = GC_Values[GC_BATCH_SIZE]
    if bsize > 1:
      dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackPrintUser)
    j = 0
    for userEntity in entityList:
      j += 1
      userEmail = normalizeEmailAddressOrUID(userEntity)
      if bsize > 1:
        parameters = dict([(u'userKey', userEmail), (u'fields', fields), (u'projection', projection), (u'customFieldMask', customFieldMask), (u'viewType', viewType)]+GM_Globals[GM_EXTRA_ARGS_LIST])
        dbatch.add(cd.users().get(**parameters), request_id=batchRequestID(u'', 0, 0, j, jcount, userEmail))
        bcount += 1
        if bcount == GC_Values[GC_BATCH_SIZE]:
          dbatch.execute()
          dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackPrintUser)
          bcount = 0
      else:
        try:
          user = callGAPI(cd.users(), u'get',
                          throw_reasons=GAPI_USER_GET_THROW_REASONS,
                          userKey=userEmail, fields=fields, projection=projection, customFieldMask=customFieldMask, viewType=viewType)
          _printUser(user)
        except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden, GAPI_badRequest, GAPI_backendError, GAPI_systemError):
          entityUnknownWarning(EN_USER, userEmail, j, jcount)
    if bcount > 0:
      dbatch.execute()

  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  todrive = False
  fieldsList = []
  fieldsTitles = {}
  titles, csvRows = initializeTitlesCSVfile(None)
  addFieldToCSVfile(u'primaryemail', USER_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
  sortHeaders = getGroupFeed = getLicenseFeed = email_parts = False
  customer = GC_Values[GC_CUSTOMER_ID]
  domain = None
  query = None
  projection = u'basic'
  customFieldMask = None
  viewType = deleted_only = orderBy = sortOrder = None
  itemsDelimiter = u' '
  select = selectLookup = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'domain':
      domain = getString(OB_DOMAIN_NAME).lower()
      customer = None
    elif myarg == u'query':
      query = getString(OB_QUERY)
    elif myarg in [u'deletedonly', u'onlydeleted']:
      deleted_only = True
    elif myarg == u'select':
      _, entityList = getEntityToModify(defaultEntityType=CL_ENTITY_USERS)
      select = True
    elif myarg == u'orderby':
      orderBy = getChoice(USERS_ORDERBY_CHOICES_MAP, mapChoice=True)
      sortOrder = getChoice(SORTORDER_CHOICES_MAP, defaultChoice=u'ascending', mapChoice=True)
    elif myarg == u'userview':
      viewType = u'domain_public'
    elif myarg == u'custom':
      if not fieldsList:
        fieldsList = [u'primaryEmail',]
      fieldsList.append(u'customSchemas')
      customFieldMask = getString(OB_SCHEMA_NAME_LIST).replace(u' ', u',')
      if customFieldMask.lower() == u'all':
        customFieldMask = None
        projection = u'full'
      else:
        projection = u'custom'
    elif myarg == u'delimiter':
      itemsDelimiter = getString(OB_STRING)
    elif myarg in PROJECTION_CHOICES_MAP:
      projection = myarg
      sortHeaders = True
      fieldsList = []
    elif myarg == u'allfields':
      projection = u'basic'
      sortHeaders = True
      fieldsList = []
    elif myarg in USER_ARGUMENT_TO_PROPERTY_MAP:
      if not fieldsList:
        fieldsList = [u'primaryEmail',]
      addFieldToCSVfile(myarg, USER_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
    elif myarg == u'fields':
      if not fieldsList:
        fieldsList = [u'primaryEmail',]
      fieldNameList = getString(OB_FIELD_NAME_LIST)
      for field in fieldNameList.lower().replace(u',', u' ').split():
        if field in USER_ARGUMENT_TO_PROPERTY_MAP:
          addFieldToCSVfile(field, USER_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
        else:
          putArgumentBack()
          invalidChoiceExit(USER_ARGUMENT_TO_PROPERTY_MAP)
    elif myarg == u'groups':
      getGroupFeed = True
    elif myarg in [u'license', u'licenses', u'licence', u'licences']:
      getLicenseFeed = True
    elif myarg in [u'emailpart', u'emailparts', u'username']:
      email_parts = True
    else:
      unknownArgumentExit()
  if entityList == None:
    if fieldsList:
      fields = u'nextPageToken,users({0})'.format(u','.join(set(fieldsList))).replace(u'.', u'/')
    else:
      fields = None
    printGettingAccountEntitiesInfo(EN_USER, qualifier=queryQualifier(query))
    page_message = getPageMessage(showFirstLastItems=True)
    try:
      entityList = callGAPIpages(cd.users(), u'list', u'users',
                                 page_message=page_message, message_attribute=u'primaryEmail',
                                 throw_reasons=[GAPI_DOMAIN_NOT_FOUND, GAPI_INVALID_INPUT, GAPI_BAD_REQUEST, GAPI_RESOURCE_NOT_FOUND, GAPI_FORBIDDEN],
                                 customer=customer, domain=domain, fields=fields, query=query,
                                 showDeleted=deleted_only, orderBy=orderBy, sortOrder=sortOrder, viewType=viewType,
                                 projection=projection, customFieldMask=customFieldMask, maxResults=GC_Values[GC_USER_MAX_RESULTS])
      for userEntity in entityList:
        _printUser(userEntity)
    except GAPI_domainNotFound:
      entityItemValueActionFailedWarning(EN_USER, PHRASE_LIST, EN_DOMAIN, domain, PHRASE_NOT_FOUND)
      return
    except GAPI_invalidInput:
      entityActionFailedWarning(EN_USER, PHRASE_LIST, invalidQuery(query))
      return
    except (GAPI_badRequest, GAPI_resourceNotFound, GAPI_forbidden):
      accessErrorExit(cd)
  else:
    if fieldsList:
      fields = u','.join(set(fieldsList)).replace(u'.', u'/')
      selectLookup = len(fieldsList) > 1
    else:
      fields = None
      selectLookup = True
    if selectLookup:
      _batchPrintUser(entityList)
    else:
      for userEntity in entityList:
        _printUser({u'primaryEmail': normalizeEmailAddressOrUID(userEntity)})
  if sortHeaders:
    sortCSVTitles([u'primaryEmail',], titles)
  if select and orderBy:
    import operator
    csvRows.sort(key=operator.itemgetter(u'name.{0}'.format(orderBy)), reverse=sortOrder == u'DESCENDING')
  if getGroupFeed:
    addTitleToCSVfile(u'Groups', titles)
    i = 0
    count = len(csvRows)
    for user in csvRows:
      i += 1
      userEmail = user[u'primaryEmail']
      printGettingAllEntityItemsForWhom(EN_GROUP_MEMBERSHIP, userEmail, i, count)
      groups = callGAPIpages(cd.groups(), u'list', u'groups',
                             userKey=userEmail)
      user[u'Groups'] = itemsDelimiter.join([groupname[u'email'] for groupname in groups])
  if getLicenseFeed:
    addTitleToCSVfile(u'Licenses', titles)
    licenses = doPrintLicenses(return_list=True)
    if len(licenses) > 1:
      for user in csvRows:
        user_licenses = []
        for u_license in licenses:
          if u_license[u'userId'].lower() == user[u'primaryEmail'].lower():
            user_licenses.append(u_license[u'skuId'])
        user[u'Licenses'] = itemsDelimiter.join(user_licenses)
  writeCSVfile(csvRows, titles, u'Users', todrive)

SITEVERIFICATION_METHOD_CHOICES_MAP = {
  u'cname': u'DNS_CNAME',
  u'txt': u'DNS_TXT',
  u'text': u'DNS_TXT',
  u'file': u'FILE',
  u'site': u'FILE',
  }

# gam create verify|verification <DomainName>
def doCreateSiteVerification():
  verif = buildGAPIObject(GAPI_SITEVERIFICATION_API)
  a_domain = getString(OB_DOMAIN_NAME)
  checkForExtraneousArguments()
  txt_record = callGAPI(verif.webResource(), u'getToken',
                        body={u'site': {u'type': u'INET_DOMAIN', u'identifier': a_domain},
                              u'verificationMethod': u'DNS_TXT'})
  printKeyValueList([u'TXT Record Name ', a_domain])
  printKeyValueList([u'TXT Record Value', txt_record[u'token']])
  printBlankLine()
  cname_record = callGAPI(verif.webResource(), u'getToken',
                          body={u'site': {u'type': u'INET_DOMAIN', u'identifier': a_domain},
                                u'verificationMethod': u'DNS_CNAME'})
  cname_token = cname_record[u'token']
  cname_list = cname_token.split(u' ')
  cname_subdomain = cname_list[0]
  cname_value = cname_list[1]
  printKeyValueList([u'CNAME Record Name ', u'{0}.{1}'.format(cname_subdomain, a_domain)])
  printKeyValueList([u'CNAME Record Value', cname_value])
  printBlankLine()
  webserver_file_record = callGAPI(verif.webResource(), u'getToken',
                                   body={u'site': {u'type': u'SITE', u'identifier': u'http://{0}/'.format(a_domain)},
                                         u'verificationMethod': u'FILE'})
  webserver_file_token = webserver_file_record[u'token']
  printKeyValueList([u'Saving web server verification file to', webserver_file_token])
  writeFile(webserver_file_token, u'google-site-verification: {0}'.format(webserver_file_token), continueOnError=True)
  printKeyValueList([u'Verification File URL', u'http://{0}/{1}'.format(a_domain, webserver_file_token)])
  printBlankLine()
  webserver_meta_record = callGAPI(verif.webResource(), u'getToken',
                                   body={u'site': {u'type': u'SITE', u'identifier': u'http://{0}/'.format(a_domain)},
                                         u'verificationMethod': u'META'})
  printKeyValueList([u'Meta URL', u'//{0}/'.format(a_domain)])
  printKeyValueList([u'Meta HTML Header Data', webserver_meta_record[u'token']])
  printBlankLine()

def _showSiteVerificationInfo(site):
  import urllib2
  printKeyValueList([u'Site', site[u'site'][u'identifier']])
  incrementIndentLevel()
  printKeyValueList([u'ID', urllib2.unquote(site[u'id'])])
  printKeyValueList([u'Type', site[u'site'][u'type']])
  printKeyValueList([u'All Owners', u''])
  if u'owners' in site:
    incrementIndentLevel()
    for owner in site[u'owners']:
      printKeyValueList([owner])
    decrementIndentLevel()
  decrementIndentLevel()

# gam update verify|verification <DomainName> cname|txt|text|file|site
def doUpdateSiteVerification():
  verif = buildGAPIObject(GAPI_SITEVERIFICATION_API)
  a_domain = getString(OB_DOMAIN_NAME)
  verificationMethod = getChoice(SITEVERIFICATION_METHOD_CHOICES_MAP, mapChoice=True)
  if verificationMethod in [u'DNS_TXT', u'DNS_CNAME']:
    verify_type = u'INET_DOMAIN'
    identifier = a_domain
  else:
    verify_type = u'SITE'
    identifier = u'http://{0}/'.format(a_domain)
  checkForExtraneousArguments()
  body = {u'site': {u'type': verify_type, u'identifier': identifier},
          u'verificationMethod': verificationMethod}
  try:
    verify_result = callGAPI(verif.webResource(), u'insert',
                             throw_reasons=[GAPI_BAD_REQUEST],
                             verificationMethod=verificationMethod, body=body)
  except GAPI_badRequest as e:
    printKeyValueList([ERROR, e.message])
    verify_data = callGAPI(verif.webResource(), u'getToken',
                           body=body)
    printKeyValueList([u'Method', verify_data[u'method']])
    printKeyValueList([u'Token', verify_data[u'token']])
    if verify_data[u'method'] == u'DNS_CNAME':
      try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = GOOGLE_NAMESERVERS
        cname_token = verify_data[u'token']
        cname_list = cname_token.split(u' ')
        cname_subdomain = cname_list[0]
        try:
          answers = resolver.query(u'{0},{1}'.format(cname_subdomain, a_domain), u'A')
          for answer in answers:
            printKeyValueList([u'DNS Record', answer])
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
          printKeyValueList([ERROR, u'No such domain found in DNS!'])
      except ImportError:
        pass
    elif verify_data[u'method'] == u'DNS_TXT':
      try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = GOOGLE_NAMESERVERS
        try:
          answers = resolver.query(a_domain, u'TXT')
          for answer in answers:
            printKeyValueList([u'DNS Record', answer.replace(u'"', u'')])
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
          printKeyValueList([ERROR, u'Domain not found in DNS!'])
      except ImportError:
        printKeyValueList([u'!!!No DNS'])
    return
  printKeyValueList([u'Verified!'])
  _showSiteVerificationInfo(verify_result)
  printKeyValueList([u'You can now add', a_domain, u'or it\'s subdomains as secondary or domain aliases of the Google Apps Account', GC_Values[GC_DOMAIN]])

# gam info verify|verification
def doInfoSiteVerification():
  verif = buildGAPIObject(GAPI_SITEVERIFICATION_API)
  checkForExtraneousArguments()
  sites = callGAPIitems(verif.webResource(), u'list', u'items')
  if sites:
    for site in sites:
      _showSiteVerificationInfo(site)
  else:
    printKeyValueList([u'No Sites Verified.'])

GUARDIAN_STATES = [u'COMPLETE', u'PENDING', u'GUARDIAN_INVITATION_STATE_UNSPECIFIED']

# gam create guardian|guardianinvite|inviteguardian <EmailAddress> <UserItem>
def doInviteGuardian():
  croom = buildGAPIObject(GAPI_CLASSROOM_API)
  body = {u'invitedEmailAddress': getEmailAddress()}
  studentId = getEmailAddress()
  checkForExtraneousArguments()
  try:
    result = callGAPI(croom.userProfiles().guardianInvitations(), u'create',
                      throw_reasons=[GAPI_NOT_FOUND, GAPI_INVALID_ARGUMENT, GAPI_BAD_REQUEST, GAPI_FORBIDDEN, GAPI_PERMISSION_DENIED, GAPI_ALREADY_EXISTS],
                      studentId=studentId, body=body)
    entityItemValueItemValueActionPerformed(EN_STUDENT, studentId, EN_GUARDIAN, result[u'invitedEmailAddress'], EN_GUARDIAN_INVITATION, result[u'invitationId'])
  except (GAPI_notFound, GAPI_invalidArgument, GAPI_badRequest, GAPI_forbidden):
    entityUnknownWarning(EN_STUDENT, studentId, 0, 0)
  except GAPI_alreadyExists:
    entityItemValueActionFailedWarning(EN_STUDENT, studentId, EN_GUARDIAN, body[u'invitedEmailAddress'], PHRASE_DUPLICATE)

# gam delete guardian|guardians <GuardianID>|<EmailAddress> <UserItem>
def doDeleteGuardian():
  croom = buildGAPIObject(GAPI_CLASSROOM_API)
  guardianId = getString(OB_GUARDIAN_ID)
  studentId = getEmailAddress()
  checkForExtraneousArguments()
  try:
    callGAPI(croom.userProfiles().guardians(), u'delete',
             throw_reasons=[GAPI_NOT_FOUND, GAPI_FORBIDDEN],
             studentId=studentId, guardianId=guardianId)
    entityItemValueActionPerformed(EN_STUDENT, studentId, EN_GUARDIAN, guardianId)
  except (GAPI_notFound, GAPI_forbidden):
    matchField = [u'invitedEmailAddress', u'invitationId'][guardianId.isdigit()]
    try:
      results = callGAPIpages(croom.userProfiles().guardianInvitations(), u'list', items=u'guardianInvitations',
                              throw_reasons=[GAPI_FORBIDDEN],
                              studentId=studentId, states=GUARDIAN_STATES)
      for result in results:
        if result[matchField] == guardianId:
          if result[u'state'] != u'PENDING':
            entityItemValueActionNotPerformedWarning(EN_STUDENT, studentId, EN_GUARDIAN, guardianId, PHRASE_NOT_A_GUARDIAN_INVITATION_NOT_PENDING)
          else:
            callGAPI(croom.userProfiles().guardianInvitations(), u'patch',
                     studentId=studentId, invitationId=result[u'invitationId'], updateMask=u'state', body={u'state': u'COMPLETE'})
            entityItemValueActionPerformed(EN_STUDENT, studentId, EN_GUARDIAN, result[u'invitedEmailAddress'])
          return
      entityItemValueActionFailedWarning(EN_STUDENT, studentId, EN_GUARDIAN, guardianId, PHRASE_NOT_A_GUARDIAN_OR_INVITATION)
    except GAPI_forbidden:
      entityUnknownWarning(EN_STUDENT, studentId, 0, 0)

#gam show guardian|guardians [invitedguardian <GuardianID>] [student <UserItem>] [invitations] [states <GuardianStateList>] [<UserTypeEntity>]
def doShowGuardians():
  printShowGuardians(False)

#gam print guardian|guardians [todrive] [invitedguardian <GuardianID>] [student <UserItem>] [invitations] [states <GuardianStateList>] [<UserTypeEntity>]
def doPrintGuardians():
  printShowGuardians(True)

def printShowGuardians(csvFormat):
  croom = buildGAPIObject(GAPI_CLASSROOM_API)
  invitedEmailAddress = None
  studentIds = [u'-',]
  states = None
  service = croom.userProfiles().guardians()
  items = u'guardians'
  entityType = EN_GUARDIAN
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile([u'studentEmail', u'studentId', u'invitedEmailAddress', u'guardianId'])
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    elif myarg == u'invitedguardian':
      invitedEmailAddress = getEmailAddress()
    elif myarg == u'student':
      studentIds = [getEmailAddress()]
    elif myarg == u'invitations':
      service = croom.userProfiles().guardianInvitations()
      items = u'guardianInvitations'
      entityType = EN_GUARDIAN_INVITATION
      titles, csvRows = initializeTitlesCSVfile([u'studentEmail', u'studentId', u'invitedEmailAddress', u'invitationId'])
      if states == None:
        states = GUARDIAN_STATES
    elif myarg == u'states':
      states = getString(OB_GUARDIAN_STATE_LIST).upper().split(u',')
    else:
      putArgumentBack()
      _, studentIds = getEntityToModify(defaultEntityType=CL_ENTITY_USERS)
  i = 0
  count = len(studentIds)
  for studentId in studentIds:
    i += 1
    kwargs = {u'invitedEmailAddress': invitedEmailAddress, u'studentId': studentId}
    if items == u'guardianInvitations':
      kwargs[u'states'] = states
    if studentId != u'-':
      if csvFormat:
        printGettingAllEntityItemsForWhom(entityType, studentId, i, count)
    try:
      result = callGAPIpages(service, u'list', items=items,
                             throw_reasons=[GAPI_NOT_FOUND, GAPI_INVALID_ARGUMENT, GAPI_BAD_REQUEST, GAPI_FORBIDDEN, GAPI_PERMISSION_DENIED],
                             **kwargs)
      jcount = len(result)
      if not csvFormat:
        entityPerformActionNumItems(EN_STUDENT, studentId, jcount, entityType, i, count)
        incrementIndentLevel()
        j = 0
        for guardian in result:
          j += 1
          printKeyValueListWithCount([u'invitedEmailAddress', guardian[u'invitedEmailAddress']], j, jcount)
          incrementIndentLevel()
          showJSON(None, guardian, skip_objects=[u'invitedEmailAddress',])
          decrementIndentLevel()
        decrementIndentLevel()
      else:
        for guardian in result:
          guardian[u'studentEmail'] = studentId
          addRowTitlesToCSVfile(flattenJSON(guardian), csvRows, titles)
    except (GAPI_notFound, GAPI_invalidArgument, GAPI_badRequest, GAPI_forbidden):
      entityUnknownWarning(EN_STUDENT, studentId, i, count)
    except GAPI_permissionDenied as e:
      entityActionFailedWarning(EN_STUDENT, studentId, e.message, i, count)
  if csvFormat:
    writeCSVfile(csvRows, titles, u'Guardians', todrive)

COURSE_STATE_OPTIONS_MAP = {
  u'active': u'ACTIVE',
  u'archived': u'ARCHIVED',
  u'provisioned': u'PROVISIONED',
  u'declined': u'DECLINED',
  }

def getCourseAttribute(myarg, body):
  if myarg == u'name':
    body[u'name'] = getString(OB_STRING)
  elif myarg == u'section':
    body[u'section'] = getString(OB_STRING)
  elif myarg == u'heading':
    body[u'descriptionHeading'] = getString(OB_STRING)
  elif myarg == u'description':
    body[u'description'] = getString(OB_STRING)
  elif myarg == u'room':
    body[u'room'] = getString(OB_STRING)
  elif myarg in [u'state', u'status']:
    body[u'courseState'] = getChoice(COURSE_STATE_OPTIONS_MAP, mapChoice=True)
  else:
    unknownArgumentExit()

# gam create course id|alias <CourseAlias> [teacher <UserItem>] <CourseAttributes>
def doCreateCourse():
  croom = buildGAPIObject(GAPI_CLASSROOM_API)
  body = {u'ownerId': u'me', u'name': u'Unknown Course'}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg in [u'alias', u'id']:
      body[u'id'] = getCourseAlias()
    elif myarg == u'teacher':
      body[u'ownerId'] = getEmailAddress()
    else:
      getCourseAttribute(myarg, body)
  try:
    result = callGAPI(croom.courses(), u'create',
                      throw_reasons=[GAPI_ALREADY_EXISTS, GAPI_NOT_FOUND, GAPI_PERMISSION_DENIED, GAPI_FORBIDDEN],
                      body=body)
    entityItemValueActionPerformed(EN_COURSE, result[u'name'], EN_COURSE_ID, result[u'id'])
  except GAPI_alreadyExists:
    entityItemValueActionFailedWarning(EN_COURSE, body[u'name'], EN_COURSE_ALIAS, removeCourseIdScope(body[u'id']), PHRASE_DUPLICATE)
  except GAPI_notFound:
    entityItemValueActionFailedWarning(EN_COURSE, body[u'name'], EN_TEACHER, body[u'ownerId'], PHRASE_DOES_NOT_EXIST)
  except (GAPI_permissionDenied, GAPI_forbidden):
    entityItemValueActionFailedWarning(EN_COURSE, body[u'name'], EN_TEACHER, body[u'ownerId'], PHRASE_NOT_ALLOWED)

# gam update courses <CourseEntity> <CourseAttributes>
def doUpdateCourses():
  updateCourses(getEntityList(OB_COURSE_ENTITY))

# gam update course <CourseID> <CourseAttributes>
def doUpdateCourse():
  updateCourses(getStringReturnInList(OB_COURSE_ID))

def updateCourses(entityList):
  croom = buildGAPIObject(GAPI_CLASSROOM_API)
  body = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    getCourseAttribute(myarg, body)
  updateMask = u','.join(body.keys())
  i = 0
  count = len(entityList)
  for course in entityList:
    i += 1
    body[u'id'] = addCourseIdScope(course)
    try:
      result = callGAPI(croom.courses(), u'patch',
                        throw_reasons=[GAPI_NOT_FOUND, GAPI_PERMISSION_DENIED],
                        id=body[u'id'], body=body, updateMask=updateMask)
      entityActionPerformed(EN_COURSE, result[u'id'], i, count)
    except GAPI_notFound:
      entityActionFailedWarning(EN_COURSE, removeCourseIdScope(body[u'id']), PHRASE_DOES_NOT_EXIST, i, count)
    except GAPI_permissionDenied:
      entityActionFailedWarning(EN_COURSE, removeCourseIdScope(body[u'id']), PHRASE_NOT_ALLOWED, i, count)

# gam delete courses <CourseEntity>
def doDeleteCourses():
  deleteCourses(getEntityList(OB_COURSE_ENTITY))

# gam delete course <CourseID>
def doDeleteCourse():
  deleteCourses(getStringReturnInList(OB_COURSE_ID))

def deleteCourses(entityList):
  croom = buildGAPIObject(GAPI_CLASSROOM_API)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for course in entityList:
    i += 1
    courseId = addCourseIdScope(course)
    try:
      callGAPI(croom.courses(), u'delete',
               throw_reasons=[GAPI_NOT_FOUND, GAPI_PERMISSION_DENIED],
               id=courseId)
      entityActionPerformed(EN_COURSE, removeCourseIdScope(courseId), i, count)
    except GAPI_notFound:
      entityActionFailedWarning(EN_COURSE, removeCourseIdScope(courseId), PHRASE_DOES_NOT_EXIST, i, count)
    except GAPI_permissionDenied:
      entityActionFailedWarning(EN_COURSE, removeCourseIdScope(courseId), PHRASE_NOT_ALLOWED, i, count)

# gam info courses <CourseEntity>
def doInfoCourses():
  infoCourses(getEntityList(OB_COURSE_ENTITY))

# gam info course <CourseID>
def doInfoCourse():
  infoCourses(getStringReturnInList(OB_COURSE_ID))

def infoCourses(entityList):
  croom = buildGAPIObject(GAPI_CLASSROOM_API)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for course in entityList:
    i += 1
    courseId = addCourseIdScope(course)
    try:
      result = callGAPI(croom.courses(), u'get',
                        throw_reasons=[GAPI_NOT_FOUND],
                        id=courseId)
      printEntityName(EN_COURSE, result[u'id'], i, count)
      incrementIndentLevel()
      showJSON(None, result)
      try:
        aliases = callGAPIpages(croom.courses().aliases(), u'list', u'aliases',
                                throw_reasons=[GAPI_NOT_IMPLEMENTED],
                                courseId=courseId)
        printKeyValueList([u'Aliases', u''])
        incrementIndentLevel()
        for alias in aliases:
          printKeyValueList([removeCourseIdScope(alias[u'alias'])])
        decrementIndentLevel()
      except GAPI_notImplemented:
        pass
      printKeyValueList([u'Participants', u''])
      incrementIndentLevel()
      teachers = callGAPIpages(croom.courses().teachers(), u'list', u'teachers',
                               throw_reasons=[GAPI_NOT_FOUND, GAPI_FORBIDDEN],
                               courseId=courseId)
      if teachers:
        printKeyValueList([u'Teachers', u''])
        incrementIndentLevel()
        for teacher in teachers:
          if u'emailAddress' in teacher[u'profile']:
            printKeyValueList([u'{0} - {1}'.format(teacher[u'profile'][u'name'][u'fullName'], teacher[u'profile'][u'emailAddress'])])
          else:
            printKeyValueList([teacher[u'profile'][u'name'][u'fullName']])
        decrementIndentLevel()
      students = callGAPIpages(croom.courses().students(), u'list', u'students',
                               throw_reasons=[GAPI_NOT_FOUND, GAPI_FORBIDDEN],
                               courseId=courseId)
      if students:
        printKeyValueList([u'Students', u''])
        incrementIndentLevel()
        for student in students:
          if u'emailAddress' in student[u'profile']:
            printKeyValueList([u'{0} - {1}'.format(student[u'profile'][u'name'][u'fullName'], student[u'profile'][u'emailAddress'])])
          else:
            printKeyValueList([student[u'profile'][u'name'][u'fullName']])
        decrementIndentLevel()
      decrementIndentLevel()
      decrementIndentLevel()
    except GAPI_notFound:
      entityActionFailedWarning(EN_COURSE, removeCourseIdScope(courseId), PHRASE_DOES_NOT_EXIST, i, count)
    except GAPI_forbidden:
      APIAccessDeniedExit()

# gam print courses [todrive] [alias|aliases] [teacher <UserItem>] [student <UserItem>] [delimiter <String>]
def doPrintCourses():
  croom = buildGAPIObject(GAPI_CLASSROOM_API)
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'id',])
  teacherId = None
  studentId = None
  get_aliases = False
  aliasesDelimiter = u' '
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'teacher':
      teacherId = getEmailAddress()
    elif myarg == u'student':
      studentId = getEmailAddress()
    elif myarg in [u'alias', u'aliases']:
      get_aliases = True
    elif myarg == u'delimiter':
      aliasesDelimiter = getString(OB_STRING)
    else:
      unknownArgumentExit()
  printGettingAccountEntitiesInfo(EN_COURSE)
  try:
    page_message = getPageMessage(noNL=True)
    all_courses = callGAPIpages(croom.courses(), u'list', u'courses',
                                page_message=page_message,
                                throw_reasons=[GAPI_NOT_FOUND, GAPI_FORBIDDEN, GAPI_BAD_REQUEST],
                                teacherId=teacherId, studentId=studentId)
  except (GAPI_notFound, GAPI_forbidden, GAPI_badRequest):
    if (not studentId) and teacherId:
      entityUnknownWarning(EN_TEACHER, teacherId)
      return
    if (not teacherId) and studentId:
      entityUnknownWarning(EN_STUDENT, studentId)
      return
    if studentId and teacherId:
      entityOrEntityUnknownWarning(EN_TEACHER, teacherId, EN_STUDENT, studentId)
      return
    all_courses = []
  for course in all_courses:
    addRowTitlesToCSVfile(flattenJSON(course), csvRows, titles)
  if get_aliases:
    addTitleToCSVfile(u'Aliases', titles)
    i = 0
    count = len(csvRows)
    for course in csvRows:
      i += 1
      courseId = course[u'id']
      printGettingAllEntityItemsForWhom(EN_ALIAS, entityTypeName(EN_COURSE, removeCourseIdScope(courseId)), i, count)
      course_aliases = callGAPIpages(croom.courses().aliases(), u'list', u'aliases',
                                     courseId=courseId)
      course[u'Aliases'] = aliasesDelimiter.join([removeCourseIdScope(alias[u'alias']) for alias in course_aliases])
  writeCSVfile(csvRows, titles, u'Courses', todrive)

def checkCourseExists(croom, courseId, i=0, count=0):
  courseId = addCourseIdScope(courseId)
  try:
    result = callGAPI(croom.courses(), u'get',
                      throw_reasons=[GAPI_NOT_FOUND],
                      id=courseId)
    return result[u'id']
  except GAPI_notFound:
    entityActionFailedWarning(EN_COURSE, removeCourseIdScope(courseId), PHRASE_DOES_NOT_EXIST, i, count)
    return None

def callbackAddParticipantsToCourse(request_id, response, exception):
  REASON_TO_MESSAGE_MAP = {GAPI_ALREADY_EXISTS: PHRASE_DUPLICATE, GAPI_FAILED_PRECONDITION: PHRASE_NOT_ALLOWED}
  ri = request_id.splitlines()
  if exception is None:
    entityItemValueActionPerformed(EN_COURSE, ri[RI_ENTITY], ri[RI_ROLE], ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
  else:
    http_status, reason, message = checkGAPIError(exception)
    if reason in [GAPI_NOT_FOUND, GAPI_FORBIDDEN, GAPI_BACKEND_ERROR]:
      errMsg = getPhraseDNEorSNA(ri[RI_ITEM])
    else:
      errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
    entityItemValueActionFailedWarning(EN_COURSE, ri[RI_ENTITY], ri[RI_ROLE], ri[RI_ITEM], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

def batchAddParticipantsToCourse(croom, courseId, i, count, addParticipants, role):
  if role == EN_STUDENT:
    service = croom.courses().students()
    attribute = u'userId'
  elif role == EN_TEACHER:
    service = croom.courses().teachers()
    attribute = u'userId'
  else:
    service = croom.courses().aliases()
    attribute = u'alias'
  setActionName(AC_ADD)
  jcount = len(addParticipants)
  noScopeCourseId = removeCourseIdScope(courseId)
  entityPerformActionNumItems(EN_COURSE, noScopeCourseId, jcount, role, i, count)
  incrementIndentLevel()
  bcount = 0
  bsize = GC_Values[GC_BATCH_SIZE]
  if bsize > 1:
    dbatch = croom.new_batch_http_request(callback=callbackAddParticipantsToCourse)
  body = {attribute: None}
  j = 0
  for participant in addParticipants:
    j += 1
    if role != EN_COURSE_ALIAS:
      cleanItem = body[attribute] = normalizeEmailAddressOrUID(participant)
    else:
      body[attribute] = addCourseIdScope(participant)
      cleanItem = removeCourseIdScope(body[attribute])
    if bsize > 1:
      parameters = dict([(u'courseId', courseId), (u'body', body)]+GM_Globals[GM_EXTRA_ARGS_LIST])
      dbatch.add(service.create(**parameters), request_id=batchRequestID(noScopeCourseId, i, count, j, jcount, cleanItem, role))
      bcount += 1
      if bcount == bsize:
        dbatch.execute()
        dbatch = croom.new_batch_http_request(callback=callbackAddParticipantsToCourse)
        bcount = 0
    else:
      try:
        callGAPI(service, u'create',
                 throw_reasons=[GAPI_ALREADY_EXISTS, GAPI_FAILED_PRECONDITION, GAPI_NOT_FOUND, GAPI_FORBIDDEN, GAPI_BACKEND_ERROR],
                 courseId=courseId, body=body)
        entityItemValueActionPerformed(EN_COURSE, noScopeCourseId, role, cleanItem, j, jcount)
      except GAPI_alreadyExists:
        entityItemValueActionFailedWarning(EN_COURSE, noScopeCourseId, role, cleanItem, PHRASE_DUPLICATE, j, jcount)
      except GAPI_failedPrecondition:
        entityItemValueActionFailedWarning(EN_COURSE, noScopeCourseId, role, cleanItem, PHRASE_NOT_ALLOWED, j, jcount)
      except (GAPI_notFound, GAPI_forbidden, GAPI_backendError):
        entityItemValueActionFailedWarning(EN_COURSE, noScopeCourseId, role, cleanItem, getPhraseDNEorSNA(cleanItem), j, jcount)
  if bcount > 0:
    dbatch.execute()
  decrementIndentLevel()

def callbackRemoveParticipantsFromCourse(request_id, response, exception):
  REASON_TO_MESSAGE_MAP = {GAPI_NOT_FOUND: PHRASE_DOES_NOT_EXIST}
  ri = request_id.splitlines()
  if exception is None:
    entityItemValueActionPerformed(EN_COURSE, ri[RI_ENTITY], ri[RI_ROLE], ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
  else:
    http_status, reason, message = checkGAPIError(exception)
    if reason in [GAPI_FORBIDDEN, GAPI_BACKEND_ERROR]:
      errMsg = getPhraseDNEorSNA(ri[RI_ITEM])
    elif reason == GAPI_NOT_FOUND and ri[RI_ROLE] != EN_COURSE_ALIAS:
      errMsg = u'{0} {1}'.format(PHRASE_NOT_A, singularEntityName(EN_PARTICIPANT))
    else:
      errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
    entityItemValueActionFailedWarning(EN_COURSE, ri[RI_ENTITY], ri[RI_ROLE], ri[RI_ITEM], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

def batchRemoveParticipantsFromCourse(croom, courseId, i, count, removeParticipants, role):
  if role == EN_STUDENT:
    service = croom.courses().students()
    attribute = u'userId'
  elif role == EN_TEACHER:
    service = croom.courses().teachers()
    attribute = u'userId'
  else:
    service = croom.courses().aliases()
    attribute = u'alias'
  setActionName(AC_REMOVE)
  jcount = len(removeParticipants)
  noScopeCourseId = removeCourseIdScope(courseId)
  entityPerformActionNumItems(EN_COURSE, noScopeCourseId, jcount, role, i, count)
  incrementIndentLevel()
  bcount = 0
  bsize = GC_Values[GC_BATCH_SIZE]
  if bsize > 1:
    dbatch = croom.new_batch_http_request(callback=callbackRemoveParticipantsFromCourse)
  kwargs = {}
  j = 0
  for participant in removeParticipants:
    j += 1
    if role != EN_COURSE_ALIAS:
      cleanItem = kwargs[attribute] = normalizeEmailAddressOrUID(participant)
    else:
      kwargs[attribute] = addCourseIdScope(participant)
      cleanItem = removeCourseIdScope(kwargs[attribute])
    if bsize > 1:
      parameters = dict([(u'courseId', courseId)]+kwargs.items()+GM_Globals[GM_EXTRA_ARGS_LIST])
      dbatch.add(service.delete(**parameters), request_id=batchRequestID(noScopeCourseId, i, count, j, jcount, cleanItem, role))
      bcount += 1
      if bcount == GC_Values[GC_BATCH_SIZE]:
        dbatch.execute()
        dbatch = croom.new_batch_http_request(callback=callbackRemoveParticipantsFromCourse)
        bcount = 0
    else:
      try:
        callGAPI(service, u'delete',
                 throw_reasons=[GAPI_NOT_FOUND, GAPI_FORBIDDEN, GAPI_BACKEND_ERROR],
                 courseId=courseId, **kwargs)
        entityItemValueActionPerformed(EN_COURSE, noScopeCourseId, role, cleanItem, j, jcount)
      except GAPI_notFound:
        if role != EN_COURSE_ALIAS:
          entityItemValueActionFailedWarning(EN_COURSE, noScopeCourseId, role, cleanItem, u'{0} {1}'.format(PHRASE_NOT_A, singularEntityName(EN_PARTICIPANT)), j, jcount)
        else:
          entityItemValueActionFailedWarning(EN_COURSE, noScopeCourseId, role, cleanItem, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_forbidden, GAPI_backendError):
        entityItemValueActionFailedWarning(EN_COURSE, noScopeCourseId, role, cleanItem, getPhraseDNEorSNA(cleanItem), j, jcount)
  if bcount > 0:
    dbatch.execute()
  decrementIndentLevel()

ADD_REMOVE_PARTICIPANT_TYPES_MAP = {
  u'alias': EN_COURSE_ALIAS,
  u'student': EN_STUDENT,
  u'students': EN_STUDENT,
  u'teacher': EN_TEACHER,
  u'teachers': EN_TEACHER,
  }
SYNC_PARTICIPANT_TYPES_MAP = {
  u'student': EN_STUDENT,
  u'students': EN_STUDENT,
  u'teacher': EN_TEACHER,
  u'teachers': EN_TEACHER,
  }
PARTICIPANT_EN_MAP = {
  EN_STUDENT: CL_ENTITY_STUDENTS,
  EN_TEACHER: CL_ENTITY_TEACHERS,
  }

# gam courses <CourseEntity> add alias <CourseAliasEntity>
# gam course <CourseID> add alias <CourseAlias>
# gam courses <CourseEntity> add teachers|students <UserTypeEntity>
# gam course <CourseID> add teacher|student <EmailAddress>
def doCourseAddParticipants(courseIdList, getEntityListArg):
  croom = buildGAPIObject(GAPI_CLASSROOM_API)
  role = getChoice(ADD_REMOVE_PARTICIPANT_TYPES_MAP, mapChoice=True)
  if not getEntityListArg:
    if role != EN_COURSE_ALIAS:
      addParticipants = getStringReturnInList(OB_EMAIL_ADDRESS)
    else:
      addParticipants = getStringReturnInList(OB_COURSE_ALIAS)
    courseParticipantLists = None
  else:
    if role != EN_COURSE_ALIAS:
      _, addParticipants = getEntityToModify(defaultEntityType=CL_ENTITY_USERS,
                                             typeMap={CL_ENTITY_COURSEPARTICIPANTS: PARTICIPANT_EN_MAP[role]},
                                             checkNotSuspended=True)
    else:
      addParticipants = getEntityList(OB_COURSE_ALIAS_ENTITY)
    courseParticipantLists = addParticipants if isinstance(addParticipants, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(courseIdList)
  for courseId in courseIdList:
    i += 1
    if courseParticipantLists:
      addParticipants = courseParticipantLists[courseId]
    courseId = checkCourseExists(croom, courseId, i, count)
    if courseId:
      batchAddParticipantsToCourse(croom, courseId, i, count, addParticipants, role)

# gam courses <CourseEntity> remove alias <CourseAliasEntity>
# gam course <CourseID> remove alias <CourseAlias>
# gam courses <CourseEntity> remove teachers|students <UserTypeEntity>
# gam course <CourseID> remove teacher|student <EmailAddress>
def doCourseRemoveParticipants(courseIdList, getEntityListArg):
  croom = buildGAPIObject(GAPI_CLASSROOM_API)
  role = getChoice(ADD_REMOVE_PARTICIPANT_TYPES_MAP, mapChoice=True)
  if not getEntityListArg:
    if role != EN_COURSE_ALIAS:
      removeParticipants = getStringReturnInList(OB_EMAIL_ADDRESS)
    else:
      removeParticipants = getStringReturnInList(OB_COURSE_ALIAS)
    courseParticipantLists = None
  else:
    if role != EN_COURSE_ALIAS:
      _, removeParticipants = getEntityToModify(defaultEntityType=CL_ENTITY_USERS,
                                                typeMap={CL_ENTITY_COURSEPARTICIPANTS: PARTICIPANT_EN_MAP[role]})
    else:
      removeParticipants = getEntityList(OB_COURSE_ALIAS_ENTITY)
    courseParticipantLists = removeParticipants if isinstance(removeParticipants, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(courseIdList)
  for courseId in courseIdList:
    i += 1
    if courseParticipantLists:
      removeParticipants = courseParticipantLists[courseId]
    courseId = checkCourseExists(croom, courseId, i, count)
    if courseId:
      batchRemoveParticipantsFromCourse(croom, courseId, i, count, removeParticipants, role)

# gam courses <CourseEntity> sync teachers|students <UserTypeEntity>
# gam course <CourseID> sync teachers|students <UserTypeEntity>
def doCourseSyncParticipants(courseIdList, getEntityListArg):
  croom = buildGAPIObject(GAPI_CLASSROOM_API)
  role = getChoice(SYNC_PARTICIPANT_TYPES_MAP, mapChoice=True)
  _, syncParticipants = getEntityToModify(defaultEntityType=CL_ENTITY_USERS,
                                          typeMap={CL_ENTITY_COURSEPARTICIPANTS: PARTICIPANT_EN_MAP[role]}, checkNotSuspended=True)
  checkForExtraneousArguments()
  courseParticipantLists = syncParticipants if isinstance(syncParticipants, dict) else None
  if not courseParticipantLists:
    syncParticipantsSet = set()
    for user in syncParticipants:
      syncParticipantsSet.add(normalizeEmailAddressOrUID(user))
  i = 0
  count = len(courseIdList)
  for courseId in courseIdList:
    i += 1
    if courseParticipantLists:
      syncParticipantsSet = set()
      for user in courseParticipantLists[courseId]:
        syncParticipantsSet.add(normalizeEmailAddressOrUID(user))
    courseId = checkCourseExists(croom, courseId, i, count)
    if courseId:
      currentParticipantsSet = set()
      for user in getUsersToModify(PARTICIPANT_EN_MAP[role], courseId):
        currentParticipantsSet.add(normalizeEmailAddressOrUID(user))
      batchAddParticipantsToCourse(croom, courseId, i, count, list(syncParticipantsSet-currentParticipantsSet), role)
      batchRemoveParticipantsFromCourse(croom, courseId, i, count, list(currentParticipantsSet-syncParticipantsSet), role)

# gam print course-participants [todrive] (course|class <CourseID>)*|([teacher <UserItem>] [student <UserItem>]) [show all|students|teachers]
def doPrintCourseParticipants():

  def _saveParticipants(participants, role):
    for member in participants:
      participant = flattenJSON(member)
      participant[u'courseId'] = courseId
      participant[u'courseName'] = course[u'name']
      participant[u'userRole'] = role
      addRowTitlesToCSVfile(participant, csvRows, titles)

  croom = buildGAPIObject(GAPI_CLASSROOM_API)
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'courseId',])
  courses = []
  teacherId = None
  studentId = None
  showMembers = u'all'
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg in [u'course', u'class']:
      courses.append(getCourseId())
    elif myarg == u'teacher':
      teacherId = getEmailAddress()
    elif myarg == u'student':
      studentId = getEmailAddress()
    elif myarg == u'show':
      showMembers = getChoice([u'all', u'students', u'teachers'])
    else:
      unknownArgumentExit()
  if len(courses) == 0:
    printGettingAccountEntitiesInfo(EN_COURSE)
    page_message = getPageMessage(noNL=True)
    try:
      all_courses = callGAPIpages(croom.courses(), u'list', u'courses',
                                  page_message=page_message,
                                  throw_reasons=[GAPI_NOT_FOUND, GAPI_FORBIDDEN, GAPI_BAD_REQUEST],
                                  teacherId=teacherId, studentId=studentId)
    except (GAPI_notFound, GAPI_forbidden, GAPI_badRequest):
      if not studentId:
        entityUnknownWarning(EN_TEACHER, teacherId)
      elif not teacherId:
        entityUnknownWarning(EN_STUDENT, studentId)
      else:
        entityOrEntityUnknownWarning(EN_TEACHER, teacherId, EN_STUDENT, studentId)
      return
  else:
    all_courses = []
    for course in courses:
      courseId = addCourseIdScope(course)
      try:
        info = callGAPI(croom.courses(), u'get',
                        throw_reasons=[GAPI_NOT_FOUND],
                        id=courseId)
        all_courses.append(info)
      except GAPI_notFound:
        entityDoesNotExistWarning(EN_COURSE, courseId)
  i = 0
  count = len(all_courses)
  for course in all_courses:
    i += 1
    courseId = course[u'id']
    page_message = getPageMessageForWhom(forWhom=formatKeyValueList(u'',
                                                                    [singularEntityName(EN_COURSE), courseId],
                                                                    currentCount(i, count)),
                                         noNL=True)
    try:
      if showMembers != u'students':
        setGettingEntityItem(EN_TEACHER)
        results = callGAPIpages(croom.courses().teachers(), u'list', u'teachers',
                                page_message=page_message,
                                throw_reasons=[GAPI_NOT_FOUND, GAPI_FORBIDDEN],
                                courseId=courseId)
        _saveParticipants(results, u'TEACHER')
      if showMembers != u'teachers':
        setGettingEntityItem(EN_STUDENT)
        results = callGAPIpages(croom.courses().students(), u'list', u'students',
                                page_message=page_message,
                                throw_reasons=[GAPI_NOT_FOUND, GAPI_FORBIDDEN],
                                courseId=courseId)
        _saveParticipants(results, u'STUDENT')
    except GAPI_forbidden:
      APIAccessDeniedExit()
  writeCSVfile(csvRows, titles, u'Course Participants', todrive)

def encode_multipart(fields, files, boundary=None):
  def escape_quote(s):
    return s.replace('"', '\\"')

  def getFormDataLine(name, value, boundary):
    return '--{0}'.format(boundary), 'Content-Disposition: form-data; name="{0}"'.format(escape_quote(name)), '', str(value)

  if boundary is None:
    boundary = ''.join(random.choice(string.digits + string.ascii_letters) for i in range(30))
  lines = []
  for name, value in fields.items():
    if name == u'tags':
      for tag in value:
        lines.extend(getFormDataLine('tag', tag, boundary))
    else:
      lines.extend(getFormDataLine(name, value, boundary))
  for name, value in files.items():
    filename = value[u'filename']
    mimetype = value[u'mimetype']
    lines.extend((
      '--{0}'.format(boundary),
      'Content-Disposition: form-data; name="{0}"; filename="{1}"'.format(escape_quote(name), escape_quote(filename)),
      'Content-Type: {0}'.format(mimetype),
      '',
      value[u'content'],
    ))
  lines.extend((
    '--{0}--'.format(boundary),
    '',
  ))
  body = '\r\n'.join(lines)
  headers = {
    'Content-Type': 'multipart/form-data; boundary={0}'.format(boundary),
    'Content-Length': str(len(body)),
  }
  return (body, headers)

# gam printer register
def doPrinterRegister():
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  form_fields = {u'name': u'GAM',
                 u'proxy': u'GAM',
                 u'uuid': cp._http.request.credentials.id_token[u'sub'],
                 u'manufacturer': __author__,
                 u'model': u'cp1',
                 u'gcp_version': u'2.0',
                 u'setup_url': GAM_URL,
                 u'support_url': u'https://groups.google.com/forum/#!forum/google-apps-manager',
                 u'update_url': GAM_RELEASES,
                 u'firmware': __version__,
                 u'semantic_state': {"version": "1.0", "printer": {"state": "IDLE",}},
                 u'use_cdd': True,
                 u'capabilities': {"version": "1.0",
                                   "printer": {"supported_content_type": [{"content_type": "application/pdf", "min_version": "1.5"},
                                                                          {"content_type": "image/jpeg"},
                                                                          {"content_type": "text/plain"},
                                                                         ],
                                               "copies": {"default": 1, "max": 100},
                                               "media_size": {"option": [{"name": "ISO_A4", "width_microns": 210000, "height_microns": 297000},
                                                                         {"name": "NA_LEGAL", "width_microns": 215900, "height_microns": 355600},
                                                                         {"name": "NA_LETTER", "width_microns": 215900, "height_microns": 279400, "is_default": True},
                                                                        ],
                                                             },
                                              },
                                  },
                 u'tags': [u'GAM', GAM_URL],
                }
  body, headers = encode_multipart(form_fields, {})
  #Get the printer first to make sure our OAuth access token is fresh
  callGAPI(cp.printers(), u'list')
  _, result = cp._http.request(uri='https://www.google.com/cloudprint/register', method='POST', body=body, headers=headers)
  result = checkCloudPrintResult(result)
  entityActionPerformed(EN_PRINTER, result[u'printers'][0][u'id'])
#
PRINTER_UPDATE_ITEMS_CHOICES_MAP = {
  u'currentquota': u'currentQuota',
  u'dailyquota': u'dailyQuota',
  u'defaultdisplayname': u'defaultDisplayName',
  u'description': u'description',
  u'displayname': u'displayName',
  u'firmware': u'firmware',
  u'gcpversion': u'gcpVersion',
  u'istosaccepted': u'isTosAccepted',
  u'manufacturer': u'manufacturer',
  u'model': u'model',
  u'name': u'name',
  u'ownerid': u'ownerId',
  u'proxy': u'proxy',
  u'public': u'public',
  u'quotaenabled': u'quotaEnabled',
  u'setupurl': u'setupUrl',
  u'status': u'status',
  u'supporturl': u'supportUrl',
  u'type': u'type',
  u'updateurl': u'updateUrl',
  u'uuid': u'uuid',
  }

# gam update printers <PrinterIDEntity> <PrinterAttributes>
def doUpdatePrinters():
  updatePrinters(getEntityList(OB_PRINTER_ID_ENTITY))

# gam update printer <PrinterID> <PrinterAttributes>
def doUpdatePrinter():
  updatePrinters(getStringReturnInList(OB_PRINTER_ID))

def updatePrinters(entityList):
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  kwargs = {}
  while CL_argvI < CL_argvLen:
    item = getChoice(PRINTER_UPDATE_ITEMS_CHOICES_MAP, mapChoice=True)
    if item in [u'isTosAccepted', u'public', u'quotaEnabled']:
      kwargs[item] = getBoolean()
    elif item in [u'currentQuota', u'dailyQuota', u'status']:
      kwargs[item] = getInteger(minVal=0)
    elif item in [u'displayName', u'defaultDisplayName']:
      kwargs[item] = getString(OB_STRING, emptyOK=True)
    else:
      kwargs[item] = getString(OB_STRING)
  i = 0
  count = len(entityList)
  for printerId in entityList:
    i += 1
    try:
      callGCP(cp.printers(), u'update',
              throw_messages=[GCP_UNKNOWN_PRINTER],
              printerid=printerId, **kwargs)
      entityActionPerformed(EN_PRINTER, printerId, i, count)
    except GCP_unknownPrinter:
      entityActionFailedWarning(EN_PRINTER, printerId, PHRASE_DOES_NOT_EXIST, i, count)

# gam delete printers <PrinterIDEntity>
def doDeletePrinters():
  deletePrinters(getEntityList(OB_PRINTER_ID_ENTITY))

# gam delete printer <PrinterID>
def doDeletePrinter():
  deletePrinters(getStringReturnInList(OB_PRINTER_ID))

def deletePrinters(entityList):
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for printerId in entityList:
    i += 1
    try:
      callGCP(cp.printers(), u'delete',
              throw_messages=[GCP_UNKNOWN_PRINTER],
              printerid=printerId)
      entityActionPerformed(EN_PRINTER, printerId, i, count)
    except GCP_unknownPrinter:
      entityActionFailedWarning(EN_PRINTER, printerId, PHRASE_DOES_NOT_EXIST, i, count)

# gam info printers <PrinterIDEntity> [everything]
def doInfoPrinters():
  infoPrinters(getEntityList(OB_PRINTER_ID_ENTITY))

# gam info printer <PrinterID> [everything]
def doInfoPrinter():
  infoPrinters(getStringReturnInList(OB_PRINTER_ID))

def infoPrinters(entityList):
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  everything = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'everything':
      everything = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(entityList)
  for printerId in entityList:
    i += 1
    try:
      result = callGCP(cp.printers(), u'get',
                       throw_messages=[GCP_UNKNOWN_PRINTER],
                       printerid=printerId)
      printEntityName(EN_PRINTER, printerId, i, count)
      incrementIndentLevel()
      printer_info = result[u'printers'][0]
      printer_info[u'createTime'] = datetime.datetime.fromtimestamp(int(printer_info[u'createTime'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
      printer_info[u'accessTime'] = datetime.datetime.fromtimestamp(int(printer_info[u'accessTime'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
      printer_info[u'updateTime'] = datetime.datetime.fromtimestamp(int(printer_info[u'updateTime'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
      printer_info[u'tags'] = u' '.join(printer_info[u'tags'])
      if not everything:
        del printer_info[u'capabilities']
        del printer_info[u'access']
      showJSON(None, printer_info)
      decrementIndentLevel()
    except GCP_unknownPrinter:
      entityActionFailedWarning(EN_PRINTER, printerId, PHRASE_DOES_NOT_EXIST, i, count)

# gam print printers [todrive] [query <QueryPrintJob>] [type <String>] [status <String>] [extrafields <String>]
def doPrintPrinters():
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'id',])
  query = None
  printer_type = None
  connection_status = None
  extra_fields = None
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'query':
      query = getString(OB_QUERY)
    elif myarg == u'type':
      printer_type = getString(OB_STRING)
    elif myarg == u'status':
      connection_status = getString(OB_STRING)
    elif myarg == u'extrafields':
      extra_fields = getString(OB_STRING)
    else:
      unknownArgumentExit()
  printers = callGCP(cp.printers(), u'list',
                     q=query, type=printer_type, connection_status=connection_status, extra_fields=extra_fields)
  for printer in printers[u'printers']:
    printer[u'createTime'] = datetime.datetime.fromtimestamp(int(printer[u'createTime'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
    printer[u'accessTime'] = datetime.datetime.fromtimestamp(int(printer[u'accessTime'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
    printer[u'updateTime'] = datetime.datetime.fromtimestamp(int(printer[u'updateTime'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
    printer[u'tags'] = u' '.join(printer[u'tags'])
    addRowTitlesToCSVfile(flattenJSON(printer), csvRows, titles)
  writeCSVfile(csvRows, titles, u'Printers', todrive)

def normalizeScopeList(rawScopeList):
  scopeList = []
  for scope in rawScopeList:
    scope = scope.lower()
    if scope != u'public':
      if scope.startswith(u'domain:'):
        scope = u'/hd/domain/{0}'.format(scope[7:])
      else:
        scope = normalizeEmailAddressOrUID(scope, noUid=True)
    scopeList.append(scope)
  return scopeList

def getPrinterScopeList(getEntityListArg):
  if not getEntityListArg:
    scope = getString(OB_EMAIL_ADDRESS).lower()
    if scope != u'public':
      if scope.find(u'@') == -1:
        if scope.startswith(u'domain:'):
          scope = u'/hd/domain/{0}'.format(scope[7:])
        else:
          scope = u'/hd/domain/{0}'.format(scope)
      else:
        scope = normalizeEmailAddressOrUID(scope, noUid=True)
    scopeList = [scope,]
    printerScopeLists = None
  else:
    _, scopeList = getEntityToModify(defaultEntityType=CL_ENTITY_USERS)
    printerScopeLists = scopeList if isinstance(scopeList, dict) else None
    if not printerScopeLists:
      scopeList = normalizeScopeList(scopeList)
  return scopeList, printerScopeLists

def batchAddACLsToPrinter(cp, printerId, i, count, scopeList, role):
  setActionName(AC_ADD)
  jcount = len(scopeList)
  entityPerformActionNumItems(EN_PRINTER, printerId, jcount, role, i, count)
  incrementIndentLevel()
  j = 0
  for scope in scopeList:
    j += 1
    if scope.lower() == u'public':
      public = True
      scope = None
      roleForScope = None
      skip_notification = None
    else:
      public = None
      roleForScope = role
      skip_notification = True
    try:
      callGCP(cp.printers(), u'share',
              throw_messages=[GCP_UNKNOWN_PRINTER, GCP_FAILED_TO_SHARE_THE_PRINTER, GCP_USER_IS_NOT_AUTHORIZED],
              printerid=printerId, role=roleForScope, scope=scope, public=public, skip_notification=skip_notification)
      if scope == None:
        scope = u'public'
        roleForScope = ROLE_USER
      entityItemValueActionPerformed(EN_PRINTER, printerId, roleForScope, scope, j, jcount)
    except GCP_userIsNotAuthorized:
      entityItemValueActionFailedWarning(EN_PRINTER, printerId, roleForScope, scope, PHRASE_ONLY_ONE_OWNER_ALLOWED, j, jcount)
    except GCP_failedToShareThePrinter:
      entityItemValueActionFailedWarning(EN_PRINTER, printerId, roleForScope, scope, PHRASE_INVALID_SCOPE, j, jcount)
    except GCP_unknownPrinter:
      entityActionFailedWarning(EN_PRINTER, printerId, PHRASE_DOES_NOT_EXIST, i, count)
      break
  decrementIndentLevel()

PRINTER_ROLE_MAP = {u'manager': ROLE_MANAGER, u'owner': ROLE_OWNER, u'user': ROLE_USER,}

# gam printers <PrinterIDEntity> add user|manager|owner <UserTypeEntity>|domain:<DomainName>|public
# gam printer <PrinterID> add user|manager|owner <EmailAddress>|<DomainName>|public
def doPrinterAddACL(printerIdList, getEntityListArg):
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  role = getChoice(PRINTER_ROLE_MAP, mapChoice=True)
  scopeList, printerScopeLists = getPrinterScopeList(getEntityListArg)
  checkForExtraneousArguments()
  i = 0
  count = len(printerIdList)
  for printerId in printerIdList:
    i += 1
    if printerScopeLists:
      scopeList = normalizeScopeList(printerScopeLists[printerId])
    batchAddACLsToPrinter(cp, printerId, i, count, scopeList, role)

def batchDeleteACLsFromPrinter(cp, printerId, i, count, scopeList, role):
  setActionName(AC_DELETE)
  jcount = len(scopeList)
  entityPerformActionNumItems(EN_PRINTER, printerId, jcount, role, i, count)
  incrementIndentLevel()
  j = 0
  for scope in scopeList:
    j += 1
    if scope.lower() == u'public':
      public = True
      scope = None
    else:
      public = None
    try:
      callGCP(cp.printers(), u'unshare',
              throw_messages=[GCP_UNKNOWN_PRINTER],
              printerid=printerId, scope=scope, public=public)
      if scope == None:
        scope = u'public'
      entityItemValueActionPerformed(EN_PRINTER, printerId, EN_SCOPE, scope, j, jcount)
    except GCP_unknownPrinter:
      entityActionFailedWarning(EN_PRINTER, printerId, PHRASE_DOES_NOT_EXIST, i, count)
      break
  decrementIndentLevel()

# gam printers <PrinterIDEntity> delete <UserTypeEntity>|domain:<DomainName>|public
# gam printer <PrinterID> delete <EmailAddress>|<DomainName>|public
def doPrinterDeleteACL(printerIdList, getEntityListArg):
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  scopeList, printerScopeLists = getPrinterScopeList(getEntityListArg)
  checkForExtraneousArguments()
  i = 0
  count = len(printerIdList)
  for printerId in printerIdList:
    i += 1
    if printerScopeLists:
      scopeList = normalizeScopeList(printerScopeLists[printerId])
    batchDeleteACLsFromPrinter(cp, printerId, i, count, scopeList, EN_SCOPE)

def getPrinterScopeListsForRole(cp, printerId, i, count, role):
  try:
    result = callGCP(cp.printers(), u'get',
                     throw_messages=[GCP_UNKNOWN_PRINTER],
                     printerid=printerId)
    try:
      jcount = len(result[u'printers'][0][u'access'])
    except KeyError:
      jcount = 0
    scopeList = []
    if jcount > 0:
      for acl in result[u'printers'][0][u'access']:
        if acl[u'role'] == role:
          scopeList.append(acl[u'scope'].lower())
    return scopeList
  except GCP_unknownPrinter:
    entityActionFailedWarning(EN_PRINTER, printerId, PHRASE_DOES_NOT_EXIST, i, count)
    return None

# gam printers <PrinterIDEntity> sync user|manager|owner <UserTypeEntity>|domain:<DomainName>|public
# gam printer <PrinterID> sync user|manager|owner <EmailAddress>|<DomainName>|public
def doPrinterSyncACL(printerIdList, getEntityListArg):
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  role = getChoice(PRINTER_ROLE_MAP, mapChoice=True)
  scopeList, printerScopeLists = getPrinterScopeList(getEntityListArg)
  checkForExtraneousArguments()
  i = 0
  count = len(printerIdList)
  for printerId in printerIdList:
    i += 1
    if printerScopeLists:
      scopeList = normalizeScopeList(printerScopeLists[printerId])
    currentScopeList = getPrinterScopeListsForRole(cp, printerId, i, count, role)
    if currentScopeList != None:
      batchAddACLsToPrinter(cp, printerId, i, count, list(set(scopeList) - set(currentScopeList)), role)
      batchDeleteACLsFromPrinter(cp, printerId, i, count, list(set(currentScopeList) - set(scopeList)), role)

# gam printers <PrinterIDEntity> wipe user|manager|owner
# gam printer <PrinterID> wipe user|manager|owner
def doPrinterWipeACL(printerIdList, getEntityListArg):
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  role = getChoice(PRINTER_ROLE_MAP, mapChoice=True)
  checkForExtraneousArguments()
  i = 0
  count = len(printerIdList)
  for printerId in printerIdList:
    i += 1
    currentScopeList = getPrinterScopeListsForRole(cp, printerId, i, count, role)
    if currentScopeList != None:
      batchDeleteACLsFromPrinter(cp, printerId, i, count, currentScopeList, role)

# gam printers <PrinterIDEntity> showacl [csv] [todrive]
# gam printer <PrinterID> showacl [csv] [todrive]
def doPrinterShowACL(printerIdList, getEntityListArg):
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  csvFormat = todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'id',])
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'csv':
      csvFormat = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(printerIdList)
  for printerId in printerIdList:
    i += 1
    try:
      result = callGCP(cp.printers(), u'get',
                       throw_messages=[GCP_UNKNOWN_PRINTER],
                       printerid=printerId)
      try:
        jcount = len(result[u'printers'][0][u'access'])
      except KeyError:
        jcount = 0
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
      if not csvFormat:
        entityPerformActionNumItems(EN_PRINTER, printerId, jcount, EN_ACL, i, count)
        if jcount == 0:
          continue
        incrementIndentLevel()
        for acl in result[u'printers'][0][u'access']:
          if u'key' in acl:
            acl[u'accessURL'] = CLOUDPRINT_ACCESS_URL.format(printerId, acl[u'key'])
          showJSON(None, acl)
          printBlankLine()
        decrementIndentLevel()
      elif jcount > 0:
        for acl in result[u'printers'][0][u'access']:
          printer = {u'id': printerId}
          if u'key' in acl:
            acl[u'accessURL'] = CLOUDPRINT_ACCESS_URL.format(printerId, acl[u'key'])
          addRowTitlesToCSVfile(flattenJSON(acl, flattened=printer), csvRows, titles)
    except GCP_unknownPrinter:
      entityActionFailedWarning(EN_PRINTER, printerId, PHRASE_DOES_NOT_EXIST, i, count)
  if csvFormat:
    writeCSVfile(csvRows, titles, u'PrinterACLs', todrive)

# gam printjobs <PrintJobEntity> cancel
# gam printjob <PrintJobID> cancel
def doPrintJobCancel(jobIdList):
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  checkForExtraneousArguments()
  ssd = u'{"state": {"type": "ABORTED", "user_action_cause": {"action_code": "CANCELLED"}}}'
  i = 0
  count = len(jobIdList)
  for jobId in jobIdList:
    i += 1
    try:
      callGCP(cp.jobs(), u'update',
              throw_messages=[GCP_UNKNOWN_JOB_ID],
              jobid=jobId, semantic_state_diff=ssd)
      entityActionPerformed(EN_PRINTJOB, jobId, i, count)
    except GCP_unknownJobId:
      entityActionFailedWarning(EN_PRINTJOB, jobId, PHRASE_DOES_NOT_EXIST, i, count)

# gam printjobs <PrintJobEntity> delete
# gam printjob <PrintJobID> delete
def doPrintJobDelete(jobIdList):
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  checkForExtraneousArguments()
  i = 0
  count = len(jobIdList)
  for jobId in jobIdList:
    i += 1
    try:
      callGCP(cp.jobs(), u'delete',
              throw_messages=[GCP_UNKNOWN_JOB_ID],
              jobid=jobId)
      entityActionPerformed(EN_PRINTJOB, jobId, i, count)
    except GCP_unknownJobId:
      entityActionFailedWarning(EN_PRINTJOB, jobId, PHRASE_DOES_NOT_EXIST, i, count)

# gam printjobs <PrintJobEntity> resubmit <PrinterID>
# gam printjob <PrintJobID> resubmit <PrinterID>
def doPrintJobResubmit(jobIdList):
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  printerId = getString(OB_PRINTER_ID)
  ssd = u'{"state": {"type": "HELD"}}'
  i = 0
  count = len(jobIdList)
  for jobId in jobIdList:
    i += 1
    try:
      result = callGCP(cp.jobs(), u'update',
                       throw_messages=[GCP_UNKNOWN_JOB_ID, GCP_CANT_MODIFY_FINISHED_JOB],
                       jobid=jobId, semantic_state_diff=ssd)
      ticket = callGCP(cp.jobs(), u'getticket',
                       throw_messages=[GCP_UNKNOWN_JOB_ID, GCP_CANT_MODIFY_FINISHED_JOB],
                       jobid=jobId, use_cjt=True)
      result = callGCP(cp.jobs(), u'resubmit',
                       throw_messages=[GCP_UNKNOWN_PRINTER, GCP_UNKNOWN_JOB_ID, GCP_CANT_MODIFY_FINISHED_JOB],
                       printerid=printerId, jobid=jobId, ticket=ticket)
      entityItemValueActionPerformed(EN_PRINTJOB, result[u'job'][u'id'], EN_PRINTER, printerId, i, count)
    except GCP_cantModifyFinishedJob:
      entityItemValueActionFailedWarning(EN_PRINTJOB, jobId, EN_PRINTER, printerId, PHRASE_FINISHED, i, count)
    except GCP_unknownJobId:
      entityActionFailedWarning(EN_PRINTJOB, jobId, PHRASE_DOES_NOT_EXIST, count)
    except GCP_unknownPrinter:
      entityItemValueActionFailedWarning(EN_PRINTJOB, jobId, EN_PRINTER, printerId, PHRASE_DOES_NOT_EXIST, i, count)
#
PRINTJOB_STATUS_MAP = {
  u'done': u'DONE',
  u'error': u'ERROR',
  u'held': u'HELD',
  u'inprogress': u'IN_PROGRESS',
  u'queued': u'QUEUED',
  u'submitted': u'SUBMITTED',
  }
# Map argument to API value
PRINTJOB_ASCENDINGORDER_MAP = {
  u'createtime': u'CREATE_TIME',
  u'status': u'STATUS',
  u'title': u'TITLE',
  }
# Map API value from ascending to descending
PRINTJOB_DESCENDINGORDER_MAP = {
  u'CREATE_TIME': u'CREATE_TIME_DESC',
  u'STATUS':  u'STATUS_DESC',
  u'TITLE': u'TITLE_DESC',
  }

PRINTJOBS_DEFAULT_JOB_LIMIT = 25
PRINTJOBS_DEFAULT_MAX_RESULTS = 100

def initPrintjobListParameters():
  return {u'older_or_newer': 0,
          u'age': None,
          u'sortorder': None,
          u'owner': None,
          u'query': None,
          u'status': None,
          u'jobLimit': PRINTJOBS_DEFAULT_JOB_LIMIT,
         }

def getPrintjobListParameters(myarg, parameters):
  if myarg == u'olderthan':
    parameters[u'older_or_newer'] = 1
    parameters[u'age'] = getAgeTime()
  elif myarg == u'newerthan':
    parameters[u'older_or_newer'] = -1
    parameters[u'age'] = getAgeTime()
  elif myarg == u'query':
    parameters[u'query'] = getString(OB_QUERY)
  elif myarg == u'status':
    parameters[u'status'] = getChoice(PRINTJOB_STATUS_MAP, mapChoice=True)
  elif myarg == u'orderby':
    parameters[u'sortorder'] = getChoice(PRINTJOB_ASCENDINGORDER_MAP, mapChoice=True)
    if getChoice(SORTORDER_CHOICES_MAP, defaultChoice=u'ascending', mapChoice=True) == u'DESCENDING':
      parameters[u'sortorder'] = PRINTJOB_DESCENDINGORDER_MAP[parameters[u'sortorder']]
  elif myarg in [u'owner', u'user']:
    parameters[u'owner'] = getEmailAddress(noUid=True)
  elif myarg == u'limit':
    parameters[u'jobLimit'] = getInteger(minVal=0)
  else:
    unknownArgumentExit()

# gam printjob <PrinterID>|any fetch
#	[olderthan|newerthan <PrintJobAge>] [query <QueryPrintJob>]
#	[status done|error|held|in_progress|queued|submitted]
#	[orderby <PrintJobOrderByFieldName> [ascending|descending]]
#	[owner|user <EmailAddress>]
#	[limit <Number>] [drivedir|(targetfolder <FilePath>)]
def doPrintJobFetch(printerIdList):
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  printerId = printerIdList[0]
  if printerId.lower() == u'any':
    printerId = None
  parameters = initPrintjobListParameters()
  targetFolder = os.getcwd()
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'drivedir':
      targetFolder = GC_Values[GC_DRIVE_DIR]
    elif myarg == u'targetfolder':
      targetFolder = os.path.expanduser(getString(OB_FILE_PATH))
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
    else:
      getPrintjobListParameters(myarg, parameters)
  if printerId:
    try:
      callGCP(cp.printers(), u'get',
              throw_messages=[GCP_UNKNOWN_PRINTER],
              printerid=printerId)
    except GCP_unknownPrinter:
      entityActionFailedWarning(EN_PRINTER, printerId, PHRASE_DOES_NOT_EXIST)
      return
  ssd = u'{"state": {"type": "DONE"}}'
  jobCount = offset = 0
  while True:
    if parameters[u'jobLimit'] == 0:
      limit = PRINTJOBS_DEFAULT_MAX_RESULTS
    else:
      limit = min(PRINTJOBS_DEFAULT_MAX_RESULTS, parameters[u'jobLimit']-jobCount)
      if limit == 0:
        break
    result = callGCP(cp.jobs(), u'list',
                     throw_messages=[GCP_UNKNOWN_PRINTER, GCP_NO_PRINT_JOBS],
                     printerid=printerId, q=parameters[u'query'], status=parameters[u'status'], sortorder=parameters[u'sortorder'],
                     owner=parameters[u'owner'], offset=offset, limit=limit)
    newJobs = result[u'range'][u'jobsCount']
    if newJobs == 0:
      break
    jobCount += newJobs
    offset += newJobs
    for job in result[u'jobs']:
      createTime = int(job[u'createTime'])/1000
      if parameters[u'older_or_newer'] > 0:
        if createTime > parameters[u'age']:
          continue
      elif parameters[u'older_or_newer'] < 0:
        if createTime < parameters[u'age']:
          continue
      fileUrl = job[u'fileUrl']
      jobId = job[u'id']
      fileName = os.path.join(targetFolder, u'{0}-{1}'.format(cleanFilename(job[u'title']), jobId))
      _, content = cp._http.request(fileUrl, method='GET')
      if writeFile(fileName, content, continueOnError=True):
#        ticket = callGCP(cp.jobs(), u'getticket',
#                         jobid=jobId, use_cjt=True)
        result = callGCP(cp.jobs(), u'update',
                         jobid=jobId, semantic_state_diff=ssd)
        entityItemValueModifierNewValueActionPerformed(EN_PRINTER, printerId, EN_PRINTJOB, jobId, AC_MODIFIER_TO, fileName)
  if jobCount == 0:
    entityItemValueActionFailedWarning(EN_PRINTER, printerId, EN_PRINTJOB, u'', PHRASE_NO_PRINT_JOBS)

# gam print printjobs [todrive] [printer|printerid <PrinterID>]
#	[olderthan|newerthan <PrintJobAge>] [query <QueryPrintJob>]
#	[status <PrintJobStatus>]
#	[orderby <PrintJobOrderByFieldName> [ascending|descending]]
#	[owner|user <EmailAddress>]
#	[limit <Number>]
def doPrintPrintJobs():
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'printerid', u'id'])
  printerId = None
  parameters = initPrintjobListParameters()
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg in [u'printer', u'printerid']:
      printerId = getString(OB_PRINTER_ID)
    else:
      getPrintjobListParameters(myarg, parameters)
  if printerId:
    try:
      callGCP(cp.printers(), u'get',
              throw_messages=[GCP_UNKNOWN_PRINTER],
              printerid=printerId)
    except GCP_unknownPrinter:
      entityActionFailedWarning(EN_PRINTER, printerId, PHRASE_DOES_NOT_EXIST)
      return
  jobCount = offset = 0
  while True:
    if parameters[u'jobLimit'] == 0:
      limit = PRINTJOBS_DEFAULT_MAX_RESULTS
    else:
      limit = min(PRINTJOBS_DEFAULT_MAX_RESULTS, parameters[u'jobLimit']-jobCount)
      if limit == 0:
        break
    result = callGCP(cp.jobs(), u'list',
                     printerid=printerId, q=parameters[u'query'], status=parameters[u'status'], sortorder=parameters[u'sortorder'],
                     owner=parameters[u'owner'], offset=offset, limit=limit)
    newJobs = result[u'range'][u'jobsCount']
    if newJobs == 0:
      break
    jobCount += newJobs
    offset += newJobs
    for job in result[u'jobs']:
      createTime = int(job[u'createTime'])/1000
      if parameters[u'older_or_newer'] > 0:
        if createTime > parameters[u'age']:
          continue
      elif parameters[u'older_or_newer'] < 0:
        if createTime < parameters[u'age']:
          continue
      updateTime = int(job[u'updateTime'])/1000
      job[u'createTime'] = datetime.datetime.fromtimestamp(createTime).strftime(u'%Y-%m-%d %H:%M:%S')
      job[u'updateTime'] = datetime.datetime.fromtimestamp(updateTime).strftime(u'%Y-%m-%d %H:%M:%S')
      job[u'tags'] = u' '.join(job[u'tags'])
      addRowTitlesToCSVfile(flattenJSON(job), csvRows, titles)
  writeCSVfile(csvRows, titles, u'Print Jobs', todrive)

# gam printjob <PrinterID> submit <FileName>|<URL> [name|title <String>] (tag <String>)*
def doPrintJobSubmit(printerIdList):
  cp = buildGAPIObject(GAPI_CLOUDPRINT_API)
  printerId = printerIdList[0]
  content = getString(OB_FILE_NAME_OR_URL)
  form_fields = {u'printerid': printerId,
                 u'title': content,
                 u'ticket': u'{"version": "1.0"}',
                 u'tags': [u'GAM', GAM_URL]}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'tag':
      form_fields[u'tags'].append(getString(OB_STRING))
    elif myarg in [u'name', u'title']:
      form_fields[u'title'] = getString(OB_STRING)
    else:
      unknownArgumentExit()
  form_files = {}
  if content[:4] == u'http':
    form_fields[u'content'] = content
    form_fields[u'contentType'] = u'url'
  else:
    filepath = content
    content = os.path.basename(content)
    mimetype = mimetypes.guess_type(filepath)[0]
    if mimetype == None:
      mimetype = u'application/octet-stream'
    filecontent = readFile(filepath)
    form_files[u'content'] = {u'filename': content, u'content': filecontent, u'mimetype': mimetype}
#  result = callGCP(cp.printers(), u'submit',
#                   body=body)
  body, headers = encode_multipart(form_fields, form_files)
  try:
    #Get the printer first to make sure our OAuth access token is fresh
    callGCP(cp.printers(), u'get',
            throw_messages=[GCP_UNKNOWN_PRINTER],
            printerid=printerId)
    _, result = cp._http.request(uri='https://www.google.com/cloudprint/submit', method='POST', body=body, headers=headers)
    result = checkCloudPrintResult(result)
    entityItemValueActionPerformed(EN_PRINTER, printerId, EN_PRINTJOB, result[u'job'][u'id'])
  except GCP_unknownPrinter:
    entityActionFailedWarning(EN_PRINTER, printerId, PHRASE_DOES_NOT_EXIST)

def _showASPs(user, asps, i=0, count=0):
  setActionName(AC_SHOW)
  jcount = len(asps)
  entityPerformActionNumItems(EN_USER, user, jcount, EN_APPLICATION_SPECIFIC_PASSWORD, i, count)
  if jcount == 0:
    setSysExitRC(NO_ENTITIES_FOUND)
    return
  incrementIndentLevel()
  for asp in asps:
    if asp[u'creationTime'] == u'0':
      created_date = u'Unknown'
    else:
      created_date = datetime.datetime.fromtimestamp(int(asp[u'creationTime'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
    if asp[u'lastTimeUsed'] == u'0':
      used_date = NEVER
    else:
      used_date = datetime.datetime.fromtimestamp(int(asp[u'lastTimeUsed'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
    printKeyValueList([u'ID', asp[u'codeId']])
    incrementIndentLevel()
    printKeyValueList([u'Name', asp[u'name']])
    printKeyValueList([u'Created', created_date])
    printKeyValueList([u'Last Used', used_date])
    decrementIndentLevel()
  decrementIndentLevel()

# gam <UserTypeEntity> delete|del asp|asps|applicationspecificpasswords <AspID>
def deleteASP(users):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  codeId = getString(OB_ASP_ID)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      callGAPI(cd.asps(), u'delete',
               throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_INVALID],
               userKey=user, codeId=codeId)
      entityItemValueActionPerformed(EN_USER, user, EN_APPLICATION_SPECIFIC_PASSWORD, codeId, i, count)
    except GAPI_userNotFound:
      entityUnknownWarning(EN_USER, user, i, count)
    except GAPI_invalid:
      entityItemValueActionFailedWarning(EN_USER, user, EN_APPLICATION_SPECIFIC_PASSWORD, codeId, PHRASE_DOES_NOT_EXIST, i, count)

# gam <UserTypeEntity> show asps|asp|applicationspecificpasswords
def showASPs(users):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      asps = callGAPIitems(cd.asps(), u'list', u'items',
                           throw_reasons=[GAPI_USER_NOT_FOUND],
                           userKey=user)
      _showASPs(user, asps, i, count)
    except GAPI_userNotFound:
      entityUnknownWarning(EN_USER, user, i, count)

def _showBackupCodes(user, codes, i, count):
  setActionName(AC_SHOW)
  jcount = len(codes)
  entityPerformActionNumItems(EN_USER, user, jcount, EN_BACKUP_VERIFICATION_CODE, i, count)
  if jcount == 0:
    setSysExitRC(NO_ENTITIES_FOUND)
    return
  incrementIndentLevel()
  j = 0
  for code in codes:
    j += 1
    printKeyValueList([u'{0:2}'.format(j), code[u'verificationCode']])
  decrementIndentLevel()

# gam <UserTypeEntity> update backupcodes|backupcode|verificationcodes
def updateBackupCodes(users):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      callGAPI(cd.verificationCodes(), u'generate',
               throw_reasons=[GAPI_USER_NOT_FOUND],
               userKey=user)
      codes = callGAPIitems(cd.verificationCodes(), u'list', u'items',
                            throw_reasons=[GAPI_USER_NOT_FOUND],
                            userKey=user)
      _showBackupCodes(user, codes, i, count)
    except GAPI_userNotFound:
      entityUnknownWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> delete|del backupcodes|backupcode|verificationcodes
def deleteBackupCodes(users):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      callGAPI(cd.verificationCodes(), u'invalidate',
               throw_reasons=[GAPI_USER_NOT_FOUND],
               userKey=user)
      printEntityKVList(EN_USER, user, [pluralEntityName(EN_BACKUP_VERIFICATION_CODE), u'', u'Invalidated'], i, count)
    except GAPI_userNotFound:
      entityUnknownWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> show backupcodes|backupcode|verificationcodes
def showBackupCodes(users):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      codes = callGAPIitems(cd.verificationCodes(), u'list', u'items',
                            throw_reasons=[GAPI_USER_NOT_FOUND],
                            userKey=user)
      _showBackupCodes(user, codes, i, count)
    except GAPI_userNotFound:
      entityUnknownWarning(EN_USER, user, i, count)

def getEmailAddressEntity(getEntityListArg):
  if not getEntityListArg:
    emailIds = getStringReturnInList(OB_EMAIL_ADDRESS)
  else:
    emailIds = getEntityList(OB_EMAIL_ADDRESS_ENTITY)
  emailLists = emailIds if isinstance(emailIds, dict) else None
  return (emailIds, emailLists)

def normalizeCalendarId(calendarId, user):
  if calendarId.lower() != u'primary':
    return normalizeEmailAddressOrUID(calendarId)
  return user
#
CALENDAR_NOTIFICATION_METHODS = [u'email', u'sms',]
CALENDAR_NOTIFICATION_TYPES_MAP = {
  u'eventcreation': u'eventCreation',
  u'eventchange': u'eventChange',
  u'eventcancellation': u'eventCancellation',
  u'eventresponse': u'eventResponse',
  u'agenda': u'agenda',
  }

def getCalendarAttributes(body):
  colorRgbFormat = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'selected':
      body[u'selected'] = getBoolean()
    elif myarg == u'hidden':
      body[u'hidden'] = getBoolean()
    elif myarg == u'summary':
      body[u'summaryOverride'] = getString(OB_STRING)
    elif myarg in [u'colorindex', u'colorid']:
      body[u'colorId'] = str(getInteger(minVal=CALENDAR_MIN_COLOR_INDEX, maxVal=CALENDAR_MAX_COLOR_INDEX))
    elif myarg == u'backgroundcolor':
      body[u'backgroundColor'] = getColorHexAttribute()
      body.setdefault(u'foregroundColor', u'#000000')
      colorRgbFormat = True
    elif myarg == u'foregroundcolor':
      body[u'foregroundColor'] = getColorHexAttribute()
      colorRgbFormat = True
    elif myarg == u'reminder':
      body.setdefault(u'defaultReminders', [])
      if not checkArgumentPresent(CLEAR_NONE_ARGUMENT):
        body[u'defaultReminders'].append(getCalendarReminder(True))
    elif myarg == u'notification':
      body.setdefault(u'notificationSettings', {u'notifications': []})
      method = getChoice(CALENDAR_NOTIFICATION_METHODS+CLEAR_NONE_ARGUMENT)
      if method not in CLEAR_NONE_ARGUMENT:
        body[u'notificationSettings'][u'notifications'].append({u'method': method,
                                                                u'type': getChoice(CALENDAR_NOTIFICATION_TYPES_MAP, mapChoice=True)})
    else:
      unknownArgumentExit()
  return colorRgbFormat

def _showCalendar(userCalendar, j, jcount):
  printEntityName(EN_CALENDAR, userCalendar[u'id'], j, jcount)
  incrementIndentLevel()
  printKeyValueList([u'Summary', userCalendar.get(u'summaryOverride', userCalendar[u'summary'])])
  printKeyValueList([u'Description', userCalendar.get(u'description', u'')])
  printKeyValueList([u'Access Level', userCalendar[u'accessRole']])
  printKeyValueList([u'Timezone', userCalendar[u'timeZone']])
  printKeyValueList([u'Location', userCalendar.get(u'location', u'')])
  printKeyValueList([u'Hidden', userCalendar.get(u'hidden', FALSE)])
  printKeyValueList([u'Selected', userCalendar.get(u'selected', FALSE)])
  printKeyValueList([u'Color ID', userCalendar[u'colorId'], u'Background Color', userCalendar[u'backgroundColor'], u'Foreground Color', userCalendar[u'foregroundColor']])
  printKeyValueList([u'Default Reminders', u''])
  incrementIndentLevel()
  for reminder in userCalendar.get(u'defaultReminders', []):
    printKeyValueList([u'Method', reminder[u'method'], u'Minutes', reminder[u'minutes']])
  decrementIndentLevel()
  printKeyValueList([u'Notifications', u''])
  incrementIndentLevel()
  if u'notificationSettings' in userCalendar:
    for notification in userCalendar[u'notificationSettings'].get(u'notifications', []):
      printKeyValueList([u'Method', notification[u'method'], u'Type', notification[u'type']])
  decrementIndentLevel()
  decrementIndentLevel()

# Process CalendarList functions
def _processCalendarList(user, i, count, calId, j, jcount, cal, function, **kwargs):
  userDefined = True
  try:
    result = callGAPI(cal.calendarList(), function,
                      throw_reasons=GAPI_CALENDAR_THROW_REASONS+[GAPI_NOT_FOUND, GAPI_DUPLICATE, GAPI_CANNOT_CHANGE_OWN_ACL],
                      **kwargs)
    if function == u'get':
      _showCalendar(result, j, jcount)
    else:
      entityItemValueActionPerformed(EN_USER, user, EN_CALENDAR, calId, j, jcount)
  except GAPI_notFound:
    entityItemValueActionFailedWarning(EN_USER, user, EN_CALENDAR, calId, PHRASE_DOES_NOT_EXIST, j, jcount)
  except GAPI_duplicate:
    entityItemValueActionFailedWarning(EN_USER, user, EN_CALENDAR, calId, PHRASE_DUPLICATE, j, jcount)
  except GAPI_cannotChangeOwnAcl:
    entityItemValueActionFailedWarning(EN_USER, user, EN_CALENDAR, calId, PHRASE_NOT_ALLOWED, j, jcount)
  except (GAPI_serviceNotAvailable, GAPI_authError):
    entityServiceNotApplicableWarning(EN_USER, user, i, count)
    userDefined = False
  return userDefined

# gam <UserTypeEntity> add calendar <CalendarItem> <CalendarAttributes>
# gam <UserTypeEntity> add calendars <CalendarEntity> <CalendarAttributes>
def addCalendars(users):
  addCalendar(users, getEntityListArg=True)

def addCalendar(users, getEntityListArg=False):
  calendarIds, calendarLists = getEmailAddressEntity(getEntityListArg)
  body = {u'selected': True, u'hidden': False}
  colorRgbFormat = getCalendarAttributes(body)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if calendarLists:
      calendarIds = calendarLists[user]
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    jcount = len(calendarIds)
    entityPerformActionNumItems(EN_USER, user, jcount, EN_CALENDAR, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for calendarId in calendarIds:
      j += 1
      body[u'id'] = calendarId = normalizeEmailAddressOrUID(calendarId)
      if not _processCalendarList(user, i, count, calendarId, j, jcount, cal, u'insert',
                                  body=body, colorRgbFormat=colorRgbFormat):
        break
    decrementIndentLevel()

# gam <UserTypeEntity> update calendar <CalendarItem> <CalendarAttributes>
# gam <UserTypeEntity> update calendars <CalendarEntity> <CalendarAttributes>
def updateCalendars(users):
  updateCalendar(users, getEntityListArg=True)

def updateCalendar(users, getEntityListArg=False):
  calendarIds, calendarLists = getEmailAddressEntity(getEntityListArg)
  body = {}
  colorRgbFormat = getCalendarAttributes(body)
  updateDeleteCalendars(users, calendarIds, calendarLists, u'update', body=body, colorRgbFormat=colorRgbFormat)

# gam <UserTypeEntity> delete|del calendar <CalendarItem>
# gam <UserTypeEntity> delete|del calendars <CalendarEntity>
def deleteCalendars(users):
  deleteCalendar(users, getEntityListArg=True)

def deleteCalendar(users, getEntityListArg=False):
  calendarIds, calendarLists = getEmailAddressEntity(getEntityListArg)
  checkForExtraneousArguments()
  updateDeleteCalendars(users, calendarIds, calendarLists, u'delete')

def updateDeleteCalendars(users, calendarIds, calendarLists, function, **kwargs):
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if calendarLists:
      calendarIds = calendarLists[user]
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    jcount = len(calendarIds)
    entityPerformActionNumItems(EN_USER, user, jcount, EN_CALENDAR, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for calendarId in calendarIds:
      j += 1
      calendarId = normalizeCalendarId(calendarId, user)
      if not _processCalendarList(user, i, count, calendarId, j, jcount, cal, function,
                                  calendarId=calendarId, **kwargs):
        break
    decrementIndentLevel()

# gam <UserTypeEntity> info calendar <CalendarItem>
# gam <UserTypeEntity> info calendars <CalendarEntity>
def infoCalendars(users):
  infoCalendar(users, getEntityListArg=True)

def infoCalendar(users, getEntityListArg=False):
  calendarIds, calendarLists = getEmailAddressEntity(getEntityListArg)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if calendarLists:
      calendarIds = calendarLists[user]
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    jcount = len(calendarIds)
    entityPerformActionNumItems(EN_USER, user, jcount, EN_CALENDAR, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for calendarId in calendarIds:
      j += 1
      calendarId = normalizeCalendarId(calendarId, user)
      if not _processCalendarList(user, i, count, calendarId, j, jcount, cal, u'get',
                                  calendarId=calendarId):
        break
    decrementIndentLevel()

# gam <UserTypeEntity> print calendars [todrive]
def printCalendars(users):
  printShowCalendars(users, True)

# gam <UserTypeEntity> show calendars
def showCalendars(users):
  printShowCalendars(users, False)

def printShowCalendars(users, csvFormat):
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile(None)
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    try:
      result = callGAPIpages(cal.calendarList(), u'list', u'items',
                             throw_reasons=GAPI_CALENDAR_THROW_REASONS)
      jcount = len(result)
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
      if not csvFormat:
        entityPerformActionNumItems(EN_USER, user, jcount, EN_CALENDAR, i, count)
        if jcount == 0:
          continue
        incrementIndentLevel()
        j = 0
        for userCalendar in result:
          j += 1
          _showCalendar(userCalendar, j, jcount)
        decrementIndentLevel()
      else:
        if jcount == 0:
          continue
        for userCalendar in result:
          row = {u'primaryEmail': user}
          addRowTitlesToCSVfile(flattenJSON(userCalendar, flattened=row), csvRows, titles)
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
  if csvFormat:
    sortCSVTitles([u'primaryEmail', u'id'], titles)
    writeCSVfile(csvRows, titles, u'Calendars', todrive)

# gam <UserTypeEntity> show calsettings
def showCalSettings(users):
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    try:
      feed = callGAPIpages(cal.settings(), u'list', u'items',
                           throw_reasons=GAPI_CALENDAR_THROW_REASONS)
      jcount = len(feed)
      printEntityKVList(EN_USER, user, [pluralEntityName(EN_CALENDAR_SETTINGS), u''], i, count)
      if jcount > 0:
        incrementIndentLevel()
        settings = {}
        for setting in feed:
          settings[setting[u'id']] = setting[u'value']
        for attr, value in sorted(settings.items()):
          printKeyValueList([attr, value])
        printBlankLine()
        decrementIndentLevel()
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# <CalendarSettings> ::==
#	[description <String>] [location <String>] [summary <String>] [timezone <String>]
def getCalendarSettings(summaryRequired=False):
  body = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'description':
      body[u'description'] = getString(OB_STRING, emptyOK=True)
    elif myarg == u'location':
      body[u'location'] = getString(OB_STRING, emptyOK=True)
    elif myarg == u'summary':
      body[u'summary'] = getString(OB_STRING)
    elif myarg == u'timezone':
      body[u'timeZone'] = getString(OB_STRING)
    else:
      unknownArgumentExit()
  if summaryRequired and not body.get(u'summary', None):
    missingArgumentExit(u'summary <String>')
  return body

# Process Calendar functions
def _processCalendar(user, i, count, calId, j, jcount, cal, function, **kwargs):
  userDefined = True
  try:
    result = callGAPI(cal.calendars(), function,
                      throw_reasons=GAPI_CALENDAR_THROW_REASONS+[GAPI_NOT_FOUND, GAPI_CANNOT_DELETE_PRIMARY_CALENDAR, GAPI_FORBIDDEN],
                      **kwargs)
    if function == u'insert':
      calId = result[u'id']
    entityItemValueActionPerformed(EN_USER, user, EN_CALENDAR, calId, j, jcount)
  except GAPI_notFound:
    entityItemValueActionFailedWarning(EN_USER, user, EN_CALENDAR, calId, PHRASE_DOES_NOT_EXIST, j, jcount)
  except (GAPI_cannotDeletePrimaryCalendar, GAPI_forbidden):
    entityItemValueActionFailedWarning(EN_USER, user, EN_CALENDAR, calId, PHRASE_NOT_ALLOWED, j, jcount)
  except (GAPI_serviceNotAvailable, GAPI_authError):
    entityServiceNotApplicableWarning(EN_USER, user, i, count)
    userDefined = False
  return userDefined

# gam <UserTypeEntity> create calendar|calendars <CalendarSettings>
def createCalendar(users):
  body = getCalendarSettings(summaryRequired=True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    _processCalendar(user, i, count, None, i, count, cal, u'insert', body=body)

# gam <UserTypeEntity> modify calendar <CalendarItem> <CalendarSettings>
# gam <UserTypeEntity> modify calendars <CalendarEntity> <CalendarSettings>
def modifyCalendars(users):
  modifyCalendar(users, getEntityListArg=True)

def modifyCalendar(users, getEntityListArg=False):
  calendarIds, calendarLists = getEmailAddressEntity(getEntityListArg)
  body = getCalendarSettings(summaryRequired=False)
  modifyRemoveCalendars(users, calendarIds, calendarLists, u'patch', body=body)

# gam <UserTypeEntity> remove calendar <CalendarItem>
# gam <UserTypeEntity> remove calendars <CalendarEntity>
def removeCalendars(users):
  removeCalendar(users, getEntityListArg=True)

def removeCalendar(users, getEntityListArg=False):
  calendarIds, calendarLists = getEmailAddressEntity(getEntityListArg)
  checkForExtraneousArguments()
  modifyRemoveCalendars(users, calendarIds, calendarLists, u'delete')

def modifyRemoveCalendars(users, calendarIds, calendarLists, function, **kwargs):
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if calendarLists:
      calendarIds = calendarLists[user]
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    jcount = len(calendarIds)
    entityPerformActionNumItems(EN_USER, user, jcount, EN_CALENDAR, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for calendarId in calendarIds:
      j += 1
      calendarId = normalizeCalendarId(calendarId, user)
      if not _processCalendar(user, i, count, calendarId, j, jcount, cal, function,
                              calendarId=calendarId, **kwargs):
        break
    decrementIndentLevel()

# gam <UserTypeEntity> update calattendees csv <FileName> [dryrun] [start <Date>] [end <Date>] [allevents]
def updateCalendarAttendees(users):
  csv_file = None
  do_it = True
  allevents = False
  start_date = end_date = None
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'csv':
      csv_file = getString(OB_FILE_NAME)
    elif myarg == u'dryrun':
      do_it = False
    elif myarg == u'start':
      start_date = getYYYYMMDD()
    elif myarg == u'end':
      end_date = getYYYYMMDD()
    elif myarg == u'allevents':
      allevents = True
    else:
      unknownArgumentExit()
  if not csv_file:
    missingArgumentExit(u'csv <FileName>')
  attendee_map = {}
  f = openFile(csv_file)
  csvFile = csv.reader(f)
  for row in csvFile:
    if len(row) >= 2:
      attendee_map[row[0].lower()] = row[1].lower()
  closeFile(f)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIObject(user)
    if not cal:
      continue
    printEntityKVList(EN_USER, user, [PHRASE_CHECKING, u''], i, count)
    incrementIndentLevel()
    try:
      page_token = None
      while True:
        events_page = callGAPIpages(cal.events(), u'list', u'items',
                                    throw_reasons=GAPI_CALENDAR_THROW_REASONS,
                                    calendarId=user, pageToken=page_token, timeMin=start_date, timeMax=end_date, showDeleted=False, showHiddenInvitations=False)
        jcount = len(events_page)
        if jcount == 0:
          break
        printKeyValueList([u'Got {0} items'.format(jcount)])
        for event in events_page:
          if event[u'status'] == u'cancelled':
            #printLine(u' skipping cancelled event')
            continue
          if u'summary' in event:
            event_summary = convertUTF8(event[u'summary'])
          else:
            event_summary = event[u'id']
          try:
            if not allevents and event[u'organizer'][u'email'].lower() != user:
              #printLine(u' skipping not-my-event {0}'.format(event_summary))
              continue
          except KeyError:
            pass # no email for organizer
          needs_update = False
          for attendee in event.get(u'attendees', []):
            if u'email' in attendee:
              old_email = attendee[u'email'].lower()
              if old_email in attendee_map:
                new_email = attendee_map[old_email]
                printKeyValueList([u'SWITCHING attendee {0} to {1} for {2}'.format(old_email, new_email, event_summary)])
                event[u'attendees'].remove(attendee)
                event[u'attendees'].append({u'email': new_email})
                needs_update = True
          if needs_update:
            body = {}
            body[u'attendees'] = event[u'attendees']
            printKeyValueList([u'UPDATING {0}'.format(event_summary)])
            if do_it:
              callGAPI(cal.events(), u'patch',
                       calendarId=user, eventId=event[u'id'], sendNotifications=False, body=body)
            else:
              printKeyValueList([u'Dry run, not pulling the trigger.'])
          #else:
          #  printLine(u' no update needed for {}'.format(event_summary))
        page_token = events_page.get(u'nextPageToken')
        if not page_token:
          break
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
      break
    decrementIndentLevel()

# gam <UserTypeEntity> transfer seccals <UserItem> [keepuser]
def transferSecCals(users):
  target_user = getEmailAddress()
  addBody = {u'role': u'owner', u'scope': {u'type': u'user', u'value': target_user}}
  remove_source_user = True
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'keepuser':
      remove_source_user = False
    else:
      unknownArgumentExit()
  if remove_source_user:
    target_user, target_cal = buildCalendarGAPIObject(target_user)
    if not target_cal:
      return
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, source_cal = buildCalendarGAPIObject(user)
    if not source_cal:
      continue
    try:
      source_calendars = callGAPIpages(source_cal.calendarList(), u'list', u'items',
                                       throw_reasons=GAPI_CALENDAR_THROW_REASONS,
                                       minAccessRole=u'owner', showHidden=True, fields=u'nextPageToken,items(id)')
      jcount = len(source_calendars)
      setActionName(AC_TRANSFER)
      entityPerformActionNumItems(EN_USER, user, jcount, EN_ACL, i, count)
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
        continue
      incrementIndentLevel()
      j = 0
      for source_calendar in source_calendars:
        j += 1
        calendarId = source_calendar[u'id']
        if calendarId.find(u'@group.calendar.google.com') != -1:
          setActionName(AC_ADD)
          try:
            result = callGAPI(source_cal.acl(), u'insert',
                              throw_reasons=[GAPI_NOT_FOUND, GAPI_INVALID],
                              calendarId=calendarId, body=addBody, fields=u'id,role')
            entityItemValueActionPerformed(EN_CALENDAR, calendarId, EN_ACL, formatACLScopeRole(result[u'id'], result[u'role']), j, jcount)
          except (GAPI_notFound, GAPI_invalid):
            entityUnknownWarning(EN_CALENDAR, calendarId, j, jcount)
            continue
          if remove_source_user:
            setActionName(AC_DELETE)
            try:
              ruleId = u'{0}:{1}'.format(u'user', user)
              callGAPI(target_cal.acl(), u'delete',
                       throw_reasons=[GAPI_NOT_FOUND, GAPI_INVALID],
                       calendarId=calendarId, ruleId=ruleId)
              entityItemValueActionPerformed(EN_CALENDAR, calendarId, EN_ACL, formatACLScopeRole(ruleId, None), j, jcount)
            except (GAPI_notFound, GAPI_invalid):
              entityUnknownWarning(EN_CALENDAR, calendarId, j, jcount)
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
    decrementIndentLevel()

def doDriveSearch(drive, user, i, count, query=None):
  if GC_Values[GC_SHOW_GETTINGS]:
    printGettingAllEntityItemsForWhom(EN_DRIVE_FILE_OR_FOLDER, user, i, count, qualifier=queryQualifier(query))
  page_message = getPageMessageForWhom(noNL=True)
  try:
    files = callGAPIpages(drive.files(), u'list', DRIVE_FILES_LIST,
                          page_message=page_message,
                          throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_INVALID_QUERY, GAPI_FILE_NOT_FOUND],
                          q=query, fields=u'nextPageToken,{0}(id)'.format(DRIVE_FILES_LIST), maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
    return [f_file[u'id'] for f_file in files]
  except GAPI_invalidQuery:
    entityItemValueActionFailedWarning(EN_USER, user, EN_DRIVE_FILE, PHRASE_LIST, invalidQuery(query), i, count)
  except GAPI_fileNotFound:
    printGettingEntityItemsForWhomDoneInfo(0)
  except (GAPI_serviceNotAvailable, GAPI_authError):
    entityServiceNotApplicableWarning(EN_USER, user, i, count)
  return None

def cleanFileIDsList(fileIdSelection, fileIds):
  fileIdSelection[u'fileIds'] = []
  fileIdSelection[u'root'] = []
  i = 0
  for fileId in fileIds:
    if fileId[:8].lower() == u'https://' or fileId[:7].lower() == u'http://':
      loc = fileId.find(u'/d/')
      if loc > 0:
        fileId = fileId[loc+3:]
        loc = fileId.find(u'/')
        if loc != -1:
          fileId = fileId[:loc]
      else:
        loc = fileId.find(u'/folderview?id=')
        if loc > 0:
          fileId = fileId[loc+15:]
          loc = fileId.find(u'&')
          if loc != -1:
            fileId = fileId[:loc]
        else:
          continue
    elif fileId.lower() == u'root':
      fileIdSelection[u'root'].append(i)
      fileId = fileId.lower()
    fileIdSelection[u'fileIds'].append(fileId)
    i += 1

def initDriveFileEntity():
  return {u'fileIds': [], u'query': None, u'dict': None, u'root': []}

def getDriveFileEntity(default=None, ignore=None):
  fileIdSelection = initDriveFileEntity()
  entitySelector = getEntitySelector()
  if entitySelector:
    cleanFileIDsList(fileIdSelection, getEntitySelection(entitySelector, False))
  else:
    myarg = getString(OB_DRIVE_FILE_ID, checkBlank=True, optional=default)
    if not myarg:
      if default:
        cleanFileIDsList(fileIdSelection, default)
      return fileIdSelection
    mycmd = myarg.lower()
    if ignore and mycmd in ignore:
      putArgumentBack()
      if default:
        cleanFileIDsList(fileIdSelection, default)
      return fileIdSelection
    if mycmd == u'id':
      cleanFileIDsList(fileIdSelection, getStringReturnInList(OB_DRIVE_FILE_ID))
    elif mycmd == u'ids':
      entityList = getEntityList(OB_DRIVE_FILE_ENTITY)
      if isinstance(entityList, dict):
        fileIdSelection[u'dict'] = entityList
      else:
        cleanFileIDsList(fileIdSelection, entityList)
    elif mycmd == u'query':
      fileIdSelection[u'query'] = getString(OB_QUERY)
    elif mycmd[:6] == u'query:':
      fileIdSelection[u'query'] = myarg[6:]
    elif mycmd == u'drivefilename':
      fileIdSelection[u'query'] = u"'me' in owners and {0} = '{1}'".format(DRIVE_FILE_NAME, getString(OB_DRIVE_FILE_NAME))
    elif mycmd[:14] == u'drivefilename:':
      fileIdSelection[u'query'] = u"'me' in owners and {0} = '{1}'".format(DRIVE_FILE_NAME, myarg[14:])
    elif mycmd == u'root':
      cleanFileIDsList(fileIdSelection, [mycmd,])
    else:
      cleanFileIDsList(fileIdSelection, [myarg,])
  return fileIdSelection

def validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters, drive=None):
  if fileIdSelection[u'dict']:
    cleanFileIDsList(fileIdSelection, fileIdSelection[u'dict'][user])
  if not drive:
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      return (user, None, 0)
  else:
    user = convertUserUIDtoEmailAddress(user)
  if parameters[DFA_PARENTQUERY]:
    more_parents = doDriveSearch(drive, user, i, count, query=parameters[DFA_PARENTQUERY])
    if more_parents == None:
      setSysExitRC(NO_ENTITIES_FOUND)
      return (user, None, 0)
    body.setdefault(u'parents', [])
    for a_parent in more_parents:
      body[u'parents'].append({u'id': a_parent})
  if fileIdSelection[u'query']:
    fileIdSelection[u'fileIds'] = doDriveSearch(drive, user, i, count, query=fileIdSelection[u'query'])
    if fileIdSelection[u'fileIds'] == None:
      setSysExitRC(NO_ENTITIES_FOUND)
      return (user, None, 0)
  elif fileIdSelection[u'root']:
    try:
      rootFolderId = callGAPI(drive.about(), u'get',
                              throw_reasons=GAPI_DRIVE_THROW_REASONS,
                              fields=u'rootFolderId')[u'rootFolderId']
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
      return (user, None, 0)
    for j in fileIdSelection[u'root']:
      fileIdSelection[u'fileIds'][j] = rootFolderId
  l = len(fileIdSelection[u'fileIds'])
  if l == 0:
    setSysExitRC(NO_ENTITIES_FOUND)
  return (user, drive, l)

DRIVEFILE_LABEL_CHOICES_MAP = {
  u'restricted': u'restricted',
  u'restrict': u'restricted',
  u'starred': u'starred',
  u'star': u'starred',
  u'trashed': u'trashed',
  u'trash': u'trashed',
  u'viewed': u'viewed',
  u'view': u'viewed',
  }

MIMETYPE_CHOICES_MAP = {
  u'gdoc': MIMETYPE_GA_DOCUMENT,
  u'gdocument': MIMETYPE_GA_DOCUMENT,
  u'gdrawing': MIMETYPE_GA_DRAWING,
  u'gfolder': MIMETYPE_GA_FOLDER,
  u'gdirectory': MIMETYPE_GA_FOLDER,
  u'gform': MIMETYPE_GA_FORM,
  u'gfusion': MIMETYPE_GA_FUSIONTABLE,
  u'gpresentation': MIMETYPE_GA_PRESENTATION,
  u'gscript': MIMETYPE_GA_SCRIPT,
  u'gsite': MIMETYPE_GA_SITES,
  u'gsheet': MIMETYPE_GA_SPREADSHEET,
  u'gspreadsheet': MIMETYPE_GA_SPREADSHEET,
  }

DFA_CONVERT = u'convert'
DFA_LOCALFILEPATH = u'localFilepath'
DFA_LOCALFILENAME = u'localFilename'
DFA_LOCALMIMETYPE = u'localMimeType'
DFA_OCR = u'ocr'
DFA_OCRLANGUAGE = u'ocrLanguage'
DFA_PARENTQUERY = u'parentQuery'

def initializeDriveFileAttributes():
  return ({}, {DFA_LOCALFILEPATH: None, DFA_LOCALFILENAME: None, DFA_LOCALMIMETYPE: None, DFA_CONVERT: None, DFA_OCR: None, DFA_OCRLANGUAGE: None, DFA_PARENTQUERY: None})

def getDriveFileAttribute(body, parameters, myarg, update):
  if myarg == u'localfile':
    parameters[DFA_LOCALFILEPATH] = getString(OB_FILE_NAME)
    parameters[DFA_LOCALFILENAME] = os.path.basename(parameters[DFA_LOCALFILEPATH])
    body.setdefault(DRIVE_FILE_NAME, parameters[DFA_LOCALFILENAME])
    body[u'mimeType'] = mimetypes.guess_type(parameters[DFA_LOCALFILEPATH])[0]
    if body[u'mimeType'] == None:
      body[u'mimeType'] = u'application/octet-stream'
    parameters[DFA_LOCALMIMETYPE] = body[u'mimeType']
  elif myarg == u'convert':
    parameters[DFA_CONVERT] = True
  elif myarg == u'ocr':
    parameters[DFA_OCR] = True
  elif myarg == u'ocrlanguage':
    parameters[DFA_OCRLANGUAGE] = getChoice(LANGUAGE_CODES_MAP, mapChoice=True)
  elif myarg in DRIVEFILE_LABEL_CHOICES_MAP:
    body.setdefault(u'labels', {})
    if update:
      body[u'labels'][DRIVEFILE_LABEL_CHOICES_MAP[myarg]] = getBoolean()
    else:
      body[u'labels'][DRIVEFILE_LABEL_CHOICES_MAP[myarg]] = True
  elif myarg in [u'lastviewedbyme', u'lastviewedbyuser', u'lastviewedbymedate', u'lastviewedbymetime']:
    body[u'lastViewedByMeDate'] = getFullTime()
  elif myarg in [u'modifieddate', u'modifiedtime']:
    body[u'modifiedDate'] = getFullTime()
  elif myarg == u'description':
    body[u'description'] = getString(OB_STRING)
  elif myarg == u'mimetype':
    body[u'mimeType'] = getChoice(MIMETYPE_CHOICES_MAP, mapChoice=True)
  elif myarg == u'parentid':
    body.setdefault(u'parents', [])
    body[u'parents'].append({u'id': getString(OB_DRIVE_FOLDER_ID)})
  elif myarg == u'parentname':
    parameters[DFA_PARENTQUERY] = u"'me' in owners and mimeType = '{0}' and {1} = '{2}'".format(MIMETYPE_GA_FOLDER, DRIVE_FILE_NAME, getString(OB_DRIVE_FOLDER_NAME))
  elif myarg == u'writerscantshare':
    body[u'writersCanShare'] = False
  else:
    unknownArgumentExit()

# gam <UserTypeEntity> print|show driveactivity [todrive] [fileid <DriveFileID>] [folderid <DriveFolderID>]
def printDriveActivity(users):
  drive_ancestorId = u'root'
  drive_fileId = None
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'user.name', u'user.permissionId', u'target.id', u'target.name', u'target.mimeType'])
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'fileid':
      drive_fileId = getString(OB_DRIVE_FILE_ID)
      drive_ancestorId = None
    elif myarg == u'folderid':
      drive_ancestorId = getString(OB_DRIVE_FOLDER_ID)
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, activity = buildActivityGAPIObject(user)
    if not activity:
      continue
    try:
      printGettingAllEntityItemsForWhom(EN_ACTIVITY, user, i, count)
      page_message = getPageMessageForWhom(noNL=True)
      feed = callGAPIpages(activity.activities(), u'list', u'activities',
                           page_message=page_message,
                           throw_reasons=GAPI_ACTIVITY_THROW_REASONS,
                           source=u'drive.google.com', userId=u'me',
                           drive_ancestorId=drive_ancestorId, groupingStrategy=u'none',
                           drive_fileId=drive_fileId, pageSize=GC_Values[GC_ACTIVITY_MAX_RESULTS])
      for item in feed:
        addRowTitlesToCSVfile(flattenJSON(item[u'combinedEvent']), csvRows, titles)
    except GAPI_serviceNotAvailable:
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
  writeCSVfile(csvRows, titles, u'Drive Activity', todrive)

# gam <UserTypeEntity> print|show drivesettings [todrive]
def printDriveSettings(users):
  todrive = False
  titles, csvRows = initializeTitlesCSVfile([u'email',])
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    else:
      unknownArgumentExit()
  dont_show = [u'kind', u'etag', u'selfLink', u'additionalRoleInfo', u'exportFormats', u'features',
               u'importFormats', u'isCurrentAppInstalled', u'maxUploadSizes', u'user']
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    printGettingEntityItemForWhom(EN_DRIVE_SETTINGS, user, i, count)
    try:
      feed = callGAPI(drive.about(), u'get',
                      throw_reasons=GAPI_DRIVE_THROW_REASONS)
      if feed:
        row = {u'email': user}
        for setting in feed:
          if setting in dont_show:
            continue
          if setting == u'quotaBytesByService':
            for subsetting in feed[setting]:
              my_name = subsetting[u'serviceName']
              row[my_name] = formatFileSize(int(subsetting[u'bytesUsed']))
              if my_name not in titles[u'set']:
                addTitleToCSVfile(my_name, titles)
          else:
            row[setting] = feed[setting]
            if setting not in titles[u'set']:
              addTitleToCSVfile(setting, titles)
        csvRows.append(row)
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
  writeCSVfile(csvRows, titles, u'User Drive Settings', todrive)

def getFilePath(drive, initialResult):
  entityType = [EN_DRIVE_FOLDER_ID, EN_DRIVE_FILE_ID][initialResult[u'mimeType'] != MIMETYPE_GA_FOLDER]
  path = []
  name = initialResult[DRIVE_FILE_NAME]
  parents = initialResult[u'parents']
  while True:
    path.append(name)
    if len(parents) == 0:
      path.reverse()
      return (entityType, os.path.join(*path))
    try:
      result = callGAPI(drive.files(), u'get',
                        throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                        fileId=parents[0][u'id'], fields=u'{0},parents(id)'.format(DRIVE_FILE_NAME))
      name = result[DRIVE_FILE_NAME]
      parents = result[u'parents']
    except (GAPI_fileNotFound, GAPI_serviceNotAvailable, GAPI_authError):
      return (entityType, PHRASE_PATH_NOT_AVAILABLE)

DRIVEFILE_FIELDS_CHOICES_MAP = {
  u'alternatelink': DRIVE_FILE_VIEW_LINK,
  u'appdatacontents': u'appDataContents',
  u'cancomment': u'canComment',
  u'canreadrevisions': u'canReadRevisions',
  u'copyable': u'copyable',
  u'createddate': u'createdDate',
  u'createdtime': u'createdDate',
  u'description': u'description',
  u'editable': u'editable',
  u'explicitlytrashed': u'explicitlyTrashed',
  u'fileextension': u'fileExtension',
  u'filesize': u'fileSize',
  u'foldercolorrgb': u'folderColorRgb',
  u'fullfileextension': u'fullFileExtension',
  u'headrevisionid': u'headRevisionId',
  u'iconlink': u'iconLink',
  u'id': u'id',
  u'lastmodifyinguser': u'lastModifyingUser',
  u'lastmodifyingusername': u'lastModifyingUserName',
  u'lastviewedbyme': u'lastViewedByMeDate',
  u'lastviewedbymedate': u'lastViewedByMeDate',
  u'lastviewedbymetime': u'lastViewedByMeDate',
  u'lastviewedbyuser': u'lastViewedByMeDate',
  u'md5': u'md5Checksum',
  u'md5checksum': u'md5Checksum',
  u'md5sum': u'md5Checksum',
  u'mime': u'mimeType',
  u'mimetype': u'mimeType',
  u'modifiedbyme': u'modifiedByMeDate',
  u'modifiedbymedate': u'modifiedByMeDate',
  u'modifiedbymetime': u'modifiedByMeDate',
  u'modifiedbyuser': u'modifiedByMeDate',
  u'modifieddate': u'modifiedDate',
  u'modifiedtime': u'modifiedDate',
  u'name': DRIVE_FILE_NAME,
  u'originalfilename': u'originalFilename',
  u'ownedbyme': u'ownedByMe',
  u'ownernames': u'ownerNames',
  u'owners': u'owners',
  u'parents': u'parents',
  u'permissions': u'permissions',
  u'quotabytesused': u'quotaBytesUsed',
  u'quotaused': u'quotaBytesUsed',
  u'shareable': u'shareable',
  u'shared': u'shared',
  u'sharedwithmedate': u'sharedWithMeDate',
  u'sharedwithmetime': u'sharedWithMeDate',
  u'sharinguser': u'sharingUser',
  u'spaces': u'spaces',
  u'thumbnaillink': u'thumbnailLink',
  u'title': DRIVE_FILE_NAME,
  u'userpermission': u'userPermission',
  u'version': u'version',
  u'viewedbyme': u'labels(viewed)',
  u'viewedbymedate': u'lastViewedByMeDate',
  u'viewedbymetime': u'lastViewedByMeDate',
  u'viewerscancopycontent': u'labels(restricted)',
  u'webcontentlink': u'webContentLink',
  u'webviewlink': DRIVE_FILE_VIEW_LINK,
  u'writerscanshare': u'writersCanShare',
  }

# gam <UserTypeEntity> show fileinfo <DriveFileEntity> [filepath] [allfields|<DriveFieldName>*]
def showDriveFileInfo(users):
  filepath = False
  fieldsList = []
  labelsList = []
  fileIdSelection = getDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'filepath':
      filepath = True
    elif myarg == u'allfields':
      fieldsList = []
    elif myarg in DRIVEFILE_FIELDS_CHOICES_MAP:
      fieldsList.append(DRIVEFILE_FIELDS_CHOICES_MAP[myarg])
    elif myarg in DRIVEFILE_LABEL_CHOICES_MAP:
      labelsList.append(DRIVEFILE_LABEL_CHOICES_MAP[myarg])
    else:
      unknownArgumentExit()
  if fieldsList or labelsList:
    fieldsList.append(DRIVE_FILE_NAME)
    fields = u','.join(set(fieldsList))
    if labelsList:
      fields += u',labels({0})'.format(u','.join(set(labelsList)))
  else:
    fields = u'*'
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FILE_OR_FOLDER, i, count)
    if jcount == 0:
      continue
    incrementIndentLevel()
    j = 0
    for fileId in fileIdSelection[u'fileIds']:
      j += 1
      try:
        result = callGAPI(drive.files(), u'get',
                          throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                          fileId=fileId, fields=fields)
        printEntityName(EN_DRIVE_FILE_OR_FOLDER, result[DRIVE_FILE_NAME], j, jcount)
        incrementIndentLevel()
        if filepath:
          _, path = getFilePath(drive, result)
          printKeyValueList([u'path', path])
        showJSON(None, result)
        decrementIndentLevel()
      except GAPI_fileNotFound:
        entityItemValueActionFailedWarning(EN_USER, user, EN_DRIVE_FILE_OR_FOLDER_ID, fileId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
        break
    decrementIndentLevel()

# gam <UserTypeEntity> show filerevisions <DriveFileEntity>
def showDriveFileRevisions(users):
  fileIdSelection = getDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FILE_OR_FOLDER, i, count)
    if jcount == 0:
      continue
    incrementIndentLevel()
    j = 0
    for fileId in fileIdSelection[u'fileIds']:
      j += 1
      try:
        result = callGAPI(drive.revisions(), u'list',
                          throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                          fileId=fileId, fields=DRIVE_REVISIONS_LIST)
        printEntityName(EN_DRIVE_FILE_OR_FOLDER_ID, fileId, j, jcount)
        incrementIndentLevel()
        for revision in result[DRIVE_REVISIONS_LIST]:
          printEntityName(EN_REVISION_ID, revision[u'id'])
          incrementIndentLevel()
          showJSON(None, revision, skip_objects=[u'id',])
          decrementIndentLevel()
        decrementIndentLevel()
      except GAPI_fileNotFound:
        entityItemValueActionFailedWarning(EN_USER, user, EN_DRIVE_FILE_OR_FOLDER_ID, fileId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
        break
    decrementIndentLevel()

DRIVEFILE_ORDERBY_CHOICES_MAP = {
  u'createddate': u'createdDate',
  u'createdtime': u'createdDate',
  u'folder': u'folder',
  u'lastviewedbyme': u'lastViewedByMeDate',
  u'lastviewedbymedate': u'lastViewedByMeDate',
  u'lastviewedbymetime': u'lastViewedByMeDate',
  u'lastviewedbyuser': u'lastViewedByMeDate',
  u'modifiedbyme': u'modifiedByMeDate',
  u'modifiedbymedate': u'modifiedByMeDate',
  u'modifiedbymetime': u'modifiedByMeDate',
  u'modifiedbyuser': u'modifiedByMeDate',
  u'modifieddate': u'modifiedDate',
  u'modifiedtime': u'modifiedDate',
  u'name': DRIVE_FILE_NAME,
  u'quotabytesused': u'quotaBytesUsed',
  u'quotaused': u'quotaBytesUsed',
  u'recency': u'recency',
  u'sharedwithmedate': u'sharedWithMeDate',
  u'sharedwithmetime': u'sharedWithMeDate',
  u'starred': u'starred',
  u'title': DRIVE_FILE_NAME,
  u'viewedbymedate': u'lastViewedByMeDate',
  u'viewedbymetime': u'lastViewedByMeDate',
  }

# gam <UserTypeEntity> print|show filelist [todrive] [query <QueryDriveFile>] [fullquery <QueryDriveFile>] [allfields|<DriveFieldName>*] (orderby <DriveOrderByFieldName> [ascending|descending])*
def printDriveFileList(users):
  allfields = filepath = todrive = False
  fieldsList = []
  fieldsTitles = {}
  labelsList = []
  orderByList = []
  titles, csvRows = initializeTitlesCSVfile([u'Owner',])
  query = u"'me' in owners"
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'todrive':
      todrive = True
    elif myarg == u'filepath':
      filepath = True
      if fieldsList:
        fieldsList.extend([u'mimeType', u'parents'])
      addTitlesToCSVfile([u'path',], titles)
    elif myarg == u'orderby':
      fieldName = getChoice(DRIVEFILE_ORDERBY_CHOICES_MAP, mapChoice=True)
      if getChoice(SORTORDER_CHOICES_MAP, defaultChoice=None, mapChoice=True) != u'DESCENDING':
        orderByList.append(fieldName)
      else:
        orderByList.append(u'{0} desc'.format(fieldName))
    elif myarg == u'query':
      query += u' and {0}'.format(getString(OB_QUERY))
    elif myarg == u'fullquery':
      query = getString(OB_QUERY)
    elif myarg == u'allfields':
      fieldsList = []
      allfields = True
    elif myarg in DRIVEFILE_FIELDS_CHOICES_MAP:
      addFieldToCSVfile(myarg, {myarg: [DRIVEFILE_FIELDS_CHOICES_MAP[myarg]]}, fieldsList, fieldsTitles, titles)
    elif myarg in DRIVEFILE_LABEL_CHOICES_MAP:
      addFieldToCSVfile(myarg, {myarg: [DRIVEFILE_LABEL_CHOICES_MAP[myarg]]}, labelsList, fieldsTitles, titles)
    else:
      unknownArgumentExit()
  if fieldsList or labelsList:
    fields = u'nextPageToken,{0}('.format(DRIVE_FILES_LIST)
    if fieldsList:
      fields += u','.join(set(fieldsList))
      if labelsList:
        fields += u','
    if labelsList:
      fields += u'labels({0})'.format(u','.join(set(labelsList)))
    fields += u')'
  elif not allfields:
    for field in [u'name', u'alternatelink']:
      addFieldToCSVfile(field, {field: [DRIVEFILE_FIELDS_CHOICES_MAP[field]]}, fieldsList, fieldsTitles, titles)
    fields = u'nextPageToken,{0}({1})'.format(DRIVE_FILES_LIST, u','.join(set(fieldsList)))
  else:
    fields = u'*'
  if orderByList:
    orderBy = u','.join(orderByList)
  else:
    orderBy = None
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    try:
      printGettingAllEntityItemsForWhom(EN_DRIVE_FILE_OR_FOLDER, user, i, count, qualifier=queryQualifier(query))
      page_message = getPageMessageForWhom()
      feed = callGAPIpages(drive.files(), u'list', DRIVE_FILES_LIST,
                           page_message=page_message,
                           throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_INVALID_QUERY, GAPI_FILE_NOT_FOUND],
                           q=query, orderBy=orderBy, fields=fields, maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
      for f_file in feed:
        a_file = {u'Owner': user}
        if filepath:
          _, path = getFilePath(drive, f_file)
          a_file[u'path'] = path
        for attrib in f_file:
          if attrib in [u'kind', u'etag']:
            continue
          if not isinstance(f_file[attrib], dict):
            if isinstance(f_file[attrib], list):
              if f_file[attrib]:
                if isinstance(f_file[attrib][0], (str, unicode, int, bool)):
                  a_file[attrib] = u' '.join(f_file[attrib])
                  if attrib not in titles[u'set']:
                    addTitleToCSVfile(attrib, titles)
                else:
                  for j, l_attrib in enumerate(f_file[attrib]):
                    for list_attrib in l_attrib:
                      if list_attrib in [u'kind', u'etag', u'selfLink']:
                        continue
                      x_attrib = u'{0}.{1}.{2}'.format(attrib, j, list_attrib)
                      a_file[x_attrib] = l_attrib[list_attrib]
                      if x_attrib not in titles[u'set']:
                        addTitleToCSVfile(x_attrib, titles)
            elif isinstance(f_file[attrib], (str, unicode, int, bool)):
              a_file[attrib] = f_file[attrib]
              if attrib not in titles[u'set']:
                addTitleToCSVfile(attrib, titles)
            else:
              sys.stderr.write(u'{0}: {1}, Attribute: {2}, Unknown type: {3}\n'.format(singularEntityName(EN_DRIVE_FILE_ID), f_file[u'id'], attrib, type(f_file[attrib])))
          elif attrib == u'labels':
            for dict_attrib in f_file[attrib]:
              a_file[dict_attrib] = f_file[attrib][dict_attrib]
              if dict_attrib not in titles[u'set']:
                addTitleToCSVfile(dict_attrib, titles)
          else:
            for dict_attrib in f_file[attrib]:
              if dict_attrib in [u'kind', u'etag']:
                continue
              x_attrib = u'{0}.{1}'.format(attrib, dict_attrib)
              a_file[x_attrib] = f_file[attrib][dict_attrib]
              if x_attrib not in titles[u'set']:
                addTitleToCSVfile(x_attrib, titles)
        csvRows.append(a_file)
    except GAPI_invalidQuery:
      entityItemValueActionFailedWarning(EN_USER, user, EN_DRIVE_FILE, PHRASE_LIST, invalidQuery(query), i, count)
      break
    except GAPI_fileNotFound:
      printGettingEntityItemsForWhomDoneInfo(0)
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
  if allfields:
    sortCSVTitles([u'Owner', u'id', DRIVE_FILE_NAME], titles)
  writeCSVfile(csvRows, titles,
               u'{0} {1} Drive Files'.format(CL_argv[GM_Globals[GM_ENTITY_CL_INDEX]],
                                             CL_argv[GM_Globals[GM_ENTITY_CL_INDEX]+1]),
               todrive)

# gam <UserTypeEntity> show filepath <DriveFileEntity>
def showDriveFilePath(users):
  fileIdSelection = getDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FILE_OR_FOLDER, i, count)
    if jcount == 0:
      continue
    incrementIndentLevel()
    j = 0
    for fileId in fileIdSelection[u'fileIds']:
      j += 1
      try:
        result = callGAPI(drive.files(), u'get',
                          throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                          fileId=fileId, fields=u'{0},mimeType,parents(id)'.format(DRIVE_FILE_NAME))
        entityType, path = getFilePath(drive, result)
        printEntityItemValue(entityType, fileId, EN_DRIVE_PATH, path, j, jcount)
      except GAPI_fileNotFound:
        entityItemValueActionFailedWarning(EN_USER, user, EN_DRIVE_FILE_OR_FOLDER_ID, fileId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
        break
    decrementIndentLevel()

# gam <UserTypeEntity> show filetree [<DriveFileEntity>] (orderby <DriveOrderByFieldName> [ascending|descending])*
def showDriveFileTree(users):
  def _printDriveFolderContents(feed, folderId):
    for f_file in feed:
      for parent in f_file[u'parents']:
        if folderId == parent[u'id']:
          printKeyValueList([f_file[DRIVE_FILE_NAME]])
          if f_file[u'mimeType'] == MIMETYPE_GA_FOLDER:
            incrementIndentLevel()
            _printDriveFolderContents(feed, f_file[u'id'])
            decrementIndentLevel()
          break

  fileIdSelection = getDriveFileEntity(default=[u'root'], ignore=[u'orderby',])
  body, parameters = initializeDriveFileAttributes()
  orderByList = []
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'orderby':
      fieldName = getChoice(DRIVEFILE_ORDERBY_CHOICES_MAP, mapChoice=True)
      if getChoice(SORTORDER_CHOICES_MAP, defaultChoice=None, mapChoice=True) != u'DESCENDING':
        orderByList.append(fieldName)
      else:
        orderByList.append(u'{0} desc'.format(fieldName))
    else:
      unknownArgumentExit()
  if not fileIdSelection[u'fileIds'] and not fileIdSelection[u'query'] and not fileIdSelection[u'dict']:
    cleanFileIDsList(fileIdSelection, [u'root',])
  if orderByList:
    orderBy = u','.join(orderByList)
  else:
    orderBy = None
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FOLDER, i, count)
    if jcount == 0:
      continue
    try:
      printGettingAllEntityItemsForWhom(EN_DRIVE_FILE_OR_FOLDER, user, i, count)
      page_message = getPageMessageForWhom()
      feed = callGAPIpages(drive.files(), u'list', DRIVE_FILES_LIST,
                           page_message=page_message,
                           throw_reasons=GAPI_DRIVE_THROW_REASONS,
                           orderBy=orderBy, fields=u'nextPageToken,{0}(id,{1},mimeType,parents(id))'.format(DRIVE_FILES_LIST, DRIVE_FILE_NAME), maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
      j = 0
      for fileId in fileIdSelection[u'fileIds']:
        j += 1
        try:
          result = callGAPI(drive.files(), u'get',
                            throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                            fileId=fileId, fields=DRIVE_FILE_NAME)
          printEntityName(EN_DRIVE_FILE_OR_FOLDER, result[DRIVE_FILE_NAME], j, jcount)
          incrementIndentLevel()
          _printDriveFolderContents(feed, fileId)
          decrementIndentLevel()
        except GAPI_fileNotFound:
          entityItemValueActionFailedWarning(EN_USER, user, EN_DRIVE_FILE_OR_FOLDER_ID, fileId, PHRASE_DOES_NOT_EXIST, j, jcount)
        except (GAPI_serviceNotAvailable, GAPI_authError):
          entityServiceNotApplicableWarning(EN_USER, user, i, count)
          break
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> add drivefile [drivefilename <DriveFileName>] [<DriveFileAttributes>]
def addDriveFile(users):
  media_body = None
  fileIdSelection = initDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'drivefilename':
      body[DRIVE_FILE_NAME] = getString(OB_DRIVE_FILE_NAME)
    else:
      getDriveFileAttribute(body, parameters, myarg, False)
  setActionName(AC_CREATE)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, _ = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    if parameters[DFA_LOCALFILEPATH]:
      media_body = googleapiclient.http.MediaFileUpload(parameters[DFA_LOCALFILEPATH], mimetype=parameters[DFA_LOCALMIMETYPE], resumable=True)
    try:
      result = callGAPI(drive.files(), DRIVE_CREATE_FILE,
                        throw_reasons=GAPI_DRIVE_THROW_REASONS,
                        convert=parameters[DFA_CONVERT], ocr=parameters[DFA_OCR], ocrLanguage=parameters[DFA_OCRLANGUAGE],
                        media_body=media_body, body=body, fields=u'id,{0},mimeType'.format(DRIVE_FILE_NAME))
      if parameters[DFA_LOCALFILENAME]:
        entityItemValueModifierNewValueActionPerformed(EN_USER, user, EN_DRIVE_FILE, result[DRIVE_FILE_NAME], AC_MODIFIER_WITH_CONTENT_FROM, parameters[DFA_LOCALFILENAME], i, count)
      elif result[u'mimeType'] != MIMETYPE_GA_FOLDER:
        entityItemValueActionPerformed(EN_USER, user, EN_DRIVE_FILE, result[DRIVE_FILE_NAME], i, count)
      else:
        entityItemValueActionPerformed(EN_USER, user, EN_DRIVE_FOLDER, result[DRIVE_FILE_NAME], i, count)
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> update drivefile <DriveFileEntity> [copy] [newfilename <DriveFileName>] [<DriveFileUpdateAttributes>]
def updateDriveFile(users):
  fileIdSelection = getDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  media_body = None
  operation = u'update'
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'copy':
      operation = u'copy'
    elif myarg == u'newfilename':
      body[DRIVE_FILE_NAME] = getString(OB_DRIVE_FILE_NAME)
    else:
      getDriveFileAttribute(body, parameters, myarg, True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    if operation == u'update':
      setActionName(AC_UPDATE)
      if parameters[DFA_LOCALFILEPATH]:
        media_body = googleapiclient.http.MediaFileUpload(parameters[DFA_LOCALFILEPATH], mimetype=parameters[DFA_LOCALMIMETYPE], resumable=True)
      entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FILE_OR_FOLDER, i, count)
      if jcount == 0:
        continue
      incrementIndentLevel()
      j = 0
      for fileId in fileIdSelection[u'fileIds']:
        j += 1
        try:
          if media_body:
            result = callGAPI(drive.files(), DRIVE_UPDATE_FILE,
                              throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                              fileId=fileId, convert=parameters[DFA_CONVERT], ocr=parameters[DFA_OCR], ocrLanguage=parameters[DFA_OCRLANGUAGE],
                              media_body=media_body, body=body, fields=u'id,{0},mimeType'.format(DRIVE_FILE_NAME))
            entityItemValueModifierNewValueActionPerformed(EN_USER, user, EN_DRIVE_FILE, result[DRIVE_FILE_NAME], AC_MODIFIER_WITH_CONTENT_FROM, parameters[DFA_LOCALFILENAME], j, jcount)
          else:
            result = callGAPI(drive.files(), DRIVE_PATCH_FILE,
                              throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                              fileId=fileId, convert=parameters[DFA_CONVERT], ocr=parameters[DFA_OCR], ocrLanguage=parameters[DFA_OCRLANGUAGE],
                              body=body, fields=u'id,{0},mimeType'.format(DRIVE_FILE_NAME))
            entityItemValueActionPerformed(EN_USER, user, [EN_DRIVE_FOLDER, EN_DRIVE_FILE][result[u'mimeType'] != MIMETYPE_GA_FOLDER], result[DRIVE_FILE_NAME], j, jcount)
        except GAPI_fileNotFound:
          entityItemValueActionFailedWarning(EN_USER, user, EN_DRIVE_FILE_OR_FOLDER_ID, fileId, PHRASE_DOES_NOT_EXIST, j, jcount)
        except (GAPI_serviceNotAvailable, GAPI_authError):
          entityServiceNotApplicableWarning(EN_USER, user, i, count)
          break
      decrementIndentLevel()
    else:
      setActionName(AC_COPY)
      entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FILE_OR_FOLDER, i, count)
      if jcount == 0:
        continue
      incrementIndentLevel()
      j = 0
      for fileId in fileIdSelection[u'fileIds']:
        j += 1
        try:
          result = callGAPI(drive.files(), u'copy',
                            throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                            fileId=fileId, convert=parameters[DFA_CONVERT], ocr=parameters[DFA_OCR], ocrLanguage=parameters[DFA_OCRLANGUAGE],
                            body=body, fields=u'id,{0}'.format(DRIVE_FILE_NAME))
          entityItemValueModifierNewValueInfoActionPerformed(EN_USER, user, EN_DRIVE_FILE, fileId, AC_MODIFIER_TO, result[DRIVE_FILE_NAME], singularEntityName(EN_DRIVE_FILE_ID), result[u'id'], j, jcount)
        except GAPI_fileNotFound:
          entityItemValueActionFailedWarning(EN_USER, user, EN_DRIVE_FILE, fileId, PHRASE_DOES_NOT_EXIST, j, jcount)
        except (GAPI_serviceNotAvailable, GAPI_authError):
          entityServiceNotApplicableWarning(EN_USER, user, i, count)
          break
      decrementIndentLevel()

# gam <UserTypeEntity> copy drivefile <DriveFileEntity> [newfilename <DriveFileName>] [recursive] [parentid <DriveFolderID>] [parentname <DriveFolderName>]
def copyDriveFile(users):
  def _recursiveFolderCopy(drive, user, i, count, folderId, folderTitle, newFolderTitle, parentId):
    body = {DRIVE_FILE_NAME: newFolderTitle, u'mimeType': MIMETYPE_GA_FOLDER, u'parents': []}
    if parentId:
      body[u'parents'].append({u'id': parentId})
    result = callGAPI(drive.files(), DRIVE_CREATE_FILE, body=body, fields=u'id')
    newFolderId = result[u'id']
    setActionName(AC_CREATE)
    entityItemValueItemValueActionPerformed(EN_USER, user, EN_DRIVE_FOLDER, newFolderTitle, EN_DRIVE_FOLDER_ID, newFolderId, i, count)
    setActionName(AC_COPY)
    source_children = callGAPI(drive.children(), u'list', folderId=folderId, fields=u'{0}(id)'.format(DRIVE_FILES_LIST))
    jcount = len(source_children[DRIVE_FILES_LIST]) if (source_children and (DRIVE_FILES_LIST in source_children)) else 0
    if jcount > 0:
      incrementIndentLevel()
      j = 0
      for child in source_children[DRIVE_FILES_LIST]:
        j += 1
        metadata = callGAPI(drive.files(), u'get', fileId=child[u'id'], fields=u'id,{0},mimeType'.format(DRIVE_FILE_NAME))
        if metadata[u'mimeType'] == MIMETYPE_GA_FOLDER:
          _recursiveFolderCopy(drive, user, j, jcount, child[u'id'], metadata[DRIVE_FILE_NAME], metadata[DRIVE_FILE_NAME], newFolderId)
        else:
          fileId = metadata[u'id']
          body = {DRIVE_FILE_NAME: metadata[DRIVE_FILE_NAME], u'parents': []}
          body[u'parents'].append({u'id': newFolderId})
          result = callGAPI(drive.files(), u'copy', fileId=fileId, body=body, fields=u'id,{0}'.format(DRIVE_FILE_NAME))
          entityItemValueModifierNewValueInfoActionPerformed(EN_USER, user, EN_DRIVE_FILE, metadata[DRIVE_FILE_NAME], AC_MODIFIER_TO, result[DRIVE_FILE_NAME], singularEntityName(EN_DRIVE_FILE_ID), result[u'id'], j, jcount)
      decrementIndentLevel()
      entityItemValueModifierNewValueInfoActionPerformed(EN_USER, user, EN_DRIVE_FOLDER, folderTitle, AC_MODIFIER_TO, newFolderTitle, singularEntityName(EN_DRIVE_FOLDER_ID), newFolderId, i, count)

  fileIdSelection = getDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  parentid = newfilename = None
  recursive = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'newfilename':
      newfilename = getString(OB_DRIVE_FILE_NAME)
      body[DRIVE_FILE_NAME] = newfilename
    elif myarg == u'recursive':
      recursive = True
    elif myarg == u'parentid':
      body.setdefault(u'parents', [])
      body[u'parents'].append({u'id': getString(OB_DRIVE_FILE_ID)})
    elif myarg == u'parentname':
      parameters[DFA_PARENTQUERY] = u"'me' in owners and mimeType = '{0}' and {1} = '{2}'".format(MIMETYPE_GA_FOLDER, DRIVE_FILE_NAME, getString(OB_DRIVE_FOLDER_NAME))
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FILE_OR_FOLDER, i, count)
    if jcount == 0:
      continue
    incrementIndentLevel()
    j = 0
    for fileId in fileIdSelection[u'fileIds']:
      j += 1
      try:
        metadata = callGAPI(drive.files(), u'get',
                            throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                            fileId=fileId, fields=u'id,{0},mimeType'.format(DRIVE_FILE_NAME))
        if metadata[u'mimeType'] == MIMETYPE_GA_FOLDER:
          if recursive:
            destFilename = newfilename or u'Copy of {0}'.format(metadata[DRIVE_FILE_NAME])
            _recursiveFolderCopy(drive, user, j, jcount, fileId, metadata[DRIVE_FILE_NAME], destFilename, parentid)
          else:
            entityItemValueActionNotPerformedWarning(EN_USER, user, EN_DRIVE_FOLDER, metadata[DRIVE_FILE_NAME], PHRASE_USE_RECURSIVE_ARGUMENT_TO_COPY_FOLDERS, j, jcount)
        else:
          result = callGAPI(drive.files(), u'copy',
                            throw_reasons=[GAPI_FILE_NOT_FOUND],
                            fileId=fileId, body=body, fields=u'id,{0}'.format(DRIVE_FILE_NAME))
          entityItemValueModifierNewValueInfoActionPerformed(EN_USER, user, EN_DRIVE_FILE, metadata[DRIVE_FILE_NAME], AC_MODIFIER_TO, result[DRIVE_FILE_NAME], singularEntityName(EN_DRIVE_FILE_ID), result[u'id'], j, jcount)
      except GAPI_fileNotFound:
        entityItemValueActionFailedWarning(EN_USER, user, EN_DRIVE_FILE, fileId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
        break
    decrementIndentLevel()
#
DELETE_DRIVEFILE_CHOICES_MAP = {u'purge': u'delete', u'trash': u'trash', u'untrash': u'untrash',}
DELETE_DRIVEFILE_FUNCTION_TO_ACTION_MAP = {u'delete': AC_PURGE, u'trash': AC_TRASH, u'untrash': AC_UNTRASH,}

# gam <UserTypeEntity> purge drivefile <DriveFileEntity>
def purgeDriveFile(users):
  deleteDriveFile(users, u'delete')

# gam <UserTypeEntity> trash drivefile <DriveFileEntity>
def trashDriveFile(users):
  deleteDriveFile(users, u'trash')

# gam <UserTypeEntity> untrash drivefile <DriveFileEntity>
def untrashDriveFile(users):
  deleteDriveFile(users, u'untrash')

# gam <UserTypeEntity> delete|del drivefile <DriveFileEntity> [purge|trash|untrash]
def deleteDriveFile(users, function=None):
  fileIdSelection = getDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  if not function:
    function = getChoice(DELETE_DRIVEFILE_CHOICES_MAP, defaultChoice=u'trash', mapChoice=True)
  checkForExtraneousArguments()
  setActionName(DELETE_DRIVEFILE_FUNCTION_TO_ACTION_MAP[function])
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FILE_OR_FOLDER, i, count)
    if jcount == 0:
      continue
    incrementIndentLevel()
    j = 0
    for fileId in fileIdSelection[u'fileIds']:
      j += 1
      try:
        result = callGAPI(drive.files(), function,
                          throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                          fileId=fileId, fields=DRIVE_FILE_NAME)
        if result and DRIVE_FILE_NAME in result:
          fileName = result[DRIVE_FILE_NAME]
        else:
          fileName = fileId
        entityItemValueActionPerformed(EN_USER, user, EN_DRIVE_FILE_OR_FOLDER, fileName, j, jcount)
      except GAPI_fileNotFound:
        entityItemValueActionFailedWarning(EN_USER, user, EN_DRIVE_FILE_OR_FOLDER_ID, fileId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
        break
    decrementIndentLevel()
#
DOCUMENT_FORMATS_MAP = {
  u'csv': [{u'mime': u'text/csv', u'ext': u'.csv'}],
  u'html': [{u'mime': u'text/html', u'ext': u'.html'}],
  u'txt': [{u'mime': u'text/plain', u'ext': u'.txt'}],
  u'tsv': [{u'mime': u'text/tsv', u'ext': u'.tsv'}],
  u'jpeg': [{u'mime': u'image/jpeg', u'ext': u'.jpeg'}],
  u'jpg': [{u'mime': u'image/jpeg', u'ext': u'.jpg'}],
  u'png': [{u'mime': u'image/png', u'ext': u'.png'}],
  u'svg': [{u'mime': u'image/svg+xml', u'ext': u'.svg'}],
  u'pdf': [{u'mime': u'application/pdf', u'ext': u'.pdf'}],
  u'rtf': [{u'mime': u'application/rtf', u'ext': u'.rtf'}],
  u'zip': [{u'mime': u'application/zip', u'ext': u'.zip'}],
  u'pptx': [{u'mime': u'application/vnd.openxmlformats-officedocument.presentationml.presentation', u'ext': u'.pptx'}],
  u'xlsx': [{u'mime': u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', u'ext': u'.xlsx'}],
  u'docx': [{u'mime': u'application/vnd.openxmlformats-officedocument.wordprocessingml.document', u'ext': u'.docx'}],
  u'ms': [{u'mime': u'application/vnd.openxmlformats-officedocument.presentationml.presentation', u'ext': u'.pptx'},
          {u'mime': u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', u'ext': u'.xlsx'},
          {u'mime': u'application/vnd.openxmlformats-officedocument.wordprocessingml.document', u'ext': u'.docx'}],
  u'microsoft': [{u'mime': u'application/vnd.openxmlformats-officedocument.presentationml.presentation', u'ext': u'.pptx'},
                 {u'mime': u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', u'ext': u'.xlsx'},
                 {u'mime': u'application/vnd.openxmlformats-officedocument.wordprocessingml.document', u'ext': u'.docx'}],
  u'micro$oft': [{u'mime': u'application/vnd.openxmlformats-officedocument.presentationml.presentation', u'ext': u'.pptx'},
                 {u'mime': u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', u'ext': u'.xlsx'},
                 {u'mime': u'application/vnd.openxmlformats-officedocument.wordprocessingml.document', u'ext': u'.docx'}],
  u'odt': [{u'mime': u'application/vnd.oasis.opendocument.text', u'ext': u'.odt'}],
  u'ods': [{u'mime': u'application/x-vnd.oasis.opendocument.spreadsheet', u'ext': u'.ods'}],
  u'openoffice': [{u'mime': u'application/vnd.oasis.opendocument.text', u'ext': u'.odt'},
                  {u'mime': u'application/x-vnd.oasis.opendocument.spreadsheet', u'ext': u'.ods'}],
  }

# gam <UserTypeEntity> get drivefile <DriveFileEntity> [format <FileFormatList>] [targetfolder <FilePath>] [revision <Number>]
def getDriveFile(users):
  fileIdSelection = getDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  revisionId = None
  exportFormatName = u'openoffice'
  exportFormats = DOCUMENT_FORMATS_MAP[exportFormatName]
  targetFolder = GC_Values[GC_DRIVE_DIR]
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'format':
      exportFormatChoices = getString(OB_FORMAT_LIST).replace(u',', u' ').lower().split()
      exportFormats = []
      for exportFormat in exportFormatChoices:
        if exportFormat in DOCUMENT_FORMATS_MAP:
          exportFormats.extend(DOCUMENT_FORMATS_MAP[exportFormat])
        else:
          putArgumentBack()
          invalidChoiceExit(DOCUMENT_FORMATS_MAP)
    elif myarg == u'targetfolder':
      targetFolder = os.path.expanduser(getString(OB_FILE_PATH))
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
    elif myarg == u'revision':
      revisionId = getInteger(minVal=1)
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FILE, i, count)
    if jcount == 0:
      continue
    incrementIndentLevel()
    j = 0
    for fileId in fileIdSelection[u'fileIds']:
      j += 1
      extension = None
      try:
        result = callGAPI(drive.files(), u'get',
                          throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                          fileId=fileId, fields=u'{0},mimeType,fileSize,downloadUrl,exportLinks'.format(DRIVE_FILE_NAME))
        if result[u'mimeType'] == MIMETYPE_GA_FOLDER:
          entityItemValueActionNotPerformedWarning(EN_USER, user, EN_DRIVE_FOLDER, result[DRIVE_FILE_NAME], PHRASE_CAN_NOT_BE_DOWNLOADED, j, jcount)
          continue
        if u'fileSize' in result:
          my_line = [u'Size', formatFileSize(int(result[u'fileSize']))]
        else:
          my_line = [u'Type', u'Google Doc']
        if u'downloadUrl' in result:
          download_url = result[u'downloadUrl']
        elif u'exportLinks' in result:
          for exportFormat in exportFormats:
            if exportFormat[u'mime'] in result[u'exportLinks']:
              download_url = result[u'exportLinks'][exportFormat[u'mime']]
              extension = exportFormat[u'ext']
              break
          else:
            entityItemValueActionNotPerformedWarning(EN_USER, user, EN_DRIVE_FILE, result[DRIVE_FILE_NAME], PHRASE_FORMAT_NOT_AVAILABLE.format(u','.join(exportFormatChoices)), j, jcount)
            continue
        else:
          entityItemValueActionNotPerformedWarning(EN_USER, user, EN_DRIVE_FILE, result[DRIVE_FILE_NAME], PHRASE_FORMAT_NOT_DOWNLOADABLE, j, jcount)
          continue
        safe_file_title = cleanFilename(result[DRIVE_FILE_NAME])
        filename = os.path.join(targetFolder, safe_file_title)
        y = 0
        while True:
          if extension and filename.lower()[-len(extension):] != extension:
            filename += extension
          if not os.path.isfile(filename):
            break
          y += 1
          filename = os.path.join(targetFolder, u'({0})-{1}'.format(y, safe_file_title))
        if revisionId:
          download_url = u'{0}&revision={1}'.format(download_url, revisionId)
        _, content = drive._http.request(download_url)
        status, e = writeFileReturnError(filename, content)
        if status:
          entityItemValueModifierNewValueInfoActionPerformed(EN_USER, user, EN_DRIVE_FILE, result[DRIVE_FILE_NAME], AC_MODIFIER_TO, filename, my_line[0], my_line[1], j, jcount)
        else:
          entityItemValueModifierNewValueActionFailedWarning(EN_USER, user, EN_DRIVE_FILE, result[DRIVE_FILE_NAME], AC_MODIFIER_TO, filename, e.strerror, j, jcount)
      except GAPI_fileNotFound:
        entityItemValueActionFailedWarning(EN_USER, user, EN_DRIVE_FILE_OR_FOLDER_ID, fileId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
        break
    decrementIndentLevel()

# gam <UserTypeEntity> transfer drive <UserItem> [keepuser]
def transferDriveFiles(users):
  target_user = getEmailAddress()
  remove_source_user = True
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'keepuser':
      remove_source_user = False
    else:
      unknownArgumentExit()
  source_query = u"'me' in owners and trashed = false"
  target_query = u"'me' in owners and mimeType = '{0}'".format(MIMETYPE_GA_FOLDER)
  target_user, target_drive = buildDriveGAPIObject(target_user)
  if not target_drive:
    return
  try:
    target_about = callGAPI(target_drive.about(), u'get',
                            throw_reasons=GAPI_DRIVE_THROW_REASONS,
                            fields=u'quotaBytesTotal,quotaBytesUsed')
    target_drive_free = int(target_about[u'quotaBytesTotal']) - int(target_about[u'quotaBytesUsed'])
  except (GAPI_serviceNotAvailable, GAPI_authError):
    entityServiceNotApplicableWarning(EN_TARGET_USER, target_user)
    return
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, source_drive = buildDriveGAPIObject(user)
    if not source_drive:
      continue
    try:
      source_about = callGAPI(source_drive.about(), u'get',
                              throw_reasons=GAPI_DRIVE_THROW_REASONS,
                              fields=u'quotaBytesTotal,quotaBytesUsed,rootFolderId,permissionId')
      source_drive_size = int(source_about[u'quotaBytesUsed'])
      if target_drive_free < source_drive_size:
        printWarningMessage(TARGET_DRIVE_SPACE_ERROR_RC,
                            u'{0} {1}'.format(MESSAGE_NO_TRANSFER_LACK_OF_DISK_SPACE,
                                              formatKeyValueList(u'',
                                                                 [u'Source drive size', formatFileSize(source_drive_size),
                                                                  u'Target drive free', formatFileSize(target_drive_free)],
                                                                 u'')))
        continue
      printKeyValueList([u'Source drive size', formatFileSize(source_drive_size),
                         u'Target drive free', formatFileSize(target_drive_free)])
      target_drive_free = target_drive_free - source_drive_size # prep target_drive_free for next user
      source_root = source_about[u'rootFolderId']
      source_permissionid = source_about[u'permissionId']
      printGettingAllEntityItemsForWhom(EN_DRIVE_FILE_OR_FOLDER, entityTypeName(EN_SOURCE_USER, user), i, count)
      page_message = getPageMessageForWhom()
      source_drive_files = callGAPIpages(source_drive.files(), u'list', DRIVE_FILES_LIST,
                                         page_message=page_message,
                                         q=source_query, fields=u'nextPageToken,{0}(id,parents,mimeType)'.format(DRIVE_FILES_LIST))
      all_source_file_ids = [source_drive_file[u'id'] for source_drive_file in source_drive_files]
      printGettingAllEntityItemsForWhom(EN_DRIVE_FILE_OR_FOLDER, entityTypeName(EN_TARGET_USER, target_user))
      page_message = getPageMessageForWhom()
      target_folders = callGAPIpages(target_drive.files(), u'list', DRIVE_FILES_LIST,
                                     page_message=page_message,
                                     q=target_query, fields=u'nextPageToken,{0}(id,{1})'.format(DRIVE_FILES_LIST, DRIVE_FILE_NAME))
      got_top_folder = False
      all_target_folder_ids = []
      for target_folder in target_folders:
        all_target_folder_ids.append(target_folder[u'id'])
        if (not got_top_folder) and convertUTF8(target_folder[DRIVE_FILE_NAME]) == u'{0} old files'.format(user):
          target_top_folder = target_folder[u'id']
          got_top_folder = True
      if not got_top_folder:
        create_folder = callGAPI(target_drive.files(), DRIVE_CREATE_FILE,
                                 body={DRIVE_FILE_NAME: u'{0} old files'.format(user), u'mimeType': MIMETYPE_GA_FOLDER}, fields=u'id')
        target_top_folder = create_folder[u'id']
      transferred_files = []
      counter = 0
      total_count = len(source_drive_files)
      while True: # we loop thru, skipping files until all of their parents are done
        skipped_files = False
        for drive_file in source_drive_files:
          file_id = drive_file[u'id']
          if file_id in transferred_files:
            continue
          source_parents = drive_file[u'parents']
          skip_file_for_now = False
          for source_parent in source_parents:
            if source_parent[u'id'] not in all_source_file_ids and source_parent[u'id'] not in all_target_folder_ids:
              continue  # means this parent isn't owned by source or target, shouldn't matter
            if source_parent[u'id'] not in transferred_files and source_parent[u'id'] != source_root:
              #printLine(u'skipping {0}'.format(file_id))
              skipped_files = skip_file_for_now = True
              break
          if skip_file_for_now:
            continue
          else:
            transferred_files.append(drive_file[u'id'])
          counter += 1
          body = {u'role': u'owner', u'type': u'user', u'value': target_user}
          callGAPI(source_drive.permissions(), DRIVE_CREATE_PERMISSIONS,
                   soft_errors=True,
                   fileId=file_id, sendNotificationEmails=False, body=body)
          printEntityKVList(EN_USER, user,
                            [singularEntityName(EN_DRIVE_FILE_OR_FOLDER_ID), drive_file[u'id'], u'Changed Owner to', target_user],
                            counter, total_count)
          target_parents = []
          for parent in source_parents:
            if u'isRoot' in parent:
              if parent[u'isRoot']:
                target_parents.append({u'id': target_top_folder})
              else:
                target_parents.append({u'id': parent[u'id']})
          callGAPI(target_drive.files(), DRIVE_PATCH_FILE,
                   soft_errors=True, retry_reasons=[GAPI_NOT_FOUND],
                   fileId=file_id, body={u'parents': target_parents})
          if remove_source_user:
            callGAPI(target_drive.permissions(), u'delete',
                     soft_errors=True,
                     fileId=file_id, permissionId=source_permissionid)
        if not skipped_files:
          break
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

def validateUserGetPermissionId(user):
  _, drive = buildDriveGAPIObject(user)
  if drive:
    try:
      result = callGAPI(drive.permissions(), u'getIdForEmail',
                        throw_reasons=GAPI_DRIVE_THROW_REASONS,
                        email=user, fields=u'id')
      return result[u'id']
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user)
  return None

# gam <UserTypeEntity> transfer ownership <DriveFileEntity> <UserItem> [includetrashed] (orderby <DriveOrderByFieldName> [ascending|descending])*
def transferDriveFileOwnership(users):
  def _transferOwnership(drive, user, i, count, f_file, j, jcount, newOwner, permissionId):
    body = {u'role': u'owner'}
    bodyAdd = {u'role': u'writer', u'type': u'user', u'value': newOwner}
    entityType = [EN_DRIVE_FILE, EN_DRIVE_FOLDER][f_file[u'mimeType'] == MIMETYPE_GA_FOLDER]
    fileDesc = u'{0} ({1})'.format(f_file[DRIVE_FILE_NAME], f_file[u'id'])
    try:
      callGAPI(drive.permissions(), DRIVE_PATCH_PERMISSIONS,
               throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND, GAPI_PERMISSION_NOT_FOUND],
               fileId=f_file[u'id'], permissionId=permissionId, transferOwnership=True, body=body)
      entityItemValueModifierNewValueInfoActionPerformed(EN_USER, user, entityType, fileDesc, AC_MODIFIER_TO, None, singularEntityName(EN_USER), newOwner, j, jcount)
    except GAPI_permissionNotFound:
      # this might happen if target user isn't explicitly in ACL (i.e. shared with anyone)
      try:
        callGAPI(drive.permissions(), DRIVE_CREATE_PERMISSIONS,
                 throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_INVALID_SHARING_REQUEST, GAPI_FILE_NOT_FOUND],
                 fileId=f_file[u'id'], sendNotificationEmails=False, body=bodyAdd)
        callGAPI(drive.permissions(), DRIVE_PATCH_PERMISSIONS,
                 throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND, GAPI_PERMISSION_NOT_FOUND],
                 fileId=f_file[u'id'], permissionId=permissionId, transferOwnership=True, body=body)
        entityItemValueModifierNewValueInfoActionPerformed(EN_USER, user, entityType, fileDesc, AC_MODIFIER_TO, None, singularEntityName(EN_USER), newOwner, j, jcount)
      except GAPI_invalidSharingRequest as e:
        entityItemValueActionFailedWarning(EN_USER, user, entityType, fileDesc, entityTypeNameMessage(EN_PERMISSION_ID, permissionId, e.message), j, jcount)
      except GAPI_permissionNotFound:
        entityDoesNotHaveItemValueSubitemValueWarning(EN_USER, user, entityType, fileDesc, EN_PERMISSION_ID, permissionId, j, jcount)
      except GAPI_fileNotFound:
        entityItemValueActionFailedWarning(EN_USER, user, entityType, fileDesc, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
    except GAPI_fileNotFound:
      entityItemValueActionFailedWarning(EN_USER, user, entityType, fileDesc, PHRASE_DOES_NOT_EXIST, j, jcount)
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

  def _recursiveTransferOwnership(drive, user, i, count, folderId, newOwner, permissionId, feed, trashed):
    incrementIndentLevel()
    for f_file in feed:
      for parent in f_file[u'parents']:
        if folderId == parent[u'id']:
          if trashed or not f_file[u'labels'][u'trashed']:
            if f_file[u'ownedByMe']:
              _transferOwnership(drive, user, i, count, f_file, 0, 0, newOwner, permissionId)
            if f_file[u'mimeType'] == MIMETYPE_GA_FOLDER:
              _recursiveTransferOwnership(drive, user, i, count, f_file[u'id'], newOwner, permissionId, feed, trashed)
          break
    decrementIndentLevel()

  fileIdSelection = getDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  newOwner = getEmailAddress()
  orderByList = []
  trashed = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'includetrashed':
      trashed = True
    elif myarg == u'orderby':
      fieldName = getChoice(DRIVEFILE_ORDERBY_CHOICES_MAP, mapChoice=True)
      if getChoice(SORTORDER_CHOICES_MAP, defaultChoice=None, mapChoice=True) != u'DESCENDING':
        orderByList.append(fieldName)
      else:
        orderByList.append(u'{0} desc'.format(fieldName))
    else:
      unknownArgumentExit()
  setActionName(AC_TRANSFER_OWNERSHIP)
  permissionId = validateUserGetPermissionId(newOwner)
  if not permissionId:
    return
  if orderByList:
    orderBy = u','.join(orderByList)
  else:
    orderBy = None
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FOLDER, i, count)
    if jcount == 0:
      continue
    j = 0
    for fileId in fileIdSelection[u'fileIds']:
      j += 1
      try:
        metadata = callGAPI(drive.files(), u'get',
                            throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                            fileId=fileId, fields=u'id,{0},mimeType,ownedByMe,labels(trashed),parents(id)'.format(DRIVE_FILE_NAME))
        if metadata[u'mimeType'] == MIMETYPE_GA_FOLDER:
          printGettingAllEntityItemsForWhom(EN_DRIVE_FILE_OR_FOLDER, user, i, count)
          page_message = getPageMessageForWhom()
          feed = callGAPIpages(drive.files(), u'list', DRIVE_FILES_LIST,
                               page_message=page_message,
                               throw_reasons=GAPI_DRIVE_THROW_REASONS,
                               orderBy=orderBy, fields=u'nextPageToken,{0}(id,{1},mimeType,ownedByMe,labels(trashed),parents(id))'.format(DRIVE_FILES_LIST, DRIVE_FILE_NAME), maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
          if trashed or not metadata[u'labels'][u'trashed']:
            if metadata[u'ownedByMe'] and metadata[u'parents']:
              _transferOwnership(drive, user, i, count, metadata, j, jcount, newOwner, permissionId)
            _recursiveTransferOwnership(drive, user, i, count, fileId, newOwner, permissionId, feed, trashed)
        else:
          if trashed or not metadata[u'labels'][u'trashed']:
            if metadata[u'ownedByMe']:
              _transferOwnership(drive, user, i, count, metadata, j, jcount, newOwner, permissionId)
      except GAPI_fileNotFound:
        entityItemValueActionFailedWarning(EN_USER, user, EN_DRIVE_FILE, fileId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
        break

# gam <UserTypeEntity> claim ownership <DriveFileEntity> [skipids <DriveFileEntity>] [skipusers <UserTypeEntity>] [subdomains <DomainNameEntity>] [includetrashed] [writerscantshare]
def claimDriveFolderOwnership(users):

  def _identifyFilesToClaimOwnership(user, files, feed, folderId, skipids, skipusers, trashed):
    for f_file in feed:
      for parent in f_file[u'parents']:
        if folderId == parent[u'id']:
          owner = f_file[u'owners'][0][u'emailAddress']
          if not f_file[u'ownedByMe'] and f_file[u'id'] not in skipids and (trashed or not f_file[u'labels'][u'trashed']) and owner not in skipusers:
            files.setdefault(owner, {})
            if f_file[u'id'] not in files[owner]:
              files[owner][f_file[u'id']] = {u'name': f_file[DRIVE_FILE_NAME], u'type': [EN_DRIVE_FILE, EN_DRIVE_FOLDER][f_file[u'mimeType'] == MIMETYPE_GA_FOLDER]}
          if f_file[u'mimeType'] == MIMETYPE_GA_FOLDER and f_file[u'id'] not in skipids and (trashed or not f_file[u'labels'][u'trashed']):
            _identifyFilesToClaimOwnership(user, files, feed, f_file[u'id'], skipids, skipusers, trashed)
          break

  fileIdSelection = getDriveFileEntity()
  skipIdSelection = initDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  skipbody, skipparameters = initializeDriveFileAttributes()
  files = {}
  skipusers = []
  subdomains = []
  trashed = False
  writerscanshare = True
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'skipids':
      skipIdSelection = getDriveFileEntity()
    elif myarg == u'skipusers':
      _, skipusers = getEntityToModify(defaultEntityType=CL_ENTITY_USERS)
    elif myarg == u'subdomains':
      subdomains = getEntityList(OB_DOMAIN_NAME_ENTITY)
    elif myarg == u'includetrashed':
      trashed = True
    elif myarg == u'writerscantshare':
      writerscanshare = False
    else:
      unknownArgumentExit()
  setActionName(AC_CLAIM_OWNERSHIP)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    origUser = user
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    permissionId = validateUserGetPermissionId(user)
    if not permissionId:
      continue
    entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FILE_OR_FOLDER, i, count)
    if jcount == 0:
      continue
    if skipIdSelection[u'query'] or skipIdSelection[u'root']:
      validateUserGetFileIDs(origUser, i, count, skipIdSelection, skipbody, skipparameters, drive=drive)
    try:
      printGettingAllEntityItemsForWhom(EN_DRIVE_FILE_OR_FOLDER, user, i, count)
      page_message = getPageMessageForWhom()
      feed = callGAPIpages(drive.files(), u'list', DRIVE_FILES_LIST,
                           page_message=page_message,
                           throw_reasons=GAPI_DRIVE_THROW_REASONS,
                           fields=u'nextPageToken,items(id,{0},mimeType,ownedByMe,parents(id),owners(emailAddress),labels(trashed))'.format(DRIVE_FILE_NAME), maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
      for source_folder in fileIdSelection[u'fileIds']:
        for f_file in feed:
          if f_file[u'id'] == source_folder:
            if not f_file[u'ownedByMe'] and f_file[u'id'] not in skipIdSelection[u'fileIds']:
              owner = f_file[u'owners'][0][u'emailAddress']
              if trashed or not f_file[u'labels'][u'trashed'] and owner not in skipusers:
                files.setdefault(owner, {})
                if f_file[u'id'] not in files[owner]:
                  files[owner][f_file[u'id']] = {u'name': f_file[DRIVE_FILE_NAME], u'type': [EN_DRIVE_FILE, EN_DRIVE_FOLDER][f_file[u'mimeType'] == MIMETYPE_GA_FOLDER]}
            break
        _identifyFilesToClaimOwnership(user, files, feed, source_folder, skipIdSelection[u'fileIds'], skipusers, trashed)
      body = {u'role': u'owner'}
      bodyAdd = {u'role': u'writer', u'type': u'user', u'value': user}
      if not writerscanshare:
        bodyShare = {u'writersCanShare': False}
      jcount = len(files)
      entityPerformActionNumItems(EN_USER, user, jcount, EN_USER, i, count)
      incrementIndentLevel()
      j = 0
      for oldOwner in files:
        j += 1
        _, userdomain = splitEmailAddress(oldOwner)
        kcount = len(files[oldOwner])
        if userdomain == GC_Values[GC_DOMAIN] or userdomain in subdomains:
          source_drive = buildGAPIServiceObject(u'drive', oldOwner)
          entityPerformActionNumItemsModifier(EN_USER, user, kcount, EN_DRIVE_FILE_OR_FOLDER, u'{0} {1}: {2}'.format(AC_MODIFIER_FROM, singularEntityName(EN_USER), oldOwner), j, jcount)
          incrementIndentLevel()
          k = 0
          for fileId, fileInfo in files[oldOwner].items():
            k += 1
            if not writerscanshare:
              callGAPI(source_drive.files(), u'patch',
                       fileId=fileId, body=bodyShare)
            entityType = fileInfo[u'type']
            fileDesc = u'{0} ({1})'.format(fileInfo[u'name'], fileId)
            try:
              callGAPI(source_drive.permissions(), DRIVE_PATCH_PERMISSIONS,
                       throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND, GAPI_PERMISSION_NOT_FOUND],
                       fileId=fileId, permissionId=permissionId, transferOwnership=True, body=body)
              entityItemValueModifierNewValueInfoActionPerformed(EN_USER, user, entityType, fileDesc, AC_MODIFIER_FROM, None, singularEntityName(EN_USER), oldOwner, k, kcount)
            except GAPI_permissionNotFound:
              # if claimer not in ACL (file might be visible for all with link)
              try:
                setActionName(AC_ADD)
                callGAPI(source_drive.permissions(), DRIVE_CREATE_PERMISSIONS,
                         throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_INVALID_SHARING_REQUEST, GAPI_FILE_NOT_FOUND],
                         fileId=fileId, sendNotificationEmails=False, body=bodyAdd)
                entityItemValueItemValueActionPerformed(EN_USER, user, entityType, fileDesc, EN_PERMISSION_ID, permissionId, k, kcount)
                setActionName(AC_CLAIM_OWNERSHIP)
                callGAPI(source_drive.permissions(), DRIVE_PATCH_PERMISSIONS,
                         throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND, GAPI_PERMISSION_NOT_FOUND],
                         fileId=fileId, permissionId=permissionId, transferOwnership=True, body=body)
                entityItemValueModifierNewValueInfoActionPerformed(EN_USER, user, entityType, fileDesc, AC_MODIFIER_FROM, None, singularEntityName(EN_USER), oldOwner, k, kcount)
              except GAPI_invalidSharingRequest as e:
                entityItemValueActionFailedWarning(EN_USER, user, entityType, fileDesc, entityTypeNameMessage(EN_PERMISSION_ID, permissionId, e.message), k, kcount)
              except GAPI_permissionNotFound:
                entityDoesNotHaveItemValueSubitemValueWarning(EN_USER, user, entityType, fileDesc, EN_PERMISSION_ID, permissionId, k, kcount)
              except GAPI_fileNotFound:
                entityItemValueActionFailedWarning(EN_USER, user, entityType, fileDesc, PHRASE_DOES_NOT_EXIST, k, kcount)
              except (GAPI_serviceNotAvailable, GAPI_authError):
                entityServiceNotApplicableWarning(EN_USER, user, i, count)
            except GAPI_fileNotFound:
              entityItemValueActionFailedWarning(EN_USER, user, entityType, fileDesc, PHRASE_DOES_NOT_EXIST, k, kcount)
            except (GAPI_serviceNotAvailable, GAPI_authError):
              entityServiceNotApplicableWarning(EN_USER, user, i, count)
              break
          decrementIndentLevel()
        else:
          entityPerformActionModifierNumItemsModifier(EN_USER, user, u'Not Performed', kcount, EN_DRIVE_FILE_OR_FOLDER, u'{0} {1}: {2}'.format(AC_MODIFIER_FROM, singularEntityName(EN_USER), oldOwner), j, jcount)
          incrementIndentLevel()
          k = 0
          for fileId, fileInfo in files[oldOwner].items():
            k += 1
            entityType = fileInfo[u'type']
            fileDesc = u'{0} ({1})'.format(fileInfo[u'name'], fileId)
            entityItemValueActionNotPerformedWarning(EN_USER, user, entityType, fileDesc, PHRASE_USER_IN_OTHER_DOMAIN.format(singularEntityName(EN_USER), oldOwner), k, kcount)
          decrementIndentLevel()
      decrementIndentLevel()
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> delete|del emptydrivefolders
def deleteEmptyDriveFolders(users):
  checkForExtraneousArguments()
  setActionName(AC_DELETE_EMPTY)
  query = u"'me' in owners and mimeType = '{0}'".format(MIMETYPE_GA_FOLDER)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    try:
      printEntityKVList(EN_USER, user,
                        [u'{0} {1}'.format(GM_Globals[GM_ACTION_TO_PERFORM], pluralEntityName(EN_DRIVE_FILE_OR_FOLDER))],
                        i, count)
      incrementIndentLevel()
      deleted_empty = True
      while deleted_empty:
        printGettingAllEntityItemsForWhom(EN_DRIVE_FOLDER, user, i, count)
        page_message = getPageMessageForWhom()
        feed = callGAPIpages(drive.files(), u'list', DRIVE_FILES_LIST,
                             page_message=page_message,
                             throw_reasons=GAPI_DRIVE_THROW_REASONS,
                             q=query, fields=u'nextPageToken,{0}(id,{1})'.format(DRIVE_FILES_LIST, DRIVE_FILE_NAME), maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
        deleted_empty = False
        for folder in feed:
          children = callGAPI(drive.children(), u'list',
                              throw_reasons=GAPI_DRIVE_THROW_REASONS,
                              folderId=folder[u'id'], fields=u'{0}(id)'.format(DRIVE_FILES_LIST), maxResults=1)
          if (not children) or (DRIVE_FILES_LIST not in children) or (len(children[DRIVE_FILES_LIST]) == 0):
            callGAPI(drive.files(), u'delete',
                     fileId=folder[u'id'])
            entityItemValueActionPerformed(EN_USER, user, EN_DRIVE_FOLDER, folder[DRIVE_FILE_NAME], i, count)
            deleted_empty = True
          else:
            entityItemValueActionNotPerformedWarning(EN_USER, user, EN_DRIVE_FOLDER, folder[DRIVE_FILE_NAME], u'{0} - {1}'.format(PHRASE_CONTAINS_AT_LEAST_1_ITEM, children[DRIVE_FILES_LIST][0][u'id']), i, count)
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
      break
    decrementIndentLevel()

# gam <UserTypeEntity> empty drivetrash
def emptyDriveTrash(users):
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive = buildDriveGAPIObject(user)
    if not drive:
      continue
    try:
      callGAPI(drive.files(), u'emptyTrash',
               throw_reasons=GAPI_DRIVE_THROW_REASONS)
      entityItemValueActionPerformed(EN_USER, user, EN_DRIVE_TRASH, None, i, count)
    except (GAPI_serviceNotAvailable, GAPI_authError):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# Utilities for DriveFileACL commands
def _showPermission(permission):
  if DRIVE_PERMISSIONS_NAME in permission:
    printKeyValueList([permission[DRIVE_PERMISSIONS_NAME]])
  elif u'id' in permission:
    if permission[u'id'] == u'anyone':
      printKeyValueList([u'Anyone'])
    elif permission[u'id'] == u'anyoneWithLink':
      printKeyValueList([u'Anyone with Link'])
    else:
      printKeyValueList([permission[u'id']])
  incrementIndentLevel()
  for key in permission:
    if key not in [u'kind', u'etag', u'selfLink', DRIVE_PERMISSIONS_NAME]:
      printKeyValueList([key, permission[key]])
  decrementIndentLevel()
#
DRIVEFILE_ACL_ROLES_MAP = {
  u'commenter': u'commenter',
  u'editor': u'writer',
  u'owner': u'owner',
  u'read': u'read',
  u'reader': u'reader',
  u'writer': u'writer',
  }

DRIVEFILE_ACL_PERMISSION_TYPES = [u'anyone', u'domain', u'group', u'user',]

# gam <UserTypeEntity> add drivefileacl <DriveFileEntity> anyone|(user <UserItem>)|(group <GroupItem>)|(domain <DomainName>)
#	(role reader|commenter|writer|owner|editor) [withlink|(allowfilediscovery <Boolean>)] [sendmail] [emailmessage <String>] [showtitles]
def addDriveFileACL(users):
  sendNotificationEmails = showTitles = False
  emailMessage = None
  fileIdSelection = getDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  body[u'type'] = getChoice(DRIVEFILE_ACL_PERMISSION_TYPES)
  if body[u'type'] != u'anyone':
    if body[u'type'] != u'domain':
      body[u'value'] = getEmailAddress()
    else:
      body[u'value'] = getString(OB_DOMAIN_NAME)
    permissionId = body[u'value']
  else:
    permissionId = u'anyone'
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'withlink':
      body[u'withLink'] = True
    elif myarg == u'allowfilediscovery':
      body[u'withLink'] = not getBoolean()
    elif myarg == u'role':
      body[u'role'] = getChoice(DRIVEFILE_ACL_ROLES_MAP, mapChoice=True)
      if body[u'role'] == u'commenter':
        body[u'role'] = u'reader'
        body[u'additionalRoles'] = [u'commenter',]
    elif myarg == u'sendemail':
      sendNotificationEmails = True
    elif myarg == u'emailmessage':
      sendNotificationEmails = True
      emailMessage = getString(OB_STRING)
    elif myarg == u'showtitles':
      showTitles = True
    else:
      unknownArgumentExit()
  if u'role' not in body:
    missingArgumentExit(u'role {0}'.format(formatChoiceList(DRIVEFILE_ACL_ROLES_MAP)))
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FILE_OR_FOLDER_ACL, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for fileId in fileIdSelection[u'fileIds']:
      j += 1
      try:
        fileName = fileId
        entityType = EN_DRIVE_FILE_OR_FOLDER_ID
        if showTitles:
          result = callGAPI(drive.files(), u'get',
                            throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                            fileId=fileId, fields=DRIVE_FILE_NAME)
          if result and DRIVE_FILE_NAME in result:
            entityType = EN_DRIVE_FILE_OR_FOLDER
            fileName = result[DRIVE_FILE_NAME]+u'('+fileId+u')'
        permission = callGAPI(drive.permissions(), DRIVE_CREATE_PERMISSIONS,
                              throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_INVALID_SHARING_REQUEST, GAPI_FILE_NOT_FOUND],
                              fileId=fileId, sendNotificationEmails=sendNotificationEmails, emailMessage=emailMessage, body=body)
        entityItemValueItemValueActionPerformed(EN_USER, user, entityType, fileName, EN_PERMISSION_ID, permissionId, j, jcount)
        _showPermission(permission)
      except GAPI_invalidSharingRequest as e:
        entityItemValueActionFailedWarning(EN_USER, user, entityType, fileName, entityTypeNameMessage(EN_PERMISSION_ID, permissionId, e.message), j, jcount)
      except GAPI_fileNotFound:
        entityItemValueActionFailedWarning(EN_USER, user, entityType, fileName, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
        break
    decrementIndentLevel()

# gam <UserTypeEntity> update drivefileacl <DriveFileEntity> <PermissionID>
#	(role reader|commenter|writer|owner|editor) [withlink|(allowfilediscovery <Boolean>)] [removeexpiration <Boolean>] [transferownership <Boolean>] [showtitles]
def updateDriveFileACL(users):
  fileIdSelection = getDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  isEmail, permissionId = getPermissionId()
  removeExpiration = transferOwnership = showTitles = None
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'withlink':
      body[u'withLink'] = True
    elif myarg == u'allowfilediscovery':
      body[u'withLink'] = not getBoolean()
    elif myarg == u'role':
      body[u'role'] = getChoice(DRIVEFILE_ACL_ROLES_MAP, mapChoice=True)
      if body[u'role'] == u'commenter':
        body[u'role'] = u'reader'
        body[u'additionalRoles'] = [u'commenter',]
    elif myarg == u'removeexpiration':
      removeExpiration = getBoolean()
    elif myarg == u'transferownership':
      transferOwnership = getBoolean()
    elif myarg == u'showtitles':
      showTitles = True
    else:
      unknownArgumentExit()
  if removeExpiration == None and u'role' not in body:
    missingArgumentExit(u'role {0}'.format(formatChoiceList(DRIVEFILE_ACL_ROLES_MAP)))
  if isEmail:
    permissionId = validateUserGetPermissionId(permissionId)
    if not permissionId:
      return
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FILE_OR_FOLDER_ACL, i, count)
    if jcount == 0:
      continue
    incrementIndentLevel()
    j = 0
    for fileId in fileIdSelection[u'fileIds']:
      j += 1
      try:
        fileName = fileId
        entityType = EN_DRIVE_FILE_OR_FOLDER_ID
        if showTitles:
          result = callGAPI(drive.files(), u'get',
                            throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                            fileId=fileId, fields=DRIVE_FILE_NAME)
          if result and DRIVE_FILE_NAME in result:
            entityType = EN_DRIVE_FILE_OR_FOLDER
            fileName = result[DRIVE_FILE_NAME]+u'('+fileId+u')'
        permission = callGAPI(drive.permissions(), DRIVE_PATCH_PERMISSIONS,
                              throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND, GAPI_PERMISSION_NOT_FOUND],
                              fileId=fileId, permissionId=permissionId, removeExpiration=removeExpiration, transferOwnership=transferOwnership, body=body)
        entityItemValueItemValueActionPerformed(EN_USER, user, entityType, fileName, EN_PERMISSION_ID, permissionId, j, jcount)
        _showPermission(permission)
      except GAPI_permissionNotFound:
        entityDoesNotHaveItemValueSubitemValueWarning(EN_USER, user, entityType, fileName, EN_PERMISSION_ID, permissionId, j, jcount)
      except GAPI_fileNotFound:
        entityItemValueActionFailedWarning(EN_USER, user, entityType, fileName, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
        break
    decrementIndentLevel()

# gam <UserTypeEntity> delete|del drivefileacl <DriveFileEntity> <PermissionID> [showtitles]
def deleteDriveFileACL(users):
  fileIdSelection = getDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  isEmail, permissionId = getPermissionId()
  showTitles = checkArgumentPresent(SHOWTITLES_ARGUMENT)
  checkForExtraneousArguments()
  if isEmail:
    permissionId = validateUserGetPermissionId(permissionId)
    if not permissionId:
      return
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FILE_OR_FOLDER_ACL, i, count)
    if jcount == 0:
      continue
    incrementIndentLevel()
    j = 0
    for fileId in fileIdSelection[u'fileIds']:
      j += 1
      try:
        fileName = fileId
        entityType = EN_DRIVE_FILE_OR_FOLDER_ID
        if showTitles:
          result = callGAPI(drive.files(), u'get',
                            throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                            fileId=fileId, fields=DRIVE_FILE_NAME)
          if result and DRIVE_FILE_NAME in result:
            entityType = EN_DRIVE_FILE_OR_FOLDER
            fileName = result[DRIVE_FILE_NAME]+u'('+fileId+u')'
        callGAPI(drive.permissions(), u'delete',
                 throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND, GAPI_PERMISSION_NOT_FOUND],
                 fileId=fileId, permissionId=permissionId)
        entityItemValueItemValueActionPerformed(EN_USER, user, entityType, fileName, EN_PERMISSION_ID, permissionId, j, jcount)
      except GAPI_permissionNotFound:
        entityDoesNotHaveItemValueSubitemValueWarning(EN_USER, user, entityType, fileName, EN_PERMISSION_ID, permissionId, j, jcount)
      except GAPI_fileNotFound:
        entityItemValueActionFailedWarning(EN_USER, user, entityType, fileName, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
        break
    decrementIndentLevel()

# gam <UserTypeEntity> show drivefileacl <DriveFileEntity> [showtitles]
def showDriveFileACL(users):
  fileIdSelection = getDriveFileEntity()
  body, parameters = initializeDriveFileAttributes()
  showTitles = checkArgumentPresent(SHOWTITLES_ARGUMENT)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, drive, jcount = validateUserGetFileIDs(user, i, count, fileIdSelection, body, parameters)
    if not drive:
      continue
    entityPerformActionNumItems(EN_USER, user, jcount, EN_DRIVE_FILE_OR_FOLDER_ACL, i, count)
    if jcount == 0:
      continue
    incrementIndentLevel()
    j = 0
    for fileId in fileIdSelection[u'fileIds']:
      j += 1
      try:
        fileName = fileId
        entityType = EN_DRIVE_FILE_OR_FOLDER_ID
        if showTitles:
          result = callGAPI(drive.files(), u'get',
                            throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                            fileId=fileId, fields=DRIVE_FILE_NAME)
          if result and DRIVE_FILE_NAME in result:
            entityType = EN_DRIVE_FILE_OR_FOLDER
            fileName = result[DRIVE_FILE_NAME]+u'('+fileId+u')'
        result = callGAPI(drive.permissions(), u'list',
                          throw_reasons=GAPI_DRIVE_THROW_REASONS+[GAPI_FILE_NOT_FOUND],
                          fileId=fileId, fields=DRIVE_PERMISSIONS_LIST)
        printEntityKVList(entityType, fileName, [pluralEntityName(EN_PERMISSIONS)], j, jcount)
        if result:
          incrementIndentLevel()
          for permission in result[DRIVE_PERMISSIONS_LIST]:
            _showPermission(permission)
          decrementIndentLevel()
      except GAPI_fileNotFound:
        entityItemValueActionFailedWarning(EN_USER, user, entityType, fileName, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_authError):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
        break
    decrementIndentLevel()

# gam <UserTypeEntity> delete|del alias|aliases
def deleteUsersAliases(users):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      user_aliases = callGAPI(cd.users(), u'get',
                              throw_reasons=GAPI_USER_GET_THROW_REASONS,
                              userKey=user, fields=u'id,primaryEmail,aliases')
      user_id = user_aliases[u'id']
      user_primary = user_aliases[u'primaryEmail']
      jcount = len(user_aliases[u'aliases']) if (u'aliases' in user_aliases) else 0
      entityPerformActionNumItems(EN_USER, user_primary, jcount, EN_ALIAS, i, count)
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
        continue
      incrementIndentLevel()
      j = 0
      for an_alias in user_aliases[u'aliases']:
        j += 1
        try:
          callGAPI(cd.users().aliases(), u'delete',
                   throw_reasons=[GAPI_RESOURCE_ID_NOT_FOUND],
                   userKey=user_id, alias=an_alias)
          entityItemValueActionPerformed(EN_USER, user_primary, EN_ALIAS, an_alias, j, jcount)
        except GAPI_resourceIdNotFound:
          entityItemValueActionFailedWarning(EN_USER, user_primary, EN_ALIAS, an_alias, PHRASE_DOES_NOT_EXIST, j, jcount)
      decrementIndentLevel()
    except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden, GAPI_badRequest, GAPI_backendError, GAPI_systemError):
      entityUnknownWarning(EN_USER, user, i, count)

def checkUserExists(cd, user, i=0, count=0):
  user = normalizeEmailAddressOrUID(user)
  try:
    callGAPI(cd.users(), u'get',
             throw_reasons=GAPI_USER_GET_THROW_REASONS,
             userKey=user, fields=u'primaryEmail')
    return user
  except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden, GAPI_badRequest, GAPI_backendError, GAPI_systemError):
    entityUnknownWarning(EN_USER, user, i, count)
    return None

# gam <UserTypeEntity> add group|groups [owner|manager|member] <GroupEntity>
def addUserToGroups(users):
  def _callbackAddUserToGroups(request_id, response, exception):
    REASON_TO_MESSAGE_MAP = {GAPI_DUPLICATE: PHRASE_DUPLICATE, GAPI_MEMBER_NOT_FOUND: PHRASE_DOES_NOT_EXIST,
                             GAPI_INVALID_MEMBER: PHRASE_INVALID_ROLE}
    ri = request_id.splitlines()
    if exception is None:
      if str(response[u'email']).lower() != ri[RI_ITEM]:
        entityItemValueActionPerformed(EN_GROUP, ri[RI_ENTITY], ri[RI_ROLE], u'{0} (primary address)'.format(response[u'email']), int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        entityItemValueActionPerformed(EN_GROUP, ri[RI_ENTITY], ri[RI_ROLE], response[u'email'], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      if reason in [GAPI_GROUP_NOT_FOUND, GAPI_FORBIDDEN]:
        entityUnknownWarning(EN_GROUP, ri[RI_ENTITY], int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
        entityItemValueActionFailedWarning(EN_GROUP, ri[RI_ENTITY], ri[RI_ROLE], ri[RI_ITEM], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _batchAddUserToGroups(cd, user, i, count, groupKeys, body):
    setActionName(AC_ADD)
    role = body[u'role']
    jcount = len(groupKeys)
    entityPerformActionModifierNumItemsModifier(EN_USER, user, AC_MODIFIER_TO, jcount, EN_GROUP, u'{0} {1}'.format(PHRASE_AS, body[u'role'].lower()), i, count)
    incrementIndentLevel()
    bcount = 0
    bsize = GC_Values[GC_BATCH_SIZE]
    if bsize > 1:
      dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackAddUserToGroups)
    j = 0
    for group in groupKeys:
      j += 1
      group = normalizeEmailAddressOrUID(group)
      if bsize > 1:
        parameters = dict([(u'groupKey', group), (u'body', body)]+GM_Globals[GM_EXTRA_ARGS_LIST])
        dbatch.add(cd.members().insert(**parameters), request_id=batchRequestID(group, i, count, j, jcount, user, body[u'role']))
        bcount += 1
        if bcount == bsize:
          dbatch.execute()
          dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackAddUserToGroups)
          bcount = 0
      else:
        try:
          response = callGAPI(cd.members(), u'insert',
                              throw_reasons=[GAPI_DUPLICATE, GAPI_MEMBER_NOT_FOUND, GAPI_INVALID_MEMBER, GAPI_GROUP_NOT_FOUND, GAPI_FORBIDDEN],
                              groupKey=group, body=body)
          if str(response[u'email']).lower() != user:
            entityItemValueActionPerformed(EN_GROUP, group, role, u'{0} (primary address)'.format(response[u'email']), j, jcount)
          else:
            entityItemValueActionPerformed(EN_GROUP, group, role, response[u'email'], j, jcount)
        except GAPI_duplicate:
          entityItemValueActionFailedWarning(EN_GROUP, group, role, user, PHRASE_DUPLICATE, j, jcount)
        except GAPI_memberNotFound:
          entityItemValueActionFailedWarning(EN_GROUP, group, role, user, PHRASE_DOES_NOT_EXIST, j, jcount)
        except GAPI_invalidMember:
          entityItemValueActionFailedWarning(EN_GROUP, group, role, user, PHRASE_INVALID_ROLE, j, jcount)
        except (GAPI_groupNotFound, GAPI_forbidden):
          entityUnknownWarning(EN_GROUP, group, j, jcount)
    if bcount > 0:
      dbatch.execute()
    decrementIndentLevel()

  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  role = getChoice(UPDATE_GROUP_ROLES_MAP, defaultChoice=ROLE_MEMBER, mapChoice=True)
  groupKeys = getEntityList(OB_GROUP_ENTITY)
  userGroupLists = groupKeys if isinstance(groupKeys, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if userGroupLists:
      groupKeys = userGroupLists[user]
    user = checkUserExists(cd, user, i, count)
    if user:
      if user.find(u'@') != -1:
        body = {u'role': role, u'email': user}
      else:
        body = {u'role': role, u'id': user}
      _batchAddUserToGroups(cd, user, i, count, groupKeys, body)

# gam <UserTypeEntity> delete|del group|groups [<GroupEntity>]
def deleteUserFromGroups(users):
  def _callbackDeleteUserFromGroups(request_id, response, exception):
    REASON_TO_MESSAGE_MAP = {GAPI_MEMBER_NOT_FOUND: u'{0} {1}'.format(PHRASE_NOT_A, singularEntityName(EN_MEMBER)),
                             GAPI_INVALID_MEMBER: PHRASE_DOES_NOT_EXIST}
    ri = request_id.splitlines()
    if exception is None:
      entityItemValueActionPerformed(EN_GROUP, ri[RI_ENTITY], ri[RI_ROLE], ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      if reason in [GAPI_GROUP_NOT_FOUND, GAPI_FORBIDDEN]:
        entityUnknownWarning(EN_GROUP, ri[RI_ENTITY], int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
        entityItemValueActionFailedWarning(EN_GROUP, ri[RI_ENTITY], ri[RI_ROLE], ri[RI_ITEM], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _batchDeleteUserFromGroups(cd, user, i, count, groupKeys):
    setActionName(AC_REMOVE)
    role = EN_MEMBER
    jcount = len(groupKeys)
    entityPerformActionModifierNumItems(EN_USER, user, AC_MODIFIER_FROM, jcount, EN_GROUP, i, count)
    incrementIndentLevel()
    bcount = 0
    bsize = GC_Values[GC_BATCH_SIZE]
    if bsize > 1:
      dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackDeleteUserFromGroups)
    j = 0
    for group in groupKeys:
      j += 1
      group = normalizeEmailAddressOrUID(group)
      if bsize > 1:
        parameters = dict([(u'groupKey', group), (u'memberKey', user)]+GM_Globals[GM_EXTRA_ARGS_LIST])
        dbatch.add(cd.members().delete(**parameters), request_id=batchRequestID(group, i, count, j, jcount, user, role))
        bcount += 1
        if bcount == bsize:
          dbatch.execute()
          dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackDeleteUserFromGroups)
          bcount = 0
      else:
        try:
          callGAPI(cd.members(), u'delete',
                   throw_reasons=[GAPI_MEMBER_NOT_FOUND, GAPI_INVALID_MEMBER, GAPI_GROUP_NOT_FOUND, GAPI_FORBIDDEN],
                   groupKey=group, memberKey=user)
          entityItemValueActionPerformed(EN_GROUP, group, role, user, j, jcount)
        except GAPI_memberNotFound:
          entityItemValueActionFailedWarning(EN_GROUP, group, role, user, u'{0} {1}'.format(PHRASE_NOT_A, singularEntityName(EN_MEMBER)), j, jcount)
        except GAPI_invalidMember:
          entityItemValueActionFailedWarning(EN_GROUP, group, role, user, PHRASE_DOES_NOT_EXIST, j, jcount)
        except (GAPI_groupNotFound, GAPI_forbidden):
          entityUnknownWarning(EN_GROUP, group, j, jcount)
    if bcount > 0:
      dbatch.execute()
    decrementIndentLevel()

  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  if CL_argvI < CL_argvLen:
    groupKeys = getEntityList(OB_GROUP_ENTITY)
    userGroupLists = groupKeys if isinstance(groupKeys, dict) else None
    checkForExtraneousArguments()
  else:
    groupKeys = None
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if groupKeys == None:
      user = checkUserExists(cd, user, i, count)
      if user:
        result = callGAPIpages(cd.groups(), u'list', u'groups',
                               userKey=user, fields=u'groups(email)')
        userGroupKeys = [item[u'email'] for item in result]
        _batchDeleteUserFromGroups(cd, user, i, count, userGroupKeys)
    else:
      if userGroupLists:
        userGroupKeys = userGroupLists[user]
      else:
        userGroupKeys = groupKeys
      user = checkUserExists(cd, user, i, count)
      if user:
        _batchDeleteUserFromGroups(cd, user, i, count, userGroupKeys)

# Utilities for License command
#
LICENSE_SKUID = u'skuId'
LICENSE_PRODUCTID = u'productId'
LICENSE_OLDSKUID = u'oldSkuId'

def getLicenseParameters(operation):
  lic = buildGAPIObject(GAPI_LICENSING_API)
  parameters = {}
  parameters[LICENSE_SKUID] = getGoogleSKUMap()
  parameters[LICENSE_PRODUCTID] = GOOGLE_SKUS[parameters[LICENSE_SKUID]]
  if operation == u'patch':
    checkArgumentPresent(FROM_ARGUMENT)
    parameters[LICENSE_OLDSKUID] = getGoogleSKUMap(matchProduct=parameters[LICENSE_PRODUCTID])
  checkForExtraneousArguments()
  return (lic, parameters)

# gam <UserTypeEntity> add license <SKUID>
def addLicense(users):
  lic, parameters = getLicenseParameters(u'insert')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      callGAPI(lic.licenseAssignments(), u'insert',
               throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_FORBIDDEN, GAPI_BACKEND_ERROR, GAPI_DUPLICATE, GAPI_CONDITION_NOT_MET],
               productId=parameters[LICENSE_PRODUCTID], skuId=parameters[LICENSE_SKUID], body={u'userId': user})
      entityItemValueActionPerformed(EN_USER, user, EN_LICENSE, parameters[LICENSE_SKUID], i, count)
    except GAPI_conditionNotMet as e:
      entityItemValueActionFailedWarning(EN_USER, user, EN_LICENSE, parameters[LICENSE_SKUID], e.message, i, count)
    except GAPI_duplicate:
      entityItemValueActionFailedWarning(EN_USER, user, EN_LICENSE, parameters[LICENSE_SKUID], PHRASE_DUPLICATE, i, count)
    except (GAPI_userNotFound, GAPI_forbidden, GAPI_backendError):
      entityUnknownWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> update license <SKUID> [from] <SKUID>
def updateLicense(users):
  lic, parameters = getLicenseParameters(u'patch')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      callGAPI(lic.licenseAssignments(), u'patch',
               throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_FORBIDDEN, GAPI_NOT_FOUND, GAPI_BACKEND_ERROR],
               productId=parameters[LICENSE_PRODUCTID], skuId=parameters[LICENSE_OLDSKUID], userId=user, body={u'skuId': parameters[LICENSE_SKUID]})
      entityItemValueModifierNewValueActionPerformed(EN_USER, user, EN_LICENSE, parameters[LICENSE_SKUID], AC_MODIFIER_FROM, parameters[LICENSE_OLDSKUID], i, count)
    except GAPI_notFound:
      entityItemValueActionFailedWarning(EN_USER, user, EN_LICENSE, parameters[LICENSE_OLDSKUID], PHRASE_DOES_NOT_EXIST, i, count)
    except (GAPI_userNotFound, GAPI_forbidden, GAPI_backendError):
      entityUnknownWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> delete|del license <SKUID>
def deleteLicense(users):
  lic, parameters = getLicenseParameters(u'delete')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      callGAPI(lic.licenseAssignments(), u'delete',
               throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_FORBIDDEN, GAPI_NOT_FOUND, GAPI_BACKEND_ERROR],
               productId=parameters[LICENSE_PRODUCTID], skuId=parameters[LICENSE_SKUID], userId=user)
      entityItemValueActionPerformed(EN_USER, user, EN_LICENSE, parameters[LICENSE_SKUID], i, count)
    except GAPI_notFound:
      entityItemValueActionFailedWarning(EN_USER, user, EN_LICENSE, parameters[LICENSE_SKUID], PHRASE_DOES_NOT_EXIST, i, count)
    except (GAPI_userNotFound, GAPI_forbidden, GAPI_backendError):
      entityUnknownWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> update photo <FileNamePattern>
#	#  #user# and #email" will be replaced with user email address #username# will be replaced by portion of email address in front of @
def updatePhoto(users):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  filenamePattern = getString(OB_PHOTO_FILENAME_PATTERN)
  checkForExtraneousArguments()
  p = re.compile(u'^(ht|f)tps?://.*$')
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, userName, _ = splitEmailAddressOrUID(user)
    filename = filenamePattern.replace(u'#user#', user)
    filename = filename.replace(u'#email#', user)
    filename = filename.replace(u'#username#', userName)
    if p.match(filename):
      import urllib2
      try:
        with urllib2.urlopen(filename) as f:
          image_data = str(f.read())
      except urllib2.HTTPError as e:
        entityItemValueActionFailedWarning(EN_USER, user, EN_PHOTO, filename, e, i, count)
        continue
    else:
      image_data = readFile(filename, continueOnError=True, displayError=True)
      if image_data == None:
        entityItemValueActionFailedWarning(EN_USER, user, EN_PHOTO, filename, e.strerror, i, count)
        continue
    body = {u'photoData': base64.urlsafe_b64encode(image_data)}
    try:
      callGAPI(cd.users().photos(), u'update',
               throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_FORBIDDEN],
               userKey=user, body=body)
      entityItemValueActionPerformed(EN_USER, user, EN_PHOTO, filename, i, count)
    except (GAPI_userNotFound, GAPI_forbidden):
      entityUnknownWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> delete|del photo
def deletePhoto(users):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      callGAPI(cd.users().photos(), u'delete',
               throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_FORBIDDEN, GAPI_NOT_FOUND],
               userKey=user)
      entityItemValueActionPerformed(EN_USER, user, EN_PHOTO, u'', i, count)
    except GAPI_notFound:
      entityItemValueActionFailedWarning(EN_USER, user, EN_PHOTO, u'', PHRASE_DOES_NOT_EXIST, i, count)
    except (GAPI_userNotFound, GAPI_forbidden):
      entityUnknownWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> get photo [drivedir|(targetfolder <FilePath>)] [noshow]
def getPhoto(users):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  targetFolder = os.getcwd()
  showPhotoData = True
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'drivedir':
      targetFolder = GC_Values[GC_DRIVE_DIR]
    elif myarg == u'targetfolder':
      targetFolder = os.path.expanduser(getString(OB_FILE_PATH))
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
    elif myarg == u'noshow':
      showPhotoData = False
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      entityPerformActionNumItems(EN_USER, user, 1, EN_PHOTO, i, count)
      photo = callGAPI(cd.users().photos(), u'get',
                       throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_FORBIDDEN, GAPI_PHOTO_NOT_FOUND],
                       userKey=user)
      filename = os.path.join(targetFolder, u'{0}.jpg'.format(user))
      photo_data = str(photo[u'photoData'])
      if showPhotoData:
        sys.stdout.write(photo_data+'\n')
      status, e = writeFileReturnError(filename, base64.urlsafe_b64decode(photo_data))
      if status:
        entityItemValueActionPerformed(EN_USER, user, EN_PHOTO, filename, i, count)
      else:
        entityItemValueActionFailedWarning(EN_USER, user, EN_PHOTO, filename, e.strerror, i, count)
    except GAPI_photoNotFound:
      entityItemValueActionFailedWarning(EN_USER, user, EN_PHOTO, u'None', PHRASE_DOES_NOT_EXIST, i, count)
    except (GAPI_userNotFound, GAPI_forbidden):
      entityUnknownWarning(EN_USER, user, i, count)

PROFILE_SHARING_CHOICES_MAP = {
  u'share': True,
  u'shared': True,
  u'unshare': False,
  u'unshared': False,
  }

# gam <UserTypeEntity> profile share|shared|unshare|unshared
def setProfile(users):
  body = {u'includeInGlobalAddressList': getChoice(PROFILE_SHARING_CHOICES_MAP, mapChoice=True)}
  checkForExtraneousArguments()
  setShowProfile(users, u'patch', body=body)

# gam <UserTypeEntity> show profile
def showProfile(users):
  checkForExtraneousArguments()
  setShowProfile(users, u'get')

def setShowProfile(users, function, **kwargs):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      result = callGAPI(cd.users(), function,
                        throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_FORBIDDEN],
                        userKey=user, fields=u'includeInGlobalAddressList', **kwargs)
      printEntityItemValue(EN_USER, user, EN_PROFILE_SHARING_ENABLED, result.get(u'includeInGlobalAddressList', u'Unknown'), i, count)
    except (GAPI_userNotFound, GAPI_forbidden):
      entityUnknownWarning(EN_USER, user, i, count)

# Utilities for Token commands
def commonClientIds(clientId):
  if clientId == u'gasmo':
    return u'1095133494869.apps.googleusercontent.com'
  return clientId

# gam <UserTypeEntity> delete|del token|tokens|3lo|oauth clientid <ClientID>
def deleteTokens(users):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkArgumentPresent(CLIENTID_ARGUMENT, required=True)
  clientId = commonClientIds(getString(OB_CLIENT_ID))
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      callGAPI(cd.tokens(), u'delete',
               throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_NOT_FOUND],
               userKey=user, clientId=clientId)
      entityItemValueActionPerformed(EN_USER, user, EN_ACCESS_TOKEN, clientId, i, count)
    except GAPI_notFound:
      entityItemValueActionFailedWarning(EN_USER, user, EN_ACCESS_TOKEN, clientId, PHRASE_DOES_NOT_EXIST, i, count)
    except GAPI_userNotFound:
      entityUnknownWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> show tokens|token|3lo|oauth [clientid <ClientID>]
def showTokens(users):
  printShowTokens(CL_ENTITY_USERS, users, False)

# gam <UserTypeEntity> print tokens|token [todrive] [clientid <ClientID>]
def printTokens(users):
  printShowTokens(CL_ENTITY_USERS, users, True)

# gam print tokens|token [todrive] [clientid <ClientID>] [<UserTypeEntity>]
def doPrintTokens():
  printShowTokens(None, None, True)

def printShowTokens(entityType, users, csvFormat):
  def _showToken(token, j, jcount):
    printKeyValueListWithCount([u'Client ID', token[u'clientId']], j, jcount)
    incrementIndentLevel()
    for item in [u'displayText', u'anonymous', u'nativeApp', u'userKey']:
      printKeyValueList([item, token.get(item, u'')])
    item = u'scopes'
    printKeyValueList([item, u''])
    incrementIndentLevel()
    for it in token.get(item, []):
      printKeyValueList([it])
    decrementIndentLevel()
    decrementIndentLevel()

  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile([u'user', u'clientId', u'displayText', u'anonymous', u'nativeApp', u'userKey', u'scopes'])
  clientId = None
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    elif myarg == u'clientid':
      clientId = commonClientIds(getString(OB_CLIENT_ID))
    elif not entityType:
      putArgumentBack()
      entityType, users = getEntityToModify(defaultEntityType=CL_ENTITY_USERS)
  if not entityType:
    users = getUsersToModify(CL_ENTITY_ALL_USERS, None)
  fields = u','.join([u'clientId', u'displayText', u'anonymous', u'nativeApp', u'userKey', u'scopes'])
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      if csvFormat:
        printGettingEntityItemForWhom(EN_ACCESS_TOKEN, user, i, count)
      if clientId:
        results = [callGAPI(cd.tokens(), u'get',
                            throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN, GAPI_NOT_FOUND, GAPI_RESOURCE_NOT_FOUND],
                            userKey=user, clientId=clientId, fields=fields)]
      else:
        results = callGAPIitems(cd.tokens(), u'list', u'items',
                                throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_FORBIDDEN],
                                userKey=user, fields=u'items({0})'.format(fields))
      jcount = len(results)
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
      if not csvFormat:
        entityPerformActionNumItems(EN_USER, user, jcount, EN_ACCESS_TOKEN, i, count)
        if jcount == 0:
          continue
        incrementIndentLevel()
        j = 0
        for token in results:
          j += 1
          _showToken(token, j, jcount)
        decrementIndentLevel()
      else:
        if jcount == 0:
          continue
        for token in results:
          row = {u'user': user, u'scopes': u' '.join(token.get(u'scopes', []))}
          for item in [u'displayText', u'anonymous', u'nativeApp', u'userKey']:
            row[item] = token.get(item, u'')
          csvRows.append(row)
    except (GAPI_notFound, GAPI_resourceNotFound):
      entityItemValueActionFailedWarning(EN_USER, user, EN_ACCESS_TOKEN, clientId, PHRASE_DOES_NOT_EXIST, i, count)
    except (GAPI_userNotFound, GAPI_domainNotFound, GAPI_forbidden):
      entityUnknownWarning(EN_USER, user, i, count)
  if csvFormat:
    writeCSVfile(csvRows, titles, u'OAuth Tokens', todrive)

# gam <UserTypeEntity> deprovision|deprov
def deprovisionUser(users):
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      printGettingEntityItemForWhom(EN_APPLICATION_SPECIFIC_PASSWORD, user, i, count)
      asps = callGAPIitems(cd.asps(), u'list', u'items',
                           throw_reasons=[GAPI_USER_NOT_FOUND],
                           userKey=user, fields=u'items(codeId)')
      jcount = len(asps)
      entityPerformActionNumItems(EN_USER, user, jcount, EN_APPLICATION_SPECIFIC_PASSWORD, i, count)
      if jcount == 0:
        continue
      incrementIndentLevel()
      j = 0
      for asp in asps:
        j += 1
        codeId = asp[u'codeId']
        try:
          callGAPI(cd.asps(), u'delete',
                   throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_INVALID],
                   userKey=user, codeId=codeId)
          entityItemValueActionPerformed(EN_USER, user, EN_APPLICATION_SPECIFIC_PASSWORD, codeId, j, jcount)
        except GAPI_invalid:
          entityItemValueActionFailedWarning(EN_USER, user, EN_APPLICATION_SPECIFIC_PASSWORD, codeId, PHRASE_DOES_NOT_EXIST, j, jcount)
      decrementIndentLevel()
#
      callGAPI(cd.verificationCodes(), u'invalidate',
               throw_reasons=[GAPI_USER_NOT_FOUND],
               userKey=user)
      printEntityKVList(EN_USER, user,
                        [pluralEntityName(EN_BACKUP_VERIFICATION_CODE), ACTION_NAMES[AC_INVALIDATE][0]],
                        i, count)
#
      tokens = callGAPIitems(cd.tokens(), u'list', u'items',
                             throw_reasons=[GAPI_USER_NOT_FOUND],
                             userKey=user, fields=u'items(clientId)')
      jcount = len(tokens)
      entityPerformActionNumItems(EN_USER, user, jcount, EN_ACCESS_TOKEN, i, count)
      if jcount == 0:
        continue
      incrementIndentLevel()
      j = 0
      for token in tokens:
        j += 1
        clientId = token[u'clientId']
        try:
          callGAPI(cd.tokens(), u'delete',
                   throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_NOT_FOUND],
                   userKey=user, clientId=clientId)
          entityItemValueActionPerformed(EN_USER, user, EN_ACCESS_TOKEN, clientId, j, jcount)
        except GAPI_notFound:
          entityItemValueActionFailedWarning(EN_USER, user, EN_ACCESS_TOKEN, clientId, PHRASE_DOES_NOT_EXIST, j, jcount)
      decrementIndentLevel()
#
      entityActionPerformed(EN_USER, user, i, count)
    except GAPI_userNotFound:
      entityUnknownWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> print gmailprofile [todrive]
def printGmailProfile(users):
  printShowGmailProfile(users, True)

# gam <UserTypeEntity> show gmailprofile
def showGmailProfile(users):
  printShowGmailProfile(users, False)

def printShowGmailProfile(users, csvFormat):
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile(None)
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    if csvFormat:
      printGettingEntityItemForWhom(EN_GMAIL_PROFILE, user, i, count)
    try:
      results = callGAPI(gmail.users(), u'getProfile',
                         throw_reasons=GAPI_GMAIL_THROW_REASONS,
                         userId=u'me')
      if not csvFormat:
        kvList = []
        for item in [u'historyId', u'messagesTotal', u'threadsTotal']:
          kvList += [item, results[item]]
        printEntityKVList(EN_USER, user, kvList, i, count)
      else:
        addRowTitlesToCSVfile(results, csvRows, titles)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
  if csvFormat:
    sortCSVTitles([u'emailAddress',], titles)
    writeCSVfile(csvRows, titles, u'Gmail Profiles', todrive)

PROFILE_PROPERTY_PRINT_ORDER = [
  u'objectType',
  u'displayName',
  u'name',
  u'nickname',
  u'domain',
  u'birthday',
  u'ageRange',
  u'gender',
  u'relationshipStatus',
  u'placesLived',
  u'language',
  u'occupation',
  u'aboutMe',
  u'braggingRights',
  u'skills',
  u'tagline',
  u'circledByCount',
  u'plusOneCount',
  u'verified',
  u'emails',
  u'organizations',
  u'urls',
  u'cover',
  ]

PROFILE_ARRAY_PROPERTY_PRINT_ORDER = {
  u'ageRange': [u'min', u'max'],
  u'cover': [u'layout', u'coverPhoto', u'coverInfo'],
  u'coverInfo': [u'topImageOffset', u'leftImageOffset'],
  u'coverPhoto': [u'url', u'height', u'width'],
  u'emails': [u'type', u'value'],
  u'image': [u'url',],
  u'name': [u'formatted', u'honorificPrefix', u'givenName', u'middleName', u'familyName', u'honorificSuffix'],
  u'organizations': [u'type', u'name', u'title', u'department', u'location', u'description', u'startDate', u'endDate', u'primary'],
  u'placesLived': [u'value', u'primary'],
  u'urls': [u'label', u'type', u'value'],
  }

def _showGplusProfile(user, i, count, result):
  def _showProfileObject(object_name, object_value, object_order=None, level=0):
    if object_name != None:
      printJSONKey(object_name)
    if isinstance(object_value, list):
      if object_name != None:
        printBlankLine()
        incrementIndentLevel()
      for sub_value in object_value:
        if isinstance(sub_value, (str, unicode, int, bool)):
          printKeyValueList([sub_value])
        else:
          _showProfileObject(None, sub_value, object_order=PROFILE_ARRAY_PROPERTY_PRINT_ORDER[object_name], level=level+1)
      if object_name != None:
        decrementIndentLevel()
    elif isinstance(object_value, dict):
      indentAfterFirst = unindentAfterLast = False
      if object_name != None:
        printBlankLine()
        incrementIndentLevel()
      elif level > 0:
        indentAfterFirst = unindentAfterLast = True
      for sub_object in object_order or PROFILE_ARRAY_PROPERTY_PRINT_ORDER[object_name]:
        value = object_value.get(sub_object)
        if value != None:
          _showProfileObject(sub_object, value, level=level+1)
          if indentAfterFirst:
            incrementIndentLevel()
            indentAfterFirst = False
      if object_name != None or unindentAfterLast:
        decrementIndentLevel()
    else:
      if object_name in [u'aboutMe',]:
        printJSONValue(dehtml(object_value))
      else:
        printJSONValue(object_value)

  enabled = result[u'isPlusUser']
  printEntityItemValue(EN_USER, user, EN_GPLUS_PROFILE, result[u'id'], i, count)
  incrementIndentLevel()
  printKeyValueList([u'isPlusUser', enabled])
  for item in PROFILE_PROPERTY_PRINT_ORDER:
    value = result.get(item)
    if value != None:
      _showProfileObject(item, value)
  decrementIndentLevel()

# gam <UserTypeEntity> print gplusprofile [todrive]
def printGplusProfile(users):
  printShowGplusProfile(users, True)

# gam <UserTypeEntity> show gplusprofile
def showGplusProfile(users):
  printShowGplusProfile(users, False)

def printShowGplusProfile(users, csvFormat):
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile(None)
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gplus = buildGplusGAPIObject(user)
    if not gplus:
      continue
    if csvFormat:
      printGettingEntityItemForWhom(EN_GPLUS_PROFILE, user, i, count)
    try:
      results = callGAPI(gplus.people(), u'get',
                         throw_reasons=GAPI_GPLUS_THROW_REASONS,
                         userId=u'me')
      if not csvFormat:
        _showGplusProfile(user, i, count, results)
      else:
        row = {u'emailAddress': user}
        addRowTitlesToCSVfile(flattenJSON(results, flattened=row), csvRows, titles)
    except GAPI_serviceNotAvailable:
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
  if csvFormat:
    sortCSVTitles([u'emailAddress', u'id', u'displayName', u'domain'], titles)
    writeCSVfile(csvRows, titles, u'Gplus Profiles', todrive)
#
def _getUserGmailLabels(gmail, user, i, count, **kwargs):
  try:
    labels = callGAPI(gmail.users().labels(), u'list',
                      throw_reasons=GAPI_GMAIL_THROW_REASONS,
                      userId=u'me', **kwargs)
    if not labels:
      labels = {u'labels': []}
    return labels
  except (GAPI_serviceNotAvailable, GAPI_badRequest):
    entityServiceNotApplicableWarning(EN_USER, user, i, count)
    return None

def _getLabelId(labels, labelName):
  for label in labels[u'labels']:
    if label[u'id'] == labelName or label[u'name'] == labelName:
      return label[u'id']
  return labelName

def _getLabelName(labels, labelId):
  for label in labels[u'labels']:
    if label[u'id'] == labelId:
      return label[u'name']
  return labelId

LABEL_LABEL_LIST_VISIBILITY_CHOICES_MAP = {
  u'hide': u'labelHide',
  u'show': u'labelShow',
  u'showifunread': u'labelShowIfUnread',
  }
LABEL_MESSAGE_LIST_VISIBILITY_CHOICES = [u'hide', u'show',]

# gam <UserTypeEntity> [add] label|labels <Name> [messagelistvisibility hide|show] [labellistvisibility hide|show|showifunread]
def addLabel(users):
  label = getString(OB_LABEL_NAME)
  body = {u'name': label}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'labellistvisibility':
      body[u'labelListVisibility'] = getChoice(LABEL_LABEL_LIST_VISIBILITY_CHOICES_MAP, mapChoice=True)
    elif myarg == u'messagelistvisibility':
      body[u'messageListVisibility'] = getChoice(LABEL_MESSAGE_LIST_VISIBILITY_CHOICES)
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    try:
      callGAPI(gmail.users().labels(), u'create',
               throw_reasons=GAPI_GMAIL_THROW_REASONS+[GAPI_DUPLICATE],
               userId=u'me', body=body)
      entityItemValueActionPerformed(EN_USER, user, EN_LABEL, label, i, count)
    except GAPI_duplicate:
      entityItemValueActionFailedWarning(EN_USER, user, EN_LABEL, label, PHRASE_DUPLICATE, i, count)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> update labelsettings <LabelName> [name <Name>] [messagelistvisibility hide|show] [labellistvisibility hide|show|showifunread]
def updateLabelSettings(users):
  label_name = getString(OB_LABEL_NAME)
  label_name_lower = label_name.lower()
  body = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'name':
      body[u'name'] = getString(OB_STRING)
    elif myarg == u'messagelistvisibility':
      body[u'messageListVisibility'] = getChoice(LABEL_MESSAGE_LIST_VISIBILITY_CHOICES)
    elif myarg == u'labellistvisibility':
      body[u'labelListVisibility'] = getChoice(LABEL_LABEL_LIST_VISIBILITY_CHOICES_MAP, mapChoice=True)
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = _getUserGmailLabels(gmail, user, i, count, fields=u'labels(id,name)')
    if not labels:
      continue
    try:
      for label in labels[u'labels']:
        if label[u'name'].lower() == label_name_lower:
          callGAPI(gmail.users().labels(), u'patch',
                   throw_reasons=GAPI_GMAIL_THROW_REASONS+[GAPI_NOT_FOUND],
                   userId=u'me', id=label[u'id'], body=body)
          break
      else:
        entityItemValueActionFailedWarning(EN_USER, user, EN_LABEL, label_name, PHRASE_DOES_NOT_EXIST, i, count)
    except GAPI_notFound:
      entityItemValueActionFailedWarning(EN_USER, user, EN_LABEL, label_name, PHRASE_DOES_NOT_EXIST, i, count)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
#
LABEL_TYPE_SYSTEM = u'system'
LABEL_TYPE_USER = u'user'

# gam <UserTypeEntity> update label|labels [search <RegularExpression>] [replace <LabelReplacement>] [merge]
#	search defaults to '^Inbox/(.*)$' which will find all labels in the Inbox
#	replace defaults to '%s'
def updateLabels(users):
  search = u'^Inbox/(.*)$'
  replace = u'%s'
  merge = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'search':
      search = getString(OB_RE_PATTERN)
    elif myarg == u'replace':
      replace = getString(OB_LABEL_REPLACEMENT)
    elif myarg == u'merge':
      merge = True
    else:
      unknownArgumentExit()
  pattern = re.compile(search, re.IGNORECASE)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = _getUserGmailLabels(gmail, user, i, count, fields=u'labels(id,name,type)')
    if not labels:
      continue
    try:
      labelMatches = 0
      for label in labels[u'labels']:
        if label[u'type'] == LABEL_TYPE_SYSTEM:
          continue
        match_result = pattern.search(label[u'name'])
        if match_result != None:
          labelMatches += 1
          newLabelName = replace % match_result.groups()
          newLabelNameLower = newLabelName.lower()
          try:
            setActionName(AC_RENAME)
            callGAPI(gmail.users().labels(), u'patch',
                     throw_reasons=[GAPI_ABORTED, GAPI_DUPLICATE],
                     userId=u'me', id=label[u'id'], body={u'name': newLabelName})
            entityItemValueModifierNewValueActionPerformed(EN_USER, user, EN_LABEL, label[u'name'], AC_MODIFIER_TO, newLabelName, i, count)
          except (GAPI_aborted, GAPI_duplicate):
            if merge:
              setActionName(AC_MERGE)
              entityPerformActionItemValueModifierNewValue(EN_USER, user, EN_LABEL, label[u'name'], AC_MODIFIER_WITH, newLabelName, i, count)
              messagesToRelabel = callGAPIpages(gmail.users().messages(), u'list', u'messages',
                                                userId=u'me', q=u'label:"{0}"'.format(label[u'name']))
              setActionName(AC_RELABEL)
              jcount = len(messagesToRelabel)
              incrementIndentLevel()
              if jcount > 0:
                for new_label in labels[u'labels']:
                  if new_label[u'name'].lower() == newLabelNameLower:
                    body = {u'addLabelIds': [new_label[u'id']]}
                    break
                j = 0
                for message in messagesToRelabel:
                  j += 1
                  callGAPI(gmail.users().messages(), u'modify',
                           userId=u'me', id=message[u'id'], body=body)
                  entityItemValueActionPerformed(EN_USER, user, EN_MESSAGE, message[u'id'], j, jcount)
              else:
                printEntityKVList(EN_USER, user,
                                  [PHRASE_NO_MESSAGES_WITH_LABEL, label[u'name']],
                                  i, count)
              decrementIndentLevel()
              callGAPI(gmail.users().labels(), u'delete',
                       userId=u'me', id=label[u'id'])
              setActionName(AC_DELETE)
              entityItemValueActionPerformed(EN_USER, user, EN_LABEL, label[u'name'], i, count)
            else:
              entityItemValueActionNotPerformedWarning(EN_USER, user, EN_LABEL, newLabelName, PHRASE_ALREADY_EXISTS_USE_MERGE_ARGUMENT, i, count)
      if labels and (labelMatches == 0):
        printEntityKVList(EN_USER, user,
                          [PHRASE_NO_LABELS_MATCH, search],
                          i, count)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> delete|del label|labels <LabelName>|regex:<RegularExpression>
def deleteLabel(users):
  def _handleProcessGmailError(exception, ri):
    http_status, reason, message = checkGAPIError(exception)
    entityItemValueActionFailedWarning(EN_USER, ri[RI_ENTITY], EN_LABEL, ri[RI_ITEM], formatHTTPError(http_status, reason, message), int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _callbackDeleteLabel(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      entityItemValueActionPerformed(EN_USER, ri[RI_ENTITY], EN_LABEL, ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      _handleProcessGmailError(exception, ri)

  def _batchDeleteLabels(gmail, user, del_labels, i, count):
    jcount = len(del_labels)
    entityPerformActionNumItems(EN_USER, user, jcount, EN_LABEL, i, count)
    incrementIndentLevel()
    dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackDeleteLabel)
    bcount = 0
    j = 0
    for del_me in del_labels:
      j += 1
      parameters = dict([(u'userId', u'me'), (u'id', del_me[u'id'])]+GM_Globals[GM_EXTRA_ARGS_LIST])
      dbatch.add(gmail.users().labels().delete(**parameters), request_id=batchRequestID(user, i, count, j, jcount, del_me[u'name']))
      bcount += 1
      if bcount == 10:
        dbatch.execute()
        dbatch = googleapiclient.http.BatchHttpRequest(callback=_callbackDeleteLabel)
        bcount = 0
    if bcount > 0:
      dbatch.execute()
    decrementIndentLevel()

  label = getString(OB_LABEL_NAME)
  label_name_lower = label.lower()
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    try:
      printGettingAllEntityItemsForWhom(EN_LABEL, user, i, count)
      labels = _getUserGmailLabels(gmail, user, i, count, fields=u'labels(id,name,type)')
      if not labels:
        continue
      del_labels = []
      if label == u'--ALL_LABELS--':
        count = len(labels[u'labels'])
        for del_label in labels[u'labels']:
          if del_label[u'type'] == LABEL_TYPE_SYSTEM:
            continue
          del_labels.append(del_label)
      elif label[:6].lower() == u'regex:':
        regex = label[6:]
        p = re.compile(regex)
        for del_label in labels[u'labels']:
          if del_label[u'type'] == LABEL_TYPE_SYSTEM:
            continue
          elif p.match(del_label[u'name']):
            del_labels.append(del_label)
      else:
        for del_label in labels[u'labels']:
          if label_name_lower == del_label[u'name'].lower():
            del_labels.append(del_label)
            break
        else:
          entityItemValueActionFailedWarning(EN_USER, user, EN_LABEL, label, PHRASE_DOES_NOT_EXIST, i, count)
          continue
      _batchDeleteLabels(gmail, user, del_labels, i, count)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> show labels|label [onlyuser] [showcounts]
def showLabels(users):
  onlyUser = showCounts = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'onlyuser':
      onlyUser = True
    elif myarg == u'showcounts':
      showCounts = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = _getUserGmailLabels(gmail, user, i, count)
    if not labels:
      continue
    try:
      jcount = len(labels[u'labels'])
      if (jcount > 0) and onlyUser:
        for label in labels[u'labels']:
          if label[u'type'] == LABEL_TYPE_SYSTEM:
            jcount -= 1
      entityPerformActionNumItems(EN_USER, user, jcount, EN_LABEL, i, count)
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
        continue
      incrementIndentLevel()
      for label in labels[u'labels']:
        if onlyUser and (label[u'type'] == LABEL_TYPE_SYSTEM):
          continue
        printKeyValueList([label[u'name']])
        incrementIndentLevel()
        for a_key in label:
          if a_key != u'name':
            printKeyValueList([a_key, label[a_key]])
        if showCounts:
          counts = callGAPI(gmail.users().labels(), u'get',
                            throw_reasons=GAPI_GMAIL_THROW_REASONS,
                            userId=u'me', id=label[u'id'],
                            fields=u'messagesTotal,messagesUnread,threadsTotal,threadsUnread')
          for a_key in counts:
            printKeyValueList([a_key, counts[a_key]])
        decrementIndentLevel()
      decrementIndentLevel()
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> delete message|messages (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_delete <Number>])|(ids <MessageIDEntity>)
# gam <UserTypeEntity> modify message|messages (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_modify <Number>])|(ids <MessageIDEntity>) (addlabel <LabelName>)* (removelabel <LabelName>)*
# gam <UserTypeEntity> spam message|messages (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_spam <Number>])|(ids <MessageIDEntity>)
# gam <UserTypeEntity> trash message|messages (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_trash <Number>])|(ids <MessageIDEntity>)
# gam <UserTypeEntity> untrash message|messages (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_untrash <Number>])|(ids <MessageIDEntity>)
def processMessages(users):
  processMessagesThreads(users, EN_MESSAGE)

# gam <UserTypeEntity> delete thread|threads (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_delete <Number>])|(ids <ThreadIDEntity>)
# gam <UserTypeEntity> modify thread|threads (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_modify <Number>])|(ids <ThreadIDEntity>) (addlabel <LabelName>)* (removelabel <LabelName>)*
# gam <UserTypeEntity> spam thread|threads (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_spam <Number>])|(ids <ThreadIDEntity>)
# gam <UserTypeEntity> trash thread|threads (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_trash <Number>])|(ids <MessageIDEntity>)
# gam <UserTypeEntity> untrash thread|threads (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [doit] [max_to_untrash <Number>])|(ids <ThreadIDEntity>)
def processThreads(users):
  processMessagesThreads(users, EN_THREAD)

def processMessagesThreads(users, entityType):
  def _initLabelNameMap():
    baseLabelNameMap = {
      u'INBOX': u'INBOX', u'SPAM': u'SPAM', u'TRASH': u'TRASH',
      u'UNREAD': u'UNREAD', u'STARRED': u'STARRED', u'IMPORTANT': u'IMPORTANT',
      u'SENT': u'SENT', u'DRAFT': u'DRAFT',
      u'CATEGORY_PERSONAL': u'CATEGORY_PERSONAL',
      u'CATEGORY_SOCIAL': u'CATEGORY_SOCIAL',
      u'CATEGORY_PROMOTIONS': u'CATEGORY_PROMOTIONS',
      u'CATEGORY_UPDATES': u'CATEGORY_UPDATES',
      u'CATEGORY_FORUMS': u'CATEGORY_FORUMS',
      }

    labelNameMap = baseLabelNameMap.copy()
    for label in userGmailLabels[u'labels']:
      if label[u'type'] == u'system':
        labelNameMap[label[u'id']] = label[u'id']
      else:
        labelNameMap[label[u'name']] = label[u'id']
    return labelNameMap

  def _convertLabelNamesToIds(bodyLabels, labelNameMap, addLabelIfMissing):
    labelIds = []
    for label in bodyLabels:
      if label not in labelNameMap:
        results = callGAPI(gmail.users().labels(), u'create',
                           userId=u'me', body={u'labelListVisibility': u'labelShow', u'messageListVisibility': u'show', u'name': label}, fields=u'id')
        labelNameMap[label] = results[u'id']
      try:
        labelIds.append(labelNameMap[label])
      except KeyError:
        pass
      if addLabelIfMissing:
        if label.find(u'/') != -1:
          # make sure to create parent labels for proper nesting
          parent_label = label[:label.rfind(u'/')]
          while True:
            if not parent_label in labelNameMap:
              result = callGAPI(gmail.users().labels(), u'create',
                                userId=u'me', body={u'name': parent_label})
              labelNameMap[parent_label] = result[u'id']
            if parent_label.find(u'/') == -1:
              break
            parent_label = parent_label[:parent_label.rfind(u'/')]
    return labelIds

  def _deleteMessageBatch(gmail, user, i, count, messageIds, mcount, jcount):
    try:
      callGAPI(gmail.users().messages(), u'batchDelete',
               throw_reasons=GAPI_GMAIL_THROW_REASONS,
               userId=u'me', body={u'ids': messageIds})
      entityItemValueActionPerformed(EN_USER, user, entityType, u'{0} of {1}'.format(mcount, jcount), i, count)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      pass

  def _batchDeleteMessages(gmail, user, jcount, messageIds, i, count):
    mcount = 0
    delMessageIds = []
    bcount = 0
    for message in messageIds:
      delMessageIds.append(message[u'id'])
      bcount += 1
      if bcount == GC_Values[GC_EMAIL_BATCH_SIZE]:
        mcount += bcount
        _deleteMessageBatch(gmail, user, i, count, delMessageIds, mcount, jcount)
        delMessageIds = []
        bcount = 0
    if bcount > 0:
      mcount += bcount
      _deleteMessageBatch(gmail, user, i, count, delMessageIds, mcount, jcount)

  def _handleProcessGmailError(exception, ri):
    REASON_TO_MESSAGE_MAP = {GAPI_NOT_FOUND: PHRASE_DOES_NOT_EXIST}
    http_status, reason, message = checkGAPIError(exception)
    errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
    entityItemValueActionFailedWarning(EN_USER, ri[RI_ENTITY], entityType, ri[RI_ITEM], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _callbackProcessMessage(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      entityItemValueActionPerformed(EN_USER, ri[RI_ENTITY], entityType, ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      _handleProcessGmailError(exception, ri)

  def _batchProcessMessagesThreads(service, function, user, jcount, messageIds, i, count, callback, **kwargs):
    method = getattr(service, function)
    dbatch = googleapiclient.http.BatchHttpRequest(callback=callback)
    bcount = 0
    j = 0
    for message in messageIds:
      j += 1
      parameters = dict([(u'userId', u'me'), (u'id', message[u'id'])]+kwargs.items()+GM_Globals[GM_EXTRA_ARGS_LIST])
      dbatch.add(method(**parameters), request_id=batchRequestID(user, i, count, j, jcount, message[u'id']))
      bcount += 1
      if bcount == GC_Values[GC_EMAIL_BATCH_SIZE]:
        dbatch.execute()
        dbatch = googleapiclient.http.BatchHttpRequest(callback=callback)
        bcount = 0
    if bcount > 0:
      dbatch.execute()

  currLabelOp = prevLabelOp = u'and'
  labelGroupOpen = False
  query = u''
  includeSpamTrash = False
  labelNameMap = {}
  doIt = quick = False
  maxToProcess = 1
  function = {AC_DELETE: u'delete', AC_MODIFY: u'modify', AC_SPAM: u'modify', AC_TRASH: u'trash', AC_UNTRASH: u'untrash'}[GM_Globals[GM_ACTION_COMMAND]]
  addLabelNames = []
  removeLabelNames = []
  messageIds = None
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'query':
      query += u' ({0})'.format(getString(OB_QUERY))
    elif myarg == u'matchlabel':
      labelName = getString(OB_LABEL_NAME).lower().replace(u' ', u'-').replace(u'/', u'-')
      if not labelGroupOpen:
        query += u'('
        labelGroupOpen = True
      query += u' label:{0}'.format(labelName)
    elif myarg in [u'or', u'and']:
      prevLabelOp = currLabelOp
      currLabelOp = myarg
      if labelGroupOpen and currLabelOp != prevLabelOp:
        query += u')'
        labelGroupOpen = False
      if currLabelOp == u'or':
        query += u' OR '
    elif myarg == u'ids':
      messageIds = getEntityList(OB_MESSAGE_ID)
    elif myarg == u'quick':
      quick = True
    elif myarg == u'notquick':
      quick = False
    elif myarg == u'doit':
      doIt = True
    elif myarg in [u'maxtodelete', u'maxtomodify', u'maxtospam', u'maxtotrash', u'maxtountrash', u'maxtoprocess']:
      maxToProcess = getInteger(minVal=0)
    elif (function == u'modify') and (myarg == u'addlabel'):
      addLabelNames.append(getString(OB_LABEL_NAME))
    elif (function == u'modify') and (myarg == u'removelabel'):
      removeLabelNames.append(getString(OB_LABEL_NAME))
    else:
      unknownArgumentExit()
  if query:
    if labelGroupOpen:
      query += u')'
  elif messageIds == None:
    missingArgumentExit(u'query|matchlabel|ids')
  listType = [u'threads', u'messages'][entityType == EN_MESSAGE]
  userMessageLists = messageIds if isinstance(messageIds, dict) else None
  includeSpamTrash = GM_Globals[GM_ACTION_COMMAND] in [AC_DELETE, AC_MODIFY, AC_UNTRASH]
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if userMessageLists:
      messageIds = userMessageLists[user]
    if messageIds != None:
      listResult = [{u'id': messageId} for messageId in messageIds]
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    service = [gmail.users().threads(), gmail.users().messages()][entityType == EN_MESSAGE]
    try:
      if addLabelNames or removeLabelNames:
        userGmailLabels = _getUserGmailLabels(gmail, user, i, count, fields=u'labels(id,name,type)')
        if not userGmailLabels:
          continue
        labelNameMap = _initLabelNameMap()
        addLabelIds = _convertLabelNamesToIds(addLabelNames, labelNameMap, True)
        removeLabelIds = _convertLabelNamesToIds(removeLabelNames, labelNameMap, False)
      if messageIds == None:
        printGettingAllEntityItemsForWhom(EN_MESSAGE, user, i, count)
        page_message = getPageMessage()
        listResult = callGAPIpages(service, u'list', listType,
                                   page_message=page_message, maxItems=[0, maxToProcess][quick],
                                   throw_reasons=GAPI_GMAIL_THROW_REASONS,
                                   userId=u'me', q=query, includeSpamTrash=includeSpamTrash, maxResults=500)
      else:
        # Neded to get authorization set up for batch
        callGAPI(gmail.users(), u'getProfile',
                 throw_reasons=GAPI_GMAIL_THROW_REASONS,
                 userId=u'me')
      jcount = len(listResult)
      if jcount == 0:
        entityNumEntitiesActionNotPerformedWarning(EN_USER, user, entityType, jcount, PHRASE_NO_ENTITIES_MATCHED.format(pluralEntityName(entityType)), i, count)
        setSysExitRC(NO_ENTITIES_FOUND)
        continue
      if messageIds == None:
        if maxToProcess and jcount > maxToProcess:
          entityNumEntitiesActionNotPerformedWarning(EN_USER, user, entityType, jcount, PHRASE_COUNT_N_EXCEEDS_MAX_TO_PROCESS_M.format(jcount, GM_Globals[GM_ACTION_TO_PERFORM], maxToProcess), i, count)
          continue
        if not doIt:
          entityNumEntitiesActionNotPerformedWarning(EN_USER, user, entityType, jcount, PHRASE_USE_DOIT_ARGUMENT_TO_PERFORM_ACTION, i, count)
          continue
      entityPerformActionNumItems(EN_USER, user, jcount, entityType, i, count)
      incrementIndentLevel()
      if function == u'delete' and entityType == EN_MESSAGE:
        _batchDeleteMessages(gmail, user, jcount, listResult, i, count)
      else:
        if GM_Globals[GM_ACTION_COMMAND] == AC_SPAM:
          kwargs = {u'body': {u'addLabelIds': [u'SPAM'], u'removeLabelIds': [u'INBOX']}}
        elif addLabelNames or removeLabelNames:
          kwargs = {u'body': {u'addLabelIds': addLabelIds, u'removeLabelIds': removeLabelIds}}
        else:
          kwargs = {}
        _batchProcessMessagesThreads(service, function, user, jcount, listResult, i, count, _callbackProcessMessage, **kwargs)
      decrementIndentLevel()
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

SMTP_HEADERS_MAP = {
  u'accept-language': u'Accept-Language',
  u'alternate-recipient': u'Alternate-Recipient',
  u'autoforwarded': u'Autoforwarded',
  u'autosubmitted': u'Autosubmitted',
  u'bcc': u'Bcc',
  u'cc': u'Cc',
  u'comments': u'Comments',
  u'content-alternative': u'Content-Alternative',
  u'content-base': u'Content-Base',
  u'content-description': u'Content-Description',
  u'content-disposition': u'Content-Disposition',
  u'content-duration': u'Content-Duration',
  u'content-id': u'Content-ID',
  u'content-identifier': u'Content-Identifier',
  u'content-language': u'Content-Language',
  u'content-location': u'Content-Location',
  u'content-md5': u'Content-MD5',
  u'content-return': u'Content-Return',
  u'content-transfer-encoding': u'Content-Transfer-Encoding',
  u'content-type': u'Content-Type',
  u'content-features': u'Content-features',
  u'conversion': u'Conversion',
  u'conversion-with-loss': u'Conversion-With-Loss',
  u'dl-expansion-history': u'DL-Expansion-History',
  u'date': u'Date',
  u'deferred-delivery': u'Deferred-Delivery',
  u'delivered-to': u'Delivered-To',
  u'delivery-date': u'Delivery-Date',
  u'discarded-x400-ipms-extensions': u'Discarded-X400-IPMS-Extensions',
  u'discarded-x400-mts-extensions': u'Discarded-X400-MTS-Extensions',
  u'disclose-recipients': u'Disclose-Recipients',
  u'disposition-notification-options': u'Disposition-Notification-Options',
  u'disposition-notification-to': u'Disposition-Notification-To',
  u'encoding': u'Encoding',
  u'encrypted': u'Encrypted',
  u'expires': u'Expires',
  u'expiry-date': u'Expiry-Date',
  u'from': u'From',
  u'generate-delivery-report': u'Generate-Delivery-Report',
  u'importance': u'Importance',
  u'in-reply-to': u'In-Reply-To',
  u'incomplete-copy': u'Incomplete-Copy',
  u'keywords': u'Keywords',
  u'language': u'Language',
  u'latest-delivery-time': u'Latest-Delivery-Time',
  u'list-archive': u'List-Archive',
  u'list-help': u'List-Help',
  u'list-id': u'List-ID',
  u'list-owner': u'List-Owner',
  u'list-post': u'List-Post',
  u'list-subscribe': u'List-Subscribe',
  u'list-unsubscribe': u'List-Unsubscribe',
  u'mime-version': u'MIME-Version',
  u'message-context': u'Message-Context',
  u'message-id': u'Message-ID',
  u'message-type': u'Message-Type',
  u'obsoletes': u'Obsoletes',
  u'original-encoded-information-types': u'Original-Encoded-Information-Types',
  u'original-message-id': u'Original-Message-ID',
  u'originator-return-address': u'Originator-Return-Address',
  u'pics-label': u'PICS-Label',
  u'prevent-nondelivery-report': u'Prevent-NonDelivery-Report',
  u'priority': u'Priority',
  u'received': u'Received',
  u'references': u'References',
  u'reply-by': u'Reply-By',
  u'reply-to': u'Reply-To',
  u'resent-bcc': u'Resent-Bcc',
  u'resent-cc': u'Resent-Cc',
  u'resent-date': u'Resent-Date',
  u'resent-from': u'Resent-From',
  u'resent-message-id': u'Resent-Message-ID',
  u'resent-reply-to': u'Resent-Reply-To',
  u'resent-sender': u'Resent-Sender',
  u'resent-to': u'Resent-To',
  u'return-path': u'Return-Path',
  u'sender': u'Sender',
  u'sensitivity': u'Sensitivity',
  u'subject': u'Subject',
  u'supersedes': u'Supersedes',
  u'to': u'To',
  u'x400-content-identifier': u'X400-Content-Identifier',
  u'x400-content-return': u'X400-Content-Return',
  u'x400-content-type': u'X400-Content-Type',
  u'x400-mts-identifier': u'X400-MTS-Identifier',
  u'x400-originator': u'X400-Originator',
  u'x400-received': u'X400-Received',
  u'x400-recipients': u'X400-Recipients',
  u'x400-trace': u'X400-Trace',
  }

# gam <UserTypeEntity> print message|messages (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])* [quick|notquick] [max_to_show <Number>] [includespamtrash])|(ids <MessageIDEntity>) [headers <String>] [showlabels] [showsize] [showsnippet] [todrive]
def printMessages(users):
  printShowMessagesThreads(users, EN_MESSAGE, True)

# gam <UserTypeEntity> print thread|threads (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])* [quick|notquick] [max_to_show <Number>] [includespamtrash])|(ids <ThreadIDEntity>) [headers <String>] [showlabels] [showsize] [showsnippet] [todrive]GAMADVNOTOLD>
def printThreads(users):
  printShowMessagesThreads(users, EN_THREAD, True)

# gam <UserTypeEntity> show message|messages (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])* [quick|notquick] [max_to_show <Number>] [includespamtrash])|(ids <MessageIDEntity>) [headers <String>] [showlabels] [showsize] [showsnippet]
def showMessages(users):
  printShowMessagesThreads(users, EN_MESSAGE, False)

# gam <UserTypeEntity> show thread|threads (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])* [quick|notquick] [max_to_show <Number>] [includespamtrash])|(ids <ThreadIDEntity>) [headers <String>] [showlabels] [showsize] [showsnippet]
def showThreads(users):
  printShowMessagesThreads(users, EN_THREAD, False)

def printShowMessagesThreads(users, entityType, csvFormat):

  def _handleShowGmailError(exception, ri):
    REASON_TO_MESSAGE_MAP = {GAPI_NOT_FOUND: PHRASE_DOES_NOT_EXIST}
    http_status, reason, message = checkGAPIError(exception)
    errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
    printKeyValueListWithCount([singularEntityName(entityType), ri[RI_ITEM], errMsg], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    setSysExitRC(AC_FAILED_RC)

  def _handlePrintGmailError(exception, ri):
    REASON_TO_MESSAGE_MAP = {GAPI_NOT_FOUND: PHRASE_DOES_NOT_EXIST}
    http_status, reason, message = checkGAPIError(exception)
    errMsg = getHTTPError(REASON_TO_MESSAGE_MAP, http_status, reason, message)
    entityItemValueActionFailedWarning(EN_USER, ri[RI_ENTITY], entityType, ri[RI_ITEM], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _showMessage(result, j, jcount):
    printEntityName(EN_MESSAGE, result[u'id'], j, jcount)
    incrementIndentLevel()
    if show_snippet:
      printKeyValueList([u'Snippet', dehtml(result[u'snippet']).replace(u'\n', u' ')])
    for name in headersToShow:
      for header in result[u'payload'][u'headers']:
        if name == header[u'name'].lower():
          printKeyValueList([SMTP_HEADERS_MAP.get(name, header[u'name']), header[u'value']])
    if show_size:
      printKeyValueList([u'SizeEstimate', result[u'sizeEstimate']])
    if show_labels:
      messageLabels = []
      for labelId in result[u'labelIds']:
        for label in labels[u'labels']:
          if label[u'id'] == labelId:
            messageLabels.append(label[u'name'])
            break
      printKeyValueList([u'Labels', u','.join(messageLabels)])
    decrementIndentLevel()

  def _callbackShowMessage(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is  None:
      _showMessage(response, int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      _handleShowGmailError(exception, ri)

  def _printMessage(user, result):
    row = {u'User': user, u'threadId': result[u'threadId'], u'id': result[u'id']}
    if show_snippet:
      row[u'Snippet'] = dehtml(result[u'snippet']).replace(u'\n', u' ')
    for name in headersToShow:
      j = 0
      for header in result[u'payload'][u'headers']:
        if name == header[u'name'].lower():
          j += 1
          if j == 1:
            row[SMTP_HEADERS_MAP.get(name, header[u'name'])] = header[u'value']
          else:
            row[u'{0} {1}'.format(SMTP_HEADERS_MAP.get(name, header[u'name']), j)] = header[u'value']
    if show_size:
      row[u'SizeEstimate'] = result[u'sizeEstimate']
    if show_labels:
      messageLabels = []
      for labelId in result[u'labelIds']:
        for label in labels[u'labels']:
          if label[u'id'] == labelId:
            messageLabels.append(label[u'name'])
            break
      row[u'Labels'] = u','.join(messageLabels)
    addRowTitlesToCSVfile(row, csvRows, titles)

  def _callbackPrintMessage(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      _printMessage(ri[RI_ENTITY], response)
    else:
      _handlePrintGmailError(exception, ri)

  def _showThread(result, j, jcount):
    printEntityName(EN_THREAD, result[u'id'], j, jcount)
    incrementIndentLevel()
    if show_snippet and u'snippet' in result:
      printKeyValueList([u'Snippet', dehtml(result[u'snippet']).replace(u'\n', u' ')])
    try:
      result = callGAPI(service, u'get',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS+[GAPI_NOT_FOUND],
                        id=result[u'id'], userId=u'me', format=u'metadata')
      kcount = len(result[u'messages'])
      k = 0
      for message in result[u'messages']:
        k += 1
        _showMessage(message, k, kcount)
    except (GAPI_serviceNotAvailable, GAPI_badRequest, GAPI_notFound):
      pass
    decrementIndentLevel()

  def _callbackShowThread(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      _showThread(response, int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      _handleShowGmailError(exception, ri)

  def _printThread(user, result):
    try:
      result = callGAPI(service, u'get',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS+[GAPI_NOT_FOUND],
                        id=result[u'id'], userId=u'me', format=u'metadata')
      for message in result[u'messages']:
        _printMessage(user, message)
    except (GAPI_serviceNotAvailable, GAPI_badRequest, GAPI_notFound):
      pass

  def _callbackPrintThread(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      _printThread(ri[RI_ENTITY], response)
    else:
      _handlePrintGmailError(exception, ri)

  def _batchPrintShowMessagesThreads(service, user, jcount, messageIds, i, count, callback):
    dbatch = googleapiclient.http.BatchHttpRequest(callback=callback)
    bcount = 0
    j = 0
    for message in messageIds:
      j += 1
      parameters = dict([(u'userId', u'me'), (u'id', message[u'id']), (u'format', u'metadata')]+GM_Globals[GM_EXTRA_ARGS_LIST])
      dbatch.add(service.get(**parameters), request_id=batchRequestID(user, i, count, j, jcount, message[u'id']))
      bcount += 1
      if maxToProcess and j == maxToProcess:
        break
      if bcount == GC_Values[GC_EMAIL_BATCH_SIZE]:
        dbatch.execute()
        dbatch = googleapiclient.http.BatchHttpRequest(callback=callback)
        bcount = 0
    if bcount > 0:
      dbatch.execute()

  currLabelOp = prevLabelOp = u'and'
  labelGroupOpen = False
  query = u''
  includeSpamTrash = False
  quick = True
  maxToProcess = 0
  show_labels = show_size = show_snippet = False
  messageIds = None
  headersToShow = [u'Date', u'Subject', u'From', u'Reply-To', u'To', u'Delivered-To', u'Content-Type', u'Message-ID']
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile([u'User', u'threadId', u'id'])
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    elif myarg == u'query':
      query += u' ({0})'.format(getString(OB_QUERY))
    elif myarg == u'matchlabel':
      labelName = getString(OB_LABEL_NAME).lower().replace(u' ', u'-').replace(u'/', u'-')
      if not labelGroupOpen:
        query += u'('
        labelGroupOpen = True
      query += u' label:{0}'.format(labelName)
    elif myarg in [u'or', u'and']:
      prevLabelOp = currLabelOp
      currLabelOp = myarg
      if labelGroupOpen and currLabelOp != prevLabelOp:
        query += u')'
        labelGroupOpen = False
      if currLabelOp == u'or':
        query += u' OR '
    elif myarg == u'ids':
      messageIds = getEntityList(OB_MESSAGE_ID)
    elif myarg == u'quick':
      quick = True
    elif myarg == u'notquick':
      quick = False
    elif myarg in[u'maxtoprint', u'maxtoshow', u'maxtoprocess']:
      maxToProcess = getInteger(minVal=0)
    elif myarg == u'headers':
      headersToShow = getString(OB_STRING, emptyOK=True).replace(u',', u' ').split()
    elif myarg == u'showlabels':
      show_labels = True
      if csvFormat:
        addTitleToCSVfile(u'Labels', titles)
    elif myarg == u'showsize':
      show_size = True
      if csvFormat:
        addTitleToCSVfile(u'SizeEstimate', titles)
    elif myarg == u'showsnippet':
      show_snippet = True
      if csvFormat:
        addTitleToCSVfile(u'Snippet', titles)
    elif myarg == u'includespamtrash':
      includeSpamTrash = True
    else:
      unknownArgumentExit()
  if query:
    if labelGroupOpen:
      query += u')'
  else:
    query = None
  if csvFormat:
    headerTitles = []
    for j, name in enumerate(headersToShow):
      headersToShow[j] = name.lower()
      headerTitles.append(SMTP_HEADERS_MAP.get(headersToShow[j], name))
    addTitlesToCSVfile(headerTitles, titles)
  else:
    for j, name in enumerate(headersToShow):
      headersToShow[j] = name.lower()
  listType = [u'threads', u'messages'][entityType == EN_MESSAGE]
  userMessageLists = messageIds if isinstance(messageIds, dict) else None
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if userMessageLists:
      messageIds = userMessageLists[user]
    if messageIds != None:
      listResult = [{u'id': messageId} for messageId in messageIds]
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    service = [gmail.users().threads(), gmail.users().messages()][entityType == EN_MESSAGE]
    try:
      if show_labels:
        labels = _getUserGmailLabels(gmail, user, i, count, fields=u'labels(id,name)')
        if not labels:
          continue
      if messageIds == None:
        printGettingAllEntityItemsForWhom(entityType, user, i, count)
        page_message = getPageMessage()
        listResult = callGAPIpages(service, u'list', listType,
                                   page_message=page_message, maxItems=[0, maxToProcess][quick],
                                   throw_reasons=GAPI_GMAIL_THROW_REASONS,
                                   userId=u'me', q=query, includeSpamTrash=includeSpamTrash, maxResults=500)
      else:
        # Neded to get authorization set up for batch
        callGAPI(gmail.users(), u'getProfile',
                 throw_reasons=GAPI_GMAIL_THROW_REASONS,
                 userId=u'me')
      jcount = len(listResult)
      if jcount == 0:
        if not csvFormat:
          entityNumEntitiesActionNotPerformedWarning(EN_USER, user, entityType, jcount, PHRASE_NO_ENTITIES_MATCHED.format(pluralEntityName(entityType)), i, count)
        setSysExitRC(NO_ENTITIES_FOUND)
        continue
      if not csvFormat:
        if messageIds or maxToProcess == 0 or jcount <= maxToProcess:
          entityPerformActionNumItems(EN_USER, user, jcount, entityType, i, count)
        else:
          entityPerformActionNumItemsModifier(EN_USER, user, maxToProcess, entityType, u'of {0} Total {1}'.format(jcount, pluralEntityName(entityType)), i, count)
      if messageIds == None and maxToProcess and (jcount > maxToProcess):
        jcount = maxToProcess
      if not csvFormat:
        incrementIndentLevel()
        _batchPrintShowMessagesThreads(service, user, jcount, listResult, i, count, [_callbackShowThread, _callbackShowMessage][entityType == EN_MESSAGE])
        decrementIndentLevel()
      else:
        _batchPrintShowMessagesThreads(service, user, jcount, listResult, i, count, [_callbackPrintThread, _callbackPrintMessage][entityType == EN_MESSAGE])
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
  if csvFormat:
    writeCSVfile(csvRows, titles, u'Messages', todrive)

# Process Email Settings
def _processEmailSettings(user, i, count, service, function, **kwargs):
  try:
    return callGData(service, function,
                     throw_errors=GDATA_EMAILSETTINGS_THROW_LIST,
                     **kwargs)
  except GData_doesNotExist:
    entityActionFailedWarning(EN_USER, user, PHRASE_DOES_NOT_EXIST, i, count)
  except (GData_serviceNotApplicable, GData_invalidDomain):
    entityServiceNotApplicableWarning(EN_USER, user, i, count)
  except (GData_badRequest, GData_internalServerError, GData_nameNotValid, GData_invalidValue) as e:
    if u'forward_to' in kwargs:
      entityItemValueActionFailedWarning(EN_USER, user, EN_FORWARDING_ADDRESS, kwargs[u'forward_to'], PHRASE_DOES_NOT_EXIST_OR_NOT_ALLOWED, i, count)
    else:
      entityBadRequestWarning(EN_USER, user, EN_EMAIL_SETTINGS, None, e.message, i, count)
  return None

# gam <UserTypeEntity> arrows <Boolean>
def setArrows(users):
  emailSettings = getEmailSettingsObject()
  enable = getBoolean()
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, userName, emailSettings.domain = splitEmailAddressOrUID(user)
    result = _processEmailSettings(user, i, count, emailSettings, u'UpdateGeneral',
                                   username=userName, arrows=enable)
    if result:
      printEntityItemValue(EN_USER, user, EN_ARROWS_ENABLED, result[u'arrows'], i, count)

# gam <UserTypeEntity> add delegate|delegates <UserEntity>
# gam <UserTypeEntity> delegate|delegates to <UserEntity>
def addDelegate(users):
  delegateTo(users, checkForTo=False)

def delegateTo(users, checkForTo=True):
  import gdata.apps.service
  cd = buildGAPIObject(GAPI_DIRECTORY_API)
  emailSettings = getEmailSettingsObject()
  if checkForTo:
    checkArgumentPresent(TO_ARGUMENT, required=True)
  delegates = getEntityList(OB_USER_ENTITY, listOptional=True)
  userDelegateLists = delegates if isinstance(delegates, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if userDelegateLists:
      delegates = userDelegateLists[user]
    delegatorEmail, delegatorName, delegatorDomain = splitEmailAddressOrUID(user)
    emailSettings.domain = delegatorDomain
    jcount = len(delegates)
    entityPerformActionNumItems(EN_DELEGATOR, delegatorEmail, jcount, EN_DELEGATE, i, count)
    continueWithUser = True
    j = 0
    for delegate in delegates:
      j += 1
      delegateEmail, _, delegateDomain = splitEmailAddressOrUID(delegate)
      delete_alias = False
      if delegateDomain == delegatorDomain:
        use_delegate_address = delegateEmail
      else:
        # Need to use an alias in delegator domain, first check to see if delegate already has one...
        try:
          aliases = callGAPI(cd.users().aliases(), u'list',
                             throw_reasons=[GAPI_USER_NOT_FOUND, GAPI_FORBIDDEN],
                             userKey=delegateEmail)
          found_alias_in_delegator_domain = False
          if aliases:
            for alias in aliases.get(u'aliases', []):
              _, aliasDomain = splitEmailAddress(alias[u'alias'])
              if aliasDomain == delegatorDomain:
                use_delegate_address = alias[u'alias']
                printLine(u'  Using existing alias {0} for delegation'.format(use_delegate_address))
                found_alias_in_delegator_domain = True
                break
          if not found_alias_in_delegator_domain:
            delete_alias = True
            use_delegate_address = u'{0}@{1}'.format(u''.join(random.sample(u'abcdefghijklmnopqrstuvwxyz0123456789', 25)), delegatorDomain)
            printLine(u'  Giving {0} temporary alias {1} for delegation'.format(delegateEmail, use_delegate_address))
            callGAPI(cd.users().aliases(), u'insert',
                     userKey=delegateEmail, body={u'alias': use_delegate_address})
            time.sleep(5)
        except GAPI_userNotFound:
          pass
        except GAPI_forbidden:
          entityUnknownWarning(EN_DELEGATE, delegateEmail, j, jcount)
          continue
      retries = 10
      for n in range(1, retries+1):
        try:
          callGData(emailSettings, u'CreateDelegate',
                    throw_errors=[GDATA_NOT_FOUND, GDATA_INVALID_DOMAIN, GDATA_SERVICE_NOT_APPLICABLE, 1000, 1001, GDATA_DOES_NOT_EXIST, GDATA_ENTITY_EXISTS],
                    delegate=use_delegate_address, delegator=delegatorName)
          incrementIndentLevel()
          entityItemValueActionPerformed(EN_DELEGATOR, delegatorEmail, EN_DELEGATE, delegateEmail, j, jcount)
          decrementIndentLevel()
          break
        except (GData_invalidDomain, GData_serviceNotApplicable, GData_doesNotExist):
          entityServiceNotApplicableWarning(EN_DELEGATOR, delegatorEmail, i, count)
          continueWithUser = False
          break
        except GData_entityExists:
          incrementIndentLevel()
          entityActionFailedWarning(EN_DELEGATOR, delegatorEmail, entityTypeNameMessage(EN_DELEGATE, delegateEmail, PHRASE_DUPLICATE), j, jcount)
          decrementIndentLevel()
          break
        except gdata.apps.service.AppsForYourDomainException as e:
          # 1st check to see if delegation already exists (causes 1000 error on create when using alias)
          get_delegates = callGData(emailSettings, u'GetDelegates',
                                    delegator=delegatorName)
          duplicateDelegation = False
          for get_delegate in get_delegates:
            if get_delegate[u'address'].lower() == delegateEmail: # Delegation is already in place
              incrementIndentLevel()
              entityActionFailedWarning(EN_DELEGATOR, delegatorEmail, entityTypeNameMessage(EN_DELEGATE, delegateEmail, PHRASE_DUPLICATE), j, jcount)
              decrementIndentLevel()
              duplicateDelegation = True
              break
          if duplicateDelegation:
            break
          # Now check if either user account is suspended or requires password change
          delegator_user_details = callGAPI(cd.users(), u'get',
                                            userKey=delegatorEmail)
          if delegator_user_details[u'suspended']:
            entityNumEntitiesActionNotPerformedWarning(EN_DELEGATOR, delegatorEmail, EN_DELEGATE, jcount, entityTypeNameMessage(EN_DELEGATOR, delegatorEmail, PHRASE_IS_SUSPENDED_NO_DELEGATION), i, count)
            setSysExitRC(USER_SUSPENDED_ERROR_RC)
            continueWithUser = False
            break
          if delegator_user_details[u'changePasswordAtNextLogin']:
            entityNumEntitiesActionNotPerformedWarning(EN_DELEGATOR, delegatorEmail, EN_DELEGATE, jcount, entityTypeNameMessage(EN_DELEGATOR, delegatorEmail, PHRASE_IS_REQD_TO_CHG_PWD_NO_DELEGATION), i, count)
            setSysExitRC(USER_SUSPENDED_ERROR_RC)
            continueWithUser = False
            break
          delegate_user_details = callGAPI(cd.users(), u'get',
                                           userKey=delegateEmail)
          if delegate_user_details[u'suspended']:
            entityActionNotPerformedWarning(EN_DELEGATOR, delegatorEmail, entityTypeNameMessage(EN_DELEGATE, delegateEmail, PHRASE_IS_SUSPENDED_NO_DELEGATION), j, jcount)
            setSysExitRC(USER_SUSPENDED_ERROR_RC)
            break
          if delegate_user_details[u'changePasswordAtNextLogin']:
            entityActionNotPerformedWarning(EN_DELEGATOR, delegatorEmail, entityTypeNameMessage(EN_DELEGATE, delegateEmail, PHRASE_IS_REQD_TO_CHG_PWD_NO_DELEGATION), j, jcount)
            setSysExitRC(USER_SUSPENDED_ERROR_RC)
            break
          # Guess it was just a normal backoff error then?
          error_code, error_message = checkGDataError(e, emailSettings)
          if n != retries:
            waitOnFailure(n, retries, error_code, error_message)
            continue
          systemErrorExit(GOOGLE_API_ERROR_RC, u'{0} - {1}'.format(error_code, error_message))
      time.sleep(10) # on success, sleep 10 seconds before exiting or moving on to next user to prevent ghost delegates
      if delete_alias:
        deleteAliases(u'target', [use_delegate_address])
      if not continueWithUser:
        break

# gam <UserTypeEntity> delete|del delegate|delegates <UserEntity>>
def deleteDelegate(users):
  emailSettings = getEmailSettingsObject()
  delegates = getEntityList(OB_USER_ENTITY, listOptional=True)
  userDelegateLists = delegates if isinstance(delegates, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if userDelegateLists:
      delegates = userDelegateLists[user]
    delegatorEmail, delegatorName, emailSettings.domain = splitEmailAddressOrUID(user)
    jcount = len(delegates)
    entityPerformActionNumItems(EN_DELEGATOR, delegatorEmail, jcount, EN_DELEGATE, i, count)
    j = 0
    for delegate in delegates:
      j += 1
      delegateEmail = addDomainToEmailAddressOrUID(delegate, emailSettings.domain)
      if not delegateEmail:
        incrementIndentLevel()
        entityItemValueActionFailedWarning(EN_DELEGATOR, delegatorEmail, EN_DELEGATE, delegate, PHRASE_DOES_NOT_EXIST, j, jcount)
        decrementIndentLevel()
        continue
      try:
        callGData(emailSettings, u'DeleteDelegate',
                  throw_errors=GDATA_EMAILSETTINGS_THROW_LIST,
                  delegate=delegateEmail, delegator=delegatorName)
        incrementIndentLevel()
        entityItemValueActionPerformed(EN_DELEGATOR, delegatorEmail, EN_DELEGATE, delegateEmail, j, jcount)
        decrementIndentLevel()
      except GData_doesNotExist:
        entityUnknownWarning(EN_DELEGATOR, delegatorEmail, i, count)
        break
      except (GData_serviceNotApplicable, GData_invalidDomain):
        entityServiceNotApplicableWarning(EN_DELEGATOR, delegatorEmail, i, count)
        break
      except GData_nameNotValid:
        incrementIndentLevel()
        entityItemValueActionFailedWarning(EN_DELEGATOR, delegatorEmail, EN_DELEGATE, delegateEmail, PHRASE_DOES_NOT_EXIST, j, jcount)
        decrementIndentLevel()

# gam <UserTypeEntity> print delegates|delegate [todrive]
def printDelegates(users):
  printShowDelegates(users, True)

# gam <UserTypeEntity> show delegates|delegate [csv]
def showDelegates(users):
  printShowDelegates(users, False)

def printShowDelegates(users, csvFormat):
  emailSettings = getEmailSettingsObject()
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile([u'Delegator', u'Delegate', u'Delegate Email', u'Delegate ID', u'Status'])
  else:
    csvStyle = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if not csvFormat and myarg == u'csv':
      csvStyle = True
    elif csvFormat and myarg == u'todrive':
      todrive = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    delegatorEmail, delegatorName, emailSettings.domain = splitEmailAddressOrUID(user)
    if csvFormat:
      printGettingAllEntityItemsForWhom(EN_DELEGATE, delegatorEmail, i, count)
    result = _processEmailSettings(user, i, count, emailSettings, u'GetDelegates',
                                   delegator=delegatorName)
    if result != None:
      jcount = len(result) if (result) else 0
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
      if not csvFormat:
        if not csvStyle:
          entityPerformActionNumItems(EN_DELEGATOR, delegatorEmail, jcount, EN_DELEGATE, i, count)
          if jcount == 0:
            continue
          incrementIndentLevel()
          j = 0
          for delegate in result:
            j += 1
            printEntityName(EN_DELEGATE, delegate[u'delegate'], j, jcount)
            incrementIndentLevel()
            printKeyValueList([u'Delegate Email', delegate[u'address']])
            printKeyValueList([u'Delegate ID', delegate[u'delegationId']])
            printKeyValueList([u'Status', delegate[u'status']])
            decrementIndentLevel()
          decrementIndentLevel()
        else:
          if jcount > 0:
            for delegate in result:
              printKeyValueList([u'{0},{1},{2}'.format(delegatorEmail, delegate[u'address'], delegate[u'status'])])
      else:
        if jcount > 0:
          for delegate in result:
            row = {u'Delegator': delegatorEmail, u'Delegate': delegate[u'delegate'], u'Delegate Email': delegate[u'address'], u'Delegate ID': delegate[u'delegationId'], u'Status': delegate[u'status']}
            csvRows.append(row)
  if csvFormat:
    writeCSVfile(csvRows, titles, u'Delegates', todrive)

FILTER_ADD_LABEL_TO_ARGUMENT_MAP = {
  u'IMPORTANT': u'important',
  u'STARRED': u'star',
  u'TRASH': u'trash',
  }

FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP = {
  u'IMPORTANT': u'notimportant',
  u'UNREAD': u'markread',
  u'INBOX': u'archive',
  u'SPAM': u'neverspam',
  }

def _printFilter(user, userFilter, labels):
  row = {u'User': user, u'id': userFilter[u'id']}
  if u'criteria' in userFilter:
    for item in userFilter[u'criteria']:
      if item in [u'hasAttachment', u'excludeChats']:
        row[item] = item
      elif item == u'size':
        row[item] = u'size {0} {1}'.format(userFilter[u'criteria'][u'sizeComparison'], formatMaxMessageBytes(userFilter[u'criteria'][item]))
      elif item == u'sizeComparison':
        pass
      else:
        row[item] = u'{0} {1}'.format(item, userFilter[u'criteria'][item])
  else:
    row[u'error'] = u'NoCriteria'
  if u'action' in userFilter:
    for labelId in userFilter[u'action'].get(u'addLabelIds', []):
      if labelId in FILTER_ADD_LABEL_TO_ARGUMENT_MAP:
        row[FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId]] = FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId]
      else:
        row[u'label'] = u'label {0}'.format(_getLabelName(labels, labelId))
    for labelId in userFilter[u'action'].get(u'removeLabelIds', []):
      if labelId in FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP:
        row[FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId]] = FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId]
    if userFilter[u'action'].get(u'forward'):
      row[u'forward'] = u'forward {0}'.format(userFilter[u'action'][u'forward'])
  else:
    row[u'error'] = u'NoActions'
  return row

def _showFilter(userFilter, j, jcount, labels):
  printEntityName(EN_FILTER, userFilter[u'id'], j, jcount)
  incrementIndentLevel()
  printKeyValueList([pluralEntityName(EN_CRITERIA), None])
  incrementIndentLevel()
  if u'criteria' in userFilter:
    for item in userFilter[u'criteria']:
      if item in [u'hasAttachment', u'excludeChats']:
        printKeyValueList([item])
      elif item == u'size':
        printKeyValueList([u'{0} {1} {2}'.format(item, userFilter[u'criteria'][u'sizeComparison'], formatMaxMessageBytes(userFilter[u'criteria'][item]))])
      elif item == u'sizeComparison':
        pass
      else:
        printKeyValueList([u'{0} "{1}"'.format(item, userFilter[u'criteria'][item])])
  else:
    printKeyValueList([ERROR, PHRASE_NO_FILTER_CRITERIA.format(singularEntityName(EN_FILTER))])
  decrementIndentLevel()
  printKeyValueList([pluralEntityName(EN_ACTION), None])
  incrementIndentLevel()
  if u'action' in userFilter:
    for labelId in userFilter[u'action'].get(u'addLabelIds', []):
      if labelId in FILTER_ADD_LABEL_TO_ARGUMENT_MAP:
        printKeyValueList([FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId]])
      else:
        printKeyValueList([u'label "{0}"'.format(_getLabelName(labels, labelId))])
    for labelId in userFilter[u'action'].get(u'removeLabelIds', []):
      if labelId in FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP:
        printKeyValueList([FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId]])
    decrementIndentLevel()
    if userFilter[u'action'].get(u'forward'):
      printKeyValueList([singularEntityName(EN_FORWARDING_ADDRESS), userFilter[u'action'][u'forward']])
  else:
    printKeyValueList([ERROR, PHRASE_NO_FILTER_ACTIONS.format(singularEntityName(EN_FILTER))])
    decrementIndentLevel()
  decrementIndentLevel()
#
FILTER_CRITERIA_CHOICES_MAP = {
  u'excludechats': u'excludeChats',
  u'from': u'from',
  u'hasattachment': u'hasAttachment',
  u'haswords': u'query',
  u'musthaveattachment': u'hasAttachment',
  u'negatedquery': u'negatedQuery',
  u'nowords': u'negatedQuery',
  u'query': u'query',
  u'size': u'size',
  u'subject': u'subject',
  u'to': u'to',
  }
FILTER_ACTION_CHOICES = [u'archive', u'forward', u'important', u'label', u'markread', u'neverspam', u'notimportant', u'star', u'trash',]

# gam <UserTypeEntity> [add] filter [from <EmailAddress>] [to <EmailAddress>] [subject <String>] [haswords|query <List>] [nowords|negatedquery <List>] [musthaveattachment|hasattachment] [excludechats] [size larger|smaller <ByteCount>]
#	[label <LabelName>] [important|notimportant] [star] [trash] [markread] [archive] [neverspam] [forward <EmailAddress>]
def addFilter(users):
  body = {}
  addLabelName = None
  addLabelIds = []
  removeLabelIds = []
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg in FILTER_CRITERIA_CHOICES_MAP:
      myarg = FILTER_CRITERIA_CHOICES_MAP[myarg]
      body.setdefault(u'criteria', {})
      if myarg in [u'from', u'to']:
        body[u'criteria'][myarg] = getEmailAddress(noUid=True)
      elif myarg in [u'subject', u'query', u'negatedQuery']:
        body[u'criteria'][myarg] = getString(OB_STRING)
      elif myarg in [u'hasAttachment', u'excludeChats']:
        body[u'criteria'][myarg] = True
      elif myarg == u'size':
        body[u'criteria'][u'sizeComparison'] = getChoice([u'larger', u'smaller'])
        body[u'criteria'][myarg] = getMaxMessageBytes()
    elif myarg in FILTER_ACTION_CHOICES:
      body.setdefault(u'action', {})
      if myarg == u'label':
        addLabelName = getString(OB_LABEL_NAME)
      elif myarg == u'important':
        addLabelIds.append(u'IMPORTANT')
        if u'IMPORTANT' in removeLabelIds:
          removeLabelIds.remove(u'IMPORTANT')
      elif myarg == u'star':
        addLabelIds.append(u'STARRED')
      elif myarg == u'trash':
        addLabelIds.append(u'TRASH')
      elif myarg == u'notimportant':
        removeLabelIds.append(u'IMPORTANT')
        if u'IMPORTANT' in addLabelIds:
          addLabelIds.remove(u'IMPORTANT')
      elif myarg == u'markread':
        removeLabelIds.append(u'UNREAD')
      elif myarg == u'archive':
        removeLabelIds.append(u'INBOX')
      elif myarg == u'neverspam':
        removeLabelIds.append(u'SPAM')
      elif myarg == u'forward':
        body[u'action'][u'forward'] = getEmailAddress(noUid=True)
    else:
      unknownArgumentExit()
  if u'criteria' not in body:
    missingChoiceExit(FILTER_CRITERIA_CHOICES_MAP)
  if u'action' not in body:
    missingChoiceExit(FILTER_ACTION_CHOICES)
  if removeLabelIds:
    body[u'action'][u'removeLabelIds'] = removeLabelIds
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = _getUserGmailLabels(gmail, user, i, count, fields=u'labels(id,name)')
    if not labels:
      continue
    try:
      if addLabelIds:
        body[u'action'][u'addLabelIds'] = addLabelIds[:]
      if addLabelName:
        if not addLabelIds:
          body[u'action'][u'addLabelIds'] = []
        body[u'action'][u'addLabelIds'].append(_getLabelId(labels, addLabelName))
      result = callGAPI(gmail.users().settings().filters(), u'create',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS+[GAPI_INVALID_ARGUMENT, GAPI_FAILED_PRECONDITION],
                        userId=u'me', body=body)
      if result:
        entityItemValueActionPerformed(EN_USER, user, EN_FILTER, result[u'id'], i, count)
    except (GAPI_invalidArgument, GAPI_failedPrecondition) as e:
      entityItemValueActionFailedWarning(EN_USER, user, EN_FILTER, u'', e.message, i, count)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> delete|del filter <FilterIDEntity>
def deleteFilters(users):
  filterIds = getEntityList(OB_FILTER_ID_ENTITY)
  filterIdLists = filterIds if isinstance(filterIds, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if filterIdLists:
      filterIds = filterIdLists[user]
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    jcount = len(filterIds)
    entityPerformActionNumItems(EN_USER, user, jcount, EN_FILTER, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for filterId in filterIds:
      j += 1
      try:
        callGAPI(gmail.users().settings().filters(), u'delete',
                 throw_reasons=GAPI_GMAIL_THROW_REASONS+[GAPI_NOT_FOUND],
                 userId=u'me', id=filterId)
        entityItemValueActionPerformed(EN_USER, user, EN_FILTER, filterId, j, jcount)
      except GAPI_notFound:
        entityItemValueActionFailedWarning(EN_USER, user, EN_FILTER, filterId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_badRequest):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
        break
    decrementIndentLevel()

# gam <UserTypeEntity> print filters [todrive]
def printFilters(users):
  printShowFilters(users, True)

# gam <UserTypeEntity> show filters
def showFilters(users):
  printShowFilters(users, False)

def printShowFilters(users, csvFormat):
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile(None)
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    labels = _getUserGmailLabels(gmail, user, i, count, fields=u'labels(id,name)')
    if not labels:
      continue
    try:
      result = callGAPI(gmail.users().settings().filters(), u'list',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS,
                        userId=u'me')
      jcount = len(result.get(u'filter', [])) if (result) else 0
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
      if not csvFormat:
        entityPerformActionNumItems(EN_USER, user, jcount, EN_FILTER, i, count)
        if jcount == 0:
          continue
        incrementIndentLevel()
        j = 0
        for userFilter in result[u'filter']:
          j += 1
          _showFilter(userFilter, j, jcount, labels)
        decrementIndentLevel()
      else:
        if jcount == 0:
          continue
        for userFilter in result[u'filter']:
          addRowTitlesToCSVfile(_printFilter(user, userFilter, labels), csvRows, titles)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
  if csvFormat:
    sortCSVTitles([u'User', u'id'], titles)
    writeCSVfile(csvRows, titles, u'Filters', todrive)

# gam <UserTypeEntity> info filters <FilterIDEntity>
def infoFilters(users):
  filterIds = getEntityList(OB_FILTER_ID_ENTITY)
  filterIdLists = filterIds if isinstance(filterIds, dict) else None
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if filterIdLists:
      filterIds = filterIdLists[user]
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    jcount = len(filterIds)
    entityPerformActionNumItems(EN_USER, user, jcount, EN_FILTER, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    labels = _getUserGmailLabels(gmail, user, i, count, fields=u'labels(id,name)')
    if not labels:
      continue
    incrementIndentLevel()
    j = 0
    for filterId in filterIds:
      j += 1
      try:
        result = callGAPI(gmail.users().settings().filters(), u'get',
                          throw_reasons=GAPI_GMAIL_THROW_REASONS+[GAPI_NOT_FOUND],
                          userId=u'me', id=filterId)
        printEntityKVList(EN_USER, user,
                          [singularEntityName(EN_FILTER), result[u'id']],
                          i, count)
        incrementIndentLevel()
        _showFilter(result, j, jcount, labels)
        decrementIndentLevel()
      except GAPI_notFound:
        entityItemValueActionFailedWarning(EN_USER, user, EN_FILTER, filterId, PHRASE_DOES_NOT_EXIST, j, jcount)
      except (GAPI_serviceNotAvailable, GAPI_badRequest):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
        break
    decrementIndentLevel()

EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP = {
  u'ARCHIVE': u'archive',
  u'DELETE': u'trash',
  u'KEEP': u'leaveInInBox',
  u'MARK_READ': u'markRead',
  u'archive': u'ARCHIVE',
  u'trash': u'DELETE',
  u'leaveInInbox': u'KEEP',
  u'markRead': u'MARK_READ',
  }

def _showForward(user, i, count, result):
  if u'enabled' in result:
    enabled = result[u'enabled']
    kvList = [singularEntityName(EN_FORWARD_ENABLED), enabled]
    if enabled:
      kvList += [singularEntityName(EN_FORWARDING_ADDRESS), result[u'emailAddress']]
      kvList += [singularEntityName(EN_ACTION), result[u'disposition']]
  else:
    enabled = result[u'enable'] == u'true'
    kvList = [singularEntityName(EN_FORWARD_ENABLED), enabled]
    if enabled:
      kvList += [singularEntityName(EN_FORWARDING_ADDRESS), result[u'forwardTo']]
      kvList += [singularEntityName(EN_ACTION), EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP[result[u'action']]]
  printEntityKVList(EN_USER, user, kvList, i, count)

EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP = {
  u'archive': u'archive',
  u'delete': u'trash',
  u'keep': u'leaveInInbox',
  u'leaveininbox': u'leaveInInbox',
  u'markread': u'markRead',
  u'trash': u'trash',
  }

# gam <UserTypeEntity> forward <FalseValues> [newapi]
# gam <UserTypeEntity> forward <TrueValues> keep|leaveininbox|archive|delete|trash|markread <EmailAddress> [newapi]
def setForward(users):
  newAPI = False
  action = forward_to = None
  enable = getBoolean()
  body = {u'enabled': enable}
  if enable:
    while CL_argvI < CL_argvLen:
      myarg = getArgument()
      if myarg in EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP:
        body[u'disposition'] = EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP[myarg]
      elif myarg == u'confirm':
        pass
      elif myarg == u'newapi':
        newAPI = True
      elif myarg.find(u'@') != -1:
        body[u'emailAddress'] = normalizeEmailAddressOrUID(CL_argv[CL_argvI-1])
      else:
        unknownArgumentExit()
    if not body.get(u'disposition'):
      missingChoiceExit(EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP)
    if not body.get(u'emailAddress'):
      missingArgumentExit(OB_EMAIL_ADDRESS)
  else:
    while CL_argvI < CL_argvLen:
      myarg = getArgument()
      if myarg == u'newapi':
        newAPI = True
      else:
        unknownArgumentExit()
  if not newAPI:
    emailSettings = getEmailSettingsObject()
    if enable:
      action = EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP[body[u'disposition']]
      forward_to = body[u'emailAddress']
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if newAPI:
      user, gmail = buildGmailGAPIObject(user)
      if not gmail:
        continue
      try:
        result = callGAPI(gmail.users().settings(), u'updateAutoForwarding',
                          throw_reasons=GAPI_GMAIL_THROW_REASONS+[GAPI_FAILED_PRECONDITION],
                          userId=u'me', body=body)
        _showForward(user, i, count, result)
      except GAPI_failedPrecondition:
        entityItemValueActionFailedWarning(EN_USER, user, EN_FORWARDING_ADDRESS, body[u'emailAddress'], PHRASE_DOES_NOT_EXIST_OR_NOT_ALLOWED, i, count)
      except (GAPI_serviceNotAvailable, GAPI_badRequest):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
    else:
      user, userName, emailSettings.domain = splitEmailAddressOrUID(user)
      result = _processEmailSettings(user, i, count, emailSettings, u'UpdateForwarding',
                                     username=userName, enable=enable, action=action, forward_to=forward_to)
      if result:
        _showForward(user, i, count, result)

# gam <UserTypeEntity> print forward [todrive] [newapi]
def printForward(users):
  printShowForward(users, True)

# gam <UserTypeEntity> show forward [newapi]
def showForward(users):
  printShowForward(users, False)

def printShowForward(users, csvFormat):
  def _printForward(user, result):
    if u'enabled' in result:
      row = {u'User': user, u'forwardEnabled': result[u'enabled']}
      if result[u'enabled']:
        row[u'forwardTo'] = result[u'emailAddress']
        row[u'disposition'] = result[u'disposition']
    else:
      row = {u'User': user, u'forwardEnabled': result[u'enable']}
      if result[u'enable'] == u'true':
        row[u'forwardTo'] = result[u'forwardTo']
        row[u'disposition'] = EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP[result[u'action']]
    csvRows.append(row)

  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile([u'User', u'forwardEnabled', u'forwardTo', u'disposition'])
  newAPI = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    elif myarg == u'newapi':
      newAPI = True
    else:
      unknownArgumentExit()
  if not newAPI:
    emailSettings = getEmailSettingsObject()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if newAPI:
      user, gmail = buildGmailGAPIObject(user)
      if not gmail:
        continue
      try:
        result = callGAPI(gmail.users().settings(), u'getAutoForwarding',
                          throw_reasons=GAPI_GMAIL_THROW_REASONS,
                          userId=u'me')
        if not csvFormat:
          _showForward(user, i, count, result)
        else:
          _printForward(user, result)
      except (GAPI_serviceNotAvailable, GAPI_badRequest):
        entityServiceNotApplicableWarning(EN_USER, user, i, count)
    else:
      user, userName, emailSettings.domain = splitEmailAddressOrUID(user)
      result = _processEmailSettings(user, i, count, emailSettings, u'GetForward',
                                     username=userName)
      if result:
        if not csvFormat:
          _showForward(user, i, count, result)
        else:
          _printForward(user, result)
  if csvFormat:
    writeCSVfile(csvRows, titles, u'Forward', todrive)

# Process ForwardingAddresses functions
def _showForwardingAddress(j, jcount, result):
  printEntityKVList(EN_FORWARDING_ADDRESS, result[u'forwardingEmail'], [u'Verification Status', result[u'verificationStatus']], j, jcount)

def _processForwardingAddress(user, i, count, emailAddress, j, jcount, gmail, function, **kwargs):
  userDefined = True
  try:
    result = callGAPI(gmail.users().settings().forwardingAddresses(), function,
                      throw_reasons=GAPI_GMAIL_THROW_REASONS+[GAPI_NOT_FOUND, GAPI_DUPLICATE],
                      userId=u'me', **kwargs)
    if function == u'get':
      _showForwardingAddress(j, count, result)
    else:
      entityItemValueActionPerformed(EN_USER, user, EN_FORWARDING_ADDRESS, emailAddress, j, jcount)
  except GAPI_notFound:
    entityItemValueActionFailedWarning(EN_USER, user, EN_FORWARDING_ADDRESS, emailAddress, PHRASE_DOES_NOT_EXIST, j, jcount)
  except GAPI_duplicate:
    entityItemValueActionFailedWarning(EN_USER, user, EN_FORWARDING_ADDRESS, emailAddress, PHRASE_DUPLICATE, j, jcount)
  except (GAPI_serviceNotAvailable, GAPI_badRequest, GAPI_authError):
    entityServiceNotApplicableWarning(EN_USER, user, i, count)
    userDefined = False
  return userDefined

# gam <UserTypeEntity> add forwardingaddresses <EmailAddressEntity>
def addForwardingAddresses(users):
  emailAddresses, emailLists = getEmailAddressEntity(True)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if emailLists:
      emailAddresses = emailLists[user]
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    jcount = len(emailAddresses)
    entityPerformActionNumItems(EN_USER, user, jcount, EN_FORWARDING_ADDRESS, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for emailAddress in emailAddresses:
      j += 1
      emailAddress = normalizeEmailAddressOrUID(emailAddress, noUid=True)
      body = {u'forwardingEmail': emailAddress}
      if not _processForwardingAddress(user, i, count, emailAddress, j, jcount, gmail, u'create', body=body):
        break
    decrementIndentLevel()

# gam <UserTypeEntity> delete forwardingaddresses <EmailAddressEntity>
def deleteForwardingAddresses(users):
  deleteInfoForwardingAddreses(users, u'delete')

# gam <UserTypeEntity> info forwardingaddresses <EmailAddressEntity>
def infoForwardingAddresses(users):
  deleteInfoForwardingAddreses(users, u'get')

def deleteInfoForwardingAddreses(users, function):
  emailAddresses, emailLists = getEmailAddressEntity(True)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if emailLists:
      emailAddresses = emailLists[user]
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    jcount = len(emailAddresses)
    entityPerformActionNumItems(EN_USER, user, jcount, EN_FORWARDING_ADDRESS, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for emailAddress in emailAddresses:
      j += 1
      emailAddress = normalizeEmailAddressOrUID(emailAddress, noUid=True)
      if not _processForwardingAddress(user, i, count, emailAddress, j, jcount, gmail, function, forwardingEmail=emailAddress):
        break
    decrementIndentLevel()

# gam <UserTypeEntity> print forwardingaddresses [todrive]
def printForwardingAddresses(users):
  printShowForwardingAddresses(users, True)

# gam <UserTypeEntity> show forwardingaddresses
def showForwardingAddresses(users):
  printShowForwardingAddresses(users, False)

def printShowForwardingAddresses(users, csvFormat):
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile([u'User', u'forwardingEmail', u'verificationStatus'])
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings().forwardingAddresses(), u'list',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS,
                        userId=u'me')
      jcount = len(result.get(u'forwardingAddresses', [])) if (result) else 0
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
      if not csvFormat:
        entityPerformActionNumItems(EN_USER, user, jcount, EN_FORWARDING_ADDRESS, i, count)
        if jcount == 0:
          continue
        incrementIndentLevel()
        j = 0
        for forward in result[u'forwardingAddresses']:
          j += 1
          _showForwardingAddress(j, jcount, forward)
        decrementIndentLevel()
      else:
        if jcount == 0:
          continue
        for forward in result[u'forwardingAddresses']:
          row = {u'User': user, u'forwardingEmail': forward[u'forwardingEmail'], u'verificationStatus': forward[u'verificationStatus']}
          csvRows.append(row)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
  if csvFormat:
    writeCSVfile(csvRows, titles, u'Forwarding Addresses', todrive)

def _showImap(user, i, count, result):
  enabled = result[u'enabled']
  kvList = [singularEntityName(EN_IMAP_ENABLED), enabled]
  if enabled:
    for item in result:
      if item != u'enabled':
        kvList += [item, result[item]]
  printEntityKVList(EN_USER, user, kvList, i, count)
#
EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICES_MAP = {
  u'archive': u'archive',
  u'deleteforever': u'deleteForever',
  u'trash': u'trash',
  }

EMAILSETTINGS_IMAP_MAX_FOLDER_SIZE_CHOICES = [u'0', u'1000', u'2000', u'5000', u'10000']

# gam <UserTypeEntity> imap|imap4 <Boolean> [noautoexpunge] [expungebehavior archive|deleteforever|trash] [maxfoldersize 0|1000|2000|5000|10000]
def setImap(users):
  enable = getBoolean()
  body = {u'enabled': enable, u'autoExpunge': True, u'expungeBehavior': u'archive', u'maxFolderSize': 0}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'noautoexpunge':
      body[u'autoExpunge'] = False
    elif myarg == u'expungebehavior':
      body[u'expungeBehavior'] = getChoice(EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICES_MAP, mapChoice=True)
    elif myarg == u'maxfoldersize':
      body[u'maxFolderSize'] = int(getChoice(EMAILSETTINGS_IMAP_MAX_FOLDER_SIZE_CHOICES))
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings(), u'updateImap',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS,
                        userId=u'me', body=body)
      _showImap(user, i, count, result)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> show imap|imap4
def showImap(users):
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings(), u'getImap',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS,
                        userId=u'me')
      _showImap(user, i, count, result)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

def _showPop(user, i, count, result):
  enabled = result[u'accessWindow'] != u'disabled'
  kvList = [singularEntityName(EN_POP_ENABLED), enabled]
  if enabled:
    kvList += [u'For', result[u'accessWindow'], singularEntityName(EN_ACTION), result[u'disposition']]
  printEntityKVList(EN_USER, user, kvList, i, count)
#
EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP = {
  u'allmail': u'allMail',
  u'fromnowon': u'fromNowOn',
  u'mailfromnowon': u'fromNowOn',
  u'newmail': u'fromNowOn',
  }

# gam <UserTypeEntity> pop|pop3 <Boolean> [for allmail|newmail|mailfromnowon|fromnowown] [action keep|leaveininbox|archive|delete|trash|markread]
def setPop(users):
  enable = getBoolean()
  body = {u'accessWindow': [u'disabled', u'allMail'][enable], u'disposition': u'leaveInInbox'}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'for':
      body[u'accessWindow'] = getChoice(EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP, mapChoice=True)
    elif myarg == u'action':
      body[u'disposition'] = getChoice(EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP, mapChoice=True)
    elif myarg == u'confirm':
      pass
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings(), u'updatePop',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS,
                        userId=u'me', body=body)
      _showPop(user, i, count, result)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> show pop|pop3
def showPop(users):
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings(), u'getPop',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS,
                        userId=u'me')
      _showPop(user, i, count, result)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> language <Language>
def setLanguage(users):
  emailSettings = getEmailSettingsObject()
  language = getChoice(LANGUAGE_CODES_MAP, mapChoice=True)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, userName, emailSettings.domain = splitEmailAddressOrUID(user)
    result = _processEmailSettings(user, i, count, emailSettings, u'UpdateLanguage',
                                   username=userName, language=language)
    if result:
      printEntityItemValue(EN_USER, user, EN_LANGUAGE, result[u'language'], i, count)

VALID_PAGESIZES = [u'25', u'50', u'100']

# gam <UserTypeEntity> pagesize 25|50|100
def setPageSize(users):
  emailSettings = getEmailSettingsObject()
  PageSize = getChoice(VALID_PAGESIZES)
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, userName, emailSettings.domain = splitEmailAddressOrUID(user)
    result = _processEmailSettings(user, i, count, emailSettings, u'UpdateGeneral',
                                   username=userName, page_size=PageSize)
    if result:
      printEntityItemValue(EN_USER, user, EN_PAGE_SIZE, result[u'pageSize'], i, count)

def _showSendAs(result, j, jcount, formatSig):
  if result[u'displayName']:
    printEntityName(EN_SENDAS_ADDRESS, u'{0} <{1}>'.format(result[u'displayName'], result[u'sendAsEmail']), j, jcount)
  else:
    printEntityName(EN_SENDAS_ADDRESS, u'<{0}>'.format(result[u'sendAsEmail']), j, jcount)
  incrementIndentLevel()
  if result.get(u'replyToAddress'):
    printKeyValueList([u'ReplyTo', result[u'replyToAddress']])
  printKeyValueList([u'IsPrimary', result.get(u'isPrimary', False)])
  printKeyValueList([u'Default', result.get(u'isDefault', False)])
  if not result.get(u'isPrimary', False):
    printKeyValueList([u'TreatAsAlias', result.get(u'treatAsAlias', False)])
    printKeyValueList([u'Verification Status', result.get(u'verificationStatus', u'unspecified')])
  printKeyValueList([singularEntityName(EN_SIGNATURE), None])
  incrementIndentLevel()
  signature = result.get(u'signature')
  if not signature:
    signature = u'None'
  if formatSig:
    printKeyValueList([indentMultiLineText(dehtml(signature))])
  else:
    printKeyValueList([indentMultiLineText(signature)])
  decrementIndentLevel()
  decrementIndentLevel()

RT_PATTERN = re.compile(r'(?s){RT}.*?{(.+?)}.*?{/RT}')
RT_OPEN_PATTERN = re.compile(r'{RT}')
RT_CLOSE_PATTERN = re.compile(r'{/RT}')
RT_STRIP_PATTERN = re.compile(r'(?s){RT}.*?{/RT}')
RT_TAG_REPLACE_PATTERN = re.compile(r'{(.*?)}')

def _processTags(tagReplacements, message):
  while True:
    match = RT_PATTERN.search(message)
    if not match:
      break
    if tagReplacements.get(match.group(1)):
      message = RT_OPEN_PATTERN.sub(u'', message, count=1)
      message = RT_CLOSE_PATTERN.sub(u'', message, count=1)
    else:
      message = RT_STRIP_PATTERN.sub(u'', message, count=1)
  while True:
    match = RT_TAG_REPLACE_PATTERN.search(message)
    if not match:
      break
    message = re.sub(match.group(0), tagReplacements.get(match.group(1), u''), message)
  return message

# Process SendAs functions
def _processSendAs(user, i, count, entityType, emailAddress, j, jcount, gmail, function, formatSig, **kwargs):
  userDefined = True
  try:
    result = callGAPI(gmail.users().settings().sendAs(), function,
                      throw_reasons=GAPI_GMAIL_THROW_REASONS+[GAPI_NOT_FOUND, GAPI_ALREADY_EXISTS, GAPI_DUPLICATE, GAPI_CANNOT_DELETE_PRIMARY_SENDAS, GAPI_INVALID_ARGUMENT],
                      userId=u'me', **kwargs)
    if function == u'get':
      _showSendAs(result, j, jcount, formatSig)
    else:
      entityItemValueActionPerformed(EN_USER, user, entityType, emailAddress, j, jcount)
  except GAPI_notFound:
    entityItemValueActionFailedWarning(EN_USER, user, entityType, emailAddress, PHRASE_DOES_NOT_EXIST, j, jcount)
  except (GAPI_alreadyExists, GAPI_duplicate):
    entityItemValueActionFailedWarning(EN_USER, user, entityType, emailAddress, PHRASE_DUPLICATE, j, jcount)
  except GAPI_cannotDeletePrimarySendAs:
    entityItemValueActionFailedWarning(EN_USER, user, entityType, emailAddress, PHRASE_NOT_ALLOWED, j, jcount)
  except GAPI_invalidArgument as e:
    entityItemValueActionFailedWarning(EN_USER, user, entityType, emailAddress, e.message, j, jcount)
  except (GAPI_serviceNotAvailable, GAPI_badRequest, GAPI_authError):
    entityServiceNotApplicableWarning(EN_USER, user, i, count)
    userDefined = False
  return userDefined

def getSendAsAttributes(myarg, body, tagReplacements):
  if myarg == u'replace':
    matchTag = getString(OB_TAG)
    matchReplacement = getString(OB_STRING, emptyOK=True)
    tagReplacements[matchTag] = matchReplacement
  elif myarg == u'name':
    body[u'displayName'] = getString(OB_NAME)
  elif myarg == u'replyto':
    body[u'replyToAddress'] = getEmailAddress(noUid=True)
  elif myarg == u'default':
    body[u'isDefault'] = True
  elif myarg == u'treatasalias':
    body[u'treatAsAlias'] = getBoolean()
  else:
    unknownArgumentExit()

# gam <UserTypeEntity> [add] sendas <EmailAddress> <Name> [signature|sig <String>|(file <FileName> [charset <CharSet>]) (replace <RegularExpression> <String>)*] [replyto <EmailAddress>] [default] [treatasalias <Boolean>]
def addSendAs(users):
  addUpdateSendAs(users, True)

# gam <UserTypeEntity> update sendas <EmailAddress> [name <Name>] [signature|sig <String>|(file <FileName> [charset <CharSet>]) (replace <RegularExpression> <String>)*] [replyto <EmailAddress>] [default] [treatasalias <Boolean>]
def updateSendAs(users):
  addUpdateSendAs(users, False)

def addUpdateSendAs(users, addCmd):
  emailAddress = getEmailAddress(noUid=True)
  if addCmd:
    body = {u'sendAsEmail': emailAddress, u'displayName': getString(OB_NAME)}
  else:
    body = {}
  signature = None
  tagReplacements = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg in [u'signature', u'sig']:
      if checkArgumentPresent(FILE_ARGUMENT):
        filename = getString(OB_FILE_NAME)
        encoding = getCharSet()
        signature = readFile(filename, encoding=encoding).replace(u'\\n', u'<br/>')
      else:
        signature = getString(OB_STRING, emptyOK=True).replace(u'\\n', u'<br/>')
    else:
      getSendAsAttributes(myarg, body, tagReplacements)
  if signature != None:
    if signature and tagReplacements:
      body[u'signature'] = _processTags(tagReplacements, signature)
    else:
      body[u'signature'] = signature
  kwargs = {u'body': body}
  if not addCmd:
    kwargs[u'sendAsEmail'] = emailAddress
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    _processSendAs(user, i, count, EN_SENDAS_ADDRESS, emailAddress, i, count, gmail, [u'patch', u'create'][addCmd], False, **kwargs)

# gam <UserTypeEntity> delete sendas <EmailAddressEntity>
def deleteSendAs(users):
  deleteInfoSendAs(users, u'delete')

# gam <UserTypeEntity> info sendas <EmailAddressEntity> [format]
def infoSendAs(users):
  deleteInfoSendAs(users, u'get')

def deleteInfoSendAs(users, function):
  emailAddresses, emailLists = getEmailAddressEntity(True)
  formatSig = False
  if function == u'get':
    while CL_argvI < CL_argvLen:
      myarg = getArgument()
      if myarg == u'format':
        formatSig = True
      else:
        unknownArgumentExit()
  else:
    checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    if emailLists:
      emailAddresses = emailLists[user]
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    jcount = len(emailAddresses)
    entityPerformActionNumItems(EN_USER, user, jcount, EN_SENDAS_ADDRESS, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND)
      continue
    incrementIndentLevel()
    j = 0
    for emailAddress in emailAddresses:
      j += 1
      emailAddress = normalizeEmailAddressOrUID(emailAddress, noUid=True)
      if not _processSendAs(user, i, count, EN_SENDAS_ADDRESS, emailAddress, j, jcount, gmail, function, formatSig, sendAsEmail=emailAddress):
        break
    decrementIndentLevel()

# gam <UserTypeEntity> print sendas [todrive]
def printSendAs(users):
  printShowSendAs(users, True)

# gam <UserTypeEntity> show sendas [format]
def showSendAs(users):
  printShowSendAs(users, False)

def printShowSendAs(users, csvFormat):
  if csvFormat:
    todrive = False
    titles, csvRows = initializeTitlesCSVfile([u'User', u'displayName', u'sendAsEmail', u'replyToAddress', u'isPrimary', u'isDefault', u'treatAsAlias', u'verificationStatus'])
  formatSig = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if csvFormat and myarg == u'todrive':
      todrive = True
    elif not csvFormat and myarg == u'format':
      formatSig = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings().sendAs(), u'list',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS,
                        userId=u'me')
      jcount = len(result.get(u'sendAs', [])) if (result) else 0
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND)
      if not csvFormat:
        entityPerformActionNumItems(EN_USER, user, jcount, EN_SENDAS_ADDRESS, i, count)
        if jcount == 0:
          continue
        incrementIndentLevel()
        j = 0
        for sendas in result[u'sendAs']:
          j += 1
          _showSendAs(sendas, j, jcount, formatSig)
        decrementIndentLevel()
      else:
        if jcount == 0:
          continue
        for sendas in result[u'sendAs']:
          row = {u'User': user, u'isPrimary': False}
          for item in sendas:
            row[item] = sendas[item]
          addRowTitlesToCSVfile(row, csvRows, titles)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)
  if csvFormat:
    writeCSVfile(csvRows, titles, u'SendAs', todrive)

# gam <UserTypeEntity> shortcuts <Boolean>
def setShortCuts(users):
  emailSettings = getEmailSettingsObject()
  enable = getBoolean()
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, userName, emailSettings.domain = splitEmailAddressOrUID(user)
    result = _processEmailSettings(user, i, count, emailSettings, u'UpdateGeneral',
                                   username=userName, shortcuts=enable)
    if result:
      printEntityItemValue(EN_USER, user, EN_KEYBOARD_SHORTCUTS_ENABLED, result[u'shortcuts'], i, count)

# gam <UserTypeEntity> signature|sig <String>|(file <FileName> [charset <CharSet>]) (replace <RegularExpression> <String>)* [name <String>] [replyto <EmailAddress>] [default] [treatasalias <Boolean>]
def setSignature(users):
  tagReplacements = {}
  if checkArgumentPresent(FILE_ARGUMENT):
    filename = getString(OB_FILE_NAME)
    encoding = getCharSet()
    signature = readFile(filename, encoding=encoding).replace(u'\\n', u'<br/>')
  else:
    signature = getString(OB_STRING, emptyOK=True).replace(u'\\n', u'<br/>')
  body = {}
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    getSendAsAttributes(myarg, body, tagReplacements)
  if signature and tagReplacements:
    body[u'signature'] = _processTags(tagReplacements, signature)
  else:
    body[u'signature'] = signature
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings().sendAs(), u'list',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS,
                        userId=u'me')
      for sendas in result[u'sendAs']:
        if sendas.get(u'isPrimary', False):
          emailAddress = sendas[u'sendAsEmail']
          _processSendAs(user, i, count, EN_SIGNATURE, emailAddress, i, count, gmail, u'patch', False, body=body, sendAsEmail=emailAddress)
          break
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> show signature|sig [format]
def showSignature(users):
  formatSig = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'format':
      formatSig = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings().sendAs(), u'list',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS,
                        userId=u'me')
      printEntityItemValue(EN_USER, user, EN_SIGNATURE, u'', i, count)
      incrementIndentLevel()
      for sendas in result[u'sendAs']:
        if sendas.get(u'isPrimary', False):
          _showSendAs(sendas, 0, 0, formatSig)
          break
      decrementIndentLevel()
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> snippets <Boolean>
def setSnippets(users):
  emailSettings = getEmailSettingsObject()
  enable = getBoolean()
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, userName, emailSettings.domain = splitEmailAddressOrUID(user)
    result = _processEmailSettings(user, i, count, emailSettings, u'UpdateGeneral',
                                   username=userName, snippets=enable)
    if result:
      printEntityItemValue(EN_USER, user, EN_SNIPPETS_ENABLED, result[u'snippets'], i, count)

# gam <UserTypeEntity> utf|utf8|utf-8|unicode <Boolean>
def setUnicode(users):
  emailSettings = getEmailSettingsObject()
  enable = getBoolean()
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, userName, emailSettings.domain = splitEmailAddressOrUID(user)
    result = _processEmailSettings(user, i, count, emailSettings, u'UpdateGeneral',
                                   username=userName, unicode=enable)
    if result:
      printEntityItemValue(EN_USER, user, EN_UNICODE_ENCODING_ENABLED, result[u'unicode'], i, count)

def _showVacation(user, i, count, result, formatReply):
  enabled = result[u'enableAutoReply']
  printEntityItemValue(EN_USER, user, EN_VACATION, None, i, count)
  incrementIndentLevel()
  printKeyValueList([u'Enabled', enabled])
  if enabled:
    printKeyValueList([u'Contacts Only', result[u'restrictToContacts']])
    printKeyValueList([u'Domain Only', result[u'restrictToDomain']])
    if u'startTime' in result:
      printKeyValueList([u'Start Date', datetime.datetime.fromtimestamp(int(result[u'startTime'])/1000).strftime('%Y-%m-%d')])
    else:
      printKeyValueList([u'Start Date', u'Started'])
    if u'endTime' in result:
      printKeyValueList([u'End Date', datetime.datetime.fromtimestamp(int(result[u'endTime'])/1000).strftime('%Y-%m-%d')])
    else:
      printKeyValueList([u'End Date', u'Not specified'])
    printKeyValueList([u'Subject', result.get(u'responseSubject', u'None')])
    printKeyValueList([u'Message', u''])
    incrementIndentLevel()
    if result.get(u'responseBodyPlainText'):
      printKeyValueList([indentMultiLineText(result[u'responseBodyPlainText'])])
    elif result.get(u'responseBodyHtml'):
      if formatReply:
        printKeyValueList([indentMultiLineText(dehtml(result[u'responseBodyHtml']))])
      else:
        printKeyValueList([indentMultiLineText(result[u'responseBodyHtml'])])
    else:
      printKeyValueList([u'None'])
    decrementIndentLevel()
  decrementIndentLevel()

# gam <UserTypeEntity> vacation <FalseValues>
# gam <UserTypeEntity> vacation <TrueValues> subject <String> (message <String>)|(file <FileName> [charset <CharSet>]) (replace <RegularExpression> <String>)* [html]
#	[contactsonly] [domainonly] [startdate <Date>] [enddate <Date>]
def setVacation(users):
  enable = getBoolean()
  body = {u'enableAutoReply': enable}
  if enable:
    responseBodyType = u'responseBodyPlainText'
    message = None
    tagReplacements = {}
    while CL_argvI < CL_argvLen:
      myarg = getArgument()
      if myarg == u'subject':
        body[u'responseSubject'] = getString(OB_STRING, checkBlank=True)
      elif myarg == u'message':
        message = getString(OB_STRING, checkBlank=True)
      elif myarg == u'file':
        filename = getString(OB_FILE_NAME)
        encoding = getCharSet()
        message = readFile(filename, encoding=encoding)
      elif myarg == u'replace':
        matchTag = getString(OB_TAG)
        matchReplacement = getString(OB_STRING, emptyOK=True)
        tagReplacements[matchTag] = matchReplacement
      elif myarg == u'html':
        responseBodyType = u'responseBodyHtml'
      elif myarg == u'contactsonly':
        body[u'restrictToContacts'] = True
      elif myarg == u'domainonly':
        body[u'restrictToDomain'] = True
      elif myarg == u'startdate':
        body[u'startTime'] = getYYYYMMDD(returnTimeStamp=True)
      elif myarg == u'enddate':
        body[u'endTime'] = getYYYYMMDD(returnTimeStamp=True)
      else:
        unknownArgumentExit()
    if message:
      if responseBodyType == u'responseBodyHtml':
        message = message.replace(u'\\n', u'<br/>')
      else:
        message = message.replace(u'\\n', u'\n')
      if tagReplacements:
        message = _processTags(tagReplacements, message)
      body[responseBodyType] = message
    if not message and not body.get(u'responseSubject'):
      missingArgumentExit(u'message or subject')
  else:
    checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings(), u'updateVacation',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS+[GAPI_INVALID_ARGUMENT],
                        userId=u'me', body=body)
      printEntityItemValue(EN_USER, user, EN_VACATION_ENABLED, result[u'enableAutoReply'], i, count)
    except GAPI_invalidArgument as e:
      entityItemValueActionFailedWarning(EN_USER, user, EN_VACATION_ENABLED, enable, e.message, i, count)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> show vacation [format]
def showVacation(users):
  formatReply = False
  while CL_argvI < CL_argvLen:
    myarg = getArgument()
    if myarg == u'format':
      formatReply = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, gmail = buildGmailGAPIObject(user)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().settings(), u'getVacation',
                        throw_reasons=GAPI_GMAIL_THROW_REASONS,
                        userId=u'me')
      _showVacation(user, i, count, result, formatReply)
    except (GAPI_serviceNotAvailable, GAPI_badRequest):
      entityServiceNotApplicableWarning(EN_USER, user, i, count)

# gam <UserTypeEntity> webclips <Boolean>
def setWebClips(users):
  emailSettings = getEmailSettingsObject()
  enable = getBoolean()
  checkForExtraneousArguments()
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, userName, emailSettings.domain = splitEmailAddressOrUID(user)
    result = _processEmailSettings(user, i, count, emailSettings, u'UpdateWebClipSettings',
                                   username=userName, enable=enable)
    if result:
      printEntityItemValue(EN_USER, user, EN_WEBCLIPS_ENABLED, result[u'enable'], i, count)

# Command line processing

# Keys into command tables
CMD_ACTION = u'acti'
CMD_FUNCTION = u'func'
CMD_OBJ_ALIASES = u'alia'

# Main commands
MAIN_COMMANDS = {
  u'batch':	{CMD_ACTION: AC_PERFORM, CMD_FUNCTION: doBatch},
  u'csv':	{CMD_ACTION: AC_PERFORM, CMD_FUNCTION: doCSV},
  u'help':	{CMD_ACTION: AC_PERFORM, CMD_FUNCTION: doUsage},
  u'list':	{CMD_ACTION: AC_LIST, CMD_FUNCTION: doListType},
  u'report':	{CMD_ACTION: AC_REPORT, CMD_FUNCTION: doReport},
  u'version':	{CMD_ACTION: AC_PERFORM, CMD_FUNCTION: doVersion},
  u'whatis':	{CMD_ACTION: AC_INFO, CMD_FUNCTION: doWhatIs},
  }

# Main commands with objects
MAIN_COMMANDS_WITH_OBJECTS = {
  u'add':
    {CMD_ACTION: AC_ADD,
     CMD_FUNCTION:
       {CL_OB_SITEACLS:	doProcessDomainSiteACLs,
       },
     CMD_OBJ_ALIASES:
       {CL_OB_SITEACL:	CL_OB_SITEACLS,
       },
    },
  u'create':
    {CMD_ACTION: AC_CREATE,
     CMD_FUNCTION:
       {CL_OB_ADMIN:	doCreateAdmin,
        CL_OB_ALIAS:	doCreateAlias,
        CL_OB_ALIASES:	doCreateAliases,
        CL_OB_CONTACT:	doCreateDomainContact,
        CL_OB_COURSE:	doCreateCourse,
        CL_OB_DATA_TRANSFER:doCreateDataTransfer,
        CL_OB_DOMAIN:	doCreateDomain,
        CL_OB_DOMAIN_ALIAS:	doCreateDomainAlias,
        CL_OB_GROUP:	doCreateGroup,
        CL_OB_GUARDIAN: doInviteGuardian,
        CL_OB_ORG:	doCreateOrg,
        CL_OB_RESOURCE:	doCreateResourceCalendar,
        CL_OB_SCHEMA:	doCreateUserSchema,
        CL_OB_SITE:	doCreateDomainSite,
        CL_OB_USER:	doCreateUser,
        CL_OB_VERIFY:	doCreateSiteVerification,
       },
     CMD_OBJ_ALIASES:
       {u'aliasdomain':	CL_OB_DOMAIN_ALIAS,
        u'aliasdomains':	CL_OB_DOMAIN_ALIAS,
        u'class':	CL_OB_COURSE,
        CL_OB_CONTACTS:	CL_OB_CONTACT,
        CL_OB_DOMAIN_ALIASES:	CL_OB_DOMAIN_ALIAS,
        CL_OB_GUARDIANS:	CL_OB_GUARDIAN,
        u'guardianinvite':	CL_OB_GUARDIAN,
        u'inviteguardian':	CL_OB_GUARDIAN,
        u'transfer':	CL_OB_DATA_TRANSFER,
        u'nickname':	CL_OB_ALIAS,
        u'nicknames':	CL_OB_ALIASES,
        u'ou':		CL_OB_ORG,
        CL_OB_SCHEMAS:	CL_OB_SCHEMA,
        CL_OB_SITES:	CL_OB_SITE,
        u'verification':CL_OB_VERIFY,
       },
    },
  u'delete':
    {CMD_ACTION: AC_DELETE,
     CMD_FUNCTION:
       {CL_OB_ADMIN:	doDeleteAdmin,
        CL_OB_ALIAS:	doDeleteAlias,
        CL_OB_ALIASES:	doDeleteAliases,
        CL_OB_CONTACTS:	doDeleteDomainContacts,
        CL_OB_COURSE:	doDeleteCourse,
        CL_OB_COURSES:	doDeleteCourses,
        CL_OB_DOMAIN:	doDeleteDomain,
        CL_OB_DOMAIN_ALIAS:	doDeleteDomainAlias,
        CL_OB_GROUP:	doDeleteGroup,
        CL_OB_GROUPS:	doDeleteGroups,
        CL_OB_GUARDIAN: doDeleteGuardian,
        CL_OB_MOBILES:	doDeleteMobileDevices,
        CL_OB_NOTIFICATION:	doDeleteNotification,
        CL_OB_ORG:	doDeleteOrg,
        CL_OB_ORGS:	doDeleteOrgs,
        CL_OB_PRINTER:	doDeletePrinter,
        CL_OB_PRINTERS:	doDeletePrinters,
        CL_OB_RESOURCE:	doDeleteResourceCalendar,
        CL_OB_RESOURCES:doDeleteResourceCalendars,
        CL_OB_SCHEMA:	doDeleteUserSchema,
        CL_OB_SCHEMAS:	doDeleteUserSchemas,
        CL_OB_SITEACLS:	doProcessDomainSiteACLs,
        CL_OB_USER:	doDeleteUser,
        CL_OB_USERS:	doDeleteUsers,
       },
     CMD_OBJ_ALIASES:
       {u'aliasdomain':	CL_OB_DOMAIN_ALIAS,
        u'aliasdomains':	CL_OB_DOMAIN_ALIAS,
        u'class':	CL_OB_COURSE,
        CL_OB_CONTACT:	CL_OB_CONTACTS,
        CL_OB_DOMAIN_ALIASES:	CL_OB_DOMAIN_ALIAS,
        CL_OB_GUARDIANS:	CL_OB_GUARDIAN,
        CL_OB_MOBILE:	CL_OB_MOBILES,
        u'nickname':	CL_OB_ALIAS,
        u'nicknames':	CL_OB_ALIASES,
        u'ou':		CL_OB_ORG,
        u'ous':		CL_OB_ORGS,
        u'print':	CL_OB_PRINTER,
        u'notifications':	CL_OB_NOTIFICATION,
        CL_OB_SITEACL:	CL_OB_SITEACLS,
       },
    },
  u'info':
    {CMD_ACTION: AC_INFO,
     CMD_FUNCTION:
       {CL_OB_ALIAS:	doInfoAlias,
        CL_OB_ALIASES:	doInfoAliases,
        CL_OB_CONTACTS:	doInfoDomainContacts,
        CL_OB_COURSE:	doInfoCourse,
        CL_OB_COURSES:	doInfoCourses,
        CL_OB_CROSES:	doInfoCrOSDevices,
        CL_OB_CUSTOMER:	doInfoCustomer,
        CL_OB_DATA_TRANSFER:doInfoDataTransfer,
        CL_OB_DOMAIN:	doInfoDomain,
        CL_OB_DOMAIN_ALIAS:	doInfoDomainAlias,
        CL_OB_INSTANCE:	doInfoInstance,
        CL_OB_GROUP:	doInfoGroup,
        CL_OB_GROUPS:	doInfoGroups,
        CL_OB_MOBILES:	doInfoMobileDevices,
        CL_OB_NOTIFICATION:	doInfoNotifications,
        CL_OB_ORG:	doInfoOrg,
        CL_OB_ORGS:	doInfoOrgs,
        CL_OB_PRINTER:	doInfoPrinter,
        CL_OB_PRINTERS:	doInfoPrinters,
        CL_OB_RESOURCE:	doInfoResourceCalendar,
        CL_OB_RESOURCES:doInfoResourceCalendars,
        CL_OB_SCHEMA:	doInfoUserSchema,
        CL_OB_SCHEMAS:	doInfoUserSchemas,
        CL_OB_SITES:	doInfoDomainSites,
        CL_OB_SITEACLS:	doProcessDomainSiteACLs,
        CL_OB_USER:	doInfoUser,
        CL_OB_USERS:	doInfoUsers,
        CL_OB_VERIFY:	doInfoSiteVerification,
       },
     CMD_OBJ_ALIASES:
       {u'aliasdomain':	CL_OB_DOMAIN_ALIAS,
        u'aliasdomains':	CL_OB_DOMAIN_ALIAS,
        u'class':	CL_OB_COURSE,
        CL_OB_CONTACT:	CL_OB_CONTACTS,
        CL_OB_CROS:	CL_OB_CROSES,
        CL_OB_DOMAIN_ALIASES:	CL_OB_DOMAIN_ALIAS,
        CL_OB_MOBILE:	CL_OB_MOBILES,
        u'nickname':	CL_OB_ALIAS,
        u'nicknames':	CL_OB_ALIASES,
        u'notifications':	CL_OB_NOTIFICATION,
        u'ou':		CL_OB_ORG,
        u'ous':		CL_OB_ORGS,
        u'print':	CL_OB_PRINTER,
        CL_OB_SITE:	CL_OB_SITES,
        CL_OB_SITEACL:	CL_OB_SITEACLS,
        u'transfer':	CL_OB_DATA_TRANSFER,
        u'verification':CL_OB_VERIFY,
       },
    },
  u'print':
    {CMD_ACTION: AC_PRINT,
     CMD_FUNCTION:
       {CL_OB_ADMINROLES:	doPrintAdminRoles,
        CL_OB_ADMINS:	doPrintAdmins,
        CL_OB_ALIASES:	doPrintAliases,
        CL_OB_CONTACTS:	doPrintDomainContacts,
        CL_OB_COURSES:	doPrintCourses,
        CL_OB_COURSE_PARTICIPANTS:	doPrintCourseParticipants,
        CL_OB_CROS:	doPrintCrOSDevices,
        CL_OB_DATA_TRANSFERS:	doPrintDataTransfers,
        CL_OB_DOMAINS:	doPrintDomains,
        CL_OB_DOMAIN_ALIASES:	doPrintDomainAliases,
        CL_OB_GROUP_MEMBERS: doPrintGroupMembers,
        CL_OB_GROUPS:	doPrintGroups,
        CL_OB_GUARDIANS: doPrintGuardians,
        CL_OB_LICENSES:	doPrintLicenses,
        CL_OB_MOBILE:	doPrintMobileDevices,
        CL_OB_ORGS:	doPrintOrgs,
        CL_OB_PRINTERS:	doPrintPrinters,
        CL_OB_PRINTJOBS:doPrintPrintJobs,
        CL_OB_ORGS:	doPrintOrgs,
        CL_OB_RESOURCES:doPrintResourceCalendars,
        CL_OB_SCHEMAS:	doPrintUserSchemas,
        CL_OB_SITES:	doPrintDomainSites,
        CL_OB_SITEACTIVITY:	doPrintDomainSiteActivity,
        CL_OB_TOKENS:	doPrintTokens,
        CL_OB_TRANSFERAPPS:	doPrintTransferApps,
        CL_OB_USERS:	doPrintUsers,
       },
     CMD_OBJ_ALIASES:
       {u'aliasdomain':		CL_OB_DOMAIN_ALIASES,
        u'aliasdomains':	CL_OB_DOMAIN_ALIASES,
        u'classes':		CL_OB_COURSES,
        CL_OB_CONTACT:		CL_OB_CONTACTS,
        u'transfers':		CL_OB_DATA_TRANSFERS,
        u'classparticipants':	CL_OB_COURSE_PARTICIPANTS,
        u'class-participants':	CL_OB_COURSE_PARTICIPANTS,
        CL_OB_DOMAIN_ALIAS:	CL_OB_DOMAIN_ALIASES,
        u'groupmembers':	CL_OB_GROUP_MEMBERS,
        u'groupsmembers':	CL_OB_GROUP_MEMBERS,
        u'groups-members':	CL_OB_GROUP_MEMBERS,
        CL_OB_GUARDIAN:		CL_OB_GUARDIANS,
        u'license':		CL_OB_LICENSES,
        u'licence':		CL_OB_LICENSES,
        u'licences':		CL_OB_LICENSES,
        u'nicknames':		CL_OB_ALIASES,
        u'ous':			CL_OB_ORGS,
        u'roles':		CL_OB_ADMINROLES,
        CL_OB_SCHEMA:		CL_OB_SCHEMAS,
        CL_OB_SITE:		CL_OB_SITES,
        CL_OB_TOKEN:		CL_OB_TOKENS,
       },
    },
  u'show':
    {CMD_ACTION: AC_SHOW,
     CMD_FUNCTION:
       {CL_OB_CONTACTS:	doShowDomainContacts,
        CL_OB_GUARDIANS: doShowGuardians,
        CL_OB_SCHEMAS:	doShowUserSchemas,
        CL_OB_SITES:	doShowDomainSites,
        CL_OB_SITEACLS:	doProcessDomainSiteACLs,
       },
     CMD_OBJ_ALIASES:
       {CL_OB_CONTACT:	CL_OB_CONTACTS,
        CL_OB_GUARDIAN:	CL_OB_GUARDIANS,
        CL_OB_SCHEMA:	CL_OB_SCHEMAS,
        CL_OB_SITE:	CL_OB_SITES,
        CL_OB_SITEACL:	CL_OB_SITEACLS,
       },
    },
  u'update':
    {CMD_ACTION: AC_UPDATE,
     CMD_FUNCTION:
       {CL_OB_ALIAS:	doUpdateAlias,
        CL_OB_ALIASES:	doUpdateAliases,
        CL_OB_CONTACTS:	doUpdateDomainContacts,
        CL_OB_COURSE:	doUpdateCourse,
        CL_OB_COURSES:	doUpdateCourses,
        CL_OB_CROSES:	doUpdateCrOSDevices,
        CL_OB_CUSTOMER:	doUpdateCustomer,
        CL_OB_DOMAIN:	doUpdateDomain,
        CL_OB_INSTANCE:	doUpdateInstance,
        CL_OB_GROUP:	doUpdateGroup,
        CL_OB_GROUPS:	doUpdateGroups,
        CL_OB_MOBILES:	doUpdateMobileDevices,
        CL_OB_NOTIFICATION:	doUpdateNotification,
        CL_OB_ORG:	doUpdateOrg,
        CL_OB_ORGS:	doUpdateOrgs,
        CL_OB_PRINTER:	doUpdatePrinter,
        CL_OB_PRINTERS:	doUpdatePrinters,
        CL_OB_RESOURCE:	doUpdateResourceCalendar,
        CL_OB_RESOURCES:doUpdateResourceCalendars,
        CL_OB_SCHEMA:	doUpdateUserSchema,
        CL_OB_SCHEMAS:	doUpdateUserSchemas,
        CL_OB_SITES:	doUpdateDomainSites,
        CL_OB_SITEACLS:	doProcessDomainSiteACLs,
        CL_OB_USER:	doUpdateUser,
        CL_OB_USERS:	doUpdateUsers,
        CL_OB_VERIFY:	doUpdateSiteVerification,
       },
     CMD_OBJ_ALIASES:
       {u'class':	CL_OB_COURSE,
        CL_OB_CONTACT:	CL_OB_CONTACTS,
        CL_OB_CROS:	CL_OB_CROSES,
        CL_OB_MOBILE:	CL_OB_MOBILES,
        u'nickname':	CL_OB_ALIAS,
        u'nicknames':	CL_OB_ALIASES,
        u'ou':		CL_OB_ORG,
        u'ous':		CL_OB_ORGS,
        u'print':	CL_OB_PRINTER,
        u'notifications':	CL_OB_NOTIFICATION,
        CL_OB_SITE:	CL_OB_SITES,
        CL_OB_SITEACL:	CL_OB_SITEACLS,
        u'verification':CL_OB_VERIFY,
       },
    },
  u'undelete':
    {CMD_ACTION: AC_UNDELETE,
     CMD_FUNCTION:
       {CL_OB_USER:	doUndeleteUser,
        CL_OB_USERS:	doUndeleteUsers,
       },
     CMD_OBJ_ALIASES:
       {
       },
    },
  }

# Oauth command sub-commands
OAUTH2_SUBCOMMANDS = {
  u'create':	{CMD_ACTION: AC_CREATE, CMD_FUNCTION: doOAuthRequest},
  u'delete':	{CMD_ACTION: AC_DELETE, CMD_FUNCTION: doOAuthDelete},
  u'info':	{CMD_ACTION: AC_INFO, CMD_FUNCTION: doOAuthInfo},
  }

# Oauth sub-command aliases
OAUTH2_SUBCOMMAND_ALIASES = {
  u'request':	u'create',
  u'revoke':	u'delete',
  u'verify':	u'info',
  }

def processOauthCommands():
  CL_subCommand = getChoice(OAUTH2_SUBCOMMANDS, choiceAliases=OAUTH2_SUBCOMMAND_ALIASES)
  setActionName(OAUTH2_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
  OAUTH2_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION]()

# Audit command sub-commands
AUDIT_SUBCOMMANDS = {
  u'uploadkey': {CMD_ACTION: AC_UPLOAD, CMD_FUNCTION: doUploadAuditKey},
  }

# Audit command sub-commands with objects
AUDIT_SUBCOMMANDS_WITH_OBJECTS = {
  u'activity':
    {u'request':{CMD_ACTION: AC_SUBMIT, CMD_FUNCTION: doSubmitActivityRequest},
     u'delete':	{CMD_ACTION: AC_DELETE, CMD_FUNCTION: doDeleteActivityRequest},
     u'download':	{CMD_ACTION: AC_DOWNLOAD, CMD_FUNCTION: doDownloadActivityRequest},
     u'status':	{CMD_ACTION: AC_LIST, CMD_FUNCTION: doStatusActivityRequests},
    },
  u'export':
    {u'request':{CMD_ACTION: AC_SUBMIT, CMD_FUNCTION: doSubmitExportRequest},
     u'delete':	{CMD_ACTION: AC_DELETE, CMD_FUNCTION: doDeleteExportRequest},
     u'download':	{CMD_ACTION: AC_DOWNLOAD, CMD_FUNCTION: doDownloadExportRequest},
     u'status':	{CMD_ACTION: AC_LIST, CMD_FUNCTION: doStatusExportRequests},
     u'watch':	{CMD_ACTION: AC_WATCH, CMD_FUNCTION: doWatchExportRequest},
    },
  u'monitor':
    {u'create':	{CMD_ACTION: AC_CREATE, CMD_FUNCTION: doCreateMonitor},
     u'delete':	{CMD_ACTION: AC_DELETE, CMD_FUNCTION: doDeleteMonitor},
     u'list':	{CMD_ACTION: AC_LIST, CMD_FUNCTION: doShowMonitors},
    },
  }

def processAuditCommands():
  CL_subCommand = getChoice(AUDIT_SUBCOMMANDS.keys()+AUDIT_SUBCOMMANDS_WITH_OBJECTS.keys())
  if CL_subCommand in AUDIT_SUBCOMMANDS:
    setActionName(AUDIT_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
    AUDIT_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION]()
  else:
    CL_objectName = getChoice(AUDIT_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand])
    setActionName(AUDIT_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CL_objectName][CMD_ACTION])
    AUDIT_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CL_objectName][CMD_FUNCTION]()

# Calendar command sub-commands
CALENDAR_SUBCOMMANDS = {
  u'add':	{CMD_ACTION: AC_ADD, CMD_FUNCTION: doCalendarAddACL},
  u'delete':	{CMD_ACTION: AC_DELETE, CMD_FUNCTION: doCalendarDeleteACL},
  u'update':	{CMD_ACTION: AC_UPDATE, CMD_FUNCTION: doCalendarUpdateACL},
  u'showacl':	{CMD_ACTION: AC_SHOW, CMD_FUNCTION: doCalendarShowACLs},
  u'addevent':	{CMD_ACTION: AC_ADD, CMD_FUNCTION: doCalendarAddEvent},
  u'wipe':	{CMD_ACTION: AC_WIPE, CMD_FUNCTION: doCalendarWipeEvents},
  }

# Calendar sub-command aliases
CALENDAR_SUBCOMMAND_ALIASES = {
  u'del':	u'delete',
  }

def processCalendarCommands():
  cal = buildGAPIObject(GAPI_CALENDAR_API)
  calendarList = getStringReturnInList(OB_EMAIL_ADDRESS)
  CL_subCommand = getChoice(CALENDAR_SUBCOMMANDS, choiceAliases=CALENDAR_SUBCOMMAND_ALIASES)
  setActionName(CALENDAR_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
  CALENDAR_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION](cal, calendarList)

# Calendars command sub-commands with objects
CALENDARS_SUBCOMMANDS_WITH_OBJECTS = {
  u'add':
    {CMD_ACTION: AC_ADD,
     CMD_FUNCTION:
       {u'acl':		doCalendarAddACL,
        u'acls':	doCalendarAddACLs,
        u'event':	doCalendarAddEvent,
       },
    },
  u'update':
    {CMD_ACTION: AC_UPDATE,
     CMD_FUNCTION:
       {u'acl':		doCalendarUpdateACL,
        u'acls':	doCalendarUpdateACLs,
        u'event':	doCalendarUpdateEvent,
       },
    },
  u'delete':
    {CMD_ACTION: AC_DELETE,
     CMD_FUNCTION:
       {u'acl':		doCalendarDeleteACL,
        u'acls':	doCalendarDeleteACLs,
        u'event':	doCalendarDeleteEvent,
       },
    },
  u'info':
    {CMD_ACTION: AC_INFO,
     CMD_FUNCTION:
       {u'acl':		doCalendarInfoACLs,
        u'acls':	doCalendarInfoACLs,
        u'event':	doCalendarInfoEvent,
       },
    },
  u'move':
    {CMD_ACTION: AC_MOVE,
     CMD_FUNCTION:
       {u'event':	doCalendarMoveEvent,
       },
    },
  u'print':
    {CMD_ACTION: AC_PRINT,
     CMD_FUNCTION:
       {u'events':	doCalendarPrintEvents,
       },
    },
  u'show':
    {CMD_ACTION: AC_SHOW,
     CMD_FUNCTION:
       {u'acls':	doCalendarShowACLs,
        u'events':	doCalendarShowEvents,
       },
    },
  u'wipe':
    {CMD_ACTION: AC_WIPE,
     CMD_FUNCTION:
       {u'acls':	doCalendarWipeACLs,
        u'events':	doCalendarWipeEvents,
       },
    },
  }

# Calendars sub-command aliases
CALENDARS_SUBCOMMAND_ALIASES = {
  u'del':	u'delete',
  }

def processCalendarsCommands():
  cal = buildGAPIObject(GAPI_CALENDAR_API)
  calendarList = getEntityList(OB_EMAIL_ADDRESS_ENTITY)
  CL_subCommand = getChoice(CALENDARS_SUBCOMMANDS_WITH_OBJECTS, choiceAliases=CALENDARS_SUBCOMMAND_ALIASES)
  setActionName(CALENDARS_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_ACTION])
  CL_objectName = getChoice(CALENDARS_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION])
  CALENDARS_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION][CL_objectName](cal, calendarList)

# Course command sub-commands
COURSE_SUBCOMMANDS = {
  u'add':	{CMD_ACTION: AC_ADD, CMD_FUNCTION: doCourseAddParticipants},
  u'remove':	{CMD_ACTION: AC_REMOVE, CMD_FUNCTION: doCourseRemoveParticipants},
  u'sync':	{CMD_ACTION: AC_SYNC, CMD_FUNCTION: doCourseSyncParticipants},
  }

# Course sub-command aliases
COURSE_SUBCOMMAND_ALIASES = {
  u'create':	u'add',
  u'del':	u'remove',
  u'delete':	u'remove',
  }

def executeCourseCommands(courseIdList, getEntityListArg):
  CL_subCommand = getChoice(COURSE_SUBCOMMANDS, choiceAliases=COURSE_SUBCOMMAND_ALIASES)
  setActionName(COURSE_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
  COURSE_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION](courseIdList, getEntityListArg)

def processCourseCommands():
  executeCourseCommands(getStringReturnInList(OB_COURSE_ID), False)

def processCoursesCommands():
  executeCourseCommands(getEntityList(OB_COURSE_ENTITY), True)

# Printer command sub-commands
PRINTER_SUBCOMMANDS = {
  u'add':	{CMD_ACTION: AC_ADD, CMD_FUNCTION: doPrinterAddACL},
  u'delete':	{CMD_ACTION: AC_DELETE, CMD_FUNCTION: doPrinterDeleteACL},
  u'showacl':	{CMD_ACTION: AC_SHOW, CMD_FUNCTION: doPrinterShowACL},
  u'sync':	{CMD_ACTION: AC_SYNC, CMD_FUNCTION: doPrinterSyncACL},
  u'wipe':	{CMD_ACTION: AC_WIPE, CMD_FUNCTION: doPrinterWipeACL},
  }

# Printer sub-command aliases
PRINTER_SUBCOMMAND_ALIASES = {
  u'del':	u'delete',
  u'remove':	u'delete',
  }

def executePrinterCommands(printerIdList, getEntityListArg):
  if printerIdList[0] == u'register':
    setActionName(AC_REGISTER)
    doPrinterRegister()
    return
  CL_subCommand = getChoice(PRINTER_SUBCOMMANDS, choiceAliases=PRINTER_SUBCOMMAND_ALIASES)
  setActionName(PRINTER_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
  PRINTER_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION](printerIdList, getEntityListArg)

def processPrinterCommands():
  executePrinterCommands(getStringReturnInList(OB_PRINTER_ID), False)

def processPrintersCommands():
  executePrinterCommands(getEntityList(OB_PRINTER_ID_ENTITY), True)

# Printjob command sub-commands
PRINTJOB_SUBCOMMANDS = {
  u'cancel':	{CMD_ACTION: AC_CANCEL, CMD_FUNCTION: doPrintJobCancel},
  u'delete':	{CMD_ACTION: AC_DELETE, CMD_FUNCTION: doPrintJobDelete},
  u'fetch':	{CMD_ACTION: AC_DOWNLOAD, CMD_FUNCTION: doPrintJobFetch},
  u'resubmit':	{CMD_ACTION: AC_RESUBMIT, CMD_FUNCTION: doPrintJobResubmit},
  u'submit':	{CMD_ACTION: AC_SUBMIT, CMD_FUNCTION: doPrintJobSubmit},
  }

def executePrintjobCommands(jobPrinterIdList):
  CL_subCommand = getChoice(PRINTJOB_SUBCOMMANDS)
  setActionName(PRINTJOB_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
  PRINTJOB_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION](jobPrinterIdList)

def processPrintjobCommands():
  executePrintjobCommands(getStringReturnInList(OB_JOB_OR_PRINTER_ID))

def processPrintjobsCommands():
  executePrintjobCommands(getEntityList(OB_PRINTER_ID_ENTITY))

# Commands
COMMANDS_MAP = {
  u'oauth':	processOauthCommands,
  u'audit':	processAuditCommands,
  u'calendar':	processCalendarCommands,
  u'calendars':	processCalendarsCommands,
  u'course':	processCourseCommands,
  u'courses':	processCoursesCommands,
  u'printer':	processPrinterCommands,
  u'printers':	processPrintersCommands,
  u'printjob':	processPrintjobCommands,
  u'printjobs':	processPrintjobsCommands,
  }

# Commands aliases
COMMANDS_ALIASES = {
  u'oauth2':	u'oauth',
  u'site':	u'sites',
  }

# <CrOSTypeEntity> commands
CROS_COMMANDS = {
  u'info':	{CMD_ACTION: AC_INFO, CMD_FUNCTION: infoCrOSDevices},
  u'list':	{CMD_ACTION: AC_LIST, CMD_FUNCTION: doListCrOS},
  u'print':	{CMD_ACTION: AC_PRINT, CMD_FUNCTION: doPrintCrOSEntity},
  u'update':	{CMD_ACTION: AC_UPDATE, CMD_FUNCTION: updateCrOSDevices},
  }

# <UserTypeEntity> commands
USER_COMMANDS = {
  u'arrows':	{CMD_ACTION: AC_SET, CMD_FUNCTION: setArrows},
  CL_OB_DELEGATE:	{CMD_ACTION: AC_ADD, CMD_FUNCTION: delegateTo},
  u'deprovision':	{CMD_ACTION: AC_DEPROVISION, CMD_FUNCTION: deprovisionUser},
  CL_OB_FILTER:	{CMD_ACTION: AC_ADD, CMD_FUNCTION: addFilter},
  CL_OB_FORWARD:	{CMD_ACTION: AC_SET, CMD_FUNCTION: setForward},
  CL_OB_IMAP:	{CMD_ACTION: AC_SET, CMD_FUNCTION: setImap},
  u'label':	{CMD_ACTION: AC_ADD, CMD_FUNCTION: addLabel},
  u'list':	{CMD_ACTION: AC_LIST, CMD_FUNCTION: doListUser},
  u'language':	{CMD_ACTION: AC_SET, CMD_FUNCTION: setLanguage},
  u'pagesize':	{CMD_ACTION: AC_SET, CMD_FUNCTION: setPageSize},
  CL_OB_POP:	{CMD_ACTION: AC_SET, CMD_FUNCTION: setPop},
  CL_OB_PROFILE:	{CMD_ACTION: AC_SET, CMD_FUNCTION: setProfile},
  CL_OB_SENDAS:	{CMD_ACTION: AC_ADD, CMD_FUNCTION: addSendAs},
  u'shortcuts':	{CMD_ACTION: AC_SET, CMD_FUNCTION: setShortCuts},
  u'signature':	{CMD_ACTION: AC_SET, CMD_FUNCTION: setSignature},
  u'snippets':	{CMD_ACTION: AC_SET, CMD_FUNCTION: setSnippets},
  u'unicode':	{CMD_ACTION: AC_SET, CMD_FUNCTION: setUnicode},
  CL_OB_VACATION:	{CMD_ACTION: AC_SET, CMD_FUNCTION: setVacation},
  u'webclips':	{CMD_ACTION: AC_SET, CMD_FUNCTION: setWebClips},
  }

# User commands with objects
#
USER_COMMANDS_WITH_OBJECTS = {
  u'add':
    {CMD_ACTION: AC_ADD,
     CMD_FUNCTION:
       {CL_OB_CALENDAR:	addCalendar,
        CL_OB_CALENDARS:addCalendars,
        CL_OB_DELEGATE:	addDelegate,
        CL_OB_DRIVEFILE:addDriveFile,
        CL_OB_DRIVEFILEACL:	addDriveFileACL,
        CL_OB_FILTER:	addFilter,
        CL_OB_FORWARDINGADDRESSES:	addForwardingAddresses,
        CL_OB_GROUP:	addUserToGroups,
        CL_OB_LABEL:	addLabel,
        CL_OB_LICENSE:	addLicense,
        CL_OB_SENDAS:	addSendAs,
        CL_OB_SITEACLS:	processUserSiteACLs,
       },
     CMD_OBJ_ALIASES:
       {CL_OB_DELEGATES:	CL_OB_DELEGATE,
        CL_OB_FILTERS:	CL_OB_FILTER,
        CL_OB_FORWARDINGADDRESS:	CL_OB_FORWARDINGADDRESSES,
        CL_OB_GROUPS:	CL_OB_GROUP,
        CL_OB_LABELS:	CL_OB_LABEL,
        u'licence':	CL_OB_LICENSE,
        CL_OB_SITEACL:	CL_OB_SITEACLS,
       },
    },
  u'claim':
    {CMD_ACTION: AC_CLAIM,
     CMD_FUNCTION:
       {CL_OB_OWNERSHIP: claimDriveFolderOwnership,
       },
     CMD_OBJ_ALIASES:
       {
       },
    },
  u'copy':
    {CMD_ACTION: AC_COPY,
     CMD_FUNCTION:
       {CL_OB_DRIVEFILE:copyDriveFile,
       },
     CMD_OBJ_ALIASES:
       {
       },
    },
  u'create':
    {CMD_ACTION: AC_CREATE,
     CMD_FUNCTION:
       {CL_OB_CALENDAR:	createCalendar,
        CL_OB_CALENDARS:createCalendar,
        CL_OB_CONTACT:	createUserContact,
        CL_OB_CONTACT_GROUP:	createUserContactGroup,
        CL_OB_SITE:	createUserSite,
       },
     CMD_OBJ_ALIASES:
       {CL_OB_CONTACTS:	CL_OB_CONTACT,
        CL_OB_CONTACT_GROUPS:	CL_OB_CONTACT_GROUP,
        CL_OB_SITES:	CL_OB_SITE,
       },
    },
  u'delete':
    {CMD_ACTION: AC_DELETE,
     CMD_FUNCTION:
       {CL_OB_ALIAS:	deleteUsersAliases,
        CL_OB_ASP:	deleteASP,
        CL_OB_BACKUPCODES:	deleteBackupCodes,
        CL_OB_CALENDAR:	deleteCalendar,
        CL_OB_CALENDARS:deleteCalendars,
        CL_OB_CONTACTS:	deleteUserContacts,
        CL_OB_CONTACT_GROUPS:	deleteUserContactGroups,
        CL_OB_DELEGATE:	deleteDelegate,
        CL_OB_DRIVEFILE:	deleteDriveFile,
        CL_OB_DRIVEFILEACL:	deleteDriveFileACL,
        CL_OB_EMPTYDRIVEFOLDERS:	deleteEmptyDriveFolders,
        CL_OB_FILTERS:	deleteFilters,
        CL_OB_FORWARDINGADDRESSES:	deleteForwardingAddresses,
        CL_OB_GROUP:	deleteUserFromGroups,
        CL_OB_LABEL:	deleteLabel,
        CL_OB_LICENSE:	deleteLicense,
        CL_OB_MESSAGES:	processMessages,
        CL_OB_PHOTO:	deletePhoto,
        CL_OB_SENDAS:	deleteSendAs,
        CL_OB_SITEACLS:	processUserSiteACLs,
        CL_OB_THREADS:	processThreads,
        CL_OB_TOKEN:	deleteTokens,
       },
     CMD_OBJ_ALIASES:
       {u'aliases':	CL_OB_ALIAS,
        u'applicationspecificpasswords':	CL_OB_ASP,
        u'asps':	CL_OB_ASP,
        u'backupcode':	CL_OB_BACKUPCODES,
        u'verificationcodes':	CL_OB_BACKUPCODES,
        CL_OB_CONTACT:	CL_OB_CONTACTS,
        CL_OB_CONTACT_GROUP:	CL_OB_CONTACT_GROUPS,
        CL_OB_DELEGATES:	CL_OB_DELEGATE,
        CL_OB_FILTER:	CL_OB_FILTERS,
        CL_OB_GROUPS:	CL_OB_GROUP,
        u'licence':	CL_OB_LICENSE,
        CL_OB_LABELS:	CL_OB_LABEL,
        CL_OB_MESSAGE:	CL_OB_MESSAGES,
        CL_OB_SITEACL:	CL_OB_SITEACLS,
        CL_OB_THREAD:	CL_OB_THREADS,
        CL_OB_TOKENS:	CL_OB_TOKEN,
        u'3lo':		CL_OB_TOKEN,
        u'oauth':	CL_OB_TOKEN,
       },
    },
  u'empty':
    {CMD_ACTION: AC_EMPTY,
     CMD_FUNCTION:
       {CL_OB_DRIVETRASH:	emptyDriveTrash,
       },
     CMD_OBJ_ALIASES:
       {
       },
    },
  u'get':
    {CMD_ACTION: AC_DOWNLOAD,
     CMD_FUNCTION:
       {CL_OB_DRIVEFILE:getDriveFile,
        CL_OB_PHOTO:	getPhoto,
       },
     CMD_OBJ_ALIASES:
       {
       },
    },
  u'info':
    {CMD_ACTION: AC_INFO,
     CMD_FUNCTION:
       {CL_OB_CALENDAR:	infoCalendar,
        CL_OB_CALENDARS:infoCalendars,
        CL_OB_CONTACTS:	infoUserContacts,
        CL_OB_CONTACT_GROUPS:	infoUserContactGroups,
        CL_OB_FILTERS:	infoFilters,
        CL_OB_FORWARDINGADDRESSES:	infoForwardingAddresses,
        CL_OB_SENDAS:	infoSendAs,
        CL_OB_SITES:	infoUserSites,
        CL_OB_SITEACLS:	processUserSiteACLs,
       },
     CMD_OBJ_ALIASES:
       {CL_OB_CONTACT:	CL_OB_CONTACTS,
        CL_OB_CONTACT_GROUP:	CL_OB_CONTACT_GROUPS,
        CL_OB_FILTER:	CL_OB_FILTERS,
        CL_OB_FORWARDINGADDRESS:	CL_OB_FORWARDINGADDRESSES,
        CL_OB_SITE:	CL_OB_SITES,
        CL_OB_SITEACL:	CL_OB_SITEACLS,
       },
    },
  u'modify':
    {CMD_ACTION: AC_MODIFY,
     CMD_FUNCTION:
       {CL_OB_CALENDAR:	modifyCalendar,
        CL_OB_CALENDARS:modifyCalendars,
        CL_OB_MESSAGES:	processMessages,
        CL_OB_THREADS:	processThreads,
       },
     CMD_OBJ_ALIASES:
       {CL_OB_MESSAGE:	CL_OB_MESSAGES,
        CL_OB_THREAD:	CL_OB_THREADS,
       },
    },
  u'purge':
    {CMD_ACTION: AC_PURGE,
     CMD_FUNCTION:
       {CL_OB_DRIVEFILE:	purgeDriveFile,
       },
     CMD_OBJ_ALIASES:
       {
       },
    },
  u'print':
    {CMD_ACTION: AC_PRINT,
     CMD_FUNCTION:
       {CL_OB_CALENDARS:	printCalendars,
        CL_OB_CONTACTS:	printUserContacts,
        CL_OB_CONTACT_GROUPS:	printUserContactGroups,
        CL_OB_DELEGATES:	printDelegates,
        CL_OB_DRIVEACTIVITY:	printDriveActivity,
        CL_OB_DRIVESETTINGS:	printDriveSettings,
        CL_OB_FILELIST:	printDriveFileList,
        CL_OB_FILTERS:	printFilters,
        CL_OB_FORWARD:	printForward,
        CL_OB_FORWARDINGADDRESSES:	printForwardingAddresses,
        CL_OB_GMAILPROFILE:	printGmailProfile,
        CL_OB_GPLUSPROFILE:	printGplusProfile,
        CL_OB_MESSAGES:	printMessages,
        CL_OB_SENDAS:	printSendAs,
        CL_OB_SITES:	printUserSites,
        CL_OB_SITEACTIVITY:	printUserSiteActivity,
        CL_OB_THREADS:	printThreads,
        CL_OB_TOKENS:	printTokens,
        CL_OB_USERS:	doPrintUserEntity,
       },
     CMD_OBJ_ALIASES:
       {CL_OB_CALENDAR:	CL_OB_CALENDARS,
        CL_OB_CONTACT:	CL_OB_CONTACTS,
        CL_OB_CONTACT_GROUP:	CL_OB_CONTACT_GROUPS,
        CL_OB_DELEGATE:	CL_OB_DELEGATES,
        CL_OB_FILTER:	CL_OB_FILTERS,
        CL_OB_FORWARDINGADDRESS:	CL_OB_FORWARDINGADDRESSES,
        CL_OB_MESSAGE:	CL_OB_MESSAGES,
        CL_OB_SITE:	CL_OB_SITES,
        CL_OB_THREAD:	CL_OB_THREADS,
        CL_OB_TOKEN:	CL_OB_TOKENS,
        u'3lo':		CL_OB_TOKENS,
        u'oauth':	CL_OB_TOKENS,
        CL_OB_USER:	CL_OB_USERS,
       },
    },
  u'remove':
    {CMD_ACTION: AC_REMOVE,
     CMD_FUNCTION:
       {CL_OB_CALENDAR:	removeCalendar,
        CL_OB_CALENDARS:removeCalendars,
       },
     CMD_OBJ_ALIASES:
       {
       },
    },
  u'show':
    {CMD_ACTION: AC_SHOW,
     CMD_FUNCTION:
       {CL_OB_ASPS:	showASPs,
        CL_OB_BACKUPCODES:	showBackupCodes,
        CL_OB_CALENDARS:	showCalendars,
        CL_OB_CALSETTINGS:	showCalSettings,
        CL_OB_CONTACTS:	showUserContacts,
        CL_OB_CONTACT_GROUPS:	showUserContactGroups,
        CL_OB_DELEGATES:	showDelegates,
        CL_OB_DRIVEACTIVITY:	printDriveActivity,
        CL_OB_DRIVEFILEACL:	showDriveFileACL,
        CL_OB_DRIVESETTINGS:	printDriveSettings,
        CL_OB_FILEINFO:	showDriveFileInfo,
        CL_OB_FILELIST:	printDriveFileList,
        CL_OB_FILEPATH:	showDriveFilePath,
        CL_OB_FILEREVISIONS:	showDriveFileRevisions,
        CL_OB_FILETREE:	showDriveFileTree,
        CL_OB_FILTERS:	showFilters,
        CL_OB_FORWARD:	showForward,
        CL_OB_FORWARDINGADDRESSES:	showForwardingAddresses,
        CL_OB_GMAILPROFILE:	showGmailProfile,
        CL_OB_GPLUSPROFILE:	showGplusProfile,
        CL_OB_IMAP:	showImap,
        CL_OB_LABELS:	showLabels,
        CL_OB_MESSAGES:	showMessages,
        CL_OB_POP:	showPop,
        CL_OB_PROFILE:	showProfile,
        CL_OB_SENDAS:	showSendAs,
        CL_OB_SIGNATURE:showSignature,
        CL_OB_SITES:	showUserSites,
        CL_OB_SITEACLS:	processUserSiteACLs,
        CL_OB_THREADS:	showThreads,
        CL_OB_TOKENS:	showTokens,
        CL_OB_VACATION:	showVacation,
       },
     CMD_OBJ_ALIASES:
       {u'applicationspecificpasswords':	CL_OB_ASP,
        u'asp':		CL_OB_ASPS,
        u'backupcode':	CL_OB_BACKUPCODES,
        u'verificationcodes':	CL_OB_BACKUPCODES,
        CL_OB_CALENDAR:	CL_OB_CALENDARS,
        CL_OB_CONTACT:	CL_OB_CONTACTS,
        CL_OB_CONTACT_GROUP:	CL_OB_CONTACT_GROUPS,
        CL_OB_DELEGATE:	CL_OB_DELEGATES,
        CL_OB_FILTER:	CL_OB_FILTERS,
        CL_OB_FORWARDINGADDRESS:	CL_OB_FORWARDINGADDRESSES,
        u'imap4':	CL_OB_IMAP,
        u'pop3':	CL_OB_POP,
        CL_OB_LABEL:	CL_OB_LABELS,
        CL_OB_MESSAGE:	CL_OB_MESSAGES,
        u'sig':		CL_OB_SIGNATURE,
        CL_OB_SITE:	CL_OB_SITES,
        CL_OB_SITEACL:	CL_OB_SITEACLS,
        CL_OB_THREAD:	CL_OB_THREADS,
        CL_OB_TOKEN:	CL_OB_TOKENS,
        u'3lo':		CL_OB_TOKENS,
        u'oauth':	CL_OB_TOKENS,
       },
    },
  u'spam':
    {CMD_ACTION: AC_SPAM,
     CMD_FUNCTION:
       {CL_OB_MESSAGES:	processMessages,
        CL_OB_THREADS:	processThreads,
       },
     CMD_OBJ_ALIASES:
       {CL_OB_MESSAGE:	CL_OB_MESSAGES,
        CL_OB_THREAD:	CL_OB_THREADS,
       },
    },
  u'transfer':
    {CMD_ACTION: AC_TRANSFER,
     CMD_FUNCTION:
       {CL_OB_DRIVE:	transferDriveFiles,
        CL_OB_SECCALS:	transferSecCals,
        CL_OB_OWNERSHIP: transferDriveFileOwnership,
       },
     CMD_OBJ_ALIASES:
       {
       },
    },
  u'trash':
    {CMD_ACTION: AC_TRASH,
     CMD_FUNCTION:
       {CL_OB_DRIVEFILE:	trashDriveFile,
        CL_OB_MESSAGES:	processMessages,
        CL_OB_THREADS:	processThreads,
       },
     CMD_OBJ_ALIASES:
       {CL_OB_MESSAGE:	CL_OB_MESSAGES,
        CL_OB_THREAD:	CL_OB_THREADS,
       },
    },
  u'untrash':
    {CMD_ACTION: AC_UNTRASH,
     CMD_FUNCTION:
       {CL_OB_DRIVEFILE:	untrashDriveFile,
        CL_OB_MESSAGES:	processMessages,
        CL_OB_THREADS:	processThreads,
       },
     CMD_OBJ_ALIASES:
       {CL_OB_MESSAGE:	CL_OB_MESSAGES,
        CL_OB_THREAD:	CL_OB_THREADS,
       },
    },
  u'update':
    {CMD_ACTION: AC_UPDATE,
     CMD_FUNCTION:
       {CL_OB_BACKUPCODES:	updateBackupCodes,
        CL_OB_CALATTENDEES:	updateCalendarAttendees,
        CL_OB_CALENDAR:	updateCalendar,
        CL_OB_CALENDARS:updateCalendars,
        CL_OB_CONTACTS:	updateUserContacts,
        CL_OB_CONTACT_GROUP:	updateUserContactGroup,
        CL_OB_DRIVEFILE:updateDriveFile,
        CL_OB_DRIVEFILEACL:	updateDriveFileACL,
        CL_OB_LABELS:	updateLabels,
        CL_OB_LABELSETTINGS:updateLabelSettings,
        CL_OB_LICENSE:	updateLicense,
        CL_OB_PHOTO:	updatePhoto,
        CL_OB_SENDAS:	updateSendAs,
        CL_OB_SITES:	updateUserSites,
        CL_OB_SITEACLS:	processUserSiteACLs,
        CL_OB_USER:	updateUsers,
       },
     CMD_OBJ_ALIASES:
       {u'backupcode':	CL_OB_BACKUPCODES,
        CL_OB_CONTACT:	CL_OB_CONTACTS,
        CL_OB_CONTACT_GROUPS:	CL_OB_CONTACT_GROUP,
        u'verificationcodes':	CL_OB_BACKUPCODES,
        CL_OB_LABEL:	CL_OB_LABELS,
        u'licence':	CL_OB_LICENSE,
        CL_OB_SITE:	CL_OB_SITES,
        CL_OB_SITEACL:	CL_OB_SITEACLS,
       },
    },
  }

# User commands aliases
USER_COMMANDS_ALIASES = {
  u'del':	u'delete',
  CL_OB_DELEGATES:	CL_OB_DELEGATE,
  u'deprov':	u'deprovision',
  u'imap4':	u'imap',
  u'pop3':	u'pop',
  u'sig':	u'signature',
  u'utf':	u'unicode',
  u'utf-8':	u'unicode',
  u'utf8':	u'unicode',
  }

# Process GAM command
def ProcessGAMCommand(args, processGamCfg=True):
  setSysExitRC(0)
  initializeArguments(args)
  resetIndentLevel()
  savedStdout = sys.stdout
  savedStderr = sys.stderr
  try:
    if checkArgumentPresent([LOOP_CMD,]):
      doLoop(processGamCfg=True)
      sys.exit(GM_Globals[GM_SYSEXITRC])
    if processGamCfg and (not SetGlobalVariables()):
      sys.exit(GM_Globals[GM_SYSEXITRC])
    if checkArgumentPresent([LOOP_CMD,]):
      doLoop(processGamCfg=False)
      sys.exit(GM_Globals[GM_SYSEXITRC])
    if CL_argvI == CL_argvLen:
      doUsage()
      sys.exit(GM_Globals[GM_SYSEXITRC])
    CL_command = getChoice(MAIN_COMMANDS, defaultChoice=None)
    if CL_command:
      setActionName(MAIN_COMMANDS[CL_command][CMD_ACTION])
      MAIN_COMMANDS[CL_command][CMD_FUNCTION]()
      sys.exit(GM_Globals[GM_SYSEXITRC])
    CL_command = getChoice(MAIN_COMMANDS_WITH_OBJECTS, defaultChoice=None)
    if CL_command:
      setActionName(MAIN_COMMANDS_WITH_OBJECTS[CL_command][CMD_ACTION])
      CL_objectName = getChoice(MAIN_COMMANDS_WITH_OBJECTS[CL_command][CMD_FUNCTION], choiceAliases=MAIN_COMMANDS_WITH_OBJECTS[CL_command][CMD_OBJ_ALIASES])
      MAIN_COMMANDS_WITH_OBJECTS[CL_command][CMD_FUNCTION][CL_objectName]()
      sys.exit(GM_Globals[GM_SYSEXITRC])
    CL_command = getChoice(COMMANDS_MAP, choiceAliases=COMMANDS_ALIASES, defaultChoice=None)
    if CL_command:
      COMMANDS_MAP[CL_command]()
      sys.exit(GM_Globals[GM_SYSEXITRC])
    GM_Globals[GM_ENTITY_CL_INDEX] = CL_argvI
    entityType, entityList = getEntityToModify(crosAllowed=True, returnOnError=True)
    if entityType == None:
      usageErrorExit(PHRASE_UNKNOWN_COMMAND_SELECTOR)
    if entityType == CL_ENTITY_USERS:
      CL_command = getChoice(USER_COMMANDS.keys()+USER_COMMANDS_WITH_OBJECTS.keys(), choiceAliases=USER_COMMANDS_ALIASES)
      if (CL_command != u'print') and (GC_Values[GC_AUTO_BATCH_MIN] > 0) and (len(entityList) > GC_Values[GC_AUTO_BATCH_MIN]):
        doAutoBatch(CL_ENTITY_USER, entityList, CL_command)
      elif CL_command in USER_COMMANDS:
        setActionName(USER_COMMANDS[CL_command][CMD_ACTION])
        USER_COMMANDS[CL_command][CMD_FUNCTION](entityList)
      else:
        setActionName(USER_COMMANDS_WITH_OBJECTS[CL_command][CMD_ACTION])
        CL_objectName = getChoice(USER_COMMANDS_WITH_OBJECTS[CL_command][CMD_FUNCTION], choiceAliases=USER_COMMANDS_WITH_OBJECTS[CL_command][CMD_OBJ_ALIASES],
                                  defaultChoice=[CL_OB_USERS, NO_DEFAULT][CL_command != u'print'])
        USER_COMMANDS_WITH_OBJECTS[CL_command][CMD_FUNCTION][CL_objectName](entityList)
    else:
      CL_command = getChoice(CROS_COMMANDS)
      if (CL_command != u'print') and (GC_Values[GC_AUTO_BATCH_MIN] > 0) and (len(entityList) > GC_Values[GC_AUTO_BATCH_MIN]):
        doAutoBatch(CL_ENTITY_CROS, entityList, CL_command)
      else:
        setActionName(CROS_COMMANDS[CL_command][CMD_ACTION])
        CROS_COMMANDS[CL_command][CMD_FUNCTION](entityList)
    sys.exit(GM_Globals[GM_SYSEXITRC])
  except KeyboardInterrupt:
    setSysExitRC(KEYBOARD_INTERRUPT_RC)
  except socket.error as e:
    printErrorMessage(SOCKET_ERROR_RC, u'{0} - {1}'.format(e.errno, e.strerror))
  except MemoryError:
    printErrorMessage(MEMORY_ERROR_RC, MESSAGE_GAM_OUT_OF_MEMORY)
  except SystemExit as e:
    GM_Globals[GM_SYSEXITRC] = e.code
  except Exception:
    from traceback import print_exc
    print_exc(file=sys.stderr)
    setSysExitRC(UNKNOWN_ERROR_RC)
  if sys.stdout != savedStdout:
    sys.stdout.close()
    sys.stdout = savedStdout
  if sys.stderr != savedStderr:
    sys.stderr.close()
    sys.stderr = savedStderr
  return GM_Globals[GM_SYSEXITRC]

# gam loop <FileName>|- [charset <String>] [fields <FieldNameList>] (matchfield <FieldName> <RegularExpression>)* gam <GAM argument list>
def doLoop(processGamCfg=True):
  filename = getString(OB_FILE_NAME)
  if (filename == u'-') and (GC_Values[GC_DEBUG_LEVEL] > 0):
    putArgumentBack()
    usageErrorExit(MESSAGE_BATCH_CSV_LOOP_DASH_DEBUG_INCOMPATIBLE.format(u'loop'))
  f, csvFile = openCSVFileReader(filename)
  matchFields = getMatchFields(csvFile.fieldnames)
  checkArgumentPresent([GAM_CMD,], required=True)
  if CL_argvI == CL_argvLen:
    missingArgumentExit(OB_GAM_ARGUMENT_LIST)
  choice = CL_argv[CL_argvI].strip().lower()
  if choice == LOOP_CMD:
    usageErrorExit(PHRASE_NESTED_LOOP_CMD_NOT_ALLOWED)
  if processGamCfg:
    if choice in GAM_META_COMMANDS:
# gam loop ... gam redirect|select|config ... process gam.cfg on each iteration
      nextProcessGamCfg = True
    else:
# gam loop ... gam !redirect|select|config ... process gam.cfg on first iteration only
      nextProcessGamCfg = False
  else:
    if choice in GAM_META_COMMANDS:
# gam redirect|select|config ... loop ... gam redirect|select|config ... process gam.cfg on each iteration
      nextProcessGamCfg = processGamCfg = True
    else:
# gam redirect|select|config ... loop ... gam !redirect|select|config ... no further processing of gam.cfg
      nextProcessGamCfg = False
  GAM_argv, subFields = getSubFields([CL_argv[0]], csvFile.fieldnames)
  for row in csvFile:
    if (not matchFields) or checkMatchFields(row, matchFields):
      ProcessGAMCommand(processSubFields(GAM_argv, row, subFields), processGamCfg=processGamCfg)
      if (GM_Globals[GM_SYSEXITRC] > 0) and (GM_Globals[GM_SYSEXITRC] <= HARD_ERROR_RC):
        break
      processGamCfg = nextProcessGamCfg
  closeFile(f)

def win32_unicode_argv():
  from ctypes import POINTER, byref, cdll, c_int, windll
  from ctypes.wintypes import LPCWSTR, LPWSTR

  GetCommandLineW = cdll.kernel32.GetCommandLineW
  GetCommandLineW.argtypes = []
  GetCommandLineW.restype = LPCWSTR

  CommandLineToArgvW = windll.shell32.CommandLineToArgvW
  CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]
  CommandLineToArgvW.restype = POINTER(LPWSTR)

  cmd = GetCommandLineW()
  argc = c_int(0)
  argv = CommandLineToArgvW(cmd, byref(argc))
  if argc.value > 0:
    # Remove Python executable and commands if present
    sys.argv = argv[argc.value-len(sys.argv):argc.value]

# Run from command line
if __name__ == "__main__":
  reload(sys)
  if hasattr(sys, u'setdefaultencoding'):
    sys.setdefaultencoding(u'UTF-8')
  if GM_Globals[GM_WINDOWS]:
    win32_unicode_argv() # cleanup sys.argv on Windows
  logging.raiseExceptions = False
  sys.exit(ProcessGAMCommand(sys.argv))
