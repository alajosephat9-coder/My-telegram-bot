import os
import sqlite3
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuration - Ensure these are set in your Render Environment Variables
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_CHAT_ID"))

# Database setup
conn = sqlite3.connect('bot_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance INTEGER)')
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Use /getprediction, /checkbalance, or /pay for details.")

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bank_info = (
        "💳 **Payment Information**\n\n"
        "Please make your transfer to the following account:\n\n"
        "**Bank Name:** Opay\n"
        "**Account Name:** Ala josephat unimangie\n"
        "**Account Number:** 8167440768\n\n"
        "After making the transfer, please send a screenshot of your payment to the Admin to receive your coins!"
    )
    await update.message.reply_text(bank_info, parse_mode='Markdown')

async def add_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Unauthorized.")
        return
    
    try:
        target_user = int(context.args[0])
        amount = int(context.args[1])
        cursor.execute('INSERT OR IGNORE INTO users (id, balance) VALUES (?, 0)', (target_user,))
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, target_user))
        conn.commit()
        await update.message.reply_text(f"Added {amount} coins to user {target_user}.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /addcoins <user_id> <amount>")

async def get_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    balance = row[0] if row else 0

    # Admin bypasses coin check; others need balance
    if user_id == ADMIN_ID or balance > 0:
        await update.message.reply_text("🌟 Signal Generated: [Star coordinates...]")
        if user_id != ADMIN_ID:
            cursor.execute('UPDATE users SET balance = balance - 1 WHERE id = ?', (user_id,))
            conn.commit()
    else:
        await update.message.reply_text("❌ Insufficient coins! Please deposit.")

# Initialize Bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("pay", pay))
app.add_handler(CommandHandler("addcoins", add_coins))
app.add_handler(CommandHandler("getprediction", get_prediction))

print("Bot is running...")
app.run_polling()
