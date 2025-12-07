from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from handlers_admin.auth import require_admin_auth
from db import SessionLocal
from utils.db_utils import get_all_products

@require_admin_auth
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main admin panel with interactive buttons"""
    keyboard = [
        [InlineKeyboardButton("📦 Product Management", callback_data="admin_products"),
         InlineKeyboardButton("📋 Order Management", callback_data="admin_orders")],
        [InlineKeyboardButton("📸 Photo Management", callback_data="admin_photos"),
         InlineKeyboardButton("💰 User Management", callback_data="admin_users")],
        [InlineKeyboardButton("📊 Analytics", callback_data="admin_analytics"),
         InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")]
    ]
    
    text = (
        "🛠️ **Admin Control Panel**\n\n"
        "Choose a section to manage:\n"
        "📦 Products - Add, edit, remove products\n"
        "📋 Orders - View and manage orders\n"
        "📸 Photos - Manage product and location photos\n"
        "💰 Users - User balance and management\n"
        "📊 Analytics - View statistics and reports\n"
        "⚙️ Settings - Bot configuration"
    )
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

@require_admin_auth
async def product_management_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Product management interface"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("➕ Add New Product", callback_data="product_add"),
         InlineKeyboardButton("📝 Edit Product", callback_data="product_edit")],
        [InlineKeyboardButton("🗑️ Remove Product", callback_data="product_remove"),
         InlineKeyboardButton("📋 List All Products", callback_data="product_list")],
        [InlineKeyboardButton("📸 Add Product Photo", callback_data="product_photo"),
         InlineKeyboardButton("📦 Manage Stock", callback_data="product_stock")],
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
    ]
    
    text = (
        "📦 **Product Management**\n\n"
        "Choose an action:\n"
        "➕ Add new products to your shop\n"
        "📝 Edit existing product details\n"
        "🗑️ Remove products from shop\n"
        "📋 View all products and their info\n"
        "📸 Manage product presentation photos\n"
        "📦 Update stock levels"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

@require_admin_auth
async def photo_management_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Photo management interface"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📸 Add Location Photos", callback_data="photo_add_location"),
         InlineKeyboardButton("🖼️ View Location Photos", callback_data="photo_show_location")],
        [InlineKeyboardButton("🖼️ Add Product Photo", callback_data="photo_add_product"),
         InlineKeyboardButton("📁 Bulk Upload Photos", callback_data="photo_bulk_upload")],
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
    ]
    
    text = (
        "📸 **Photo Management**\n\n"
        "Manage your product and location photos:\n"
        "📸 Upload pickup location photos\n"
        "🖼️ View available location photos\n"
        "🖼️ Add product presentation photos\n"
        "📁 Bulk upload multiple photos"
    )
    
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

@require_admin_auth
async def select_product_for_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show product selection for photo operations"""
    query = update.callback_query
    await query.answer()
    
    action = query.data  # photo_add_location or photo_show_location
    context.user_data["photo_action"] = action
    
    async with SessionLocal() as session:
        products = await get_all_products(session)
        
        if not products:
            await query.edit_message_text(
                "❌ No products found. Please add products first.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Photo Management", callback_data="admin_photos")
                ]])
            )
            return
        
        keyboard = []
        for product in products:
            keyboard.append([InlineKeyboardButton(
                f"{product.name} ({product.category})", 
                callback_data=f"product_selected_{product.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Photo Management", callback_data="admin_photos")])
        
        action_text = "add location photos to" if action == "photo_add_location" else "view location photos for"
        text = f"📸 **Select Product**\n\nChoose which product you want to {action_text}:"
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

@require_admin_auth  
async def order_management_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Order management interface"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📋 View All Orders", callback_data="orders_view_all"),
         InlineKeyboardButton("🔍 Filter Orders", callback_data="orders_filter")],
        [InlineKeyboardButton("✅ Complete Orders", callback_data="orders_complete"),
         InlineKeyboardButton("❌ Cancel Orders", callback_data="orders_cancel")],
        [InlineKeyboardButton("📊 Export Orders", callback_data="orders_export"),
         InlineKeyboardButton("🚚 View Deliveries", callback_data="orders_deliveries")],
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
    ]
    
    text = (
        "📋 **Order Management**\n\n"
        "Manage customer orders:\n"
        "📋 View all pending/completed orders\n"
        "🔍 Filter orders by user, product, or date\n"
        "✅ Mark orders as completed\n"
        "❌ Cancel orders and refund users\n"
        "📊 Export order data to CSV\n"
        "🚚 View delivery history"
    )
    
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

@require_admin_auth
async def user_management_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User management interface"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💰 Add Coins", callback_data="user_add_coins"),
         InlineKeyboardButton("💳 Set Balance", callback_data="user_set_balance")],
        [InlineKeyboardButton("👥 Top Users", callback_data="user_top_users"),
         InlineKeyboardButton("📊 User Stats", callback_data="user_stats")],
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
    ]
    
    text = (
        "💰 **User Management**\n\n"
        "Manage user accounts and balances:\n"
        "💰 Add coins to user accounts\n"
        "💳 Set specific user balance\n"
        "👥 View top users by balance\n"
        "📊 View user statistics"
    )
    
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

@require_admin_auth
async def analytics_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analytics and reports interface"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📊 Dashboard", callback_data="analytics_dashboard"),
         InlineKeyboardButton("💹 Profits", callback_data="analytics_profits")],
        [InlineKeyboardButton("📈 Sales Report", callback_data="analytics_sales"),
         InlineKeyboardButton("🔄 Export Data", callback_data="analytics_export")],
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
    ]
    
    text = (
        "📊 **Analytics & Reports**\n\n"
        "View business insights:\n"
        "📊 Sales dashboard and overview\n"
        "💹 Profit tracking and analysis\n"
        "📈 Detailed sales reports\n"
        "🔄 Export data to CSV files"
    )
    
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Callback handler dispatcher
@require_admin_auth
async def admin_panel_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all admin panel callback queries"""
    query = update.callback_query
    data = query.data
    
    # Debug logging to confirm which handler is active
    try:
        from pathlib import Path as _P
        print(f"[INTERFACE] Admin callback received: {data} (from {str(_P(__file__).name)})")
    except Exception:
        print(f"[INTERFACE] Admin callback received: {data}")
    
    try:
        if data == "admin_main":
            # Show main admin panel
            keyboard = [
                [InlineKeyboardButton("📦 Product Management", callback_data="admin_products"),
                 InlineKeyboardButton("📋 Order Management", callback_data="admin_orders")],
                [InlineKeyboardButton("📸 Photo Management", callback_data="admin_photos"),
                 InlineKeyboardButton("💰 User Management", callback_data="admin_users")],
                [InlineKeyboardButton("📊 Analytics", callback_data="admin_analytics"),
                 InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")]
            ]
            
            text = (
                "🛠️ **Admin Control Panel**\n\n"
                "Choose a section to manage:\n"
                "📦 Products - Add, edit, remove products\n"
                "📋 Orders - View and manage orders\n"
                "📸 Photos - Manage product and location photos\n"
                "💰 Users - User balance and management\n"
                "📊 Analytics - View statistics and reports\n"
                "⚙️ Settings - Bot configuration"
            )
            
            await query.edit_message_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
        elif data == "admin_products":
            await product_management_panel(update, context)
        elif data == "admin_photos":
            await photo_management_panel(update, context)
        elif data == "admin_orders":
            await order_management_panel(update, context)
        elif data == "admin_users":
            await user_management_panel(update, context)
        elif data == "admin_analytics":
            await analytics_panel(update, context)
        elif data == "admin_settings":
            await query.edit_message_text(
                "⚙️ **Settings Panel**\n\nSettings management coming soon!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")
                ]]),
                parse_mode="Markdown"
            )
        # Product management sub-actions (handled here to avoid NameError)
        elif data in {"product_add", "product_list", "product_edit", "product_remove", "product_photo", "product_stock"}:
            try:
                print(f"[INTERFACE] Local product handler path for: {data}")
                if data == "product_add":
                    await _interface_show_add_product_form(query)
                elif data == "product_list":
                    await _interface_show_product_list(query)
                elif data == "product_edit":
                    await _interface_show_product_list(query)
                elif data == "product_remove":
                    await _interface_show_product_list(query)
                elif data == "product_photo":
                    # Reuse the existing photo panel
                    await photo_management_panel(update, context)
                elif data == "product_stock":
                    await _interface_show_product_list(query)
            except Exception as e:
                # Safe fallback without Markdown to avoid entity parse issues
                await query.edit_message_text(
                    f"Error handling product action: {e}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_products")]])
                )
        elif data in ["photo_add_location", "photo_show_location"]:
            await select_product_for_photos(update, context)
        else:
            # Forward any other callbacks (product_*, manage_*, etc.) to the unified handler
            from handlers_admin.unified_interface import unified_admin_callback_handler
            await unified_admin_callback_handler(update, context)
    
    except Exception as e:
        print(f"Error in admin callback handler: {e}")
        await query.answer(f"Error: {e}", show_alert=True)


# --- Local minimal helpers to avoid NameError and Markdown parse issues ---
async def _interface_show_product_list(query):
    """Minimal product list without Markdown to avoid parse issues."""
    async with SessionLocal() as session:
        products = await get_all_products(session)

        if not products:
            text = "No products found. Use /addproduct to add one."
            keyboard = [[
                InlineKeyboardButton("➕ Add Product", callback_data="product_add"),
                InlineKeyboardButton("🔙 Back", callback_data="admin_products"),
            ]]
        else:
            text_lines = [f"Products ({len(products)}):", ""]
            keyboard = []
            for product in products[:10]:
                status = "LOW" if getattr(product, "stock", 0) < 5 else "OK"
                text_lines.append(f"- {product.name} | ${product.price} | Stock: {getattr(product, 'stock', 0)} ({status})")
                keyboard.append([
                    InlineKeyboardButton(
                        (product.name if len(product.name) <= 32 else product.name[:29] + "..."),
                        callback_data=f"manage_product_{product.id}"
                    )
                ])
            if len(products) > 10:
                keyboard.append([InlineKeyboardButton(f"... and {len(products)-10} more", callback_data="product_list")])
            keyboard.extend([
                [InlineKeyboardButton("➕ Add Product", callback_data="product_add"), InlineKeyboardButton("🔄 Refresh", callback_data="product_list")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_products")],
            ])
            text = "\n".join(text_lines)

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def _interface_show_add_product_form(query):
    """Minimal instructions to add a product, without Markdown."""
    text = (
        "Add New Product\n\n"
        "Use the command: /addproduct <name> <category> <price> <description>\n"
        "Example: /addproduct \"Gaming Laptop\" Electronics 1299.99 \"RTX graphics\"\n\n"
        "Notes:\n"
        "- Use quotes for multi-word fields\n"
        "- Price is a number (no $)\n"
        "- Description optional"
    )
    keyboard = [
        [InlineKeyboardButton("📋 View Products", callback_data="product_list")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_products")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# Aliases to avoid NameError if other code expects these names in this module
async def show_add_product_form(query):
    return await _interface_show_add_product_form(query)


async def show_product_list(query):
    return await _interface_show_product_list(query)