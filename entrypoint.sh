#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# echo "---> Running Django database migrations..."
# python manage.py migrate --noinput

# echo "---> Collecting static files..."
# python manage.py collectstatic --noinput --clear

echo "---> Starting Daphne ASGI server..."
# Start Daphne with explicit port binding from $PORT, default to 8000 if not set
exec daphne -b 0.0.0.0 -p ${PORT:-8000} odintrack_project.asgi:application --access-log - 