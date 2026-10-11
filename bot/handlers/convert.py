import logging
from pathlib import Path
from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import img2pdf

router = Router()
logger = logging.getLogger(__name__)

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# Foydalanuvchi rasmlarini saqlash
user_images = {}  # {user_id: [path1, path2, ...]}

class ConvertStates(StatesGroup):
    waiting_for_filename = State()

def get_action_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Davom etish", callback_data="continue_images")
    builder.button(text="Tayyor (PDF qilish)", callback_data="make_pdf")
    builder.adjust(1)
    return builder.as_markup()

def get_name_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Ha", callback_data="change_name_yes")
    builder.button(text="Yo‘q", callback_data="change_name_no")
    builder.adjust(2)
    return builder.as_markup()

@router.message(F.photo | F.document)
async def collect_images(message: Message, bot: Bot):
    user_id = message.from_user.id

    if message.photo:
        file_id = message.photo[-1].file_id
        file_name = f"{user_id}_{file_id}.jpg"
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("image/"):
        file_id = message.document.file_id
        file_name = message.document.file_name or f"{user_id}_{file_id}.jpg"
    else:
        await message.answer("Faqat rasm yuboring.")
        return

    image_path = TEMP_DIR / file_name

    try:
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, destination=image_path)

        if user_id not in user_images:
            user_images[user_id] = []
        user_images[user_id].append(image_path)

        count = len(user_images[user_id])

        await message.answer(
            f"Rasm qabul qilindi ({count} ta).\n\n"
            f"Davom etasizmi yoki PDF tayyorlaymizmi?",
            reply_markup=get_action_keyboard()
        )

    except Exception as e:
        logger.error(e)
        await message.answer("Rasmni yuklab olishda xatolik yuz berdi.")

@router.callback_query(F.data == "continue_images")
async def continue_collecting(callback: CallbackQuery):
    await callback.message.edit_text(
        "Yana rasm yuboring.\n"
        "Tugagach «Tayyor (PDF qilish)» tugmasini bosing."
    )
    await callback.answer()

@router.callback_query(F.data == "make_pdf")
async def ask_change_name(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    images = user_images.get(user_id, [])

    if not images:
        await callback.message.edit_text("Siz hali rasm yubormadingiz. Avval rasm tashlang.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "PDF nomini o‘zgartirasizmi?",
        reply_markup=get_name_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "change_name_yes")
async def ask_filename(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Yangi PDF nomini yozing (masalan: mening_hujjatim):")
    await state.set_state(ConvertStates.waiting_for_filename)
    await callback.answer()

@router.callback_query(F.data == "change_name_no")
async def convert_default_name(callback: CallbackQuery, bot: Bot):
    await callback.message.edit_text("PDF tayyorlanmoqda... ⏳")
    await callback.answer()
    await create_pdf(callback.from_user.id, bot, callback.message, filename=None)

@router.message(ConvertStates.waiting_for_filename)
async def get_custom_name(message: Message, state: FSMContext, bot: Bot):
    custom_name = message.text.strip()

    if not custom_name:
        await message.answer("Nom bo‘sh bo‘lishi mumkin emas. Qayta yozing:")
        return

    if not custom_name.lower().endswith(".pdf"):
        custom_name += ".pdf"

    await message.answer("PDF tayyorlanmoqda... ⏳")
    await state.clear()
    await create_pdf(message.from_user.id, bot, message, filename=custom_name)

async def create_pdf(user_id: int, bot: Bot, message: Message, filename: str | None = None):
    images = user_images.get(user_id, [])
    if not images:
        await message.answer("Rasmlar topilmadi.")
        return

    if filename is None:
        filename = f"File_{user_id}.pdf"

    pdf_path = TEMP_DIR / filename

    try:
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert([str(img) for img in images]))

        pdf_file = FSInputFile(pdf_path, filename=filename)
        await message.answer_document(
            pdf_file,
            caption=f"PDF tayyor ✅\nJami {len(images)} ta rasm"
        )

    except Exception as e:
        logger.error(e)
        await message.answer("PDF yaratishda xatolik yuz berdi.")
    finally:
        for img in images:
            img.unlink(missing_ok=True)
        pdf_path.unlink(missing_ok=True)
        user_images.pop(user_id, None)

@router.message(F.text)
async def any_text(message: Message):
    user_id = message.from_user.id
    if user_id in user_images and user_images[user_id]:
        await message.answer(
            f"Sizda hozir {len(user_images[user_id])} ta rasm bor.\n"
            f"Yana rasm yuboring yoki tugmani bosing:",
            reply_markup=get_action_keyboard()
        )
    else:
        await message.answer("Rasm yuboring, men uni PDF qilib beraman.")