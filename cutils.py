# Appengine console utils

CHUNK = 200

from google.appengine.ext import db
from models import Channel, Subscriber, Message, Delivery

def delete_all_deliveries():
  while Delivery.all().fetch(CHUNK):
    db.delete(Delivery.all().fetch(CHUNK))

def delete_all_messages():
  while Message.all().fetch(CHUNK):
    db.delete(Message.all().fetch(CHUNK))

def delete_all_subscribers():
  while Subscriber.all().fetch(CHUNK):
    db.delete(Subscriber.all().fetch(CHUNK))

def delete_all_channels():
  while Channel.all().fetch(CHUNK):
    db.delete(Channel.all().fetch(CHUNK))

def deleteall():
  delete_all_deliveries()
  delete_all_messages()
  delete_all_subscribers()
  delete_all_channels()
