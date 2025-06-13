from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler
from db import SessionLocal
from db_utils import (
    add_product, remove_product, edit_product, get_all_products, get_product_by_name, add_location_photo
)
from sqlalchemy.future import select
from db import LocationPhoto

# --- Conversation states ---
ADD_PRODUCT_PHOTO = 1
ADD_LOCATION_PHOTO_BULK = 2
ADD_PRODUCT_PHOTO_BULK = 3

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

# --- Single Presentation Photo Management ---

async def add_product_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /addproductphoto <product_name>")
        return ConversationHandler.END
    product_name = " ".join(args)
    context.user_data['photo_product_name'] = product_name
    await update.message.reply_text(f"Send the presentation photo for {product_name}")
    return ADD_PRODUCT_PHOTO

async def receive_product_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_name = context.user_data.get('photo_product_name')
    if not product_name or not update.message.photo:
        await update.message.reply_text("Please use /addproductphoto <product_name> first and then send a photo.")
        return ConversationHandler.END
    file_id = update.message.photo[-1].file_id
    async with SessionLocal() as session:
        product = await get_product_by_name(session, product_name)
        if not product:
            await update.message.reply_text("Product not found.")
            return ConversationHandler.END
        product.image = file_id
        await session.commit()
        await update.message.reply_text("Presentation photo updated.")
    context.user_data.pop('photo_product_name', None)
    return ConversationHandler.END

# --- Bulk Presentation Photo Management ---

async def add_product_photo_bulk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /addproductphoto_bulk <product_name>")
        return ConversationHandler.END
    product_name = " ".join(args)
    context.user_data['photo_product_name_bulk'] = product_name
    await update.message.reply_text(
        f"Send one or more presentation photos for {product_name}.\n"
        "When finished, send /done."
    )
    return ADD_PRODUCT_PHOTO_BULK

async def receive_product_photo_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_name = context.user_data.get('photo_product_name_bulk')
    if not product_name:
        await update.message.reply_text("Please use /addproductphoto_bulk <product_name> first.")
        return ConversationHandler.END
    if not update.message.photo:
        await update.message.reply_text("Please send a photo, not text.")
        return ADD_PRODUCT_PHOTO_BULK
    file_id = update.message.photo[-1].file_id
    async with SessionLocal() as session:
        product = await get_product_by_name(session, product_name)
        if not product:
            await update.message.reply_text("Product not found.")
            return ConversationHandler.END
        # For bulk, just update the main image each time (last photo sent is used in catalog)
        product.image = file_id
        await session.commit()
        await update.message.reply_text("Presentation photo updated. Send more or /done to finish.")
    return ADD_PRODUCT_PHOTO_BULK

async def done_adding_product_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('photo_product_name_bulk', None)
    await update.message.reply_text("Bulk presentation photo upload finished.")
    return ConversationHandler.END

# --- Bulk Location Photo Management ---

async def add_location_photo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /addlocationphoto <product_name>")
        return ConversationHandler.END
    product_name = " ".join(args)
    context.user_data['location_photo_product'] = product_name
    await update.message.reply_text(
        f"Send one or more location photos for {product_name}.\n"
        "When finished, send /done."
    )
    return ADD_LOCATION_PHOTO_BULK

async def receive_location_photo_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_name = context.user_data.get('location_photo_product')
    if not product_name:
        await update.message.reply_text("Please use /addlocationphoto <product_name> first.")
        return ConversationHandler.END
    if not update.message.photo:
        await update.message.reply_text("Please send a photo, not text.")
        return ADD_LOCATION_PHOTO_BULK
    file_id = update.message.photo[-1].file_id
    caption = update.message.caption or ""
    async with SessionLocal() as session:
        product = await get_product_by_name(session, product_name)
        if not product:
            await update.message.reply_text("Product not found.")
            return ConversationHandler.END
        await add_location_photo(session, product.id, file_id, caption)
        await update.message.reply_text("Location photo added. Send more or /done to finish.")
    return ADD_LOCATION_PHOTO_BULK

async def done_adding_location_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('location_photo_product', None)
    await update.message.reply_text("Bulk location photo upload finished.")
    return ConversationHandler.END

# --- Show Available Location Photos for a Product (Admin Only) ---

async def show_location_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Optionally, restrict to admins only (uncomment and set your admin IDs)
    # ADMIN_IDS = ["123456789", ...]
    # if str(update.effective_user.id) not in ADMIN_IDS:
    #     await update.message.reply_text("You are not authorized to use this command.")
    #     return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /showlocationphotos <product_name>")
        return

    product_name = " ".join(args)
    async with SessionLocal() as session:
        product = await get_product_by_name(session, product_name)
        if not product:
            await update.message.reply_text("Product not found.")
            return

        result = await session.execute(
            select(LocationPhoto).where(
                LocationPhoto.product_id == product.id,
                LocationPhoto.is_delivered == False
            )
        )
        photos = result.scalars().all()
        if not photos:
            await update.message.reply_text("No available location photos for this product.")
            return

        for photo in photos:
            await update.message.reply_photo(
                photo=photo.file_id,
                caption=f"Photo ID: {photo.id}\nProduct: {product.name}"
            )