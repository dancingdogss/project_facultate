from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from utils.db_utils import get_all_orders

async def all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        orders = await get_all_orders(session)
    if not orders:
        await update.message.reply_text("No orders found.")
        return
    for order in orders:
        msg = (
            f"🛒 *Order ID:* {order.id}\n"
            f"👤 User ID: {order.user_id}\n"
            f"📦 Product: {order.product_name}\n"
            f"🔢 Quantity: {order.quantity}\n"
            f"📅 Date: {order.created_at}\n"
            f"🚦 Status: {order.status}"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

# --- Stubs for other admin order commands ---

async def export_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Export orders (stub)")

async def set_order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Set order status (stub)")

async def deliveries_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Deliveries (stub)")

async def findorder_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Find order (stub)")

async def export_deliveries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Export deliveries (stub)")

async def removedelivery_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Remove delivery (stub)")