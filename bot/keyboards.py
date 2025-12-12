from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

kb_start = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Регистрация"), KeyboardButton(text="🔑 Вход")]
    ],
    resize_keyboard=True, 
    input_field_placeholder="Выберите действие..."
)

kb_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📂 Мои категории"), KeyboardButton(text="➕ Новая категория")],
        [KeyboardButton(text="💸 Добавить доход"), KeyboardButton(text="💸 Добавить расход")],
        [KeyboardButton(text="📊 Статистика")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Управляйте финансами..."
)