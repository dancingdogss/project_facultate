from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from utils.db_utils import get_user
from config import DEFAULT_START_COINS

async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    async with SessionLocal() as session:
        user = await get_user(session, user_id)
        balance = user.balance if user else DEFAULT_START_COINS
    await update.message.reply_text(f"💰 Your balance: `{balance}` coins", parse_mode="Markdown")

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_balance(update, context)

async def deposit_ltc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Replace this with your real deposit address logic
    await update.message.reply_text("Send LTC to this address: `YOUR_LTC_ADDRESS`", parse_mode="Markdown")