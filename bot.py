import telebot
import time
import threading
import json
import os
import sys
import logging
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import textwrap
import requests
import re

# Убираем reload(sys) - он не нужен в Python 3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не установлен")
    sys.exit(1)

ADMIN_ID = int(os.environ.get("ADMIN_ID", "8788760253"))
FILE = "data.json"
FRAME_FILE = "frame.png"
bot = telebot.TeleBot(BOT_TOKEN)

try:
    bot.get_me()
    logger.info("✅ Бот авторизован!")
except Exception as e:
    logger.error(f"❌ Ошибка: {e}")
    sys.exit(1)

# ============ ДАННЫЕ ============

def load_data():
    if os.path.exists(FILE):
        try:
            with open(FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "reputation" not in data:
                    data["reputation"] = {}
                if "rep_cooldown" not in data:
                    data["rep_cooldown"] = 300
                if "interval" not in data:
                    data["interval"] = 45
                if "messages" not in data:
                    data["messages"] = []
                if "index" not in data:
                    data["index"] = 0
                return data
        except Exception as e:
            logger.error(f"Ошибка загрузки: {e}")
    
    default_data = {
        "interval": 45,
        "messages": [],
        "index": 0,
        "reputation": {},
        "rep_cooldown": 300
    }
    
    with open(FILE, 'w', encoding='utf-8') as f:
        json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    return default_data

data = load_data()

def save():
    try:
        with open(FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        return False

# ============ РЕПУТАЦИЯ ============

RANKINGS = [
    (-100, "Призрак"),
    (-75, "Тень"),
    (-50, "Недостойный"),
    (-25, "Опущенный"),
    (-10, "Тёмный друн"),
    (0, "Друн"),
    (10, "Бурмалда"),
    (25, "Сократ"),
    (50, "Босс"),
    (75, "Легенда"),
    (100, "Бог")
]

def get_rank(rep):
    for i in range(len(RANKINGS) - 1, -1, -1):
        threshold, rank = RANKINGS[i]
        if rep >= threshold:
            return rank
    return RANKINGS[0][1]

def get_user_rep(user_id):
    uid = str(user_id)
    if uid not in data["reputation"]:
        data["reputation"][uid] = {"rep": 0, "last_rep_time": 0}
        save()
    return data["reputation"][uid]

def change_rep(giver_id, target_id, amount):
    if giver_id == target_id:
        return False, "❌ Нельзя менять свою репутацию!"
    
    current_time = time.time()
    giver_data = get_user_rep(giver_id)
    
    if current_time - giver_data["last_rep_time"] < data["rep_cooldown"]:
        wait_time = int(data["rep_cooldown"] - (current_time - giver_data["last_rep_time"]))
        minutes = wait_time // 60
        seconds = wait_time % 60
        return False, f"⏳ Подожди {minutes} мин {seconds} сек!"
    
    target_data = get_user_rep(target_id)
    target_data["rep"] += amount
    giver_data["last_rep_time"] = current_time
    
    data["reputation"][str(giver_id)] = giver_data
    data["reputation"][str(target_id)] = target_data
    save()
    
    return True, f"✅ {'+' if amount > 0 else ''}{amount} реп!"

# ============ ЗАГРУЗКА РАМКИ ============

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    try:
        if m.from_user.id != ADMIN_ID:
            return
        if not m.caption or m.caption.lower() not in ['/setframe', 'рамка']:
            return
        
        photo = m.photo[-1]
        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(FRAME_FILE, 'wb') as f:
            f.write(downloaded_file)
        
        try:
            img = Image.open(FRAME_FILE)
            img.verify()
            bot.reply_to(m, f"✅ Рамка установлена!")
            logger.info(f"✅ Рамка сохранена")
        except Exception as e:
            bot.reply_to(m, f"❌ Файл повреждён: {e}")
            os.remove(FRAME_FILE)
            
    except Exception as e:
        logger.error(f"Ошибка загрузки фото: {e}")
        bot.reply_to(m, f"❌ Ошибка: {e}")

@bot.message_handler(content_types=['document'])
def handle_document(m):
    try:
        if m.from_user.id != ADMIN_ID:
            return
        if not m.caption or m.caption.lower() not in ['/setframe', 'рамка']:
            return
        
        doc = m.document
        if doc.mime_type != "image/png":
            bot.reply_to(m, "❌ Отправь PNG файл!")
            return
        
        file_info = bot.get_file(doc.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(FRAME_FILE, 'wb') as f:
            f.write(downloaded_file)
        
        try:
            img = Image.open(FRAME_FILE)
            img.verify()
            bot.reply_to(m, f"✅ Рамка установлена!")
            logger.info(f"✅ Рамка сохранена")
        except Exception as e:
            bot.reply_to(m, f"❌ Файл повреждён: {e}")
            os.remove(FRAME_FILE)
            
    except Exception as e:
        logger.error(f"Ошибка загрузки документа: {e}")
        bot.reply_to(m, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['getframe'])
def get_frame(m):
    try:
        if m.from_user.id != ADMIN_ID:
            return
        if os.path.exists(FRAME_FILE):
            with open(FRAME_FILE, 'rb') as f:
                bot.send_photo(m.chat.id, f, caption="🖼️ Текущая рамка")
        else:
            bot.reply_to(m, "❌ Рамка не установлена")
    except Exception as e:
        logger.error(f"Ошибка getframe: {e}")
        bot.reply_to(m, "❌ Ошибка")

# ============ СОЗДАНИЕ ЦИТАТЫ ============

def remove_emojis(text):
    """Удаляет эмодзи из текста"""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # эмотиконы
        u"\U0001F300-\U0001F5FF"  # символы
        u"\U0001F680-\U0001F6FF"  # транспорт
        u"\U0001F1E0-\U0001F1FF"  # флаги
        u"\U00002500-\U00002BEF"  # китайские символы
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"
        u"\u3030"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def create_quote_image(text, user_info):
    """Создаёт цитату с аватаркой и рамкой"""
    size = 512
    avatar_size = 80
    padding = 30
    
    # Создаём фон
    bg = Image.new('RGBA', (size, size), (20, 20, 20, 255))
    
    # Загружаем рамку
    if os.path.exists(FRAME_FILE):
        try:
            frame = Image.open(FRAME_FILE).convert("RGBA")
            frame = frame.resize((size, size), Image.Resampling.LANCZOS)
            bg.paste(frame, (0, 0), frame)
        except Exception as e:
            logger.error(f"Ошибка загрузки рамки: {e}")
    
    draw = ImageDraw.Draw(bg)
    
    # Шрифты
    try:
        font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'font.ttf')
        if os.path.exists(font_path):
            font_text = ImageFont.truetype(font_path, 24)
            font_name = ImageFont.truetype(font_path, 18)
            font_rep = ImageFont.truetype(font_path, 14)
        else:
            font_text = ImageFont.load_default()
            font_name = ImageFont.load_default()
            font_rep = ImageFont.load_default()
    except:
        font_text = ImageFont.load_default()
        font_name = ImageFont.load_default()
        font_rep = ImageFont.load_default()
    
    # Аватарка
    avatar = None
    if user_info.get('avatar'):
        try:
            response = requests.get(user_info['avatar'], timeout=10)
            avatar = Image.open(io.BytesIO(response.content)).convert("RGBA")
            avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
            mask = Image.new('L', (avatar_size, avatar_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
            avatar.putalpha(mask)
        except:
            avatar = None
    
    # Вставляем аватарку
    avatar_x = padding
    avatar_y = padding
    if avatar:
        bg.paste(avatar, (avatar_x, avatar_y), avatar)
    else:
        draw.ellipse(
            [(avatar_x, avatar_y), (avatar_x + avatar_size, avatar_y + avatar_size)],
            fill=(100, 100, 100),
            outline=(200, 200, 200),
            width=2
        )
        draw.text(
            (avatar_x + avatar_size//2 - 10, avatar_y + avatar_size//2 - 15),
            "User",
            font=font_text,
            fill=(255, 255, 255)
        )
    
    # Имя (очищаем от эмодзи)
    name = remove_emojis(user_info['name']) or "User"
    draw.text((avatar_x + avatar_size + 15, avatar_y + 5), name, font=font_name, fill=(255, 255, 255))
    
    # Репутация
    rep_text = f"⭐ {user_info['rep']} | {user_info['rank']}"
    draw.text((avatar_x + avatar_size + 15, avatar_y + 27), rep_text, font=font_rep, fill=(255, 215, 0))
    
    # Текст цитаты (очищаем от эмодзи)
    quote_text = remove_emojis(user_info['text'])
    if len(quote_text) > 200:
        quote_text = quote_text[:197] + "..."
    
    wrapped = textwrap.wrap(quote_text, width=28)
    if len(wrapped) > 6:
        wrapped = wrapped[:5] + ['...']
    
    line_height = 32
    total_height = len(wrapped) * line_height
    text_start_y = (size - total_height) // 2 + 20
    
    for i, line in enumerate(wrapped):
        y = text_start_y + i * line_height
        try:
            bbox = draw.textbbox((0, 0), line, font=font_text)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = len(line) * 14
        x = (size - text_width) // 2
        draw.text((x, y), line, font=font_text, fill=(255, 255, 255))
    
    # Подпись внизу
    footer_text = user_info.get('username') or user_info['name']
    footer_text = remove_emojis(footer_text) or "User"
    footer_text = f"— {footer_text}"
    try:
        bbox = draw.textbbox((0, 0), footer_text, font=font_name)
        footer_width = bbox[2] - bbox[0]
    except:
        footer_width = len(footer_text) * 10
    x = size - footer_width - padding
    y = size - padding - 10
    draw.text((x, y), footer_text, font=font_name, fill=(255, 215, 0))
    
    # Сохраняем
    img_byte_arr = io.BytesIO()
    bg.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr

# ============ КОМАНДЫ ============

@bot.message_handler(commands=['q'])
def quote_cmd(m):
    """Создание цитаты"""
    try:
        if m.chat.type != "group" and m.chat.type != "supergroup":
            bot.reply_to(m, "❌ Только в группах!")
            return
        
        if not m.reply_to_message:
            bot.reply_to(m, "❌ Ответь на сообщение: /q")
            return
        
        quote_msg = m.reply_to_message
        user = quote_msg.from_user
        
        # Аватарка
        avatar_url = None
        try:
            profile_photos = bot.get_user_profile_photos(user.id, limit=1)
            if profile_photos.total_count > 0:
                file_id = profile_photos.photos[0][-1].file_id
                file_info = bot.get_file(file_id)
                avatar_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        except:
            pass
        
        # Текст
        text = quote_msg.text or quote_msg.caption or "Сообщение без текста"
        
        # Репутация
        user_rep = get_user_rep(user.id)
        rep = user_rep["rep"]
        rank = get_rank(rep)
        
        user_info = {
            'name': user.first_name,
            'username': user.username,
            'text': text,
            'rep': rep,
            'rank': rank,
            'avatar': avatar_url
        }
        
        # Создаём цитату
        img_bytes = create_quote_image(text, user_info)
        
        # Отправляем
        bot.send_photo(
            m.chat.id,
            img_bytes,
            caption=f"📝 Цитата от {user.first_name}",
            reply_to_message_id=m.message_id
        )
        
    except Exception as e:
        logger.error(f"Ошибка q: {e}")
        bot.reply_to(m, f"❌ Ошибка: {str(e)[:50]}")

# ============ РЕПУТАЦИЯ ============

@bot.message_handler(commands=['prep'])
def plus_rep(m):
    if m.chat.type != "group" and m.chat.type != "supergroup":
        return
    if not m.reply_to_message:
        bot.reply_to(m, "❌ Ответь на сообщение: /prep")
        return
    target = m.reply_to_message.from_user
    if target.is_bot:
        bot.reply_to(m, "❌ Нельзя давать репутацию ботам!")
        return
    result, message = change_rep(m.from_user.id, target.id, 1)
    bot.reply_to(m, message)

@bot.message_handler(commands=['mrep'])
def minus_rep(m):
    if m.chat.type != "group" and m.chat.type != "supergroup":
        return
    if not m.reply_to_message:
        bot.reply_to(m, "❌ Ответь на сообщение: /mrep")
        return
    target = m.reply_to_message.from_user
    if target.is_bot:
        bot.reply_to(m, "❌ Нельзя менять репутацию ботам!")
        return
    result, message = change_rep(m.from_user.id, target.id, -1)
    bot.reply_to(m, message)

@bot.message_handler(commands=['rep'])
def show_rep(m):
    if m.chat.type != "group" and m.chat.type != "supergroup":
        return
    target = m.reply_to_message.from_user if m.reply_to_message else m.from_user
    user_rep = get_user_rep(target.id)
    rep = user_rep["rep"]
    rank = get_rank(rep)
    name = f"@{target.username}" if target.username else target.first_name
    response = f"📊 Репутация {name}\n\n⭐ {rep} реп\n🏅 {rank}"
    bot.reply_to(m, response)

@bot.message_handler(commands=['toprep'])
def top_rep(m):
    if m.chat.type != "group" and m.chat.type != "supergroup":
        return
    if not data["reputation"]:
        bot.reply_to(m, "📭 Нет данных")
        return
    sorted_users = sorted(data["reputation"].items(), key=lambda x: x[1]["rep"], reverse=True)[:10]
    response = "🏆 Топ репутации:\n\n"
    for i, (uid, rep_data) in enumerate(sorted_users, 1):
        try:
            user = bot.get_chat_member(m.chat.id, int(uid))
            name = f"@{user.user.username}" if user.user.username else user.user.first_name
            rep = rep_data["rep"]
            rank = get_rank(rep)
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            response += f"{medal} {name} — {rep} реп ({rank})\n"
        except:
            pass
    bot.reply_to(m, response)

# ============ ПОМОЩЬ ============

@bot.message_handler(commands=['start', 'help'])
def help_cmd(m):
    if m.from_user.id == ADMIN_ID:
        bot.reply_to(m,
            "👑 Команды бота:\n\n"
            "📝 ЦИТАТЫ:\n"
            "/q (реплай) — создать цитату\n\n"
            "🖼️ РАМКА:\n"
            "Отправь фото с подписью /setframe\n"
            "Или отправь PNG с подписью /setframe\n"
            "/getframe — показать текущую рамку\n\n"
            "⭐ РЕПУТАЦИЯ:\n"
            "/prep (реплай) — +1 реп\n"
            "/mrep (реплай) — -1 реп\n"
            "/rep — показать репутацию\n"
            "/toprep — топ репутации"
        )

# ============ ЗАПУСК ============

logger.info("🔥 Бот запущен!")
logger.info(f"👑 Админ: {ADMIN_ID}")

if os.path.exists(FRAME_FILE):
    logger.info("🖼️ Рамка найдена")
else:
    logger.info("🖼️ Рамка не установлена")

try:
    bot.send_message(ADMIN_ID, "✅ Бот запущен!\n\nОтправь фото с подписью /setframe чтобы установить рамку")
except:
    pass

bot.infinity_polling()