from __future__ import print_function
import os
import urllib
import logging
import cloudstorage as gcs
import httplib2
import os
import time, calendar
import re
import dateutil.parser

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from entities_def import CredentialsM

from google.appengine.api import urlfetch
from entities_def import User
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
from datetime import  timedelta, tzinfo

from google.appengine.api import users
from oauth2client.contrib.appengine import StorageByKeyName

import jinja2
import webapp2
import json

app = Flask(__name__)


CLIENT_SECRET_FILE = 'client_secret.json'
SCOPES = 'https://www.googleapis.com/auth/calendar'
APPLICATION_NAME = 'Travlendar'
mode_dict = {
    "Car": "driving",
    "Walk": "walking",
    "Bike": "bicycling",
    "Public Transport": "transit",
    "Public": "transit",
    "Fastest": "fastest"
}

def get_estimated_time(origin_in, destination_in, arrival_time, transit_mode="driving"):
    origin = origin_in.replace(" ", "+")
    destination = destination_in.replace(" ", "+")

    url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=%s&destinations=%s&arrival_time=%d&mode=%s&key=AIzaSyA8kKYiHIDlMbXvLmOBA8W2r1W9FVA5Blg" % (origin, destination, arrival_time, transit_mode)
    logging.info("Request url is %s" % url)

    response = json.loads(urlfetch.fetch(url).content, encoding="utf-8")
    for i in response:
        logging.info("%s", i)
    elements = response["rows"][0]["elements"]

    #for i in elements:
    i = elements[0]
    logging.info("single element %s" % i)
    if i["status"].decode('utf-8') == "OK":
        duration = i["duration"]["text"]
        logging.info("From %s to %s takes %s " % (origin, destination, duration))
    return i["duration"]["value"]

def get_credentials(email):
    cred_list = CredentialsM.query(CredentialsM.user_email == email).fetch()

    if len(cred_list) != 0:
        cred = cred_list[0]
        logging.info("use old cred" + str(cred))
        token = cred.access_token
        credentials = AccessTokenCredentials(token, 'user-agent-value')

        return credentials

def find_fastest_method(origin, destination, arrival_time, options):
    time_list = []
    for item in options:
        time_list.append((get_estimated_time(origin, destination, arrival_time, transit_mode=item), item))
    logging.info("time list: %s " % time_list)
    return min(time_list)


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

    user_db = User.query(User.email == email).fetch()[0]
    transit_mode = 'walk'
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


    dt = dateutil.parser.parse(event['end']['dateTime'])
    be = dateutil.parser.parse(event['start']['dateTime']) - timedelta(hours = 24)

    #now = datetime.datetime.utcnow() - timedelta(hours = 24);
    #now = now.isoformat() + 'Z' # 'Z' indicates UTC time
    #logging.info("now:" + now)

    origin_start_time_string = event['start']['dateTime']
    ####Delete
    logging.info("find event!!!!!:" + str(event))
    service.events().delete(calendarId='primary', eventId=event_id).execute()

    event_name = req_evt['eventName']
    address = req_evt['location']
    txt_arrival_time = req_evt['startTime']
    txt_stop_time = req_evt['endTime']

    #event['location'] = req_evt['location']
    #event['start']['dateTime'] = req_evt['startTime']
    #event['end']['dateTime'] = req_evt['endTime']
    #event['summary'] = req_evt['eventName']
#############################

    arrival_time_string = txt_arrival_time.decode('utf-8') + " %s" % time.tzname[0]
    arrival_test_time = time.strptime(arrival_time_string, "%Y/%m/%d %H:%M %Z")

    stop_time_string = txt_stop_time.decode('utf-8') + " %s" % time.tzname[0]
    stop_test_time = time.strptime(stop_time_string, "%Y/%m/%d %H:%M %Z")

    logging.info("%s %s" % (arrival_time_string, stop_time_string))
    arrival_time = calendar.timegm(arrival_test_time)
    stop_time = calendar.timegm(stop_test_time)
    
    arrival_time_string_google = datetime.datetime.fromtimestamp(arrival_time).strftime('%Y-%m-%dT%H:%M:00-06:00')

    logging.info("events:" + event['end']['dateTime'] +"|"+ arrival_time_string_google)
    logging.info('origin event time:' + dt.isoformat() + be.isoformat())
    travel_list_old = service.events().list(
            calendarId='primary', timeMin=now, timeMax=event['end']['dateTime'], singleEvents=True,
            orderBy='startTime').execute()
    events_travel = travel_list_old.get('items', [])
    logging.info("old :" + str(events_travel))

    temp_list = []
    
    for item in events_travel:
        logging.info("%%%%%%%%%%%%%%%item:" + str(item) + origin_start_time_string)
        
        logging.info("item orig:" + origin_start_time_string)
        if item['summary'].startswith('Travel to') and item['end']['dateTime'].startswith(origin_start_time_string):
            logging.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#########delete:" + str(item))
            service.events().delete(calendarId='primary', eventId=item['id']).execute()
        else:
            temp_list.append(item)
    
    eventsResult = service.events().list(
            calendarId='primary', timeMin=now, timeMax=arrival_time_string_google, singleEvents=True,
            orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    logging.info("old :" + str(events))


    #events = temp_list
    now_time = time.time()

    if not events:
        logging.info('No upcoming events found.')
        origin_address = "Austin" # in the future maybe offer an default location
        origin_time_stamp = now_time
        logging.info("No upcoming events found, using address %s and time %d" % (origin_address, origin_time_stamp))
    else:
        for event in reversed(events):
            start = event['start'].get('dateTime', event['start'].get('date'))
            # logging.info("Found event: %s" % event)
            logging.info("Found event: %s %s" % (start, event['summary']))
        previous_event = events[-1]
        origin_address = previous_event['location']
        origin_stop_time = previous_event['end']['dateTime']
        t = re.search("(\d+-\d+-\d+T\d+:\d+:\d+)([+-]\d+):(\d+)", origin_stop_time)
        origin_stop_time = t.group(1) + " %s" % time.tzname[0]
        logging.info("Found stop time %s" % origin_stop_time)

        origin_time_stamp = int(datetime.datetime.strptime(origin_stop_time, "%Y-%m-%dT%H:%M:%S %Z").strftime("%s"))
        logging.info("Found previous event at %s, end at %s aka ts %d" % (origin_address, origin_stop_time, origin_time_stamp))

    trip_mode = 'fastest'
    if trip_mode == "fastest":
        travel_options = user_db.travel_option
        method_list = []
        for i in travel_options:
            logging.info("travel option input got %s" % (i.decode('utf-8')))
            method_list.append(mode_dict.get(i.decode('utf-8')))
        logging.info("Searching for best option in %s " % method_list)
        travel_time, transit_mode = find_fastest_method(origin=origin_address, destination=address,
                                                             arrival_time=arrival_time, options = method_list)
    else:
        travel_time = get_estimated_time(origin_in=origin_address, destination_in=address,
                                              arrival_time=arrival_time, transit_mode=trip_mode)
        transit_mode = trip_mode


    departure_time = arrival_time - travel_time
    if departure_time < origin_time_stamp:
        logging.info("ERROR!!! not enough time to travel to next location")
    else:
        logging.info("Arrival time is %s, departure time needs to be %s" % (arrival_time, departure_time))

        departure_time_string = datetime.datetime.fromtimestamp(departure_time).strftime('%Y-%m-%dT%H:%M:00-06:00')
        arrival_time_string = datetime.datetime.fromtimestamp(arrival_time).strftime('%Y-%m-%dT%H:%M:00-06:00')
        end_time_string = datetime.datetime.fromtimestamp(stop_time).strftime('%Y-%m-%dT%H:%M:00-06:00')
        logging.info("String departure time is %s" % departure_time_string)

        event = {
            'summary': "Travel to %s using %s" % (event_name, transit_mode),
            'location': address,
            'description': "Proposed method %s " % transit_mode,
            'start': {
                'dateTime': departure_time_string,
                'timeZone': 'America/Chicago',
            },
            'end': {
                'dateTime': arrival_time_string,
                'timeZone': 'America/Chicago',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
            'colorId': 5,
        }

        logging.info("Adding event %s " % event)
        event = service.events().insert(calendarId='primary', body=event).execute()
        logging.info('Travel event created: %s' % (event.get('htmlLink')))
        event = {
            'summary': event_name,
            'location': address,
            'description': 'test',
            'start': {
                'dateTime': arrival_time_string,
                'timeZone': 'America/Chicago',
            },
            'end': {
                'dateTime': end_time_string,
                'timeZone': 'America/Chicago',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        logging.info("Adding event %s " % event)

        event = service.events().insert(calendarId='primary', body=event).execute()
        logging.info('Real event created: %s' % (event.get('htmlLink')))

#####################################
    return json.dumps(event)
    

@app.route('/api/delete/<event_id>/<email>', methods = ['DELETE'])
def delete(event_id = None, email=None):
    logging.info("event_id" + event_id)

    credentials = get_credentials(email)
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    return jsonify( { 'result': True } )
