import telebot
import time
import threading
import json
import os
import sys
import logging

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не установлен")
    sys.exit(1)

try:
    GROUP_ID = int(os.environ.get("GROUP_ID", "-1003911641166"))
    ADMIN_ID = int(os.environ.get("ADMIN_ID", "8788760253"))
except ValueError:
    logger.error("❌ GROUP_ID и ADMIN_ID должны быть числами")
    sys.exit(1)

FILE = "data.json"
bot = telebot.TeleBot(BOT_TOKEN)

# Проверка бота при запуске
try:
    bot.get_me()
    logger.info("✅ Бот успешно авторизован!")
except Exception as e:
    logger.error(f"❌ Ошибка авторизации: {e}")
    sys.exit(1)

def load_data():
    if os.path.exists(FILE):
        try:
            with open(FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки: {e}")
    
    default_data = {
        "interval": 45,
        "messages": [
            '🔔 Не забудь зайти в наш <a href="https://discord.gg/AqjCnK77c">Дискорд-сервер</a>!',
            '🔔 Подпишись на мой <a href="https://t.me/killer2017official">Телеграм-канал</a>!',
            '🔔 Есть вопрос или предложение? <a href="https://t.me/hahahahahahahahaaahhahahahahaha">Тебе сюда</a>!'
        ],
        "index": 0
    }
    
    with open(FILE, 'w', encoding='utf-8') as f:
        json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    return default_data

data = load_data()

def save():
    try:
        with open(FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("💾 Данные сохранены")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")

def send_reminder():
    if data["messages"]:
        msg = data["messages"][data["index"]]
        data["index"] = (data["index"] + 1) % len(data["messages"])
        save()
        try:
            bot.send_message(GROUP_ID, msg, parse_mode="HTML", disable_web_page_preview=True)
            logger.info(f"✅ Отправлено: {msg[:40]}...")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка отправки: {e}")
            return False
    else:
        logger.warning("⚠️ Нет сообщений")
        return False

def scheduler():
    logger.info(f"⏰ Планировщик запущен (интервал: {data['interval']} мин)")
    while True:
        time.sleep(data["interval"] * 60)
        send_reminder()

# Команды админа
@bot.message_handler(commands=['start', 'help'])
def help_cmd(m):
    logger.info(f"📩 Команда /help от {m.from_user.id}")
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        bot.reply_to(m, 
            "👑 Команды:\n"
            "/list - список сообщений\n"
            "/add текст - добавить\n"
            "/del N - удалить\n"
            "/interval N - интервал (минуты)\n"
            "/ping - тестовая отправка\n"
            "/status - статус бота"
        )
    else:
        bot.reply_to(m, "❌ Доступ запрещён")

@bot.message_handler(commands=['list'])
def list_cmd(m):
    logger.info(f"📩 Команда /list от {m.from_user.id}")
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        if not data["messages"]:
            bot.reply_to(m, "📭 Список пуст")
        else:
            clean = []
            for i, msg in enumerate(data["messages"]):
                clean_text = msg.replace('<a href="', '').replace('">', ': ').replace('</a>', '')
                clean.append(f"{i+1}. {clean_text}")
            bot.reply_to(m, "\n".join(clean))
    else:
        bot.reply_to(m, "❌ Доступ запрещён")

@bot.message_handler(commands=['add'])
def add_cmd(m):
    logger.info(f"📩 Команда /add от {m.from_user.id}")
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        t = m.text.replace("/add ", "", 1).strip()
        if t:
            data["messages"].append(t)
            save()
            bot.reply_to(m, f"✅ Добавлено! Всего: {len(data['messages'])}")
        else:
            bot.reply_to(m, "❌ /add текст")
    else:
        bot.reply_to(m, "❌ Доступ запрещён")

@bot.message_handler(commands=['del'])
def del_cmd(m):
    logger.info(f"📩 Команда /del от {m.from_user.id}")
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
    else:
        bot.reply_to(m, "❌ Доступ запрещён")

@bot.message_handler(commands=['interval'])
def interval_cmd(m):
    logger.info(f"📩 Команда /interval от {m.from_user.id}")
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
    else:
        bot.reply_to(m, "❌ Доступ запрещён")

@bot.message_handler(commands=['ping'])
def ping_cmd(m):
    logger.info(f"📩 Команда /ping от {m.from_user.id}")
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        result = send_reminder()
        if result:
            bot.reply_to(m, "✅ Тест отправлен!")
        else:
            bot.reply_to(m, "❌ Ошибка отправки")
    else:
        bot.reply_to(m, "❌ Доступ запрещён")

@bot.message_handler(commands=['status'])
def status_cmd(m):
    logger.info(f"📩 Команда /status от {m.from_user.id}")
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        bot.reply_to(m, f"""📊 Статус бота:
        
📝 Сообщений: {len(data['messages'])}
⏱️ Интервал: {data['interval']} минут
📌 Индекс: {data['index']}
👥 Группа: {GROUP_ID}
🤖 Бот: @{bot.get_me().username}
""")
    else:
        bot.reply_to(m, "❌ Доступ запрещён")

# Команды в группе
@bot.message_handler(commands=['discord'])
def disc(m):
    logger.info(f"📩 Команда /discord в группе от {m.from_user.id}")
    if m.chat.id == GROUP_ID:
        bot.reply_to(m, '🔗 <a href="https://discord.gg/AqjCnK77c">Дискорд-сервер</a>', parse_mode="HTML")

@bot.message_handler(commands=['telegram'])
def tg(m):
    logger.info(f"📩 Команда /telegram в группе от {m.from_user.id}")
    if m.chat.id == GROUP_ID:
        bot.reply_to(m, '📢 <a href="https://t.me/killer2017official">Телеграм-канал</a>', parse_mode="HTML")

@bot.message_handler(commands=['question'])
def q(m):
    logger.info(f"📩 Команда /question в группе от {m.from_user.id}")
    if m.chat.id == GROUP_ID:
        bot.reply_to(m, '💬 <a href="https://t.me/hahahahahahahahaaahhahahahahaha">Вопросы и предложения</a>', parse_mode="HTML")

# Обработчик всех сообщений для отладки
@bot.message_handler(func=lambda m: True)
def debug_all(m):
    logger.info(f"📩 Сообщение: {m.text} | Чат: {m.chat.id} | Тип: {m.chat.type} | От: {m.from_user.id}")

logger.info("🔥 Бот запускается...")
logger.info(f"👑 Админ: {ADMIN_ID}")
logger.info(f"👥 Группа: {GROUP_ID}")

# Проверка, что бот может отправлять сообщения в группу
try:
    test_msg = f"🤖 Бот запущен! ID: {time.time()}"
    bot.send_message(GROUP_ID, test_msg)
    logger.info("✅ Тестовое сообщение в группу отправлено")
except Exception as e:
    logger.error(f"❌ Не могу отправить в группу: {e}")

# Запуск планировщика
threading.Thread(target=scheduler, daemon=True).start()

# Запуск бота
try:
    logger.info("✅ Бот готов к работе!")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
except Exception as e:
    logger.error(f"❌ Критическая ошибка: {e}")
    sys.exit(1)