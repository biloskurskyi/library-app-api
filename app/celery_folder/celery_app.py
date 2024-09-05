import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Create and configure a Celery application instance.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

app = Celery('app')
app.config_from_object('django.conf:settings')
app.conf.broker_url = settings.CELERY_BROKER_URL
app.autodiscover_tasks()

# Daily at midnight.
app.conf.beat_schedule = {
    'run-periodic-task-every-minute': {
        'task': 'borrow.tasks.send_overdue_notifications',
        'schedule': crontab(hour='0', minute='0'),  # crontab(minute='*/1')
    },
}
