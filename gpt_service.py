from openai import AsyncOpenAI
from aiogram.types import Message

import re

import re

def convert_to_html(text: str) -> str:
    if not text:
        return ""

    # **Жирный текст** → <b>текст</b>
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

    # *Курсив* → <i>текст</i>
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)

    # ***Жирный курсив*** → <b><i>текст</i></b>
    text = re.sub(r"\*\*\*(.*?)\*\*\*", r"<b><i>\1</i></b>", text)

    # `Моноширинный текст` → <code>текст</code>
    text = re.sub(r"`(.*?)`", r"<code>\1</code>", text)

    # [Текст ссылки](https://example.com) → <a href="https://example.com">Текст ссылки</a>
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', text)

    return text



class GPTService:
    def __init__(self, api_key):
        self.client = AsyncOpenAI(api_key=api_key)
        self.user_sessions = {}  # Хранение истории сообщений пользователей

    async def get_suggestions(self, user_data, category, subcategory, additional_text=None):
        user_id = user_data.get("user_id")  # Исправлено (было "id")
        
        # ✅ Создаём историю диалога для нового пользователя
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = [{"role": "system", "content": "Ты дружелюбный чат-бот общающийся с подростком. запоминай контекст диалога и отвечай последовательно. Если пользователь ссылается на прошлое сообщение, учитывай его в ответе."}]

        prompt = (
            f"Пользователь:\n"
            f"Имя: {user_data.get('name', 'Неизвестно')}\n"
            f"Возраст: {user_data.get('age', 'Неизвестно')}\n"
            f"Интересы: {user_data.get('interests', 'Не указаны')}\n\n"
            f"Выбранная категория: {category}\n"
            f"Подкатегория: {subcategory}\n\n"
        )
        if additional_text:
            prompt += f"Адаптируй категории под пользователя: {additional_text}\n\n"
        
        prompt += "Предложи 5 идей для этого пользователя. Если они не подходят, предложи еще по 3."

        # ✅ Добавляем сообщение пользователя в историю
        self.user_sessions[user_id].append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.user_sessions[user_id]
            )
            reply = convert_to_html(response.choices[0].message.content.strip())
            
            # ✅ Добавляем ответ GPT в историю
            self.user_sessions[user_id].append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            return f"Ошибка при обращении к GPT: {e}"

    async def chat_gpt_response(self, message: Message):
        """ Отправляет запрос в ChatGPT и получает ответ """
        user_id = message.from_user.id
        user_message = message.text

        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = [{"role": "system", "content": "Ты дружелюбный чат-бот."}]


        # ✅ Добавляем сообщение пользователя в историю
        self.user_sessions[user_id].append({"role": "user", "content": user_message})

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.user_sessions[user_id]
            )

            reply = convert_to_html(response.choices[0].message.content) # Получаем текст ответа
            
            # ✅ Добавляем ответ GPT в историю
            self.user_sessions[user_id].append({"role": "assistant", "content": reply})

            return reply
        except Exception as e:
            return f"Ошибка GPT: {e}"
