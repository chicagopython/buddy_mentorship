#!/bin/sh

if [[ $DYNO == "web"* ]]; then
  gunicorn buddy_mentorship.wsgi:application -w 4 --bind 0.0.0.0:$PORT
elif  [[ $DYNO == "release"* ]]; then
  python manage.py migrate
fi