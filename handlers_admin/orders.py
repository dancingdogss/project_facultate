from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from db_utils import (
    get_order_by_id, get_orders, update_order_status, get_all_deliveries,
    remove_delivery, get_delivery_by_id
)
from db_utils import get_user, set_user_balance, get_product

async def set_order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /setorderstatus <order_id> <status>")
        return
    order_id, new_status = args[0], args[1]
    async with SessionLocal() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await update.message.reply_text("Order not found.")
            return
        if order.status == "completed":
            await update.message.reply_text("Cannot change status of a completed order.")
            return
        # Refund if cancelling a pending order
        if order.status == "pending" and new_status == "cancelled":
            user = await get_user(session, order.user_id)
            product = await get_product(session, order.product_id)
            if product and user:
                refund = product.price * order.quantity
                await set_user_balance(session, user.id, user.balance + refund)
                await update.message.reply_text(f"User refunded {refund} coins for cancelled order.")
        # Send location if marking as completed and product has location_image
        if order.status == "pending" and new_status == "completed":
            product = await get_product(session, order.product_id)
            if product and product.image:
                try:
                    await context.bot.send_photo(
                        chat_id=order.user_id,
                        photo=product.image,
                        caption=product.description or "Here is your pickup location.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    await update.message.reply_text(f"Could not send location photo to user: {e}")
        order.status = new_status
        await session.commit()
        await update.message.reply_text(f"Order {order_id} status updated to {new_status}.")

async def all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        orders = await get_orders(session, limit=30)
    msg = "📦 *All Orders:*\n"
    if not orders:
        msg += "No orders found."
    else:
        for order in orders:
            msg += (
                f"- ID: `{order.id}` | {order.product_name} x{order.quantity} | "
                f"User: `{order.user_id}` | Status: *{order.status}* | {order.created_at}\n"
            )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def export_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import csv
    from io import StringIO
    async with SessionLocal() as session:
        orders = await get_orders(session, limit=1000)
    csvfile = StringIO()
    writer = csv.writer(csvfile)
    writer.writerow(['User ID', 'Order ID', 'Product', 'Quantity', 'Status', 'Created At'])
    for order in orders:
        writer.writerow([
            order.user_id,
            order.id,
            order.product_name,
            order.quantity,
            order.status,
            order.created_at
        ])
    csvfile.seek(0)
    await update.message.reply_document(
        document=csvfile.getvalue().encode(),
        filename="orders_export.csv",
        caption="🗂️ All orders exported as CSV."
    )

async def deliveries_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        deliveries = await get_all_deliveries(session)
    if not deliveries:
        await update.message.reply_text("No deliveries found.")
        return
    msg = "🚚 *Deliveries:*\n"
    for d in deliveries:
        msg += f"- ID: `{d.id}` | {d.info}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def removedelivery_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /removedelivery <delivery_id>")
        return
    delivery_id = args[0]
    async with SessionLocal() as session:
        success = await remove_delivery(session, delivery_id)
    if not success:
        await update.message.reply_text("Delivery not found.")
        return
    await update.message.reply_text(f"Delivery {delivery_id} removed.")

async def export_deliveries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import csv
    from io import StringIO
    async with SessionLocal() as session:
        deliveries = await get_all_deliveries(session)
    csvfile = StringIO()
    writer = csv.writer(csvfile)
    writer.writerow(['Delivery ID', 'Info'])
    for d in deliveries:
        writer.writerow([
            d.id,
            getattr(d, "info", "")
        ])
    csvfile.seek(0)
    await update.message.reply_document(
        document=csvfile.getvalue().encode(),
        filename="deliveries_export.csv",
        caption="🗂️ All deliveries exported as CSV."
    )

async def findorder_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /findorder <order_id>")
        return
    order_id = args[0]
    async with SessionLocal() as session:
        order = await get_order_by_id(session, order_id)
    if order:
        msg = (
            f"Order found:\n"
            f"User: `{order.user_id}`\n"
            f"Product: {order.product_name}\n"
            f"Quantity: {order.quantity}\n"
            f"Status: {order.status}\n"
            f"Created: {order.created_at}"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("Order not found.")