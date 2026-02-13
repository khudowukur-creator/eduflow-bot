import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- ASOSIY MA'LUMOTLAR ---
API_TOKEN = '8027783889:AAGfvyoiQCEMGH2GfT9C_sK1BWZZcV9XsT0'
ADMIN_ID = 7031270541 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Render uchun fake port (xatoliklarni oldini olish uchun)
async def handle(request):
    return web.Response(text="Bot is running!")

class AddCourse(StatesGroup):
    name = State()
    price = State()
    description = State()

# --- BAZA BILAN ISHLASH ---
def get_courses():
    conn = sqlite3.connect('eduflow.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, description FROM courses")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_course_by_id(course_id):
    conn = sqlite3.connect('eduflow.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()

# --- START VA BILDIRISHNOMA ---
@dp.message(Command("start"))
async def start(message: types.Message):
    # Sizga (7031270541 ID) yangi odam kirsa xabar boradi
    if message.from_user.id != ADMIN_ID:
        user_info = (
            f"🔔 **Botga yangi foydalanuvchi kirdi!**\n\n"
            f"👤 Ismi: {message.from_user.full_name}\n"
            f"🆔 ID: {message.from_user.id}\n"
            f"🔗 Username: @{message.from_user.username if message.from_user.username else 'Mavjud emas'}"
        )
        try:
            await bot.send_message(ADMIN_ID, user_info, parse_mode="Markdown")
        except:
            pass

    kb = [[types.KeyboardButton(text="📚 Kurslarni ko'rish")], [types.KeyboardButton(text="📞 Yordam")]]
    if message.from_user.id == ADMIN_ID:
        kb.append([types.KeyboardButton(text="⚙️ Admin Panel")])
    
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Salom! EduFlowUz botiga xush kelibsiz. Bot endi Admin Panel bilan ishlaydi!", reply_markup=keyboard)

# --- ADMIN PANEL ---
@dp.message(F.text == "⚙️ Admin Panel")
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        kb = [
            [types.KeyboardButton(text="➕ Kurs qo'shish")],
            [types.KeyboardButton(text="🗑 Kursni o'chirish")],
            [types.KeyboardButton(text="🏠 Bosh menyu")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("Admin Panelga xush kelibsiz!", reply_markup=keyboard)

# --- O'CHIRISH (INLINE TUGMALAR) ---
@dp.message(F.text == "🗑 Kursni o'chirish")
async def show_delete_list(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        courses = get_courses()
        if not courses:
            await message.answer("O'chirish uchun kurslar mavjud emas.")
            return
        builder = InlineKeyboardBuilder()
        for c in courses:
            builder.row(types.InlineKeyboardButton(text=f"❌ {c[1]}", callback_data=f"del_{c[0]}"))
        await message.answer("O'chirmoqchi bo'lgan kursingizni tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("del_"))
async def process_delete(callback: types.CallbackQuery):
    course_id = int(callback.data.split("_")[1])
    delete_course_by_id(course_id)
    await callback.answer("Kurs o'chirildi!")
    await callback.message.edit_text("✅ Kurs muvaffaqiyatli o'chirildi.")

# --- KURS QO'SHISH ---
@dp.message(F.text == "➕ Kurs qo'shish")
async def start_add_course(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Yangi kurs nomini yuboring:")
        await state.set_state(AddCourse.name)

@dp.message(AddCourse.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Kurs narxini yuboring:")
    await state.set_state(AddCourse.price)

@dp.message(AddCourse.price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Kurs haqida ma'lumot yuboring:")
    await state.set_state(AddCourse.description)

@dp.message(AddCourse.description)
async def process_desc(message: types.Message, state: FSMContext):
    data = await state.get_data()
    conn = sqlite3.connect('eduflow.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO courses (name, price, description) VALUES (?, ?, ?)", 
                   (data['name'], data['price'], message.text))
    conn.commit()
    conn.close()
    await message.answer(f"✅ '{data['name']}' kursi qo'shildi.")
    await state.clear()

# --- FOYDALANUVCHILAR UCHUN ---
@dp.message(F.text == "📚 Kurslarni ko'rish")
async def list_courses(message: types.Message):
    courses = get_courses()
    if not courses:
        await message.answer("Hozircha kurslar yo'q.")
        return
    text = "🚀 EduFlowUz platformasidagi kurslar:\n\n"
    for c in courses:
        text += f"📔 **{c[1]}**\n💰 Narxi: {c[2]}\n📝 Ma'lumot: {c[3]}\n\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🏠 Bosh menyu")
async def back_home(message: types.Message):
    await start(message)

# --- SERVERNI ISHGA TUSHIRISH ---
async def main():
    # Render uchun portni ochamiz
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await site.start()
    
    print("Bot serverda ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())