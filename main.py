import logging
import json
import os
import asyncio
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
# 👇 YOUR SETTINGS (Do not change unless needed)
# ======================================================

# 1. Aapka Bot Token (Jo aapne diya tha)
BOT_TOKEN = "8467195773:AAG9F7ckbEf_nFQUWgHqTsAuVKUfHciEjzQ"

# 2. Aapka MAIN CHANNEL ID (Jahan se message aayega)
SOURCE_CHANNEL_ID = -1003058384907

# 3. Database File (Automatic banegi)
DB_FILE = "connected_chats.json"

# ======================================================

# Logging Setup (Error tracking ke liye)
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- DATABASE SYSTEM (Auto-Save/Delete) ---
def load_chats():
    """File se saved groups/channels load karega."""
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Database Error: {e}")
        return []

def save_chat(chat_id):
    """Naya group/channel save karega."""
    chats = load_chats()
    if chat_id not in chats:
        chats.append(chat_id)
        with open(DB_FILE, 'w') as f:
            json.dump(chats, f)
        print(f"✅ LINKED: New Chat Connected ({chat_id})")

def remove_chat(chat_id):
    """Agar bot kick ho gaya to id hata dega."""
    chats = load_chats()
    if chat_id in chats:
        chats.remove(chat_id)
        with open(DB_FILE, 'w') as f:
            json.dump(chats, f)
        print(f"❌ REMOVED: Chat Disconnected ({chat_id})")

# --- 1. AUTO-DETECT (Admin bante hi ID save) ---
async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot ka status check karega (Admin/Member/Kicked)."""
    result = update.my_chat_member
    if not result: return

    new_status = result.new_chat_member.status
    chat_id = result.chat.id
    chat_title = result.chat.title or "Unknown Chat"

    # Agar Bot ko Add kiya ya Admin banaya
    if new_status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR]:
        save_chat(chat_id)
        logger.info(f"🔗 Connected to: {chat_title}")
    
    # Agar Bot ko nikal diya (Left/Kicked)
    elif new_status in [ChatMember.LEFT, ChatMember.BANNED]:
        remove_chat(chat_id)
        logger.info(f"💔 Disconnected from: {chat_title}")

# --- 2. FORWARDING LOGIC (With Forward Tag) ---
async def forward_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main Channel ka message sab jagah forward karega."""
    
    # Check: Kya message Main Channel se aaya hai?
    if update.effective_chat.id == SOURCE_CHANNEL_ID:
        # Message ID lo
        msg_id = update.effective_message.id
        
        # Saved chats load karo
        target_chats = load_chats()
        
        if not target_chats:
            print("⚠️ Warning: Bot kisi bhi group me nahi hai!")
            return

        print(f"📩 Post Detected! Forwarding to {len(target_chats)} chats...")
        
        success = 0
        failed = 0
        
        for chat_id in target_chats:
            # Khud ko wapis mat bhejo
            if chat_id == SOURCE_CHANNEL_ID: 
                continue
                
            try:
                # 🔥 YAHAN HAI MAGIC: 'forward_message' use karne se 
                # "Forwarded from..." ka Tag aayega.
                await context.bot.forward_message(
                    chat_id=chat_id,
                    from_chat_id=SOURCE_CHANNEL_ID,
                    message_id=msg_id
                )
                success += 1
            except Exception as e:
                # Agar koi error aaye (Bot kicked, permission denied)
                failed += 1
                logger.warning(f"⚠️ Failed to send to {chat_id}: {e}")
                # Optional: Agar permission denied hai to chat remove kar sakte hain
                # remove_chat(chat_id) 

        print(f"🚀 REPORT: Sent: {success} | Failed: {failed}")

# --- 3. STATUS CHECK ---
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chats = load_chats()
    await update.message.reply_text(f"📊 **Ultra Pro Bot Status:**\n\n✅ Connected Chats: {len(chats)}\n🚀 System: Online & Ready!")

# --- MAIN EXECUTION ---
def main():
    print("🤖 ULTRA PRO FORWARDER BOT STARTED...")
    print(f"📡 Monitoring Channel: {SOURCE_CHANNEL_ID}")
    
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.Chat(chat_id=SOURCE_CHANNEL_ID), forward_post))
    app.add_handler(CommandHandler("stats", stats_cmd))

    # Start Polling
    app.run_polling()

if __name__ == '__main__':
    main()
