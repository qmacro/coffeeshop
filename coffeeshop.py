# coffeeshop
# A lightweight REST-orientated pubsub mechanism
# (c) 2009 DJ Adams
# See https://github.com/qmacro/coffeeshop/

import os
import re
import cgi
import logging
import wsgiref.handlers
import datetime
#import urllib2

from models import Channel, Subscriber, Message, Delivery
from bucket import agoify

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
from google.appengine.api import urlfetch
from django.utils import simplejson

VERSION = "0.01"
DEBUG = True

# Name of task queue for message distribution
QUEUE_DISTRIBUTION='msgdist'

# Statuses
STATUS_DELIVERED='DELIVERED'

CT_JSON = 'application/json'

if DEBUG:
  logging.getLogger().setLevel(logging.DEBUG)


def isNumber(n):
  try:
    int(n); return True
  except ValueError:
    pass


class EntityRequestHandler(webapp.RequestHandler):
  """Base RequestHandler supplying common methods
  for retrieving entities such as channels and subscribers
  """
  def _getentity(self, type, id):
    entity = None

    # id must be numeric
    if not isNumber(id):
      self.response.out.write("%s must be numeric (got %s)" % (type.__name__, id))
      self.response.set_status(404)
      return

    id = int(id)
    if id == 0:
      self.response.out.write("%s cannot be zero (got %s)" % (type.__name__, id))
      self.response.set_status(404)
      return

    entity = type.get_by_id(int(id))
    if entity is None:
      self.response.out.write("%s %s not found" % (type.__name__, id))
      self.response.set_status(404)
      return

    return entity



class MainPageHandler(webapp.RequestHandler):
  def get(self):
    template_values = {
      'version': VERSION,
      'server_software': os.environ.get("SERVER_SOFTWARE", "unknown"),
    }
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))

class ChannelContainerHandler(webapp.RequestHandler):
  """Handler for main /channel/ resource
  """
  def get(self):
    """Show list of channels
    """
#   TODO: paging
    channels = []
    for channel in db.GqlQuery("SELECT * FROM Channel ORDER BY created DESC"):
      channels.append({
        'channelid': channel.key().id(),
        'name': channel.name,
        'created': channel.created,
        'created_ago': agoify(channel.created),
      })
    template_values = {
      'channels': channels,
    }
    path = os.path.join(os.path.dirname(__file__), 'channel_list.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    """Handles a POST to the /channel/ resource
    Creates a new channel resource (/channel/{id}) and returns
    its Location with a 201
    """
    channel = Channel()
    name = self.request.get('name').rstrip('\n')
    channel.name = name
    channel.put()
#   Not sure I like this ... re-put()ing
    if len(channel.name) == 0:
      channel.name = 'channel-' + str(channel.key().id())
      channel.put()

    # If we've got here from a web form, redirect the user to the 
    # channel list, otherwise return the 201
    if self.request.get('channelsubmissionform'):
      self.redirect('/channel/')
    else:
      self.response.headers['Location'] = self.request.url + str(channel.key().id()) + '/'
      self.response.set_status(201)


class ChannelSubmissionformHandler(webapp.RequestHandler):
  """Handles the channel submission form resource
  /channel/submissionform/
  """
  def get(self):
    """Renders channel submission form, that has a POST action to
    the /channel/ resource
    """
    path = os.path.join(os.path.dirname(__file__), 'channelsubmissionform.html')
    self.response.out.write(template.render(path, {}))


class ChannelHandler(EntityRequestHandler):
  """Handles an individual channel resource
  e.g. /channel/123/
  Shows when it was created, and a link to subscribers (if there are any)
  """
  def get(self, channelid):
    """Return general information on the channel"""
    channel = self._getentity(Channel, channelid)
    if channel is None: return

    anysubscribers = Subscriber.all().filter('channel =', channel).fetch(1)
    
    template_values = {
      'channel': channel,
      'anysubscribers': anysubscribers,
    }
    path = os.path.join(os.path.dirname(__file__), 'channel_detail.html')
    self.response.out.write(template.render(path, template_values))

  # The publish bit!
  def post(self, channelid):
    """Handles a message publish to this channel"""
    channel = self._getentity(Channel, channelid)
    if channel is None: return

    contenttype = self.request.headers['Content-Type']

    # Save message
    message = Message(
      contenttype = contenttype,
      body = self.request.body,
      channel = channel,
    )
    message.put()

#   for subscriber in Subscriber.all().filter('channel =', channel):
    subscribers = Subscriber.all().filter('channel =', channel)
    if subscribers.count():
      for subscriber in subscribers:
  
        # Set up delivery of message to subscriber
        delivery = Delivery(
          message = message,
          recipient = subscriber,
        )
        delivery.put()
  
      # Kick off a task to distribute message
      taskqueue.Task(
        url='/distributor/' + str(message.key())
      ).add(QUEUE_DISTRIBUTION)

      logging.debug("Delivery queued for %d subscribers of channel %s" % (subscribers.count(), channelid))
    else:
      logging.debug("No subscribers for channel %s" % (channelid, ))

    # TODO should we return a 202 instead of a 302?
    # Actually I think it's just a 201, as we've created a new (message) resource
#   self.redirect(self.request.url + 'message/' + str(message.key()))

    # Try to detect whether we're from the coffeeshop browser, and if so, return a 302
    self.response.headers['Location'] = self.request.url + "message/%s" % str(message.key())
    if contenttype == "application/x-www-form-urlencoded" and self.request.get('messagesubmissionform') == "coffeeshop":
      self.response.set_status(302)
    else:
      self.response.set_status(201)

  def delete(self, channelid):
    """Handle deletion of a channel. Only allow if there are no subscribers"""
    channel = self._getentity(Channel, channelid)
    if channel is None: return

    # Check the subscribers
    nrsubscribers = Subscriber.all().filter('channel =', channel).count()
    if nrsubscribers:
      # Can't delete if subscribers still exist
      self.response.set_status(405, "CANNOT DELETE - %s SUBSCRIBERS" % nrsubscribers)
      self.response.headers['Allow'] = "GET, POST"
    else:
      channel.delete()
      self.response.set_status(204)


class ChannelSubscriberSubmissionformHandler(webapp.RequestHandler):
  """Handles the subscriber submission form for a given channel,
  i.e. resource /channel/{id}/subscriber/submissionform
  """
  def get(self, channelid):
    """Handles a GET to the /channel/{id}/subscriber/submissionform resource
    """
    channel = Channel.get_by_id(int(channelid))
    if channel is None:
      self.response.out.write("Channel %s not found" % (channelid, ))
      self.response.set_status(404)
      return

    template_values = {
      'channel': channel,
      'channelsubscriberresource': '/channel/' + channelid + '/subscriber/',
    }
    path = os.path.join(os.path.dirname(__file__), 'subscribersubmissionform.html')
    self.response.out.write(template.render(path, template_values))


class ChannelSubscriberContainerHandler(webapp.RequestHandler):
  """Handles the subscribers for a given channel, i.e. resource
  /channel/{id}/subscriber/
  """
  def get(self, channelid):
    """Handles a GET to the /channel/{id}/subscriber/ resource
    """
    channel = Channel.get_by_id(int(channelid))
    if channel is None:
      self.response.out.write("Channel %s not found" % (channelid, ))
      self.response.set_status(404)
      return

    subscribers = []
    for subscriber in Subscriber.all().filter('channel =', channel):
      subscribers.append({
        'subscriberid': subscriber.key().id(),
        'name': subscriber.name,
        'resource': subscriber.resource,
        'created': subscriber.created,
      })

    template_values = {
      'channel': channel,
      'subscribers': subscribers,
    }
    path = os.path.join(os.path.dirname(__file__), 'channelsubscriber.html')
    self.response.out.write(template.render(path, template_values))

  def post(self, channelid):
    """Handles a POST to the /channel/{id}/subscriber/ resource
    which is to add a subscriber to the channel
    """
#   Get channel first
    channel = Channel.get_by_id(int(channelid))
    if channel is None:
      self.response.out.write("Channel %s not found" % (channelid, ))
      self.response.set_status(404)
      return

#   Add subscriber
    name = self.request.get('name').rstrip('\n')
    resource = self.request.get('resource').rstrip('\n')
    subscriber = Subscriber()
    subscriber.channel = channel
    subscriber.name = name
    subscriber.resource = resource
    subscriber.put()
#   Not sure I like this ... re-put()ing
    if len(subscriber.name) == 0:
      subscriber.name = 'subscriber-' + str(subscriber.key().id())
      subscriber.put()

#   If we've got here from a web form, redirect the user to the 
#   channel subscriber resource, otherwise return the 201
    if self.request.get('subscribersubmissionform'):
      self.redirect(self.request.path_info)
    else:
      self.response.headers['Location'] = self.request.url + str(subscriber.key().id()) + '/'
      self.response.set_status(201)


class ChannelSubscriberHandler(EntityRequestHandler):
  """Handles a given channel subscriber, i.e. resource
  /channel/{id}/subscriber/{id}/
  """

  def get(self, channelid, subscriberid):
    channel = self._getentity(Channel, channelid)
    if channel is None: return

    subscriber = self._getentity(Subscriber, subscriberid)
    if subscriber is None: return

    template_values = {
      'channel': channel,
      'subscriber': subscriber,
    }
    path = os.path.join(os.path.dirname(__file__), 'subscriber_detail.html')
    self.response.out.write(template.render(path, template_values))

  def delete(self, channelid, subscriberid):
    """Handle deletion of a subscribers.
    Only allow if there are no outstanding deliveries."""

    channel = self._getentity(Channel, channelid)
    if channel is None: return

    subscriber = self._getentity(Subscriber, subscriberid)
    if subscriber is None: return

    nrdeliveries = Delivery.all().filter('recipient =', subscriber).filter('status !=', STATUS_DELIVERED).count()
    if nrdeliveries:
      # Can't delete if deliveries still outstanding
      self.response.set_status(405, "CANNOT DELETE - %s DELIVERIES OUTSTANDING" % nrdeliveries)
      self.response.headers['Allow'] = "GET"
    else:
      subscriber.delete()
      self.response.set_status(204)


class SubscriberContainerHandler(webapp.RequestHandler):
  """Handles the subscriber container resource, i.e.
  /subscriber/
  GET will just return a list of subscribers, by channel
  """
  def get(self):
    subscribers = db.GqlQuery("SELECT * FROM Subscriber "
                                  "ORDER BY channel ASC, created DESC")
    template_values = {
      'subscribers': subscribers,
    }
    path = os.path.join(os.path.dirname(__file__), 'subscriber.html')
    self.response.out.write(template.render(path, template_values))
    

class ChannelMessageHandler(webapp.RequestHandler):
  """Handles message delivery status resources in the form of
  /channel/{cid}/message/{mid}
  """
  def get(self, channelid, messageid):
    message = Message.get(messageid)
    if message is None:
      self.response.out.write("Message %s not found" % (messageid, ))
      self.response.set_status(404)
      return

    deliveries = Delivery.all().filter('message =', message)

    channelurl = "%s://%s/channel/%d/" % (self.request.scheme, self.request.host, message.channel.key().id())

    # Poor conneg
    if (self.request.headers.has_key('Accept')
      and self.request.headers['Accept'] == CT_JSON):
      logging.info("JSON requested")
      deliveryinfo = []
      for d in deliveries:
        deliveryinfo.append({
          'recipient': "%ssubscriber/%d/" % (channelurl, d.recipient.key().id()),
          'status': d.status,
          'timestamp': d.updated.strftime("%Y-%m-%dT%H:%M:%SZ"),
      })
      info = {
        'message': {
          'resource': "%smessage/%s" % (channelurl, str(message.key())),
          'key': str(message.key()),
          'created': message.created.strftime("%Y-%m-%dT%H:%M:%SZ"),
          'channel': channelurl,
          'delivery': deliveryinfo,
        },
      }
      self.response.out.write(simplejson.dumps(info))
      self.response.headers['Content-Type'] = CT_JSON
      return

    template_values = {
      'message': message,
      #'deliveries': Delivery.all().filter('message =', message),
      'deliveries': deliveries,
    }
    path = os.path.join(os.path.dirname(__file__), 'messagedetail.html')
    self.response.out.write(template.render(path, template_values))


class ChannelMessageContainerHandler(EntityRequestHandler):
  """Handles the message container resource for a channel, in the form of
  /channel/{cid}/message/
  """
  def get(self, channelid):
    channel = self._getentity(Channel, channelid)
    if channel is None: return

    template_values = {
      'channel': channel,
      'messages': Message.all().filter('channel =', channel),
    }
    path = os.path.join(os.path.dirname(__file__), 'messagelist.html')
    self.response.out.write(template.render(path, template_values))


class ChannelMessageSubmissionformHandler(EntityRequestHandler):
  """Handles the channel message submission form for a given channel,
  i.e. resource /channel/{id}/message/submissionform
  """
  def get(self, channelid):
    channel = self._getentity(Channel, channelid)
    if channel is None: return

    template_values = {
      'channel': channel,
    }
    path = os.path.join(os.path.dirname(__file__), 'messagesubmissionform.html')
    self.response.out.write(template.render(path, template_values))


class MessageHandler(webapp.RequestHandler):
  """Handles the message overview resource, i.e.
  /message/
  GET will just return a list of messages, by channel
  Not sure whether this resource will cause confusion where you'd think
  you can POST to this resource (which you can't, of course).
  """
  def get(self):
    # This seems expensive. TODO: refactor
    messages = []
    for message in db.GqlQuery("SELECT * FROM Message ORDER BY created DESC"):
      recipients = Delivery.all().filter('message =', message).count()
      delivered = Delivery.all().filter('message =', message).filter('status =', STATUS_DELIVERED).count()
      messages.append({
        'message': message,
        'recipients': recipients,
        'delivered': delivered,
      })
    template_values = {
      'messages': messages,
    }
    path = os.path.join(os.path.dirname(__file__), 'message.html')
    self.response.out.write(template.render(path, template_values))
    


class DistributorWorker(webapp.RequestHandler):
  """Task Queue worker - distributes a given message. The task queue 
  mechanism may retry this if not all the deliveries have been made.
  It should keep retrying until they all have been made.
  """
  def post(self, messageid):
    # Retrieve the message, make sure it exists
    message = Message.get(messageid)
    if message is None:
       logging.debug("Message %s does not exist, returning 200" % (messageid, ))
       self.response.set_status(200)
       return

    # Assume all deliveries are successful (i.e. this task is done)
    deliveriessucceeded = True

    # For this message, process those deliveries that have not yet been
    # delivered (status will be None)
    for delivery in Delivery.all().filter('message =', message).filter('status =', None):
      logging.debug("Processing delivery %s" % (delivery.key(), ))

      # Make the delivery with a POST to the recipient's resource
      # sending the published body, with the published body's content-type
      status = 999
      try:
        result = urlfetch.fetch(
          url = delivery.recipient.resource,
          payload = message.body,
          method = urlfetch.POST,
          headers = { 'Content-Type': message.contenttype },
          follow_redirects = False,
        )
        status = result.status_code
      except: 
        logging.error("urlfetch encountered an EXCEPTION")

      # If we've had a successful status then consider this 
      # particular delivery done. Otherwise, mark the delivery
      # as failed.
      if status < 400:
        delivery.status = STATUS_DELIVERED
        delivery.put()
      else:
        deliveriessucceeded = False

    # If there are failed deliveries, mark this task as failed
    # so that the task queue mechanism will retry.
    if not deliveriessucceeded:
      self.response.set_status(500)


def main():
  application = webapp.WSGIApplication([
    (r'/', MainPageHandler),
    (r'/channel/submissionform/?', ChannelSubmissionformHandler),
    (r'/channel/(.+?)/subscriber/submissionform', ChannelSubscriberSubmissionformHandler),
    (r'/channel/(.+?)/subscriber/', ChannelSubscriberContainerHandler),
    (r'/channel/(.+?)/subscriber/(.+?)/', ChannelSubscriberHandler),
    (r'/channel/(.+?)/message/submissionform/?', ChannelMessageSubmissionformHandler),
    (r'/channel/(.+?)/message/(.+)', ChannelMessageHandler),
    (r'/channel/(.+?)/message/', ChannelMessageContainerHandler),
    (r'/channel/(.+?)/', ChannelHandler),
    (r'/channel/?', ChannelContainerHandler),
    (r'/subscriber/', SubscriberContainerHandler),
    (r'/message/', MessageHandler),
    (r'/distributor/(.+?)', DistributorWorker),
  ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == "__main__":
  main()





