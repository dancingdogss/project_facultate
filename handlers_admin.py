import csv
import os
import json
from datetime import datetime
from io import StringIO
from config import ADMIN_IDS, DEFAULT_START_COINS
from models import load_json, save_json
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext, ConversationHandler

ADD_LOCATION_WAIT_PHOTO = 200  # Use a unique state number
# ---- ADMIN ORDERS ----



def log_delivery(user_id, order, product):
    deliveries_file = "deliveries.json"
    if os.path.exists(deliveries_file):
        with open(deliveries_file, "r", encoding="utf-8") as f:
            deliveries = json.load(f)
    else:
        deliveries = []
    deliveries.append({
        "user_id": user_id,
        "order": order,
        "product_name": product.get("name"),
        "location_image": product.get("location_image"),
        "location_caption": product.get("location_caption"),
        "stock_id": order.get("order_id", "N/A"),
        "delivered_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    })
    with open(deliveries_file, "w", encoding="utf-8") as f:
        json.dump(deliveries, f, ensure_ascii=False, indent=2)



async def deliveries_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return
    deliveries_file = "deliveries.json"
    if not os.path.exists(deliveries_file):
        await update.message.reply_text("No deliveries logged yet.")
        return
    with open(deliveries_file, "r", encoding="utf-8") as f:
        deliveries = json.load(f)
    if not deliveries:
        await update.message.reply_text("No deliveries logged yet.")
        return
    msg = "📦 *Completed Deliveries:*\n"
    for d in deliveries[-20:]:  # Show last 20 deliveries
        msg += (
            f"- User: {d['user_id']}\n"
            f"  Product: {d['product_name']}\n"
            f"  Stock ID: `{d.get('stock_id', 'N/A')}`\n"
            f"  Delivered: {d['delivered_at']}\n"
            f"  Caption: {d.get('location_caption', '')}\n\n"
        )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def removedelivery_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /removedelivery <stock_id>")
        return
    stock_id = context.args[0]
    deliveries_file = "deliveries.json"
    if not os.path.exists(deliveries_file):
        await update.message.reply_text("No deliveries logged yet.")
        return
    with open(deliveries_file, "r", encoding="utf-8") as f:
        deliveries = json.load(f)
    new_deliveries = [d for d in deliveries if d.get("stock_id") != stock_id]
    if len(new_deliveries) == len(deliveries):
        await update.message.reply_text("No delivery found with that Stock ID.")
        return
    with open(deliveries_file, "w", encoding="utf-8") as f:
        json.dump(new_deliveries, f, ensure_ascii=False, indent=2)
    await update.message.reply_text(f"✅ Delivery with Stock ID `{stock_id}` removed.", parse_mode="Markdown")

async def export_deliveries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return
    deliveries_file = "deliveries.json"
    if not os.path.exists(deliveries_file):
        await update.message.reply_text("No deliveries logged yet.")
        return
    with open(deliveries_file, "r", encoding="utf-8") as f:
        deliveries = json.load(f)
    if not deliveries:
        await update.message.reply_text("No deliveries logged yet.")
        return
    csvfile = StringIO()
    writer = csv.writer(csvfile)
    writer.writerow(['User ID', 'Product Name', 'Stock ID', 'Delivered At', 'Location Caption'])
    for d in deliveries:
        writer.writerow([
            d.get('user_id', ''),
            d.get('product_name', ''),
            d.get('stock_id', ''),
            d.get('delivered_at', ''),
            d.get('location_caption', '')
        ])
    csvfile.seek(0)
    await update.message.reply_document(
        document=csvfile.getvalue().encode(),
        filename="deliveries_export.csv",
        caption="🗂️ All deliveries exported as CSV."
    )
    
async def confirm_admin_order(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    orders = load_json("orders.json", {})
    user_id = query.data.split("_")[1]
    if user_id not in orders:
        await query.message.reply_text("Order not found.")
        return
    user_orders = orders[user_id]
    del orders[user_id]
    save_json("orders.json", orders)
    msg = f"✅ Order for user {user_id} confirmed and deleted:\n"
    for product in user_orders:
        if isinstance(product, dict):
            msg += f"  - {product['name']} x{product.get('quantity', 1)}\n"
        else:
            msg += f"  - {product}\n"
    await query.message.reply_text(msg)

async def cancel_admin_order(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.data.split("_")[1]
    orders = load_json("orders.json", {})
    if user_id not in orders:
        await query.message.reply_text("Order not found.")
        return
    del orders[user_id]
    save_json("orders.json", orders)
    await query.message.reply_text(f"Order for user {user_id} cancelled and deleted.")







# ---- ADMIN COMMANDS ----

async def add_location_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return ConversationHandler.END
    await update.message.reply_text(
        "Please send the *product name* for which you want to set the stock location.",
        parse_mode="Markdown"
    )
    return ADD_LOCATION_WAIT_PHOTO

async def add_location_receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return ConversationHandler.END

    if not update.message.photo or not update.message.caption:
        await update.message.reply_text("Please send a photo with a caption (location info).")
        return ADD_LOCATION_WAIT_PHOTO

    # The admin should have sent the product name as the previous message
    product_name = context.user_data.get("add_location_product")
    if not product_name:
        # Try to get from reply-to or ask again
        await update.message.reply_text("Please first send the product name as a message.")
        return ADD_LOCATION_WAIT_PHOTO

    products = load_json("products.json", [])
    for p in products:
        if p["name"].lower() == product_name.lower():
            p["location_image"] = update.message.photo[-1].file_id
            p["location_caption"] = update.message.caption
            save_json("products.json", products)
            await update.message.reply_text(f"Location photo and caption set for {product_name}.")
            return ConversationHandler.END

    await update.message.reply_text("Product not found. Please try again.")
    return ConversationHandler.END

# Helper to set product name before photo
async def add_location_set_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_location_product"] = update.message.text.strip()
    await update.message.reply_text("Now send the location photo with a caption (location info).")
    return ADD_LOCATION_WAIT_PHOTO

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied. You are not an admin.")
        return
    args = " ".join(context.args)
    parts = [part.strip() for part in args.split("|", maxsplit=5)]
    if len(parts) < 4:
        await update.message.reply_text(
            "Invalid format. Use:\n"
            "/addproduct Name | Price | FileID_or_ImageURL | Stock | [Description] | [Category]"
        )
        return
    name, price, image, stock = parts[:4]
    description = parts[4] if len(parts) >= 5 else ""
    category = parts[5] if len(parts) == 6 else "General"
    try:
        price = int(price)
        stock = int(stock)
    except:
        await update.message.reply_text("Price and Stock must be integers.")
        return
    products = load_json("products.json", [])
    products.append({
        "name": name,
        "price": price,
        "image": image,
        "stock": stock,
        "description": description,
        "category": category
    })
    save_json("products.json", products)
    await update.message.reply_text(
        f"✅ Product added:\n*{name}* ({price} coins)\nStock: {stock}\nCategory: {category}\nDescription: {description or '(none)'}",
        parse_mode="Markdown"
    )

async def remove_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied. You are not an admin.")
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "Usage: /removeproduct <index>\n\nExample: /removeproduct 0\n\nIndexes start at 0. Use /productlist to see indexes."
        )
        return
    idx = int(args[0])
    current_products = load_json("products.json", [])
    if idx < 0 or idx >= len(current_products):
        await update.message.reply_text("Invalid index. Use /productlist to see available indexes.")
        return
    removed = current_products.pop(idx)
    save_json("products.json", current_products)
    await update.message.reply_text(f"✅ Removed product: *{removed['name']}*", parse_mode="Markdown")

async def product_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied. You are not an admin.")
        return
    current_products = load_json("products.json", [])
    if not current_products:
        await update.message.reply_text("No products available.")
        return
    msg = "🛍️ *Product List:*\n"
    for idx, product in enumerate(current_products):
        msg += f"{idx}. {product['name']} ({product['price']} coins) [Stock: {product.get('stock', 0)}]\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def export_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied. You are not an admin.")
        return
    orders = load_json("orders.json", {})
    if not orders:
        await update.message.reply_text("No orders found.")
        return
    csvfile = StringIO()
    writer = csv.writer(csvfile)
    writer.writerow(['User ID', 'Product Name', 'Quantity'])
    for user, order_list in orders.items():
        for product in order_list:
            if isinstance(product, dict):
                writer.writerow([user, product['name'], product.get('quantity', 1)])
            else:
                writer.writerow([user, product, 1])
    csvfile.seek(0)
    await update.message.reply_document(
        document=csvfile.getvalue().encode(),
        filename="orders_export.csv",
        caption="🗂️ All shop orders exported as CSV."
    )

async def all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied. You are not an admin.")
        return
    orders = load_json("orders.json", {})
    if not orders:
        await update.message.reply_text("No orders yet.")
        return

    # Group orders by status
    grouped = {"pending": [], "completed": [], "cancelled": [], "other": []}
    for uid, items in orders.items():
        for idx, o in enumerate(items):
            if isinstance(o, dict):
                status = o.get("order_status", "pending").lower()
                entry = {
                    "user": uid,
                    "idx": idx,
                    "order_id": o.get("order_id", "N/A"),
                    "name": o.get("name", "N/A"),
                    "qty": o.get("quantity", 1),
                    "date": o.get("created_at", "N/A"),
                }
                if status in grouped:
                    grouped[status].append(entry)
                else:
                    grouped["other"].append(entry)

    msg = "🗒️ *All Orders Overview:*\n\n"
    for status in ["pending", "completed", "cancelled", "other"]:
        if grouped[status]:
            msg += f"━━━━━━━━━━━━━━━\n*{status.capitalize()} Orders:*\n"
            for entry in grouped[status]:
                msg += (
                    f"• *Order ID:* `{entry['order_id']}`\n"
                    f"  *Product:* {entry['name']} x{entry['qty']}\n"
                    f"  *User:* `{entry['user']}`\n"
                    f"  *Date:* {entry['date']}\n\n"
                )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied. You are not an admin.")
        return
    args = " ".join(context.args)
    # Allow spaces and bars in description, so split max 2 times
    parts = [part.strip() for part in args.split("|", maxsplit=2)]
    if len(parts) != 3:
        await update.message.reply_text(
            "Invalid format. Use:\n"
            "/editproduct <index> | <field> | <new_value>\n"
            "Fields: name, price, image, stock, description"
        )
        return
    idx_str, field, value = parts
    valid_fields = ["name", "price", "image", "stock", "description"]
    try:
        idx = int(idx_str)
        if field not in valid_fields:
            raise Exception("Invalid field")
    except Exception:
        await update.message.reply_text(
            "Invalid format or field. Fields: name, price, image, stock, description."
        )
        return
    products = load_json("products.json", [])
    if idx < 0 or idx >= len(products):
        await update.message.reply_text("Invalid index. Use /productlist to see indexes.")
        return
    old_value = products[idx].get(field, "")
    if field == "stock" or field == "price":
        try:
            value = int(value)
        except:
            await update.message.reply_text(f"{field.capitalize()} must be an integer.")
            return
    products[idx][field] = value
    save_json("products.json", products)
    await update.message.reply_text(
        f"✅ Product updated:\n*{field}* changed from {old_value} to {value}",
        parse_mode="Markdown"
    )

async def set_order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied. You are not an admin.")
        return
    args = context.args
    if len(args) != 3:
        await update.message.reply_text("Usage: /setorderstatus <user_id> <order_id> <status>")
        return
    target_id, order_id, status = args
    orders = load_json("orders.json", {})
    if target_id not in orders:
        await update.message.reply_text("User has no orders.")
        return
    
    # Find order by order_id
    order = None
    for o in orders[target_id]:
        if isinstance(o, dict) and o.get("order_id") == order_id:
            order = o
            break
    if not order:
        await update.message.reply_text("Order ID not found for this user.")
        return

    old_status = order.get("order_status", "pending")
    if old_status == "completed":
        await update.message.reply_text("❌ This order is already completed and cannot be changed.")
        return
    
    order["order_status"] = status
    save_json("orders.json", orders)

    # Notify user for completed or cancelled
    if status.lower() == "completed":
        try:
            products = load_json("products.json", [])
            product = next((p for p in products if p["name"] == order["name"]), None)
            if product and product.get("location_image"):
                await context.bot.send_photo(
                    chat_id=int(target_id),
                    photo=product["location_image"],
                    caption=product.get("location_caption", "Your pickup location."),
                    parse_mode="Markdown"
                )
            else:
                await context.bot.send_message(
                    chat_id=int(target_id),
                    text=f"✅ Your order '{order['name']}' (x{order['quantity']}) is *completed*!",
                    parse_mode="Markdown"
                )
            # Log the delivery
            log_delivery(target_id, order, product)
        except Exception:
            pass
    elif status.lower() == "cancelled":
        try:
            await context.bot.send_message(
                chat_id=int(target_id),
                text=f"❌ Your order '{order['name']}' (x{order['quantity']}) has been *cancelled*. If you have questions, contact support.",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    await update.message.reply_text(f"Order status updated from {old_status} to {status}.")

    # --- Restock if cancelled ---
    if status.lower() == "cancelled" and old_status != "cancelled":
        products = load_json("products.json", [])
        for p in products:
            if p["name"] == order["name"]:
                p["stock"] = p.get("stock", 0) + order.get("quantity", 1)
                break
        save_json("products.json", products)
    # --- End restock ---
        # --- Restock if cancelled ---
    if status.lower() == "cancelled" and old_status != "cancelled":
        products = load_json("products.json", [])
        for p in products:
            if p["name"] == order["name"]:
                p["stock"] = p.get("stock", 0) + order.get("quantity", 1)
                break
        save_json("products.json", products)
        # --- Refund coins to user ---
        balances = load_json("balances.json", {})
        user_balance = balances.get(target_id, DEFAULT_START_COINS)
        # Find product price (from updated products list)
        price = next((p["price"] for p in products if p["name"] == order["name"]), 0)
        refund = order.get("quantity", 1) * price
        balances[target_id] = user_balance + refund
        save_json("balances.json", balances)
        await update.message.reply_text(f"Refunded {refund} coins to user {target_id}.")
    # --- End restock & refund ---
    await update.message.reply_text(f"Order status updated from {old_status} to {status}.")
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=f"Your order '{order['name']}' (x{order['quantity']}) status changed to: *{status}*",
            parse_mode="Markdown"
        )
    except Exception:
        pass


async def findorder_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /findorder <order_id>")
        return
    search_id = context.args[0]
    orders = load_json("orders.json", {})
    for uid, items in orders.items():
        for o in items:
            if isinstance(o, dict) and o.get("order_id") == search_id:
                msg = (
                    f"Order found:\n"
                    f"User: {uid}\n"
                    f"Product: {o['name']}\n"
                    f"Quantity: {o['quantity']}\n"
                    f"Status: {o['order_status']}\n"
                    f"Ordered: {o['created_at']}\n"
                )
                await update.message.reply_text(msg)
                return
    await update.message.reply_text("Order ID not found.")

async def addcoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /addcoins <user_id> <amount>")
        return
    target_id = str(args[0])
    try:
        amt = int(args[1])
    except:
        await update.message.reply_text("Amount must be an integer.")
        return
    balances = load_json("balances.json", {})
    balances[target_id] = balances.get(target_id, DEFAULT_START_COINS) + amt
    save_json("balances.json", balances)
    await update.message.reply_text(f"✅ {amt} coins added to user {target_id}.")

async def setcoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /setcoins <user_id> <amount>")
        return
    target_id = str(args[0])
    try:
        amt = int(args[1])
    except:
        await update.message.reply_text("Amount must be an integer.")
        return
    balances = load_json("balances.json", {})
    balances[target_id] = amt
    save_json("balances.json", balances)
    await update.message.reply_text(f"✅ User {target_id} balance set to {amt} coins.")

async def topusers_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return
    balances = load_json("balances.json", {})
    top = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]
    msg = "🏆 *Top Users by Coins:*\n"
    for i, (uid, bal) in enumerate(top, 1):
        msg += f"{i}. {uid}: {bal} coins\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def profits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return
    profits = load_json("profits.json", [])
    if not profits:
        await update.message.reply_text("No profits logged yet.")
        return

    total_coins = sum(p["amount"] for p in profits)
    total_sales = len(profits)
    # Top products by coins earned
    product_stats = {}
    for p in profits:
        name = p["product"]
        product_stats.setdefault(name, 0)
        product_stats[name] += p["amount"]
    top_products = sorted(product_stats.items(), key=lambda x: x[1], reverse=True)[:3]

    msg = (
        f"💰 *Profit Analytics*\n"
        f"Total coins earned: *{total_coins}*\n"
        f"Total sales: *{total_sales}*\n\n"
        f"🏆 *Top Products:*\n"
    )
    for i, (prod, coins) in enumerate(top_products, 1):
        msg += f"{i}. {prod}: {coins} coins\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def dashboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return
    orders = load_json("orders.json", {})
    products = load_json("products.json", [])
    balances = load_json("balances.json", {})
    # Total sales and orders
    total_orders = sum(len(v) for v in orders.values())
    total_sales = 0
    product_sales = {}
    for user_orders in orders.values():
        for o in user_orders:
            if isinstance(o, dict):
                total_sales += o.get("quantity", 1) * next((p["price"] for p in products if p["name"] == o["name"]), 0)
                product_sales[o["name"]] = product_sales.get(o["name"], 0) + o.get("quantity", 1)
    # Top-selling products
    top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
    # Low-stock products
    low_stock = [f"{p['name']} ({p.get('stock', 0)})" for p in products if p.get("stock", 0) <= 2]
    # User count
    user_count = len(balances)
    msg = (
        f"📊 *Admin Dashboard*\n"
        f"Total users: {user_count}\n"
        f"Total orders: {total_orders}\n"
        f"Total sales: {total_sales} coins\n"
        f"\nTop products:\n"
    )
    for name, qty in top_products:
        msg += f"  - {name}: {qty} sold\n"
    msg += "\nLow stock:\n"
    msg += "\n".join(low_stock) if low_stock else "  - None"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def export_profits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return
    profits = load_json("profits.json", [])
    if not profits:
        await update.message.reply_text("No profits logged yet.")
        return
    csvfile = StringIO()
    writer = csv.writer(csvfile)
    writer.writerow(['User ID', 'Product', 'Quantity', 'Amount', 'Stock ID', 'Datetime'])
    for p in profits:
        writer.writerow([
            p.get('user_id', ''),
            p.get('product', ''),
            p.get('quantity', ''),
            p.get('amount', ''),
            p.get('stock_id', ''),
            p.get('datetime', '')
        ])
    csvfile.seek(0)
    await update.message.reply_document(
        document=csvfile.getvalue().encode(),
        filename="profits_export.csv",
        caption="🗂️ All profits exported as CSV."
    )

async def profits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return
    profits = load_json("profits.json", [])
    if not profits:
        await update.message.reply_text("No profits logged yet.")
        return
    msg = "💰 *Recent Profits:*\n"
    for p in profits[-20:]:
        msg += (
            f"- {p['datetime']}: {p['product']} x{p['quantity']} | "
            f"StockID: `{p['stock_id']}` | +{p['amount']} coins\n"
        )
    await update.message.reply_text(msg, parse_mode="Markdown")

