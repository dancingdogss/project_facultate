from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal, User
from utils.db_utils import get_user, create_user_if_not_exists
from sqlalchemy import text
from handlers_admin.auth import require_admin_auth, log_admin_action
from config import DEFAULT_START_COINS
from datetime import datetime
import csv
import io

# --- Profits Command ---
@require_admin_auth
async def profits_cmd(update, context):
    async with SessionLocal() as session:
        result = await session.execute(
            text("SELECT SUM(o.quantity * p.price) FROM orders o JOIN products p ON o.product_id = p.id WHERE o.status = 'completed'")
        )
        total = result.scalar()
    await update.message.reply_text(f"💰 Total profits from completed orders: {total or 0} coins")
    log_admin_action(update.effective_user.id, update.message.text)

# --- Export Profits Command ---
@require_admin_auth
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
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Order ID", "User ID", "Product", "Quantity", "Unit Price", "Status", "Created At", "Profit"])
    for r in rows:
        profit = r.quantity * r.price
        writer.writerow([r.id, r.user_id, r.product_name, r.quantity, r.price, r.status, r.created_at, profit])
    output.seek(0)
    await update.message.reply_document(document=io.BytesIO(output.getvalue().encode()), filename="profits.csv")
    log_admin_action(update.effective_user.id, update.message.text)

# --- Add Coins Command ---
@require_admin_auth
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
            # Auto-create user if not found
            await create_user_if_not_exists(session, user_id, datetime.utcnow(), DEFAULT_START_COINS)
            user = await get_user(session, user_id)
        user.balance += amount
        await session.commit()
        await update.message.reply_text(f"Added {amount} coins to user {user_id}. New balance: {user.balance}")
    log_admin_action(update.effective_user.id, update.message.text)

# --- Set Coins Command ---
@require_admin_auth
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
            # Auto-create user if not found
            await create_user_if_not_exists(session, user_id, datetime.utcnow(), DEFAULT_START_COINS)
            user = await get_user(session, user_id)
        user.balance = amount
        await session.commit()
        await update.message.reply_text(f"Set user {user_id} balance to {amount}.")
    log_admin_action(update.effective_user.id, update.message.text)

# --- All Users Command ---
@require_admin_auth
async def users_cmd(update, context):
    async with SessionLocal() as session:
        result = await session.execute(User.__table__.select())
        users = result.fetchall()
    if not users:
        await update.message.reply_text("No users found.")
        return
    msg = "👥 All Users:\n"
    for u in users:
        join_date = u.join_date.strftime('%Y-%m-%d %H:%M:%S') if hasattr(u, 'join_date') and u.join_date else 'N/A'
        msg += f"- ID: {u.id} | Joined: {join_date} | Balance: {u.balance}\n"
    await update.message.reply_text(msg)
    log_admin_action(update.effective_user.id, update.message.text)

# --- Top Users Command ---
@require_admin_auth
async def topusers_cmd(update, context):
    async with SessionLocal() as session:
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
    log_admin_action(update.effective_user.id, update.message.text)

# --- Dashboard Command ---
@require_admin_auth
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
    log_admin_action(update.effective_user.id, update.message.text)