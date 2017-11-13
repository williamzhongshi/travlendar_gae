#!/usr/bin/env python

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START imports]
import os
import urllib
import logging
import cloudstorage as gcs

from google.appengine.api import app_identity, mail, users
from google.appengine.ext import ndb
from entities_def import User, Photo, Stream
import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]
def user_key(name):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('user', name)



class show_photos_in_stream(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        template_values = {
            'user': user,
        }

        # create user
        user_obj = User()
        user_obj.username =users.get_current_user()
        user_obj.email = users.get_current_user().email()
        user_obj.put()

        template = JINJA_ENVIRONMENT.get_template('show_photo_in_stream.html')
        self.response.write(template.render(template_values))

    def __get_tag(tags):
        return __sanitize_str(tags).split(',')

    def __get_subs(subs):
        return __sanitize_str(subs).split(',')

    def __sanitize_str(s):
        return s.strip()

    def post(self):
        user = users.get_current_user()

        stream_name = self.request.get('name')
        subscriber_list = self.request.get('subs')
        pic_url = self.request.get('pic_url')
        tags = self.request.get('tags')

        user_obj = User()
        user_obj.username =users.get_current_user()
        user_obj.email = users.get_current_user().email()

        stream = Stream(parent=user_key(obj.username)
        stream.name = stream_name
        stream.cover_image = pic_url
        stream.tags = __get_tag.(tags)#[tags]
        stream.subs = __get_subs(subscriber_list)#[subscriber_list]

        stream.put()

        # Just try to retrieve from NDB
        target_query = Stream.query(ancestor = user_key(obj.username)
        targets = target_query.fetch(10)

        template_values = {
            'stream': targets,
        }

        template = JINJA_ENVIRONMENT.get_template('show_stream.html')
        self.response.write(template.render(template_values))
        

# [START app]
app = webapp2.WSGIApplication([
    #('/', MainPage),
    ('/management', Management)
    # ('/sign', Guestbook),
], debug=True)
# [END app]
