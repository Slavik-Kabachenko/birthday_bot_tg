import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import threading
import time
import pytz
import requests

TOKEN = "7516740132:AAHSFRZtQ77HiA5Bp_st-7PA8_-mZ7E3dJU"
TIMEZONE_API_URL = "http://worldtimeapi.org/api/timezone/"
bot = telebot.TeleBot(TOKEN)

user_data = {}
birthdays = {}
months = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = KeyboardButton("➕ Додати свій день народження")
    btn2 = KeyboardButton("📅 Список днів народження")
    markup.add(btn1, btn2)
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

def gender_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("Чоловік"), KeyboardButton("Жінка"))
    return markup

def confirm_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("Так"), KeyboardButton("Ні"))
    return markup

def get_local_time(city):
    try:
        response = requests.get(TIMEZONE_API_URL)
        if response.status_code == 200:
            timezones = response.json()
            for tz in timezones:
                if city.lower() in tz.lower():
                    timezone = pytz.timezone(tz)
                    return datetime.now(timezone).strftime('%d %B, %H:%M')
        return "Не вдалося визначити часовий пояс"
    except Exception:
        return "Не вдалося визначити часовий пояс"

def birthday_checker():
    while True:
        now = datetime.now()
        for chat_id, data in birthdays.items():
            city = data['city']
            try:
                local_time = get_local_time(city)
                if "Не вдалося" not in local_time:
                    local_hour = int(local_time.split(', ')[1].split(':')[0])
                    if local_hour == 9:
                        bot.send_message(chat_id, f"🎉 Вітаємо {data['username']} з Днем Народження! 🎂")
            except Exception as e:
                print(f"Помилка з часовим поясом для {city}: {e}")
        time.sleep(60)

@bot.message_handler(commands=['start'])
def start_conversation(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Привіт! Обери дію:", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text in ["➕ Додати свій день народження", "📅 Список днів народження"])
def handle_buttons(message):
    chat_id = message.chat.id
    if message.text == "➕ Додати свій день народження":
        bot.send_message(chat_id, "Давай почнемо з твого року народження. Введи 4 цифри (наприклад, 2002).")
        user_data[chat_id] = {'step': 'year', 'username': message.from_user.username}
    elif message.text == "📅 Список днів народження":
        if birthdays:
            response = "Список днів народження:\n"
            markup = InlineKeyboardMarkup()
            for user_chat_id, data in birthdays.items():  # Фікс: заміна chat_id на user_chat_id
                username = data['username']
                profile_url = f"tg://user?id={user_chat_id}"  # Вказуємо ID користувача для відкриття профілю
                button = InlineKeyboardButton(f"{username} - {data['date']}", url=profile_url)
                markup.add(button)
            bot.send_message(chat_id, response, reply_markup=markup)  # Відправляємо відповідь саме тому, хто натиснув кнопку
        else:
            response = "Список днів народження поки що порожній."
            bot.send_message(chat_id, response)

@bot.message_handler(func=lambda message: message.chat.id in user_data)
def process_info(message):
    chat_id = message.chat.id
    step = user_data[chat_id]['step']

    if step == 'year':
        if message.text.isdigit() and len(message.text) == 4:
            user_data[chat_id]['year'] = message.text
            bot.send_message(chat_id, "Гаразд! Тепер вибери місяць народження:", reply_markup=month_menu())
            user_data[chat_id]['step'] = 'month'
        else:
            bot.send_message(chat_id, "Будь ласка, введи правильний рік у форматі 4 цифр (наприклад, 2002).")
    elif step == 'month':
        if message.text in months:
            user_data[chat_id]['month'] = message.text
            bot.send_message(chat_id, "Чудово! Тепер вибери день народження:", reply_markup=day_menu())
            user_data[chat_id]['step'] = 'day'
        else:
            bot.send_message(chat_id, "Будь ласка, вибери місяць з клавіатури.", reply_markup=month_menu())
    elif step == 'day':
        if message.text.isdigit() and 1 <= int(message.text) <= 31:
            user_data[chat_id]['day'] = message.text
            bot.send_message(chat_id, "Вкажи свою стать:", reply_markup=gender_menu())
            user_data[chat_id]['step'] = 'gender'
        else:
            bot.send_message(chat_id, "Будь ласка, вибери день з клавіатури.", reply_markup=day_menu())
    elif step == 'gender':
        if message.text in ["Чоловік", "Жінка"]:
            user_data[chat_id]['gender'] = message.text
            bot.send_message(chat_id, "Вкажи місто, в якому проживаєш.")
            user_data[chat_id]['step'] = 'city'
        else:
            bot.send_message(chat_id, "Будь ласка, вибери стать з клавіатури.", reply_markup=gender_menu())
    elif step == 'city':
        user_data[chat_id]['city'] = message.text
        local_time = get_local_time(message.text)
        full_date = f"{user_data[chat_id]['day']} {user_data[chat_id]['month']}"
        bot.send_message(
            chat_id,
            f"Ти знаходишся в місті {message.text}. Твій день народження {full_date}. Все правильно?",
            reply_markup=confirm_menu()
        )
        user_data[chat_id]['step'] = 'confirm'
    elif step == 'confirm':
        if message.text == "Так":
            username = message.from_user.username if message.from_user.username else message.from_user.first_name
            chat_city = user_data[chat_id]['city']
            full_date = f"{user_data[chat_id]['day']} {user_data[chat_id]['month']} {user_data[chat_id]['year']}"

            # Збереження у список днів народження
            birthdays[chat_id] = {
                'username': username,
                'date': full_date,
                'city': chat_city
            }

            bot.send_message(
                chat_id,
                f"Дякую! Твої дані збережено. 🎉",
                reply_markup=main_menu()  # Повертаємо головне меню
            )

            del user_data[chat_id]  # Очищаємо тимчасові дані користувача
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

threading.Thread(target=birthday_checker, daemon=True).start()
print("Бот працює...")
bot.polling()
