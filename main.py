import telebot
import time
import threading
import json
import os

# Чтение токена из переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в переменных окружения")

# ID группы и админа - тоже лучше вынести в переменные окружения
GROUP_ID = int(os.environ.get("GROUP_ID", -1003911641166))
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8788760253))

FILE = "data.json"

bot = telebot.TeleBot(BOT_TOKEN)

# Данные
if os.path.exists(FILE):
    with open(FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
else:
    data = {
        "interval": 45,
        "messages": [
            '🔔 Не забудь зайти в наш <a href="https://discord.gg/AqjCnK77c">Дискорд-сервер</a>!',
            '🔔 Подпишись на мой <a href="https://t.me/killer2017official">Телеграм-канал</a>!',
            '🔔 Есть вопрос или предложение? <a href="https://t.me/hahahahahahahahaaahhahahahahaha">Тебе сюда</a>!'
        ],
        "index": 0
    }

def save():
    with open(FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Отправка
def send_reminder():
    if data["messages"]:
        msg = data["messages"][data["index"]]
        data["index"] = (data["index"] + 1) % len(data["messages"])
        save()
        try:
            bot.send_message(GROUP_ID, msg, parse_mode="HTML", disable_web_page_preview=True)
            print(f"✅ Отправлено: {msg[:40]}")
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")

# Таймер
def scheduler():
    while True:
        time.sleep(data["interval"] * 60)
        send_reminder()

# Команды для админа (ЛС)
@bot.message_handler(commands=['start', 'help'])
def help_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        bot.reply_to(m, 
            "👑 Команды:\n"
            "/list - список\n"
            "/add текст - добавить\n"
            "/del N - удалить\n"
            "/interval N - интервал (минуты)\n"
            "/ping - тест\n\n"
            "Пример с ссылкой:\n"
            '/add 🔔 Текст с <a href="https://ссылка">кликабельным словом</a>!'
        )

@bot.message_handler(commands=['list'])
def list_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        if not data["messages"]:
            bot.reply_to(m, "📭 Пусто")
        else:
            clean = []
            for i, msg in enumerate(data["messages"]):
                clean_text = msg.replace('<a href="', '').replace('">', ': ').replace('</a>', '')
                clean.append(f"{i+1}. {clean_text}")
            bot.reply_to(m, "\n".join(clean))

@bot.message_handler(commands=['add'])
def add_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        t = m.text.replace("/add ", "", 1).strip()
        if t:
            data["messages"].append(t)
            save()
            bot.reply_to(m, f"✅ Добавлено! Всего: {len(data['messages'])}")
        else:
            bot.reply_to(m, "❌ /add текст")

@bot.message_handler(commands=['del'])
def del_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        try:
            n = int(m.text.replace("/del ", "").strip()) - 1
            if 0 <= n < len(data["messages"]):
                data["messages"].pop(n)
                save()
                bot.reply_to(m, f"✅ Удалено! Осталось: {len(data['messages'])}")
            else:
                bot.reply_to(m, f"❌ Номер от 1 до {len(data['messages'])}")
        except:
            bot.reply_to(m, "❌ /del 1")

@bot.message_handler(commands=['interval'])
def interval_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        try:
            n = int(m.text.replace("/interval ", "").strip())
            if n < 1:
                bot.reply_to(m, "❌ Минимум 1 минута")
            else:
                data["interval"] = n
                save()
                bot.reply_to(m, f"✅ Интервал: {n} минут")
        except:
            bot.reply_to(m, "❌ /interval 30")
@bot.message_handler(commands=['ping'])
def ping_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        send_reminder()
        bot.reply_to(m, "✅ Тест отправлен!")

# Команды в группе
@bot.message_handler(commands=['discord'])
def disc(m):
    if m.chat.id == GROUP_ID:
        bot.reply_to(m, '🔗 <a href="https://discord.gg/AqjCnK77c">Дискорд-сервер</a>', parse_mode="HTML")

@bot.message_handler(commands=['telegram'])
def tg(m):
    if m.chat.id == GROUP_ID:
        bot.reply_to(m, '📢 <a href="https://t.me/killer2017official">Телеграм-канал</a>', parse_mode="HTML")

@bot.message_handler(commands=['question'])
def q(m):
    if m.chat.id == GROUP_ID:
        bot.reply_to(m, '💬 <a href="https://t.me/hahahahahahahahaaahhahahahahaha">Вопросы и предложения</a>', parse_mode="HTML")

# Дебаг
@bot.message_handler(func=lambda m: True)
def debug(m):
    print(f"📩 Чат: {m.chat.id} | {m.text}")

print("🔥 Бот запущен")
threading.Thread(target=scheduler, daemon=True).start()
bot.infinity_polling()