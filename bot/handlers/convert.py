import logging
from pathlib import Path

from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile
import img2pdf

router = Router()
logger = logging.getLogger(__name__)

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

@router.message(F.photo | F.document)
async def convert_image_to_pdf(message: Message, bot: Bot):
    # Photo yoki image document ekanligini tekshiramiz
    if message.photo:
        file_id = message.photo[-1].file_id
        file_name = f"{file_id}.jpg"
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("image/"):
        file_id = message.document.file_id
        file_name = message.document.file_name or f"{file_id}.jpg"
    else:
        await message.answer("Faqat rasm yuboring (photo yoki image document).")
        return

    image_path = TEMP_DIR / file_name
    pdf_path = TEMP_DIR / f"{file_id}.pdf"

    try:
        # Rasmni yuklab olamiz
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, destination=image_path)

        # PDF yasaymiz
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(str(image_path)))

        # PDFni yuboramiz
        pdf_file = FSInputFile(pdf_path, filename="converted.pdf")
        await message.answer_document(pdf_file, caption="PDF tayyor ✅")

    except Exception as e:
        logger.error(f"Xato: {e}")
        await message.answer("Xatolik yuz berdi. Qayta urinib ko‘ring.")
    finally:
        # Tozalash
        image_path.unlink(missing_ok=True)
        pdf_path.unlink(missing_ok=True)