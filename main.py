import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")  # /groupid buyrug'i orqali guruhda olinadi

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ---- Statik ma'lumotlar ----
CONTACT_PHONE = "+998(66)229-10-00"
ADDRESS_TEXT = "Самарқанд вилояти, Самарқанд шаҳри, Даҳбед кўчаси 32-уй"
SCHEDULE_IMAGE_PATH = "assets/grafik.jpg"  # shu manzilga rasmni GitHub orqali yuklaysiz


# ---- FSM holatlari (Murojaat jarayoni) ----
class Murojaat(StatesGroup):
    fio = State()
    manzil = State()
    telefon = State()
    matn = State()
    fayl = State()


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Murojaat yuborish", callback_data="murojaat")],
            [InlineKeyboardButton(text="☎️ Bog'lanish", callback_data="boglanish")],
            [
                InlineKeyboardButton(
                    text="📍 Samarqand viloyati Xalq qabulxonasi manzili",
                    callback_data="manzil",
                )
            ],
            [InlineKeyboardButton(text="🗓 Shaxsiy qabul grafigi", callback_data="grafik")],
        ]
    )


def skip_file_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="fayl_skip")]
        ]
    )


# ---- /start ----
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Assalomu alaykum!\n\n"
        "Samarqand viloyati Xalq qabulxonasi mudiri o'rinbosari "
        "Xurshid Ochilovning rasmiy botiga xush kelibsiz.\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=main_menu(),
    )


# ---- Guruh/chat ID ni bilish uchun yordamchi buyruq ----
@dp.message(Command("groupid"))
async def group_id(message: Message):
    await message.answer(f"Chat ID: `{message.chat.id}`", parse_mode="Markdown")


# ---- Bog'lanish ----
@dp.callback_query(F.data == "boglanish")
async def contact_handler(call: CallbackQuery):
    await call.message.answer(f"☎️ Bog'lanish uchun telefon raqami:\n{CONTACT_PHONE}")
    await call.answer()


# ---- Manzil ----
@dp.callback_query(F.data == "manzil")
async def address_handler(call: CallbackQuery):
    await call.message.answer(f"📍 Manzil:\n{ADDRESS_TEXT}")
    await call.answer()


# ---- Shaxsiy qabul grafigi (rasm) ----
@dp.callback_query(F.data == "grafik")
async def schedule_handler(call: CallbackQuery):
    if os.path.exists(SCHEDULE_IMAGE_PATH):
        photo = FSInputFile(SCHEDULE_IMAGE_PATH)
        await call.message.answer_photo(photo, caption="🗓 Shaxsiy qabul grafigi")
    else:
        await call.message.answer("Grafik rasmi hali yuklanmagan.")
    await call.answer()


# ---- Murojaat jarayoni boshlanishi ----
@dp.callback_query(F.data == "murojaat")
async def murojaat_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(Murojaat.fio)
    await call.message.answer("✍️ F.I.Sh. to'liq holda kiriting:")
    await call.answer()


@dp.message(Murojaat.fio)
async def get_fio(message: Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await state.set_state(Murojaat.manzil)
    await message.answer("🏠 Yashash manzilingizni to'liq kiriting:")


@dp.message(Murojaat.manzil)
async def get_manzil(message: Message, state: FSMContext):
    await state.update_data(manzil=message.text)
    await state.set_state(Murojaat.telefon)
    await message.answer("📞 Telefon raqamingizni kiriting (masalan: +998901234567):")


@dp.message(Murojaat.telefon)
async def get_telefon(message: Message, state: FSMContext):
    await state.update_data(telefon=message.text)
    await state.set_state(Murojaat.matn)
    await message.answer("📝 Murojaat matnini yozing:")


@dp.message(Murojaat.matn)
async def get_matn(message: Message, state: FSMContext):
    await state.update_data(matn=message.text)
    await state.set_state(Murojaat.fayl)
    await message.answer(
        "📎 Agar murojaatingizga tegishli foto yoki fayl bo'lsa yuboring.\n"
        "Bo'lmasa, pastdagi tugmani bosing:",
        reply_markup=skip_file_keyboard(),
    )


@dp.callback_query(F.data == "fayl_skip", Murojaat.fayl)
async def skip_file(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await finish_murojaat(call.message, call.from_user, state, file_id=None, file_type=None)


@dp.message(Murojaat.fayl, F.photo)
async def get_photo(message: Message, state: FSMContext):
    await finish_murojaat(
        message, message.from_user, state, file_id=message.photo[-1].file_id, file_type="photo"
    )


@dp.message(Murojaat.fayl, F.document)
async def get_document(message: Message, state: FSMContext):
    await finish_murojaat(
        message, message.from_user, state, file_id=message.document.file_id, file_type="document"
    )


async def finish_murojaat(answer_target: Message, user, state: FSMContext, file_id, file_type):
    data = await state.get_data()

    text = (
        "🆕 <b>Yangi murojaat</b>\n\n"
        f"👤 F.I.Sh: {data.get('fio')}\n"
        f"🏠 Manzil: {data.get('manzil')}\n"
        f"📞 Telefon: {data.get('telefon')}\n"
        f"📝 Matn: {data.get('matn')}\n\n"
        f"🔗 Foydalanuvchi: @{user.username or 'mavjud emas'} (ID: {user.id})"
    )

    if GROUP_CHAT_ID:
        if file_type == "photo":
            await bot.send_photo(GROUP_CHAT_ID, file_id, caption=text, parse_mode="HTML")
        elif file_type == "document":
            await bot.send_document(GROUP_CHAT_ID, file_id, caption=text, parse_mode="HTML")
        else:
            await bot.send_message(GROUP_CHAT_ID, text, parse_mode="HTML")
    else:
        logging.warning("GROUP_CHAT_ID sozlanmagan — murojaat guruhga yuborilmadi.")

    await answer_target.answer(
        "✅ Murojaatingiz qabul qilindi.\n\n"
        "Belgilangan tartibda ko'rib chiqiladi.\n"
        "Zarurat tug'ilganda Siz bilan bog'lanamiz.",
        reply_markup=main_menu(),
    )
    await state.clear()


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
