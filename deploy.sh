#!/bin/bash

# end up when failed
set -Eeuo pipefail

if [ $# -eq 0 ]; then
    echo 'Should provide least one argument'
    exit 1
fi
/usr/bin/date +%s > "packages/LASTSYNC"
/usr/bin/rsync --partial -r -c --update --links --delete --exclude=.gitignore "packages/" $1:/var/www/repo/
