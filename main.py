import telebot
import time
import threading
import json
import os
import sys

# Чтение токена из переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ Ошибка: BOT_TOKEN не установлен в переменных окружения")
    sys.exit(1)

# ID группы и админа
try:
    GROUP_ID = int(os.environ.get("GROUP_ID", "-1003911641166"))
    ADMIN_ID = int(os.environ.get("ADMIN_ID", "8788760253"))
except ValueError:
    print("❌ Ошибка: GROUP_ID и ADMIN_ID должны быть числами")
    sys.exit(1)

FILE = "data.json"

bot = telebot.TeleBot(BOT_TOKEN)

# Загрузка данных
def load_data():
    if os.path.exists(FILE):
        try:
            with open(FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Ошибка загрузки данных: {e}, создаю новый файл")
    
    return {
        "interval": 45,
        "messages": [
            '🔔 Не забудь зайти в наш <a href="https://discord.gg/AqjCnK77c">Дискорд-сервер</a>!',
            '🔔 Подпишись на мой <a href="https://t.me/killer2017official">Телеграм-канал</a>!',
            '🔔 Есть вопрос или предложение? <a href="https://t.me/hahahahahahahahaaahhahahahahaha">Тебе сюда</a>!'
        ],
        "index": 0
    }

data = load_data()

def save():
    try:
        with open(FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("💾 Данные сохранены")
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")

# Отправка
def send_reminder():
    if data["messages"]:
        msg = data["messages"][data["index"]]
        data["index"] = (data["index"] + 1) % len(data["messages"])
        save()
        try:
            bot.send_message(GROUP_ID, msg, parse_mode="HTML", disable_web_page_preview=True)
            print(f"✅ Отправлено: {msg[:40]}...")
            return True
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            return False
    else:
        print("⚠️ Нет сообщений для отправки")
        return False

# Таймер
def scheduler():
    print(f"⏰ Запущен планировщик (интервал: {data['interval']} минут)")
    while True:
        time.sleep(data["interval"] * 60)
        try:
            send_reminder()
        except Exception as e:
            print(f"❌ Ошибка в планировщике: {e}")

# Команды для админа
@bot.message_handler(commands=['start', 'help'])
def help_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        bot.reply_to(m, 
            "👑 Команды:\n"
            "/list - список сообщений\n"
            "/add текст - добавить сообщение\n"
            "/del N - удалить сообщение (по номеру)\n"
            "/interval N - установить интервал (минуты)\n"
            "/ping - тестовая отправка\n"
            "/status - статус бота\n\n"
            "Пример с ссылкой:\n"
            '/add 🔔 Текст с <a href="https://ссылка">кликабельным словом</a>!'
        )

@bot.message_handler(commands=['list'])
def list_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        if not data["messages"]:
            bot.reply_to(m, "📭 Список сообщений пуст")
        else:
            clean = []
            for i, msg in enumerate(data["messages"]):
                # Упрощённая очистка для списка
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
            bot.reply_to(m, f"✅ Добавлено! Всего: {len(data['messages'])} сообщений")
        else:
            bot.reply_to(m, "❌ Укажите текст: /add ваш текст")

@bot.message_handler(commands=['del'])
def del_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        try:
            n = int(m.text.replace("/del ", "").strip()) - 1
            if 0 <= n < len(data["messages"]):
                removed = data["messages"].pop(n)
                save()
                bot.reply_to(m, f"✅ Удалено! Осталось: {len(data['messages'])} сообщений")
            else:
                bot.reply_to(m, f"❌ Номер от 1 до {len(data['messages'])}")
        except ValueError:
            bot.reply_to(m, "❌ Укажите номер: /del 1")

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
                bot.reply_to(m, f"✅ Интервал установлен: {n} минут")
        except ValueError:
            bot.reply_to(m, "❌ Укажите число: /interval 30")

@bot.message_handler(commands=['ping'])
def ping_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        result = send_reminder()
        if result:
            bot.reply_to(m, "✅ Тестовое сообщение отправлено!")
        else:
            bot.reply_to(m, "❌ Ошибка отправки, проверьте логи")

@bot.message_handler(commands=['status'])
def status_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        status = f"""📊 Статус бота:
        
📝 Сообщений: {len(data['messages'])}
⏱️ Интервал: {data['interval']} минут
📌 Индекс: {data['index']}
👥 Группа: {GROUP_ID}
🔄 Следующее сообщение: {data['index'] + 1 if data['messages'] else 'нет сообщений'}
"""
        bot.reply_to(m, status)

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
    print(f"📩 Чат: {m.chat.id} | Тип: {m.chat.type} | Текст: {m.text}")

print("🔥 Бот запускается...")
print(f"👑 Админ: {ADMIN_ID}")
print(f"👥 Группа: {GROUP_ID}")

# Запуск планировщика
threading.Thread(target=scheduler, daemon=True).start()

# Запуск бота с обработкой ошибок
try:
    print("✅ Бот готов к работе!")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    sys.exit(1)