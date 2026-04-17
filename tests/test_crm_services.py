from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from repositories.database import Database
from repositories.lead_repository import LeadRepository
from repositories.reminder_repository import ReminderRepository
from services.lead_service import ForwardedLeadDraft, LeadService
from services.reminder_service import ReminderService


def build_services(base_path: Path):
    database = Database(str(base_path / "crm.sqlite3"))
    database.initialize()
    lead_repository = LeadRepository(database)
    reminder_repository = ReminderRepository(database)
    lead_service = LeadService(lead_repository, reminder_repository)
    reminder_service = ReminderService(lead_service, "UTC")
    return lead_service, reminder_service


class CRMServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.lead_service, self.reminder_service = build_services(self.base_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_manual_lead_and_reminder(self) -> None:
        lead = self.lead_service.create_manual_lead(
            owner_user_id=1,
            owner_chat_id=101,
            name="Anna Petrova",
            phone="+375291234567",
            lead_type="buyer",
            source="referral",
        )

        scheduled_at = self.reminder_service.schedule_from_preset(
            "1h",
            now=datetime(2026, 4, 16, 9, 0, 0, tzinfo=self.reminder_service.timezone),
        )
        updated_lead, reminder = self.lead_service.set_reminder(1, lead.id, scheduled_at)

        self.assertEqual(lead.name, "Anna Petrova")
        self.assertEqual(lead.status, "new")
        self.assertEqual(lead.phone, "+375291234567")
        self.assertEqual(updated_lead.next_call_at, scheduled_at)
        self.assertTrue(reminder.is_active)

    def test_forwarded_duplicate_detection_uses_telegram_identity(self) -> None:
        self.lead_service.create_forwarded_lead(
            owner_user_id=1,
            owner_chat_id=101,
            draft=ForwardedLeadDraft(
                name="Client One",
                telegram_user_id="555",
                telegram_username="client_one",
                telegram_display_name="Client One",
            ),
        )

        duplicate = self.lead_service.find_duplicate(
            1,
            telegram_user_id="555",
            telegram_username="another_username",
            name="Another Name",
            source="telegram",
        )

        self.assertIsNotNone(duplicate)
        self.assertEqual(duplicate.telegram_user_id, "555")

    def test_mark_called_clears_reminder(self) -> None:
        lead = self.lead_service.create_manual_lead(
            owner_user_id=1,
            owner_chat_id=101,
            name="Ivan",
            phone=None,
            lead_type="seller",
            source="telegram",
        )
        scheduled_at = self.reminder_service.schedule_from_preset(
            "tm10",
            now=datetime(2026, 4, 16, 9, 0, 0, tzinfo=self.reminder_service.timezone),
        )
        self.lead_service.set_reminder(1, lead.id, scheduled_at)

        completed = self.lead_service.mark_called(
            1,
            lead.id,
            datetime(2026, 4, 16, 9, 30, 0, tzinfo=self.reminder_service.timezone),
        )

        self.assertIsNone(completed.next_call_at)
        self.assertIsNotNone(completed.last_contact_at)
        self.assertIsNone(self.lead_service.get_active_reminder(lead.id))


if __name__ == "__main__":
    unittest.main()
