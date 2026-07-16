"""initial migration

Revision ID: 65f752411347
Revises: 
Create Date: 2026-07-07 16:52:17.473991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '65f752411347'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Base / Independent Tables create karenge pehle
    op.create_table('admins',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=30), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    
    op.create_table('contact_submissions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('subject', sa.String(length=255), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('otp_codes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('code', sa.String(length=6), nullable=False),
    sa.Column('purpose', sa.String(length=30), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('verified_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('otp_codes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_otp_codes_email'), ['email'], unique=False)

    op.create_table('plans',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('monthly_price', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('yearly_price', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('token_limit', sa.Integer(), nullable=True),
    sa.Column('whatsapp_number_limit', sa.Integer(), nullable=True),
    sa.Column('features_json', sa.JSON(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('platform_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('llm_provider', sa.String(length=50), nullable=True),
    sa.Column('token_rate_limit', sa.Integer(), nullable=True),
    sa.Column('stt_model', sa.String(length=50), nullable=True),
    sa.Column('meta_app_id', sa.String(length=64), nullable=True),
    sa.Column('meta_app_secret_encrypted', sa.Text(), nullable=True),
    sa.Column('meta_api_version', sa.String(length=20), nullable=True),
    sa.Column('meta_configuration_id', sa.String(length=64), nullable=True),
    sa.Column('meta_webhook_verify_token', sa.String(length=255), nullable=True),
    sa.Column('maintenance_mode', sa.Boolean(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

    # 2. Users table banayenge bina kisi business foreign key ke constraint ke
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('business_id', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )

    # 3. Ab users table ban chuki hai, toh businesses table bina crash ke ban jayegi
    op.create_table('businesses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('business_name', sa.String(length=200), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('industry', sa.String(length=100), nullable=True),
    sa.Column('email_verified', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # 4. Ab users ki remaining circular dependency wali foreign key link karenge
    op.create_foreign_key('fk_users_business_id_businesses', 'users', 'businesses', ['business_id'], ['id'])

    # 5. Baki ki saari dependent tables as usual create ho jayengi
    op.create_table('api_request_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('endpoint', sa.String(length=255), nullable=True),
    sa.Column('method', sa.String(length=10), nullable=True),
    sa.Column('status_code', sa.Integer(), nullable=True),
    sa.Column('response_time_ms', sa.Integer(), nullable=True),
    sa.Column('business_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('conversations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('business_id', sa.Integer(), nullable=False),
    sa.Column('customer_phone', sa.String(length=20), nullable=False),
    sa.Column('customer_name', sa.String(length=120), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('ended_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('business_id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('file_path', sa.String(length=500), nullable=True),
    sa.Column('file_type', sa.String(length=20), nullable=True),
    sa.Column('file_size', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('chunk_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('subscriptions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('business_id', sa.Integer(), nullable=False),
    sa.Column('plan_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('billing_cycle', sa.String(length=10), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(), nullable=True),
    sa.Column('next_billing_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
    sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('support_tickets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('business_id', sa.Integer(), nullable=False),
    sa.Column('subject', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('priority', sa.String(length=10), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('resolved_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('whatsapp_numbers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('business_id', sa.Integer(), nullable=False),
    sa.Column('phone_number_id', sa.String(length=64), nullable=True),
    sa.Column('waba_id', sa.String(length=64), nullable=True),
    sa.Column('meta_business_id', sa.String(length=64), nullable=True),
    sa.Column('display_number', sa.String(length=20), nullable=True),
    sa.Column('access_token_encrypted', sa.Text(), nullable=True),
    sa.Column('token_expires_at', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('verification_status', sa.String(length=20), nullable=True),
    sa.Column('daily_message_limit', sa.Integer(), nullable=True),
    sa.Column('connected_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('phone_number_id')
    )
    
    op.create_table('document_chunks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('business_id', sa.Integer(), nullable=False),
    sa.Column('chunk_text', sa.Text(), nullable=False),
    sa.Column('chunk_index', sa.Integer(), nullable=True),
    sa.Column('faiss_vector_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('invoices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('business_id', sa.Integer(), nullable=False),
    sa.Column('subscription_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('invoice_date', sa.DateTime(), nullable=True),
    sa.Column('paid_at', sa.DateTime(), nullable=True),
    sa.Column('pdf_url', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
    sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=False),
    sa.Column('sender', sa.String(length=20), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('tokens_used', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('ticket_replies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ticket_id', sa.Integer(), nullable=False),
    sa.Column('sender', sa.String(length=20), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('token_usage_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('business_id', sa.Integer(), nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=True),
    sa.Column('model_used', sa.String(length=50), nullable=True),
    sa.Column('tokens_used', sa.Integer(), nullable=True),
    sa.Column('cost_estimate', sa.Numeric(precision=10, scale=4), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('token_usage_logs')
    op.drop_table('ticket_replies')
    op.drop_table('messages')
    op.drop_table('invoices')
    op.drop_table('document_chunks')
    op.drop_table('whatsapp_numbers')
    op.drop_table('support_tickets')
    op.drop_table('subscriptions')
    op.drop_table('documents')
    op.drop_table('conversations')
    op.drop_table('api_request_logs')
    
    # User se dynamic foreign key drop karenge pehle dropdown logic follow karne ke liye
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_business_id_businesses', type_='foreignkey')
        
    op.drop_table('users')
    op.drop_table('platform_settings')
    op.drop_table('plans')
    with op.batch_alter_table('otp_codes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_otp_codes_email'))

    op.drop_table('otp_codes')
    op.drop_table('contact_submissions')
    op.drop_table('businesses')
    op.drop_table('admins')