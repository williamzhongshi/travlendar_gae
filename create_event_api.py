import os
import urllib
import logging
import cloudstorage as gcs

from google.appengine.api import app_identity, mail, users, search
from google.appengine.ext import ndb
from flask import Flask, jsonify, abort, request, make_response, url_for

import jinja2
import webapp2
import json

app = Flask(__name__)

# def serializeResult(result):
#    #l = []
#    #for s in result:
#    re = {}
#    re['body'] =

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
    # re =
    # return json.dumps({"OK"})
