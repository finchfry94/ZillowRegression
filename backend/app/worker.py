from celery import Celery

celery_app = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=['app.tasks']
)

celery_app.conf.task_routes = {"app.tasks.*": {"queue": "celery"}}

# Enable Celery events
celery_app.conf.worker_send_task_events = True
celery_app.conf.task_send_sent_event = True

# Add the new setting for broker connection retries on startup
celery_app.conf.broker_connection_retry_on_startup = True
celery_app.conf.broker_connection_max_retries = 100  # Retry up to 100 times
celery_app.conf.broker_connection_retry_backoff = 2  # Wait 2 seconds between retries
celery_app.conf.broker_connection_retry_backoff_max = 30 # wait a maximum of 30 seconds between retries
