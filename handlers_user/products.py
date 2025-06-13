from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db import SessionLocal
from db_utils import get_all_products, get_products_by_category, get_product_by_name, search_products

async def categories_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Support both /start (message) and callback (query)
    if hasattr(update, "message") and update.message:
        target = update.message
    else:
        target = update.callback_query.message

    async with SessionLocal() as session:
        products = await get_all_products(session)
    categories = sorted(set(p.category or "Other" for p in products))
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat_{cat}")] for cat in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await target.reply_text("Select a category:", reply_markup=reply_markup)
    
async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.replace("cat_", "")
    async with SessionLocal() as session:
        products = await get_products_by_category(session, cat)
    if not products:
        await query.message.reply_text(f"No products found in category {cat}.")
        return
    for product in products:
        keyboard = [
            [InlineKeyboardButton(f"Order {product.name}", callback_data=f"order_{product.name}")],
            [InlineKeyboardButton("ℹ️ Details", callback_data=f"details_{product.name}")],
            [InlineKeyboardButton("🔙 Back to Categories", callback_data="back_to_categories")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
        ]
        caption = (
            f"*{product.name}*\n"
            f"Price: {product.price} coins\n"
            f"Stock: {product.stock}\n"
            f"Category: {product.category or 'N/A'}"
        )
        try:
            await query.message.reply_photo(
                photo=product.image,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            await query.message.reply_text(
                f"Could not display product {product.name}: {e}"
            )

async def product_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_name = query.data.replace("details_", "")
    async with SessionLocal() as session:
        product = await get_product_by_name(session, product_name)
    if not product:
        await query.message.reply_text("Product not found.")
        return
    caption = (
        f"*{product.name}*\n"
        f"Price: {product.price} coins\n"
        f"Stock: {product.stock}\n"
        f"Category: {product.category or 'N/A'}\n\n"
        f"{product.description or ''}"
    )
    keyboard = [
        [InlineKeyboardButton(f"Order {product.name}", callback_data=f"order_{product.name}")],
        [InlineKeyboardButton("🔙 Back to Categories", callback_data="back_to_categories")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
    ]
    try:
        await query.message.reply_photo(
            photo=product.image,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await query.message.reply_text(
            f"Could not display product {product.name}: {e}"
        )

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    async with SessionLocal() as session:
        products = await search_products(session, text)
    if not products:
        await update.message.reply_text("No products found matching your search.")
        return
    for product in products:
        keyboard = [
            [InlineKeyboardButton(f"Order {product.name}", callback_data=f"order_{product.name}")],
            [InlineKeyboardButton("ℹ️ Details", callback_data=f"details_{product.name}")]
        ]
        caption = (
            f"*{product.name}*\n"
            f"Price: {product.price} coins\n"
            f"Stock: {product.stock}\n"
            f"Category: {product.category or 'N/A'}"
        )
        try:
            await update.message.reply_photo(
                photo=product.image,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            await update.message.reply_text(
                f"Could not display product {product.name}: {e}"
            )