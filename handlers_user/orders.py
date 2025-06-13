from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_IDS, DEFAULT_START_COINS
from db import SessionLocal
from db_utils import (
    get_product_by_name, update_product_stock, get_user, set_user_balance,
    get_orders_by_user, add_order, add_profit
)
from datetime import datetime

ORDER_QUANTITY, ORDER_CONFIRM = range(2)

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_name = query.data.replace("order_", "")
    async with SessionLocal() as session:
        product = await get_product_by_name(session, product_name)
    if not product:
        await query.message.reply_text("Product not found.")
        return ConversationHandler.END
    if product.stock < 1:
        await query.message.reply_text(
            f"Sorry, {product.name} is out of stock."
        )
        return ConversationHandler.END
    context.user_data["order_product"] = product
    await query.message.reply_text(
        f"How many *{product.name}* do you want to order?\n"
        f"Stock available: {product.stock}\n"
        f"Price per item: {product.price} coins\n"
        "(Type a number, or /cancel to abort.)",
        parse_mode="Markdown"
    )
    return ORDER_QUANTITY

async def receive_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit() or int(text) < 1:
        await update.message.reply_text("Please enter a valid positive number.")
        return ORDER_QUANTITY
    user_id = str(update.message.from_user.id)
    qty = int(text)
    product = context.user_data.get("order_product")
    async with SessionLocal() as session:
        # Refresh product info
        product_latest = await get_product_by_name(session, product.name)
        if product_latest is None:
            await update.message.reply_text("Something went wrong. Try again.")
            return ConversationHandler.END
        current_stock = product_latest.stock
        price = product_latest.price
        total_cost = price * qty
        user = await get_user(session, user_id)
        balance = user.balance if user else DEFAULT_START_COINS
        if qty > current_stock:
            await update.message.reply_text(f"Sorry, only {current_stock} left in stock.")
            return ORDER_QUANTITY
        if total_cost > balance:
            await update.message.reply_text(f"Not enough coins! You need {total_cost}, but have {balance}.")
            return ConversationHandler.END
    context.user_data["order_quantity"] = qty
    context.user_data["order_total_cost"] = total_cost
    confirm_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data="confirm_order"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_order")
        ]
    ])
    await update.message.reply_text(
        f"You are about to order *{qty} x {product.name}* for *{total_cost} coins*.\n"
        f"Do you want to confirm?",
        parse_mode="Markdown",
        reply_markup=confirm_markup
    )
    return ORDER_CONFIRM

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    product = context.user_data.get("order_product")
    qty = context.user_data.get("order_quantity", 1)
    async with SessionLocal() as session:
        # Refresh product info
        product_latest = await get_product_by_name(session, product.name)
        if product_latest is None:
            await query.message.reply_text("Product not found or has been removed.")
            return ConversationHandler.END
        current_stock = product_latest.stock
        price = product_latest.price
        user = await get_user(session, user_id)
        balance = user.balance if user else DEFAULT_START_COINS
        if qty > current_stock:
            await query.message.reply_text(f"Sorry, not enough stock left. Only {current_stock} available.")
            return ConversationHandler.END
        if price * qty > balance:
            await query.message.reply_text(f"Not enough coins! You need {price * qty}, but have {balance}.")
            return ConversationHandler.END
        # Update stock
        product_latest.stock -= qty
        await session.commit()
        new_stock = product_latest.stock
        low_stock_threshold = 2
        if new_stock <= low_stock_threshold:
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=(
                            f"⚠️ Low Stock Alert!\n"
                            f"Product: {product.name}\n"
                            f"Stock remaining: {new_stock}"
                        )
                    )
                except Exception:
                    pass
        # Update user balance
        user.balance -= price * qty
        await session.commit()
        # Add order
        order_status = "completed" if product_latest.image else "pending"
        order = await add_order(
            session,
            user_id=user_id,
            product_id=product_latest.id,
            product_name=product_latest.name,
            quantity=qty,
            status=order_status,
            created_at=datetime.utcnow()
        )
        await session.commit()
        await query.message.reply_text(
            f"✅ Order confirmed: {qty} x {product.name} for {price * qty} coins!\n"
            f"Your new balance: {user.balance} coins."
        )
        # Log profit for admin
        await add_profit(
            session,
            user_id=user_id,
            product=product.name,
            quantity=qty,
            amount=price * qty,
            stock_id=order.id,
            dt=order.created_at
        )
        # Notify admins about the new order
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"🛒 *New Order Placed!*\n"
                        f"User: [{query.from_user.full_name}](tg://user?id={user_id}) (`{user_id}`)\n"
                        f"Product: {product.name}\n"
                        f"Quantity: {qty}\n"
                        f"Total: {price * qty} coins\n"
                        f"Status: {order_status}"
                    ),
                    parse_mode="Markdown"
                )
            except Exception:
                pass
        location_image = product_latest.image
        location_caption = product_latest.description or "Here is your pickup location."
        if location_image and order_status == "completed":
            try:
                await query.message.reply_photo(
                    photo=location_image,
                    caption=location_caption,
                    parse_mode="Markdown"
                )
            except Exception:
                await query.message.reply_text("Could not send location photo.")
    return ConversationHandler.END

async def cancel_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Order cancelled.")
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END

async def myorders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    async with SessionLocal() as session:
        user_orders = await get_orders_by_user(session, user_id)
    if not user_orders:
        await update.message.reply_text("You don’t have any orders yet.")
        return
    msg = "📝 *Your Orders:*\n"
    for o in user_orders[-10:]:  # Show last 10 orders
        status = o.status
        created = o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else "N/A"
        order_id = o.id
        msg += (
            f"- ID: `{order_id}`\n"
            f"  {o.product_name} x{o.quantity} | Status: *{status}* | Ordered: {created}\n"
        )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def filter_orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    filter_status = query.data.replace("filter_orders_", "")
    async with SessionLocal() as session:
        user_orders = await get_orders_by_user(session, user_id)
    msg = "📝 *Your Orders:*\n"
    found = False
    for o in user_orders:
        status = o.status
        if filter_status != "all" and status != filter_status:
            continue
        created = o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else "N/A"
        order_id = o.id
        msg += f"- ID: `{order_id}`\n  {o.product_name} x{o.quantity} | Status: *{status}* | Ordered: {created}\n"
        found = True
    if not found:
        msg += "No orders found for this filter."
    keyboard = [
        [
            InlineKeyboardButton("🔙 Back to Filters", callback_data="back_to_orders_filters")
        ]
    ]
    await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def back_to_orders_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Pending", callback_data="filter_orders_pending"),
            InlineKeyboardButton("Completed", callback_data="filter_orders_completed"),
            InlineKeyboardButton("Cancelled", callback_data="filter_orders_cancelled")
        ],
        [InlineKeyboardButton("All", callback_data="filter_orders_all")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
    ]
    await query.message.reply_text("Filter your orders:", reply_markup=InlineKeyboardMarkup(keyboard))