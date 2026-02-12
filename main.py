import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Sizning bot tokiningiz
API_TOKEN = '8027783889:AAGfvyoiQCEMGH2GfT9C_sK1BWZZcV9XsT0'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def get_courses():
    conn = sqlite3.connect('eduflow.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, description FROM courses")
    rows = cursor.fetchall()
    conn.close()
    return rows

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = [
        [types.KeyboardButton(text="📚 Kurslarni ko'rish")],
        [types.KeyboardButton(text="📞 Yordam")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(f"Salom! EduFlowUz botiga xush kelibsiz.", reply_markup=keyboard)

@dp.message(lambda message: message.text == "📚 Kurslarni ko'rish")
async def list_courses(message: types.Message):
    courses = get_courses()
    if not courses:
        await message.answer("Hozircha kurslar yo'q.")
        return
    text = "🔥 Mavjud kurslarimiz:\n\n"
    for c in courses:
        text += f"📔 **{c[0]}**\n💰 Narxi: {c[1]} so'm\n📝 Ma'lumot: {c[2]}\n\n"
    await message.answer(text, parse_mode="Markdown")

async def main():
    print("Bot ishga tushdi... Telegramdan tekshirib ko'ring!")
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())