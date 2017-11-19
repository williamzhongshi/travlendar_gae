from google.appengine.ext import ndb

class User(ndb.Expando):
    username = ndb.StringProperty(indexed=True)
    email = ndb.StringProperty(indexed=True)
    subscribe_stream = ndb.StringProperty(repeated=True)
    travel_option = ndb.StringProperty(repeated=True)
    display = ndb.StringProperty()

class CredentialsM(ndb.Expando):
  access_token = ndb.StringProperty()
  user_email = ndb.StringProperty()

