#!/bin/sh

# Add a channel

. ./config.sh

CHANNELNAME=$1
if [ -z $CHANNELNAME ]
  then CHANNELNAME=testchannel
fi

echo "name=$CHANNELNAME" \
  | POST -Se $HUBROOT/channel/ \
  | grep -E '^(POST |Location:)'

