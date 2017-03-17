# -*- coding: utf-8 -*-

# Copyright (C) 2016 Ross Scroggs All Rights Reserved.
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Google API resources

"""
# APIs
ADMIN = u'admin'
ADMIN_SETTINGS = u'admin-settings'
APPSACTIVITY = u'appsactivity'
CALENDAR = u'calendar'
CLASSROOM = u'classroom'
CLOUDPRINT = u'cloudprint'
CONTACTS = u'contacts'
DATATRANSFER = u'datatransfer'
DIRECTORY = u'directory'
DRIVE = u'drive'
DRIVE3 = 'drive3'
EMAIL_AUDIT = u'email-audit'
EMAIL_SETTINGS = u'email-settings'
GMAIL = u'gmail'
GPLUS = u'plus'
GROUPSMIGRATION = u'groupsmigration'
GROUPSSETTINGS = u'groupssettings'
LICENSING = u'licensing'
REPORTS = u'reports'
RESELLER = u'reseller'
SITES = u'sites'
SITEVERIFICATION = u'siteVerification'
#
FAM1_SCOPES = u'fam1'
FAM2_SCOPES = u'fam2'
FAM_LIST = [FAM1_SCOPES, FAM2_SCOPES]
PREV_FAM_LIST = [u'gapi', u'gdata']
#
OAUTH2_TOKEN_ERRORS = [
  u'access_denied', u'invalid_grant', u'unauthorized_client: Unauthorized client or scope in request.', u'access_denied: Requested client not authorized.',
  u'invalid_grant: Not a valid email.', u'invalid_grant: Invalid email or User ID', u'invalid_grant: Bad Request',
  u'invalid_request: Invalid impersonation prn email address.', u'internal_failure: Backend Error',
  ]

_INFO = {
  ADMIN_SETTINGS: {u'version': u'v2', u'credfam': FAM2_SCOPES, u'localjson': True},
  APPSACTIVITY: {u'version': u'v1', u'credfam': FAM1_SCOPES, u'svcacctscopes': [u'https://www.googleapis.com/auth/activity', u'https://www.googleapis.com/auth/drive']},
  CALENDAR: {u'version': u'v3', u'credfam': FAM1_SCOPES, u'svcacctscopes': [u'https://www.googleapis.com/auth/calendar',]},
  CLASSROOM: {u'version': u'v1', u'credfam': FAM2_SCOPES},
  CLOUDPRINT: {u'version': u'v2', u'credfam': FAM2_SCOPES, u'localjson': True},
  CONTACTS: {u'version': u'v3', u'credfam': FAM2_SCOPES, u'svcacctscopes': [u'https://www.google.com/m8/feeds',], u'localjson': True},
  DATATRANSFER: {u'version': u'datatransfer_v1', u'credfam': FAM1_SCOPES},
  DIRECTORY: {u'version': u'directory_v1', u'credfam': FAM1_SCOPES},
  DRIVE: {u'version': 'v2', u'credfam': FAM1_SCOPES, u'svcacctscopes': [u'https://www.googleapis.com/auth/drive',]},
  DRIVE3: {u'version': 'v3', u'credfam': FAM1_SCOPES, u'svcacctscopes': [u'https://www.googleapis.com/auth/drive',]},
  EMAIL_AUDIT: {u'version': u'v1', u'credfam': FAM2_SCOPES, u'localjson': True},
  EMAIL_SETTINGS: {u'version': u'v2', u'credfam': FAM1_SCOPES, u'localjson': True},
  GMAIL: {u'version': u'v1', u'credfam': FAM1_SCOPES, u'svcacctscopes': [u'https://mail.google.com/', u'https://www.googleapis.com/auth/gmail.settings.basic',
                                                                         u'https://www.googleapis.com/auth/gmail.settings.sharing',]},
  GPLUS: {u'version': u'v1', u'credfam': FAM1_SCOPES, u'svcacctscopes': [u'https://www.googleapis.com/auth/plus.me', u'https://www.googleapis.com/auth/plus.login',
                                                                         u'https://www.googleapis.com/auth/userinfo.email', u'https://www.googleapis.com/auth/userinfo.profile']},
  GROUPSMIGRATION: {u'version': u'v1', u'credfam': FAM2_SCOPES},
  GROUPSSETTINGS: {u'version': u'v1', u'credfam': FAM2_SCOPES},
  LICENSING: {u'version': u'v1', u'credfam': FAM1_SCOPES},
  REPORTS: {u'version': u'reports_v1', u'credfam': FAM2_SCOPES},
  RESELLER: {u'version': u'v1', u'credfam': FAM2_SCOPES},
  SITES: {u'version': u'v1', u'credfam': FAM2_SCOPES, u'svcacctscopes': [u'https://sites.google.com/feeds',], u'localjson': True},
  SITEVERIFICATION: {u'version': u'v1', u'credfam': FAM2_SCOPES},
  }
#
DRIVE_FILE_CREATED_DATE_TIME = u'createdDate'
DRIVE_FILE_MARKED_VIEWED_BY_ME_DATE_TIME = u'markedViewedByMeDate'
DRIVE_FILE_LAST_VIEWED_BY_ME_DATE_TIME = u'lastViewedByMeDate'
DRIVE_FILE_MODIFIED_BY_ME_DATE_TIME = u'modifiedByMeDate'
DRIVE_FILE_MODIFIED_DATE_TIME = u'modifiedDate'
DRIVE_FILE_NAME = u'title'
DRIVE_FILE_SHARED_WITH_ME_DATE_TIME = u'sharedWithMeDate'
DRIVE_FILE_SIZE = u'fileSize'
DRIVE_FILE_VIEW_LINK = u'alternateLink'
DRIVE_FILE_LABEL_RESTRICTED = u'restricted'
DRIVE_FILE_LABEL_VIEWED = u'viewed'
#
DRIVE_FILES_LIST = u'items'
DRIVE_CREATE_FILE = u'insert'
DRIVE_PATCH_FILE = u'patch'
DRIVE_UPDATE_FILE = u'update'
#
DRIVE_PERMISSIONS_DOMAIN_TYPE_VALUE = u'value'
DRIVE_PERMISSIONS_EXPIRATION_DATE_TIME = u'expirationDate'
DRIVE_PERMISSIONS_GROUP_USER_TYPE_VALUE = u'value'
DRIVE_PERMISSIONS_LIST = u'items'
DRIVE_PERMISSIONS_NAME = u'name'
#
DRIVE_CREATE_PERMISSIONS = u'insert'
DRIVE_PATCH_PERMISSIONS = u'patch'
#
DRIVE_REVISIONS_LIST = u'items'
#
DRIVE_CREATE_TEAMDRIVE = u'insert'
DRIVE_TEAMDRIVES_LIST = u'items'
#
DRIVE_PARENTS_ID = u'parents(id)'

def getVersion(api):
  version = _INFO[api][u'version']
  cred_family = _INFO[api][u'credfam']
  if api in [DIRECTORY, REPORTS, DATATRANSFER]:
    api = ADMIN
  elif api == DRIVE3:
    api = DRIVE
  return (api, version, u'{0}-{1}'.format(api, version), cred_family)

def getSortedSvcAcctScopesList():
  all_scopes = []
  for api in _INFO:
    for scope in _INFO[api].get(u'svcacctscopes', []):
      if scope not in all_scopes:
        all_scopes.append(scope)
  all_scopes.sort()
  return (all_scopes, len(all_scopes))

def getSvcAcctScopes(api):
  return _INFO[api][u'svcacctscopes']

def hasLocalJSON(api):
  return _INFO[api].get(u'localjson', False)
