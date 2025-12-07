from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from handlers_admin.auth import require_admin_auth
from db import SessionLocal
from utils.db_utils import get_all_products, get_product_by_id, get_orders, get_order_by_id, update_order_status, count_unused_location_photos
from handlers_admin.orders import fulfill_order_and_deliver_photos

@require_admin_auth  
async def unified_admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unified handler for all admin interface callbacks"""
    query = update.callback_query
    data = query.data
    
    print(f"Admin callback received: {data}")  # Debug logging
    
    try:
        await query.answer()  # Always answer the callback
        
        # Main admin panel navigation
        if data == "admin_main":
            await show_main_admin_panel(query)
        elif data == "admin_products":
            await show_product_management_panel(query)
        elif data == "admin_orders":
            await show_order_management_panel(query)
        elif data == "admin_photos":
            await show_photo_management_panel(query)
        elif data == "admin_users":
            await show_user_management_panel(query)
        elif data == "admin_analytics":
            await show_analytics_panel(query)
        elif data == "admin_settings":
            await show_settings_panel(query)
            
        # Product management callbacks
        elif data == "product_list":
            await show_product_list(query)
        elif data == "product_add":
            await show_add_product_form(query)
        elif data == "product_search":
            await show_product_search(query)
        elif data == "product_stats":
            await show_product_stats(query)
        elif data.startswith("manage_product_"):
            await manage_single_product(query, data.replace("manage_product_", ""))
        elif data.startswith("edit_product_"):
            await show_edit_product_form(query, data.replace("edit_product_", ""))
        elif data.startswith("delete_product_"):
            await confirm_delete_product(query, data.replace("delete_product_", ""))
        elif data.startswith("confirm_delete_product_"):
            await delete_product(query, data.replace("confirm_delete_product_", ""))
        elif data.startswith("toggle_product_"):
            await toggle_product_availability(query, data.replace("toggle_product_", ""))
        elif data.startswith("duplicate_product_"):
            await show_duplicate_product_form(query, data.replace("duplicate_product_", ""))
        elif data.startswith(("manage_product_photos_", "product_orders_", "export_products")):
            await handle_advanced_product_features(query, data)
            
        # Order management callbacks  
        elif data == "orders_view_all":
            await show_order_management_panel(query)
        elif data in ["orders_show_pending", "orders_show_completed", "orders_show_cancelled"]:
            await show_orders_by_status(query, data)
        elif data.startswith("manage_order_"):
            await manage_single_order(query, data.replace("manage_order_", ""))
        elif data.startswith(("complete_order_", "cancel_order_", "pending_order_")):
            await handle_order_status_change(query, context, data)
        elif data.startswith("orders_show_pending_all"):
            await show_all_orders_by_status(query, "pending")
        elif data.startswith("orders_show_completed_all"):
            await show_all_orders_by_status(query, "completed")
        elif data.startswith("orders_show_cancelled_all"):
            await show_all_orders_by_status(query, "cancelled")
        elif data.startswith("export_"):
            await handle_order_export(query, data)
        elif data.startswith("view_user_"):
            await show_user_details(query, data.replace("view_user_", ""))
        elif data.startswith("view_product_"):
            await show_product_details_from_order(query, data.replace("view_product_", ""))
            
        # Photo management callbacks
        elif data in ["photo_add_location", "photo_show_location"]:
            await show_product_selection_for_photos(query, context, data)
        elif data.startswith("product_selected_"):
            await handle_product_selected_for_photos(query, context, data.replace("product_selected_", ""))
        
        # User management callbacks
        elif data in ["user_add_coins", "user_set_balance", "user_top_users", "user_stats"]:
            await handle_user_management_actions(query, data)
        elif data.startswith("manage_user_balance_"):
            await handle_user_management_actions(query, data)
            
        # Analytics callbacks
        elif data in ["analytics_dashboard", "analytics_profits", "analytics_sales", "analytics_export"]:
            await handle_analytics_actions(query, data)
            
        # Settings callbacks
        elif data in ["settings_bot", "settings_admin", "settings_database", "settings_notifications"]:
            await handle_settings_actions(query, data)
        
        else:
            await query.edit_message_text(
                f"❌ Unknown command: {data}\n\nPlease try again or return to the main panel.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")
                ]]),
                parse_mode="Markdown"
            )
    
    except Exception as e:
        print(f"Error in admin callback handler: {e}")
        try:
            await query.edit_message_text(
                f"❌ **Error occurred:**\n{str(e)}\n\nPlease try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")
                ]]),
                parse_mode="Markdown"
            )
        except:
            pass

async def show_main_admin_panel(query):
    """Show the main admin control panel"""
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

async def show_product_management_panel(query):
    """Show product management options"""
    keyboard = [
        [InlineKeyboardButton("📋 List All Products", callback_data="product_list"),
         InlineKeyboardButton("➕ Add New Product", callback_data="product_add")],
        [InlineKeyboardButton("🔍 Search Products", callback_data="product_search"),
         InlineKeyboardButton("📊 Product Stats", callback_data="product_stats")],
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
    ]
    
    text = (
        "📦 **Product Management**\n\n"
        "Choose an action:\n"
        "📋 View and manage existing products\n"
        "➕ Add new products to your shop\n"
        "🔍 Search for specific products\n"
        "📊 View product statistics"
    )
    
    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_order_management_panel(query):
    """Show order management options"""
    async with SessionLocal() as session:
        orders = await get_orders(session, limit=100)
        
        # Count orders by status
        pending = len([o for o in orders if o.status == "pending"])
        completed = len([o for o in orders if o.status == "completed"])
        cancelled = len([o for o in orders if o.status == "cancelled"])
        
        text = (
            f"📋 **Order Management**\n\n"
            f"📊 **Order Summary:**\n"
            f"⏳ Pending: {pending}\n"
            f"✅ Completed: {completed}\n"
            f"❌ Cancelled: {cancelled}\n"
            f"📦 Total: {len(orders)}\n\n"
            f"Choose an action:"
        )
        
        keyboard = [
            [InlineKeyboardButton(f"⏳ Pending ({pending})", callback_data="orders_show_pending"),
             InlineKeyboardButton(f"✅ Completed ({completed})", callback_data="orders_show_completed")],
            [InlineKeyboardButton(f"❌ Cancelled ({cancelled})", callback_data="orders_show_cancelled"),
             InlineKeyboardButton("📊 Export Orders", callback_data="orders_export")],
            [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def show_photo_management_panel(query):
    """Show photo management options"""
    keyboard = [
        [InlineKeyboardButton("📸 Add Location Photos", callback_data="photo_add_location"),
         InlineKeyboardButton("🖼️ View Location Photos", callback_data="photo_show_location")],
        [InlineKeyboardButton("🖼️ Add Product Photos", callback_data="photo_add_product"),
         InlineKeyboardButton("📁 Manage All Photos", callback_data="photo_manage_all")],
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
    ]
    
    text = (
        "📸 **Photo Management**\n\n"
        "Manage your product and location photos:\n"
        "📸 Upload pickup location photos\n"
        "🖼️ View available location photos\n"
        "🖼️ Add product presentation photos\n"
        "📁 Manage all photos at once"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_user_management_panel(query):
    """Show user management options"""
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

async def show_analytics_panel(query):
    """Show analytics options"""
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

async def show_settings_panel(query):
    """Show settings options"""
    keyboard = [
        [InlineKeyboardButton("⚙️ Bot Settings", callback_data="settings_bot"),
         InlineKeyboardButton("🔑 Admin Settings", callback_data="settings_admin")],
        [InlineKeyboardButton("🗃️ Database", callback_data="settings_database"),
         InlineKeyboardButton("📢 Notifications", callback_data="settings_notifications")],
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
    ]
    
    text = (
        "⚙️ **Settings Panel**\n\n"
        "Configure bot settings:\n"
        "⚙️ General bot configuration\n"
        "🔑 Admin user management\n"
        "🗃️ Database maintenance\n"
        "📢 Notification settings\n\n"
        "⚠️ *Settings management coming soon!*"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_product_list(query):
    """Show interactive product list"""
    async with SessionLocal() as session:
        products = await get_all_products(session)
        
        if not products:
            await query.edit_message_text(
                "📦 **No Products Found**\n\nYour shop is empty. Add some products first!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("➕ Add First Product", callback_data="product_add"),
                    InlineKeyboardButton("🔙 Back", callback_data="admin_products")
                ]]),
                parse_mode="Markdown"
            )
            return
        
        text = f"📦 **Product List** ({len(products)} products)\n\nSelect a product to manage:\n\n"
        
        keyboard = []
        for product in products[:10]:  # Show first 10 products
            stock_status = "🔴" if product.stock < 5 else "🟢"
            button_text = f"{stock_status} {product.name} (${product.price})"
            keyboard.append([InlineKeyboardButton(
                button_text[:50] + "..." if len(button_text) > 50 else button_text,
                callback_data=f"manage_product_{product.id}"
            )])
        
        if len(products) > 10:
            keyboard.append([InlineKeyboardButton(f"... and {len(products) - 10} more", callback_data="product_list_all")])
        
        keyboard.extend([
            [InlineKeyboardButton("➕ Add New Product", callback_data="product_add"),
             InlineKeyboardButton("🔄 Refresh", callback_data="product_list")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_products")]
        ])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def manage_single_product(query, product_id):
    """Show management options for a specific product"""
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await query.edit_message_text("❌ Product not found.")
            return
        
        unused_photos = await count_unused_location_photos(session, product_id)
        stock_status = "🔴 LOW STOCK" if product.stock < 5 else "🟢 In Stock"
        
        text = (
            f"📦 **{product.name}**\n\n"
            f"💰 **Price:** ${product.price}\n"
            f"📦 **Stock:** {product.stock} ({stock_status})\n"
            f"🏷️ **Category:** {product.category or 'N/A'}\n"
            f"📸 **Location Photos:** {unused_photos} available\n"
            f"📝 **Description:** {product.description or 'No description'}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("✏️ Edit Details", callback_data=f"edit_product_{product_id}"),
             InlineKeyboardButton("📸 Manage Photos", callback_data=f"photos_product_{product_id}")],
            [InlineKeyboardButton("📦 Update Stock", callback_data=f"stock_product_{product_id}"),
             InlineKeyboardButton("💰 Change Price", callback_data=f"price_product_{product_id}")],
            [InlineKeyboardButton("🗑️ Delete Product", callback_data=f"delete_product_{product_id}"),
             InlineKeyboardButton("📊 View Stats", callback_data=f"stats_product_{product_id}")],
            [InlineKeyboardButton("🔙 Back to Products", callback_data="product_list")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def show_orders_by_status(query, status_data):
    """Show orders filtered by status"""
    status_map = {
        "orders_show_pending": "pending",
        "orders_show_completed": "completed", 
        "orders_show_cancelled": "cancelled"
    }
    
    status = status_map.get(status_data)
    if not status:
        return
    
    async with SessionLocal() as session:
        orders = await get_orders(session, limit=50)
        filtered_orders = [o for o in orders if o.status == status]
        
        status_emoji = {"pending": "⏳", "completed": "✅", "cancelled": "❌"}
        status_name = {"pending": "Pending", "completed": "Completed", "cancelled": "Cancelled"}
        
        text = f"{status_emoji[status]} **{status_name[status]} Orders** ({len(filtered_orders)})\n\n"
        
        keyboard = []
        
        for order in filtered_orders[:8]:  # Show first 8
            order_date = order.created_at.strftime("%m/%d %H:%M")
            button_text = f"{order.product_name} - User {order.user_id[-4:]} ({order_date})"
            keyboard.append([InlineKeyboardButton(
                button_text[:55] + "..." if len(button_text) > 55 else button_text,
                callback_data=f"manage_order_{order.id}"
            )])
        
        if len(filtered_orders) > 8:
            keyboard.append([InlineKeyboardButton(f"... and {len(filtered_orders) - 8} more", callback_data=f"{status_data}_all")])
        
        keyboard.extend([
            [InlineKeyboardButton("🔄 Refresh", callback_data=status_data),
             InlineKeyboardButton("📊 Export", callback_data=f"export_{status}")],
            [InlineKeyboardButton("🔙 Back", callback_data="orders_view_all")]
        ])
        
        if not filtered_orders:
            text += f"No {status} orders found."
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def manage_single_order(query, order_id):
    """Show management options for a specific order"""
    async with SessionLocal() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await query.edit_message_text("❌ Order not found.")
            return
        
        order_date = order.created_at.strftime("%Y-%m-%d %H:%M:%S")
        status_emoji = {"pending": "⏳", "completed": "✅", "cancelled": "❌"}
        
        text = (
            f"📋 **Order Details**\n\n"
            f"**ID:** `{order.id[:8]}...`\n"
            f"**User:** {order.user_id}\n"
            f"**Product:** {order.product_name}\n"
            f"**Quantity:** {order.quantity}\n"
            f"**Status:** {status_emoji.get(order.status, '')} {order.status.title()}\n"
            f"**Date:** {order_date}\n"
        )
        
        keyboard = []
        
        # Status change buttons
        if order.status == "pending":
            keyboard.extend([
                [InlineKeyboardButton("✅ Complete Order", callback_data=f"complete_order_{order_id}"),
                 InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_order_{order_id}")],
            ])
        elif order.status in ["completed", "cancelled"]:
            keyboard.append([InlineKeyboardButton("🔄 Mark Pending", callback_data=f"pending_order_{order_id}")])
        
        keyboard.extend([
            [InlineKeyboardButton("👤 View User", callback_data=f"view_user_{order.user_id}"),
             InlineKeyboardButton("📦 View Product", callback_data=f"view_product_{order.product_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="orders_view_all")]
        ])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def handle_order_status_change(query, context, data):
    """Handle order status changes"""
    parts = data.split("_", 2)
    if len(parts) < 3:
        await query.edit_message_text("❌ Invalid order data.")
        return
        
    action = parts[0]  # complete, cancel, pending
    order_id = parts[2]  # order UUID
    
    async with SessionLocal() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await query.edit_message_text("❌ Order not found.")
            return
        
        success_messages = {
            "complete": "✅ Order completed successfully!",
            "cancel": "❌ Order cancelled successfully!",
            "pending": "⏳ Order marked as pending!"
        }
        
        if action == "complete" and order.status != "completed":
            result = await fulfill_order_and_deliver_photos(session, order, context)
            message = success_messages["complete"]
            if result == "no_photos":
                message += "\n⚠️ Note: No location photos were available."
        elif action == "cancel" and order.status != "cancelled":
            await update_order_status(session, order_id, "cancelled")
            message = success_messages["cancel"]
        elif action == "pending":
            await update_order_status(session, order_id, "pending")
            message = success_messages["pending"]
        else:
            message = f"❌ Order is already {order.status}."
        
        await query.edit_message_text(
            f"{message}\n\nOrder: `{order_id[:8]}...`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Orders", callback_data="orders_view_all")
            ]]),
            parse_mode="Markdown"
        )

async def show_product_selection_for_photos(query, context, action):
    """Show product selection for photo operations"""
    context.user_data["photo_action"] = action
    
    async with SessionLocal() as session:
        products = await get_all_products(session)
        
        if not products:
            await query.edit_message_text(
                "❌ No products found. Please add products first.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin_photos")
                ]]),
                parse_mode="Markdown"
            )
            return
        
        keyboard = []
        for product in products:
            keyboard.append([InlineKeyboardButton(
                f"{product.name} ({product.category})", 
                callback_data=f"product_selected_{product.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_photos")])
        
        action_text = "add location photos to" if action == "photo_add_location" else "view location photos for"
        text = f"📸 **Select Product**\n\nChoose which product you want to {action_text}:"
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def handle_product_selected_for_photos(query, context, product_id):
    """Handle product selection for photo operations"""
    action = context.user_data.get("photo_action")
    
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await query.edit_message_text("❌ Product not found.")
            return
        
        if action == "photo_show_location":
            # Show location photos for this product
            unused_count = await count_unused_location_photos(session, product_id)
            
            text = (
                f"📸 **Location Photos for {product.name}**\n\n"
                f"📊 Available photos: {unused_count}\n\n"
                f"Use the old command `/showlocationphotos {product_id}` to view individual photos."
            )
            
            keyboard = [
                [InlineKeyboardButton("➕ Add More Photos", callback_data=f"photo_add_location")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_photos")]
            ]
            
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
        elif action == "photo_add_location":
            # Start photo upload process
            text = (
                f"📸 **Add Location Photos**\n\n"
                f"Selected product: **{product.name}**\n\n"
                f"Use the old command `/addlocationphoto {product_id}` to upload photos.\n\n"
                f"Or continue with the new interface (coming soon)."
            )
            
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Photo Management", callback_data="admin_photos")]
            ]
            
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

# ============= PRODUCT MANAGEMENT FUNCTIONS =============

async def show_product_list(query):
    """Display all products with management options"""
    async with SessionLocal() as session:
        products = await get_all_products(session)
        
        if not products:
            text = "📦 **No Products Found**\n\nYour shop doesn't have any products yet."
            keyboard = [[InlineKeyboardButton("➕ Add First Product", callback_data="product_add")],
                       [InlineKeyboardButton("🔙 Back", callback_data="admin_products")]]
        else:
            text = f"📦 **All Products** ({len(products)})\n\nSelect a product to manage:"
            keyboard = []
            
            for product in products:
                availability = "✅" if product.available else "❌"
                button_text = f"{availability} {product.name} - ${product.price}"
                keyboard.append([InlineKeyboardButton(
                    button_text[:50] + "..." if len(button_text) > 50 else button_text,
                    callback_data=f"manage_product_{product.id}"
                )])
            
            keyboard.extend([
                [InlineKeyboardButton("➕ Add New Product", callback_data="product_add"),
                 InlineKeyboardButton("📊 Product Stats", callback_data="product_stats")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_products")]
            ])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def manage_single_product(query, product_id):
    """Show management options for a specific product"""
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await query.edit_message_text("❌ Product not found.")
            return
        
        availability = "Available" if product.available else "Unavailable"
        availability_emoji = "✅" if product.available else "❌"
        
        text = (
            f"📦 **Product Details**\n\n"
            f"**Name:** {product.name}\n"
            f"**Category:** {product.category}\n"
            f"**Price:** ${product.price}\n"
            f"**Status:** {availability_emoji} {availability}\n"
            f"**Description:** {product.description or 'No description'}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("✏️ Edit Product", callback_data=f"edit_product_{product_id}"),
             InlineKeyboardButton("🗑️ Delete Product", callback_data=f"delete_product_{product_id}")],
            [InlineKeyboardButton("📸 Manage Photos", callback_data=f"manage_product_photos_{product_id}"),
             InlineKeyboardButton("📊 View Orders", callback_data=f"product_orders_{product_id}")],
            [InlineKeyboardButton("🔄 Toggle Availability", callback_data=f"toggle_product_{product_id}"),
             InlineKeyboardButton("📋 Duplicate", callback_data=f"duplicate_product_{product_id}")],
            [InlineKeyboardButton("🔙 Back to Products", callback_data="product_list")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def show_add_product_form(query):
    """Show add product form instructions"""
    text = (
        "➕ **Add New Product**\n\n"
        "To add a new product, use the command:\n"
        "`/addproduct <name> <category> <price> <description>`\n\n"
        "**Example:**\n"
        "`/addproduct \"Gaming Laptop\" Electronics 1299.99 \"High-performance gaming laptop with RTX graphics\"`\n\n"
        "📝 **Tips:**\n"
        "• Use quotes for multi-word names\n"
        "• Price should be a number (no $ symbol)\n"
        "• Description is optional\n"
        "• Product will be available by default"
    )
    
    keyboard = [
        [InlineKeyboardButton("📋 View All Products", callback_data="product_list")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_products")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_product_search(query):
    """Show product search instructions"""
    text = (
        "🔍 **Search Products**\n\n"
        "To search for products, use one of these commands:\n\n"
        "**By Name:**\n"
        "`/searchproduct product_name`\n\n"
        "**By Category:**\n"
        "`/searchcategory category`\n\n"
        "**By Price Range:**\n"
        "`/searchprice min_price max_price`\n\n"
        "**Examples:**\n"
        "`/searchproduct laptop`\n"
        "`/searchcategory Electronics`\n"
        "`/searchprice 100 500`"
    )
    
    keyboard = [
        [InlineKeyboardButton("📋 View All Products", callback_data="product_list")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_products")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_product_stats(query):
    """Show product statistics"""
    async with SessionLocal() as session:
        products = await get_all_products(session)
        orders = await get_orders(session, limit=1000)
        
        if not products:
            text = "📊 **Product Statistics**\n\n❌ No products found."
            keyboard = [[InlineKeyboardButton("➕ Add Product", callback_data="product_add")]]
        else:
            available_count = len([p for p in products if p.available])
            unavailable_count = len(products) - available_count
            
            # Calculate category distribution
            categories = {}
            for product in products:
                categories[product.category] = categories.get(product.category, 0) + 1
            
            # Calculate sales stats
            product_sales = {}
            total_revenue = 0
            for order in orders:
                if order.status == "completed":
                    product_sales[order.product_name] = product_sales.get(order.product_name, 0) + order.quantity
                    # Find product to get price
                    product = next((p for p in products if p.name == order.product_name), None)
                    if product:
                        total_revenue += product.price * order.quantity
            
            text = (
                f"📊 **Product Statistics**\n\n"
                f"📦 **Inventory:**\n"
                f"• Total Products: {len(products)}\n"
                f"• Available: {available_count}\n"
                f"• Unavailable: {unavailable_count}\n\n"
                f"📊 **Categories:**\n"
            )
            
            for category, count in categories.items():
                text += f"• {category}: {count}\n"
            
            text += (
                f"\n💰 **Sales:**\n"
                f"• Total Revenue: ${total_revenue:.2f}\n"
                f"• Products Sold: {sum(product_sales.values())}\n"
            )
            
            if product_sales:
                top_product = max(product_sales.items(), key=lambda x: x[1])
                text += f"• Top Seller: {top_product[0]} ({top_product[1]} sold)\n"
        
        keyboard = [
            [InlineKeyboardButton("📋 View Products", callback_data="product_list"),
             InlineKeyboardButton("📈 Export Data", callback_data="export_products")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_products")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def show_edit_product_form(query, product_id):
    """Show edit product instructions"""
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await query.edit_message_text("❌ Product not found.")
            return
        
        text = (
            f"✏️ **Edit Product: {product.name}**\n\n"
            f"**Current Details:**\n"
            f"• Name: {product.name}\n"
            f"• Category: {product.category}\n"
            f"• Price: ${product.price}\n"
            f"• Description: {product.description or 'None'}\n"
            f"• Status: {'Available' if product.available else 'Unavailable'}\n\n"
            f"To edit this product, use:\n"
            f"`/editproduct {product_id} <name> <category> <price> <description>`\n\n"
            f"**Example:**\n"
            f"`/editproduct {product_id} \"Updated Name\" Electronics 999.99 \"New description\"`"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Toggle Availability", callback_data=f"toggle_product_{product_id}")],
            [InlineKeyboardButton("🔙 Back to Product", callback_data=f"manage_product_{product_id}")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def confirm_delete_product(query, product_id):
    """Show delete confirmation"""
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await query.edit_message_text("❌ Product not found.")
            return
        
        text = (
            f"🗑️ **Delete Product**\n\n"
            f"⚠️ **WARNING:** This action cannot be undone!\n\n"
            f"Product to delete:\n"
            f"• **Name:** {product.name}\n"
            f"• **Category:** {product.category}\n"
            f"• **Price:** ${product.price}\n\n"
            f"Are you sure you want to delete this product?"
        )
        
        keyboard = [
            [InlineKeyboardButton("❌ Yes, Delete", callback_data=f"confirm_delete_product_{product_id}"),
             InlineKeyboardButton("✅ No, Keep It", callback_data=f"manage_product_{product_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data=f"manage_product_{product_id}")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def delete_product(query, product_id):
    """Actually delete the product"""
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await query.edit_message_text("❌ Product not found.")
            return
        
        product_name = product.name
        
        # Delete the product
        await session.delete(product)
        await session.commit()
        
        text = f"✅ **Product Deleted**\n\nProduct '{product_name}' has been permanently deleted."
        
        keyboard = [
            [InlineKeyboardButton("📋 View Remaining Products", callback_data="product_list")],
            [InlineKeyboardButton("🔙 Back to Product Management", callback_data="admin_products")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def toggle_product_availability(query, product_id):
    """Toggle product availability"""
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await query.edit_message_text("❌ Product not found.")
            return
        
        # Toggle availability
        product.available = not product.available
        await session.commit()
        
        status = "Available" if product.available else "Unavailable"
        emoji = "✅" if product.available else "❌"
        
        text = f"{emoji} **Product Status Updated**\n\nProduct '{product.name}' is now {status}."
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Product", callback_data=f"manage_product_{product_id}")],
            [InlineKeyboardButton("📋 View All Products", callback_data="product_list")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def show_duplicate_product_form(query, product_id):
    """Show duplicate product instructions"""
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await query.edit_message_text("❌ Product not found.")
            return
        
        text = (
            f"📋 **Duplicate Product: {product.name}**\n\n"
            f"To create a copy of this product, use:\n"
            f"`/duplicateproduct {product_id} <new_name>`\n\n"
            f"**Example:**\n"
            f"`/duplicateproduct {product_id} \"Copy of {product.name}\"`\n\n"
            f"The new product will have the same category, price, and description, but will be named differently."
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Product", callback_data=f"manage_product_{product_id}")],
            [InlineKeyboardButton("📋 View All Products", callback_data="product_list")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def handle_advanced_product_features(query, data):
    """Handle advanced product features like photo management and order viewing"""
    if data.startswith("manage_product_photos_"):
        product_id = data.replace("manage_product_photos_", "")
        text = (
            f"📸 **Product Photo Management**\n\n"
            f"Photo management for this product:\n"
            f"• Use `/addproductphoto {product_id}` to add photos\n"
            f"• Use `/viewproductphotos {product_id}` to view photos\n"
            f"• Use `/deleteproductphoto {product_id} <photo_id>` to remove photos\n\n"
            f"Advanced photo management interface coming soon!"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Product", callback_data=f"manage_product_{product_id}")]]
        
    elif data.startswith("product_orders_"):
        product_id = data.replace("product_orders_", "")
        
        # Get orders for this product
        async with SessionLocal() as session:
            product = await get_product_by_id(session, product_id)
            if not product:
                await query.edit_message_text("❌ Product not found.")
                return
            
            orders = await get_orders(session, limit=100)
            product_orders = [o for o in orders if o.product_name == product.name]
            
            if not product_orders:
                text = f"📊 **Orders for {product.name}**\n\nNo orders found for this product."
            else:
                pending = len([o for o in product_orders if o.status == "pending"])
                completed = len([o for o in product_orders if o.status == "completed"])
                cancelled = len([o for o in product_orders if o.status == "cancelled"])
                total_sold = sum(o.quantity for o in product_orders if o.status == "completed")
                
                text = (
                    f"📊 **Orders for {product.name}**\n\n"
                    f"📦 Total Orders: {len(product_orders)}\n"
                    f"⏳ Pending: {pending}\n"
                    f"✅ Completed: {completed}\n"
                    f"❌ Cancelled: {cancelled}\n"
                    f"🛒 Total Sold: {total_sold} units\n"
                    f"💰 Revenue: ${product.price * total_sold:.2f}"
                )
            
            keyboard = [
                [InlineKeyboardButton("📋 View All Orders", callback_data="orders_view_all")],
                [InlineKeyboardButton("🔙 Back to Product", callback_data=f"manage_product_{product_id}")]
            ]
    
    elif data == "export_products":
        text = (
            "📈 **Export Product Data**\n\n"
            "To export product data, use:\n"
            "`/exportproducts <format>`\n\n"
            "**Available formats:**\n"
            "• CSV - Comma-separated values\n"
            "• JSON - JavaScript Object Notation\n"
            "• TXT - Plain text\n\n"
            "**Example:**\n"
            "`/exportproducts csv`"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 View Stats", callback_data="product_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_products")]
        ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    ) 
 
 #   = = = = = = = = = = = = =   U S E R   M A N A G E M E N T   F U N C T I O N S   = = = = = = = = = = = = = 
 
 a s y n c   d e f   h a n d l e _ u s e r _ m a n a g e m e n t _ a c t i o n s ( q u e r y ,   d a t a ) : 
         i f   d a t a   = =   ' u s e r _ a d d _ c o i n s ' : 
                 t e x t   =   '   * * A d d   C o i n s   t o   U s e r * * \ n \ n T o   a d d   c o i n s   u s e :   / a d d c o i n s   u s e r _ i d   a m o u n t ' 
                 k e y b o a r d   =   [ [ I n l i n e K e y b o a r d B u t t o n ( '   B a c k ' ,   c a l l b a c k _ d a t a = ' a d m i n _ u s e r s ' ) ] ] 
         e l i f   d a t a   = =   ' u s e r _ s e t _ b a l a n c e ' : 
                 t e x t   =   '   * * S e t   U s e r   B a l a n c e * * \ n \ n T o   s e t   b a l a n c e   u s e :   / s e t b a l a n c e   u s e r _ i d   a m o u n t ' 
                 k e y b o a r d   =   [ [ I n l i n e K e y b o a r d B u t t o n ( '   B a c k ' ,   c a l l b a c k _ d a t a = ' a d m i n _ u s e r s ' ) ] ] 
         e l i f   d a t a   = =   ' u s e r _ t o p _ u s e r s ' : 
                 t e x t   =   '   * * T o p   U s e r s * * \ n \ n T o   v i e w   t o p   u s e r s   u s e :   / t o p u s e r s ' 
                 k e y b o a r d   =   [ [ I n l i n e K e y b o a r d B u t t o n ( '   B a c k ' ,   c a l l b a c k _ d a t a = ' a d m i n _ u s e r s ' ) ] ] 
         e l i f   d a t a   = =   ' u s e r _ s t a t s ' : 
                 t e x t   =   '   * * U s e r   S t a t i s t i c s * * \ n \ n T o   v i e w   s t a t s   u s e :   / u s e r s t a t s ' 
                 k e y b o a r d   =   [ [ I n l i n e K e y b o a r d B u t t o n ( '   B a c k ' ,   c a l l b a c k _ d a t a = ' a d m i n _ u s e r s ' ) ] ] 
         
         a w a i t   q u e r y . e d i t _ m e s s a g e _ t e x t ( t e x t ,   r e p l y _ m a r k u p = I n l i n e K e y b o a r d M a r k u p ( k e y b o a r d ) ,   p a r s e _ m o d e = ' M a r k d o w n ' ) 
 
 a s y n c   d e f   h a n d l e _ a n a l y t i c s _ a c t i o n s ( q u e r y ,   d a t a ) : 
         i f   d a t a   = =   ' a n a l y t i c s _ d a s h b o a r d ' : 
                 t e x t   =   '   * * A n a l y t i c s   D a s h b o a r d * * \ n \ n B a s i c   s t a t s   a n d   o v e r v i e w   c o m i n g   s o o n ! ' 
                 k e y b o a r d   =   [ [ I n l i n e K e y b o a r d B u t t o n ( '   B a c k ' ,   c a l l b a c k _ d a t a = ' a d m i n _ a n a l y t i c s ' ) ] ] 
         e l i f   d a t a   = =   ' a n a l y t i c s _ p r o f i t s ' : 
                 t e x t   =   '   * * P r o f i t   A n a l y t i c s * * \ n \ n U s e :   / p r o f i t s   p e r i o d ' 
                 k e y b o a r d   =   [ [ I n l i n e K e y b o a r d B u t t o n ( '   B a c k ' ,   c a l l b a c k _ d a t a = ' a d m i n _ a n a l y t i c s ' ) ] ] 
         e l i f   d a t a   = =   ' a n a l y t i c s _ s a l e s ' : 
                 t e x t   =   '   * * S a l e s   R e p o r t s * * \ n \ n U s e :   / s a l e s r e p o r t   p e r i o d   f o r m a t ' 
                 k e y b o a r d   =   [ [ I n l i n e K e y b o a r d B u t t o n ( '   B a c k ' ,   c a l l b a c k _ d a t a = ' a d m i n _ a n a l y t i c s ' ) ] ] 
         e l i f   d a t a   = =   ' a n a l y t i c s _ e x p o r t ' : 
                 t e x t   =   '   * * E x p o r t   D a t a * * \ n \ n U s e :   / e x p o r t d a t a   t y p e   f o r m a t ' 
                 k e y b o a r d   =   [ [ I n l i n e K e y b o a r d B u t t o n ( '   B a c k ' ,   c a l l b a c k _ d a t a = ' a d m i n _ a n a l y t i c s ' ) ] ] 
         
         a w a i t   q u e r y . e d i t _ m e s s a g e _ t e x t ( t e x t ,   r e p l y _ m a r k u p = I n l i n e K e y b o a r d M a r k u p ( k e y b o a r d ) ,   p a r s e _ m o d e = ' M a r k d o w n ' ) 
 
 a s y n c   d e f   h a n d l e _ s e t t i n g s _ a c t i o n s ( q u e r y ,   d a t a ) : 
         i f   d a t a   = =   ' s e t t i n g s _ b o t ' : 
                 t e x t   =   '   * * B o t   S e t t i n g s * * \ n \ n U s e :   / s e t d e f a u l t c o i n s   a m o u n t ' 
                 k e y b o a r d   =   [ [ I n l i n e K e y b o a r d B u t t o n ( '   B a c k ' ,   c a l l b a c k _ d a t a = ' a d m i n _ s e t t i n g s ' ) ] ] 
         e l i f   d a t a   = =   ' s e t t i n g s _ a d m i n ' : 
                 t e x t   =   '   * * A d m i n   S e t t i n g s * * \ n \ n U s e :   / a d d a d m i n   u s e r _ i d ' 
                 k e y b o a r d   =   [ [ I n l i n e K e y b o a r d B u t t o n ( '   B a c k ' ,   c a l l b a c k _ d a t a = ' a d m i n _ s e t t i n g s ' ) ] ] 
         e l i f   d a t a   = =   ' s e t t i n g s _ d a t a b a s e ' : 
                 t e x t   =   '   * * D a t a b a s e   M a n a g e m e n t * * \ n \ n U s e :   / b a c k u p d b ' 
                 k e y b o a r d   =   [ [ I n l i n e K e y b o a r d B u t t o n ( '   B a c k ' ,   c a l l b a c k _ d a t a = ' a d m i n _ s e t t i n g s ' ) ] ] 
         e l i f   d a t a   = =   ' s e t t i n g s _ n o t i f i c a t i o n s ' : 
                 t e x t   =   '   * * N o t i f i c a t i o n s * * \ n \ n U s e :   / n o t i f i c a t i o n s   o n / o f f ' 
                 k e y b o a r d   =   [ [ I n l i n e K e y b o a r d B u t t o n ( '   B a c k ' ,   c a l l b a c k _ d a t a = ' a d m i n _ s e t t i n g s ' ) ] ] 
         
         a w a i t   q u e r y . e d i t _ m e s s a g e _ t e x t ( t e x t ,   r e p l y _ m a r k u p = I n l i n e K e y b o a r d M a r k u p ( k e y b o a r d ) ,   p a r s e _ m o d e = ' M a r k d o w n ' ) 
  
 