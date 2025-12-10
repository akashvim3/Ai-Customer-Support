import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('ai_customer_support')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    # Generate daily analytics snapshot every day at midnight
    'generate-daily-snapshot': {
        'task': 'analytics.tasks.generate_daily_snapshot',
        'schedule': crontab(hour=0, minute=0),
    },

    # Update agent performance every hour
    'update-agent-performance': {
        'task': 'analytics.tasks.update_agent_performance',
        'schedule': crontab(minute=0),
    },

    # Update sentiment trends every 6 hours
    'update-sentiment-trends': {
        'task': 'analytics.tasks.update_sentiment_trends',
        'schedule': crontab(hour='*/6', minute=0),
    },

    # Check for alerts every 15 minutes
    'check-for-alerts': {
        'task': 'analytics.tasks.check_for_alerts',
        'schedule': crontab(minute='*/15'),
    },

    # Clean up old data weekly (Sunday at 2 AM)
    'cleanup-old-data': {
        'task': 'config.tasks.cleanup_old_data',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),
    },

    # Train ML models weekly (Sunday at 3 AM)
    'train-ml-models': {
        'task': 'config.tasks.train_ml_models',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),
    },
}

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
