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
# 👇 SETTINGS (DO NOT CHANGE)
# ======================================================

BOT_TOKEN = "8154391218:AAGm8qXYUHaoN6b8Ot6U7Dcc0zkwibbcwEI"
SOURCE_CHANNEL_ID = -1003058384907
DB_FILE = "connected_chats.json"

# 🔥 PERMANENT LIST (Updated with ALL IDs)
PERMANENT_GROUPS = [
    # Old List
    -1002554467279, -1003614519401, -1003671065660, -1003530653689,
    -1003394404055, -1003386859636, -1003584586389, -1003698713874,
    -1003447302984, -1003650175289, -1003418788520, -1003699928112,
    -1003693513496, -1003412241173, -1003591240948, -1003545211632,
    -1003334168204, -1003606493371, -1003686349611, -1003105670231,
    -1003283931383, -1003464518144,
    
    # New Added IDs
    -1003531237188, -1003546040666, -1003684473925, -1003393758583,
    -1003320689404, -1003647673748, -1003244767515, -1003437946111
]

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
    return "BW Bot is Running Permanently! 🚀"

def run_http():
    app_web.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# --- CHAT MANAGEMENT (Hybrid System) ---
def get_all_chats():
    """Permanent List + New Auto-Detected Chats ko mix karega"""
    
    # 1. Start with Permanent List
    all_chats = set(PERMANENT_GROUPS)
    
    # 2. Add New Chats from File (if any)
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                saved_chats = json.load(f)
                all_chats.update(saved_chats)
        except:
            pass
            
    return list(all_chats)

def save_new_chat(chat_id):
    """Sirf naye groups ko file me save karega"""
    if chat_id in PERMANENT_GROUPS:
        return # Already hardcoded hai

    current_saved = []
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                current_saved = json.load(f)
        except:
            current_saved = []

    if chat_id not in current_saved:
        current_saved.append(chat_id)
        with open(DB_FILE, 'w') as f:
            json.dump(current_saved, f)
        print(f"✅ NEW Group Saved to File: {chat_id}")

# --- START COMMAND ---
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != SOURCE_CHANNEL_ID:
        save_new_chat(chat_id)
        await update.message.reply_text("✅ BW System Connected! (Permanent Mode)")
    else:
        await update.message.reply_text("👋 BW Bot is Online & Ready!")

# --- AUTO-DETECT ---
async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if not result: return
    new_status = result.new_chat_member.status
    chat_id = result.chat.id
    
    if new_status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR]:
        save_new_chat(chat_id)

# --- FORWARDING LOGIC (Bulletproof) ---
async def forward_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Sirf Main Channel se messages accept karo
    if not update.effective_chat or update.effective_chat.id != SOURCE_CHANNEL_ID:
        return

    msg_id = update.effective_message.id
    
    # Load all chats (Fixed + New)
    target_chats = get_all_chats()
    
    print(f"📩 Post Detected! Sending to {len(target_chats)} Groups...")
    
    success = 0
    failed = 0
    
    for chat_id in target_chats:
        # Loop se bachne ke liye (Main channel me wapis mat bhejo)
        if chat_id == SOURCE_CHANNEL_ID: 
            continue
            
        try:
            # 1. Forward Message
            sent_msg = await context.bot.forward_message(
                chat_id=chat_id,
                from_chat_id=SOURCE_CHANNEL_ID,
                message_id=msg_id
            )
            
            # 2. Pin Message (Optional)
            try:
                await context.bot.pin_chat_message(
                    chat_id=chat_id, 
                    message_id=sent_msg.message_id
                )
            except:
                pass # Pin fail hua to koi baat nahi (Permission issue)

            success += 1
        except Exception as e:
            failed += 1
            print(f"⚠️ Fail: {chat_id} | Error: {e}")

    print(f"🚀 Report: Sent {success} | Failed {failed}")

# --- STATUS CHECK ---
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = len(get_all_chats())
    await update.message.reply_text(f"📊 **BW System Status:**\n✅ Total Target Groups: {total}\n🔒 Permanent Mode: ON")

# --- MAIN ---
def main():
    keep_alive()
    print("🤖 BW PERMANENT BOT STARTED...")
    
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
    
    # Message Handler
    app.add_handler(MessageHandler(filters.Chat(chat_id=SOURCE_CHANNEL_ID), forward_post))

    app.run_polling()

if __name__ == '__main__':
    main()
