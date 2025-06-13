from telegram import Update, InputFile
from telegram.ext import ContextTypes
from db import SessionLocal
from db_utils import (
    get_profits, get_all_profits, get_all_users, get_top_users,
    get_all_orders, set_user_balance, add_user_balance
)

async def profits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        profits = await get_profits(session, limit=30)
    if not profits:
        await update.message.reply_text("No profits recorded yet.")
        return
    msg = "💸 *Profits:*\n"
    total = 0
    for p in profits:
        msg += (
            f"- User: `{p.user_id}` | Product: {p.product} | "
            f"Qty: {p.quantity} | Amount: {p.amount} | "
            f"Date: {p.datetime}\n"
        )
        total += int(p.amount)
    msg += f"\n*Total (last 30):* {total} coins"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def export_profits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import csv
    from io import StringIO
    async with SessionLocal() as session:
        profits = await get_all_profits(session)
    csvfile = StringIO()
    writer = csv.writer(csvfile)
    writer.writerow(['User ID', 'Product', 'Quantity', 'Amount', 'Stock ID', 'Datetime'])
    for p in profits:
        writer.writerow([
            p.user_id,
            p.product,
            p.quantity,
            p.amount,
            p.stock_id,
            p.datetime
        ])
    csvfile.seek(0)
    await update.message.reply_document(
        document=csvfile.getvalue().encode(),
        filename="profits_export.csv",
        caption="🗂️ Profits exported as CSV."
    )

async def dashboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        users = await get_all_users(session)
        orders = await get_all_orders(session)
        profits = await get_all_profits(session)
    msg = (
        f"📊 *Dashboard*\n"
        f"Total Users: {len(users)}\n"
        f"Total Orders: {len(orders)}\n"
        f"Total Profits: {sum(int(p.amount) for p in profits)} coins"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def topusers_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        users = await get_top_users(session, limit=10)
    if not users:
        await update.message.reply_text("No users found.")
        return
    msg = "🏆 *Top Users by Balance:*\n"
    for user in users:
        msg += f"- `{user.id}`: {user.balance} coins\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def addcoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /addcoins <user_id> <amount>")
        return
    user_id, amount = args[0], int(args[1])
    async with SessionLocal() as session:
        await add_user_balance(session, user_id, amount)
    await update.message.reply_text(f"Added {amount} coins to user {user_id}.")

async def setcoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /setcoins <user_id> <amount>")
        return
    user_id, amount = args[0], int(args[1])
    async with SessionLocal() as session:
        await set_user_balance(session, user_id, amount)
    await update.message.reply_text(f"Set user {user_id}'s balance to {amount} coins.")