#!/usr/bin/env python

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START imports]
import base64
import hashlib
import hmac
import json
import os
import urllib
import logging
import cloudstorage as gcs
import sys

# from oauth2client import client
# from oauth2client.contrib import appengine
# from googleapiclient import discovery

from entities_def import User
from entities_def import CredentialsM

from google.appengine.api import memcache
from google.appengine.api import app_identity, mail, users
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from oauth2client.client import AccessTokenCredentials

import jinja2
import webapp2

from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build

from apiclient import discovery
import google.oauth2.credentials
import google_auth_oauthlib.flow
import httplib2
import os
import datetime

from google.appengine.api import users
from oauth2client.contrib.appengine import StorageByKeyName

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

MAPS_KEY = 'AIzaSyA8kKYiHIDlMbXvLmOBA8W2r1W9FVA5Blg'


CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

flow = flow_from_clientsecrets('./client_secret.json', scope='https://www.googleapis.com/auth/calendar', redirect_uri='http://localhost:8080/auth')
# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file('./client_secret.json' , scopes=['https://www.googleapis.com/auth/calendar'])
        flow.redirect_uri='http://localhost:8080/auth'
        #auth_uri = flow.step1_get_authorize_url()
        auth_uri, state = flow.authorization_url(access_type='offline',include_granted_scopes='true')
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            target_user = User.query(User.email == user.email()).fetch()

            if len(target_user) == 0:
                logging.info("User not found, creating User entity %s" % users.get_current_user().email())
                logging.info("%s", dir(user))
                user_obj = User()
                user_obj.username = user.email()  # not sure what this is for
                user_obj.email = user.email()
                user_obj.put()



            #cred_list = CredentialsM.query(CredentialsM.user_email == user.email()).fetch()

#            if len(cred_list) != 0:
#                cred = cred_list[0]
#                logging.info("use old cred" + str(cred))
#                token = cred.access_token
#                credentials = AccessTokenCredentials(token, 'user-agent-value')
#
#                http = credentials.authorize(httplib2.Http())
#                #credentials.refresh(http)
#                service = discovery.build('calendar', 'v3', http=http)
#
#                now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
#                print('Getting the upcoming 10 events')
#                eventsResult = service.events().list(
#                        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
#                        orderBy='startTime').execute()
#                events = eventsResult.get('items', [])
#
#                if not events:
#                    logging.info('No upcoming events found.')
#                for event in events:
#                    start = event['start'].get('dateTime', event['start'].get('date'))
#                    logging.info("Found event: %s %s" % (start, event['summary']))
#
                # Refer to the Python quickstart on how to setup the environment:
                # https://developers.google.com/google-apps/calendar/quickstart/python
                # Change the scope to 'https://www.googleapis.com/auth/calendar' and delete any
                # stored credentials.


        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login Using Google'




        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'auth_url' : auth_uri
        }

        template = JINJA_ENVIRONMENT.get_template('Login.html')
        self.response.write(template.render(template_values))

class AuthPage(webapp2.RequestHandler):
    def get(self):
        code = self.request.get('code')
        logging.info('code:' + str(code))

        user = users.get_current_user()
        

        cred_list = CredentialsM.query(CredentialsM.user_email == user.email()).fetch()
        #if len(cred_list) == 0:
        logging.info("no cred in ndb")
        cred = CredentialsM()
        credentials = flow.step2_exchange(code)
        logging.info("dumping:" + credentials.access_token)
        cred.user_email = user.email()
        cred.access_token = credentials.access_token
        cred.put()
        logging.info("cred:" + str(credentials))
       # else:
       #     cred = cred_list[0]
       #     logging.info("use old cred" + str(cred))
       #     credentials = AccessTokenCredentials(cred.access_token, 'user-agent-value')

        logging.info("cred after:" + str(credentials))

        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        eventsResult = service.events().list(
                calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
                orderBy='startTime').execute()
        events = eventsResult.get('items', [])

        if not events:
            logging.info('No upcoming events found.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            logging.info("Found event: %s %s" % (start, event['summary']))
            logging.info("event %s" % (event['id']))

        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            target_user = User.query(User.email == user.email()).fetch()

            if len(target_user) == 0:
                logging.info("User not found, creating User entity %s" % users.get_current_user().email())
                user_obj = User()
                user_obj.username = user.email()  # not sure what this is for
                user_obj.email = user.email()
                user_obj.put()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login Using Google'

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('DisplayCalendar.html')
        self.response.write(template.render(template_values))


# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/auth', AuthPage)
], debug=True)
# [END app]
