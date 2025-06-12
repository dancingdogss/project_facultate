from telegram import Update, InputFile
from telegram.ext import ContextTypes
from models import load_json, save_json

async def set_order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /setorderstatus <order_id> <status>")
        return
    order_id, new_status = args[0], args[1]
    orders = load_json("orders.json", {})
    found = False
    for user_id, user_orders in orders.items():
        for order in user_orders:
            if order.get("order_id") == order_id:
                if order.get("order_status") == "completed":
                    await update.message.reply_text("Cannot change status of a completed order.")
                    return
                # Refund if cancelling a pending order
                if order.get("order_status") == "pending" and new_status == "cancelled":
                    balances = load_json("balances.json", {})
                    products = load_json("products.json", [])
                    price = 0
                    for p in products:
                        if p["name"] == order["name"]:
                            price = p["price"]
                            break
                    refund = price * order["quantity"]
                    balances[user_id] = balances.get(user_id, 0) + refund
                    save_json("balances.json", balances)
                    await update.message.reply_text(f"User refunded {refund} coins for cancelled order.")
                # Send location if marking as completed and product has location_image
                if order.get("order_status") == "pending" and new_status == "completed":
                    products = load_json("products.json", [])
                    product = next((p for p in products if p["name"] == order["name"]), None)
                    if product and product.get("location_image"):
                        try:
                            await context.bot.send_photo(
                                chat_id=user_id,
                                photo=product["location_image"],
                                caption=product.get("location_caption", "Here is your pickup location."),
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            await update.message.reply_text(f"Could not send location photo to user: {e}")
                order["order_status"] = new_status
                found = True
    if found:
        save_json("orders.json", orders)
        await update.message.reply_text(f"Order {order_id} status updated to {new_status}.")
    else:
        await update.message.reply_text("Order not found.")
async def all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orders = load_json("orders.json", {})
    msg = "📦 *All Orders:*\n"
    count = 0
    for user_id, user_orders in orders.items():
        for order in user_orders:
            msg += (
                f"- ID: `{order.get('order_id', 'N/A')}` | {order.get('name', '')} x{order.get('quantity', '')} | "
                f"User: `{user_id}` | Status: *{order.get('order_status', 'pending')}* | {order.get('created_at', '')}\n"
            )
            count += 1
            if count >= 30:
                break
        if count >= 30:
            break
    if count == 0:
        msg += "No orders found."
    await update.message.reply_text(msg, parse_mode="Markdown")

async def export_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import csv
    from io import StringIO
    orders = load_json("orders.json", {})
    csvfile = StringIO()
    writer = csv.writer(csvfile)
    writer.writerow(['User ID', 'Order ID', 'Product', 'Quantity', 'Status', 'Created At'])
    for user_id, user_orders in orders.items():
        for order in user_orders:
            writer.writerow([
                user_id,
                order.get('order_id', ''),
                order.get('name', ''),
                order.get('quantity', ''),
                order.get('order_status', ''),
                order.get('created_at', '')
            ])
    csvfile.seek(0)
    await update.message.reply_document(
        document=csvfile.getvalue().encode(),
        filename="orders_export.csv",
        caption="🗂️ All orders exported as CSV."
    )

async def deliveries_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deliveries = load_json("deliveries.json", [])
    if not deliveries:
        await update.message.reply_text("No deliveries found.")
        return
    msg = "🚚 *Deliveries:*\n"
    for d in deliveries:
        msg += f"- ID: `{d.get('delivery_id', 'N/A')}` | {d.get('info', '')}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def removedelivery_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /removedelivery <delivery_id>")
        return
    delivery_id = args[0]
    deliveries = load_json("deliveries.json", [])
    new_deliveries = [d for d in deliveries if d.get('delivery_id') != delivery_id]
    if len(new_deliveries) == len(deliveries):
        await update.message.reply_text("Delivery not found.")
        return
    save_json("deliveries.json", new_deliveries)
    await update.message.reply_text(f"Delivery {delivery_id} removed.")

async def export_deliveries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import csv
    from io import StringIO
    deliveries = load_json("deliveries.json", [])
    csvfile = StringIO()
    writer = csv.writer(csvfile)
    writer.writerow(['Delivery ID', 'Info'])
    for d in deliveries:
        writer.writerow([
            d.get('delivery_id', ''),
            d.get('info', '')
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
    orders = load_json("orders.json", {})
    for user_id, user_orders in orders.items():
        for order in user_orders:
            if order.get("order_id") == order_id:
                msg = (
                    f"Order found:\n"
                    f"User: `{user_id}`\n"
                    f"Product: {order.get('name', '')}\n"
                    f"Quantity: {order.get('quantity', '')}\n"
                    f"Status: {order.get('order_status', 'pending')}\n"
                    f"Created: {order.get('created_at', '')}"
                )
                await update.message.reply_text(msg, parse_mode="Markdown")
                return
    await update.message.reply_text("Order not found.")