from sqlalchemy import select
from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal, Order
from utils.db_utils import (
    get_all_orders, update_order_status, get_order_by_id, get_unused_location_photo, mark_location_photo_delivered, get_products_by_category
)

async def all_orders(update, context):
    category = " ".join(context.args) if context.args else None
    async with SessionLocal() as session:
        if category:
            # Filter orders by product category
            products = await get_products_by_category(session, category)
            product_ids = [p.id for p in products]
            if not product_ids:
                await update.message.reply_text(f"No products found in category '{category}'.")
                return
            orders = []
            for pid in product_ids:
                result = await session.execute(select(Order).where(Order.product_id == pid))
                orders.extend(result.scalars().all())
        else:
            orders = await get_all_orders(session)
    if not orders:
        await update.message.reply_text("No orders found.")
        return

    order_lines = []
    for order in orders:
        order_lines.append(
            f"🛒 *Order ID:* `{order.id}`\n"
            f"👤 *User ID:* `{order.user_id}`\n"
            f"📦 *Product:* {order.product_name}\n"
            f"🔢 *Quantity:* {order.quantity}\n"
            f"📅 *Date:* `{order.created_at}`\n"
            f"🚦 *Status:* {order.status}\n"
        )

    # Group orders so each message is <4000 chars
    MAX_LEN = 4000
    chunk = ""
    for line in order_lines:
        if len(chunk) + len(line) > MAX_LEN:
            await update.message.reply_text(chunk, parse_mode="Markdown")
            chunk = ""
        chunk += line + "\n"
    if chunk:
        await update.message.reply_text(chunk, parse_mode="Markdown")

# --- Stubs for other admin order commands ---

async def export_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Export orders (stub)")

async def set_order_status(update, context):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /setorderstatus <order_id> <new_status>")
        return
    order_id, new_status = args[0], args[1]
    async with SessionLocal() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await update.message.reply_text("Order not found.")
            return

        # Only do the location photo logic if marking as completed
        if new_status == "completed":
            # Get an unused location photo for this product
            photo = await get_unused_location_photo(session, order.product_id)
            if not photo:
                await update.message.reply_text("No unused location photos available for this product!")
                return

            # Mark photo as delivered and link to order
            await mark_location_photo_delivered(session, photo.id, order_id)

            # Send photo to user
            try:
                await context.bot.send_photo(
                    chat_id=order.user_id,
                    photo=photo.file_id,
                    caption=photo.caption or "Here is your pickup location!"
                )
            except Exception as e:
                await update.message.reply_text(f"Failed to send photo to user: {e}")

        # Update order status
        result = await update_order_status(session, order_id, new_status)
    if result is None:
        await update.message.reply_text("Order not found.")
    elif result == "completed":
        await update.message.reply_text("Order is already completed.")
    else:
        await update.message.reply_text(f"Order {order_id} status updated to {new_status}.")

async def deliveries_cmd(update, context):
    async with SessionLocal() as session:
        deliveries = await get_all_deliveries(session)
    if not deliveries:
        await update.message.reply_text("No deliveries found.")
        return
    msg = ""
    for d in deliveries:
        msg += (
            f"🚚 Delivery ID: {d.id}\n"
            f"Product ID: {d.product_id}\n"
            f"Order ID: {d.order_id}\n"
            f"Delivered At: {d.delivered_at}\n\n"
        )
    await update.message.reply_text(msg)

async def findorder_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Find order (stub)")

async def export_deliveries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Export deliveries (stub)")

async def removedelivery_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Remove delivery (stub)")