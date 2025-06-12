from config import main_menu, DEFAULT_START_COINS
from models import load_json, save_json
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from .balance import deposit_ltc
from .products import categories_cmd

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    balances = load_json("balances.json", {})
    if user_id not in balances:
        balances[user_id] = DEFAULT_START_COINS
        save_json("balances.json", balances)
    reply_markup = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    await update.message.reply_text(
        f"Welcome to the Shop Bot! 🛒\n\nChoose an option:\n"
        f"You have {balances[user_id]} coins.",
        reply_markup=reply_markup
    )
    first_joins = load_json("first_join.json", {})
    if user_id not in first_joins:
        from datetime import datetime
        first_joins[user_id] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        save_json("first_join.json", first_joins)

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.message.from_user.id)
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
        balances = load_json("balances.json", {})
        balance = balances.get(user_id, DEFAULT_START_COINS)
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
    balances = load_json("balances.json", {})
    orders = load_json("orders.json", {})
    joins = load_json("first_join.json", {})
    balance = balances.get(user_id, DEFAULT_START_COINS)
    order_count = len(orders.get(user_id, []))
    join_date = joins.get(user_id, "Unknown")
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