#!/bin/sh
python2.5 appengine_console.py `pwd | sed -e 's/^.*\///'` giant:8888
