from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from utils.db_utils import get_user

async def profits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Replace this with your real profit calculation logic
    await update.message.reply_text("Profits (stub)")

async def export_profits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Export profits (stub)")

async def addcoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args) != 3:
        await update.message.reply_text("Usage: /addcoins <user_id> <amount>")
        return
    user_id, amount = args[1], args[2]
    if not amount.isdigit():
        await update.message.reply_text("Amount must be a number.")
        return
    amount = int(amount)
    async with SessionLocal() as session:
        user = await get_user(session, user_id)
        if not user:
            await update.message.reply_text("User not found.")
            return
        user.balance += amount
        await session.commit()
        await update.message.reply_text(f"Added {amount} coins to user {user_id}. New balance: {user.balance}")

async def setcoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args) != 3:
        await update.message.reply_text("Usage: /setcoins <user_id> <amount>")
        return
    user_id, amount = args[1], args[2]
    if not amount.isdigit():
        await update.message.reply_text("Amount must be a number.")
        return
    amount = int(amount)
    async with SessionLocal() as session:
        user = await get_user(session, user_id)
        if not user:
            await update.message.reply_text("User not found.")
            return
        user.balance = amount
        await session.commit()
        await update.message.reply_text(f"Set user {user_id} balance to {amount}.")
async def topusers_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Top users (stub)")

async def dashboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Dashboard (stub)")