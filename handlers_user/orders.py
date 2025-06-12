from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from models import load_json, save_json
from config import ADMIN_IDS, DEFAULT_START_COINS
import uuid
from datetime import datetime

ORDER_QUANTITY, ORDER_CONFIRM = range(2)

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_name = query.data.replace("order_", "")
    products = load_json("products.json", [])
    product = next((p for p in products if p["name"] == product_name), None)
    if not product:
        await query.message.reply_text("Product not found.")
        return ConversationHandler.END
    if product.get("stock", 0) < 1:
        await query.message.reply_text(
            f"Sorry, {product['name']} is out of stock."
        )
        return ConversationHandler.END
    context.user_data["order_product"] = product
    await query.message.reply_text(
        f"How many *{product['name']}* do you want to order?\n"
        f"Stock available: {product.get('stock', 0)}\n"
        f"Price per item: {product['price']} coins\n"
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
    products = load_json("products.json", [])
    # Find the latest product info by name
    product_latest = next((p for p in products if p["name"] == product["name"]), None)
    if product_latest is None:
        await update.message.reply_text("Something went wrong. Try again.")
        return ConversationHandler.END
    current_stock = product_latest.get("stock", 0)
    price = product_latest.get("price", 0)
    total_cost = price * qty
    balances = load_json("balances.json", {})
    balance = balances.get(user_id, DEFAULT_START_COINS)
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
        f"You are about to order *{qty} x {product['name']}* for *{total_cost} coins*.\n"
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
    products = load_json("products.json", [])
    # Find the latest product info by name
    product_latest = next((p for p in products if p["name"] == product["name"]), None)
    if product_latest is None:
        await query.message.reply_text("Product not found or has been removed.")
        return ConversationHandler.END
    current_stock = product_latest.get("stock", 0)
    price = product_latest.get("price", 0)
    balances = load_json("balances.json", {})
    balance = balances.get(user_id, DEFAULT_START_COINS)
    if qty > current_stock:
        await query.message.reply_text(f"Sorry, not enough stock left. Only {current_stock} available.")
        return ConversationHandler.END
    if price * qty > balance:
        await query.message.reply_text(f"Not enough coins! You need {price * qty}, but have {balance}.")
        return ConversationHandler.END
    # Update stock
    product_latest["stock"] -= qty
    save_json("products.json", products)
    low_stock_threshold = 2
    new_stock = product_latest["stock"]
    if new_stock <= low_stock_threshold:
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"⚠️ Low Stock Alert!\n"
                        f"Product: {product['name']}\n"
                        f"Stock remaining: {new_stock}"
                    )
                )
            except Exception:
                pass
    balances[user_id] = balance - (price * qty)
    save_json("balances.json", balances)
    orders = load_json("orders.json", {})
    if user_id not in orders:
        orders[user_id] = []
    location_image = product_latest.get("location_image")
    order_status = "completed" if location_image else "pending"
    order = {
        "order_id": str(uuid.uuid4()),
        "name": product["name"],
        "quantity": qty,
        "order_status": order_status,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    orders[user_id].append(order)
    save_json("orders.json", orders)
    await query.message.reply_text(
        f"✅ Order confirmed: {qty} x {product['name']} for {price * qty} coins!\n"
        f"Your new balance: {balances[user_id]} coins."
    )
    # Log profit for admin
    profits = load_json("profits.json", [])
    profit_entry = {
        "user_id": user_id,
        "product": product["name"],
        "quantity": qty,
        "amount": price * qty,
        "stock_id": order["order_id"],
        "datetime": order["created_at"]
    }
    profits.append(profit_entry)
    save_json("profits.json", profits)
    # Notify admins about the new order
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"🛒 *New Order Placed!*\n"
                    f"User: [{query.from_user.full_name}](tg://user?id={user_id}) (`{user_id}`)\n"
                    f"Product: {product['name']}\n"
                    f"Quantity: {qty}\n"
                    f"Total: {price * qty} coins\n"
                    f"Status: {order_status}"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass
    location_image = product_latest.get("location_image")
    location_caption = product_latest.get("location_caption", "Here is your pickup location.")
    if location_image:
        try:
            await query.message.reply_photo(
                photo=location_image,
                caption=location_caption,
                parse_mode="Markdown"
            )
        except Exception as e:
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
    orders = load_json("orders.json", {})
    user_orders = orders.get(user_id, [])
    if not user_orders:
        await update.message.reply_text("You don’t have any orders yet.")
        return
    msg = "📝 *Your Orders:*\n"
    for o in user_orders[-10:]:  # Show last 10 orders
        if isinstance(o, dict):
            status = o.get("order_status", "pending")
            created = o.get("created_at", "N/A")
            order_id = o.get("order_id", "N/A")
            msg += (
                f"- ID: `{order_id}`\n"
                f"  {o['name']} x{o['quantity']} | Status: *{status}* | Ordered: {created}\n"
            )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def filter_orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    orders = load_json("orders.json", {})
    user_orders = orders.get(user_id, [])
    filter_status = query.data.replace("filter_orders_", "")
    msg = "📝 *Your Orders:*\n"
    found = False
    for o in user_orders:
        if isinstance(o, dict):
            status = o.get("order_status", "pending")
            if filter_status != "all" and status != filter_status:
                continue
            created = o.get("created_at", "N/A")
            order_id = o.get("order_id", "N/A")
            msg += f"- ID: `{order_id}`\n  {o['name']} x{o['quantity']} | Status: *{status}* | Ordered: {created}\n"
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