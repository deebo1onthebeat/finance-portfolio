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
from aiogram.fsm.storage.redis import RedisStorage

# Импорты
from states import RegisterState, LoginState, CategoryState, TransactionState, CategoryEditState
from keyboards import kb_start, kb_main

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")
# Адрес Redis
REDIS_URL = "redis://localhost:6379/0" 

logging.basicConfig(level=logging.INFO)

# --- НАСТРОЙКА REDIS ---
storage = RedisStorage.from_url(REDIS_URL)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
async def save_token(user_id: int, token: str):
    """Сохраняет токен в Redis."""
    await storage.redis.set(f"user:{user_id}:token", token)

async def get_token(user_id: int) -> str | None:
    """Получает токен из Redis."""
    token = await storage.redis.get(f"user:{user_id}:token")
    if token:
        return token.decode("utf-8")
    return None

# --- СТАРТ ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    token = await get_token(message.from_user.id)
    if token:
        await message.answer("С возвращением! Вы уже авторизованы.", reply_markup=kb_main)
    else:
        await message.answer("Привет! Я твой финансовый помощник.", reply_markup=kb_start)

# ==========================================
# REGISTRATION & LOGIN
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
                # Сохраняем в Redis
                await save_token(message.from_user.id, token)
                await message.answer("✅ Вы вошли!", reply_markup=kb_main)
            else:
                await message.answer("❌ Неверные данные.", reply_markup=kb_start)
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
    await state.clear()

@dp.message(F.text == "🚪 Выход")
async def process_logout(message: types.Message, state: FSMContext):
    redis_key = f"user:{message.from_user.id}:token"
    await storage.redis.delete(redis_key)
    await state.clear()
    await message.answer("Вы успешно вышли. 👋", reply_markup=kb_start)

# ==========================================
# CATEGORIES (Управление)
# ==========================================

# Вспомогательная функция для отображения списка
async def show_categories_list(message_or_call, user_id, token):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_URL}/categories/",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                categories = response.json()
                if not categories:
                    text = "Список категорий пуст."
                    keyboard = None
                else:
                    text = "📂 Ваши категории:\nВыберите категорию для управления:"
                    buttons = [
                        [InlineKeyboardButton(text=f"🔹 {cat['name']}", callback_data=f"open_cat_{cat['id']}")]
                        for cat in categories
                    ]
                    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                
                if isinstance(message_or_call, types.Message):
                    await message_or_call.answer(text, reply_markup=keyboard)
                else:
                    await message_or_call.message.edit_text(text, reply_markup=keyboard)
            else:
                err_text = "❌ Ошибка API."
                if isinstance(message_or_call, types.Message):
                    await message_or_call.answer(err_text)
                else:
                    await message_or_call.message.edit_text(err_text)
        except Exception as e:
            err_text = f"Ошибка: {e}"
            if isinstance(message_or_call, types.Message):
                await message_or_call.answer(err_text)

# 1. Обработчик кнопки меню "Мои категории"
@dp.message(F.text == "📂 Мои категории")
async def get_categories_handler(message: types.Message):
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer("⚠️ Войдите в систему!")
        return
    await show_categories_list(message, message.from_user.id, token)

# 2. Детальный просмотр категории (Инлайн)
@dp.callback_query(F.data.startswith("open_cat_"))
async def open_category_detail(callback: CallbackQuery):
    cat_id = int(callback.data.split("_")[2])
    text = f"⚙️ Управление категорией (ID: {cat_id})\nЧто хотите сделать?"
    buttons = [
        [InlineKeyboardButton(text="✏️ Изменить название", callback_data=f"edit_cat_{cat_id}")],
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"del_cat_{cat_id}")],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back_to_cats")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

# 3. Кнопка "Назад"
@dp.callback_query(F.data == "back_to_cats")
async def back_to_categories_list(callback: CallbackQuery):
    token = await get_token(callback.from_user.id)
    if token:
        await show_categories_list(callback, callback.from_user.id, token)
    await callback.answer()

# 4. Кнопка "Удалить" (Заглушка)
@dp.callback_query(F.data.startswith("del_cat_"))
async def delete_category_stub(callback: CallbackQuery):
    await callback.answer("Функция удаления пока в разработке 🛠", show_alert=True)

# 5. Редактирование: Старт
@dp.callback_query(F.data.startswith("edit_cat_"))
async def start_edit_category(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[2])
    await state.update_data(editing_cat_id=cat_id)
    await callback.message.answer("Введите новое название для категории:")
    await state.set_state(CategoryEditState.waiting_for_new_name)
    await callback.answer()

# 6. Редактирование: Ввод имени
@dp.message(CategoryEditState.waiting_for_new_name)
async def ask_confirm_edit(message: types.Message, state: FSMContext):
    await state.update_data(new_name=message.text)
    text = f"Вы точно хотите изменить название на '{message.text}'?"
    buttons = [[
        InlineKeyboardButton(text="✅ Да", callback_data="conf_edit_yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data="conf_edit_no")
    ]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(CategoryEditState.waiting_for_confirmation)

# 7. Редактирование: Подтверждение
@dp.callback_query(CategoryEditState.waiting_for_confirmation)
async def process_confirm_edit(callback: CallbackQuery, state: FSMContext):
    if callback.data == "conf_edit_no":
        await callback.message.edit_text("Отмена.")
        await state.clear()
        token = await get_token(callback.from_user.id)
        if token:
            await show_categories_list(callback, callback.from_user.id, token)
        return

    # Если Да
    data = await state.get_data()
    token = await get_token(callback.from_user.id)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{API_URL}/categories/{data['editing_cat_id']}",
                json={"name": data['new_name']},
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                await callback.message.edit_text("✅ Успешно изменено!")
            else:
                await callback.message.edit_text(f"❌ Ошибка API: {response.text}")
        except Exception as e:
            await callback.message.edit_text(f"Ошибка: {e}")

    await state.clear()
    await asyncio.sleep(1)
    if token:
        await show_categories_list(callback, callback.from_user.id, token)

# --- СОЗДАНИЕ КАТЕГОРИИ (Кнопка меню) ---
@dp.message(F.text == "➕ Новая категория")
async def start_add_cat(message: types.Message, state: FSMContext):
    if not await get_token(message.from_user.id): return await message.answer("Войдите!")
    await message.answer("Название категории:")
    await state.set_state(CategoryState.waiting_for_name)

@dp.message(CategoryState.waiting_for_name)
async def process_add_cat(message: types.Message, state: FSMContext):
    token = await get_token(message.from_user.id)
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
# TRANSACTIONS
# ==========================================
@dp.message(F.text == "📊 Статистика")
async def get_stats(message: types.Message):
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer("⚠️ Войдите в систему!")
        return

    now = datetime.now()
    start_date = date(now.year, now.month, 1)
    _, last_day = calendar.monthrange(now.year, now.month)
    end_date = date(now.year, now.month, last_day)

    await message.answer(f"📊 Считаю финансы за {now.strftime('%B %Y')}...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_URL}/transactions/stats",
                params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                stats = response.json()
                text = (
                    f"📅 Статистика за текущий месяц:\n\n"
                    f"📈 Доходы: {stats['total_income']:,.2f} ₽\n"
                    f"📉 Расходы: {stats['total_expense']:,.2f} ₽\n"
                    f"➖➖➖➖➖➖➖➖➖➖\n"
                    f"💰 Баланс: {stats['balance']:,.2f} ₽"
                )
                await message.answer(text)
            else:
                await message.answer(f"❌ Ошибка API: {response.text}")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

@dp.message(F.text == "🎨 Диаграмма")
async def get_chart(message: types.Message):
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer("⚠️ Войдите в систему!")
        return

    now = datetime.now()
    start_date = date(now.year, now.month, 1)
    _, last_day = calendar.monthrange(now.year, now.month)
    end_date = date(now.year, now.month, last_day)

    await message.answer("Рисую диаграмму... 🎨")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_URL}/transactions/graph",
                params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                from aiogram.types import BufferedInputFile
                photo = BufferedInputFile(response.content, filename="chart.png")
                await message.answer_photo(photo, caption=f"Ваши расходы за {now.strftime('%B %Y')}")
            elif response.status_code == 404:
                await message.answer("Нет данных для диаграммы.")
            else:
                await message.answer(f"❌ Ошибка API: {response.text}")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

# --- ТРАНЗАКЦИИ ВВОД ---
@dp.message(F.text.in_({"💸 Добавить доход", "💸 Добавить расход"}))
async def start_transaction(message: types.Message, state: FSMContext):
    if not await get_token(message.from_user.id):
        await message.answer("⚠️ Войдите в систему!")
        return

    tran_type = "income" if message.text == "💸 Добавить доход" else "expense"
    await state.update_data(type=tran_type)
    await message.answer(f"💰 Введите сумму ({'Доход' if tran_type == 'income' else 'Расход'}):")
    await state.set_state(TransactionState.waiting_for_amount)

@dp.message(TransactionState.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число (например, 500):")
        return

    await state.update_data(amount=amount)
    
    token = await get_token(message.from_user.id)
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

@dp.callback_query(TransactionState.waiting_for_category)
async def process_category_click(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[1])
    await state.update_data(category_id=category_id)
    await callback.message.edit_text(f"Категория выбрана. Введите описание (или '-'):")
    await state.set_state(TransactionState.waiting_for_description)
    await callback.answer()

@dp.message(TransactionState.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    description = message.text if message.text != "-" else None
    data = await state.get_data()
    data['transaction_date'] = datetime.now().isoformat()
    data['description'] = description
    
    token = await get_token(message.from_user.id)
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
    print("Бот запущен с Redis! 🐘")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")