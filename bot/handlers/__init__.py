from aiogram import Router
from .start import router as start_router
from .user import router as user_router
from .admin import router as admin_router
from .broadcast import router as broadcast_router
from .movie_codes import router as codes_router

def get_main_router() -> Router:
    main_router = Router()
    main_router.include_router(start_router)
    main_router.include_router(user_router)
    main_router.include_router(admin_router)
    main_router.include_router(broadcast_router)
    main_router.include_router(codes_router)
    return main_router
