from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal, User
from utils.db_utils import get_all_users, get_all_orders
from sqlalchemy.future import select

async def search_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for users by ID"""
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /searchuser <user_id>")
        return
    
    search_term = args[0]
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.id.like(f"%{search_term}%")))
        users = result.scalars().all()
    
    if not users:
        await update.message.reply_text("No users found.")
        return
    
    msg = "👤 *Users Found:*\n\n"
    for user in users:
        msg += f"ID: `{user.id}`\n"
        msg += f"Balance: {user.balance} coins\n"
        msg += f"Joined: {user.join_date}\n\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    async with SessionLocal() as session:
        users = await get_all_users(session)
        orders = await get_all_orders(session)
    
    # Group orders by user
    user_orders = {}
    for order in orders:
        user_orders[order.user_id] = user_orders.get(order.user_id, 0) + 1
    
    total_users = len(users)
    if total_users == 0:
        await update.message.reply_text("No users in the database.")
        return
        
    active_users = len([u for u in users if user_orders.get(u.id, 0) > 0])
    avg_balance = sum(u.balance for u in users) / total_users if total_users > 0 else 0
    
    msg = "📊 *User Statistics*\n\n"
    msg += f"Total Users: {total_users}\n"
    msg += f"Active Users: {active_users}\n"
    msg += f"Average Balance: {avg_balance:.2f} coins\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")