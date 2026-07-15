#!/bin/bash
set -e

# Set CACHE_URL to use local memory
# This is needed because currently memcached is not started and we need cache inside management commands
export CACHE_URL=locmemcache://

# Ensure a Django secret key exists.
# A missing key would fall back to the insecure shared default baked into
# settings.py, which settings.py now refuses to run with when DEBUG is off.
# Generating a fresh random key per start is safe: it only invalidates existing
# login sessions, it does not touch stored data.
# Generated without loading Django settings to avoid the insecure-default guard.
if [ -z "${DJANGO_SECRET_KEY}" ]; then
  echo "DJANGO_SECRET_KEY is not set. Generating a random one for this container start."
  echo "Set DJANGO_SECRET_KEY in the environment to keep login sessions valid across restarts."
  export DJANGO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
fi

echo "Checking if FIELD_ENCRYPTION_KEY variable is set..."
if [ -z "${FIELD_ENCRYPTION_KEY}" ]; then
  echo "############################################################"
  echo "# WARNING: FIELD_ENCRYPTION_KEY is not set.                #"
  echo "# Generating a temporary key for this container start.     #"
  echo "# Stored connection passwords are encrypted with this key, #"
  echo "# so a different key on the next start makes them          #"
  echo "# UNREADABLE. For any real deployment generate one and set #"
  echo "# it in the environment to keep it stable across restarts: #"
  echo "#   ./manage.py generate_encryption_key                    #"
  echo "############################################################"
  # Generated with Fernet directly (not via manage.py) so this does not load
  # Django settings and trip the insecure-default guard before the key is set.
  export FIELD_ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
fi

# wait shortly and then run db migrations (retry on error)
sleep 3
while ! python ./manage.py migrate 2>&1; do
  echo "Waiting on DB..."
  sleep 3
done

# create superuser silently
if [ -z ${SUPERUSER_NAME+x} ]; then
  SUPERUSER_NAME='admin'
fi
if [ -z ${SUPERUSER_EMAIL+x} ]; then
  SUPERUSER_EMAIL='admin@example.com'
fi
if [ -z ${SUPERUSER_PASSWORD+x} ]; then
    SUPERUSER_PASSWORD='admin'
fi

echo "Username: ${SUPERUSER_NAME}, E-Mail: ${SUPERUSER_EMAIL}"

python ./manage.py shell --interface python << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='${SUPERUSER_NAME}'):
    u=User.objects.create_superuser('${SUPERUSER_NAME}', '${SUPERUSER_EMAIL}', '${SUPERUSER_PASSWORD}')
END

# copy static files
python ./manage.py collectstatic --no-input

# init default groups
python ./manage.py initgroups
python ./manage.py initguacd


# Set CACHE_URL to use memcached via sock file
export CACHE_URL=memcache:///tmp/memcached.sock

# Nginx
# if certificates doesn't exist create a self signed certificate
echo " "
echo "Checking that SSL certificate and key files exist..."

[ ! -f /ssl/cert.key ] && \
[ ! -f /ssl/cert.crt ] && \
echo "/ssl/cert.crt and /ssl/cert.key not provided" && \
echo "Creating self signed certificate:" && \
mkdir -p /ssl && \
openssl req -x509 -nodes -days 3650 -subj "/CN=guacozy" -addext "subjectAltName=DNS:guacozy" -newkey rsa:4096 -keyout /ssl/cert.key -out /ssl/cert.crt;


echo "Initialisation is done."

# launch whatever is passed by docker
# (i.e. the RUN instruction in the Dockerfile)
exec ${@}