from sqlalchemy import select
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from db import SessionLocal, LocationPhoto
from utils.db_utils import (
    add_order, get_product_by_name, get_orders_by_user, get_user, set_user_balance,
    get_unused_location_photos_by_product, mark_location_photo_delivered, update_order_status,
    log_delivered_photo  # <-- add this if not present 
)
from utils.file_utils import save_delivered_photo_to_folder
from datetime import datetime


ORDER_QUANTITY, ORDER_CONFIRM = range(2)

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_name = query.data.replace("order_", "")
    context.user_data["order_product"] = product_name
    await query.message.reply_text(f"How many units of {product_name} do you want to order?")
    return ORDER_QUANTITY

async def receive_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quantity = update.message.text
    if not quantity.isdigit() or int(quantity) <= 0:
        await update.message.reply_text("Please enter a valid positive number.")
        return ORDER_QUANTITY
    context.user_data["order_quantity"] = int(quantity)
    product_name = context.user_data["order_product"]
    keyboard = [
        [InlineKeyboardButton("✅ Yes", callback_data="confirm_order"),
         InlineKeyboardButton("❌ No", callback_data="cancel_order")]
    ]
    await update.message.reply_text(
        f"Confirm order for {quantity} units of {product_name}?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ORDER_CONFIRM





async def confirm_order(update, context):
    query = update.callback_query
    await query.answer()
    product_name = context.user_data.get("order_product")
    quantity = context.user_data.get("order_quantity")
    user = query.from_user

    async with SessionLocal() as session:
        product = await get_product_by_name(session, product_name)
        if not product:
            await query.message.reply_text("Sorry, this product no longer exists.")
            return ConversationHandler.END

        db_user = await get_user(session, str(user.id))
        total_price = product.price * quantity

        if db_user.balance < total_price:
            await query.message.reply_text("❌ Not enough balance for this order.")
            return ConversationHandler.END

        if product.stock < quantity:
            await query.message.reply_text("❌ Not enough stock for this order.")
            return ConversationHandler.END
        
        # Deduct balance and stock
        db_user.balance -= total_price
        product.stock -= quantity
        await session.commit()

        # Save order to DB
        order = await add_order(
            session=session,
            user_id=str(user.id),
            product_id=product.id,
            product_name=product.name,
            quantity=quantity,
            status="pending",
            created_at=datetime.utcnow()
        )

        # Get all unused location photos for this product
        result = await session.execute(
            select(LocationPhoto).where(
                LocationPhoto.product_id == product.id,
                LocationPhoto.is_delivered == False
            ).limit(quantity)
        )
        photos = result.scalars().all()

        fulfilled = 0
        for photo in photos:
            # Mark photo as delivered
            await mark_location_photo_delivered(session, photo.id, order.id)
            # Send photo to user
            try:
                await context.bot.send_photo(
                    chat_id=user.id,
                    photo=photo.file_id,
                    caption=photo.caption or "Here is your pickup location!"
                )
                # Log the delivered photo in the database
                await log_delivered_photo(
                    session,
                    order.id,
                    str(user.id),
                    product.id,
                    product.name,
                    photo.file_id,
                    photo.caption or ""
                )
                # Save the delivered photo to the folder
                await save_delivered_photo_to_folder(
                    context.bot,
                    photo.file_id,
                    product.name,
                    order.id,
                    user.id
                )
                fulfilled += 1
            except Exception as e:
                print(f"Failed to send photo: {e}")

        # If all units fulfilled, mark order as completed
        if fulfilled == quantity:
            await update_order_status(session, order.id, "completed")
            await query.message.reply_text(f"✅ Order placed and fulfilled for {quantity} units of {product_name}!")
        else:
            # Partial fulfillment
            await update_order_status(session, order.id, "pending")
            await query.message.reply_text(
                f"⚠️ Only {fulfilled} out of {quantity} units could be fulfilled for {product_name}.\n"
                f"Order remains pending for the rest. You will receive the rest as soon as more locations are added."
            )

    # Notify user (summary)
    await query.message.reply_text(f"✅ Order placed for {quantity} units of {product_name}!")

    # Notify admin (replace ADMIN_CHAT_ID with your admin's chat id)
    ADMIN_CHAT_ID = 5501799605  # <-- set your admin Telegram user/chat ID here
    admin_msg = (
        f"🛒 New Order!\n"
        f"User: {user.full_name} (@{user.username or 'N/A'})\n"
        f"User ID: {user.id}\n"
        f"Product: {product_name}\n"
        f"Quantity: {quantity}"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg)
    except Exception as e:
        print(f"Failed to notify admin: {e}")

    # Clear user_data
    context.user_data.pop("order_product", None)
    context.user_data.pop("order_quantity", None)
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if hasattr(update, "callback_query"):
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("Order cancelled.")
    else:
        await update.message.reply_text("Order cancelled.")
    context.user_data.pop("order_product", None)
    context.user_data.pop("order_quantity", None)
    return ConversationHandler.END

# --- User's Order History ---
async def myorders_cmd(update, context):
    user_id = str(update.effective_user.id)
    async with SessionLocal() as session:
        orders = await get_orders_by_user(session, user_id)
    if not orders:
        await update.message.reply_text("You have no orders yet.")
        return
    msg = ""
    for order in orders:
        msg += (
            f"🛒 *Order ID:* {order.id}\n"
            f"📦 Product: {order.product_name}\n"
            f"🔢 Quantity: {order.quantity}\n"
            f"📅 Date: {order.created_at}\n"
            f"🚦 Status: {order.status}\n\n"
        )
    await update.message.reply_text(msg, parse_mode="Markdown")

# --- Stubs for compatibility ---
async def filter_orders_callback(update, context):
    await update.callback_query.answer("Filter orders (stub)")

async def back_to_orders_filters(update, context):
    await update.callback_query.answer("Back to orders filters (stub)")

async def simulate_deposit(update, context):
    await update.message.reply_text("Simulated deposit (stub)")