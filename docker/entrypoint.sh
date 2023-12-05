#!/bin/bash

if [ -z "$1" ]; then
    REMOTE_REPOSITORY="$1";
else
    REMOTE_REPOSITORY=https://github.com/kunoisayami/repos
fi

/home/build/dockerbuild.sh $REMOTE_REPOSITORY