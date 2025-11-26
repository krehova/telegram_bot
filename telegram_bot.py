import telebot
import random

bot = telebot.TeleBot("8449206917:AAHDTZvCzLpnpAZ_im566fN-tnB28eugtr8")

participants = {}   # name -> chat_id
collecting = False


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
                 "рандомайзер подарков запущен!\n"
                 "чтобы добавить участников, отправьте /start в чат боту.\n")


@bot.message_handler(commands=['add'])
def add(message):
    global collecting
    collecting = True
    bot.reply_to(message,
                 "Send each participant's *name*. One per message.\n"
                 "The person must have already messaged the bot.\n"
                 "Send /done when finished.",
                 parse_mode='Markdown')


@bot.message_handler(commands=['done'])
def done(message):
    global collecting

    if not participants:
        bot.reply_to(message, "No participants added!")
        return

    collecting = False

    bot.reply_to(message, "Randomizing pairs")

    names = list(participants.keys())
    shuffled = names.copy()

    # Ensure nobody gets themselves
    while True:
        random.shuffle(shuffled)
        if all(a != b for a, b in zip(names, shuffled)):
            break

    # Notify each participant privately
    for giver, receiver in zip(names, shuffled):
        chat_id = participants[giver]
        bot.send_message(chat_id,
                         f"Ты даришь подарок: *{receiver}*!",
                         parse_mode='Markdown')

    bot.reply_to(message, "Assignments sent!")


@bot.message_handler(func=lambda m: True)
def collect(message):
    global collecting

    if not collecting:
        return

    name = message.text.strip()

    participants[name] = message.chat.id
    bot.reply_to(message, f"добавлен: *{name}*", parse_mode='Markdown')


bot.polling()
