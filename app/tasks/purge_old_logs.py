"""Cron job: delete api_request_logs older than 90 days. Run daily.
Schedule via Railway cron, APScheduler, or a simple external scheduler hitting
a protected endpoint -- wire whichever fits your deploy setup."""
from datetime import datetime, timedelta
from app.extensions import db
from app.models.api_request_log import ApiRequestLog


def run():
    cutoff = datetime.utcnow() - timedelta(days=90)
    deleted = ApiRequestLog.query.filter(ApiRequestLog.created_at < cutoff).delete()
    db.session.commit()
    print(f"Purged {deleted} old api_request_logs rows")
