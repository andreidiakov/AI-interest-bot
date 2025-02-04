import asyncio
import os
import random
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile
from aiogram.filters import Command
from storage import UserStorage, ActivitiesLoader
from keyboard import generate_keyboard
from gpt_service import GPTService

load_dotenv() 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
user_storage = UserStorage()
activities_loader = ActivitiesLoader()
gpt_requests = GPTService(OPENAI_API_KEY)

motivation_on = True
probability = 0.5
delay = 15 #*60 - тест

async def send_info(message: Message):
    image = FSInputFile("image.png")
    info_text = (
                "Я — твой интеллектуальный помощник и знаю сотни способов, как прогнать скуку. "+
                "Давай вместе найдём для тебя увлекательное занятие — рисование, игры, эксперименты или что-то совсем новое.\n\n"+
                "Готов попробовать? Тогда начинаем!"
            )
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=image,
        caption=info_text,
        reply_markup=generate_keyboard(MAIN_MENU_OPTIONS)
    )

async def send_random_motivation_image(message: Message):
    #Отправляет случайную мотивационную картинку, если прошло 5 минут.
    user = user_storage.add_user(message.from_user.id)
    user.motivation_available = False # Блокируем повторную отправку
    await asyncio.sleep(delay)

    random.seed(None) 
    image_number = random.randint(1, 5)
    image_path = f"image_{image_number}.png"
    try:
        image = FSInputFile(image_path)
        await bot.send_photo(
            chat_id=message.chat.id,
            photo = image)
        print(f"[LOG] Пользователю {user.user_id}: отправили {image_path}")
        user.motivation_available = True
    except FileNotFoundError:
        print(f"[WARNING] Изображение {image_path} не найдено.")

# Команда возврата в главное меню
MAIN_MENU_OPTIONS = ["Начать!", "Профиль", "О боте"]
PROFILE_MENU_OPTIONS = ["Изменить данные", "Назад"]

# Логирование для консоли
def log_to_console(user_id: int, message: str):
    """Выводит техническое сообщение в консоль."""
    print(f"[LOG] Пользователь {user_id}:\n{message}")


# Обработчик команды /start
@dp.message(Command(commands=["start"]))
async def start_command(message: Message):
    user = user_storage.add_user(message.from_user.id)

    if not user.agreed:
        agreement_text = (
            "Добро пожаловать! Прежде чем продолжить, "
            "вы должны согласиться с пользовательским соглашением: "
            "https://drive.google.com/file/d/1einPlu7V560Jb7v8npiCqqsr7b54L6Z4/view?usp=drive_link\n\n"
            "Нажмите 'Согласен', чтобы продолжить, или 'Не согласен', чтобы выйти."
        )
        await message.answer(agreement_text, reply_markup=generate_keyboard(["Согласен", "Не согласен"]))
        log_to_console(message.from_user.id, "Пользователь начал взаимодействие, ожидается согласие.")
    else:
        await send_info(message)
        log_to_console(message.from_user.id, "Пользователь повторно использует команду /start.")


# Обработчик команды /main
@dp.message(Command(commands=["main"]))
async def main_menu_command(message: Message):
    user = user_storage.get_user(message.from_user.id)

    if not user:
        await message.answer("Пожалуйста, начните с команды /start.")
        log_to_console(message.from_user.id, "Попытка использовать /main без предварительного старта.")
        return

    keyboard = generate_keyboard(MAIN_MENU_OPTIONS)
    await message.answer("Вы в главном меню. Выберите действие:", reply_markup=keyboard)
    log_to_console(message.from_user.id, "Пользователь вернулся в главное меню.")


# Обработка профиля
@dp.message()
async def handle_message(message: Message):
    user = user_storage.get_user(message.from_user.id)

    if not user:
        await message.answer("Пожалуйста, начните c команды /start.")
        log_to_console(message.from_user.id, "Пользователь не найден, предложено использовать /start.")
        return

    # Обработка согласия
    if not user.agreed:
        if message.text == "Согласен":
            user.set_agreement(True)
            user_storage.save_data()
            await message.answer("Отлично! Напишите своё имя, чтобы начать.", reply_markup=ReplyKeyboardRemove())
            log_to_console(message.from_user.id, "Пользователь согласился с пользовательским соглашением.")
        elif message.text == "Не согласен":
            await message.answer("Вы отказались от пользовательского соглашения. До свидания!")
            log_to_console(message.from_user.id, "Пользователь отказался от пользовательского соглашения.")
        else:
            keyboard = generate_keyboard(["Согласен", "Не согласен"])
            await message.answer("Пожалуйста, выберите 'Согласен' или 'Не согласен'.", reply_markup=keyboard)
            log_to_console(message.from_user.id, f"Некорректный ввод: {message.text}")
        return

    if user.should_send_motivation(probability):
        asyncio.create_task(send_random_motivation_image(message))

    # Если включён статус GPT, перенаправляем все сообщения в GPT (кроме команды "Назад")
    if user.gpt_status == True and message.text != "Назад":
        response = await gpt_requests.chat_gpt_response(message)
        await message.answer(response, parse_mode="HTML")
        log_to_console(user.user_id, f"Сообщение отправлено в GPT: {message.text}")
        return
    elif user.gpt_status != False:
        user.set_gpt_status(False)
        subcategories = activities_loader.get_subcategories(user.selected_category)
        await message.answer("Выберите подкатегорию:", reply_markup=generate_keyboard(subcategories, include_back=True))
        return

    
    # Сбор имени
    if not user.name:
        user.set_name(message.text)
        user_storage.save_data()
        await message.answer(f"Приятно познакомиться, {user.name}! Сколько вам лет?", reply_markup=ReplyKeyboardRemove())
        log_to_console(message.from_user.id, f"Указано имя: {user.name}")
        return

    # Сбор возраста
    if not user.age:
        if not message.text.isdigit():
            await message.answer("Пожалуйста, укажите возраст целым числом.")
            log_to_console(message.from_user.id, f"Некорректный ввод возраста: {message.text}")
        else:
            user.set_age(int(message.text))
            user_storage.save_data()
            await message.answer("Чем вы увлекаетесь?")
            log_to_console(message.from_user.id, f"Указан возраст: {user.age}")
        return

    # Сбор увлечений
    if not user.interests:
        user.set_interests(message.text)
        user_storage.save_data()
        keyboard = generate_keyboard(MAIN_MENU_OPTIONS)
        await message.answer(
            f"Спасибо за информацию, {user.name} ({user.age} лет), увлекающийся {user.interests}!\n",
            reply_markup=keyboard,
        )
        await send_info(message)
        log_to_console(message.from_user.id, f"Указаны увлечения: {user.interests}")
        return

    # Выбор категории
    if message.text in activities_loader.get_categories():
        user.selected_category = message.text
        subcategories = activities_loader.get_subcategories(message.text)
        await message.answer("Выберите подкатегорию:", reply_markup=generate_keyboard(subcategories, include_back=True))
        return

    # Выбор подкатегории
    if message.text in activities_loader.get_subcategories(user.selected_category):
        user.selected_subcategory = message.text
        user.set_gpt_status(True)
        response = await gpt_requests.get_suggestions(
            user_data=user.to_dict(),
            category=user.selected_category,
            subcategory=user.selected_subcategory,
            additional_text= activities_loader.get_activities(user.selected_category, message.text)
        )
        await message.answer(f"{response}",parse_mode="HTML" )
        log_to_console(user.user_id, f"Сообщение отправлено в GPT: {message.text}")
        await message.answer(
            "Что вас заинтересовало? \nВы также можете нажать 'Назад', если хотите выйти из режима диалога",
            reply_markup=generate_keyboard(["Назад"]),
        )
        return
    
    # Главное меню
    if message.text == "Начать!":
        subcategories = activities_loader.get_categories()
        await message.answer("Выберите категорию:", reply_markup=generate_keyboard(subcategories, include_back=True))
        log_to_console(message.from_user.id, "Пользователь выбрал 'Начать'.")
    elif message.text == "О боте":
        await send_info(message)
        log_to_console(message.from_user.id, "Пользователь выбрал 'О боте'.")
    elif message.text == "Профиль":
        keyboard = generate_keyboard(PROFILE_MENU_OPTIONS)
        await message.answer(
            f"Ваш профиль:\n\n"
            f"Имя: {user.name}\n"
            f"Возраст: {user.age}\n"
            f"Увлечения: {user.interests}\n\n"
            "Хотите изменить данные?",
            reply_markup=keyboard,
        )
        log_to_console(message.from_user.id, "Пользователь открыл профиль.")
    elif message.text == "Изменить данные":
        user.reset_data()
        user_storage.save_data()
        await message.answer("Давайте начнём заново! Как вас зовут?", reply_markup=ReplyKeyboardRemove)
        log_to_console(message.from_user.id, "Пользователь начал изменение данных.")
    elif message.text == "Назад":
        keyboard = generate_keyboard(MAIN_MENU_OPTIONS)
        await message.answer("Вы вернулись в главное меню.", reply_markup=keyboard)
        log_to_console(message.from_user.id, "Пользователь вернулся в главное меню.")
    else:
        keyboard = generate_keyboard(MAIN_MENU_OPTIONS)
        await message.answer("Выберите действие из меню.", reply_markup=keyboard)
        log_to_console(message.from_user.id, f"Некорректный ввод в главном меню: {message.text}")


# Запуск бота
async def main():
    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
