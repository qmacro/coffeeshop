#!/usr/bin/python2.5

import unittest
import httplib, urllib, re

HUBROOT = 'giant:8888'

# Relative resource patterns
CHANNEL = r'^\/channel\/(\d+)\/$'

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
    data = urllib.urlencode({ 'name': 'Channel A' })
    self.conn.request("POST", "/channel/", data)
    res = self.conn.getresponse()
    self.assertEqual(res.status, 201)
    
  def testChannelCreationLocation(self):
    """A valid Location is returned for a created channel"""
    data = urllib.urlencode({ 'name': 'Channel A' })
    self.conn.request("POST", "/channel/", data)
    res = self.conn.getresponse()
    self.assertTrue(re.search(CHANNEL, res.getheader('Location')))

  def testChannelInfo(self):
    """There is channel info available"""
    # Create the channel first
    data = urllib.urlencode({ 'name': 'testChannelInfo' })
    self.conn.request("POST", "/channel/", data)
    createres = self.conn.getresponse()

    # Check we have channel info
    self.conn.request("GET", createres.getheader('Location'))
    checkres = self.conn.getresponse()

    # We're looking for a 200, and "No subscribers"
    self.assertEqual(checkres.status, 200)
    self.assertTrue(re.search('No subscribers', checkres.read()))

  def testChannelNotFound(self):
    """404 is returned for non-existent channel"""
    self.conn.request("GET", "/channel/9999999/")
    res = self.conn.getresponse()
    self.assertEqual(res.status, 404)

  def testZeroChannelNotFound(self):
    """404 is returned for non-existent channel"""
    self.conn.request("GET", "/channel/0/")
    res = self.conn.getresponse()
    self.assertEqual(res.status, 404)

     

class OtherTests(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass
    
  def testSomething(self):
    pass

if __name__ == '__main__':
  unittest.main()
  
