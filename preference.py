import base64
import hashlib
import hmac
import json
import os
import urllib
import logging
import cloudstorage as gcs
import sys

from entities_def import User
from entities_def import CredentialsM

import jinja2
import webapp2
from google.appengine.api import users

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Preference(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'error_type': 'modal'
            # 'url': decorator.authorize_url(),
            # 'has_credentials': decorator.has_credentials()
        }
        template = JINJA_ENVIRONMENT.get_template('UserPreferences.html')
        self.response.write(template.render(template_values))


    def post(self):
        user = users.get_current_user()
        target_user = User.query(User.email == user.email()).fetch()

        preferences = self.request.get_all('travelPref')
        view_calendar = self.request.get('display')

        pref_list = []

        logging.info("view calendar" + str(view_calendar))
        logging.info("preference" + str(preferences))

        for i in preferences:
            pre = i.split('/')
            logging.info("preference %s", pre)
            logging.info("preference %s", i)
            # pref_list.append(str(pre))
            pref_list.append(i)

        if len(target_user) != 0:
            user_obj = target_user[0]

        
            user_obj.display = view_calendar
            user_obj.travel_option = pref_list
            user_obj.put()

        template_values = {
            'user': user,
            'error_type': 'modal'
        }

        template = JINJA_ENVIRONMENT.get_template('UserPreferences.html')
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/preference', Preference),
], debug=True)
