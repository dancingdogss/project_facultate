from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from db import SessionLocal
from utils.db_utils import add_order, get_product_by_name, get_product_by_id, get_orders_by_user, get_user, get_order_by_id
from datetime import datetime
from handlers_admin.orders import fulfill_order_and_deliver_photos

ORDER_QUANTITY, ORDER_CONFIRM = range(2)
ADMIN_IDS = [5501799605]  # <-- Replace with your actual admin Telegram user IDs
LOW_STOCK_THRESHOLD = 5   # You can adjust this threshold as needed

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

        # Check user balance
        user_obj = await get_user(session, str(user.id))
        total_price = product.price * quantity
        if user_obj.balance < total_price:
            await query.message.reply_text(f"Insufficient balance. You need {total_price} coins.")
            return ConversationHandler.END

        # Deduct balance
        user_obj.balance -= total_price

        # Reduce product stock
        product.stock -= quantity
        await session.commit()

        # --- Stock alert logic ---
        if product.stock < LOW_STOCK_THRESHOLD:
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"⚠️ Low stock alert!\nProduct: {product.name}\nStock left: {product.stock}"
                    )
                except Exception as e:
                    print(f"Failed to notify admin {admin_id} about low stock: {e}")

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
        await session.commit()

        # Fetch the order again (with ID)
        order = await get_order_by_id(session, order.id)

        # Fulfill order and deliver photos if possible
        ADMIN_CHAT_ID = ADMIN_IDS[0]  # Use the first admin for fulfillment notifications
        await fulfill_order_and_deliver_photos(session, context.bot, order, user_obj, product, admin_chat_id=ADMIN_CHAT_ID)

    # Notify user (fulfillment function also sends messages, but this is a fallback)
    await query.message.reply_text(f"✅ Order placed for {quantity} units of {product_name}!")

    # Notify admin (already done in fulfill_order_and_deliver_photos, but you can keep this for redundancy)
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

async def orderstatus_cmd(update, context):
    args = update.message.text.split()
    if len(args) != 2:
        await update.message.reply_text("Usage: /orderstatus <order_id>")
        return
    order_id = args[1]
    user_id = str(update.effective_user.id)
    async with SessionLocal() as session:
        order = await get_order_by_id(session, order_id)
    if not order or str(order.user_id) != user_id:
        await update.message.reply_text("Order not found.")
        return
    await update.message.reply_text(
        f"Order {order.id} status: {order.status}\n"
        f"Product: {order.product_name}\n"
        f"Quantity: {order.quantity}\n"
        f"Date: {order.created_at}"
    )

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
    # Split long messages to avoid Telegram's 4096 char limit
    MAX_LEN = 4000
    lines = msg.split('\n')
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) + 1 > MAX_LEN:
            await update.message.reply_text(chunk, parse_mode="Markdown")
            chunk = ""
        chunk += line + "\n"
    if chunk:
        await update.message.reply_text(chunk, parse_mode="Markdown")

# --- Stubs for compatibility ---

async def back_to_orders_filters(update, context):
    await update.callback_query.answer("Back to orders filters (stub)")

async def simulate_deposit(update, context):
    await update.message.reply_text("Simulated deposit (stub)")