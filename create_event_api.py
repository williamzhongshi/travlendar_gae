import calendar
import os
import re
import urllib
import logging

import time

import datetime

import cloudstorage as gcs

from google.appengine.api import app_identity, mail, users, search
from google.appengine.ext import ndb
from flask import Flask, jsonify, abort, request, make_response, url_for
from entities_def import User, CredentialsM
from create_event import mode_dict, find_fastest_method
from trip_tools import *


import jinja2
import webapp2
import json


from oauth2client.client import AccessTokenCredentials
from apiclient import discovery

import httplib2

app = Flask(__name__)

def serializeResult(result):
   #l = []
   #for s in result:
   re = {}
   re['body'] = result

@app.route('/api/create_event/<name>', methods=['GET'])
def get(name=None):
    logging.info("got name %s" % name)
    #req_evt = request.get_json()['event']


@app.route('/api/create_event/<name>', methods=['POST'])
def post(name=None):
    logging.info("got name %s" % name)
    #logging.info("got request %s " % request.values)
    logging.info("got request %s " % request.get_data())
    whole_json = request.get_json()
    logging.info("got json %s " % whole_json)
    req_evt = request.get_json()['name']
    logging.info("got event name %s " % req_evt)
    #re = serializeResult("OK")
    #return json.dumps(re)

   # user_obj = User.query(User.email == users.get_current_user().email()).fetch()[0]
    #user = users.get_current_user()
   # user_db = User.query(User.email == user.email()).fetch()[0]
   # user_db = User.query(User.email == "williamzhongshi@gmail.com").fetch()[0]

    tmp_email = "williamzhongshi@gmail.com"
    user_db = User.query(User.email == tmp_email).fetch()[0]

    event_name = request.get_json()['name']
    address = request.get_json()['address']
    txt_arrival_time = request.get_json()['eventStart']
    txt_stop_time = request.get_json()['eventEnd']
    transit_mode = request.get_json()['travel']
    trip_mode = mode_dict.get(transit_mode).lower()

    logging.info(
        "Event name: %s, address: %s, start; %s, stop: %s, transit_mode: %s " % (event_name, address, txt_arrival_time, txt_stop_time, transit_mode))
    arrival_time_string = txt_arrival_time.strip() + " UTC" # "" %s" % time.tzname[0]
    arrival_test_time = time.strptime(arrival_time_string, "%m-%d-%Y %H:%M %Z")

    stop_time_string = txt_stop_time.strip() + " UTC" #  " %s" % time.tzname[0]
    stop_test_time = time.strptime(stop_time_string, "%m-%d-%Y %H:%M %Z")

    logging.info("%s %s" % (arrival_time_string, stop_time_string))
    arrival_time = calendar.timegm(arrival_test_time) + 3600*6
    stop_time = calendar.timegm(stop_test_time) + 3600*6
    logging.info("arrival stop timestamp %d %d" % (arrival_time, stop_time))

    cred_list = CredentialsM.query(CredentialsM.user_email == tmp_email).fetch()
    logging.info("cred list len %d " % len(cred_list))
    if len(cred_list) != 0:
        cred = cred_list[0]
        logging.info("use old cred" + str(cred))
        token = cred.access_token
        credentials = AccessTokenCredentials(token, 'user-agent-value')
        http = credentials.authorize(httplib2.Http())
        # credentials.refresh(http)
        service = discovery.build('calendar', 'v3', http=http)
        #
        # # original address hardcoded for now
        arrival_time_string_google = datetime.datetime.fromtimestamp(arrival_time).strftime('%Y-%m-%dT%H:%M:00-06:00')
        # if depart_from_previous_dest:
        logging.info('Getting the upcoming 10 events')
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        now_time = time.time()

        logging.info("arrival_time_string_google: %s " % arrival_time_string_google)

        # look for all events from now to before new event, find the last event before new event,
        # get address and stop time
        eventsResult = service.events().list(
            calendarId='primary', timeMin=now, timeMax=arrival_time_string_google, singleEvents=True,
            orderBy='startTime').execute()
        events = eventsResult.get('items', [])
        if not events:
            logging.info('No upcoming events found.')
            origin_address = "Austin"  # in the future maybe offer an default location
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
            origin_stop_time = t.group(1) + " UTC" # " %s" % time.tzname[0]
            logging.info("Found stop time %s" % origin_stop_time)

            origin_time_stamp = int(datetime.datetime.strptime(origin_stop_time, "%Y-%m-%dT%H:%M:%S %Z").strftime("%s")) + 3600*6
            logging.info("Found previous event at %s, end at %s aka ts %d" % (
            origin_address, origin_stop_time, origin_time_stamp))
        #    else:
        #        origin_address = default_address
        # else:
        #    origin_address = default_address

        # calculate time needed from previous event to new event
        if trip_mode == "fastest":
            travel_options = user_db.travel_option
            method_list = []
            if len(travel_options) == 0:
                logging.info("No user preference found, use all")
                method_list = ["driving", "bicycling", "walking", "transit"]
            else:
                for i in travel_options:
                    logging.info("travel option input got %s" % (i.decode('utf-8')))
                    method_list.append(mode_dict.get(i.decode('utf-8')))
            logging.info("Searching for best option in %s " % method_list)
            travel_time, transit_mode = find_fastest_method(origin=origin_address, destination=address,
                                                            arrival_time=arrival_time, options=method_list)
        else:
            travel_time = get_estimated_time(origin_in=origin_address, destination_in=address,
                                             arrival_time=arrival_time, transit_mode=trip_mode)
            transit_mode = trip_mode
        # travel_time = self.get_estimated_time(origin_in=origin_address, destination_in=address,
        #                                       arrival_time=arrival_time, transit_mode=transit_mode)

        # calculate when have to start

        departure_time = arrival_time - travel_time

        logging.info("arrival_time %d, travel_time %d, departure_time %d, origin_time_stamp %d" % (arrival_time, travel_time, departure_time, origin_time_stamp))

        if departure_time < origin_time_stamp:
            logging.info("ERROR!!! not enough time to travel to next location")

        else:
            logging.info("Arrival time is %s, departure time needs to be %s" % (arrival_time, departure_time))

            departure_time_string = datetime.datetime.fromtimestamp(departure_time - 3600*6).strftime('%Y-%m-%dT%H:%M:00-06:00')
            arrival_time_string = datetime.datetime.fromtimestamp(arrival_time - 3600*6).strftime('%Y-%m-%dT%H:%M:00-06:00')
            end_time_string = datetime.datetime.fromtimestamp(stop_time - 3600*6).strftime('%Y-%m-%dT%H:%M:00-06:00')
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

    else:
        logging.info("credential not found")
    return "OK"