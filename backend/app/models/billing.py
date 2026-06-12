import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Wallet(Base):
    """Usage-based billing wallet (agency level)."""
    __tablename__ = "wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id"), unique=True, nullable=False)

    balance = Column(Numeric(10, 4), default=0)  # Current balance in dollars

    # Auto-recharge settings
    auto_recharge = Column(Boolean, default=True)
    recharge_threshold = Column(Numeric(10, 2), default=10.00)
    recharge_amount = Column(Numeric(10, 2), default=50.00)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WalletTransaction(Base):
    """Wallet transaction history."""
    __tablename__ = "wallet_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)

    type = Column(String(20), nullable=False)  # credit, debit, refund
    amount = Column(Numeric(10, 4), nullable=False)

    # What was this for
    resource_type = Column(String(50))  # sms, email, voice, ai
    resource_id = Column(String(255))  # Twilio SID, etc.
    description = Column(Text)

    # Balance after transaction
    balance_after = Column(Numeric(10, 4))

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_wallet_transactions_wallet", "wallet_id", "created_at"),
    )

class Subscription(Base):
    """Stripe subscription tracking (agency level)."""
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id"), nullable=False)

    stripe_subscription_id = Column(String(100), unique=True)
    stripe_price_id = Column(String(100))

    tier = Column(String(50), nullable=False)  # starter, professional, agency, enterprise
    status = Column(String(20), default="active")  # active, past_due, canceled, paused

    # Limits
    contact_limit = Column(Integer, default=5000)
    user_limit = Column(Integer, default=3)

    # Billing period
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)

    # Dunning
    failed_payment_count = Column(Integer, default=0)
    last_payment_attempt = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    canceled_at = Column(DateTime)
