import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Bot ma'lumotlari
API_TOKEN = '8027783889:AAGfvyo1QCEMGH2GfT9C_sK1BWZZcV9XsT0'
ADMIN_ID = 7031270541  # Sizning ID raqamingiz o'rnatildi

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Kurs qo'shish jarayoni uchun holatlar
class AddCourse(StatesGroup):
    name = State()
    price = State()
    description = State()

# Ma'lumotlar bazasidan kurslarni olish
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
    
    # Faqat sizga ko'rinadigan Admin Panel tugmasi
    if message.from_user.id == ADMIN_ID:
        kb.append([types.KeyboardButton(text="⚙️ Admin Panel")])
        
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(f"Salom! EduFlowUz botiga xush kelibsiz. Bot endi Admin Panel bilan ishlaydi!", reply_markup=keyboard)

# Admin Panel menyusi
@dp.message(F.text == "⚙️ Admin Panel")
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        kb = [
            [types.KeyboardButton(text="➕ Kurs qo'shish")],
            [types.KeyboardButton(text="🏠 Bosh menyu")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("Siz adminsiz! Yangi kurs qo'shishni xohlaysizmi?", reply_markup=keyboard)

# Kurs qo'shish bosqichlari
@dp.message(F.text == "➕ Kurs qo'shish")
async def start_add_course(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Yangi kurs nomini yuboring:")
        await state.set_state(AddCourse.name)

@dp.message(AddCourse.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Kurs narxini yuboring (masalan: 150000):")
    await state.set_state(AddCourse.price)

@dp.message(AddCourse.price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Kurs haqida batafsil ma'lumot yuboring:")
    await state.set_state(AddCourse.description)

@dp.message(AddCourse.description)
async def process_desc(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Ma'lumotlarni bazaga saqlash
    conn = sqlite3.connect('eduflow.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO courses (name, price, description) VALUES (?, ?, ?)", 
                   (data['name'], data['price'], message.text))
    conn.commit()
    conn.close()
    
    await message.answer(f"✅ Tayyor! '{data['name']}' kursi bazaga qo'shildi.")
    await state.clear()

@dp.message(F.text == "📚 Kurslarni ko'rish")
async def list_courses(message: types.Message):
    courses = get_courses()
    if not courses:
        await message.answer("Hozircha kurslar yo'q.")
        return
    
    text = "🚀 EduFlowUz platformasidagi kurslar:\n\n"
    for c in courses:
        text += f"📔 **{c[0]}**\n💰 Narxi: {c[1]} so'm\n📝 Ma'lumot: {c[2]}\n\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🏠 Bosh menyu")
async def back_home(message: types.Message):
    await start(message)

async def main():
    print("Bot Admin Panel (ID: 7031270541) bilan ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())