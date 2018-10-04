#!/bin/bash

NAME="apple_app"                                   # Name of the application
DJANGODIR=/home/iesfinanceadmin/apple/financial               # Django project directory
SOCKFILE=/home/iesfinanceadmin/financial_env/run/gunicorn.sock  # we will communicte using this unix socket
USER=iesfinanceadmin                                         # the user to run as
GROUP=iesfinanceadmin                                        # the group to run as
NUM_WORKERS=6                                       # how many worker processes should Gunicorn spawn
TIMEOUT=600
DJANGO_SETTINGS_MODULE=financial.settings      # which settings file should Django use
DJANGO_WSGI_MODULE=financial.wsgi              # WSGI module name
echo "Starting $NAME as `whoami`"

# Activate the virtual environment

cd $DJANGODIR
source /home/iesfinanceadmin/financial_env/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist

RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)

exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --timeout $TIMEOUT \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=-
