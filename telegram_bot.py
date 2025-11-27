import telebot
import os
import sqlite3
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1420675874   # <-- put your Telegram ID

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)


# ============================
#   DATABASE SETUP
# ============================

def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            name TEXT PRIMARY KEY,
            chat_id INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def add_participant(name, chat_id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO participants (name, chat_id) VALUES (?, ?)",
                (name, chat_id))
    conn.commit()
    conn.close()


def remove_participant(name):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM participants WHERE name = ?", (name,))
    conn.commit()
    conn.close()


def get_participants():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT name, chat_id FROM participants")
    data = cur.fetchall()
    conn.close()
    return data


def clear_participants():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM participants")
    conn.commit()
    conn.close()


init_db()


# ============================
#       ADMIN CHECK
# ============================

def is_admin(message):
    return message.from_user.id == ADMIN_ID


# ============================
#      BOT COMMANDS
# ============================

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
                 "Отправьте свое *имя*, чтобы участвовать.",
                parse_mode="Markdown")


@bot.message_handler(commands=['list'])
def list_cmd(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔ Нет доступа.")

    participants = get_participants()
    if not participants:
        return bot.reply_to(message, "📭 Участников пока нет.")

    text = "📜 *Текущие участники:*\n\n"
    for name, _ in participants:
        text += f"• {name}\n"

    bot.reply_to(message, text, parse_mode="Markdown")


@bot.message_handler(commands=['remove'])
def remove_cmd(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔ Нет доступа.")

    try:
        name = message.text.split(" ", 1)[1].strip()
    except:
        return bot.reply_to(message, "Использование: /remove <имя>")

    remove_participant(name)
    bot.reply_to(message, f"🗑 Удален участник: {name}")


@bot.message_handler(commands=['reset'])
def reset_cmd(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔ Нет доступа.")

    clear_participants()
    bot.reply_to(message, "🔄 Список очищён.")


@bot.message_handler(commands=['done'])
def done_cmd(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔ Нет доступа.")

    import random

    participants = get_participants()

    if len(participants) < 2:
        return bot.reply_to(message, "❗ Нужно минимум 2 участника.")

    names = [p[0] for p in participants]
    ids = {p[0]: p[1] for p in participants}

    shuffled = names.copy()

    # ensure no self-match
    while True:
        random.shuffle(shuffled)
        if all(a != b for a, b in zip(names, shuffled)):
            break

    # send assignments
    for giver, receiver in zip(names, shuffled):
        bot.send_message(
            ids[giver],
            f"Ты даришь подарок: *{receiver}*",
            parse_mode="Markdown"
        )

    bot.reply_to(message, "🎉 Рассылка завершена!")


# ============================
#  DEFAULT HANDLER (ADD NAME)
# ============================

@bot.message_handler(func=lambda m: True)
def add_name(message):
    name = message.text.strip()

    # Check if user already participated using chat_id
    for existing, cid in get_participants():
        if cid == message.chat.id:
            return bot.reply_to(message, "❗ Вы уже участвуете.")

        if existing.lower() == name.lower():
            return bot.reply_to(message, "❗ Это имя уже занято.")

    add_participant(name, message.chat.id)
    bot.reply_to(message, f"✔ Вы добавлены как: *{name}*", parse_mode="Markdown")


# ============================
#        WEBHOOK SERVER
# ============================

@app.route("/webhook", methods=["POST"])
def webhook():
    json_data = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return "OK", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=os.getenv("RAILWAY_PUBLIC_DOMAIN") + "/webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
