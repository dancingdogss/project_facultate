from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from utils.db_utils import search_products

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /search <keyword>")
        return

    keyword = " ".join(context.args)
    async with SessionLocal() as session:
        products = await search_products(session, keyword)

    if not products:
        await update.message.reply_text(f"No products found for '{keyword}'.")
        return

    for product in products:
        msg = (
            f"*{product.name}*\n"
            f"💰 Price: {product.price} coins\n"
            f"📦 Stock: {product.stock}\n"
            f"🏷️ Category: {product.category or 'N/A'}\n\n"
            f"{product.description or 'No description available.'}"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")