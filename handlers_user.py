from config import ADMIN_IDS, DEFAULT_START_COINS, main_menu
from models import load_json, save_json
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackContext
from datetime import datetime
import uuid
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import ReplyKeyboardMarkup
from telegram.ext import ConversationHandler

# Conversation states
ORDER_QUANTITY, ORDER_CONFIRM = range(2)

# ---- USER MENU HANDLER ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    balances = load_json("balances.json", {})
    if user_id not in balances:
        balances[user_id] = DEFAULT_START_COINS
        save_json("balances.json", balances)
    reply_markup = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    await update.message.reply_text(
        f"Welcome to the Shop Bot! 🛒\n\nChoose an option:\n"
        f"You have {balances[user_id]} coins.",
        reply_markup=reply_markup
    )
    first_joins = load_json("first_join.json", {})
    if user_id not in first_joins:
        from datetime import datetime
        first_joins[user_id] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        save_json("first_join.json", first_joins)


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.message.from_user.id)
    if text == "🛒 View Products":
        categories = ["Cox", "Klein", "Shrooms"]
        keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat_{cat}")] for cat in categories]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Select a category:", reply_markup=reply_markup)
        return
        
    elif text == "📦 My Orders":
        keyboard = [
        [
            InlineKeyboardButton("Pending", callback_data="filter_orders_pending"),
            InlineKeyboardButton("Completed", callback_data="filter_orders_completed"),
            InlineKeyboardButton("Cancelled", callback_data="filter_orders_cancelled")
        ],
        [InlineKeyboardButton("All", callback_data="filter_orders_all")]
    ]
        await update.message.reply_text("Filter your orders:", reply_markup=InlineKeyboardMarkup(keyboard))


    elif text == "💰 My Balance":
        balances = load_json("balances.json", {})
        balance = balances.get(user_id, DEFAULT_START_COINS)
        await update.message.reply_text(f"💰 You have {balance} coins.")
    elif text == "ℹ️ Help":
        await update.message.reply_text(
            "Welcome to the Shop Bot! Use the menu to view products, check your orders, balance, or get help."
        )
    elif text == "👤 Profile":
        await profile_cmd(update, context)
    elif text == "💳 Deposit LTC":  
        await deposit_ltc(update, context)

async def handle_back_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from config import main_menu  # Import here if not already at top

    if query.data == "back_to_categories":
        # Show categories menu (reuse your categories_cmd)
        await categories_cmd(update, context)
        return ConversationHandler.END

    elif query.data == "back_to_menu":
        reply_markup = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
        await query.message.reply_text("Main Menu:", reply_markup=reply_markup)
        return ConversationHandler.END



# ---- PRODUCT ORDER CONVERSATION ----
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    current_products = load_json("products.json", [])
    product_idx = int(query.data.split("_")[1])
    product = current_products[product_idx]
    if product.get("stock", 0) < 1:
        await query.message.reply_text(
            f"Sorry, {product['name']} is out of stock."
        )
        return ConversationHandler.END
    context.user_data["order_product"] = product
    context.user_data["order_idx"] = product_idx
    await query.message.reply_text(
        f"How many *{product['name']}* do you want to order?\n"
        f"Stock available: {product.get('stock', 0)}\n"
        f"Price per item: {product['price']} coins\n"
        "(Type a number, or /cancel to abort.)",
        parse_mode="Markdown"
    )
    return ORDER_QUANTITY


async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    balances = load_json("balances.json", {})
    orders = load_json("orders.json", {})
    joins = load_json("first_join.json", {})

    balance = balances.get(user_id, DEFAULT_START_COINS)
    order_count = len(orders.get(user_id, []))
    join_date = joins.get(user_id, "Unknown")

    msg = (
        f"👤 *Your Profile*\n"
        f"Name: {user.full_name}\n"
        f"Username: @{user.username or 'N/A'}\n"
        f"User ID: `{user.id}`\n"
        f"Balance: {balance} coins\n"
        f"Orders: {order_count}\n"
        f"Joined: {join_date}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")



async def receive_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit() or int(text) < 1:
        await update.message.reply_text("Please enter a valid positive number.")
        return ORDER_QUANTITY
    user_id = str(update.message.from_user.id)
    qty = int(text)
    product = context.user_data.get("order_product")
    product_idx = context.user_data.get("order_idx")
    products = load_json("products.json", [])
    if product is None or product_idx is None or product_idx >= len(products):
        await update.message.reply_text("Something went wrong. Try again.")
        return ConversationHandler.END
    current_stock = products[product_idx].get("stock", 0)
    price = products[product_idx].get("price", 0)
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
    product_idx = context.user_data.get("order_idx")
    qty = context.user_data.get("order_quantity", 1)
    products = load_json("products.json", [])
    if product_idx is None or product_idx < 0 or product_idx >= len(products):
        await query.message.reply_text("Product not found or has been removed.")
        return ConversationHandler.END
    current_stock = products[product_idx].get("stock", 0)
    price = products[product_idx].get("price", 0)
    balances = load_json("balances.json", {})
    balance = balances.get(user_id, DEFAULT_START_COINS)
    if qty > current_stock:
        await query.message.reply_text(f"Sorry, not enough stock left. Only {current_stock} available.")
        return ConversationHandler.END
    if price * qty > balance:
        await query.message.reply_text(f"Not enough coins! You need {price * qty}, but have {balance}.")
        return ConversationHandler.END
    products[product_idx]["stock"] -= qty
    save_json("products.json", products)
    low_stock_threshold = 2
    new_stock = products[product_idx]["stock"]
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
    location_image = product.get("location_image")
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
                    f"Status: pending"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass
    location_image = product.get("location_image")
    location_caption = product.get("location_caption", "Here is your pickup location.")
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
    # It's fine if this gets called for normal menu messages.
    # Optionally, don't send "Order cancelled" if not actually ordering
    return ConversationHandler.END


# ---- PRODUCT DETAILS ----
async def product_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_idx = int(query.data.split("_")[1])
    products = load_json("products.json", [])
    if product_idx < 0 or product_idx >= len(products):
        await query.message.reply_text("Product not found.")
        return
    product = products[product_idx]
    description = product.get("description", "No description provided.")
    msg = (
        f"*{product['name']}*\n"
        f"_{description}_\n\n"
        f"Price: {product['price']} coins\n"
        f"Stock: {product['stock']}\n"
        f"Category: {product.get('category', 'General')}"
    )
    try:
        await query.message.reply_photo(
            photo=product.get("image", ""),
            caption=msg,
            parse_mode="Markdown"
        )
    except Exception as e:
        await query.message.reply_text(msg, parse_mode="Markdown")

    # Add navigation buttons here
    keyboard = [
        [InlineKeyboardButton("⬅️ Back to Categories", callback_data="back_to_categories")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
    ]
    await query.message.reply_text(
        "What would you like to do next?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---- DEPOSIT COMMANDS ----
async def deposit_ltc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    # Load deposit addresses
    deposit_addresses = load_json("deposit_addresses.json", {})
    
    if user_id not in deposit_addresses:
        # Generate a new deposit address for the user
        # In a real implementation, you would generate a new address using a Litecoin wallet API
        # For now, we'll use a placeholder address
        deposit_addresses[user_id] = "LTC1234567890abcdef"  # Replace with actual address generation
        save_json("deposit_addresses.json", deposit_addresses)
    
    address = deposit_addresses[user_id]
    keyboard = [
        [InlineKeyboardButton("Check Balance", callback_data=f"check_balance_{user_id}")],
        [InlineKeyboardButton("💸 Simulate Deposit (+100 coins)", callback_data="simulate_deposit")],
        [InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]
    ]
    

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Litecoin Deposit Address:\n\n{address}\n\n"
        "Send your Litecoins to this address to increase your balance.\n"
        "Your balance will be updated automatically once the transaction is confirmed.\n"
        "Note: Please do not send any other cryptocurrencies to this address.",
        reply_markup=reply_markup
    )

async def simulate_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    balances = load_json("balances.json", {})
    balances[user_id] = balances.get(user_id, 0) + 100
    save_json("balances.json", balances)
    await query.message.reply_text("✅ 100 coins have been added to your balance for testing!")

async def check_balance(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.data.split("_")[1]
    
    # In a real implementation, you would check the actual balance using a Litecoin wallet API
    # For now, we'll just show a placeholder message
    await query.message.reply_text(
        "Your current balance will be updated automatically once your deposit is confirmed."
    )

# ---- BALANCE COMMANDS ----
async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    balances = load_json("balances.json", {})
    balance = balances.get(user_id, DEFAULT_START_COINS)
    await update.message.reply_text(f"💰 You have {balance} coins.")

async def categories_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_json("products.json", [])
    categories = sorted(set(p.get("category", "General") for p in products))
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat_{cat}")] for cat in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Support both /categories (message) and callback (button)
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("Select a category:", reply_markup=reply_markup)
    elif hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.message.reply_text("Select a category:", reply_markup=reply_markup)

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data[4:]
    products = load_json("products.json", [])
    filtered = [p for p in products if p.get("category", "General") == cat]
    if not filtered:
        await query.message.reply_text("No products in this category.")
        return
    for product in filtered:
        idx = products.index(product)
        
    products = load_json("products.json", [])
    filtered = [p for p in products if p.get("category", "General") == cat]
    if not filtered:
        await query.message.reply_text("No products in this category.")
        return
    for product in filtered:
        idx = products.index(product)  # This gets the index in the full products list!
        stock = product.get("stock", 0)
        price = product.get("price", 0)
        caption = (
            f"*{product['name']}*\n"
            f"Price: {price} coins\n"
            f"Stock: {stock}\n"
            f"Category: {cat}"
    )
        keyboard = [
        [InlineKeyboardButton(f"Order {product['name']}", callback_data=f"order_{idx}")],
        [InlineKeyboardButton("ℹ️ Details", callback_data=f"details_{idx}")]
    ]
        try:
            await query.message.reply_photo(
            photo=product["image"],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        except Exception as e:
            await query.message.reply_text(
            f"Could not display product {product['name']}: {e}"
        )
            # At the end of show_category, after showing all products:
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back to Categories", callback_data="back_to_categories")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
        ])
        await update.callback_query.message.reply_text(
            "What would you like to do next?",
            reply_markup=back_keyboard
)
      

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /search <keyword>")
        return
    keyword = " ".join(context.args).lower()
    products = load_json("products.json", [])
    found = [p for p in products if keyword in p["name"].lower() or keyword in p.get("description", "").lower()]
    if not found:
        await update.message.reply_text("No products found for your search.")
        return
    for idx, product in enumerate(found):
        stock = product.get("stock", 0)
        price = product.get("price", 0)
        caption = (
            f"*{product['name']}*\n"
            f"Price: {price} coins\n"
            f"Stock: {stock}\n"
            f"Category: {product.get('category', 'General')}"
        )
        keyboard = [
            [InlineKeyboardButton(f"Order {product['name']}", callback_data=f"order_{idx}")],
            [InlineKeyboardButton("ℹ️ Details", callback_data=f"details_{idx}")]
        ]
        try:
            await update.message.reply_photo(
                photo=product["image"],
                caption=caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            await update.message.reply_text(
                f"Could not display product {product['name']}: {e}"
            )

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
        [InlineKeyboardButton("All", callback_data="filter_orders_all")]
    ]
    await query.message.reply_text("Filter your orders:", reply_markup=InlineKeyboardMarkup(keyboard))
