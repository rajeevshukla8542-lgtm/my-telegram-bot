import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import sqlite3
import threading

# 1. BOT TOKEN
TOKEN = "8862005997:AAGnKDRRaOTj4Nz9LA6NRMumHEu_d7ueNVA"
bot = telebot.TeleBot(TOKEN)

# 2. GROUP IDS
MAIN_GROUP_ID = -1003935974729
STORAGE_CHAT_ID = -1003962769274
START_MESSAGE_ID = 3
OWNER_ID = 1411317912  # Aapki asli ID set hai

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

# Function to delete message after delay
def delete_message_after_delay(chat_id, message_id, delay=60):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Delete error: {e}")

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
                    # YAHAN protect_content=False kiya hai taaki user save/forward kar sake 1 min me
                    sent_msg = bot.copy_message(
                        chat_id=call.message.chat.id,
                        from_chat_id=STORAGE_CHAT_ID,
                        message_id=current_id,
                        protect_content=False
                    )
                    
                    # File ko 1 minute (60 seconds) baad delete karne ka timer
                    threading.Thread(
                        target=delete_message_after_delay, 
                        args=(call.message.chat.id, sent_msg.message_id, 60)
                    ).start()

                    success_count += 1
                    empty_streak = 0
                except:
                    empty_streak += 1
                current_id += 1

            if success_count == 0:
                bot.send_message(call.message.chat.id, "⚠️ Storage me koi file nahi mili.")
            else:
                # User ko clear warning aur tarika batana
                warning_text = (
                    f"✅ **Done! {success_count} files bhej di gayi hain.**\n\n"
                    "⚠️ **IMPORTANT NOTICE:**\n"
                    "Copyright issues ki wajah se yeh saari files **1 MINUTE** me is chat se automatic delete ho jayengi! "
                    "Jaldi se is file ko select karke apne **'Saved Messages'** ya kisi doosre chat me forward (save) kar lo."
                )
                warning_msg = bot.send_message(call.message.chat.id, warning_text, parse_mode="Markdown")
                
                # Yeh warning message bhi 1 minute baad khud gayab ho jayega
                threading.Thread(
                    target=delete_message_after_delay, 
                    args=(call.message.chat.id, warning_msg.message_id, 60)
                ).start()
        else:
            bot.answer_callback_query(call.id, "❌ Pehle group join karo!", show_alert=True)

# Bot ko run karne ke liye
print("Secure Bot with Auto-Delete & Forward Enabled is running...")
bot.infinity_polling()
