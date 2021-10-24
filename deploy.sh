#!/bin/bash
if [ $# -eq 0 ]; then
    echo 'Should provide least one argument'
    exit 1
fi
ARCH=$(/usr/bin/uname -m)
/usr/bin/rsync --partial -r --update --link --delete $DEPLOY_ARGS --exclude=.gitignore  "packages/$ARCH" $1:/var/www/repo/
echo "date +%s > /var/www/repo/$ARCH/LAST_SYNC" | /usr/bin/xargs /usr/bin/ssh $1
