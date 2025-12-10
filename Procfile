web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3
worker: celery -A config worker --log-level=info
beat: celery -A config beat --log-level=info
