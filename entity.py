from google.appengine.ext import db
from oauth2client.contrib.appengine import CredentialsProperty

class CredentialsModel(db.Model):
  credentials = CredentialsProperty()
