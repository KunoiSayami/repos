#!/bin/bash

if [ -f /home/build/repos/.placehold ]; then
  rm /home/build/repos/.placehold
fi

find /home/build/repos -maxdepth 0 -empty -exec rm -rf {} \;

if [ -d /home/build/repos ]; then
  chown -R build:build /home/build/repos
fi