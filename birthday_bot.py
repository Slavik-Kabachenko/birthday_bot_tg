import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import threading
import time

TOKEN = "7516740132:AAHSFRZtQ77HiA5Bp_st-7PA8_-mZ7E3dJU"
bot = telebot.TeleBot(TOKEN)

user_data = {}
birthdays = {}
months = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
          "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]

# Створення меню
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("➕ Додати свій день народження"),
               KeyboardButton("📅 Список днів народження"))
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

# Функція для перевірки днів народження
def birthday_checker():
    while True:
        now = datetime.now()
        current_date = f"{now.day} {months[now.month - 1]}"
        if now.hour == 9:  # Вітання о 9:00
            for chat_id, data in birthdays.items():
                if data['date'] == current_date:
                    bot.send_message(chat_id, f"🎉 Вітаємо {data['username']} з Днем Народження! 🎂")
        time.sleep(3600)  # Перевірка щогодини

# Обробник команди /start
@bot.message_handler(commands=['start'])
def start_conversation(message):
    bot.send_message(message.chat.id, "Привіт! Обери дію:", reply_markup=main_menu())

# Обробник кнопок меню
@bot.message_handler(func=lambda message: message.text in ["➕ Додати свій день народження", "📅 Список днів народження"])
def handle_buttons(message):
    if message.text == "➕ Додати свій день народження":
        bot.send_message(message.chat.id, "Введи свій рік народження (наприклад, 2002).")
        user_data[message.chat.id] = {'step': 'year', 'username': message.from_user.username}
    elif message.text == "📅 Список днів народження":
        if birthdays:
            response = "Список днів народження:\n"
            for chat_id, data in birthdays.items():
                username = f"@{data['username']}" if data['username'] else message.from_user.first_name
                response += f"{username}: {data['date']}\n"
            bot.send_message(message.chat.id, response)
        else:
            bot.send_message(message.chat.id, "Список днів народження поки що порожній.")

# Обробник введення даних користувача
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
            bot.send_message(chat_id, "Будь ласка, введи правильний рік у форматі 4 цифр (наприклад, 2002).")
    elif step == 'month':
        if message.text in months:
            user_data[chat_id]['month'] = message.text
            bot.send_message(chat_id, "Оберіть день народження:", reply_markup=day_menu())
            user_data[chat_id]['step'] = 'day'
        else:
            bot.send_message(chat_id, "Будь ласка, вибери місяць із клавіатури.")
    elif step == 'day':
        if message.text.isdigit() and 1 <= int(message.text) <= 31:
            user_data[chat_id]['day'] = message.text
            full_date = f"{user_data[chat_id]['day']} {user_data[chat_id]['month']}"
            bot.send_message(chat_id, f"Твій день народження: {full_date}. Усе правильно?", reply_markup=confirm_menu())
            user_data[chat_id]['step'] = 'confirm'
        else:
            bot.send_message(chat_id, "Будь ласка, вибери день із клавіатури.")
    elif step == 'confirm':
        if message.text == "Так":
            username = message.from_user.username or message.from_user.first_name
            full_date = f"{user_data[chat_id]['day']} {user_data[chat_id]['month']}"
            birthdays[chat_id] = {'username': username, 'date': full_date}
            bot.send_message(chat_id, "Дякую! Твої дані збережено. 🎉", reply_markup=main_menu())
            del user_data[chat_id]
        else:
            bot.send_message(chat_id, "Давай почнемо заново. Введи свій рік народження:")
            user_data[chat_id]['step'] = 'year'

@bot.message_handler(commands=['delete_birthday'])
def delete_birthday(message):
    chat_id = message.chat.id
    if chat_id in birthdays:
        del birthdays[chat_id]
        bot.send_message(chat_id, "Ваш день народження було успішно видалено зі списку.")
    else:
        bot.send_message(chat_id, "Ви ще не додали свій день народження.")

@bot.chat_member_handler(func=lambda message: message.chat.id == message.new_chat_member.id)
def new_member(message):
    if message.new_chat_member.is_bot:
        bot.send_message(
            message.chat.id,
            "Вітаю! Я бот, який може привітати тебе з Днем Народження, навіть якщо всі забули! 🎉"
        )
# Запуск бота
threading.Thread(target=birthday_checker, daemon=True).start()
print("Бот працює...")
bot.polling()
