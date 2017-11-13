from google.appengine.ext import ndb


class User(ndb.Expando):
    username = ndb.StringProperty(indexed=True)
    email = ndb.StringProperty(indexed=True)
    subscribe_stream = ndb.StringProperty(repeated=True)


