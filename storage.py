import pickle
import os
import json
from users import User

class UserStorage:
    def __init__(self, filename="users_backup.pkl"):
        self.filename = filename
        self.users = {}
        self.load_data()

    def add_user(self, user_id):
        if user_id not in self.users:
            self.users[user_id] = User(user_id)
        return self.users[user_id]

    def get_user(self, user_id):
        return self.users.get(user_id)

    def save_data(self):
        with open(self.filename, "wb") as file:
            pickle.dump(self.users, file)

    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, "rb") as file:
                self.users = pickle.load(file)

class ActivitiesLoader:
    def __init__(self):
        self.activities = self.load_activities("activities.json")

    @staticmethod
    def load_activities(file_path):
        """Загружает данные из JSON-файла."""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_categories(self):
        return list(self.activities.keys())

    def get_subcategories(self, category):
        return list(self.activities.get(category, {}).keys())

    def get_activities(self, category, subcategory):
        return self.activities.get(category, {}).get(subcategory, [])