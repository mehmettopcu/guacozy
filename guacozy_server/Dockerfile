FROM python:3.11-slim-bookworm
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install build dependencies for psycopg2 and python-ldap
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    libpq-dev \
    libldap2-dev \
    libsasl2-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements*.txt /app/

RUN pip install --upgrade pip && \
    pip install  -r requirements-ldap.txt

# Django service
EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

