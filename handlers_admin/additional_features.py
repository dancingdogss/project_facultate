# ============= USER MANAGEMENT FUNCTIONS =============

async def handle_user_management_actions(query, data):
    """Handle all user management callback actions"""
    if data == "user_add_coins":
        await show_add_coins_form(query)
    elif data == "user_set_balance":
        await show_set_balance_form(query)
    elif data == "user_top_users":
        await show_top_users(query)
    elif data == "user_stats":
        await show_user_stats(query)
    elif data.startswith("manage_user_balance_"):
        user_id = data.replace("manage_user_balance_", "")
        await show_user_balance_management(query, user_id)

async def show_add_coins_form(query):
    """Show add coins form instructions"""
    text = (
        "💰 **Add Coins to User**\n\n"
        "To add coins to a user's account, use:\n"
        "`/addcoins user_id amount`\n\n"
        "**Examples:**\n"
        "`/addcoins 123456789 50`\n"
        "`/addcoins @username 100`\n\n"
        "📝 **Tips:**\n"
        "• Amount must be positive\n"
        "• Use user ID or @username\n"
        "• Coins will be added to current balance\n"
        "• User will be notified of the addition"
    )
    
    keyboard = [
        [InlineKeyboardButton("👥 View Top Users", callback_data="user_top_users")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_users")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_set_balance_form(query):
    """Show set balance form instructions"""
    text = (
        "💳 **Set User Balance**\n\n"
        "To set a specific balance for a user, use:\n"
        "`/setbalance user_id amount`\n\n"
        "**Examples:**\n"
        "`/setbalance 123456789 250`\n"
        "`/setbalance @username 0`\n\n"
        "⚠️ **Warning:**\n"
        "• This will replace the current balance\n"
        "• Amount can be 0 to reset balance\n"
        "• User will be notified of the change\n"
        "• Action is logged for audit"
    )
    
    keyboard = [
        [InlineKeyboardButton("💰 Add Coins Instead", callback_data="user_add_coins")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_users")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_top_users(query):
    """Show top users by balance"""
    async with SessionLocal() as session:
        # This would need a proper user balance query
        text = (
            "👥 **Top Users by Balance**\n\n"
            "To view top users, use:\n"
            "`/topusers` or `/topusers limit`\n\n"
            "**Examples:**\n"
            "`/topusers` - Top 10 users\n"
            "`/topusers 25` - Top 25 users\n\n"
            "Advanced user analytics coming soon!"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 User Stats", callback_data="user_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_users")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def show_user_stats(query):
    """Show user statistics"""
    text = (
        "📊 **User Statistics**\n\n"
        "To view detailed user statistics, use:\n"
        "`/userstats`\n\n"
        "**Statistics include:**\n"
        "• Total registered users\n"
        "• Active users (last 30 days)\n"
        "• Average user balance\n"
        "• User growth trends\n"
        "• Order frequency per user\n\n"
        "Advanced analytics dashboard coming soon!"
    )
    
    keyboard = [
        [InlineKeyboardButton("👥 Top Users", callback_data="user_top_users")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_users")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ============= ANALYTICS FUNCTIONS =============

async def handle_analytics_actions(query, data):
    """Handle all analytics callback actions"""
    if data == "analytics_dashboard":
        await show_analytics_dashboard(query)
    elif data == "analytics_profits":
        await show_profit_analytics(query)
    elif data == "analytics_sales":
        await show_sales_report(query)
    elif data == "analytics_export":
        await show_analytics_export(query)

async def show_analytics_dashboard(query):
    """Show analytics dashboard"""
    async with SessionLocal() as session:
        # Get basic stats
        products = await get_all_products(session)
        orders = await get_orders(session, limit=1000)
        
        total_orders = len(orders)
        completed_orders = len([o for o in orders if o.status == "completed"])
        pending_orders = len([o for o in orders if o.status == "pending"])
        
        # Calculate revenue
        total_revenue = 0
        for order in orders:
            if order.status == "completed":
                product = next((p for p in products if p.name == order.product_name), None)
                if product:
                    total_revenue += product.price * order.quantity
        
        text = (
            f"📊 **Analytics Dashboard**\n\n"
            f"**Overview:**\n"
            f"📦 Total Products: {len(products)}\n"
            f"📋 Total Orders: {total_orders}\n"
            f"✅ Completed Orders: {completed_orders}\n"
            f"⏳ Pending Orders: {pending_orders}\n"
            f"💰 Total Revenue: ${total_revenue:.2f}\n\n"
            f"**Conversion Rate:** {(completed_orders/max(total_orders, 1)*100):.1f}%\n"
            f"**Average Order Value:** ${(total_revenue/max(completed_orders, 1)):.2f}"
        )
    
    keyboard = [
        [InlineKeyboardButton("💹 Profit Analysis", callback_data="analytics_profits"),
         InlineKeyboardButton("📈 Sales Report", callback_data="analytics_sales")],
        [InlineKeyboardButton("🔄 Export Data", callback_data="analytics_export"),
         InlineKeyboardButton("🔙 Back", callback_data="admin_analytics")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_profit_analytics(query):
    """Show profit analytics"""
    text = (
        "💹 **Profit Analytics**\n\n"
        "To view detailed profit analysis, use:\n"
        "`/profits` or `/profits period`\n\n"
        "**Available periods:**\n"
        "• `today` - Today's profits\n"
        "• `week` - This week's profits\n"
        "• `month` - This month's profits\n"
        "• `all` - All-time profits\n\n"
        "**Examples:**\n"
        "`/profits today`\n"
        "`/profits month`\n\n"
        "Advanced profit tracking dashboard coming soon!"
    )
    
    keyboard = [
        [InlineKeyboardButton("📊 Dashboard", callback_data="analytics_dashboard")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_analytics")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_sales_report(query):
    """Show sales report options"""
    text = (
        "📈 **Sales Reports**\n\n"
        "To generate sales reports, use:\n"
        "`/salesreport period format`\n\n"
        "**Periods:**\n"
        "• `daily` - Daily sales\n"
        "• `weekly` - Weekly summary\n"
        "• `monthly` - Monthly report\n"
        "• `yearly` - Annual overview\n\n"
        "**Formats:**\n"
        "• `text` - Simple text format\n"
        "• `csv` - Spreadsheet format\n"
        "• `pdf` - Professional report\n\n"
        "**Example:**\n"
        "`/salesreport monthly csv`"
    )
    
    keyboard = [
        [InlineKeyboardButton("💹 Profit Analysis", callback_data="analytics_profits")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_analytics")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_analytics_export(query):
    """Show analytics export options"""
    text = (
        "🔄 **Export Analytics Data**\n\n"
        "To export your shop's data, use:\n"
        "`/exportdata type format`\n\n"
        "**Data Types:**\n"
        "• `orders` - Order history\n"
        "• `products` - Product catalog\n"
        "• `users` - User data\n"
        "• `profits` - Profit records\n"
        "• `all` - Complete dataset\n\n"
        "**Formats:**\n"
        "• `csv` - Excel compatible\n"
        "• `json` - Developer friendly\n"
        "• `pdf` - Report format\n\n"
        "**Examples:**\n"
        "`/exportdata orders csv`\n"
        "`/exportdata all json`"
    )
    
    keyboard = [
        [InlineKeyboardButton("📊 Dashboard", callback_data="analytics_dashboard")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_analytics")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ============= SETTINGS FUNCTIONS =============

async def handle_settings_actions(query, data):
    """Handle all settings callback actions"""
    if data == "settings_bot":
        await show_bot_settings(query)
    elif data == "settings_admin":
        await show_admin_settings(query)
    elif data == "settings_database":
        await show_database_settings(query)
    elif data == "settings_notifications":
        await show_notification_settings(query)

async def show_bot_settings(query):
    """Show bot settings options"""
    text = (
        "⚙️ **Bot Settings**\n\n"
        "Configure your bot's behavior:\n\n"
        "**Available Commands:**\n"
        "`/setdefaultcoins amount` - Set default starting coins\n"
        "`/setmainmenu` - Customize main menu\n"
        "`/setwelcomemsg text` - Set welcome message\n"
        "`/togglemaintenance` - Enable/disable maintenance mode\n"
        "`/setmaxorders number` - Set max orders per user\n\n"
        "**Current Settings:**\n"
        "• Default Coins: 100\n"
        "• Maintenance Mode: Off\n"
        "• Max Orders: Unlimited"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔑 Admin Settings", callback_data="settings_admin")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_settings")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_admin_settings(query):
    """Show admin settings options"""
    text = (
        "🔑 **Admin Settings**\n\n"
        "Manage admin access and permissions:\n\n"
        "**Available Commands:**\n"
        "`/addadmin user_id` - Add new admin\n"
        "`/removeadmin user_id` - Remove admin access\n"
        "`/listadmins` - Show all admins\n"
        "`/setadminrole user_id role` - Set admin role\n\n"
        "**Admin Roles:**\n"
        "• `owner` - Full access\n"
        "• `manager` - Product/order management\n"
        "• `support` - User support only\n\n"
        "**Current Admins:**\n"
        "• You (Owner)\n"
        "• Use `/listadmins` for complete list"
    )
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Bot Settings", callback_data="settings_bot")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_settings")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_database_settings(query):
    """Show database settings options"""
    text = (
        "🗃️ **Database Management**\n\n"
        "Manage your bot's database:\n\n"
        "**Available Commands:**\n"
        "`/backupdb` - Create database backup\n"
        "`/dbstats` - Show database statistics\n"
        "`/cleanupdb` - Clean old/unused data\n"
        "`/optimizedb` - Optimize database performance\n\n"
        "⚠️ **Warning:**\n"
        "Database operations can take time. Always backup before major changes!\n\n"
        "**Recommendations:**\n"
        "• Backup weekly\n"
        "• Cleanup monthly\n"
        "• Optimize quarterly"
    )
    
    keyboard = [
        [InlineKeyboardButton("📢 Notifications", callback_data="settings_notifications")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_settings")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_notification_settings(query):
    """Show notification settings options"""
    text = (
        "📢 **Notification Settings**\n\n"
        "Configure admin notifications:\n\n"
        "**Available Commands:**\n"
        "`/notifications on/off` - Toggle all notifications\n"
        "`/notifyorders on/off` - New order notifications\n"
        "`/notifyusers on/off` - New user notifications\n"
        "`/notifyerrors on/off` - Error notifications\n"
        "`/setnotifychannel channel_id` - Set notification channel\n\n"
        "**Current Status:**\n"
        "• All Notifications: On\n"
        "• Order Notifications: On\n"
        "• User Notifications: On\n"
        "• Error Notifications: On\n"
        "• Notification Channel: This chat"
    )
    
    keyboard = [
        [InlineKeyboardButton("🗃️ Database", callback_data="settings_database")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_settings")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )