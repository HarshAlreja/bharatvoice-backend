"""Import all models so Flask-Migrate can detect them."""
from app.models.admin import Admin
from app.models.user import User
from app.models.otp_code import OtpCode
from app.models.business import Business
from app.models.whatsapp_number import WhatsAppNumber
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.token_usage_log import TokenUsageLog
from app.models.api_request_log import ApiRequestLog
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.models.platform_settings import PlatformSettings
from app.models.support_ticket import SupportTicket, TicketReply
from app.models.contact_submission import ContactSubmission
