import telebot
import random
import os

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

participants = {}
collecting = False

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Доьро пожаловать в обмен подарками! Используйте /add чтобы добавить участников.")

@bot.message_handler(commands=['add'])
def add(message):
    global collecting
    collecting = True
    bot.reply_to(message, "Отправьте имя каждого участника. /done когда закончите.")

@bot.message_handler(commands=['done'])
def done(message):
    global collecting

    if not participants:
        bot.reply_to(message, "Участников нет.")
        return

    collecting = False
    names = list(participants.keys())
    shuffled = names.copy()

    while True:
        random.shuffle(shuffled)
        if all(a != b for a, b in zip(names, shuffled)):
            break

    for giver, receiver in zip(names, shuffled):
        chat_id = participants[giver]
        bot.send_message(chat_id, f"Ты даришь подарок:: {receiver}")

    bot.reply_to(message, "готово")

@bot.message_handler(func=lambda m: True)
def collect(message):
    global collecting

    if not collecting:
        return

    name = message.text.strip()
    participants[name] = message.chat.id
    bot.reply_to(message, f"Добавлен {name}")

bot.polling()
