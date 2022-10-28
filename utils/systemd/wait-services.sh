#!/bin/bash
echo "Checking is service running"
while /usr/bin/systemctl status --no-page | grep update-repo@ | grep -v grep;
do
  sleep 1
done