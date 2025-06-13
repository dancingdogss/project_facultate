from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from db import SessionLocal
from utils.db_utils import add_order, get_product_by_name, get_orders_by_user
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

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_name = context.user_data.get("order_product")
    quantity = context.user_data.get("order_quantity")
    user = query.from_user

    async with SessionLocal() as session:
        # Get product info
        product = await get_product_by_name(session, product_name)
        if not product:
            await query.message.reply_text("Sorry, this product no longer exists.")
            return ConversationHandler.END
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

    # Notify user
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