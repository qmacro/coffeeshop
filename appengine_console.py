#!/usr/bin/python2.5

import code
import getpass
import sys
import os

base_path = "/home/dj/dev/google_appengine"
sys.path.append(base_path)
sys.path.append(base_path + "/lib/webob")
sys.path.append(base_path + "/lib/django")
sys.path.append(base_path + "/lib/yaml/lib")

from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.ext import db

def auth_func():
# return 'admin',''
  return raw_input('Username:'), getpass.getpass('Password:')

if len(sys.argv) < 2:
  print "Usage: %s app_id [host]" % (sys.argv[0],)
app_id = sys.argv[1]
if len(sys.argv) > 2:
  host = sys.argv[2]
else:
  host = "%s.appspot.com" % app_id

print "Host is %s" % host
  
remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

pythonrc = os.environ.get("PYTHONSTARTUP")
if pythonrc and os.path.isfile(pythonrc):
  try:
    execfile(pythonrc)
  except NameError:
    pass
import user
code.interact('App Engine interactive console for %s' % (app_id,), None, locals()) 

