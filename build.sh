#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Crear superusuario automáticamente sin consola
python manage.py createsuperuser --noinput || true