from config import main_menu, DEFAULT_START_COINS
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from .balance import deposit_ltc
from .products import categories_cmd
from db import SessionLocal
from db_utils import get_user, create_user_if_not_exists, get_user_orders_count
from datetime import datetime

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    async with SessionLocal() as session:
        user = await get_user(session, user_id)
        if not user:
            await create_user_if_not_exists(session, user_id, datetime.utcnow(), DEFAULT_START_COINS)
            balance = DEFAULT_START_COINS
            join_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        else:
            balance = user.balance
            join_date = user.join_date.strftime("%Y-%m-%d %H:%M:%S") if user.join_date else "Unknown"
    reply_markup = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    await update.message.reply_text(
        f"Welcome to the Shop Bot! 🛒\n\nChoose an option:\n"
        f"You have {balance} coins.",
        reply_markup=reply_markup
    )

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.message.from_user.id)
    async with SessionLocal() as session:
        user = await get_user(session, user_id)
        balance = user.balance if user else DEFAULT_START_COINS
    if text == "🛒 View Products":
        await categories_cmd(update, context)
        return
    elif text == "📦 My Orders":
        keyboard = [
            [
                InlineKeyboardButton("Pending", callback_data="filter_orders_pending"),
                InlineKeyboardButton("Completed", callback_data="filter_orders_completed"),
                InlineKeyboardButton("Cancelled", callback_data="filter_orders_cancelled")
            ],
            [InlineKeyboardButton("All", callback_data="filter_orders_all")]
        ]
        await update.message.reply_text("Filter your orders:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif text == "💰 My Balance":
        await update.message.reply_text(f"💰 You have {balance} coins.")
    elif text == "ℹ️ Help":
        await update.message.reply_text(
            "Welcome to the Shop Bot! Use the menu to view products, check your orders, balance, or get help."
        )
    elif text == "👤 Profile":
        await profile_cmd(update, context)
    elif text == "💳 Deposit LTC":
        await deposit_ltc(update, context)

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    async with SessionLocal() as session:
        db_user = await get_user(session, user_id)
        balance = db_user.balance if db_user else DEFAULT_START_COINS
        order_count = await get_user_orders_count(session, user_id)
        join_date = db_user.join_date.strftime("%Y-%m-%d %H:%M:%S") if db_user and db_user.join_date else "Unknown"
    msg = (
        f"👤 *Your Profile*\n"
        f"Name: {user.full_name}\n"
        f"Username: @{user.username or 'N/A'}\n"
        f"User ID: `{user.id}`\n"
        f"Balance: {balance} coins\n"
        f"Orders: {order_count}\n"
        f"Joined: {join_date}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_back_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "back_to_categories":
        from .products import categories_cmd
        await categories_cmd(update, context)
        return ConversationHandler.END
    elif query.data == "back_to_menu":
        from config import main_menu
        from telegram import ReplyKeyboardMarkup
        reply_markup = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
        await query.message.reply_text("Main Menu:", reply_markup=reply_markup)
        return ConversationHandler.END