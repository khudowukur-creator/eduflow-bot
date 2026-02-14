import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- 1. ASOSIY MA'LUMOTLAR ---
# Tokenlarni ehtiyotkorlik bilan qo'shtirnoq ichiga yozing
API_TOKEN = '8027783889:AAGfvyoiQCEMGH2GfT9C_sK1BWZZcV9XsT0'
CLICK_TOKEN = '398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065'
ADMIN_ID = 7031270541 #

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class AddCourse(StatesGroup):
    name = State()
    price = State()
    description = State()
    video_id = State()

# Render uchun majburiy veb-interfeys
async def handle(request):
    return web.Response(text="Bot is running!")

# --- 2. BAZANI SOZLASH ---
def init_db():
    conn = sqlite3.connect('eduflow_final.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS courses 
                      (id INTEGER PRIMARY KEY, name TEXT, price TEXT, description TEXT, video_id TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS purchases 
                      (user_id INTEGER, course_id INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. START VA BILDIRISHNOMA ---
@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        try:
            user_info = f"🔔 **Yangi foydalanuvchi:** {message.from_user.full_name}\n🆔 ID: {message.from_user.id}"
            await bot.send_message(ADMIN_ID, user_info, parse_mode="Markdown")
        except:
            pass

    kb = [[types.KeyboardButton(text="📚 Kurslarni ko'rish")], [types.KeyboardButton(text="📞 Yordam")]]
    if message.from_user.id == ADMIN_ID:
        kb.append([types.KeyboardButton(text="⚙️ Admin Panel")])
    
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Xush kelibsiz! Kerakli bo'limni tanlang.", reply_markup=keyboard)

# --- 4. KURSNI KO'RISH VA TO'LOV ---
@dp.message(F.text == "📚 Kurslarni ko'rish")
async def list_courses(message: types.Message):
    conn = sqlite3.connect('eduflow_final.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, description FROM courses")
    courses = cursor.fetchall()
    conn.close()

    if not courses:
        await message.answer("Hozircha kurslar yo'q.")
        return

    for c in courses:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="💳 To'lov (Click)", callback_data=f"buy_{c[0]}"))
        builder.row(types.InlineKeyboardButton(text="📺 Videoni ko'rish", callback_data=f"view_{c[0]}"))
        await message.answer(f"📔 **{c[1]}**\n💰 Narxi: {c[2]} so'm\n📝 {c[3]}", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def send_invoice(callback: types.CallbackQuery):
    course_id = int(callback.data.split("_")[1])
    conn = sqlite3.connect('eduflow_final.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, price FROM courses WHERE id = ?", (course_id,))
    course = cursor.fetchone()
    conn.close()

    price_val = int(''.join(filter(str.isdigit, course[1]))) * 100 
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=course[0],
        description="To'lovdan so'ng video ochiladi.",
        payload=f"course_{course_id}",
        provider_token=CLICK_TOKEN,
        currency="UZS",
        prices=[types.LabeledPrice(label=course[0], amount=price_val)]
    )

@dp.pre_checkout_query(lambda query: True)
async def checkout(query: types.Pre_checkout_query):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def got_payment(message: types.Message):
    course_id = int(message.successful_payment.invoice_payload.split("_")[1])
    conn = sqlite3.connect('eduflow_final.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO purchases (user_id, course_id) VALUES (?, ?)", (message.from_user.id, course_id))
    conn.commit()
    conn.close()
    await message.answer("✅ To'lov muvaffaqiyatli! Videoni ko'rishingiz mumkin.")

@dp.callback_query(F.data.startswith("view_"))
async def view_video(callback: types.CallbackQuery):
    course_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    conn = sqlite3.connect('eduflow_final.db')
    cursor = conn.cursor()
    cursor.execute("SELECT video_id FROM courses WHERE id = ?", (course_id,))
    video = cursor.fetchone()
    cursor.execute("SELECT * FROM purchases WHERE user_id = ? AND course_id = ?", (user_id, course_id))
    paid = cursor.fetchone()
    conn.close()
    
    if paid or user_id == ADMIN_ID:
        if video and video[0]:
            await callback.message.answer_video(video=video[0])
        else:
            await callback.answer("Video yo'q.", show_alert=True)
    else:
        await callback.answer("❌ Avval to'lov qiling!", show_alert=True)

# --- 5. ADMIN PANEL ---
@dp.message(F.text == "⚙️ Admin Panel")
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        kb = [[types.KeyboardButton(text="➕ Kurs qo'shish")], [types.KeyboardButton(text="🗑 Kursni o'chirish")], [types.KeyboardButton(text="🏠 Bosh menyu")]]
        await message.answer("Admin Panel:", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@dp.message(F.text == "➕ Kurs qo'shish")
async def add_start(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Nomini yuboring:")
        await state.set_state(AddCourse.name)

@dp.message(AddCourse.name)
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Narxni faqat raqamda:")
    await state.set_state(AddCourse.price)

@dp.message(AddCourse.price)
async def add_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Tavsif:")
    await state.set_state(AddCourse.description)

@dp.message(AddCourse.description)
async def add_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Videoni yuboring:")
    await state.set_state(AddCourse.video_id)

@dp.message(AddCourse.video_id, F.video)
async def add_video(message: types.Message, state: FSMContext):
    data = await state.get_data()
    conn = sqlite3.connect('eduflow_final.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO courses (name, price, description, video_id) VALUES (?, ?, ?, ?)", 
                   (data['name'], data['price'], data['description'], message.video.file_id))
    conn.commit()
    conn.close()
    await message.answer("✅ Saqlandi!")
    await state.clear()

# --- 6. SERVERNI ISHGA TUSHIRISH ---
async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()
    
    print(f"Bot {port}-portda ishga tushdi...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())