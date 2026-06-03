import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import sqlite3
import threading
import os
from flask import Flask

# 1. BOT CONFIG (Original IDs)
TOKEN = "8862005997:AAGnKDRRaOTj4Nz9LA6NRMumHEu_d7ueNVA"
bot = telebot.TeleBot(TOKEN)

MAIN_GROUP_ID = -1003935974729
STORAGE_CHAT_ID = -1003962769274
START_MESSAGE_ID = 3
OWNER_ID = 1411317912

# 2. DATABASE SETUP
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
conn.commit()

# 3. WEB SERVER FOR RENDER (Keep-Alive)
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is active and running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# 4. FUNCTIONS
def is_user_member(user_id):
    try:
        member = bot.get_chat_member(MAIN_GROUP_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def delete_message_after_delay(chat_id, message_id, delay=60):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Delete error: {e}")

# 5. COMMANDS
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

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id == OWNER_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f"📊 **Bot Total Users:** {total_users}")
    else:
        bot.send_message(message.chat.id, "❌ Yeh command aapke liye nahi hai.")

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id
    if call.data == "check_and_open":
        if is_user_member(user_id):
            bot.answer_callback_query(call.id, "Files bhej raha hoon...")
            success_count = 0
            current_id = START_MESSAGE_ID
            empty_streak = 0

            while empty_streak < 20:
                try:
                    sent_msg = bot.copy_message(
                        chat_id=call.message.chat.id,
                        from_chat_id=STORAGE_CHAT_ID,
                        message_id=current_id,
                        protect_content=False
                    )
                    threading.Thread(
                        target=delete_message_after_delay, 
                        args=(call.message.chat.id, sent_msg.message_id, 60)
                    ).start()
                    success_count += 1
                    empty_streak = 0
                    time.sleep(0.5) 
                except:
                    empty_streak += 1
                current_id += 1

            if success_count > 0:
                warning_text = f"✅ **Done! {success_count} files bhej di gayi hain.**\n\n⚠️ **IMPORTANT:** Yeh files 1 MINUTE me delete ho jayengi!"
                warning_msg = bot.send_message(call.message.chat.id, warning_text, parse_mode="Markdown")
                threading.Thread(target=delete_message_after_delay, args=(call.message.chat.id, warning_msg.message_id, 60)).start()
        else:
            bot.answer_callback_query(call.id, "❌ Pehle group join karo!", show_alert=True)

# 6. RUN
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Secure Bot with Auto-Delete is running...")
    bot.infinity_polling()
    
