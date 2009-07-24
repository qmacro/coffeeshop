#!/bin/sh
# starter script for the local dev appengine

PYTHON=python2.5
APPENGINELOCATION=~/dev/google_appengine
HOST=`hostname`

# If unspecified, port is 8888
PORT=$1
if [ -z $PORT ]
  then PORT=8888
fi

# Can use this for e.g. -c clearing the db
EXTRAOPTS=$2

$PYTHON $APPENGINELOCATION/dev_appserver.py -a $HOST -p $PORT $EXTRAOPTS .
