import os
import re
import cgi
import logging
import wsgiref.handlers

from models import Channel, Subscriber

from google.appengine.ext.webapp import template
#from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db

#     ***************
class MainPageHandler(webapp.RequestHandler):
#     ***************
  def get(self):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))

#     ***********************
class ChannelContainerHandler(webapp.RequestHandler):
#     ***********************
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
    logging.info("submitted channel: %s" % (name, ))
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
      self.response.headers['Location'] = '/channel/' + str(channel.key().id())
      self.response.set_status(201)


#     ****************************
class ChannelSubmissionformHandler(webapp.RequestHandler):
#     ****************************
  """Handles the channel submission form resource
  /channel/submissionform/
  """
  def get(self):
    """Renders channel submission form, that has a POST action to
    the /channel/ resource
    """
    path = os.path.join(os.path.dirname(__file__), 'channelsubmissionform.html')
    self.response.out.write(template.render(path, {}))


#     **************
class ChannelHandler(webapp.RequestHandler):
#     **************
  """Handles an individual channel resource
  e.g. /channel/123/
  """
  def get(self, channelid):
    channel = Channel.get_by_id(int(channelid))
    anysubscribers = Subscriber.all().filter('channel =', channel).fetch(1)
    
    logging.info(anysubscribers)
    template_values = {
      'channel': channel,
      'anysubscribers': anysubscribers,
    }
    path = os.path.join(os.path.dirname(__file__), 'channel_detail.html')
    self.response.out.write(template.render(path, template_values))


#     **************************************
class ChannelSubscriberSubmissionformHandler(webapp.RequestHandler):
#     **************************************
  """Handles the subscriber submission form for a given channel,
  i.e. resource /channel/{id}/subscriber/submissionform
  """
  def get(self, channelid):
    """Handles a GET to the /channel/{id}/subscriber/submissionform resource
    """
    logging.info("ChannelSubscriberSubmissionformHandler GET")
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


#     *********************************
class ChannelSubscriberContainerHandler(webapp.RequestHandler):
#     *********************************
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
      logging.info(subscriber.key().id())
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
    path = os.path.join(os.path.dirname(__file__), 'subscriber.html')
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

#   If we've got here from a web form, redirect the user to the 
#   channel subscriber resource, otherwise return the 201
    if self.request.get('subscribersubmissionform'):
      logging.info("rediercting to %s" % (self.request.path_info, ))
      self.redirect(self.request.path_info)
    else:
      self.response.headers['Location'] = '/channel/' + channelid + '/subscriber/' + str(subscriber.key().id()) + '/'
      self.response.set_status(201)


#     ************************
class ChannelSubscriberHandler(webapp.RequestHandler):
#     ************************
  """Handles a given channel subscriber, i.e. resource
  /channel/{id}/subscriber/{id}/
  """
  def get(self, channelid, subscriberid):
    """Handles a GET to the /channel/{id}/subscriber/{id}/ resource
    """
    channel = Channel.get_by_id(int(channelid))
    if channel is None:
      self.response.out.write("Channel %s not found" % (channelid, ))
      self.response.set_status(404)
      return

    subscriber = Subscriber.get_by_id(int(subscriberid))
    if subscriber is None:
      self.response.out.write("Subscriber %s for channel %s not found" % (subscriberid, channelid))
      self.response.set_status(404)
      return

    template_values = {
      'channel': channel,
      'subscriber': subscriber,
    }
    path = os.path.join(os.path.dirname(__file__), 'subscriber_detail.html')
    self.response.out.write(template.render(path, template_values))



def main():
  application = webapp.WSGIApplication([
    (r'/', MainPageHandler),
    (r'/channel/submissionform/?', ChannelSubmissionformHandler),
    (r'/channel/(.+?)/subscriber/submissionform', ChannelSubscriberSubmissionformHandler),
    (r'/channel/(.+?)/subscriber/', ChannelSubscriberContainerHandler),
    (r'/channel/(.+?)/subscriber/(.+?)/', ChannelSubscriberHandler),
    (r'/channel/(.+?)/?', ChannelHandler),
    (r'/channel/?', ChannelContainerHandler),
  ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == "__main__":
  main()





