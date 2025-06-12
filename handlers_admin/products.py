from telegram import Update, InputFile
from telegram.ext import ContextTypes, ConversationHandler
from models import load_json, save_json
import uuid

ADD_LOCATION_WAIT_PRODUCT, ADD_LOCATION_WAIT_PHOTO = range(2)
# --- Product Management ---

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("Usage: /addproduct <name> <price> <stock> <category>")
        return
    name, price, stock, category = args[0], args[1], args[2], args[3]
    products = load_json("products.json", [])
    new_product = {
        "id": str(uuid.uuid4()),
        "name": name,
        "price": int(price),
        "stock": int(stock),
        "category": category,
        "image": "",  # You can add image upload logic separately
        "description": ""
    }
    products.append(new_product)
    save_json("products.json", products)
    await update.message.reply_text(f"✅ Product '{name}' added.")

async def remove_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /removeproduct <product_id>")
        return
    product_id = args[0]
    products = load_json("products.json", [])
    new_products = [p for p in products if p.get("id") != product_id]
    if len(new_products) == len(products):
        await update.message.reply_text("Product not found.")
        return
    save_json("products.json", new_products)
    await update.message.reply_text(f"Product {product_id} removed.")

async def edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Usage: /editproduct <product_id> <field> <new_value>")
        return
    product_id, field, new_value = args[0], args[1], args[2]
    products = load_json("products.json", [])
    found = False
    for p in products:
        if p.get("id") == product_id:
            if field in p:
                if field in ["price", "stock"]:
                    p[field] = int(new_value)
                else:
                    p[field] = new_value
                found = True
    if found:
        save_json("products.json", products)
        await update.message.reply_text(f"Product {product_id} updated: {field} = {new_value}")
    else:
        await update.message.reply_text("Product not found or invalid field.")

async def product_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = load_json("products.json", [])
    if not products:
        await update.message.reply_text("No products found.")
        return
    msg = "🛒 *Product List:*\n"
    for p in products:
        msg += (
            f"- ID: `{p.get('id', 'N/A')}` | {p.get('name', '')} | "
            f"Price: {p.get('price', '')} | Stock: {p.get('stock', '')} | "
            f"Category: {p.get('category', '')}\n"
        )
    await update.message.reply_text(msg, parse_mode="Markdown")

# --- Stock Location Management (if you use it) ---

ADD_LOCATION_WAIT_PHOTO = 1

async def add_location_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send the *product ID* for which you want to set the pickup location.", parse_mode="Markdown")
    return ADD_LOCATION_WAIT_PRODUCT

async def add_location_set_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This expects the admin to send the product ID as text
    context.user_data["add_location_product_id"] = update.message.text.strip()
    await update.message.reply_text("Now send the *location photo* with a caption (pickup info).", parse_mode="Markdown")
    return ADD_LOCATION_WAIT_PHOTO

async def add_location_receive_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_location_product_id"] = update.message.text.strip()
    await update.message.reply_text("Now send the *location photo* with a caption (pickup info).", parse_mode="Markdown")
    return ADD_LOCATION_WAIT_PHOTO

async def add_location_receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = context.user_data.get("add_location_product_id")
    if not product_id:
        await update.message.reply_text("No product ID found. Please start again.")
        return ConversationHandler.END
    products = load_json("products.json", [])
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        await update.message.reply_text("Product not found. Please try again.")
        return ConversationHandler.END
    photo = update.message.photo[-1]
    product["location_image"] = photo.file_id
    product["location_caption"] = update.message.caption
    save_json("products.json", products)
    await update.message.reply_text(f"Location photo and caption set for *{product['name']}*.", parse_mode="Markdown")
    return ConversationHandler.END