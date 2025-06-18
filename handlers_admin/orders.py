import random
import os
import io
import csv
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from db import SessionLocal
from utils.db_utils import (
    get_all_orders, get_order_by_id, get_product_by_id, get_location_photos_by_product,
    get_user
)
import asyncio

SET_ORDER_ID, SET_ORDER_STATUS = range(2)

# --- ALL ORDERS FILTER INTERFACE ---

async def all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("By User", callback_data="filter_user")],
        [InlineKeyboardButton("By Order ID", callback_data="filter_id")],
        [InlineKeyboardButton("By Product", callback_data="filter_product")],
        [InlineKeyboardButton("By Date", callback_data="filter_date")],
        [InlineKeyboardButton("Show All", callback_data="filter_all")]
    ]
    await update.message.reply_text(
        "How would you like to filter orders?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def filter_orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    filter_type = query.data.replace("filter_", "")
    context.user_data["filter_type"] = filter_type

    if filter_type == "all":
        await show_orders(update, context, filter_type=None, filter_value=None)
        return

    prompt = {
        "user": "Enter the User ID:",
        "id": "Enter the Order ID:",
        "product": "Enter the Product Name:",
        "date": "Enter the Date (YYYY-MM-DD):"
    }
    await query.message.reply_text(prompt[filter_type])
    context.user_data["awaiting_filter_value"] = True



async def filter_value_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("filter_value_input called. Awaiting:", context.user_data.get("awaiting_filter_value"))  # Debug print
    # Only process if we're in the filter flow
    if not context.user_data.get("awaiting_filter_value"):
        return  # Let other handlers process this message!

    filter_type = context.user_data.get("filter_type")
    value = update.message.text.strip()
    await show_orders(update, context, filter_type, value)

    # Clean up filter state
    context.user_data.pop("awaiting_filter_value", None)
    context.user_data.pop("filter_type", None)

async def show_orders(update, context, filter_type=None, filter_value=None):
    async with SessionLocal() as session:
        orders = await get_all_orders(session)
        if filter_type == "user":
            filtered = [o for o in orders if str(o.user_id) == str(filter_value)]
        elif filter_type == "id":
            filtered = [o for o in orders if str(o.id) == filter_value]
        elif filter_type == "product":
            filtered = [o for o in orders if filter_value.lower() in o.product_name.lower()]
        elif filter_type == "date":
            filtered = [o for o in orders if str(o.created_at).startswith(filter_value)]
        else:
            filtered = orders

    if not filtered:
        await update.message.reply_text("No orders found for this filter.")
        return

    # Group by status for clarity
    grouped = {}
    for order in filtered:
        grouped.setdefault(order.status.capitalize(), []).append(order)

    msg = ""
    for status, group in grouped.items():
        msg += f"\n<b>{status} Orders ({len(group)}):</b>\n"
        msg += "<pre>OrderID                             UserID   Product         Qty   Date\n"
        msg += "---------------------------------  -------  --------------  ----  ----------\n"
        for o in group:
            msg += f"{str(o.id):<34} {str(o.user_id):<8} {o.product_name[:14]:<15} {str(o.quantity):<6} {str(o.created_at)[:10]}\n"
        msg += "</pre>\n"
        for o in group:
            msg += f"Full Order ID: <code>{o.id}</code>\n"

    await update.message.reply_text(msg, parse_mode="HTML")

# --- Set Order Status Implementation ---

async def set_order_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the order ID to update:")
    return SET_ORDER_ID

async def set_order_status_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_id = update.message.text.strip()
    context.user_data["set_order_id"] = order_id
    await update.message.reply_text("Enter new status (completed/canceled):")
    return SET_ORDER_STATUS

async def set_order_status_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = update.message.text.strip().lower()
    order_id = context.user_data["set_order_id"]
    if status not in ["completed", "canceled"]:
        await update.message.reply_text("Invalid status. Use 'completed' or 'canceled'.")
        return SET_ORDER_STATUS

    async with SessionLocal() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await update.message.reply_text("Order not found.")
            return ConversationHandler.END

        user = await get_user(session, order.user_id)
        product = await get_product_by_id(session, order.product_id)
        if not user or not product:
            await update.message.reply_text("User or product not found.")
            return ConversationHandler.END

        delivered_count = getattr(order, "delivered_count", 0)
        quantity = getattr(order, "quantity", 1)
        to_deliver = quantity - delivered_count

        if status == "completed":
            photos = await get_location_photos_by_product(session, product.id)
            if len(photos) < to_deliver:
                await update.message.reply_text(
                    f"Not enough location photos to complete the order. Needed: {to_deliver}, available: {len(photos)}."
                )
                return ConversationHandler.END
            selected_photos = random.sample(photos, to_deliver)
            for photo in selected_photos:
                await context.bot.send_photo(chat_id=user.id, photo=photo.file_id, caption=photo.caption or "")
                await session.delete(photo)
            order.status = "completed"
            order.delivered_count = quantity
            await session.commit()
            await update.message.reply_text("Order marked as completed and photos delivered.")
        elif status == "canceled":
            refund_units = quantity - delivered_count
            refund_amount = refund_units * product.price
            user.balance += refund_amount
            order.status = "canceled"
            await session.commit()
            await context.bot.send_message(chat_id=user.id, text=f"Your order {order_id} was canceled. You have been refunded {refund_amount} coins.")
            await update.message.reply_text("Order canceled and user refunded.")

        # Notify the user of the status change
        await context.bot.send_message(
            chat_id=order.user_id,
            text=f"Your order {order.id} status has changed to: {order.status}."
        )

    return ConversationHandler.END

# --- Fulfill Order and Deliver Photos ---

async def fulfill_order_and_deliver_photos(session, bot, order, user, product, admin_chat_id=None):
    from utils.db_utils import get_location_photos_by_product

    quantity = getattr(order, "quantity", 1)
    delivered_count = getattr(order, "delivered_count", 0)
    to_deliver = quantity - delivered_count

    photos = await get_location_photos_by_product(session, product.id)
    delivered_now = 0

    delivered_folder = os.path.join(os.getcwd(), "delivered_photos")
    os.makedirs(delivered_folder, exist_ok=True)

    if len(photos) >= to_deliver:
        selected_photos = random.sample(photos, to_deliver)
        for photo in selected_photos:
            # Send photo to user
            await bot.send_photo(chat_id=user.id, photo=photo.file_id, caption=photo.caption or "")
            # Download photo from Telegram and save to delivered_photos
            file = await bot.get_file(photo.file_id)
            dt_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{product.name}_{user.id}_{order.id}_{dt_str}.jpg"
            filepath = os.path.join(delivered_folder, filename)
            await file.download_to_drive(filepath)
            # Remove photo from product (delete from DB)
            await session.delete(photo)
            delivered_now += 1
        order.status = "completed"
        order.delivered_count = quantity
        await session.commit()
        await bot.send_message(chat_id=user.id, text="Your order is completed and all location photos have been sent!")
        if admin_chat_id:
            await bot.send_message(chat_id=admin_chat_id, text=f"Order {order.id} for user {user.id} auto-completed and delivered.")
    else:
        if len(photos) > 0:
            selected_photos = random.sample(photos, len(photos))
            for photo in selected_photos:
                await bot.send_photo(chat_id=user.id, photo=photo.file_id, caption=photo.caption or "")
                file = await bot.get_file(photo.file_id)
                dt_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"{product.name}_{user.id}_{order.id}_{dt_str}.jpg"
                filepath = os.path.join(delivered_folder, filename)
                await file.download_to_drive(filepath)
                await session.delete(photo)
                delivered_now += 1
            await bot.send_message(chat_id=user.id, text=f"{delivered_now} location photo(s) sent. The rest will be delivered when available.")
        else:
            await bot.send_message(chat_id=user.id, text="No location photos available yet. Your order is pending.")
        order.status = "pending"
        order.delivered_count = delivered_now
        await session.commit()
        if admin_chat_id:
            await bot.send_message(chat_id=admin_chat_id, text=f"Order {order.id} for user {user.id} is pending (not enough location photos).")

# --- Export Orders Implementation ---

async def export_orders(update, context):
    async with SessionLocal() as session:
        orders = await get_all_orders(session)
    if not orders:
        await update.message.reply_text("No orders to export.")
        return
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Order ID", "User ID", "Product", "Quantity", "Status", "Created At"])
    for o in orders:
        writer.writerow([o.id, o.user_id, o.product_name, o.quantity, o.status, o.created_at])
    output.seek(0)
    await update.message.reply_document(document=io.BytesIO(output.getvalue().encode()), filename="orders.csv")

# --- Stubs for other admin order commands ---

async def deliveries_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Deliveries (stub)")

async def findorder_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args) < 3:
        await update.message.reply_text(
            "Usage:\n"
            "/findorder user <user_id>\n"
            "/findorder product <product_name>\n"
            "/findorder status <status>\n"
            "/findorder date <YYYY-MM-DD>"
        )
        return

    filter_type = args[1].lower()
    filter_value = " ".join(args[2:])

    async with SessionLocal() as session:
        if filter_type == "user":
            orders = await get_all_orders(session)
            filtered = [o for o in orders if str(o.user_id) == filter_value]
        elif filter_type == "product":
            orders = await get_all_orders(session)
            filtered = [o for o in orders if filter_value.lower() in o.product_name.lower()]
        elif filter_type == "status":
            orders = await get_all_orders(session)
            filtered = [o for o in orders if o.status.lower() == filter_value.lower()]
        elif filter_type == "date":
            orders = await get_all_orders(session)
            filtered = [o for o in orders if str(o.created_at).startswith(filter_value)]
        else:
            await update.message.reply_text("Unknown filter type.")
            return

    if not filtered:
        await update.message.reply_text("No orders found for this filter.")
        return

    for order in filtered:
        msg = (
            f"🛒 *Order ID:* {order.id}\n"
            f"👤 User ID: {order.user_id}\n"
            f"📦 Product: {order.product_name}\n"
            f"🔢 Quantity: {order.quantity}\n"
            f"📅 Date: {order.created_at}\n"
            f"🚦 Status: {order.status}"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

async def export_deliveries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Export deliveries (stub)")

async def removedelivery_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Remove delivery (stub)")