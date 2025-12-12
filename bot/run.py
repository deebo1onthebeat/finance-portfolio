import asyncio
import os
import logging
import httpx
from datetime import datetime, date
import calendar

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Импорты
from states import RegisterState, LoginState, CategoryState, TransactionState
from keyboards import kb_start, kb_main

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users_tokens = {}

# --- СТАРТ ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я твой финансовый помощник.", reply_markup=kb_start)

# ==========================================
# REGISTRATION & LOGIN (Код без изменений)
# ==========================================
@dp.message(F.text == "📝 Регистрация")
async def start_register(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш Email:")
    await state.set_state(RegisterState.waiting_for_email)

@dp.message(RegisterState.waiting_for_email)
async def reg_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Придумайте пароль:")
    await state.set_state(RegisterState.waiting_for_password)

@dp.message(RegisterState.waiting_for_password)
async def reg_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    data = await state.get_data()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_URL}/auth/register", json=data)
            if response.status_code == 200:
                await message.answer("✅ Успешно! Жмите '🔑 Вход'.", reply_markup=kb_start)
            else:
                await message.answer(f"❌ Ошибка: {response.text}", reply_markup=kb_start)
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
    await state.clear()

@dp.message(F.text == "🔑 Вход")
async def start_login(message: types.Message, state: FSMContext):
    await message.answer("Email:")
    await state.set_state(LoginState.waiting_for_email)

@dp.message(LoginState.waiting_for_email)
async def login_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Пароль:")
    await state.set_state(LoginState.waiting_for_password)

@dp.message(LoginState.waiting_for_password)
async def login_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    data = await state.get_data()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_URL}/auth/login", json=data)
            if response.status_code == 200:
                token = response.json()['access_token']
                users_tokens[message.from_user.id] = token
                await message.answer("✅ Вы вошли!", reply_markup=kb_main)
            else:
                await message.answer("❌ Неверные данные.", reply_markup=kb_start)
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
    await state.clear()

# ==========================================
# CATEGORIES
# ==========================================
@dp.message(F.text == "📂 Мои категории")
async def get_categories(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_tokens:
        await message.answer("⚠️ Войдите в систему!")
        return
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_URL}/categories/", 
            headers={"Authorization": f"Bearer {users_tokens[user_id]}"}
        )
        if response.status_code == 200:
            cats = response.json()
            text = "📂 **Категории:**\n" + "\n".join([f"- {c['name']}" for c in cats])
            await message.answer(text if cats else "Пусто.")
        else:
            await message.answer("Ошибка получения категорий.")

@dp.message(F.text == "➕ Новая категория")
async def start_add_cat(message: types.Message, state: FSMContext):
    if message.from_user.id not in users_tokens: return await message.answer("Войдите!")
    await message.answer("Название категории:")
    await state.set_state(CategoryState.waiting_for_name)

@dp.message(CategoryState.waiting_for_name)
async def process_add_cat(message: types.Message, state: FSMContext):
    token = users_tokens.get(message.from_user.id)
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{API_URL}/categories/", 
            json={"name": message.text},
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            await message.answer(f"✅ Категория '{message.text}' создана!")
        else:
            await message.answer("Ошибка создания.")
    await state.clear()


# ==========================================
# 📊 СТАТИСТИКА (GET /stats)
# ==========================================
@dp.message(F.text == "📊 Статистика")
async def get_stats(message: types.Message):
    if message.from_user.id not in users_tokens:
        await message.answer("⚠️ Сначала войдите в систему!")
        return

    token = users_tokens[message.from_user.id]
    
    # 1. Вычисляем даты
    now = datetime.now()
    start_date = date(now.year, now.month, 1)
    _, last_day = calendar.monthrange(now.year, now.month)
    end_date = date(now.year, now.month, last_day)

    await message.answer(f"📊 Считаю финансы за {now.strftime('%B %Y')}...")

    async with httpx.AsyncClient() as client:
        try:
            # 2. Отправляем запрос
            response = await client.get(
                f"{API_URL}/transactions/stats",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                stats = response.json()
                
                # 3. Красиво форматируем ответ
                text = (
                    f"📅 **Статистика за текущий месяц:**\n\n"
                    f"📈 **Доходы:** {stats['total_income']:,.2f} ₽\n"
                    f"📉 **Расходы:** {stats['total_expense']:,.2f} ₽\n"
                    f"➖➖➖➖➖➖➖➖➖➖\n"
                    f"💰 **Баланс:** {stats['balance']:,.2f} ₽"
                )
                await message.answer(text)
            else:
                await message.answer(f"❌ Ошибка API: {response.text}")
                
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

# ==========================================
# 🎨 ДИАГРАММА (GET /transactions/graph)
# ==========================================
@dp.message(F.text == "🎨 Диаграмма")
async def get_chart(message: types.Message):
    if message.from_user.id not in users_tokens:
        await message.answer("⚠️ Сначала войдите в систему!")
        return

    token = users_tokens[message.from_user.id]
    
    # Даты текущего месяца
    now = datetime.now()
    start_date = date(now.year, now.month, 1)
    _, last_day = calendar.monthrange(now.year, now.month)
    end_date = date(now.year, now.month, last_day)

    await message.answer("Рисую диаграмму... 🎨")

    async with httpx.AsyncClient() as client:
        try:
            # Делаем запрос. Обрати внимание: мы НЕ ждем JSON, мы ждем байты (content)
            response = await client.get(
                f"{API_URL}/transactions/graph",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                # Отправляем картинку пользователю
                # BufferedInputFile - это способ передать байты в aiogram
                from aiogram.types import BufferedInputFile
                
                photo = BufferedInputFile(response.content, filename="chart.png")
                await message.answer_photo(photo, caption=f"Ваши расходы за {now.strftime('%B %Y')}")
                
            elif response.status_code == 404:
                await message.answer("Нет данных для диаграммы за этот месяц.")
            else:
                await message.answer(f"❌ Ошибка API: {response.text}")
                
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

# ==========================================
# 🆕 ТРАНЗАКЦИИ (ДОХОД / РАСХОД)
# ==========================================

# 1. Запуск процесса
@dp.message(F.text.in_({"💸 Добавить доход", "💸 Добавить расход"}))
async def start_transaction(message: types.Message, state: FSMContext):
    if message.from_user.id not in users_tokens:
        await message.answer("⚠️ Сначала войдите в систему!")
        return

    tran_type = "income" if message.text == "💸 Добавить доход" else "expense"
    await state.update_data(type=tran_type)
    
    await message.answer(f"💰 Введите сумму ({'Доход' if tran_type == 'income' else 'Расход'}):")
    await state.set_state(TransactionState.waiting_for_amount)

# 2. Получаем сумму
@dp.message(TransactionState.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число (например, 500):")
        return

    await state.update_data(amount=amount)
    
    token = users_tokens[message.from_user.id]
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_URL}/categories/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            categories = response.json()
            if not categories:
                await message.answer("❌ Нет категорий. Сначала создайте их!")
                await state.clear()
                return
            
            # Инлайн-кнопки
            buttons = [
                [InlineKeyboardButton(text=cat['name'], callback_data=f"cat_{cat['id']}")]
                for cat in categories
            ]
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await message.answer("Выберите категорию:", reply_markup=keyboard)
            await state.set_state(TransactionState.waiting_for_category)
        else:
            await message.answer("Ошибка API при загрузке категорий.")
            await state.clear()

# 3. Нажали на категорию
@dp.callback_query(TransactionState.waiting_for_category)
async def process_category_click(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[1])
    await state.update_data(category_id=category_id)
    
    await callback.message.edit_text(f"Категория выбрана. Введите описание (или '-'):")
    await state.set_state(TransactionState.waiting_for_description)
    await callback.answer()

# 4. Ввели описание и финиш
@dp.message(TransactionState.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    description = message.text if message.text != "-" else None
    
    data = await state.get_data()
    data['transaction_date'] = datetime.now().isoformat()
    data['description'] = description
    
    token = users_tokens[message.from_user.id]
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_URL}/transactions/",
                json=data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                tran = response.json()
                await message.answer(
                    f"✅ Записано!\n"
                    f"Сумма: {tran['amount']} ₽\n"
                    f"Тип: {'Доход' if tran['type'] == 'income' else 'Расход'}",
                    reply_markup=kb_main
                )
            else:
                await message.answer(f"❌ Ошибка API: {response.text}")
                
        except Exception as e:
            await message.answer(f"Ошибка соединения: {e}")
            
    await state.clear()

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")