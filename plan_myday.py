import logging

from entities_def import User
from entities_def import CredentialsM
import jinja2
import webapp2
from oauth2client.client import flow_from_clientsecrets
from apiclient import discovery
import google_auth_oauthlib.flow
import httplib2
import os
import datetime

from google.appengine.api import users

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]


class PlanMyDay(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            template_values = {
                'user_email': user.email()
            }

            template = JINJA_ENVIRONMENT.get_template('PlanMyDay.html')
            self.response.write(template.render(template_values))
        else:
            logging.info("No user found, maybe not logged in")


# [START app]
app = webapp2.WSGIApplication([
    ('/plan_myday', PlanMyDay),

], debug=True)
# [END app]