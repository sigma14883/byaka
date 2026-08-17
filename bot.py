import telebot
import time
import threading
import json
import os
import sys
import logging
import random
import re

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

try:
    bot.get_me()
    logger.info("✅ Бот авторизован!")
except Exception as e:
    logger.error(f"❌ Ошибка: {e}")
    sys.exit(1)

def load_data():
    if os.path.exists(FILE):
        try:
            with open(FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    default_data = {
        "interval": 45,
        "messages": [
            '🔔 Не забудь зайти в наш <a href="https://discord.gg/AqjCnK77c">Дискорд-сервер</a>!',
            '🔔 Подпишись на мой <a href="https://t.me/killer2017official">Телеграм-канал</a>!',
            '🔔 Есть вопрос или предложение? <a href="https://t.me/hahahahahahahahaaahhahahahahaha">Тебе сюда</a>!'
        ],
        "index": 0,
        "rp_commands": {}
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
        logger.error(f"Ошибка сохранения: {e}")

def send_reminder():
    if data["messages"]:
        msg = data["messages"][data["index"]]
        data["index"] = (data["index"] + 1) % len(data["messages"])
        save()
        try:
            bot.send_message(GROUP_ID, msg, parse_mode="HTML", disable_web_page_preview=True)
            logger.info(f"✅ Отправлено")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return False
    return False

def scheduler():
    while True:
        time.sleep(data["interval"] * 60)
        send_reminder()

# ============ РП КОМАНДЫ ============

@bot.message_handler(commands=['rp'])
def create_rp(m):
    logger.info(f"📩 Команда /rp от {m.from_user.id}")
    try:
        if m.chat.id != GROUP_ID:
            bot.reply_to(m, "❌ Только в группе!")
            return
        
        # Получаем текст после /rp
        text = m.text.replace("/rp", "", 1).strip()
        
        # Разделяем по /
        args = text.split('/')
        
        # Убираем пустые элементы
        args = [arg.strip() for arg in args if arg.strip()]
        
        logger.info(f"Аргументы: {args}")
        
        if len(args) < 3:
            bot.reply_to(m, 
                "❌ Формат: /rp команда/эмодзи/текст\n"
                "Пример: /rp обнять/♥️/обнял(а)\n"
                "Пример: /rp ударить/👊/ударил(а)"
            )
            return
        
        cmd = args[0].lower()
        emoji = args[1]
        action = args[2]
        
        user_id = str(m.from_user.id)
        
        if user_id not in data["rp_commands"]:
            data["rp_commands"][user_id] = {}
        
        if cmd in data["rp_commands"][user_id]:
            bot.reply_to(m, f"⚠️ Команда '{cmd}' уже есть! Используй /rpdel {cmd}")
            return
        
        data["rp_commands"][user_id][cmd] = {"emoji": emoji, "text": action}
        save()
        
        bot.reply_to(m, 
            f"✅ Команда '{cmd}' создана!\n\n"
            f"Эмодзи: {emoji}\n"
            f"Действие: {action}\n\n"
            f"Используй: {cmd} @юзер"
        )
        logger.info(f"✅ Создана команда {cmd} для {m.from_user.first_name}")
        
    except Exception as e:
        logger.error(f"Ошибка create_rp: {e}")
        bot.reply_to(m, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['rpdel'])
def delete_rp(m):
    logger.info(f"📩 Команда /rpdel от {m.from_user.id}")
    try:
        if m.chat.id != GROUP_ID:
            bot.reply_to(m, "❌ Только в группе!")
            return
        
        cmd = m.text.replace("/rpdel", "", 1).strip().lower()
        if not cmd:
            bot.reply_to(m, "❌ Укажи команду: /rpdel обнять")
            return
        
        user_id = str(m.from_user.id)
        if user_id in data["rp_commands"] and cmd in data["rp_commands"][user_id]:
            del data["rp_commands"][user_id][cmd]
            save()
            bot.reply_to(m, f"✅ Команда '{cmd}' удалена!")
        else:
            bot.reply_to(m, f"❌ Команда '{cmd}' не найдена")
    except Exception as e:
        logger.error(f"Ошибка delete_rp: {e}")
        bot.reply_to(m, "❌ Ошибка")

@bot.message_handler(commands=['rplist'])
def list_rp(m):
    logger.info(f"📩 Команда /rplist от {m.from_user.id}")
    try:
        if m.chat.id != GROUP_ID:
            bot.reply_to(m, "❌ Только в группе!")
            return
        
        if not data["rp_commands"]:
            bot.reply_to(m, "📭 Нет РП команд. Создай: /rp обнять/♥️/обнял(а)")
            return
        
        text = "📋 РП команды в группе:\n\n"
        count = 0
        for uid, cmds in data["rp_commands"].items():
            try:
                user = bot.get_chat_member(m.chat.id, int(uid))
                name = user.user.first_name
                for cmd, info in cmds.items():
                    text += f"{name}: {cmd} {info['emoji']} - {info['text']}\n"
                    count += 1
                    if count >= 30:
                        text += "\n...и ещё"
                        break
            except Exception as e:
                logger.error(f"Ошибка получения пользователя {uid}: {e}")
        
        bot.reply_to(m, text)
    except Exception as e:
        logger.error(f"Ошибка list_rp: {e}")
        bot.reply_to(m, "❌ Ошибка")

# ============ ОБРАБОТЧИК РП (БЕЗ ПРЕФИКСОВ) ============

@bot.message_handler(func=lambda m: m.chat.id == GROUP_ID and m.text and not m.text.startswith('/'))
def handle_rp(m):
    try:
        text = m.text.strip()
        
        # Проверяем на бяка
        if text.lower().startswith('бяка'):
            return
        
        # Разбиваем на слова
        words = text.split()
        if not words:
            return
        
        # Первое слово - команда
        cmd = words[0].lower()
        user_id = str(m.from_user.id)
        
        # Проверяем наличие команды у пользователя
        if user_id not in data["rp_commands"]:
            return
        
        if cmd not in data["rp_commands"][user_id]:
            return
        
        # Получаем данные команды
        cmd_info = data["rp_commands"][user_id][cmd]
        emoji = cmd_info["emoji"]
        action = cmd_info["text"]
        
        logger.info(f"🎭 РП команда: {cmd} от {m.from_user.first_name}")
        
        # Ищем цель
        target = None
        target_text = " ".join(words[1:]) if len(words) > 1 else ""
        
        # 1. Реплай
        if m.reply_to_message:
            target = m.reply_to_message.from_user
        
        # 2. @username
        if not target and target_text:
            mention = re.search(r'@(\w+)', target_text)
            if mention:
                username = mention.group(1)
                try:
                    members = bot.get_chat_members(m.chat.id)
                    for member in members:
                        if member.user.username and member.user.username.lower() == username.lower():
                            target = member.user
                            break
                except:
                    pass
        
        # 3. По имени
        if not target and target_text:
            try:
                members = bot.get_chat_members(m.chat.id)
                for member in members:
                    name = member.user.first_name or ""
                    if name.lower() in target_text.lower():
                        target = member.user
                        break
            except:
                pass
        
        # Ответ
        if not target:
            bot.reply_to(m, f"{emoji} {m.from_user.first_name} {action}")
        elif target.id == m.from_user.id:
            bot.reply_to(m, f"{emoji} {m.from_user.first_name} {action} себя 😄")
        elif target.id == bot.get_me().id:
            bot.reply_to(m, f"{emoji} {m.from_user.first_name} {action} бота 😄")
        else:
            bot.reply_to(m, f"{emoji} {m.from_user.first_name} {action} {target.first_name}")
            
    except Exception as e:
        logger.error(f"Ошибка handle_rp: {e}")

# ============ ИГРА БЯКА ============

@bot.message_handler(func=lambda m: m.chat.id == GROUP_ID and m.text and 'бяка' in m.text.lower())
def handle_byaka(m):
    logger.info(f"🎲 Обнаружено 'бяка' от {m.from_user.first_name}: {m.text}")
    try:
        text = m.text.lower()
        
        # Убираем "бяка"
        rest = text.replace('бяка', '', 1).strip()
        
        if not rest:
            bot.reply_to(m, "❌ Напиши: бяка кто [действие]")
            return
        
        # Проверяем наличие "кто"
        if 'кто' in rest:
            # Берём всё после "кто"
            parts = rest.split('кто', 1)
            action = parts[1].strip() if len(parts) > 1 else ""
        else:
            action = rest
        
        if not action:
            bot.reply_to(m, "❌ Укажи действие\nПример: бяка кто пойдёт гулять")
            return
        
        logger.info(f"Действие: {action}")
        
        # Получаем участников чата
        try:
            members = bot.get_chat_members(m.chat.id)
            candidates = []
            bot_id = bot.get_me().id
            
            for member in members:
                user = member.user
                if user.id != bot_id and user.id != m.from_user.id and not user.is_bot:
                    candidates.append(user)
            
            logger.info(f"Кандидатов: {len(candidates)}")
            
            if not candidates:
                bot.reply_to(m, "❌ Нет кандидатов 😅")
                return
            
            # Выбираем случайного
            chosen = random.choice(candidates)
            logger.info(f"🎯 Выбран: {chosen.first_name}")
            
            # Формируем ответ
            if chosen.username:
                response = f"🤔 Думаю, @{chosen.username}"
            else:
                response = f"🤔 Думаю, {chosen.first_name}"
            
            bot.reply_to(m, f"{response} {action} 😄")
            logger.info(f"✅ Ответ бяка отправлен")
            
        except Exception as e:
            logger.error(f"Ошибка получения участников: {e}")
            bot.reply_to(m, "❌ Ошибка получения списка участников")
            
    except Exception as e:
        logger.error(f"Ошибка byaka: {e}")
        bot.reply_to(m, f"❌ Ошибка: {str(e)}")

# ============ АДМИН КОМАНДЫ ============

@bot.message_handler(commands=['start', 'help'])
def help_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        bot.reply_to(m,
            "👑 Команды админа:\n"
            "/list - список сообщений\n"
            "/add текст - добавить\n"
            "/del N - удалить\n"
            "/interval N - интервал\n"
            "/ping - тест\n"
            "/status - статус\n\n"
            "🎭 РП команды (в группе):\n"
            "/rp обнять/♥️/обнял(а) - создать\n"
            "/rpdel обнять - удалить\n"
            "/rplist - список\n\n"
            "Использование: обнять @юзер\n"
            "Игра: бяка кто пойдёт гулять"
        )

@bot.message_handler(commands=['list'])
def list_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        if not data["messages"]:
            bot.reply_to(m, "📭 Пусто")
            return
        text = "\n".join([f"{i+1}. {msg[:50]}..." for i, msg in enumerate(data["messages"])])
        bot.reply_to(m, text)

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
                bot.reply_to(m, "❌ Минимум 1")
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

@bot.message_handler(commands=['status'])
def status_cmd(m):
    if m.chat.type == "private" and m.from_user.id == ADMIN_ID:
        total_rp = sum(len(cmds) for cmds in data["rp_commands"].values())
        bot.reply_to(m,
            f"📊 Статус:\n"
            f"Сообщений: {len(data['messages'])}\n"
            f"Интервал: {data['interval']} мин\n"
            f"РП команд: {total_rp}\n"
            f"Группа: {GROUP_ID}"
        )

# Команды в группе
@bot.message_handler(commands=['discord'])
def disc(m):
    if m.chat.id == GROUP_ID:
        bot.reply_to(m, '🔗 <a href="https://discord.gg/AqjCnK77c">Дискорд</a>', parse_mode="HTML")

@bot.message_handler(commands=['telegram'])
def tg(m):
    if m.chat.id == GROUP_ID:
        bot.reply_to(m, '📢 <a href="https://t.me/killer2017official">Телеграм-канал</a>', parse_mode="HTML")

@bot.message_handler(commands=['question'])
def q(m):
    if m.chat.id == GROUP_ID:
        bot.reply_to(m, '💬 <a href="https://t.me/hahahahahahahahaaahhahahahahaha">Вопросы</a>', parse_mode="HTML")

logger.info("🔥 Бот запущен!")
logger.info(f"👑 Админ: {ADMIN_ID}")
logger.info(f"👥 Группа: {GROUP_ID}")

try:
    bot.send_message(GROUP_ID, "✅ Бот перезапущен! Проверяем /rp и бяка")
except Exception as e:
    logger.error(f"Ошибка отправки: {e}")

threading.Thread(target=scheduler, daemon=True).start()
bot.infinity_polling()