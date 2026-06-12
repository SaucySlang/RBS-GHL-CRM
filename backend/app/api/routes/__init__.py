from fastapi import APIRouter
from app.api.routes import (
    contacts, messages, conversations, webhooks, sub_accounts, deals,
    forms, public_forms, automations, ai_receptionist, branding,
)

router = APIRouter()

# Agency-level (unscoped) routes
router.include_router(sub_accounts.router, prefix="/sub-accounts", tags=["Sub-Accounts"])

# Tenant-scoped routes (require X-SubAccount-ID header)
router.include_router(contacts.router, prefix="/contacts", tags=["Contacts"])
router.include_router(messages.router, prefix="/messages", tags=["Messages"])
router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
router.include_router(deals.router, prefix="/deals", tags=["Deals"])
router.include_router(forms.router, prefix="/forms", tags=["Forms"])
router.include_router(automations.router, prefix="/automations", tags=["Automations"])
router.include_router(ai_receptionist.router, prefix="/receptionist", tags=["AI Receptionist"])
router.include_router(branding.router, prefix="/branding", tags=["Branding"])

# Public, unauthenticated lead capture (embedded on external sites)
router.include_router(public_forms.router, prefix="/public", tags=["Public"])
router.include_router(ai_receptionist.public_router, prefix="/public", tags=["Public"])
router.include_router(branding.public_router, prefix="/public", tags=["Public"])

# Inbound provider webhooks (tenant resolved from payload)
router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])

@router.get("/")
async def api_root():
    return {"message": "Omni-Channel CRM API", "version": "1.0"}
