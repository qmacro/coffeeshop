#!/bin/sh

# Set up some channels with subscribers

CID=`./addchannel.sh channelOne | grep -v '^POST' | sed -re 's/^.+channel\/([0123456789]+)\//\1/'`
./addsubscriber.sh $CID alpha
./addsubscriber.sh $CID beta

CID=`./addchannel.sh channelTwo | grep -v '^POST' | sed -re 's/^.+channel\/([0123456789]+)\//\1/'`
./addsubscriber.sh $CID gamma
