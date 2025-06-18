from telegram import Update, ReplyKeyboardRemove, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from db import SessionLocal
from utils.db_utils import (
    get_all_products, add_product, remove_product, edit_product,
    add_product_photo, get_product_by_id, add_location_photo, get_location_photos_by_product
)

# States for ConversationHandler
ADD_NAME, ADD_PRICE, ADD_STOCK, ADD_CATEGORY, ADD_DESCRIPTION = range(5)
REMOVE_ID = 5
EDIT_ID, EDIT_FIELD, EDIT_VALUE = 6, 7, 8
PHOTO_PRODUCT_ID, PHOTO_RECEIVE = 9, 10
LOCATION_PRODUCT_ID, LOCATION_RECEIVE = 11, 12
SHOW_LOCATION_PHOTOS = 14

# --- Product List ---
async def product_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        products = await get_all_products(session)
    if not products:
        await update.message.reply_text("No products found.")
        return
    msg = ""
    for product in products:
        msg += (
            f"*ID: {product.id}*\n"
            f"*{product.name}*\n"
            f"💰 Price: {product.price} coins\n"
            f"📦 Stock: {product.stock}\n"
            f"🏷️ Category: {product.category or 'N/A'}\n"
            f"{product.description or 'No description available.'}\n\n"
        )
    await update.message.reply_text(msg, parse_mode="Markdown")

# --- Add Product ---
async def add_product_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter product name:")
    return ADD_NAME

async def add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_product_name"] = update.message.text
    await update.message.reply_text("Enter product price (number):")
    return ADD_PRICE

async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = update.message.text
    if not price.isdigit():
        await update.message.reply_text("Please enter a valid number for price.")
        return ADD_PRICE
    context.user_data["add_product_price"] = int(price)
    await update.message.reply_text("Enter product stock (number):")
    return ADD_STOCK

async def add_product_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stock = update.message.text
    if not stock.isdigit():
        await update.message.reply_text("Please enter a valid number for stock.")
        return ADD_STOCK
    context.user_data["add_product_stock"] = int(stock)
    await update.message.reply_text("Enter product category:")
    return ADD_CATEGORY

async def add_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_product_category"] = update.message.text
    await update.message.reply_text("Enter product description (or type '-' for none):")
    return ADD_DESCRIPTION

async def add_product_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    if description == "-":
        description = ""
    context.user_data["add_product_description"] = description

    async with SessionLocal() as session:
        await add_product(
            session=session,
            name=context.user_data["add_product_name"],
            price=context.user_data["add_product_price"],
            stock=context.user_data["add_product_stock"],
            category=context.user_data["add_product_category"],
            description=context.user_data["add_product_description"]
        )

    await update.message.reply_text("✅ Product added!", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Product addition cancelled.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

# --- Remove Product by ID ---
async def remove_product_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the ID of the product to remove:")
    return REMOVE_ID

async def remove_product_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = update.message.text.strip()
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await update.message.reply_text("Product not found.")
            return ConversationHandler.END
        await remove_product(session, product_id)
    await update.message.reply_text(f"✅ Product with ID {product_id} removed.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- Edit Product by ID ---
async def edit_product_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the ID of the product to edit:")
    return EDIT_ID

async def edit_product_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = update.message.text.strip()
    context.user_data["edit_product_id"] = product_id
    await update.message.reply_text(
        "Which field do you want to edit? (name, price, stock, category, description)"
    )
    return EDIT_FIELD

async def edit_product_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = update.message.text.lower()
    if field not in ["name", "price", "stock", "category", "description"]:
        await update.message.reply_text(
            "Invalid field. Choose from: name, price, stock, category, description."
        )
        return EDIT_FIELD
    context.user_data["edit_field"] = field
    await update.message.reply_text(f"Enter new value for {field}:")
    return EDIT_VALUE

async def edit_product_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text
    product_id = context.user_data["edit_product_id"]
    field = context.user_data["edit_field"]
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await update.message.reply_text("Product not found.")
            return ConversationHandler.END
        await edit_product(session, product_id, field, value)
    await update.message.reply_text(
        f"✅ Product with ID {product_id} updated.", reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

# --- Add Product Photo by ID ---
async def add_product_photo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the product ID to add a presentation photo to:")
    return PHOTO_PRODUCT_ID

async def receive_product_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = update.message.text.strip()
    context.user_data["photo_product_id"] = product_id
    await update.message.reply_text("Now send the presentation photo for this product:")
    return PHOTO_RECEIVE

async def save_product_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please send a photo.")
        return PHOTO_RECEIVE
    file_id = update.message.photo[-1].file_id
    product_id = context.user_data["photo_product_id"]
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await update.message.reply_text("Product not found.")
            return ConversationHandler.END
        product.image = file_id
        await session.commit()
    await update.message.reply_text("✅ Presentation photo added to product.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

# --- Add Location Photo (Bulk) by Product ID ---
async def add_location_photo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the product ID to add location photos to:")
    return LOCATION_PRODUCT_ID

async def receive_location_photo_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = update.message.text.strip()
    context.user_data["location_product_id"] = product_id
    await update.message.reply_text(
        "Now send location photos for this product (with optional captions). "
        "When you are done, type /done."
    )
    return LOCATION_RECEIVE

async def save_location_photo_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please send a photo or type /done to finish.")
        return LOCATION_RECEIVE
    file_id = update.message.photo[-1].file_id
    caption = update.message.caption or ""
    product_id = context.user_data["location_product_id"]
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await update.message.reply_text("Product not found.")
            return ConversationHandler.END
        await add_location_photo(session, product_id, file_id, caption)
    await update.message.reply_text("Location photo added. Send another or type /done to finish.")
    return LOCATION_RECEIVE

async def done_adding_location_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Done adding location photos.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

# --- Show Location Photos by Product ID ---
async def show_location_photos_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the product ID to show location photos for:")
    return SHOW_LOCATION_PHOTOS

async def send_location_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = update.message.text.strip()
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await update.message.reply_text("Product not found.")
            return ConversationHandler.END
        photos = await get_location_photos_by_product(session, product_id)
    if not photos:
        await update.message.reply_text("No location photos found for this product.")
        return ConversationHandler.END
    media = [InputMediaPhoto(photo.file_id, caption=photo.caption or None) for photo in photos]
    await update.message.reply_media_group(media)
    return ConversationHandler.END

# --- Low Stock Command ---
async def lowstock_cmd(update, context):
    LOW_STOCK_THRESHOLD = 5
    async with SessionLocal() as session:
        products = await get_all_products(session)
    low_stock = [p for p in products if p.stock < LOW_STOCK_THRESHOLD]
    if not low_stock:
        await update.message.reply_text("All products are sufficiently stocked.")
        return
    msg = "⚠️ Low Stock Products:\n"
    for p in low_stock:
        msg += f"- {p.name}: {p.stock} left\n"
    await update.message.reply_text(msg)