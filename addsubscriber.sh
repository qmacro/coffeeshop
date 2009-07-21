#!/bin/sh

# Add a subscriber for a given channel

. ./config.sh

CHANNELID=$1
if [ -z $CHANNELID ]
  then CHANNELID=1
fi

SUBSCRIBER=$2
if [ -z $SUBSCRIBER ]
  then SUBSCRIBER=testsubscriber
fi

echo "name=$SUBSCRIBER&resource=$SUBROOT/$SUBSCRIBER" \
  | POST -Se $HUBROOT/channel/$CHANNELID/subscriber/ \
  | grep -E '^(POST |Location:)'
