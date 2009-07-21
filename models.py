from google.appengine.ext import db

class Channel(db.Model):
  name = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)

class Subscriber(db.Model):
  name = db.StringProperty()
  channel = db.ReferenceProperty(Channel)
  resource = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)

class Message(db.Model):
  contenttype = db.StringProperty()
  body = db.BlobProperty()
  channel = db.ReferenceProperty(Channel)
  created = db.DateTimeProperty(auto_now_add=True)

class Delivery(db.Model):
  message = db.ReferenceProperty(Message)
  recipient = db.ReferenceProperty(Subscriber)
  status = db.StringProperty()
  updated = db.DateTimeProperty(auto_now=True)
