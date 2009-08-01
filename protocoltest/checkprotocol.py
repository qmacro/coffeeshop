#!/usr/bin/python2.5

import unittest
import httplib, urllib, re
import logging, sys

HUBROOT = 'giant:8888'
LOGFILE = 'unittest.log'
SUBSCRIBER_CONTAINER = 'subscriber/'

logger = None

# Relative resource patterns
CHANNEL = r'^\/channel\/(\d+)\/$'

def log(message, callhier=1):
  # callhier=1 : gets the name of this function's caller
  caller = sys._getframe(callhier).f_code.co_name
  logger.debug("%s: %s" % (caller, message))


def newChannel(conn, channelname="Channel A"):
  data = urllib.urlencode({ 'name': channelname })
  conn.request("POST", "/channel/", data)
  res = conn.getresponse()
  location = res.getheader('Location')
  idsearch = re.search(CHANNEL, location)
  log("created channel %s" % location, 2)
  return (res.status, location, idsearch.group(1))


class BasicTests(unittest.TestCase):

  def setUp(self):
    self.conn = httplib.HTTPConnection(HUBROOT)

  def tearDown(self):
    self.conn = None

  def testStartPageExists(self):
    """Check the start page exists"""
    self.conn.request("GET", "/")
    res = self.conn.getresponse()
    self.assertEqual(res.status, 200)


class ChannelTests(unittest.TestCase):
  
  def setUp(self):
    self.conn = httplib.HTTPConnection(HUBROOT)

  def tearDown(self):
    self.conn = None

  def testChannelContainerExists(self):
    """The channel container page exists"""
    self.conn.request("GET", "/channel/")
    res = self.conn.getresponse()
    self.assertEqual(res.status, 200)

  def testChannelCreationStatus(self):
    """A channel can be created"""
    status, location, id = newChannel(self.conn, "testChannelCreationStatus")
    self.assertEqual(status, 201)
    
  def testDuplicateChannelName(self):
    """A name can be used for more than one channel"""
    status, location, id = newChannel(self.conn, "testDuplicateChannelName")
    self.assertEqual(status, 201)
    status, location, id = newChannel(self.conn, "testDuplicateChannelName")
    self.assertEqual(status, 201)
    
  def testChannelCreationLocation(self):
    """A valid Location is returned for a created channel"""
    status, location, id = newChannel(self.conn, "testChannelCreationLocation")
    self.assertTrue(re.search(CHANNEL, location))

  def testChannelInfo(self):
    """There is channel info available"""
    # Create the channel first
    status, location, id = newChannel(self.conn, "testChannelInfo")

    # Check we have channel info - 
    # We're looking for a 200, and "No subscribers"
    self.conn.request("GET", location)
    res = self.conn.getresponse()

    self.assertEqual(res.status, 200)
    self.assertTrue(re.search('No subscribers', res.read()))

  def testInvalidChannelId(self):
    """Get 404 when the channel id is non-numeric"""
    self.conn.request("GET", "/channel/nonnumeric/")
    res = self.conn.getresponse()
    self.assertEqual(res.status, 404)

  def testChannelNotFound(self):
    """404 is returned for non-existent channel"""
    self.conn.request("GET", "/channel/9999999/")
    res = self.conn.getresponse()
    self.assertEqual(res.status, 404)

  def testZeroChannelNotFound(self):
    """404 is returned for channel zero"""
    self.conn.request("GET", "/channel/0/")
    res = self.conn.getresponse()
    self.assertEqual(res.status, 404)

    
class SubscriberTests(unittest.TestCase):
  
  def setUp(self):
    self.conn = httplib.HTTPConnection(HUBROOT)

  def tearDown(self):
    self.conn = None

  def testSubscriberContainerResourceExists(self):
    """A subscriber container resource exists for a channel"""
    # Create the channel first
    status, location, id = newChannel(self.conn, "testSubscriberContainerResourceExists")

    # GET the subscriber container
    self.conn.request("GET", location + SUBSCRIBER_CONTAINER)
    res = self.conn.getresponse()
    log("retrieve %s%s : %s" % (location, SUBSCRIBER_CONTAINER, res.status))
    self.assertEqual(res.status, 200)


if __name__ == '__main__':
  logger = logging.getLogger("unitlogger")
  logger.setLevel(logging.DEBUG)
  loghandler = logging.FileHandler(LOGFILE, "w")
  loghandler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
  loghandler.setLevel(logging.DEBUG)
  logger.addHandler(loghandler)

  unittest.main()
  
