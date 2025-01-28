import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import sqlite3
import threading
import time

# 🔑 Токен бота
TOKEN = "7563338858:AAFRqa2583ScPdIf4G76Wgsy8wP4B0_3O-Y"
bot = telebot.TeleBot(TOKEN)

# 📅 Місяці
months = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
          "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]

# 🗂 Підключення до бази
conn = sqlite3.connect("birthdays.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS birthdays (
                    chat_id INTEGER PRIMARY KEY,
                    username TEXT,
                    date TEXT)''')
conn.commit()

user_data = {}

# 📌 Функція для збереження дня народження в базі
def save_birthday(chat_id, username, date):
    cursor.execute("INSERT OR REPLACE INTO birthdays (chat_id, username, date) VALUES (?, ?, ?)",
                   (chat_id, username, date))
    conn.commit()

# 📌 Функція для отримання списку днів народження
def get_birthdays():
    cursor.execute("SELECT username, date FROM birthdays")
    return cursor.fetchall()

# 📌 Функція для видалення дня народження
def delete_birthday(chat_id):
    cursor.execute("DELETE FROM birthdays WHERE chat_id = ?", (chat_id,))
    conn.commit()

# 📌 Головне меню
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("➕ Додати свій день народження"),
               KeyboardButton("📅 Список днів народження"),
               KeyboardButton("❌ Видалити свій день народження"))
    return markup

def month_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [KeyboardButton(month) for month in months]
    markup.add(*buttons)
    return markup

def day_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    buttons = [KeyboardButton(str(day)) for day in range(1, 32)]
    markup.add(*buttons)
    return markup

def confirm_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Так"), KeyboardButton("Ні"))
    return markup

# 🎉 Функція для перевірки та надсилання привітань
def birthday_checker():
    while True:
        now = datetime.now()
        current_date = f"{now.day} {months[now.month - 1]}"
        if now.hour == 9:  # Перевіряти о 9:00
            cursor.execute("SELECT chat_id, username FROM birthdays WHERE date = ?", (current_date,))
            for chat_id, username in cursor.fetchall():
                bot.send_message(chat_id, f"🎉 Вітаємо @{username} з Днем Народження! 🎂")
        time.sleep(3600)  # Перевіряти щогодини

# 🏁 Обробник команди /start
@bot.message_handler(commands=['start'])
def start_conversation(message):
    bot.send_message(message.chat.id, "Привіт! Обери дію:", reply_markup=main_menu())

# 📜 Обробник кнопки "📅 Список днів народження"
@bot.message_handler(func=lambda message: message.text == "📅 Список днів народження")
def list_birthdays(message):
    birthday_list = get_birthdays()
    if birthday_list:
        response = "🎂 Список днів народження:\n"
        for username, date in birthday_list:
            response += f"@{username}: {date}\n"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "Список днів народження поки що порожній.")

# ➕ Додавання дня народження
@bot.message_handler(func=lambda message: message.text == "➕ Додати свій день народження")
def add_birthday(message):
    bot.send_message(message.chat.id, "Введи свій рік народження (наприклад, 2002).")
    user_data[message.chat.id] = {'step': 'year', 'username': message.from_user.username}

# ❌ Видалення дня народження
@bot.message_handler(func=lambda message: message.text == "❌ Видалити свій день народження")
def remove_birthday(message):
    chat_id = message.chat.id
    delete_birthday(chat_id)
    bot.send_message(chat_id, "Ваш день народження успішно видалено зі списку.")

# 📝 Обробка введених користувачем даних
@bot.message_handler(func=lambda message: message.chat.id in user_data)
def process_info(message):
    chat_id = message.chat.id
    step = user_data[chat_id]['step']

    if step == 'year':
        if message.text.isdigit() and len(message.text) == 4:
            user_data[chat_id]['year'] = message.text
            bot.send_message(chat_id, "Оберіть місяць народження:", reply_markup=month_menu())
            user_data[chat_id]['step'] = 'month'
        else:
            bot.send_message(chat_id, "Будь ласка, введіть рік у форматі 4 цифр (наприклад, 2002).")

    elif step == 'month':
        if message.text in months:
            user_data[chat_id]['month'] = message.text
            bot.send_message(chat_id, "Оберіть день народження:", reply_markup=day_menu())
            user_data[chat_id]['step'] = 'day'
        else:
            bot.send_message(chat_id, "Будь ласка, виберіть місяць із клавіатури.")

    elif step == 'day':
        if message.text.isdigit() and 1 <= int(message.text) <= 31:
            user_data[chat_id]['day'] = message.text
            full_date = f"{user_data[chat_id]['day']} {user_data[chat_id]['month']}"
            bot.send_message(chat_id, f"Твій день народження: {full_date}. Усе правильно?", reply_markup=confirm_menu())
            user_data[chat_id]['step'] = 'confirm'
        else:
            bot.send_message(chat_id, "Будь ласка, виберіть день із клавіатури.")

    elif step == 'confirm':
        if message.text == "Так":
            username = message.from_user.username or message.from_user.first_name
            full_date = f"{user_data[chat_id]['day']} {user_data[chat_id]['month']}"
            save_birthday(chat_id, username, full_date)
            bot.send_message(chat_id, "Дякую! Твої дані збережено. 🎉", reply_markup=main_menu())
            del user_data[chat_id]
        else:
            bot.send_message(chat_id, "Давай почнемо заново. Введи свій рік народження:")
            user_data[chat_id]['step'] = 'year'

# 🚀 Запуск бота та потокового перевірника днів народження
threading.Thread(target=birthday_checker, daemon=True).start()
print("Бот працює...")
bot.polling()
