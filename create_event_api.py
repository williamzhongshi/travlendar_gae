import os
import urllib
import logging
import cloudstorage as gcs

from google.appengine.api import app_identity, mail, users, search
from google.appengine.ext import ndb
from entities_def import User, Photo, Stream
from all_stream_api import serializeStream, get_char_set
from flask import Flask, jsonify, abort, request, make_response, url_for

import jinja2
import webapp2
import json

app = Flask(__name__)


@app.route('/api/create_event/<name>', methods=['POST'])
def post(name=None):
    logging.info("got name" % name)
