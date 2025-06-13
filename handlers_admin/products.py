from telegram import Update, ReplyKeyboardRemove, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from db import SessionLocal
from utils.db_utils import (
    get_all_products, add_product, remove_product, edit_product, get_products_by_category,
    add_product_photo, get_product_by_name, add_location_photo, get_location_photos_by_product
)

# States for ConversationHandler
ADD_NAME, ADD_PRICE, ADD_STOCK, ADD_CATEGORY, ADD_DESCRIPTION = range(5)
REMOVE_NAME = 5
EDIT_NAME, EDIT_FIELD, EDIT_VALUE = 6, 7, 8
PHOTO_PRODUCT_NAME, PHOTO_RECEIVE, PHOTO_SAVE = 9, 10, 15
LOCATION_PRODUCT_NAME, LOCATION_RECEIVE, LOCATION_DONE = 11, 12, 13
SHOW_LOCATION_PHOTOS, SHOW_LOCATION_SEND = 14, 16

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
            f"*ID:* {product.id}\n"
            f"*Name:* {product.name}\n"
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

# --- Remove Product ---

async def remove_product_by_id_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /removeproductid <product_id>")
        return
    product_id = context.args[0]
    async with SessionLocal() as session:
        result = await remove_product(session, product_id)
    if result:
        await update.message.reply_text(f"✅ Product with ID `{product_id}` removed.")
    else:
        await update.message.reply_text("Product not found.")

async def remove_product_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the name of the product to remove:")
    return REMOVE_NAME

async def remove_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    async with SessionLocal() as session:
        product = await get_product_by_name(session, name)
        if not product:
            await update.message.reply_text("Product not found.")
            return ConversationHandler.END
        await remove_product(session, product.id)
    await update.message.reply_text(f"✅ Product '{name}' removed.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- Remove Products by Category ---
async def remove_category_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /removecategory <category>")
        return
    category = " ".join(context.args)
    async with SessionLocal() as session:
        products = await get_products_by_category(session, category)
        if not products:
            await update.message.reply_text("No products found in this category.")
            return
        for product in products:
            await remove_product(session, product.id)
    await update.message.reply_text(f"✅ All products in category '{category}' removed.")
# --- Edit Product ---
async def edit_product_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the name of the product to edit:")
    return EDIT_NAME

async def edit_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    context.user_data["edit_product_name"] = name
    await update.message.reply_text("Which field do you want to edit? (name, price, stock, category, description)")
    return EDIT_FIELD

async def edit_product_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = update.message.text.lower()
    if field not in ["name", "price", "stock", "category", "description"]:
        await update.message.reply_text("Invalid field. Choose from: name, price, stock, category, description.")
        return EDIT_FIELD
    context.user_data["edit_field"] = field
    await update.message.reply_text(f"Enter new value for {field}:")
    return EDIT_VALUE

async def edit_product_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text
    name = context.user_data["edit_product_name"]
    field = context.user_data["edit_field"]
    async with SessionLocal() as session:
        product = await get_product_by_name(session, name)
        if not product:
            await update.message.reply_text("Product not found.")
            return ConversationHandler.END
        await edit_product(session, product.id, field, value)
    await update.message.reply_text(f"✅ Product '{name}' updated.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

# --- Add Product Photo ---
async def add_product_photo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the product name to add a photo to:")
    return PHOTO_PRODUCT_NAME

async def receive_product_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    context.user_data["photo_product_name"] = name
    await update.message.reply_text("Send the photo for this product:")
    return PHOTO_RECEIVE

async def save_product_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please send a photo.")
        return PHOTO_RECEIVE
    file_id = update.message.photo[-1].file_id
    name = context.user_data["photo_product_name"]
    async with SessionLocal() as session:
        product = await get_product_by_name(session, name)
        if not product:
            await update.message.reply_text("Product not found.")
            return ConversationHandler.END
        await add_product_photo(session, product.id, file_id)
    await update.message.reply_text("✅ Photo added to product.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

# --- Add Location Photo (Bulk) ---
async def add_location_photo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the product name to add location photos to:")
    return LOCATION_PRODUCT_NAME

async def receive_location_photo_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    context.user_data["location_product_name"] = name
    await update.message.reply_text("Send location photos one by one. Type /done when finished.")
    return LOCATION_RECEIVE

async def save_location_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please send a photo.")
        return LOCATION_RECEIVE
    file_id = update.message.photo[-1].file_id
    name = context.user_data["location_product_name"]
    async with SessionLocal() as session:
        product = await get_product_by_name(session, name)
        if not product:
            await update.message.reply_text("Product not found.")
            return ConversationHandler.END
        await add_location_photo(session, product.id, file_id)
    await update.message.reply_text("Location photo added. Send another or /done to finish.")
    return LOCATION_RECEIVE

async def done_adding_location_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Done adding location photos.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

async def locationphotos_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /locationphotos <product_name>")
        return
    product_name = " ".join(context.args)
    async with SessionLocal() as session:
        product = await get_product_by_name(session, product_name)
        if not product:
            await update.message.reply_text(f"Product '{product_name}' not found.")
            return
        photos = await get_location_photos_by_product(session, product.id)
        available_photos = [p for p in photos if not p.is_delivered]
    count = len(available_photos)
    if count == 0:
        await update.message.reply_text(f"No available location photos for '{product_name}'.")
        return
    await update.message.reply_text(
        f"📦 *{product_name}* has *{count}* available location photo(s):",
        parse_mode="Markdown"
    )
    # Telegram allows up to 10 photos per media group
    batch = []
    for idx, photo in enumerate(available_photos, 1):
        caption = photo.caption if photo.caption else f"Location photo {idx}"
        batch.append(InputMediaPhoto(media=photo.file_id, caption=caption if idx == 1 else None))
        if len(batch) == 10 or idx == count:
            await update.message.reply_media_group(batch)
            batch = []


# --- Show Location Photos ---
async def show_location_photos_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the product name to show location photos for:")
    return SHOW_LOCATION_PHOTOS

async def send_location_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    async with SessionLocal() as session:
        product = await get_product_by_name(session, name)
        if not product:
            await update.message.reply_text("Product not found.")
            return ConversationHandler.END
        photos = await get_location_photos_by_product(session, product.id)
    if not photos:
        await update.message.reply_text("No location photos found for this product.")
        return ConversationHandler.END
    media = [InputMediaPhoto(photo.file_id) for photo in photos]
    await update.message.reply_media_group(media)
    return ConversationHandler.END