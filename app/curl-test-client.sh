#!/bin/bash
for i in {1..100}; do
  USER_AGENT="Client-$i"
  curl -s -k -A "$USER_AGENT" -H 'header info' -b 'stuff' 'http://flask-app.cnr.com:30080/api?caner='$i
done
