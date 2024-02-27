import os

os.system("pip install -r requirements.txt")

# bot.py
import os
import json
from PIL import Image
from pyzbar.pyzbar import decode
import telebot
import sqlite3
from telebot import types
from config import TOKEN, TEACHER, OWNER
from colorama import Fore, Back, Style
import qrcode
from io import BytesIO
import json
import subprocess

os.system("cls")

bot = telebot.TeleBot(TOKEN)
DB_FILE = 'accounts.db'
last_found_user_id = None

def prm(chatid):
    bot.send_message(chatid, "🚫 Отказано в доступе!\nПричина: Недостаточно полномочий")

def create_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            ID INTEGER PRIMARY KEY,
            Balance INTEGER,
            Name TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_balance_name(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT Balance, Name FROM accounts WHERE ID = ?', (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None)

def update_balance_name(chat_id, new_balance, name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO accounts (ID, Balance, Name) VALUES (?, ?, ?)', (chat_id, new_balance, name))
    
    # Если баланс уже существует, не обновляем его до 0
    if new_balance != 0:
        cursor.execute('UPDATE accounts SET Balance = ? WHERE ID = ?', (new_balance, chat_id))
    
    conn.commit()
    cursor.execute('SELECT Balance FROM accounts WHERE ID = ?', (chat_id,))
    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_id_by_name(name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT ID FROM accounts WHERE Name = ?', (name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_balance(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT Balance FROM accounts WHERE ID = ?', (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_balance(chat_id, new_balance):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO accounts (ID, Balance) VALUES (?, ?)', (chat_id, new_balance))
    cursor.execute('UPDATE accounts SET Balance = ? WHERE ID = ?', (new_balance, chat_id))
    conn.commit()
    cursor.execute('SELECT Balance FROM accounts WHERE ID = ?', (chat_id,))
    result = cursor.fetchone()[0]
    conn.close()
    return result

def get_students():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT Name, ID FROM accounts WHERE ID != ?', (TEACHER,))
    students = cursor.fetchall()
    conn.close()
    return students

@bot.message_handler(commands=['start'])
def handle_start(message):
    create_table()
    user_id = message.chat.id

    if user_id == TEACHER:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("🔻 Списать")
        item2 = types.KeyboardButton("🔺 Пополнить")
        item3 = types.KeyboardButton("Баланс")
        item4 = types.KeyboardButton("🔍 Поиск по имени")
        item5 = types.KeyboardButton("🛍 Покупки")
        item6 = types.KeyboardButton("📢 Объявление")
        markup.add(item1, item2, item3, item4, item5, item6)

        bot.send_message(user_id, "Добро пожаловать!", reply_markup=markup)
    else:
        balance, name = get_balance_name(user_id)

        if balance is None:
            bot.send_message(user_id, "Добро пожаловать! Для завершения регистрации, укажите вашу фамилию и имя:")
            bot.register_next_step_handler(message, process_registration)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton("🔒 Мой счёт")
            item2 = types.KeyboardButton("♻️ Перевод")
            item3 = types.KeyboardButton("🔍 Поиск")
            item4 = types.KeyboardButton("🛍 Покупки")
            item5 = types.KeyboardButton(last_found_user_id)
            
            if last_found_user_id == None:
                markup.add(item1, item2, item3, item4)
            else:
                markup.add(item1, item2, item3, item4, item5)

            bot.send_message(user_id, f"Добро пожаловать, {name}!\nВаш счёт:\nID: {user_id}\nБаланс: {balance} баллов", reply_markup=markup)


def process_registration(message):
    user_id = message.chat.id
    name = message.text

    # Обновляем имя пользователя в базе данных
    update_balance_name(user_id, 0, name)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("🔒 Мой счёт")
    item2 = types.KeyboardButton("♻️ Перевод")
    item3 = types.KeyboardButton("🔍 Поиск")
    item4 = types.KeyboardButton(last_found_user_id)
    if last_found_user_id != None:
        markup.add(item1, item2, item3, item4)

    else:
        markup.add(item1, item2, item3)

    bot.send_message(user_id, f"Регистрация завершена, {name}!\nВаш счёт:\nID: {user_id}\nБаланс: 0 баллов", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔍 Поиск по имени")
def handle_teacher_search_by_name(message):
    if message.chat.id == TEACHER:
        bot.send_message(message.chat.id, "Введите имя для поиска:")
        bot.register_next_step_handler(message, process_teacher_search_by_name)
    else:
        prm(message.chat.id)

def process_teacher_search_by_name(message):
    name = message.text
    user_id = get_id_by_name(name)

    if user_id is not None:
        balance, _ = get_balance_name(user_id)
        global last_found_user_id
        last_found_user_id = user_id

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("🔻 Списать")
        item2 = types.KeyboardButton("🔺 Пополнить")
        item3 = types.KeyboardButton("Баланс")
        item4 = types.KeyboardButton("🔍 Поиск по имени")
        item5 = types.KeyboardButton("🛍 Покупки")
        item6 = types.KeyboardButton("📢 Объявление")
        markup.add(item1, item2, item3, item4, item5, item6)

        bot.send_message(message.chat.id, f"Пользователь {name} найден!\nID: {user_id}\nБаланс: {balance} баллов.", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, f"Пользователь {name} не найден.")

# Обработчики для учителя (TEACHER)
@bot.message_handler(func=lambda message: message.text == "🔻 Списать")
def handle_teacher_withdraw(message):
    if message.chat.id == TEACHER:
        bot.send_message(message.chat.id, "Введите номер счёта:")
        bot.register_next_step_handler(message, process_teacher_withdraw_account)

    else:
        prm(message.chat.id)

def process_teacher_withdraw_account(message):
    account_id = int(message.text)
    bot.send_message(message.chat.id, "Введите сумму для списания:")
    bot.register_next_step_handler(message, process_teacher_withdraw_amount, account_id)

def process_teacher_withdraw_amount(message, account_id):
    try:
        amount = int(message.text)
        account_balance = get_balance(account_id)

        if account_balance is not None and account_balance >= amount:
            updated_account_balance = update_balance(account_id, account_balance - amount)
            bot.send_message(message.chat.id, f"Списание выполнено!")
            bot.send_message(account_id, f"Списание {amount} баллов с счёта {account_id} выполнено!\nТекущий баланс: {updated_account_balance} баллов\nСтатус: ✅")
        else:
            bot.send_message(message.chat.id, "Ошибка: Недостаточно средств на счету.")
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка: Введите корректное число.")

@bot.message_handler(func=lambda message: message.text == "🔺 Пополнить")
def handle_teacher_deposit(message):
    if message.chat.id == TEACHER:
        bot.send_message(message.chat.id, "Введите номер счёта:")
        bot.register_next_step_handler(message, process_teacher_deposit_account)
    else:
        prm(message.chat.id)

def process_teacher_deposit_account(message):
    account_id = int(message.text)
    bot.send_message(message.chat.id, "Введите сумму для пополнения:")
    bot.register_next_step_handler(message, process_teacher_deposit_amount, account_id)

def process_teacher_deposit_amount(message, account_id):
    try:
        amount = int(message.text)
        if amount > 0:
            account_balance = get_balance(account_id) or 0
            updated_account_balance = update_balance(account_id, account_balance + amount)
            bot.send_message(message.chat.id, f"Пополнение выполнено!")
            bot.send_message(account_id, f"Пополнение {amount} баллов на счёт {account_id} выполнено!\nТекущий баланс: {updated_account_balance} баллов\nСтатус: ✅")
        else:
            bot.send_message(message.chat.id, "Ошибка: Введите положительное число.")
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка: Введите корректное число.")

@bot.message_handler(func=lambda message: message.text == "Баланс")
def handle_teacher_check_balance(message):
    if message.chat.id == TEACHER:
        bot.send_message(message.chat.id, "Введите номер счёта:")
        bot.register_next_step_handler(message, process_teacher_check_balance)

    else:
        prm(message.chat.id)

def process_teacher_check_balance(message):
    account_id = int(message.text)
    account_balance = get_balance(account_id)

    if account_balance is not None:
        bot.send_message(message.chat.id, f"Баланс счёта {account_id}: {account_balance} баллов.")
    else:
        bot.send_message(message.chat.id, "Ошибка: Счет не найден.")

# Обработчики для обычных пользователей
@bot.message_handler(func=lambda message: message.text == "🔒 Мой счёт")
def handle_my_account(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("🔙")
    item2 = types.KeyboardButton("♻️ Перевод")
    markup.add(item1, item2)

    balance = get_balance(message.chat.id)
    bot.send_message(message.chat.id, f"Ваш счёт:\nID: {message.chat.id}\nБаланс: {balance} баллов", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "♻️ Перевод")
def handle_transfer(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton(last_found_user_id)
    markup.add(item1)

    if last_found_user_id != None:
        bot.send_message(message.chat.id, "Введите номер счёта для перевода:", reply_markup=markup)
        bot.register_next_step_handler(message, process_transfer_account)

    else:
        bot.send_message(message.chat.id, "Введите номер счёта для перевода:")
        bot.register_next_step_handler(message, process_transfer_account)

def process_transfer_account(message):
    to_account = message.text

    if to_account == str(message.chat.id):
        bot.send_message(message.chat.id, "Ошибка: Нельзя переводить баллы самому себе. Попробуйте еще раз.")
        handle_home(message)
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    item1 = types.KeyboardButton("1")
    item2 = types.KeyboardButton("10")
    item3 = types.KeyboardButton("100")

    markup.add(item1, item2, item3)

    bot.send_message(message.chat.id, "Введите количество баллов для перевода (минимум 1):", reply_markup=markup)
    bot.register_next_step_handler(message, process_transfer_amount, to_account)



def process_transfer_amount(message, to_account):
    try:
        amount = int(message.text)

        if amount < 1:
            raise ValueError("Сумма перевода должна быть не меньше 1 балла")

        from_account_balance = get_balance(message.chat.id)

        if from_account_balance is not None and from_account_balance >= amount:
            to_account_balance = get_balance(to_account)

            if to_account_balance is not None:
                update_balance(message.chat.id, from_account_balance - amount)
                updated_to_account_balance = update_balance(to_account, to_account_balance + amount)
                from_user_name = get_balance_name(message.chat.id)[1]
                bot.send_message(message.chat.id, f"Перевод выполнен!")
                bot.send_message(to_account, f"Перевод {amount} баллов от {from_user_name} на счёт {to_account} выполнен!\nТекущий баланс: {updated_to_account_balance} баллов\nСтатус: ✅", reply_markup=None)
            else:
                bot.send_message(message.chat.id, "Ошибка: Невозможно выполнить перевод. Попробуйте еще раз.")
        else:
            bot.send_message(message.chat.id, "Ошибка: Недостаточно баллов на счету для выполнения перевода. Попробуйте еще раз.")
    except ValueError as e:
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("🔒 Мой счёт")
    item2 = types.KeyboardButton("♻️ Перевод")
    item3 = types.KeyboardButton("🔍 Поиск")
    item4 = types.KeyboardButton(last_found_user_id)
    if last_found_user_id != None:
        markup.add(item1, item2, item3, item4)

    else:
        markup.add(item1, item2, item3)

    bot.send_message(message.chat.id, "Главное меню", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔍 Поиск")
def handle_teacher_search_by_name(message):
    bot.send_message(message.chat.id, "Введите имя для поиска:")
    bot.register_next_step_handler(message, process_children_search_by_name)

def process_children_search_by_name(message):
    name = message.text
    user_id = get_id_by_name(name)

    if user_id is not None:
        balance, _ = get_balance_name(user_id)
        global last_found_user_id
        last_found_user_id = user_id

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("🔒 Мой счёт")
        item2 = types.KeyboardButton("♻️ Перевод")
        item3 = types.KeyboardButton("🔍 Поиск")
        item4 = types.KeyboardButton(last_found_user_id)
        markup.add(item1, item2, item3, item4)

        bot.send_message(message.chat.id, f"Пользователь {name} найден!\nID: {user_id}\nБаланс: {balance} баллов.", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, f"Пользователь {name} не найден.")

@bot.message_handler(commands=['payme'])
def get_money(message):
    if message.chat.id == OWNER:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("🔙")
        item2 = types.KeyboardButton("Списать налог")
        markup.add(item1, item2)
        bot.send_message(message.chat.id, "Нажмите кнопку для списания", reply_markup=markup)

    else:
        prm(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "Списать налог")
def Nalogi(message):
    if message.chat.id == OWNER:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Получаем текущий баланс OWNER
        owner_balance = get_balance(OWNER)

        # Получаем все строки в базе данных
        cursor.execute('SELECT ID, Balance FROM accounts')
        rows = cursor.fetchall()

        for row in rows:
            user_id, balance = row

            # Проверяем, что ID не равен TEACHER и OWNER
            if user_id != TEACHER and user_id != OWNER:
                # Обновляем баланс пользователя, вычитая 1 балл
                updated_balance = update_balance(user_id, balance - 1)
                bot.send_message(user_id, f"Списан 1 балл налога. Текущий баланс: {updated_balance} баллов.")

                # Обновляем баланс OWNER, добавляя 1 балл
                owner_balance = update_balance(OWNER, owner_balance + 1)

        conn.close()
        bot.send_message(OWNER, f"Списание налога завершено. Текущий баланс: {owner_balance} баллов.")
    else:
        prm(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "🛍 Покупки")
def handle_purchase(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("🔙")
    item2 = types.KeyboardButton("Создать мой товар")
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "Добро пожаловать в раздел покупок! Пожалуйста, отправьте фотографию QR-кода для оплаты.", reply_markup=markup)
    bot.register_next_step_handler(message, process_qr_code)

def process_qr_code(message):
    if message.text == "🔙":
        handle_home(message)
        return
    elif message.text == "Создать мой товар":
        bot.send_message(message.chat.id, "Введите цену товара:")
        bot.register_next_step_handler(message, process_create_product_price)
    else:
        try:
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            file_path = file_info.file_path
            downloaded_file = bot.download_file(file_path)

            with open("qr_code.jpg", 'wb') as new_file:
                new_file.write(downloaded_file)

            qr_data = decode(Image.open("qr_code.jpg"))

            if qr_data:
                qr_text = qr_data[0].data.decode('utf-8')
                qr_info = json.loads(qr_text)

                if "Summ" in qr_info and "Description" in qr_info and "Author" in qr_info:
                    purchase_sum = qr_info["Summ"]
                    description = qr_info["Description"]
                    author_id = qr_info["Author"]

                    user_balance = get_balance(message.chat.id)

                    if user_balance is not None and user_balance >= purchase_sum:
                        update_balance(message.chat.id, user_balance - purchase_sum)
                        author_balance = update_balance(author_id, get_balance(author_id) + purchase_sum)

                        bot.send_message(message.chat.id, f"Оплачена покупка: {description}")
                        bot.send_message(author_id, f"Товар оплачен!\nСумма: {purchase_sum}\nОписание: {description}\nПокупатель: {message.chat.id}")

                    else:
                        bot.send_message(message.chat.id, "Ошибка: Недостаточно средств на счету для оплаты покупки.")
                else:
                    bot.send_message(message.chat.id, "Ошибка: Неверный формат QR-кода.")
            else:
                bot.send_message(message.chat.id, "Ошибка: QR-код не распознан. Попробуйте еще раз.")
        except Exception as e:
            print(e)
            bot.send_message(message.chat.id, "Ошибка при обработке QR-кода. Попробуйте еще раз.")

        os.remove("qr_code.jpg")
        handle_home(message)

def process_create_product_price(message):
    try:
        price = int(message.text)
        bot.send_message(message.chat.id, "Введите описание товара:")
        bot.register_next_step_handler(message, process_create_product_description, price)
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка: Введите корректное число.")

def process_create_product_description(message, price):
    description = message.text

    author_id = message.chat.id

    product_info = {
        "Summ": price,
        "Description": description,
        "Author": author_id
    }

    qr_code_text = json.dumps(product_info)

    # Создаем QR-код с использованием библиотеки qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_code_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    img_byte_array = BytesIO()
    img.save(img_byte_array)
    img_byte_array.seek(0)

    bot.send_photo(message.chat.id, photo=img_byte_array, caption="QR-код для вашего товара создан! Поделитесь им с покупателями.")

    handle_home(message)


@bot.message_handler(func=lambda message: message.text == "🔙")
def handle_home(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if message.chat.id == TEACHER:
        item1 = types.KeyboardButton("🔻 Списать")
        item2 = types.KeyboardButton("🔺 Пополнить")
        item3 = types.KeyboardButton("Баланс")
        item4 = types.KeyboardButton("🔍 Поиск по имени")
        item5 = types.KeyboardButton("🛍 Покупки")
        item6 = types.KeyboardButton("📢 Объявление")
        markup.add(item1, item2, item3, item4, item5, item6)
    else:
        item1 = types.KeyboardButton("🔒 Мой счёт")
        item2 = types.KeyboardButton("♻️ Перевод")
        item3 = types.KeyboardButton("🔍 Поиск")
        item4 = types.KeyboardButton("🛍 Покупки")
        item5 = types.KeyboardButton(last_found_user_id)
        if last_found_user_id == None:
            markup.add(item1, item2, item3, item4)
        else:
            markup.add(item1, item2, item3, item4, item5)

    bot.send_message(message.chat.id, "Главное меню", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📢 Объявление")
def handle_announce(message):
    if message.chat.id == TEACHER:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("🔙")
        item2 = types.KeyboardButton("Только текст")
        item3 = types.KeyboardButton("Отправить медиа")
        markup.add(item1, item2, item3)
        bot.send_message(message.chat.id, "Введите текст объявления или выберите вариант отправки:", reply_markup=markup)
        bot.register_next_step_handler(message, process_announcement_choice)
    else:
        prm(message.chat.id)

def process_announcement_choice(message):
    if message.text == "🔙":
        handle_home(message)
        return
    elif message.text == "Только текст":
        bot.send_message(message.chat.id, "Введите текст объявления:")
        bot.register_next_step_handler(message, process_announcement)
    elif message.text == "Отправить медиа":
        bot.send_message(message.chat.id, "Прикрепите медиа-файл к объявлению или отправьте только текст:")
        bot.register_next_step_handler(message, process_announcement_media)

def process_announcement(message):
    announcement_text = message.text
    send_announcement_to_users(message, announcement_text, None)

def process_announcement_media(message):
    if message.photo or message.video or message.sticker or message.voice:
        media_file = None

        if message.photo:
            media_file = message.photo[-1].file_id
        elif message.video:
            media_file = message.video.file_id
        elif message.sticker:
            media_file = message.sticker.file_id
        elif message.voice:
            media_file = message.voice.file_id

        if media_file:
            send_announcement_to_users(message, None, media_file)
        else:
            bot.send_message(message.chat.id, "Ошибка: Не удалось прикрепить медиа-файл к объявлению.")
            handle_home(message)
    else:
        bot.send_message(message.chat.id, "Ошибка: Не найдено прикрепленного медиа-файла.")
        handle_home(message)

def send_announcement_to_users(message, announcement_text, media_file):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Получаем все пользователи из базы данных
    cursor.execute('SELECT ID FROM accounts')
    users = cursor.fetchall()

    for user_id in users:
        try:
            if media_file:
                if media_file.startswith('CAACAgIA') or media_file.startswith('AgAC'):
                    # Если медиа-файл это стикер или голосовое сообщение
                    bot.send_sticker(user_id[0], media_file)
                elif media_file.startswith('BQACAgIA') or media_file.startswith('AgAD'):
                    # Если медиа-файл это фото или видео
                    bot.send_photo(user_id[0], media_file, caption=announcement_text)
                # Можно добавить другие типы медиа-файлов по аналогии
            else:
                bot.send_message(user_id[0], announcement_text)
        except Exception as e:
            print(f"Error sending announcement to user {user_id[0]}: {str(e)}")

    conn.close()

    bot.send_message(TEACHER, "Объявление успешно отправлено всем пользователям.")
    handle_home(message)

@bot.message_handler(commands=['update'])
def handle_update(message):
    if message.chat.id == OWNER:
        # Получаем текст сообщения после команды '/update'
        command_text = message.text.split(' ', 1)[-1]

        # Формируем команду для запуска ipsbupdate.py в новом окне
        if os.name == 'nt':  # Проверяем операционную систему (Windows)
            command = f'start python ipsbupdate.py {command_text}'
        else:  # Для Linux и других ОС
            command = f'x-terminal-emulator -e python ipsbupdate.py {command_text}'

        # Запускаем новый процесс с командой
        try:
            subprocess.Popen(command, shell=True)
            bot.send_message(OWNER, "Обновление запущено. Бот будет завершен.")
            # Завершаем работу текущего процесса бота
            os._exit(0)
        except Exception as e:
            bot.send_message(OWNER, f"Ошибка при запуске обновления: {e}")
    else:
        prm(message.chat.id)

if __name__ == "__main__":
    print('Bot started!')
    bot.polling(none_stop=True)
