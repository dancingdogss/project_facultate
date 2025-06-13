from db import SessionLocal
from telegram import Update
from telegram.ext import ContextTypes
from utils.db_utils import get_profits, set_user_balance, get_all_users
from utils.db_utils import set_user_balance



async def users_cmd(update, context):
    async with SessionLocal() as session:
        users = await get_all_users(session)
    if not users:
        await update.message.reply_text("No users found.")
        return
    msg = ""
    for user in users:
        msg += f"👤 {user.id} | Joined: {user.join_date} | Balance: {user.balance}\n"
    await update.message.reply_text(msg)

async def profits_cmd(update, context):
    async with SessionLocal() as session:
        profits = await get_profits(session)
    if not profits:
        await update.message.reply_text("No profits recorded.")
        return
    msg = ""
    for p in profits:
        msg += (
            f"💸 Profit ID: {p.id}\n"
            f"User: {p.user_id}\n"
            f"Product: {p.product}\n"
            f"Quantity: {p.quantity}\n"
            f"Amount: {p.amount}\n"
            f"Date: {p.datetime}\n\n"
        )
    await update.message.reply_text(msg)

async def export_profits(update, context):
    await update.message.reply_text("Export profits (stub)")

async def addcoins_cmd(update, context):
    await update.message.reply_text("Add coins (stub)")


async def setcoins_cmd(update, context):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /setcoins <user_id> <amount>")
        return
    user_id, amount = args[0], args[1]
    try:
        amount = int(amount)
    except ValueError:
        await update.message.reply_text("Amount must be a number.")
        return
    async with SessionLocal() as session:
        user = await set_user_balance(session, user_id, amount)
    if user:
        await update.message.reply_text(f"✅ Set balance for user `{user_id}` to `{amount}` coins.", parse_mode="Markdown")
    else:
        await update.message.reply_text("User not found.")

async def topusers_cmd(update, context):
    await update.message.reply_text("Top users (stub)")

async def dashboard_cmd(update, context):
    await update.message.reply_text("Dashboard (stub)")

async def user_stats_cmd(update, context):
    await update.message.reply_text("User stats feature not implemented yet.")

async def search_user_cmd(update, context):
    await update.message.reply_text("Search user feature not implemented yet.")

async def order_stats_cmd(update, context):
    await update.message.reply_text("Order stats feature not implemented yet.")