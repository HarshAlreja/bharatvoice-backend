"""Cross-tenant invoice oversight."""
from flask import Blueprint, request
from app.models.invoice import Invoice
from app.middleware.admin_guard import admin_required
from app.utils.responses import success

admin_invoices_bp = Blueprint("admin_invoices", __name__)


@admin_invoices_bp.route("/invoices", methods=["GET"])
@admin_required
def list_invoices():
    business_id = request.args.get("business_id")
    query = Invoice.query
    if business_id:
        query = query.filter_by(business_id=business_id)

    invoices = query.order_by(Invoice.invoice_date.desc()).limit(200).all()
    return success({"invoices": [
        {"id": i.id, "business_id": i.business_id, "amount": float(i.amount or 0), "status": i.status}
        for i in invoices
    ]})
