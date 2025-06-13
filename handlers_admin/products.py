from telegram import Update, InputFile
from telegram.ext import ContextTypes, ConversationHandler
from db import SessionLocal
from db_utils import add_product, remove_product, edit_product, get_all_products, get_product

ADD_LOCATION_WAIT_PRODUCT, ADD_LOCATION_WAIT_PHOTO = range(2)

# --- Product Management ---

async def add_product_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("Usage: /addproduct <name> <price> <stock> <category>")
        return
    name, price, stock, category = args[0], args[1], args[2], args[3]
    async with SessionLocal() as session:
        product = await add_product(session, name, price, stock, category)
    await update.message.reply_text(f"✅ Product '{name}' added.")

async def remove_product_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /removeproduct <product_id>")
        return
    product_id = args[0]
    async with SessionLocal() as session:
        success = await remove_product(session, product_id)
    if success:
        await update.message.reply_text(f"Product {product_id} removed.")
    else:
        await update.message.reply_text("Product not found.")

async def edit_product_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Usage: /editproduct <product_id> <field> <new_value>")
        return
    product_id, field, new_value = args[0], args[1], args[2]
    async with SessionLocal() as session:
        success = await edit_product(session, product_id, field, new_value)
    if success:
        await update.message.reply_text(f"Product {product_id} updated: {field} = {new_value}")
    else:
        await update.message.reply_text("Product not found or invalid field.")

async def product_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        products = await get_all_products(session)
    if not products:
        await update.message.reply_text("No products found.")
        return
    msg = "🛒 *Product List:*\n"
    for p in products:
        msg += (
            f"- ID: `{p.id}` | {p.name} | "
            f"Price: {p.price} | Stock: {p.stock} | "
            f"Category: {p.category}\n"
        )
    await update.message.reply_text(msg, parse_mode="Markdown")

# --- Stock Location Management ---

async def add_location_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send the *product ID* for which you want to set the pickup location.", parse_mode="Markdown")
    return ADD_LOCATION_WAIT_PRODUCT

async def add_location_set_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_location_product_id"] = update.message.text.strip()
    await update.message.reply_text("Now send the *location photo* with a caption (pickup info).", parse_mode="Markdown")
    return ADD_LOCATION_WAIT_PHOTO

async def add_location_receive_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_location_product_id"] = update.message.text.strip()
    await update.message.reply_text("Now send the *location photo* with a caption (pickup info).", parse_mode="Markdown")
    return ADD_LOCATION_WAIT_PHOTO

async def add_location_receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = context.user_data.get("add_location_product_id")
    if not product_id:
        await update.message.reply_text("No product ID found. Please start again.")
        return ConversationHandler.END
    async with SessionLocal() as session:
        product = await get_product(session, product_id)
        if not product:
            await update.message.reply_text("Product not found. Please try again.")
            return ConversationHandler.END
        photo = update.message.photo[-1]
        product.image = photo.file_id
        product.description = update.message.caption
        await session.commit()
        await update.message.reply_text(f"Location photo and caption set for *{product.name}*.", parse_mode="Markdown")
    return ConversationHandler.END