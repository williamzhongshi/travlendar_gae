import hmac
import json
import os
import time, calendar
import urllib
import logging

import re
import urllib2
import dateutil.parser

import cloudstorage as gcs
from entities_def import CredentialsM


# from oauth2client import client
# from oauth2client.contrib import appengine
# from googleapiclient import discovery

from entities_def import User

from google.appengine.api import memcache
from google.appengine.api import app_identity, mail, users
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from datetime import  timedelta, tzinfo
import google.oauth2.credentials
import google_auth_oauthlib.flow
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.client import AccessTokenCredentials

from trip_tools import *

from apiclient.discovery import build
from apiclient import discovery

import httplib2
import os
import datetime

import jinja2
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

MAPS_KEY = 'AIzaSyA8kKYiHIDlMbXvLmOBA8W2r1W9FVA5Blg'

default_address = "UT Austin"

mode_dict = {
    "Car": "driving",
    "Walk": "walking",
    "Bike": "bicycling",
    "Public Transport": "transit",
    "Public": "transit",
    "Fastest": "fastest"
}
def get_credentials(email):
    cred_list = CredentialsM.query(CredentialsM.user_email == email).fetch()

    if len(cred_list) != 0:
        cred = cred_list[0]
        logging.info("use old cred" + str(cred))
        token = cred.access_token
        credentials = AccessTokenCredentials(token, 'user-agent-value')

        return credentials

def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    return next_month - datetime.timedelta(days=next_month.day)

def change_time(t):
    t = time.mktime(t.timetuple()) 
    return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%dT%H:%M:00-06:00')

def get_list_time(display):
    now = datetime.datetime.now() - datetime.timedelta(hours=6)
    if display == 'Month':
        todayDate = now
        return (change_time(todayDate.replace(day=1, hour=0, minute=0, second=0)), change_time(last_day_of_month(now.replace(hour=23,minute=59,second=59))))
    elif display == 'Week':
        dt = now
        start = dt - datetime.timedelta(days=dt.weekday())
        end = start + datetime.timedelta(days=6)
        return (change_time(start.replace(hour=0,minute=0,second=0)), change_time(end.replace(hour=23,minute=59,second=59)))
    elif display == 'Day':
        return (change_time(now.replace(hour=0,minute=0,second=0)), change_time(now.replace(hour=23,minute=59,second=59)))
    elif display is None:
        return (change_time(now.replace(hour=0,minute=0,second=0)), change_time(now.replace(hour=23,minute=59,second=59)))
    

class ManageEvent(webapp2.RequestHandler):

    def get(self):
        email = users.get_current_user().email()
        user_obj = User.query(User.email == email).fetch()[0]

        display = user_obj.display
        credentials = get_credentials(email)

        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        (start_time, end_time) = get_list_time(display)
        logging.info("start " + start_time)
        logging.info("end " + end_time)
        logging.info("display " + display)
        logging.info("now " + str(datetime.datetime.today()))
        logging.info("now " + str(datetime.datetime.now()))

        event_list = service.events().list(
                calendarId='primary', timeMin=start_time, timeMax=end_time, singleEvents=True,
                orderBy='startTime').execute()
        logging.info("event_list" + str(event_list))


        for e in event_list['items']:
            logging.info("event:" + e['summary'])

        template_values = {
                'events': event_list['items'],
                'email':email,
        }
        template = JINJA_ENVIRONMENT.get_template('ManageEvent.html')
        self.response.write(template.render(template_values))

class DeleteEvent(webapp2.RequestHandler):
    def get(self):
        event_id = self.request.get('event_id')
        email = users.get_current_user().email()
        credentials = get_credentials(email)

        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        event = service.events().get(calendarId='primary', eventId=event_id).execute()


        dt = dateutil.parser.parse(event['end']['dateTime'])
        be = dateutil.parser.parse(event['start']['dateTime']) - timedelta(hours = 24)

        origin_start_time_string = event['start']['dateTime']
        logging.info("find event!!!!!:" + str(event))
        service.events().delete(calendarId='primary', eventId=event_id).execute()

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

        email = users.get_current_user().email()
        user_obj = User.query(User.email == email).fetch()[0]

        display = user_obj.display
        credentials = get_credentials(email)

        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        (start_time, end_time) = get_list_time(display)
        logging.info("start " + start_time)
        logging.info("end " + end_time)
        logging.info("display " + display)
        logging.info("now " + str(datetime.datetime.today()))
        logging.info("now " + str(datetime.datetime.now()))

        event_list = service.events().list(
                calendarId='primary', timeMin=start_time, timeMax=end_time, singleEvents=True,
                orderBy='startTime').execute()
        logging.info("event_list" + str(event_list))


        for e in event_list['items']:
            logging.info("event:" + e['summary'])

        template_values = {
                'events': event_list['items'],
                'email':email,
        }
        template = JINJA_ENVIRONMENT.get_template('ManageEvent.html')
        self.response.write(template.render(template_values))

class PatchEvent(webapp2.RequestHandler):
    def post(self):
        email = users.get_current_user().email()
        user_db = User.query(User.email == email).fetch()[0]
        transit_mode = 'walk'

        credentials = get_credentials(email)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        event_id = self.request.get('eventID')

        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        event = service.events().get(calendarId='primary', eventId=event_id).execute()


        dt = dateutil.parser.parse(event['end']['dateTime'])
        be = dateutil.parser.parse(event['start']['dateTime']) - timedelta(hours = 24)

        origin_start_time_string = event['start']['dateTime']
        logging.info("find event!!!!!:" + str(event))
        service.events().delete(calendarId='primary', eventId=event_id).execute()

        #event_name = req_evt['eventName']
        event_name = self.request.get('eventName')
        address = self.request.get('location') #req_evt['location']
        txt_arrival_time = self.request.get('startTime') #req_evt['startTime']
        txt_stop_time = self.request.get('endTime') #req_evt['endTime']

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
        email = users.get_current_user().email()
        user_obj = User.query(User.email == email).fetch()[0]

        display = user_obj.display
        credentials = get_credentials(email)

        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        (start_time, end_time) = get_list_time(display)
        logging.info("start " + start_time)
        logging.info("end " + end_time)
        logging.info("display " + display)
        logging.info("now " + str(datetime.datetime.today()))
        logging.info("now " + str(datetime.datetime.now()))

        event_list = service.events().list(
                calendarId='primary', timeMin=start_time, timeMax=end_time, singleEvents=True,
                orderBy='startTime').execute()
        logging.info("event_list" + str(event_list))


        for e in event_list['items']:
            logging.info("event:" + e['summary'])

        template_values = {
                'events': event_list['items'],
                'email':email,
        }
        template = JINJA_ENVIRONMENT.get_template('ManageEvent.html')
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/manage_event', ManageEvent),
    ('/manage_event_delete', DeleteEvent),
    ('/manage_event_modify', PatchEvent)
], debug=True)
