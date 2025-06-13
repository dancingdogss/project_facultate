from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from utils.db_utils import get_all_products, get_products_by_category, get_product_by_name

CATEGORY_EMOJIS = {
    "Cox": "❄️",
    "Klein": "🔑",
    "Shrooms": "🍄",
    "Spliff": "🚬",
    # Add more as needed
}

def get_categories_keyboard(categories):
    keyboard = [
        [f"{CATEGORY_EMOJIS.get(cat, '📦')} {cat}"] for cat in categories
    ]
    keyboard.append(["🔙 Back to Menu"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def categories_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, force_category=None):
    if force_category:
        await show_category_products(update, context, force_category)
        return

    async with SessionLocal() as session:
        products = await get_all_products(session)
    categories = sorted(set(p.category or "Other" for p in products))
    await update.message.reply_text(
        "📂 *Choose a category:*",
        reply_markup=get_categories_keyboard(categories),
        parse_mode="Markdown"
    )

async def show_category_products(update: Update, context: ContextTypes.DEFAULT_TYPE, category_name: str):
    async with SessionLocal() as session:
        products = await get_products_by_category(session, category_name)

    if not products:
        await update.message.reply_text(f"No products found in category {category_name}.")
        return

    for product in products:
        keyboard = [
            [InlineKeyboardButton(f"🛒 Order {product.name}", callback_data=f"order_{product.name}")],
            [InlineKeyboardButton("ℹ️ Details", callback_data=f"details_{product.name}")],
            [InlineKeyboardButton("🔙 Back to Categories", callback_data="back_to_categories")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
        ]

        caption = (
            f"*{product.name}*\n"
            f"💰 Price: {product.price} coins\n"
            f"📦 Stock: {product.stock}\n"
            f"🏷️ Category: {product.category or 'N/A'}\n\n"
            f"{product.description or 'No description available.'}"
        )

        reply_markup = InlineKeyboardMarkup(keyboard)

        if product.image:
            try:
                await update.message.reply_photo(
                    photo=product.image,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            except Exception:
                await update.message.reply_text(
                    f"📷 Photo not available\n\n{caption}",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(
                f"📷 No photo available\n\n{caption}",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

async def product_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_name = query.data.replace("details_", "")
    async with SessionLocal() as session:
        product = await get_product_by_name(session, product_name)
    if product:
        msg = (
            f"*{product.name}*\n"
            f"💰 Price: {product.price} coins\n"
            f"📦 Stock: {product.stock}\n"
            f"🏷️ Category: {product.category or 'N/A'}\n\n"
            f"{product.description or 'No description available.'}"
        )
        await query.message.reply_text(msg, parse_mode="Markdown")
    else:
        await query.message.reply_text("Product not found.")

async def back_to_categories_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    async with SessionLocal() as session:
        products = await get_all_products(session)
    categories = sorted(set(p.category or "Other" for p in products))
    await query.message.reply_text(
        "📂 *Choose a category:*",
        reply_markup=get_categories_keyboard(categories),
        parse_mode="Markdown"
    )

async def back_to_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from .menu import get_main_menu_keyboard
    await query.message.reply_text("Main Menu:", reply_markup=get_main_menu_keyboard())