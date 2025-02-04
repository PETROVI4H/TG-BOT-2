import telebot
import os
import requests
import re
import pandas as pd
from telebot import types

bot = telebot.TeleBot('7174452154:AAGVz3XEPWC2nuLqhOxAg_umUbjI9q6Ehns')

uploaded_file_path = None
df = None

def sanitize_filename(file_url):
    return re.sub(r'[<>:"/\\|?*#]', '_', file_url)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Перейти в Omni', url='https://omni.top-academy.ru/login/index#/'))

    welcome_message = (
        f'Здравствуйте, {message.from_user.first_name}!\n\n'
        'Я бот, который поможет вам подсчитать количество проведенных пар для вашей группы по дисциплинам.\n\n'
        'Вот что вы можете сделать с моей помощью:\n\n'
        '1. Загрузить файл с расписанием.\n'
        '2. Просмотреть нужную информацию  — после загрузки файла используйте кнопки внизу экрана, чтобы получить список для вывода необходимых вам столбцов.\n\n'
        'Для получения дополнительной информации, используйте команду /help.\n\n'
        'Пожалуйста, выберите одну из команд ниже для продолжения.'
    )

    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)

@bot.message_handler(commands=['help'])
def about(message):
    help_message = (
        "<b><u>Информация о боте:</u></b>\n\n"
        "Этот бот поможет вам подсчитать количество проведенных пар для вашей группы по дисциплинам.\n"
        "Вот список доступных команд:\n\n"
        "<b>/start</b> - Стартовая команда, которая приветствует вас и дает инструкции по загрузке документа с расписанием.\n"
        "<b>/help</b> - Выводит информацию о доступных функциях бота.\n"
        "<b>/url</b> - Позволяет отправить ссылку на файл с расписанием (например, Excel, CSV и другие).\n"
        "<b>/file</b> - Позволяет загрузить файл с расписанием прямо в чат.\n"
        "<b>/pairs</b> - Показывает количество проведенных пар для вашей группы по дисциплинам.\n"
        "<b>/warnings</b> - Выводит предупреждения по преподавателям с посещаемостью ниже 65%.\n\n"
        "<b>Как работать с ботом:</b>\n"
        '1. Загрузить файл с расписанием.\n'
        '2. Просмотреть нужную информацию  — после загрузки файла используйте кнопки внизу экрана, чтобы получить список для вывода необходимых вам столбцов.\n\n'
    )
    bot.send_message(message.chat.id, help_message, parse_mode='html')

@bot.message_handler(commands=['url'])
def ask_for_url(message):
    bot.send_message(message.chat.id, "Пожалуйста, отправьте ссылку на файл с расписанием. Это может быть файл в формате Excel, CSV и другие поддерживаемые форматы.")

@bot.message_handler(commands=['file'])
def ask_for_file(message):
    bot.send_message(message.chat.id, "Пожалуйста, отправьте файл с расписанием в формате Excel или CSV.")

@bot.message_handler(func=lambda message: message.text.startswith('http'))
def handle_url(message):
    global uploaded_file_path, df

    file_url = message.text.strip()

    try:
        response = requests.get(file_url)

        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()

            if 'excel' in content_type:
                user_id = message.from_user.id
                user_dir = f'./user_files/{user_id}'

                os.makedirs(user_dir, exist_ok=True)

                file_name = sanitize_filename(file_url.split("/")[-1])
                file_path = os.path.join(user_dir, file_name)

                with open(file_path, 'wb') as f:
                    f.write(response.content)

                try:
                    df = pd.read_excel(file_path, engine="openpyxl")
                    uploaded_file_path = file_path
                    bot.send_message(message.chat.id, f"Файл Excel загружен: {file_name}. Пример данных:\n{df.head()}")
                    offer_column_selection(message)
                except Exception as e:
                    bot.send_message(message.chat.id, f"Ошибка при обработке Excel файла: {e}")
                    return
            else:
                bot.send_message(message.chat.id, "Файл имеет неподдерживаемый формат или не может быть проанализирован.")
        else:
            bot.send_message(message.chat.id, "Не удалось загрузить файл по предоставленной ссылке. Пожалуйста, проверьте ссылку.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при обработке файла: {e}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    global uploaded_file_path, df

    file_info = bot.get_file(message.document.file_id)
    file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}'
    file_name = message.document.file_name

    try:
        response = requests.get(file_url)

        if response.status_code == 200:
            user_id = message.from_user.id
            user_dir = f'./user_files/{user_id}'

            os.makedirs(user_dir, exist_ok=True)

            sanitized_file_name = sanitize_filename(file_name)
            file_path = os.path.join(user_dir, sanitized_file_name)

            with open(file_path, 'wb') as f:
                f.write(response.content)

            try:
                df = pd.read_excel(file_path, engine="openpyxl")
                uploaded_file_path = file_path
                bot.send_message(message.chat.id, f"Файл загружен: {sanitized_file_name}. Пример данных:\n{df.head()}")
                offer_column_selection(message)
            except Exception as e:
                bot.send_message(message.chat.id, f"Ошибка при обработке Excel файла: {e}")
                return
        else:
            bot.send_message(message.chat.id, "Не удалось загрузить файл. Пожалуйста, попробуйте снова.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при обработке документа: {e}")

def offer_column_selection(message):
    if df is not None:
        subject_columns = [col for col in df.columns]
        if subject_columns:
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            for column in subject_columns:
                markup.add(types.KeyboardButton(column))
            markup.add(types.KeyboardButton("Отмена"))
            bot.send_message(message.chat.id, "Выберите столбец для отображения данных:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "В файле нет столбцов для отображения.")

@bot.message_handler(func=lambda message: message.text in df.columns)
def show_column_data(message):
    if df is None:
        bot.send_message(message.chat.id, "Сначала загрузите файл с расписанием с помощью команды /url или /file.")
        return

    column_name = message.text

    if column_name == "Отмена":
        bot.send_message(message.chat.id, "Отмена выбора.")
        return

    column_data = df[column_name].to_list()
    column_data_str = "\n".join(str(item) for item in column_data)

    bot.send_message(message.chat.id, f"Данные для столбца {column_name}:\n{column_data_str}")

@bot.message_handler(commands=['warnings'])
def show_warnings(message):
    if df is None:
        bot.send_message(message.chat.id, "Сначала загрузите файл с расписанием с помощью команды /url или /file.")
        return

    if 'ФИО преподавателя' not in df.columns:
        bot.send_message(message.chat.id, "В файле отсутствует столбец 'ФИО преподавателя'.")
        return

    warnings = []
    for _, row in df.iterrows():
        attendance_value = str(row['Средняя посещаемость']).strip()
        if '%' in attendance_value:
            try:
                attendance_percentage = float(attendance_value.replace('%', '').strip())
                if attendance_percentage < 65:
                    warnings.append(f"{row['ФИО преподавателя']}: посещаемость {attendance_percentage}%")
            except ValueError:
                continue
        else:
            continue

    if warnings:
        bot.send_message(message.chat.id, "Предупреждения по посещаемости ниже 65%:\n" + "\n".join(warnings))
    else:
        bot.send_message(message.chat.id, "Все преподаватели имеют посещаемость выше 65%.")

bot.polling(none_stop=True)