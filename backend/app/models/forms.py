import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.tenancy import TenantMixin


# The six standard capture fields, in default order. `sub_account_id` is the
# hidden workspace-context field embedded in every rendered form.
DEFAULT_FORM_FIELDS = [
    {"key": "first_name", "label": "First Name", "type": "text", "required": True, "enabled": True},
    {"key": "last_name", "label": "Last Name", "type": "text", "required": False, "enabled": True},
    {"key": "email", "label": "Email", "type": "email", "required": True, "enabled": True},
    {"key": "phone", "label": "Phone", "type": "tel", "required": False, "enabled": True},
    {"key": "message", "label": "Message", "type": "textarea", "required": False, "enabled": True},
    {"key": "sub_account_id", "label": "Sub-Account ID", "type": "hidden", "required": True, "enabled": True},
]

DEFAULT_FORM_CONFIG = {
    "submit_label": "Send",
    "success_message": "Thanks! We'll be in touch shortly.",
    "theme": {"background": "#09090e", "accent": "#8b5cf6", "text": "#e5e7eb"},
}


class Form(TenantMixin, Base):
    """A lead-capture form built in the visual builder and embedded via iframe."""
    __tablename__ = "forms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(255), nullable=False)
    fields_json = Column(JSONB, nullable=False, default=lambda: list(DEFAULT_FORM_FIELDS))
    configurations_json = Column(JSONB, nullable=False, default=lambda: dict(DEFAULT_FORM_CONFIG))
    is_published = Column(Boolean, default=False, nullable=False)

    submission_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
