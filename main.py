import logging

import exceptions
from handlers.calculator import inline_commission, send_calculation
from handlers.crm import CRMHandler
from handlers.start import start
from repositories.database import Database
from repositories.lead_repository import LeadRepository
from repositories.reminder_repository import ReminderRepository
from services.lead_service import LeadService
from services.reminder_service import ReminderService
from settings import ACCESS_TOKEN, CRM_DATABASE_PATH, CRM_TIMEZONE
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
)


def build_services() -> tuple[LeadService, ReminderService]:
    database = Database(CRM_DATABASE_PATH)
    database.initialize()
    lead_repository = LeadRepository(database)
    reminder_repository = ReminderRepository(database)
    lead_service = LeadService(lead_repository, reminder_repository)
    reminder_service = ReminderService(lead_service, CRM_TIMEZONE)
    return lead_service, reminder_service


async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    crm_handler: CRMHandler = context.application.bot_data["crm_handler"]
    if await crm_handler.handle_message(update, context):
        return

    await send_calculation(update, context)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Unknown command. Use /start to open the menu.",
    )


async def on_startup(application: Application) -> None:
    reminder_service: ReminderService = application.bot_data["reminder_service"]
    await reminder_service.load_existing_jobs(application)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error
    if isinstance(error, exceptions.LeadNotFoundError):
        target = getattr(update, "callback_query", None)
        if target is not None:
            await target.answer("Lead not found.", show_alert=True)
            return

        if getattr(update, "effective_chat", None) is not None:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Lead not found.",
            )
        return

    if isinstance(error, ValueError):
        if getattr(update, "effective_chat", None) is not None:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=str(error),
            )
        return

    logging.exception("Unhandled update error", exc_info=error)


def build_application() -> Application:
    lead_service, reminder_service = build_services()
    crm_handler = CRMHandler(lead_service, reminder_service)

    application = ApplicationBuilder().token(ACCESS_TOKEN).post_init(on_startup).build()
    application.bot_data["crm_handler"] = crm_handler
    application.bot_data["reminder_service"] = reminder_service

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(crm_handler.handle_callback))
    application.add_handler(InlineQueryHandler(inline_commission))
    application.add_handler(MessageHandler(filters.FORWARDED, route_message))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), route_message))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    application.add_error_handler(error_handler)
    return application


def main() -> None:
    application = build_application()

    application.run_polling()


if __name__ == "__main__":
    main()
