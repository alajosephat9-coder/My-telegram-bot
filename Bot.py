import os
import sqlite3
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest
from flask import Flask
from threading import Thread

# 1. Setup Flask "Health Check" Server to keep Render happy
app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Bot is alive!"
def run_web():
    app_web.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
Thread(target=run_web, daemon=True).start()

# 2. Configuration & DB
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_CHAT_ID"))

conn = sqlite3.connect('bot_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance INTEGER)')
conn.commit()

# ... (Keep your existing start, pay, add_coins, and get_prediction functions exactly as they are) ...

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Use /getprediction or /pay for details.")

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bank_info = ("💳 **Payment Info**\n\nBank: Opay\nAccount: Ala josephat unimangie\nNumber: 8167440768")
    await update.message.reply_text(bank_info, parse_mode='Markdown')

async def add_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_user, amount = int(context.args[0]), int(context.args[1])
        cursor.execute('INSERT OR IGNORE INTO users (id, balance) VALUES (?, 0)', (target_user,))
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, target_user))
        conn.commit()
        await update.message.reply_text(f"Added {amount} coins to {target_user}.")
    except: await update.message.reply_text("Usage: /addcoins <id> <amount>")

async def get_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    balance = row[0] if row else 0
    if user_id == ADMIN_ID or balance > 0:
        await update.message.reply_text("🌟 Signal Generated!")
        if user_id != ADMIN_ID:
            cursor.execute('UPDATE users SET balance = balance - 1 WHERE id = ?', (user_id,))
            conn.commit()
    else:
        await update.message.reply_text("❌ Insufficient coins!")

# 3. Initialization
request = HTTPXRequest(connect_timeout=60.0, read_timeout=60.0)
app = ApplicationBuilder().token(TOKEN).request(request).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("pay", pay))
app.add_handler(CommandHandler("addcoins", add_coins))
app.add_handler(CommandHandler("getprediction", get_prediction))

print("Bot is running...")
app.run_polling()
