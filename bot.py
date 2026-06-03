import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import sqlite3

# 1. BOT TOKEN
TOKEN = "8862005997:AAGnKDRRaOTj4Nz9LA6NRMumHEu_d7ueNVA"
bot = telebot.TeleBot(TOKEN)

# 2. GROUP IDS
MAIN_GROUP_ID = -1003935974729
STORAGE_CHAT_ID = -1003962769274
START_MESSAGE_ID = 3
OWNER_ID = 1411317912

# 3. DATABASE SETUP
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
conn.commit()

# Helper function to check membership
def is_user_member(user_id):
    try:
        member = bot.get_chat_member(MAIN_GROUP_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    try:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ I Have Joined", callback_data="check_and_open"))
    bot.send_message(message.chat.id, "Bot use karne ke liye pehle group join karo!", reply_markup=markup)

# /stats command
@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id == OWNER_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f"📊 **Bot Total Users:** {total_users}")
    else:
        bot.send_message(message.chat.id, "❌ Yeh command aapke liye nahi hai.")

# Callback handler
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id

    if call.data == "check_and_open":
        if is_user_member(user_id):
            success_count = 0
            current_id = START_MESSAGE_ID
            empty_streak = 0

            bot.answer_callback_query(call.id, "Files bhej raha hoon...")

            while empty_streak < 20:
                try:
                    bot.copy_message(
                        chat_id=call.message.chat.id,
                        from_chat_id=STORAGE_CHAT_ID,
                        message_id=current_id,
                        protect_content=True
                    )
                    success_count += 1
                    empty_streak = 0
                except:
                    empty_streak += 1
                current_id += 1

            if success_count == 0:
                bot.send_message(call.message.chat.id, "⚠️ Storage me koi file nahi mili.")
            else:
                bot.send_message(call.message.chat.id, f"✅ Done! {success_count} files bhej di gayi hain.")
        else:
            bot.answer_callback_query(call.id, "❌ Pehle group join karo!", show_alert=True)

# Bot ko run karne ke liye
print("Secure Bot with Stats is running...")
bot.infinity_polling()
