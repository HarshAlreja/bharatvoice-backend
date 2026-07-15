"""App factory. Registers extensions and all blueprints."""
from flask import Flask
from app.config import get_config
from app.extensions import db, migrate, jwt, cors


def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=False,
    )

    # Request logging -- populates api_request_logs, used by admin/analytics.py
    # and the admin dashboard's total_api_calls / avg_response_time_ms metrics.
    from app.middleware.request_logger import start_timer, log_request
    app.before_request(start_timer)
    app.after_request(log_request)

    with app.app_context():
        from app import models  # noqa: F401  registers all models for migrations

    # ---- Blueprints ----
    from app.routes.auth.client_auth import client_auth_bp
    from app.routes.auth.admin_auth import admin_auth_bp

    from app.routes.admin.dashboard import admin_dashboard_bp
    from app.routes.admin.businesses import admin_businesses_bp
    from app.routes.admin.users import admin_users_bp
    from app.routes.admin.whatsapp_numbers import admin_whatsapp_bp
    from app.routes.admin.documents import admin_documents_bp
    from app.routes.admin.conversations import admin_conversations_bp
    from app.routes.admin.analytics import admin_analytics_bp
    from app.routes.admin.revenue import admin_revenue_bp
    from app.routes.admin.settings import admin_settings_bp
    from app.routes.admin.support import admin_support_bp
    from app.routes.admin.plans import admin_plans_bp
    from app.routes.admin.subscriptions import admin_subscriptions_bp
    from app.routes.admin.invoices import admin_invoices_bp

    from app.routes.client.dashboard import client_dashboard_bp
    from app.routes.client.knowledge_base import client_kb_bp
    from app.routes.client.conversations import client_conversations_bp
    from app.routes.client.whatsapp import client_whatsapp_bp
    from app.routes.client.analytics import client_analytics_bp
    from app.routes.client.settings import client_settings_bp
    from app.routes.client.billing import client_billing_bp

    from app.routes.webhook.whatsapp_webhook import webhook_bp
    from app.routes.public.contact import contact_bp

    app.register_blueprint(client_auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_auth_bp, url_prefix="/api/auth")

    app.register_blueprint(admin_dashboard_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_businesses_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_users_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_whatsapp_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_documents_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_conversations_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_analytics_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_revenue_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_settings_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_support_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_plans_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_subscriptions_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_invoices_bp, url_prefix="/api/admin")

    app.register_blueprint(client_dashboard_bp, url_prefix="/api")
    app.register_blueprint(client_kb_bp, url_prefix="/api")
    app.register_blueprint(client_conversations_bp, url_prefix="/api")
    app.register_blueprint(client_whatsapp_bp, url_prefix="/api")
    app.register_blueprint(client_analytics_bp, url_prefix="/api")
    app.register_blueprint(client_settings_bp, url_prefix="/api")
    app.register_blueprint(client_billing_bp, url_prefix="/api")

    app.register_blueprint(webhook_bp, url_prefix="/api/webhook")
    app.register_blueprint(contact_bp, url_prefix="/api")

    return app