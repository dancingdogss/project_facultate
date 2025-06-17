from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from utils.db_utils import get_user
from sqlalchemy import text


# This command calculates total profits from completed orders and sends it to the chat
async def profits_cmd(update, context):
    async with SessionLocal() as session:
        result = await session.execute(
            text("SELECT SUM(o.quantity * p.price) FROM orders o JOIN products p ON o.product_id = p.id WHERE o.status = 'completed'")
        )
        total = result.scalar()
    await update.message.reply_text(f"💰 Total profits from completed orders: {total or 0} coins")



# This command exports profits from completed orders to a CSV file and sends it to the chat 

async def export_profits(update, context):
    async with SessionLocal() as session:
        result = await session.execute(
            text(
                "SELECT o.id, o.user_id, o.product_name, o.quantity, p.price, o.status, o.created_at "
                "FROM orders o JOIN products p ON o.product_id = p.id WHERE o.status = 'completed'"
            )
        )
        rows = result.fetchall()
    if not rows:
        await update.message.reply_text("No profits to export.")
        return
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Order ID", "User ID", "Product", "Quantity", "Unit Price", "Status", "Created At", "Profit"])
    for r in rows:
        profit = r.quantity * r.price
        writer.writerow([r.id, r.user_id, r.product_name, r.quantity, r.price, r.status, r.created_at, profit])
    output.seek(0)
    await update.message.reply_document(document=io.BytesIO(output.getvalue().encode()), filename="profits.csv")

    #
# This command adds coins to a user's balance. It expects a user ID and an amount.

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


# This command sets a user's balance to a specific amount. It expects a user ID and an amount.


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

# This command retrieves the top 10 users by balance and sends them to the chat

async def topusers_cmd(update, context):
    async with SessionLocal() as session:
        from db import User
        result = await session.execute(
            User.__table__.select().order_by(User.balance.desc()).limit(10)
        )
        users = result.fetchall()
    if not users:
        await update.message.reply_text("No users found.")
        return
    msg = "🏆 Top Users by Balance:\n"
    for i, u in enumerate(users, 1):
        msg += f"{i}. User ID: {u.id} | Balance: {u.balance}\n"
    await update.message.reply_text(msg)


# This command provides a dashboard with top products and low stock items


async def dashboard_cmd(update, context):
    async with SessionLocal() as session:
        # Top products by sales
        result = await session.execute(
            text("SELECT product_name, SUM(quantity) as total_sold FROM orders GROUP BY product_name ORDER BY total_sold DESC LIMIT 5")
        )
        top_products = result.fetchall()
        # Low stock products
        from db import Product
        result2 = await session.execute(
            Product.__table__.select().where(Product.stock < 5)
        )
        low_stock = result2.fetchall()
    msg = "📊 Dashboard\n\n"
    msg += "🔥 Top Products:\n"
    for p in top_products:
        msg += f"- {p[0]}: {p[1]} sold\n"
    msg += "\n⚠️ Low Stock:\n"
    for p in low_stock:
        msg += f"- {p.name}: {p.stock} left\n"
    await update.message.reply_text(msg)