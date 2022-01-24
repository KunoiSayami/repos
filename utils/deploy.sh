#!/bin/bash

# end up when failed
set -Eeuo pipefail

if [ $# -eq 0 ]; then
    echo 'Should provide least one argument'
    exit 1
fi

if [ -z ${SSH_CLIENT+x} ]; then
    ADDITIONAL_PARAM="--partial"
else
    ADDITIONAL_PARAM="--partial -v"
fi

/usr/bin/date +%s > "packages/LASTSYNC"
/usr/bin/rsync $ADDITIONAL_PARAM -r -c --update --links --delete --exclude=.gitignore "packages/" $1:/var/www/repo/
