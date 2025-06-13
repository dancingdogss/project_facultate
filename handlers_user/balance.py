from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import DEFAULT_START_COINS
from db import SessionLocal
from db_utils import get_user, set_user_balance

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    async with SessionLocal() as session:
        user = await get_user(session, user_id)
        balance = user.balance if user else DEFAULT_START_COINS
    await update.message.reply_text(f"💰 You have {balance} coins.")

async def deposit_ltc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    # For demonstration, we'll keep deposit addresses in memory or you can migrate this to DB as well
    address = "LTC1234567890abcdef"
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
    async with SessionLocal() as session:
        user = await get_user(session, user_id)
        new_balance = (user.balance if user else 0) + 100
        await set_user_balance(session, user_id, new_balance)
    await query.message.reply_text("✅ 100 coins have been added to your balance for testing!")

async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    async with SessionLocal() as session:
        user = await get_user(session, user_id)
        balance = user.balance if user else DEFAULT_START_COINS
    await query.message.reply_text(f"💰 You have {balance} coins.")