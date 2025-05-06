#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# echo "---> Running Django database migrations..."
# python manage.py migrate --noinput

# echo "---> Collecting static files..."
# python manage.py collectstatic --noinput --clear

echo "---> Starting Gunicorn server (with debug logging, explicit bind, no pre-commands)..."
# Start Gunicorn with debug logging and explicit port binding
# Ensure PORT environment variable is available in Railway
exec gunicorn odintrack_project.wsgi --bind 0.0.0.0:${PORT:-8080} --log-file - --log-level debug 