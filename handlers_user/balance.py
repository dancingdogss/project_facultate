from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from models import load_json, save_json
from config import DEFAULT_START_COINS

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    balances = load_json("balances.json", {})
    balance = balances.get(user_id, DEFAULT_START_COINS)
    await update.message.reply_text(f"💰 You have {balance} coins.")

async def deposit_ltc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    deposit_addresses = load_json("deposit_addresses.json", {})
    if user_id not in deposit_addresses:
        deposit_addresses[user_id] = "LTC1234567890abcdef"
        save_json("deposit_addresses.json", deposit_addresses)
    address = deposit_addresses[user_id]
    keyboard = [
        [InlineKeyboardButton("Check Balance", callback_data=f"check_balance_{user_id}")],
        [InlineKeyboardButton("💸 Simulate Deposit (+100 coins)", callback_data="simulate_deposit")],
        [InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Litecoin Deposit Address:\n\n{address}\n\n"
        "Send your Litecoins to this address to increase your balance.\n"
        "Your balance will be updated automatically once the transaction is confirmed.\n"
        "Note: Please do not send any other cryptocurrencies to this address.",
        reply_markup=reply_markup
    )

async def simulate_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    balances = load_json("balances.json", {})
    balances[user_id] = balances.get(user_id, 0) + 100
    save_json("balances.json", balances)
    await query.message.reply_text("✅ 100 coins have been added to your balance for testing!")

async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    balances = load_json("balances.json", {})
    balance = balances.get(user_id, DEFAULT_START_COINS)
    await query.message.reply_text(f"💰 You have {balance} coins.")