from datetime import datetime

from repositories.database import Database
from repositories.lead_repository import LeadRepository
from repositories.reminder_repository import ReminderRepository
from services.lead_service import ForwardedLeadDraft, LeadService
from services.reminder_service import ReminderService


def build_services(tmp_path):
    database = Database(str(tmp_path / "crm.sqlite3"))
    database.initialize()
    lead_repository = LeadRepository(database)
    reminder_repository = ReminderRepository(database)
    lead_service = LeadService(lead_repository, reminder_repository)
    reminder_service = ReminderService(lead_service, "UTC")
    return lead_service, reminder_service


def test_create_manual_lead_and_reminder(tmp_path):
    lead_service, reminder_service = build_services(tmp_path)

    lead = lead_service.create_manual_lead(
        owner_user_id=1,
        owner_chat_id=101,
        name="Anna Petrova",
        phone="+375291234567",
        lead_type="buyer",
        source="referral",
    )

    scheduled_at = reminder_service.schedule_from_preset("1h", now=datetime(2026, 4, 16, 9, 0, 0, tzinfo=reminder_service.timezone))
    updated_lead, reminder = lead_service.set_reminder(1, lead.id, scheduled_at)

    assert lead.name == "Anna Petrova"
    assert lead.status == "new"
    assert lead.phone == "+375291234567"
    assert updated_lead.next_call_at == scheduled_at
    assert reminder.is_active is True


def test_forwarded_duplicate_detection_uses_telegram_identity(tmp_path):
    lead_service, _ = build_services(tmp_path)

    lead_service.create_forwarded_lead(
        owner_user_id=1,
        owner_chat_id=101,
        draft=ForwardedLeadDraft(
            name="Client One",
            telegram_user_id="555",
            telegram_username="client_one",
            telegram_display_name="Client One",
        ),
    )

    duplicate = lead_service.find_duplicate(
        1,
        telegram_user_id="555",
        telegram_username="another_username",
        name="Another Name",
        source="telegram",
    )

    assert duplicate is not None
    assert duplicate.telegram_user_id == "555"


def test_mark_called_clears_reminder(tmp_path):
    lead_service, reminder_service = build_services(tmp_path)

    lead = lead_service.create_manual_lead(
        owner_user_id=1,
        owner_chat_id=101,
        name="Ivan",
        phone=None,
        lead_type="seller",
        source="telegram",
    )
    scheduled_at = reminder_service.schedule_from_preset("tm10", now=datetime(2026, 4, 16, 9, 0, 0, tzinfo=reminder_service.timezone))
    lead_service.set_reminder(1, lead.id, scheduled_at)

    completed = lead_service.mark_called(1, lead.id, datetime(2026, 4, 16, 9, 30, 0, tzinfo=reminder_service.timezone))

    assert completed.next_call_at is None
    assert completed.last_contact_at is not None
    assert lead_service.get_active_reminder(lead.id) is None
