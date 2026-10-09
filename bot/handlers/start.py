from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Salom! 👋\n\n"
        "Menga rasm yuboring — men uni PDF qilib qaytaraman.\n"
        "Photo yoki Document sifatida yuborishingiz mumkin."
    )