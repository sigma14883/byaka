import telebot
import time
import threading
import json
import os
import sys
import logging

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

# Статусы по репутации (порядок от меньшего к большему)
RANKINGS = [
    (-100, "👻 Призрак"),
    (-75, "💀 Тень"),
    (-50, "😈 Недостойный"),
    (-25, "😔 Опущенный"),
    (-10, "🥴 Тёмный друн"),
    (0, "🍺 Друн"),
    (10, "😎 Бурмалда"),
    (25, "🧠 Сократ"),
    (50, "👑 Босс"),
    (75, "⭐ Легенда"),
    (100, "🔥 Бог")
]

def get_rank(rep):
    """Получить статус по репутации"""
    # Идём с конца (от большего к меньшему)
    for i in range(len(RANKINGS) - 1, -1, -1):
        threshold, rank = RANKINGS[i]
        if rep >= threshold:
            return rank
    # Если репутация меньше -100
    return RANKINGS[0][1]

def load_data():
    """Загрузка данных из файла"""
    if os.path.exists(FILE):
        try:
            with open(FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "reputation" not in data:
                    data["reputation"] = {}
                if "rep_cooldown" not in data:
                    data["rep_cooldown"] = 300
                if "messages" not in data:
                    data["messages"] = [
                        '🔔 Не забудь зайти в наш <a href="https://discord.gg/AqjCnK77c">Дискорд-сервер</a>!',
                        '🔔 Подпишись на мой <a href="https://t.me/killer2017official">Телеграм-канал</a>!',
                        '🔔 Есть вопрос или предложение? <a href="https://t.me/hahahahahahahahaaahhahahahahaha">Тебе сюда</a>!'
                    ]
                if "interval" not in data:
                    data["interval"] = 45
                if "index" not in data:
                    data["index"] = 0
                
                logger.info(f"✅ Данные загружены из {FILE}")
                logger.info(f"📊 Пользователей в репутации: {len(data.get('reputation', {}))}")
                return data
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки: {e}")
    
    logger.info("🆕 Создаём новый файл данных")
    default_data = {
        "interval": 5,
        "messages": [
            '🔔 Не забудь зайти в наш <a href="https://discord.gg/AqjCnK77c">Дискорд-сервер</a>!',
            '🔔 Подпишись на мой <a href="https://t.me/killer2017official">Телеграм-канал</a>!',
            '🔔 Есть вопрос или предложение? <a href="https://t.me/hahahahahahahahaaahhahahahahaha">Тебе сюда</a>!'
        ],
        "index": 0,
        "reputation": {},
        "rep_cooldown": 300
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
    
    if amount > 0:
        return True, f"✅ +1 реп пользователю!"
    else:
        return True, f"✅ -1 реп пользователю!"

def send_reminder():
    if data["messages"]:
        msg = data["messages"][data["index"]]
        data["index"] = (data["index"] + 1) % len(data["messages"])
        save()
        try:
            bot.send_message(GROUP_ID, msg, parse_mode="HTML", disable_web_page_preview=True)
            logger.info("✅ Отправлено")
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
        
        if m.reply_to_message:
            target = m.reply_to_message.from_user
        else:
            target = m.from_user
        
        user_data = get_user_rep(target.id)
        rep = user_data["rep"]
        rank = get_rank(rep)
        
        name = target.first_name
        if target.username:
            username = f"@{target.username}"
        else:
            username = name
        
        # Определяем следующий статус
        next_rank = None
        need = None
        for threshold, rank_name in RANKINGS:
            if rep < threshold:
                next_rank = rank_name
                need = threshold - rep
                break
        
        response = f"📊 Репутация {username}\n\n"
        response += f"⭐ Репутация: {rep}\n"
        response += f"🏅 Статус: {rank}\n"
        
        if next_rank and need:
            response += f"📈 До {next_rank}: {need} репа\n"
        
        # Кулдаун для автора
        giver_data = get_user_rep(m.from_user.id)
        current_time = time.time()
        if current_time - giver_data["last_rep_time"] < data["rep_cooldown"]:
            wait = int(data["rep_cooldown"] - (current_time - giver_data["last_rep_time"]))
            minutes = wait // 60
            seconds = wait % 60
            response += f"\n⏳ Твой кулдаун: {minutes} мин {seconds} сек"
        else:
            response += f"\n✅ Ты можешь ставить реп!"
        
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
        
        sorted_users = sorted(
            data["reputation"].items(),
            key=lambda x: x[1]["rep"],
            reverse=True
        )[:10]
        
        response = "🏆 Топ репутации:\n\n"
        position = 1
        
        for uid, rep_data in sorted_users:
            try:
                user = bot.get_chat_member(m.chat.id, int(uid))
                name = user.user.first_name
                if user.user.username:
                    name = f"@{user.user.username}"
                
                rep = rep_data["rep"]
                rank = get_rank(rep)
                
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
            "⭐ Команды репутации (в группе):\n"
            "/prep (реплай) - +1 реп\n"
            "/mrep (реплай) - -1 реп\n"
            "/rep - показать репутацию\n"
            "/toprep - топ репутации\n\n"
            "⏳ Кулдаун: 5 минут"
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
        total_users = len(data["reputation"])
        bot.reply_to(m,
            f"📊 Статус бота:\n"
            f"📝 Сообщений: {len(data['messages'])}\n"
            f"⏱️ Интервал: {data['interval']} мин\n"
            f"👥 Пользователей в репе: {total_users}\n"
            f"👥 Группа: {GROUP_ID}\n"
            f"💾 Данные сохранены в {FILE}\n"
            f"⏳ Кулдаун: {data['rep_cooldown']//60} мин"
        )

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
    bot.send_message(GROUP_ID, "✅ Бот перезапущен! Репутация работает!")
except Exception as e:
    logger.error(f"Ошибка отправки: {e}")

threading.Thread(target=scheduler, daemon=True).start()
bot.infinity_polling()