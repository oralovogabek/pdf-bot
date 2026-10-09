from aiogram import Router

from .start import router as start_router
from .convert import router as convert_router

def get_handlers_router() -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(convert_router)
    return router