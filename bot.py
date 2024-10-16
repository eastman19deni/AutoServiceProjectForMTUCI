import logging
import aiosqlite

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from db import init_db, get_db # Импортируем функции работы с базой данных

 
TOKEN = "7342889272:AAGKu7WQAfOPF5R-lSqJ_N8JuSgTWTMJyLU"# Константная переменная(не меняется в коде)

# Включаем логирование
logging.basicConfig(level=logging.INFO)
# Инициализация бота и хранилища
storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

# Класс состояний для арендодателя
class LandlordForm(StatesGroup):
    description = State() #Описание помещения
    price = State() #Указание цены
    availability = State() #Указание доступных временных слотов

# Класс состояний для арендатора
class TenantForm(StatesGroup):
    booking = State() #Бронирование слота

# Функция для инициализации базы данных при старте
async def on_startup(dispatcher):
    await init_db()
    
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    # Создаём разметку для кнопок и добавляем их
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Я арендодатель", "Я арендатор")
    await message.reply("Выберите свою роль:", reply_markup=markup)

# Обработка выбора пользователя

# При выборе "Я арендодатель"
@dp.message_handler(lambda message: message.text == "Я арендодатель")
async def landlord_start(message: types.Message):
    await message.reply("Вы выбрали функционал для арендодателей.\nДля сдачи помещения нужно ответить на следующие вопросы:", reply_markup=types.ReplyKeyboardRemove())
    await message.reply("Введите описание помещения:")
    await LandlordForm.description.set()
#Сохранение описания и запрос цены
@dp.message_handler(state=LandlordForm.description)
async def landlord_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.reply("Введите цену за аренду:")
    await LandlordForm.price.set()

#Сохранение цены и запрос временных слотов
@dp.message_handler(state=LandlordForm.price)
async def landlord_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.reply("Укажите доступные временные слоты (например: '2024-10-15 09:00 - 12:00'):")
    await LandlordForm.availability.set()
    
#Сохранение слотов и добавление данных в базу
@dp.message_handler(state=LandlordForm.availability)
async def landlord_availability(message: types.Message, state: FSMContext):
    data = await state.get_data()
    description = data['description']
    price = data['price']
    availability = message.text

    #Подключаемся к базе данных через aiosqlite
    db = await get_db() # Дожидаемся выполнения корутины

    async with db.execute(
            "INSERT INTO premises (description, price, availability) VALUES (?, ?, ?)",
            (description, price, availability)
        ) as cursor:
            await db.commit() # СОхраняем изменения в базе данных

    await message.reply("Вы успешно добавили помещение под аренду!")
    await state.finish()

# При выборе "Я арендатор" - показ доступных слотов под аренду
@dp.message_handler(lambda message: message.text == "Я арендатор")
async def tenant_start(message: types.Message):
    async with get_db() as db:
        cursor = await db.execute("SELECT id, discription, price, availability FROM premises")
        rows = await cursor.fetchall()

        if not rows:
            await message.reply("Нет достпуных помещений для бронирования.")
            return
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for row in rows:
            slot_info = f"ID: {row[0]} | {row[3]} (Цена: {row[2]})"
            markup.add(slot_info)
        
        await message.reply("Выберите слот для бронирования:", reply_markup=markup)
        await TenantForm.booking.set()

# Сохранение бронирования в базе данных
@dp.message_handler(state=TenantForm.booking)
async def tenant_booking(message: types.Message, state: FSMContext):
    selected_slot = message.text.split(" | ")[0].split(": ")[1] #Извлекаем ID слота

    async with get_db() as db:
        await db.execute(
            "INSERT INTO bookings (tenant_id, slot) VALUES (?, ?)",
            (message.from_user.id, selected_slot)
        )
        await db.commit()

    await message.reply(f"Вы успешно забронировали слот ID: {selected_slot}")
    await state.commit()

#Запуск бота
if __name__ == '__main__':#while == TRUE
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)