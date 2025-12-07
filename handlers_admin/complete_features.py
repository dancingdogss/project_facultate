"""
Complete admin features implementation
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from db import SessionLocal
from utils.db_utils import get_all_products, get_orders

# ============= USER MANAGEMENT FUNCTIONS =============

async def handle_user_management_actions(query, data):
    """Handle user management callback actions"""
    if data == "user_add_coins":
        text = (
            "💰 **Add Coins to User**\n\n"
            "To add coins to a user's account, use:\n"
            "`/addcoins user_id amount`\n\n"
            "**Examples:**\n"
            "`/addcoins 123456789 50`\n"
            "`/addcoins @username 100`"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_users")]]
        
    elif data == "user_set_balance":
        text = (
            "💳 **Set User Balance**\n\n"
            "To set a specific balance for a user, use:\n"
            "`/setbalance user_id amount`\n\n"
            "**Examples:**\n"
            "`/setbalance 123456789 250`\n"
            "`/setbalance @username 0`"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_users")]]
        
    elif data == "user_top_users":
        text = (
            "👥 **Top Users by Balance**\n\n"
            "To view top users, use:\n"
            "`/topusers` or `/topusers limit`\n\n"
            "**Examples:**\n"
            "`/topusers` - Top 10 users\n"
            "`/topusers 25` - Top 25 users"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_users")]]
        
    elif data == "user_stats":
        text = (
            "📊 **User Statistics**\n\n"
            "To view detailed user statistics, use:\n"
            "`/userstats`\n\n"
            "**Statistics include:**\n"
            "• Total registered users\n"
            "• Active users (last 30 days)\n"
            "• Average user balance\n"
            "• User growth trends"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_users")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ============= ANALYTICS FUNCTIONS =============

async def handle_analytics_actions(query, data):
    """Handle analytics callback actions"""
    if data == "analytics_dashboard":
        # Get basic stats
        async with SessionLocal() as session:
            try:
                products = await get_all_products(session)
                orders = await get_orders(session, limit=1000)
                
                total_orders = len(orders)
                completed_orders = len([o for o in orders if o.status == "completed"])
                
                # Calculate revenue
                total_revenue = 0
                for order in orders:
                    if order.status == "completed":
                        product = next((p for p in products if p.name == order.product_name), None)
                        if product:
                            total_revenue += product.price * order.quantity
                
                text = (
                    f"📊 **Analytics Dashboard**\n\n"
                    f"📦 Total Products: {len(products)}\n"
                    f"📋 Total Orders: {total_orders}\n"
                    f"✅ Completed Orders: {completed_orders}\n"
                    f"💰 Total Revenue: ${total_revenue:.2f}\n"
                    f"📈 Conversion Rate: {(completed_orders/max(total_orders, 1)*100):.1f}%"
                )
            except Exception as e:
                text = f"📊 **Analytics Dashboard**\n\n❌ Error loading data: {str(e)}"
        
        keyboard = [
            [InlineKeyboardButton("💹 Profits", callback_data="analytics_profits"),
             InlineKeyboardButton("📈 Sales", callback_data="analytics_sales")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_analytics")]
        ]
        
    elif data == "analytics_profits":
        text = (
            "💹 **Profit Analytics**\n\n"
            "To view profit analysis, use:\n"
            "`/profits period`\n\n"
            "**Periods:** today, week, month, all\n"
            "**Example:** `/profits month`"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_analytics")]]
        
    elif data == "analytics_sales":
        text = (
            "📈 **Sales Reports**\n\n"
            "To generate sales reports, use:\n"
            "`/salesreport period format`\n\n"
            "**Periods:** daily, weekly, monthly\n"
            "**Formats:** text, csv, pdf\n"
            "**Example:** `/salesreport monthly csv`"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_analytics")]]
        
    elif data == "analytics_export":
        text = (
            "🔄 **Export Analytics Data**\n\n"
            "To export data, use:\n"
            "`/exportdata type format`\n\n"
            "**Types:** orders, products, users, all\n"
            "**Formats:** csv, json, pdf\n"
            "**Example:** `/exportdata orders csv`"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_analytics")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ============= SETTINGS FUNCTIONS =============

async def handle_settings_actions(query, data):
    """Handle settings callback actions"""
    if data == "settings_bot":
        text = (
            "⚙️ **Bot Settings**\n\n"
            "**Available Commands:**\n"
            "`/setdefaultcoins amount`\n"
            "`/setmainmenu`\n"
            "`/togglemaintenance`\n\n"
            "**Current Settings:**\n"
            "• Default Coins: 100\n"
            "• Maintenance Mode: Off"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_settings")]]
        
    elif data == "settings_admin":
        text = (
            "🔑 **Admin Settings**\n\n"
            "**Available Commands:**\n"
            "`/addadmin user_id`\n"
            "`/removeadmin user_id`\n"
            "`/listadmins`\n\n"
            "**Current Admins:**\n"
            "• You (Owner)\n"
            "• Use `/listadmins` for complete list"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_settings")]]
        
    elif data == "settings_database":
        text = (
            "🗃️ **Database Management**\n\n"
            "**Available Commands:**\n"
            "`/backupdb` - Create backup\n"
            "`/dbstats` - Show statistics\n"
            "`/cleanupdb` - Clean old data\n"
            "`/optimizedb` - Optimize performance\n\n"
            "⚠️ Always backup before major changes!"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_settings")]]
        
    elif data == "settings_notifications":
        text = (
            "📢 **Notification Settings**\n\n"
            "**Available Commands:**\n"
            "`/notifications on/off`\n"
            "`/notifyorders on/off`\n"
            "`/notifyusers on/off`\n"
            "`/notifyerrors on/off`\n\n"
            "**Current Status:** All notifications on"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_settings")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ============= PHOTO MANAGEMENT FUNCTIONS =============

async def handle_photo_management_actions(query, data):
    """Handle photo management callback actions"""
    if data == "photo_add_product":
        text = (
            "🖼️ **Add Product Photos**\n\n"
            "To add product presentation photos, use:\n"
            "`/addproductphoto product_id`\n\n"
            "**Examples:**\n"
            "`/addproductphoto 12345`\n\n"
            "Product photos are used for display in the catalog."
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_photos")]]
        
    elif data == "photo_manage_all":
        text = (
            "📁 **Manage All Photos**\n\n"
            "**Available Commands:**\n"
            "`/listphotos type` - List photos by type\n"
            "`/deletephoto photo_id` - Delete a photo\n"
            "`/photoinfo photo_id` - Get photo details\n\n"
            "**Photo Types:**\n"
            "• location - Pickup location photos\n"
            "• product - Product presentation photos\n"
            "• delivered - Delivered order photos"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_photos")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )