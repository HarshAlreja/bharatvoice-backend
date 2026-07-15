"""Platform-wide config (singleton row). No shared WhatsApp token anymore --
only BharatVoice's own Meta Developer App id/secret, used for OAuth exchange."""
from flask import Blueprint, request
from app.extensions import db
from app.models.platform_settings import PlatformSettings
from app.middleware.admin_guard import super_admin_required
from app.utils.responses import success


def _get_or_create_settings():
    settings = PlatformSettings.query.get(1)
    if not settings:
        settings = PlatformSettings(id=1)
        db.session.add(settings)
        db.session.commit()
    return settings


admin_settings_bp = Blueprint("admin_settings", __name__)


@admin_settings_bp.route("/settings/fetch", methods=["GET"])
@super_admin_required
def fetch_settings():
    s = _get_or_create_settings()
    return success({
        "llm_provider": s.llm_provider,
        "token_rate_limit": s.token_rate_limit,
        "stt_model": s.stt_model,
        "webhook_token": s.meta_webhook_verify_token,
        "meta_app_id": s.meta_app_id,
        "meta_api_version": s.meta_api_version,
        "meta_configuration_id": s.meta_configuration_id,
        "maintenance_mode": s.maintenance_mode,
    })


@admin_settings_bp.route("/settings/update", methods=["PUT"])
@super_admin_required
def update_settings():
    body = request.get_json(silent=True) or {}
    s = _get_or_create_settings()

    s.llm_provider = body.get("llm_provider", s.llm_provider)
    s.token_rate_limit = body.get("token_rate_limit", s.token_rate_limit)
    s.stt_model = body.get("stt_model", s.stt_model)
    s.meta_webhook_verify_token = body.get("webhook_token", s.meta_webhook_verify_token)
    s.meta_app_id = body.get("meta_app_id", s.meta_app_id)
    s.meta_api_version = body.get("meta_api_version", s.meta_api_version)
    s.meta_configuration_id = body.get("meta_configuration_id", s.meta_configuration_id)
    s.maintenance_mode = body.get("maintenance_mode", s.maintenance_mode)

    db.session.commit()
    return success(message="Settings saved")