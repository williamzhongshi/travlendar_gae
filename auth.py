from __future__ import print_function
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build

import google.oauth2.credentials
import google_auth_oauthlib.flow
import httplib2
import os

import datetime



flow = flow_from_clientsecrets('./client_secret.json', scope='https://www.googleapis.com/auth/calendar', redirect_uri='http://localhost:8080')

auth_uri = flow.step1_get_authorize_url()

print(auth_uri)

code='4/o7rDJfy1T4blR6FeqJi2QEufwarspx0-MKawVYzOcCc'
credentials = flow.step2_exchange(code)


http = credentials.authorize(httplib2.Http())
service = discovery.build('calendar', 'v3', http=http)

now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
print('Getting the upcoming 10 events')
eventsResult = service.events().list(
    calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
    orderBy='startTime').execute()
events = eventsResult.get('items', [])

if not events:
    print('No upcoming events found.')
for event in events:
    start = event['start'].get('dateTime', event['start'].get('date'))
    print(start, event['summary'])

