#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "---> Running Django database migrations..."
python manage.py migrate --noinput

echo "---> Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "---> Starting Gunicorn server..."
# Replace the line below with your project's actual Gunicorn command
# This should match what was in your Procfile's web process or your custom start command
exec gunicorn odintrack_project.wsgi --log-file - 