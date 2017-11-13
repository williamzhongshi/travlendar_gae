import hmac
import json
import os
import time, calendar
import urllib
import logging
import cloudstorage as gcs

# from oauth2client import client
# from oauth2client.contrib import appengine
# from googleapiclient import discovery

from entities_def import User

from google.appengine.api import memcache
from google.appengine.api import app_identity, mail, users
from google.appengine.ext import ndb
from google.appengine.api import urlfetch

import jinja2
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

MAPS_KEY = 'AIzaSyA8kKYiHIDlMbXvLmOBA8W2r1W9FVA5Blg'

class CreateEvent(webapp2.RequestHandler):

    def get_estimated_time(self, origin_in, destination_in, arrival_time, transit_mode="car"):
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




    def get(self):

        template_values = {
        }
        template = JINJA_ENVIRONMENT.get_template('CreateEvent.html')
        self.response.write(template.render(template_values))


    def post(self):
        user_obj = User.query(User.email == users.get_current_user().email()).fetch()[0]

        event_name = self.request.get('txtEventName')
        address = self.request.get('txtAddress')
        txt_arrival_time = self.request.get('eventstart')
        stop_time = self.request.get('eventend')
        transit_mode = "driving"

        logging.info("Event name: %s, address: %s, start; %s, stop: %s " % (event_name, address, txt_arrival_time, stop_time))

        # original address hardcoded for now
        origin_address = "UT Austin"
        # time hardcoded for now
        time_string = "11 13 2017 10 10 %s" % time.tzname[0]
        test_time = time.strptime(time_string, "%m %d %Y %H %M %Z")
        arrival_time = calendar.timegm(test_time)
        logging.info("Arrival time is %s %s" % (arrival_time, test_time))

        self.get_estimated_time(origin_in=origin_address, destination_in=address, arrival_time=arrival_time, transit_mode=transit_mode)






# [START app]
app = webapp2.WSGIApplication([
    ('/create_event', CreateEvent),

], debug=True)
# [END app]
