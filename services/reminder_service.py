from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from models.lead import Lead
from models.reminder import Reminder
from services.lead_service import LeadService


class ReminderService:
    def __init__(self, lead_service: LeadService, timezone_name: str):
        self.lead_service = lead_service
        self.timezone = ZoneInfo(timezone_name)

    def now(self) -> datetime:
        return datetime.now(self.timezone)

    def schedule_from_preset(self, preset: str, *, now: datetime | None = None) -> datetime | None:
        current_time = now or self.now()

        if preset == "none":
            return None
        if preset == "1h":
            return current_time + timedelta(hours=1)
        if preset == "t18":
            target_time = current_time.replace(hour=18, minute=0, second=0, microsecond=0)
            return target_time if target_time > current_time else target_time + timedelta(days=1)
        if preset == "tm10":
            tomorrow = current_time + timedelta(days=1)
            return tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        if preset == "3d":
            target_day = current_time + timedelta(days=3)
            return target_day.replace(hour=10, minute=0, second=0, microsecond=0)
        if preset == "1w":
            target_day = current_time + timedelta(days=7)
            return target_day.replace(hour=10, minute=0, second=0, microsecond=0)

        raise ValueError(f"Unknown reminder preset: {preset}")

    def format_datetime(self, value: datetime | None) -> str:
        if value is None:
            return "-"

        localized = value.astimezone(self.timezone)
        return localized.strftime("%Y-%m-%d %H:%M")

    async def load_existing_jobs(self, application: Application) -> None:
        for lead, reminder in self.lead_service.list_active_reminders():
            self.schedule_job(application, lead, reminder)

    def schedule_job(self, application: Application, lead: Lead, reminder: Reminder) -> None:
        if application.job_queue is None:
            return

        self.cancel_job(application, lead.id)

        run_at = reminder.scheduled_at.astimezone(self.timezone)
        if run_at <= self.now():
            run_at = self.now()

        application.job_queue.run_once(
            self.send_reminder,
            when=run_at,
            name=self._job_name(lead.id),
            data={"lead_id": lead.id, "reminder_id": reminder.id},
        )

    def cancel_job(self, application: Application, lead_id: int) -> None:
        if application.job_queue is None:
            return

        for job in application.job_queue.get_jobs_by_name(self._job_name(lead_id)):
            job.schedule_removal()

    async def send_reminder(self, context) -> None:
        from telegram import InlineKeyboardMarkup

        from keyboards.crm import reminder_notification_keyboard

        job_data = context.job.data
        lead = self.lead_service.get_lead_by_id(job_data["lead_id"])
        reminder = self.lead_service.get_active_reminder(job_data["lead_id"])

        if lead is None or reminder is None or lead.is_archived:
            return

        keyboard: InlineKeyboardMarkup = reminder_notification_keyboard(lead.id)
        text = (
            f"Call reminder\n"
            f"{lead.name}\n"
            f"Phone: {lead.phone or '-'}\n"
            f"Status: {lead.status_label}\n"
            f"Scheduled: {self.format_datetime(reminder.scheduled_at)}"
        )

        await context.bot.send_message(
            chat_id=lead.owner_chat_id,
            text=text,
            reply_markup=keyboard,
        )
        self.lead_service.mark_reminder_sent(job_data["reminder_id"])

    @staticmethod
    def _job_name(lead_id: int) -> str:
        return f"lead-reminder-{lead_id}"
