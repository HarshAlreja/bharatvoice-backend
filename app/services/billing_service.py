"""MRR/ARR/ARPU calculations + invoice generation for subscription_renewal task."""
from sqlalchemy import func
from app.extensions import db
from app.models.subscription import Subscription


def revenue_metrics():
    active_subs = Subscription.query.filter_by(status="active").all()
    mrr = sum(
        float(s.amount) if s.billing_cycle == "monthly" else float(s.amount) / 12
        for s in active_subs
    )
    arr = mrr * 12
    active_count = len(active_subs)
    arpu = mrr / active_count if active_count else 0

    return {
        "mrr": round(mrr, 2),
        "arr": round(arr, 2),
        "active_subscriptions": active_count,
        "arpu": round(arpu, 2),
    }
