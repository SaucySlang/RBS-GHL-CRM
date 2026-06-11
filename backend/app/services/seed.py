"""First-run seeding: a default agency with one sub-account per business."""
import logging
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.tenancy import Agency, SubAccount, IndustryType

logger = logging.getLogger(__name__)

DEFAULT_SUB_ACCOUNTS = [
    ("Real Estate", IndustryType.REAL_ESTATE),
    ("Music Production Studio", IndustryType.MUSIC_PRODUCTION),
    ("E-commerce Brands", IndustryType.ECOMMERCE),
    ("AI Consulting", IndustryType.AI_CONSULTING),
]


async def seed_default_tenants() -> None:
    """Create the default agency + sub-accounts if the database is empty."""
    async with AsyncSessionLocal() as session:
        count = (await session.execute(select(func.count(Agency.id)))).scalar()
        if count:
            return

        agency = Agency(name="My Agency", slug="my-agency")
        session.add(agency)
        await session.flush()

        from app.services.workflow_engine import create_speed_to_lead_workflow

        for name, industry in DEFAULT_SUB_ACCOUNTS:
            sub_account = SubAccount(
                agency_id=agency.id, name=name, industry_type=industry
            )
            session.add(sub_account)
            await session.flush()
            # Every workspace starts with the speed-to-lead chain ready to go
            await create_speed_to_lead_workflow(session, sub_account.id)

        await session.commit()
        logger.info("Seeded default agency with %d sub-accounts", len(DEFAULT_SUB_ACCOUNTS))
