import hmac
import json
import os
import time, calendar
import urllib
import logging

import re

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
import google.oauth2.credentials
import google_auth_oauthlib.flow
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.client import AccessTokenCredentials

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

class CreateEvent(webapp2.RequestHandler):

    def get_estimated_time(self, origin_in, destination_in, arrival_time, transit_mode="driving"):
        origin = origin_in.replace(" ", "+")
        destination = destination_in.replace(" ", "+")

        url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=%s&destinations=%s&arrival_time=%d&transit_mode=%s&key=AIzaSyA8kKYiHIDlMbXvLmOBA8W2r1W9FVA5Blg" % (origin, destination, arrival_time, transit_mode)
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

    def get(self):

        template_values = {
        }
        template = JINJA_ENVIRONMENT.get_template('CreateEvent.html')
        self.response.write(template.render(template_values))


    def post(self):
        # user_obj = User.query(User.email == users.get_current_user().email()).fetch()[0]
        user = users.get_current_user()
        event_name = self.request.get('txtEventName')
        address = self.request.get('txtAddress')
        txt_arrival_time = self.request.get('eventstart')
        txt_stop_time = self.request.get('eventend')
        transit_mode = "driving"

        depart_from_previous_dest = True

        logging.info("Event name: %s, address: %s, start; %s, stop: %s " % (event_name, address, txt_arrival_time, txt_stop_time))


        # time hardcoded for now
        arrival_time_string = txt_arrival_time.decode('utf-8') + " %s" % time.tzname[0]
        arrival_test_time = time.strptime(arrival_time_string, "%Y/%m/%d %H:%M %Z")

        stop_time_string = txt_stop_time.decode('utf-8') + " %s" % time.tzname[0]
        stop_test_time = time.strptime(stop_time_string, "%Y/%m/%d %H:%M %Z")

        logging.info("%s %s" % (arrival_time_string, stop_time_string))
        arrival_time = calendar.timegm(arrival_test_time)
        stop_time = calendar.timegm(stop_test_time)

        cred_list = CredentialsM.query(CredentialsM.user_email == user.email()).fetch()

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
            #if depart_from_previous_dest:
            logging.info('Getting the upcoming 10 events')
            now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
            logging.info("arrival_time_string_google: %s " % arrival_time_string_google)
            eventsResult = service.events().list(
                calendarId='primary', timeMin=now, timeMax=arrival_time_string_google, singleEvents=True,
                orderBy='startTime').execute()
            events = eventsResult.get('items', [])
            if not events:
                logging.info('No upcoming events found.')
            for event in reversed(events):
                start = event['start'].get('dateTime', event['start'].get('date'))
                # logging.info("Found event: %s" % event)
                logging.info("Found event: %s %s" % (start, event['summary']))
            previous_event = events[-1]

            #    if previous_event.get('location') is not None:
            # logging.info("Previous location: %s" % (previous_event['location']))
            origin_address = previous_event['location']
            # logging.info("Previous event %s " % previous_event)
            origin_stop_time = previous_event['end']['dateTime']
            t = re.search("(\d+-\d+-\d+T\d+:\d+:\d+)([+-]\d+):(\d+)", origin_stop_time)
            origin_stop_time = t.group(1) + " %s" % time.tzname[0]
            logging.info("Found stop time %s" % origin_stop_time)

            origin_time_stamp = int(datetime.datetime.strptime(origin_stop_time, "%Y-%m-%dT%H:%M:%S %Z").strftime("%s"))
            logging.info("Found previous event at %s, end at %s aka ts %d" % (origin_address, origin_stop_time, origin_time_stamp))
            #    else:
            #        origin_address = default_address
            #else:
            #    origin_address = default_address

            travel_time = self.get_estimated_time(origin_in=origin_address, destination_in=address,
                                                  arrival_time=arrival_time, transit_mode=transit_mode)

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
                    'summary': "Travel to %s" + event_name,
                    'location': address,
                    'description': 'test',
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


# [START app]
app = webapp2.WSGIApplication([
    ('/create_event', CreateEvent),

], debug=True)
# [END app]
