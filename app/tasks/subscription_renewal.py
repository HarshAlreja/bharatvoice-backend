"""Cron job: generate invoices for subscriptions due for renewal. Run daily."""
from datetime import datetime
from dateutil.relativedelta import relativedelta
from app.extensions import db
from app.models.subscription import Subscription
from app.models.invoice import Invoice


def run():
    due = Subscription.query.filter(
        Subscription.status == "active",
        Subscription.next_billing_at <= datetime.utcnow(),
    ).all()

    for sub in due:
        db.session.add(Invoice(
            business_id=sub.business_id, subscription_id=sub.id,
            amount=sub.amount, status="pending", invoice_date=datetime.utcnow(),
        ))
        months = 1 if sub.billing_cycle == "monthly" else 12
        sub.next_billing_at = datetime.utcnow() + relativedelta(months=months)

    db.session.commit()
    print(f"Generated {len(due)} invoices")
