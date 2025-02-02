from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def generate_keyboard(options, include_back=False):
    """Генерирует клавиатуру на основе списка опций."""
    keyboard = [[KeyboardButton(text=option)] for option in options]
    
    if include_back:
        keyboard.append([KeyboardButton(text="Назад")])  # Добавляем кнопку "Назад"
    
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=keyboard)

