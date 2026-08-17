import telebot
import time
import threading
import json
import os
import sys
import logging
import random
import re

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
        "index": 0,
        "rp_commands": {}  # {user_id: {command: {"emoji": "♥️", "text": "обнял(а)"}}}
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

# ============ РП КОМАНДЫ В ГРУППЕ ============

# Создание РП команды
@bot.message_handler(commands=['rp'])
def create_rp_command(m):
    if m.chat.id != GROUP_ID:
        bot.reply_to(m, "❌ Создавай РП команды только в группе!")
        return
    
    user_id = str(m.from_user.id)
    args = m.text.replace("/rp ", "", 1).strip().split('/')
    
    if len(args) < 3:
        bot.reply_to(m, 
            "❌ Формат: /rp команда/эмодзи/текст_действия\n\n"
            "Пример: /rp обнять/♥️/обнял(а)\n"
            "Пример: /rp ударить/👊/ударил(а)\n"
            "Пример: /rp поцеловать/💋/поцеловал(а)\n\n"
            "Потом просто напиши: обнять @юзер\n"
            "Или: обнять (реплай на сообщение)"
        )
        return
    
    command = args[0].strip().lower()
    emoji = args[1].strip()
    action_text = args[2].strip()
    
    # Инициализация
    if user_id not in data["rp_commands"]:
        data["rp_commands"][user_id] = {}
    
    if command in data["rp_commands"][user_id]:
        bot.reply_to(m, f"⚠️ Команда '{command}' уже существует! Используй /rpdel {command} чтобы удалить")
        return
    
    # Сохраняем команду
    data["rp_commands"][user_id][command] = {
        "emoji": emoji,
        "text": action_text
    }
    save()
    
    bot.reply_to(m, 
        f"✅ РП команда создана!\n\n"
        f"Команда: {command}\n"
        f"Эмодзи: {emoji}\n"
        f"Действие: {action_text}\n\n"
        f"Использование: {command} @юзер\n"
        f"Или: {command} (реплай на сообщение)"
    )

# Удаление РП команды
@bot.message_handler(commands=['rpdel'])
def delete_rp_command(m):
    if m.chat.id != GROUP_ID:
        bot.reply_to(m, "❌ Удаляй РП команды только в группе!")
        return
    
    user_id = str(m.from_user.id)
    command = m.text.replace("/rpdel ", "", 1).strip().lower()
    
    if not command:
        bot.reply_to(m, "❌ Укажи команду: /rpdel обнять")
        return
    
    if user_id not in data["rp_commands"] or command not in data["rp_commands"][user_id]:
        bot.reply_to(m, f"❌ Команда '{command}' не найдена!")
        return
    
    del data["rp_commands"][user_id][command]
    save()
    
    bot.reply_to(m, f"✅ Команда '{command}' удалена!")

# Список РП команд
@bot.message_handler(commands=['rplist'])
def list_rp_commands(m):
    if m.chat.id != GROUP_ID:
        bot.reply_to(m, "❌ Список команд только в группе!")
        return
    
    all_commands = []
    for uid, commands in data["rp_commands"].items():
        if commands:
            try:
                user = bot.get_chat_member(m.chat.id, int(uid))
                name = user.user.first_name or f"ID:{uid}"
                for cmd, info in commands.items():
                    all_commands.append(f"{name}: {cmd} {info['emoji']} ({info['text']})")
            except:
                pass
    
    if not all_commands:
        bot.reply_to(m, "📭 Нет РП команд в группе. Создай: /rp обнять/♥️/обнял(а)")
        return
    
    text = "📋 РП команды в группе:\n\n" + "\n".join(all_commands[:30])
    if len(all_commands) > 30:
        text += f"\n\n...и ещё {len(all_commands)-30} команд"
    
    bot.reply_to(m, text)

# ============ ОБРАБОТКА РП КОМАНД (БЕЗ ПРЕФИКСОВ) ============

@bot.message_handler(func=lambda m: m.chat.id == GROUP_ID and m.text and not m.text.startswith('/'))
def handle_rp_command(m):
    text = m.text.strip()
    
    # Пропускаем команды бота
    if text.startswith('/'):
        return
    
    # Разбиваем на слова
    words = text.split()
    if not words:
        return
    
    # Первое слово - возможная команда
    possible_command = words[0].lower()
    
    # Проверяем, есть ли такая команда у пользователя
    user_id = str(m.from_user.id)
    
    if user_id not in data["rp_commands"]:
        return
    
    if possible_command not in data["rp_commands"][user_id]:
        return
    
    # Получаем информацию о команде
    cmd_info = data["rp_commands"][user_id][possible_command]
    emoji = cmd_info["emoji"]
    action = cmd_info["text"]
    
    # Остальной текст (цель)
    target_text = " ".join(words[1:]) if len(words) > 1 else ""
    
    # Определяем цель
    target = None
    
    # 1. Проверяем реплай
    if m.reply_to_message:
        target = m.reply_to_message.from_user
    
    # 2. Проверяем упоминание @username
    if not target and target_text:
        mention_match = re.search(r'@(\w+)', target_text)
        if mention_match:
            username = mention_match.group(1)
            try:
                chat_members = bot.get_chat_members(m.chat.id)
                for member in chat_members:
                    if member.user.username and member.user.username.lower() == username.lower():
                        target = member.user
                        break
            except:
                pass
    
    # 3. Проверяем имя в тексте
    if not target and target_text:
        try:
            chat_members = bot.get_chat_members(m.chat.id)
            target_text_lower = target_text.lower()
            for member in chat_members:
                name = member.user.first_name or ""
                if name.lower() in target_text_lower:
                    target = member.user
                    break
        except:
            pass
    
    # Если цель не найдена - выводим общее сообщение
    if not target:
        bot.reply_to(m, f"{emoji} {m.from_user.first_name} {action}")
        return
    
    # Если цель - сам пользователь
    if target.id == m.from_user.id:
        bot.reply_to(m, f"{emoji} {m.from_user.first_name} {action} себя 😄")
        return
    
    # Если цель - бот
    if target.id == bot.get_me().id:
        bot.reply_to(m, f"{emoji} {m.from_user.first_name} {action} бота 😄")
        return
    
    # Выводим РП действие
    bot.reply_to(m, f"{emoji} {m.from_user.first_name} {action} {target.first_name}")

# ============ ИГРА БЯКА ============

@bot.message_handler(func=lambda m: m.chat.id == GROUP_ID and m.text and m.text.lower().startswith('бяка'))
def handle_byaka(m):
    text = m.text.lower()
    
    # Парсим: "бяка кто что-то"
    rest = text[5:].strip()
    
    if not rest:
        bot.reply_to(m, "❌ Напиши: бяка кто [действие]")
        return
    
    if not rest.startswith("кто"):
        bot.reply_to(m, "❌ Формат: бяка кто [действие]")
        return
    
    action = rest[3:].strip()
    
    if not action:
        bot.reply_to(m, "❌ Укажи действие: бяка кто пойдёт гулять")
        return
    
    try:
        # Получаем всех участников чата
        chat_members = bot.get_chat_members(m.chat.id)
        
        # Фильтруем: исключаем бота и автора
        candidates = []
        for member in chat_members:
            user = member.user
            if user.id != bot.get_me().id and user.id != m.from_user.id:
                if not user.is_bot:
                    candidates.append(user)
        
        if not candidates:
            bot.reply_to(m, "❌ Нет подходящих кандидатов 😅")
            return
        
        # Выбираем случайного
        chosen = random.choice(candidates)
        
        # Генерируем ответ
        if chosen.username:
            response = f"🤔 Думаю, @{chosen.username}"
        else:
            response = f"🤔 Думаю, {chosen.first_name}"
        
        bot.reply_to(m, f"{response} {action} 😄")
        
    except Exception as e:
        logger.error(f"Ошибка в бяка: {e}")
        bot.reply_to(m, "❌ Ошибка, попробуй позже")

# ============ ОБЫЧНЫЕ КОМАНДЫ ============

# Команды админа
@bot.message_handler(commands=['start', 'help'])
def help_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        bot.reply_to(m, 
            "👑 Команды админа:\n"
            "/list - список сообщений\n"
            "/add текст - добавить\n"
            "/del N - удалить\n"
            "/interval N - интервал (минуты)\n"
            "/ping - тестовая отправка\n"
            "/status - статус бота\n\n"
            "🎭 РП команды в группе:\n"
            "/rp команда/эмодзи/текст - создать\n"
            "/rpdel команда - удалить\n"
            "/rplist - список всех команд\n\n"
            "Пример: /rp обнять/♥️/обнял(а)\n"
            "Использование: обнять @юзер"
        )

@bot.message_handler(commands=['list'])
def list_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        if not data["messages"]:
            bot.reply_to(m, "📭 Список пуст")
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
        result = send_reminder()
        if result:
            bot.reply_to(m, "✅ Тест отправлен!")
        else:
            bot.reply_to(m, "❌ Ошибка отправки")

@bot.message_handler(commands=['status'])
def status_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        bot.reply_to(m, f"""📊 Статус бота:
        
📝 Сообщений: {len(data['messages'])}
⏱️ Интервал: {data['interval']} минут
📌 Индекс: {data['index']}
👥 Группа: {GROUP_ID}
🎭 РП команд: {sum(len(cmds) for cmds in data['rp_commands'].values())}
""")

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

# Отладка
@bot.message_handler(func=lambda m: True)
def debug_all(m):
    if m.chat.id == GROUP_ID:
        logger.info(f"📩 {m.from_user.first_name}: {m.text}")

logger.info("🔥 Бот запускается...")
logger.info(f"👑 Админ: {ADMIN_ID}")
logger.info(f"👥 Группа: {GROUP_ID}")

# Проверка отправки в группу
try:
    bot.send_message(GROUP_ID, "🤖 Бот перезапущен! РП команды работают без префиксов 🎉")
    logger.info("✅ Тестовое сообщение отправлено")
except Exception as e:
    logger.error(f"❌ Ошибка отправки в группу: {e}")

# Запуск планировщика
threading.Thread(target=scheduler, daemon=True).start()

# Запуск бота
try:
    logger.info("✅ Бот готов к работе!")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
except Exception as e:
    logger.error(f"❌ Критическая ошибка: {e}")
    sys.exit(1)