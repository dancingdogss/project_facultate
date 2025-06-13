from config import DEFAULT_START_COINS
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from .balance import deposit_ltc
from .products import categories_cmd, CATEGORY_EMOJIS, get_categories_keyboard
from .orders import myorders_cmd
from utils.db_utils import get_user, create_user_if_not_exists, get_user_orders_count, get_all_products
from datetime import datetime
from db import SessionLocal
from config import ADMIN_CHAT_ID
import os

WELCOME_PHOTO_PATH = os.path.join("products_pics", "winners_shop.png")

def get_main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [["🛒 Browse Products", "🔍 Search"],
         ["📦 My Orders", "👤 Profile"],
         ["💰 Balance", "💸 Deposit LTC"],
         ["ℹ️ Help"]
         
         ],
    
         resize_keyboard=True
    )

async def start(update, context):
    user_id = str(update.message.from_user.id)
    async with SessionLocal() as session:
        user = await get_user(session, user_id)
        if not user:
            await create_user_if_not_exists(session, user_id, datetime.utcnow(), DEFAULT_START_COINS)
            balance = DEFAULT_START_COINS
        else:
            balance = user.balance
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"👤 New user joined!\nName: {user.full_name}\nUsername: @{user.username or 'N/A'}\nID: {user_id}"
                )

            except Exception as e:
                print(f"Error sending message to admin: {e}")
    if os.path.exists(WELCOME_PHOTO_PATH):
        with open(WELCOME_PHOTO_PATH, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption="👋 *Welcome to the Winners Shop!*",
                parse_mode="Markdown"
            )

    await update.message.reply_text(
        f"Choose an option below:\n"
        f"💰 *Your balance:* `{balance}` coins",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.message.from_user.id)
    async with SessionLocal() as session:
        user = await get_user(session, user_id)
        balance = user.balance if user else DEFAULT_START_COINS
        products = await get_all_products(session)
    categories = sorted(set(p.category or "Other" for p in products))
    category_buttons = [f"{CATEGORY_EMOJIS.get(cat, '📦')} {cat}" for cat in categories]

    if text == "🛒 Browse Products":
        await update.message.reply_text(
            "📂 *Choose a category:*",
            reply_markup=get_categories_keyboard(categories),
            parse_mode="Markdown"
        )
    elif text == "🔍 Search":
        await update.message.reply_text("Type `/search <keyword>` to search for products.", parse_mode="Markdown")
    elif text == "📦 My Orders":
        await myorders_cmd(update, context)
    elif text == "👤 Profile":
        await profile_cmd(update, context)
    elif text == "💰 Balance":
        await update.message.reply_text(f"💰 You have `{balance}` coins.", parse_mode="Markdown")
    elif text == "💸 Deposit LTC":
        await deposit_ltc(update, context)
    elif text == "ℹ️ Help":
        await update.message.reply_text(
            "ℹ️ *Help*\n\n"
            "• 🛒 *Browse Products*: View all available products.\n"
            "• 🔍 *Search*: Find products by name or description.\n"
            "• 📦 *My Orders*: View your order history.\n"
            "• 👤 *Profile*: View your profile and stats.\n"
            "• 💰 *Balance*: Check your coin balance.\n"
            "• 💸 *Deposit LTC*: Get a Litecoin deposit address.\n"
            "Use the menu buttons or type commands directly.",
            parse_mode="Markdown"
        )
    elif text in category_buttons:
        for cat in categories:
            if text == f"{CATEGORY_EMOJIS.get(cat, '📦')} {cat}":
                await categories_cmd(update, context, force_category=cat)
                return
    elif text == "🔙 Back to Menu":
        await update.message.reply_text("Main Menu:", reply_markup=get_main_menu_keyboard())
    else:
        await update.message.reply_text("Please choose an option from the menu below.", reply_markup=get_main_menu_keyboard())

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
        f"Balance: `{balance}` coins\n"
        f"Orders: `{order_count}`\n"
        f"Joined: {join_date}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_back_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "back_to_categories":
        await categories_cmd(update, context)
        return ConversationHandler.END
    elif query.data == "back_to_menu":
        await query.message.reply_text("Main Menu:", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END