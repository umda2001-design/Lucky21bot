import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# ===== Asosiy sozlamalar =====
TOKEN = "8260238407:AAHjNBlT2yoF_UiCeEyYaHjmPCp4P6TjuN8"  # <-- bu yerga o'zingizning tokeningizni yozing
ADMIN_ID = 7853450608          # <-- o'zingizning Telegram ID'ingiz
BOT_USERNAME = "LUCKY_021bot"  # <-- bot username
CARD_NUMBER = "5614 6868 3556 6046"
REQUIRED_REFERRALS = 5         # Nechta do‘st kerak

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ===== SQLite bazasi =====
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    invited_by INTEGER,
    referrals INTEGER DEFAULT 0
)
""")
conn.commit()

# ===== /start komandasi =====
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    inviter_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    # Foydalanuvchini bazaga yozish
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing = cursor.fetchone()
    if not existing:
        cursor.execute("INSERT INTO users (user_id, invited_by, referrals) VALUES (?, ?, ?)", (user_id, inviter_id, 0))
        conn.commit()
        if inviter_id:
            cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id=?", (inviter_id,))
            conn.commit()

    # Referal sonini olish
    cursor.execute("SELECT referrals FROM users WHERE user_id=?", (user_id,))
    referrals = cursor.fetchone()[0]

    # Tugmalar
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    if referrals < REQUIRED_REFERRALS:
        text = (
            f"👋 Xush kelibsiz, <b>{message.from_user.full_name}</b>!\n\n"
            f"🎯 O‘yinda qatnashish uchun 5 ta do‘st taklif qilishingiz kerak.\n"
            f"📊 Siz hozircha: <b>{referrals} / {REQUIRED_REFERRALS}</b>\n\n"
            f"🔗 Taklif havolangiz:\n"
            f"https://t.me/{BOT_USERNAME}?start={user_id}"
        )
    else:
        text = (
            f"✅ Siz {REQUIRED_REFERRALS} ta do‘st taklif qildingiz!\n"
            f"Endi o‘yinda qatnashishingiz mumkin 👇"
        )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="💳 To‘lov qilish", callback_data="pay")]
        )

    await message.answer(text, reply_markup=keyboard)

# ===== To‘lov bosilganda =====
@dp.callback_query(lambda c: c.data == "pay")
async def pay_handler(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ To‘lov qildim", callback_data="paid")]]
    )
    await callback.message.edit_text(
        f"<b>Karta raqami:</b>\n<code>{CARD_NUMBER}</code>\n\n"
        "To‘lovni amalga oshirgach pastdagi tugmani bosing 👇",
        reply_markup=keyboard
    )

# ===== To‘lov qabul qilindi =====
@dp.callback_query(lambda c: c.data == "paid")
async def paid_handler(callback: types.CallbackQuery):
    await callback.answer()
    user = callback.from_user
    await bot.send_message(
        ADMIN_ID,
        f"<b>{user.full_name}</b> to‘lovni amalga oshirdi!\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"💳 Karta: <code>{CARD_NUMBER}</code>"
    )
    await callback.message.answer(
        "✅ To‘lov qabul qilindi!\n🎫 Siz endi ertangi o‘yinda qatnashasiz!\n"
        "📅 O‘yin vaqti: soat 21:00"
    )

# ===== Ishga tushirish =====
async def main():
    print("✅ Lucky 021 Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())