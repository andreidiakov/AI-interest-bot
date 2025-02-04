from datetime import datetime
import asyncio
import random
from aiogram.types import Message, FSInputFile

class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.name = None
        self.age = None
        self.interests = None
        self.agreed = False
        self.gpt_status = False 
        self.selected_category = None  
        self.selected_subcategory = None  
        self.motivation_available = True #можно присылать
        self.last_interaction = datetime.now()

    def set_name(self, name):
        self.name = name

    def set_age(self, age):
        self.age = age

    def set_interests(self, interests):
        self.interests = interests

    def set_agreement(self, agreed):
        self.agreed = agreed

    def set_gpt_status(self, status):
        self.gpt_status = status
    
    def update_last_interaction(self):
        self.last_interaction = datetime.now()
    
    #Сбрасывает все данные пользователя, кроме согласия с условиями.
    def reset_data(self):
        self.name = None
        self.age = None
        self.interests = None
        self.selected_category = None
        self.selected_subcategory = None
        self.gpt_status = False

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "age": self.age,
            "interests": self.interests,
            "agreed": self.agreed,
            "last_interaction": self.last_interaction.strftime("%Y-%m-%d %H:%M:%S"),
        }
    
    def should_send_motivation(self, probability=0.5):
        return self.motivation_available and (random.random() < probability) # вероятность
