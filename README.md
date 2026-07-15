# BharatVoice Backend

Flask + SQLAlchemy multi-tenant backend. Per-client Meta WhatsApp Business Account model:
every business connects their OWN WABA via Meta Embedded Signup. BharatVoice never holds
a shared WhatsApp token -- only its own Meta Developer App credentials (META_APP_ID /
META_APP_SECRET), used purely to exchange each client's Embedded Signup code for their
own long-lived business token.

## Structure
- app/routes/admin   -> super-admin panel, cross-tenant, no business_id filter
- app/routes/client  -> client dashboard, always scoped by business_id (tenant_guard)
- app/routes/webhook -> public Meta webhook, ONE endpoint for ALL tenants, routes by phone_number_id
- app/vectorstore    -> one FAISS index per business_id
- app/services/meta_oauth_service.py -> Embedded Signup code exchange, per client

## Setup
1. cp .env.example .env, fill in values
2. pip install -r requirements.txt
3. flask db upgrade
4. python run.py
"# bharatvoice-backend" 
