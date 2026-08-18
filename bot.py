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

# Статусы по репутации
RANKINGS = {
    -100: "👻 Призрак",
    -75: "💀 Тень",
    -50: "😈 Недостойный",
    -25: "😔 Опущенный",
    -10: "🥴 Тёмный друн",
    0: "🍺 Друн",
    10: "😎 Бурмалда",
    25: "🧠 Сократ",
    50: "👑 Босс",
    75: "⭐ Легенда",
    100: "🔥 Бог"
}

def get_rank(rep):
    """Получить статус по репутации"""
    ranks = sorted(RANKINGS.keys())
    for threshold in ranks:
        if rep <= threshold:
            return RANKINGS[threshold]
    return RANKINGS[ranks[-1]]

def load_data():
    """Загрузка данных из файла"""
    if os.path.exists(FILE):
        try:
            with open(FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"✅ Данные загружены из {FILE}")
                logger.info(f"📊 Пользователей в репутации: {len(data.get('reputation', {}))}")
                return data
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки: {e}")
    
    # Создаём новые данные
    logger.info("🆕 Создаём новый файл данных")
    default_data = {
        "interval": 45,
        "messages": [
            '🔔 Не забудь зайти в наш <a href="https://discord.gg/AqjCnK77c">Дискорд-сервер</a>!',
            '🔔 Подпишись на мой <a href="https://t.me/killer2017official">Телеграм-канал</a>!',
            '🔔 Есть вопрос или предложение? <a href="https://t.me/hahahahahahahahaaahhahahahahaha">Тебе сюда</a>!'
        ],
        "index": 0,
        "rp_commands": {},
        "reputation": {},  # {user_id: {"rep": 0, "last_rep_time": 0}}
        "rep_cooldown": 300  # 5 минут
    }
    
    with open(FILE, 'w', encoding='utf-8') as f:
        json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    return default_data

# Загружаем данные
data = load_data()

def save():
    """Сохранение данных в файл"""
    try:
        with open(FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("💾 Данные сохранены")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")
        return False

def get_user_rep(user_id):
    """Получить данные репутации пользователя"""
    uid = str(user_id)
    if uid not in data["reputation"]:
        data["reputation"][uid] = {"rep": 0, "last_rep_time": 0}
        save()
    return data["reputation"][uid]

def change_rep(giver_id, target_id, amount):
    """Изменить репутацию"""
    giver_uid = str(giver_id)
    target_uid = str(target_id)
    
    # Нельзя менять свою репутацию
    if giver_id == target_id:
        return False, "❌ Нельзя менять свою репутацию!"
    
    # Проверяем кулдаун
    current_time = time.time()
    giver_data = get_user_rep(giver_id)
    
    if current_time - giver_data["last_rep_time"] < data["rep_cooldown"]:
        wait_time = int(data["rep_cooldown"] - (current_time - giver_data["last_rep_time"]))
        minutes = wait_time // 60
        seconds = wait_time % 60
        return False, f"⏳ Подожди {minutes} мин {seconds} сек перед следующим репом!"
    
    # Изменяем репутацию цели
    target_data = get_user_rep(target_id)
    target_data["rep"] += amount
    
    # Обновляем время последнего репа у дающего
    giver_data["last_rep_time"] = current_time
    
    # Сохраняем
    data["reputation"][giver_uid] = giver_data
    data["reputation"][target_uid] = target_data
    save()
    
    return True, f"✅ Репутация изменена на {amount}"

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
            logger.error(f"❌ Ошибка отправки: {e}")
            return False
    return False

def scheduler():
    while True:
        time.sleep(data["interval"] * 60)
        send_reminder()

# ============ КОМАНДЫ РЕПУТАЦИИ ============

@bot.message_handler(commands=['prep'])
def plus_rep(m):
    """Добавить репутацию (+1)"""
    try:
        if m.chat.id != GROUP_ID:
            bot.reply_to(m, "❌ Только в группе!")
            return
        
        if not m.reply_to_message:
            bot.reply_to(m, "❌ Ответь на сообщение пользователя: /prep")
            return
        
        target = m.reply_to_message.from_user
        
        if target.is_bot:
            bot.reply_to(m, "❌ Нельзя давать репутацию ботам!")
            return
        
        result, message = change_rep(m.from_user.id, target.id, 1)
        bot.reply_to(m, message)
        
    except Exception as e:
        logger.error(f"Ошибка prep: {e}")
        bot.reply_to(m, "❌ Ошибка")

@bot.message_handler(commands=['mrep'])
def minus_rep(m):
    """Убрать репутацию (-1)"""
    try:
        if m.chat.id != GROUP_ID:
            bot.reply_to(m, "❌ Только в группе!")
            return
        
        if not m.reply_to_message:
            bot.reply_to(m, "❌ Ответь на сообщение пользователя: /mrep")
            return
        
        target = m.reply_to_message.from_user
        
        if target.is_bot:
            bot.reply_to(m, "❌ Нельзя менять репутацию ботам!")
            return
        
        result, message = change_rep(m.from_user.id, target.id, -1)
        bot.reply_to(m, message)
        
    except Exception as e:
        logger.error(f"Ошибка mrep: {e}")
        bot.reply_to(m, "❌ Ошибка")

@bot.message_handler(commands=['rep'])
def show_rep(m):
    """Показать репутацию"""
    try:
        if m.chat.id != GROUP_ID:
            bot.reply_to(m, "❌ Только в группе!")
            return
        
        # Если есть реплай - показываем репутацию того, кому ответили
        if m.reply_to_message:
            target = m.reply_to_message.from_user
        else:
            target = m.from_user
        
        user_data = get_user_rep(target.id)
        rep = user_data["rep"]
        rank = get_rank(rep)
        
        # Имя пользователя
        name = target.first_name
        if target.username:
            username = f"@{target.username}"
        else:
            username = name
        
        # Определяем следующий статус
        next_rank = None
        ranks = sorted(RANKINGS.keys())
        for threshold in ranks:
            if rep < threshold:
                next_rank = RANKINGS[threshold]
                need = threshold - rep
                break
        
        # Формируем ответ
        response = f"📊 Репутация {username}\n\n"
        response += f"⭐ Репутация: {rep}\n"
        response += f"🏅 Статус: {rank}\n"
        
        if next_rank:
            response += f"📈 До {next_rank}: {need} репа\n"
        
        # Добавляем информацию о кулдауне
        if str(m.from_user.id) in data["reputation"]:
            last_time = data["reputation"][str(m.from_user.id)]["last_rep_time"]
            current_time = time.time()
            if current_time - last_time < data["rep_cooldown"]:
                wait = int(data["rep_cooldown"] - (current_time - last_time))
                minutes = wait // 60
                seconds = wait % 60
                response += f"\n⏳ Кулдаун: {minutes} мин {seconds} сек"
            else:
                response += f"\n✅ Реп доступен!"
        
        bot.reply_to(m, response)
        
    except Exception as e:
        logger.error(f"Ошибка rep: {e}")
        bot.reply_to(m, "❌ Ошибка")

@bot.message_handler(commands=['toprep'])
def top_rep(m):
    """Топ репутации"""
    try:
        if m.chat.id != GROUP_ID:
            bot.reply_to(m, "❌ Только в группе!")
            return
        
        if not data["reputation"]:
            bot.reply_to(m, "📭 Нет данных о репутации")
            return
        
        # Сортируем по репутации
        sorted_users = sorted(
            data["reputation"].items(),
            key=lambda x: x[1]["rep"],
            reverse=True
        )[:10]  # Топ 10
        
        response = "🏆 Топ репутации:\n\n"
        position = 1
        
        for uid, rep_data in sorted_users:
            try:
                # Пытаемся получить пользователя
                user = bot.get_chat_member(m.chat.id, int(uid))
                name = user.user.first_name
                if user.user.username:
                    name = f"@{user.user.username}"
                
                rep = rep_data["rep"]
                rank = get_rank(rep)
                
                # Эмодзи для топ-3
                medal = ""
                if position == 1:
                    medal = "🥇 "
                elif position == 2:
                    medal = "🥈 "
                elif position == 3:
                    medal = "🥉 "
                
                response += f"{medal}{position}. {name} — {rep} реп ({rank})\n"
                position += 1
                
            except Exception as e:
                logger.error(f"Ошибка получения пользователя {uid}: {e}")
        
        bot.reply_to(m, response)
        
    except Exception as e:
        logger.error(f"Ошибка toprep: {e}")
        bot.reply_to(m, "❌ Ошибка")

# ============ ИГРА БЯКА ============

@bot.message_handler(func=lambda m: m.chat.id == GROUP_ID and m.text and m.text.lower().startswith('бяка'))
def handle_byaka(m):
    """Игра Бяка"""
    try:
        text = m.text.lower()
        rest = text[5:].strip()
        
        if not rest:
            bot.reply_to(m, "❌ Напиши: бяка кто [действие]")
            return
        
        # Проверяем на "кто"
        if rest.startswith("кто"):
            action = rest[3:].strip()
        else:
            action = rest
        
        if not action:
            bot.reply_to(m, "❌ Укажи действие")
            return
        
        # Получаем участников
        members = bot.get_chat_members(m.chat.id)
        candidates = []
        bot_id = bot.get_me().id
        
        for member in members:
            user = member.user
            if user.id != bot_id and user.id != m.from_user.id and not user.is_bot:
                candidates.append(user)
        
        if not candidates:
            bot.reply_to(m, "❌ Нет кандидатов 😅")
            return
        
        # Выбираем случайного
        chosen = random.choice(candidates)
        
        # Получаем репутацию выбранного
        user_rep = get_user_rep(chosen.id)
        rep = user_rep["rep"]
        rank = get_rank(rep)
        
        # Формируем ответ с репутацией
        if chosen.username:
            username = f"@{chosen.username}"
        else:
            username = chosen.first_name
        
        response = f"🤔 Думаю, {username}\n"
        response += f"⭐ Репутация: {rep}\n"
        response += f"🏅 Статус: {rank}\n"
        response += f"📝 Действие: {action} 😄"
        
        bot.reply_to(m, response)
        
    except Exception as e:
        logger.error(f"Ошибка byaka: {e}")
        bot.reply_to(m, "❌ Ошибка")

# ============ РП КОМАНДЫ ============

@bot.message_handler(commands=['rp'])
def create_rp(m):
    try:
        if m.chat.id != GROUP_ID:
            bot.reply_to(m, "❌ Только в группе!")
            return
        
        text = m.text.replace("/rp", "", 1).strip()
        args = text.split('/')
        args = [arg.strip() for arg in args if arg.strip()]
        
        if len(args) < 3:
            bot.reply_to(m, 
                "❌ Формат: /rp команда/эмодзи/текст\n"
                "Пример: /rp обнять/♥️/обнял(а)"
            )
            return
        
        cmd = args[0].lower()
        emoji = args[1]
        action = args[2]
        user_id = str(m.from_user.id)
        
        if user_id not in data["rp_commands"]:
            data["rp_commands"][user_id] = {}
        
        if cmd in data["rp_commands"][user_id]:
            bot.reply_to(m, f"⚠️ Команда '{cmd}' уже есть!")
            return
        
        data["rp_commands"][user_id][cmd] = {"emoji": emoji, "text": action}
        save()
        
        bot.reply_to(m, 
            f"✅ Команда '{cmd}' создана!\n"
            f"Эмодзи: {emoji}\n"
            f"Действие: {action}\n\n"
            f"Используй: {cmd} @юзер"
        )
        
    except Exception as e:
        logger.error(f"Ошибка create_rp: {e}")
        bot.reply_to(m, "❌ Ошибка")

@bot.message_handler(commands=['rpdel'])
def delete_rp(m):
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
    try:
        if m.chat.id != GROUP_ID:
            bot.reply_to(m, "❌ Только в группе!")
            return
        
        if not data["rp_commands"]:
            bot.reply_to(m, "📭 Нет РП команд")
            return
        
        text = "📋 РП команды:\n\n"
        count = 0
        for uid, cmds in data["rp_commands"].items():
            try:
                user = bot.get_chat_member(m.chat.id, int(uid))
                name = user.user.first_name
                for cmd, info in cmds.items():
                    text += f"{name}: {cmd} {info['emoji']} ({info['text']})\n"
                    count += 1
                    if count >= 30:
                        text += "\n...и ещё"
                        break
            except:
                pass
        
        bot.reply_to(m, text)
        
    except Exception as e:
        logger.error(f"Ошибка list_rp: {e}")
        bot.reply_to(m, "❌ Ошибка")

# ============ ОБРАБОТКА РП (БЕЗ ПРЕФИКСА) ============

@bot.message_handler(func=lambda m: m.chat.id == GROUP_ID and m.text and not m.text.startswith('/'))
def handle_rp(m):
    try:
        text = m.text.strip()
        
        # Пропускаем бяка
        if text.lower().startswith('бяка'):
            return
        
        words = text.split()
        if not words:
            return
        
        cmd = words[0].lower()
        user_id = str(m.from_user.id)
        
        if user_id not in data["rp_commands"]:
            return
        
        if cmd not in data["rp_commands"][user_id]:
            return
        
        cmd_info = data["rp_commands"][user_id][cmd]
        emoji = cmd_info["emoji"]
        action = cmd_info["text"]
        
        # Ищем цель
        target = None
        target_text = " ".join(words[1:]) if len(words) > 1 else ""
        
        if m.reply_to_message:
            target = m.reply_to_message.from_user
        
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
        
        if not target:
            bot.reply_to(m, f"{emoji} {m.from_user.first_name} {action}")
        elif target.id == m.from_user.id:
            bot.reply_to(m, f"{emoji} {m.from_user.first_name} {action} себя 😄")
        else:
            bot.reply_to(m, f"{emoji} {m.from_user.first_name} {action} {target.first_name}")
            
    except Exception as e:
        logger.error(f"Ошибка handle_rp: {e}")

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
            "⭐ Репутация (в группе):\n"
            "/prep - +1 реп (реплай)\n"
            "/mrep - -1 реп (реплай)\n"
            "/rep - показать репутацию\n"
            "/toprep - топ репутации\n\n"
            "🎭 РП команды (в группе):\n"
            "/rp обнять/♥️/обнял(а) - создать\n"
            "/rpdel обнять - удалить\n"
            "/rplist - список\n\n"
            "🎲 Игра: бяка кто пойдёт гулять"
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
        total_users = len(data["reputation"])
        bot.reply_to(m,
            f"📊 Статус бота:\n"
            f"📝 Сообщений: {len(data['messages'])}\n"
            f"⏱️ Интервал: {data['interval']} мин\n"
            f"🎭 РП команд: {total_rp}\n"
            f"👥 Пользователей в репе: {total_users}\n"
            f"👥 Группа: {GROUP_ID}\n"
            f"💾 Данные сохранены в {FILE}"
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
logger.info(f"📁 Файл данных: {FILE}")
logger.info(f"👥 Пользователей в репе: {len(data['reputation'])}")

try:
    bot.send_message(GROUP_ID, "✅ Бот перезапущен! Репутация сохранена!")
except Exception as e:
    logger.error(f"Ошибка отправки: {e}")

threading.Thread(target=scheduler, daemon=True).start()
bot.infinity_polling()