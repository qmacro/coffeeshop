from google.appengine.ext import db

class Channel(db.Model):
  name = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)

class Subscriber(db.Model):
  name = db.StringProperty()
  channel = db.ReferenceProperty(Channel)
  resource = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)

