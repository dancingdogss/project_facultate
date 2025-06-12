from telegram import Update, InputFile
from telegram.ext import ContextTypes
from models import load_json, save_json

async def profits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profits = load_json("profits.json", [])
    if not profits:
        await update.message.reply_text("No profits recorded yet.")
        return
    msg = "💸 *Profits:*\n"
    total = 0
    for p in profits[-30:]:
        msg += (
            f"- User: `{p.get('user_id', '')}` | Product: {p.get('product', '')} | "
            f"Qty: {p.get('quantity', '')} | Amount: {p.get('amount', 0)} | "
            f"Date: {p.get('datetime', '')}\n"
        )
        total += int(p.get('amount', 0))
    msg += f"\n*Total (last 30):* {total} coins"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def export_profits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import csv
    from io import StringIO
    profits = load_json("profits.json", [])
    csvfile = StringIO()
    writer = csv.writer(csvfile)
    writer.writerow(['User ID', 'Product', 'Quantity', 'Amount', 'Stock ID', 'Datetime'])
    for p in profits:
        writer.writerow([
            p.get('user_id', ''),
            p.get('product', ''),
            p.get('quantity', ''),
            p.get('amount', ''),
            p.get('stock_id', ''),
            p.get('datetime', '')
        ])
    csvfile.seek(0)
    await update.message.reply_document(
        document=csvfile.getvalue().encode(),
        filename="profits_export.csv",
        caption="🗂️ Profits exported as CSV."
    )

async def dashboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_json("balances.json", {})
    orders = load_json("orders.json", {})
    profits = load_json("profits.json", [])
    msg = (
        f"📊 *Dashboard*\n"
        f"Total Users: {len(users)}\n"
        f"Total Orders: {sum(len(v) for v in orders.values())}\n"
        f"Total Profits: {sum(int(p.get('amount', 0)) for p in profits)} coins"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def topusers_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balances = load_json("balances.json", {})
    if not balances:
        await update.message.reply_text("No users found.")
        return
    sorted_users = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]
    msg = "🏆 *Top Users by Balance:*\n"
    for uid, bal in sorted_users:
        msg += f"- `{uid}`: {bal} coins\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def addcoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /addcoins <user_id> <amount>")
        return
    user_id, amount = args[0], int(args[1])
    balances = load_json("balances.json", {})
    balances[user_id] = balances.get(user_id, 0) + amount
    save_json("balances.json", balances)
    await update.message.reply_text(f"Added {amount} coins to user {user_id}.")

async def setcoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /setcoins <user_id> <amount>")
        return
    user_id, amount = args[0], int(args[1])
    balances = load_json("balances.json", {})
    balances[user_id] = amount
    save_json("balances.json", balances)
    await update.message.reply_text(f"Set user {user_id}'s balance to {amount} coins.")