import logging
import json
import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, ChatMember
from telegram.ext import (
    Application, 
    MessageHandler, 
    ContextTypes, 
    filters, 
    ChatMemberHandler,
    CommandHandler
)

# ======================================================
# 👇 SETTINGS 
# ======================================================

BOT_TOKEN = "8467195773:AAG9F7ckbEf_nFQUWgHqTsAuVKUfHciEjzQ"
SOURCE_CHANNEL_ID = -1003058384907
DB_FILE = "connected_chats.json"

# ======================================================

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- SERVER (Keep Alive) ---
app_web = Flask('')

@app_web.route('/')
def home():
    return "BW Bot is Running! 🚀"

def run_http():
    app_web.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# --- DATABASE ---
def load_chats():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_chat(chat_id):
    chats = load_chats()
    if chat_id not in chats:
        chats.append(chat_id)
        with open(DB_FILE, 'w') as f:
            json.dump(chats, f)
        print(f"✅ DATA SAVED: {chat_id}")

def remove_chat(chat_id):
    chats = load_chats()
    if chat_id in chats:
        chats.remove(chat_id)
        with open(DB_FILE, 'w') as f:
            json.dump(chats, f)
        print(f"❌ DATA REMOVED: {chat_id}")

# --- START COMMAND ---
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Agar user group me /start dabaye to use save kar lo
    if chat_id != SOURCE_CHANNEL_ID:
        save_chat(chat_id)
        await update.message.reply_text("✅ Group Connected Successfully!")
    else:
        await update.message.reply_text("BW Bot Active! 🟢")

# --- AUTO-DETECT ---
async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if not result: return
    new_status = result.new_chat_member.status
    chat_id = result.chat.id
    if new_status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR]:
        save_chat(chat_id)
    elif new_status in [ChatMember.LEFT, ChatMember.BANNED]:
        remove_chat(chat_id)

# --- FORWARDING LOGIC (FIXED) ---
async def forward_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if update is valid
    if not update.effective_chat or update.effective_chat.id != SOURCE_CHANNEL_ID:
        return

    msg = update.effective_message
    msg_id = msg.id
    
    # 🔍 DEBUG: Check database
    target_chats = load_chats()
    print(f"📩 New Post! Forwarding to {len(target_chats)} groups...")

    if not target_chats:
        print("⚠️ ERROR: Group List is Empty! (Render ne file delete kar di hogi)")
        print("👉 Solution: Groups me dubara /start bhejo ya Bot ko remove karke add karo.")
        return
    
    success = 0
    for chat_id in target_chats:
        if chat_id == SOURCE_CHANNEL_ID: continue
        try:
            # Step 1: Forward
            sent = await context.bot.forward_message(
                chat_id=chat_id,
                from_chat_id=SOURCE_CHANNEL_ID,
                message_id=msg_id
            )
            # Step 2: Pin
            try:
                await context.bot.pin_chat_message(chat_id=chat_id, message_id=sent.message_id)
            except:
                pass # Pin fail ho to ignore karo
            success += 1
        except Exception as e:
            print(f"⚠️ Failed for {chat_id}: {e}")

    print(f"🚀 Sent to {success} Groups!")

# --- MAIN ---
def main():
    keep_alive()
    print("🤖 BW BOT RELOADED...")
    
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("stats", start_cmd)) # Stats check
    
    # Admin Tracker
    app.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))

    # 🔥 POWERFUL FILTER: Handles Channel Posts & Messages
    # Ye line sabse important hai 👇
    app.add_handler(MessageHandler(filters.Chat(chat_id=SOURCE_CHANNEL_ID), forward_post))

    app.run_polling()

if __name__ == '__main__':
    main()
