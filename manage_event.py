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

app = webapp2.WSGIApplication([
    ('/manage_event', ManageEvent),
    ('/manage_event_delete', DeleteEvent)
], debug=True)
