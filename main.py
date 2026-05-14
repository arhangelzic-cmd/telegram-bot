import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = "ВАШ ТОКЕН"
# ВСТАВЬ СВОЙ TELEGRAM ID
ADMIN_ID = ВАШ ID


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# =========================
# СОСТОЯНИЯ
# =========================

class ApplicationForm(StatesGroup):
    name = State()
    phone = State()
    message = State()


# =========================
# КЛАВИАТУРЫ
# =========================

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Оставить заявку")],
        [KeyboardButton(text="ℹ️ О боте")],
    ],
    resize_keyboard=True,
)

phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)],
        [KeyboardButton(text="❌ Отмена")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Отмена")],
    ],
    resize_keyboard=True,
)


# =========================
# КОМАНДЫ
# =========================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Привет! 👋\n\n"
        "Я бот для приёма заявок.\n"
        "Нажми кнопку ниже, чтобы оставить заявку.",
        reply_markup=main_keyboard,
    )

    await bot.send_message(
        ADMIN_ID,
        "👤 Пользователь запустил бота\n\n"
        f"ID: {message.from_user.id}\n"
        f"Имя: {message.from_user.full_name}\n"
        f"Username: @{message.from_user.username if message.from_user.username else 'нет'}\n"
        f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
    )


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "Доступные команды:\n\n"
        "/start — запустить бота\n"
        "/help — помощь\n"
        "/stats — статистика для админа"
    )


@dp.message(Command("stats"))
async def stats_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У тебя нет доступа к этой команде.")
        return

    await message.answer(
        "📊 Статистика пока базовая.\n"
        "Следующим шагом можно подключить базу данных SQLite и считать заявки."
    )


# =========================
# МЕНЮ
# =========================

@dp.message(F.text == "ℹ️ О боте")
async def about_bot(message: Message):
    await message.answer(
        "Этот бот принимает заявки и отправляет их администратору.\n\n"
        "Можно использовать для услуг, консультаций, заказов или обратной связи."
    )


@dp.message(F.text == "📝 Оставить заявку")
async def create_application(message: Message, state: FSMContext):
    await state.set_state(ApplicationForm.name)
    await message.answer(
        "Введите ваше имя:",
        reply_markup=cancel_keyboard,
    )


@dp.message(F.text == "❌ Отмена")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=main_keyboard,
    )


# =========================
# СБОР ЗАЯВКИ
# =========================

@dp.message(ApplicationForm.name)
async def get_name(message: Message, state: FSMContext):
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("Имя слишком короткое. Введите имя ещё раз:")
        return

    await state.update_data(name=name)
    await state.set_state(ApplicationForm.phone)

    await message.answer(
        "Теперь отправьте номер телефона.\n\n"
        "Можно нажать кнопку ниже или написать номер вручную:",
        reply_markup=phone_keyboard,
    )


@dp.message(ApplicationForm.phone)
async def get_phone(message: Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()

    if len(phone) < 5:
        await message.answer("Номер слишком короткий. Введите номер ещё раз:")
        return

    await state.update_data(phone=phone)
    await state.set_state(ApplicationForm.message)

    await message.answer(
        "Напишите сообщение к заявке:",
        reply_markup=cancel_keyboard,
    )


@dp.message(ApplicationForm.message)
async def get_application_message(message: Message, state: FSMContext):
    user_message = message.text.strip()

    if len(user_message) < 3:
        await message.answer("Сообщение слишком короткое. Напишите подробнее:")
        return

    data = await state.get_data()

    name = data.get("name")
    phone = data.get("phone")

    admin_text = (
        "📩 Новая заявка\n\n"
        f"👤 Имя: {name}\n"
        f"📱 Телефон: {phone}\n"
        f"💬 Сообщение: {user_message}\n\n"
        "Данные Telegram:\n"
        f"ID: {message.from_user.id}\n"
        f"Имя в Telegram: {message.from_user.full_name}\n"
        f"Username: @{message.from_user.username if message.from_user.username else 'нет'}\n"
        f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    )

    await bot.send_message(ADMIN_ID, admin_text)

    await message.answer(
        "Спасибо! ✅\n\n"
        "Ваша заявка отправлена. С вами скоро свяжутся.",
        reply_markup=main_keyboard,
    )

    await state.clear()


# =========================
# ЗАПУСК
# =========================

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
