#!/bin/bash
set -e
LOGFILE=/home/c-beam/c-beam/c-beamd/c-beamd.log
LOGDIR=$(dirname $LOGFILE)
NUM_WORKERS=3
# user/group to run as
USER=c-beam
GROUP=c-beam
ADDRESS=0.0.0.0:4254
DJANGO_SETTINGS=cbeamd.settings
DJANGO_SETTINGS_MODULE=cbeamd.settings
source /home/c-beam/.virtualenvs/c-beam/bin/activate
cd /home/c-beam/c-beam/c-beamd
test -d $LOGDIR || mkdir -p $LOGDIR
exec gunicorn -w $NUM_WORKERS --bind=$ADDRESS \
  --user=$USER --group=$GROUP --log-level=debug \
  cbeamd.wsgi:application \
  --log-file=$LOGFILE 2>>$LOGFILE
