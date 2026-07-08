import os
import random
import sqlite3
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)

# Enable basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Load configurations securely from Environment Variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_CHAT_ID", "8205491965"))
DB_NAME = "users.db"

# Matrix Configuration
VALID_ROWS = [0, 1, 2]  # Rows 1, 2, and 3
GRID_SIZE = 5

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, coins INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()

def get_coins(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def update_coins(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        new_balance = max(0, row[0] + amount)
        cursor.execute("UPDATE users SET coins = ? WHERE user_id = ?", (new_balance, user_id))
    else:
        new_balance = max(0, amount)
        cursor.execute("INSERT INTO users (user_id, coins) VALUES (?, ?)", (user_id, new_balance))
    conn.commit()
    conn.close()
    return new_balance

def generate_prediction_grid():
    grid = [["⬛" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    possible_spots = [(r, c) for r in VALID_ROWS for c in range(GRID_SIZE)]
    star_spots = random.sample(possible_spots, 3)
    for (r, c) in star_spots:
        grid[r][c] = "⭐"
    return "\n".join(" ".join(row) for row in grid)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    keyboard = [["🎯 Get Prediction", "💰 Check Balance"], ["💳 How to Deposit / Pay"]]
    await update.message.reply_text("Welcome! Use the buttons below.", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def handle_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if get_coins(user_id) < 2:
        await update.message.reply_text("❌ Insufficient coins! Please deposit.")
        return
    new_bal = update_coins(user_id, -2)
    await update.message.reply_text(f"🎯 Prediction:\n{generate_prediction_grid()}\n\nBalance: {new_bal} coins.")

async def handle_incoming_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
    await update.message.reply_text("✅ Screenshot sent to admin for verification.")

if __name__ == '__main__':
    init_db()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_incoming_screenshot))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("🎯 Get Prediction"), handle_prediction))
    application.run_polling()
