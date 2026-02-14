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
CLICK_TOKEN = '398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Render uchun veb-interfeys (Port xatosini oldini oladi)
async def handle(request):
    return web.Response(text="Bot is running live!")

class AddCourse(StatesGroup):
    name = State()
    price = State()
    description = State()
    video_id = State()

# --- BAZANI SOZLASH (V2) ---
def init_db():
    conn = sqlite3.connect('eduflow_v2.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS courses 
                      (id INTEGER PRIMARY KEY, name TEXT, price TEXT, description TEXT, video_id TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS purchases 
                      (user_id INTEGER, course_id INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- START VA BILDIRISHNOMA ---
@dp.message(Command("start"))
async def start(message: types.Message):
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
    await message.answer("Salom! EduFlowUz botiga xush kelibsiz.", reply_markup=keyboard)

# --- KURSNI KO'RISH ---
@dp.message(F.text == "📚 Kurslarni ko'rish")
async def list_courses(message: types.Message):
    conn = sqlite3.connect('eduflow_v2.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, description, video_id FROM courses")
    courses = cursor.fetchall()
    conn.close()

    if not courses:
        await message.answer("Hozircha kurslar mavjud emas.")
        return

    for c in courses:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="💳 To'lov qilish (Click)", callback_data=f"buy_{c[0]}"))
        builder.row(types.InlineKeyboardButton(text="📺 Videoni ko'rish", callback_data=f"view_{c[0]}"))
        
        text = f"📔 **Kurs:** {c[1]}\n💰 **Narxi:** {c[2]} so'm\n📝 **Ma'lumot:** {c[3]}"
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# --- CLICK TO'LOV ---
@dp.callback_query(F.data.startswith("buy_"))
async def send_invoice(callback: types.CallbackQuery):
    course_id = int(callback.data.split("_")[1])
    conn = sqlite3.connect('eduflow_v2.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, price FROM courses WHERE id = ?", (course_id,))
    course = cursor.fetchone()
    conn.close()

    if course:
        price_val = int(''.join(filter(str.isdigit, course[1]))) * 100 
        await bot.send_invoice(
            chat_id=callback.message.chat.id,
            title=course[0],
            description="Kurs uchun to'lov qiling va video darslikka ega bo'ling.",
            payload=f"course_{course_id}",
            provider_token=CLICK_TOKEN,
            currency="UZS",
            prices=[types.LabeledPrice(label=course[0], amount=price_val)]
        )

@dp.pre_checkout_query(lambda query: True)
async def checkout(pre_checkout_query: types.Pre_checkout_query):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def got_payment(message: types.Message):
    course_id = int(message.successful_payment.invoice_payload.split("_")[1])
    conn = sqlite3.connect('eduflow_v2.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO purchases (user_id, course_id) VALUES (?, ?)", (message.from_user.id, course_id))
    conn.commit()
    conn.close()
    await message.answer("✅ To'lov muvaffaqiyatli! Endi 'Videoni ko'rish' tugmasi orqali darsni ko'rishingiz mumkin.")

# --- VIDEO KO'RISH ---
@dp.callback_query(F.data.startswith("view_"))
async def view_video(callback: types.CallbackQuery):
    course_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    conn = sqlite3.connect('eduflow_v2.db')
    cursor = conn.cursor()
    cursor.execute("SELECT video_id FROM courses WHERE id = ?", (course_id,))
    video = cursor.fetchone()
    cursor.execute("SELECT * FROM purchases WHERE user_id = ? AND course_id = ?", (user_id, course_id))
    paid = cursor.fetchone()
    conn.close()
    
    if paid or user_id == ADMIN_ID:
        if video and video[0]:
            await callback.message.answer_video(video=video[0], caption="Marhamat, dars videoni tomosha qiling!")
        else:
            await callback.answer("Ushbu kurs uchun video hali yuklanmagan.", show_alert=True)
    else:
        await callback.answer("❌ Videoni ko'rish uchun avval to'lov qilishingiz kerak!", show_alert=True)

# --- ADMIN PANEL ---
@dp.message(F.text == "⚙️ Admin Panel")
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        kb = [[types.KeyboardButton(text="➕ Kurs qo'shish")], [types.KeyboardButton(text="🗑 Kursni o'chirish")], [types.KeyboardButton(text="🏠 Bosh menyu")]]
        await message.answer("Admin Panel:", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@dp.message(F.text == "➕ Kurs qo'shish")
async def start_add_course(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Kurs nomini yuboring:")
        await state.set_state(AddCourse.name)

@dp.message(AddCourse.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Narxni faqat raqamlarda yuboring (Masalan: 50000):")
    await state.set_state(AddCourse.price)

@dp.message(AddCourse.price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Kurs tavsifini yuboring:")
    await state.set_state(AddCourse.description)

@dp.message(AddCourse.description)
async def process_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Endi kurs videosini yuboring (Faqat video fayl formatida):")
    await state.set_state(AddCourse.video_id)

@dp.message(AddCourse.video_id, F.video)
async def process_video(message: types.Message, state: FSMContext):
    data = await state.get_data()
    v_id = message.video.file_id
    conn = sqlite3.connect('eduflow_v2.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO courses (name, price, description, video_id) VALUES (?, ?, ?, ?)", 
                   (data['name'], data['price'], data['description'], v_id))
    conn.commit()
    conn.close()
    await message.answer(f"✅ '{data['name']}' kursi video bilan muvaffaqiyatli saqlandi.")
    await state.clear()

@dp.message(F.text == "🗑 Kursni o'chirish")
async def show_delete_list(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        conn = sqlite3.connect('eduflow_v2.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM courses")
        courses = cursor.fetchall()
        conn.close()
        if not courses:
            await message.answer("O'chirish uchun kurslar yo'q.")
            return
        builder = InlineKeyboardBuilder()
        for c in courses:
            builder.row(types.InlineKeyboardButton(text=f"❌ {c[1]}", callback_data=f"del_{c[0]}"))
        await message.answer("O'chirmoqchi bo'lgan kursingizni tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("del_"))
async def process_delete(callback: types.CallbackQuery):
    c_id = int(callback.data.split("_")[1])
    conn = sqlite3.connect('eduflow_v2.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE id = ?", (c_id,))
    conn.commit()
    conn.close()
    await callback.answer("Kurs o'chirildi!")
    await callback.message.edit_text("✅ Kurs muvaffaqiyatli o'chirildi.")

@dp.message(F.text == "🏠 Bosh menyu")
async def back_home(message: types.Message):
    await start(message)

# --- SERVERNI ISHGA TUSHIRISH (RENDER UCHUN) ---
async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"Bot serverda {port}-port orqali ishga tushdi...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())