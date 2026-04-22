from aiogram import Router

from app.bot.handlers.announcements import router as announcements_router
from app.bot.handlers.buy import router as buy_router
from app.bot.handlers.calculate import router as calculate_router
from app.bot.handlers.crm import router as crm_router
from app.bot.handlers.inline import router as inline_router
from app.bot.handlers.start import router as start_router
from app.bot.handlers.stats import router as stats_router
from app.bot.handlers.unknown import router as unknown_router

router = Router()
router.include_router(start_router)
router.include_router(stats_router)
router.include_router(buy_router)
router.include_router(announcements_router)
router.include_router(crm_router)
router.include_router(calculate_router)
router.include_router(inline_router)
router.include_router(unknown_router)

__all__ = ["router"]