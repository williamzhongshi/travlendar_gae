from __future__ import print_function
import os
import urllib
import logging
import cloudstorage as gcs
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from entities_def import CredentialsM

from google.appengine.api import app_identity, mail, users, search
from google.appengine.ext import ndb
from flask import Flask, jsonify, abort, request, make_response, url_for
from oauth2client.client import AccessTokenCredentials
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

import jinja2
import webapp2
import json

app = Flask(__name__)


CLIENT_SECRET_FILE = 'client_secret.json'
SCOPES = 'https://www.googleapis.com/auth/calendar'
APPLICATION_NAME = 'Travlendar'

def get_credentials(email):
    cred_list = CredentialsM.query(CredentialsM.user_email == email).fetch()

    if len(cred_list) != 0:
        cred = cred_list[0]
        logging.info("use old cred" + str(cred))
        token = cred.access_token
        credentials = AccessTokenCredentials(token, 'user-agent-value')

        return credentials

@app.route('/api/getdetails/<event_id>/<email>', methods = ['GET'])
def get(event_id = None, email=None):
    logging.info("event_id" + event_id)
    credentials = get_credentials(email)
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    # 3rmeaak08fjhli6ov0g83dfvhe
    logging.info(str(event))

    return json.dumps(event)

@app.route('/api/patch/<event_id>/<email>', methods = ['PATCH'])
def patch(event_id = None, email=None):
    logging.info("event_id" + event_id)
    content = request.get_json()

    logging.info("json" + str(request.get_json()))
    credentials = get_credentials(email)
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    req_evt = request.get_json()['event']
    logging.info("req_evt:" + str(req_evt))

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    event['eventName'] = req_evt['eventName']
    event['location'] = req_evt['location']
    event['startTime'] = req_evt['startTime']
    event['endTime'] = req_evt['endTime']

    updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    return json.dumps(event)
    

@app.route('/api/delete/<event_id>/<email>', methods = ['DELETE'])
def delete(event_id = None, email=None):
    logging.info("event_id" + event_id)

    credentials = get_credentials(email)
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    return jsonify( { 'result': True } )
