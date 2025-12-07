from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from handlers_admin.auth import require_admin_auth
from db import SessionLocal
from utils.db_utils import get_all_products, get_product_by_id, remove_product, get_orders, get_order_by_id, update_order_status
from handlers_admin.orders import fulfill_order_and_deliver_photos
import asyncio

# Conversation states
AWAITING_PRODUCT_EDIT = 1
AWAITING_ORDER_STATUS = 2

@require_admin_auth
async def enhanced_product_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show interactive product list"""
    query = update.callback_query
    await query.answer()
    
    async with SessionLocal() as session:
        products = await get_all_products(session)
        
        if not products:
            await query.edit_message_text(
                "📦 **No Products Found**\n\nYour shop is empty. Add some products first!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("➕ Add First Product", callback_data="product_add_new"),
                    InlineKeyboardButton("🔙 Back", callback_data="admin_products")
                ]]),
                parse_mode="Markdown"
            )
            return
        
        text = "📦 **Product List**\n\nSelect a product to manage:\n\n"
        
        keyboard = []
        for product in products:
            stock_status = "🔴" if product.stock < 5 else "🟢"
            button_text = f"{stock_status} {product.name} (${product.price})"
            keyboard.append([InlineKeyboardButton(
                button_text, 
                callback_data=f"manage_product_{product.id}"
            )])
        
        keyboard.append([
            InlineKeyboardButton("➕ Add New Product", callback_data="product_add_new"),
            InlineKeyboardButton("🔙 Back", callback_data="admin_products")
        ])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

@require_admin_auth
async def manage_single_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show management options for a specific product"""
    query = update.callback_query
    await query.answer()
    
    product_id = query.data.replace("manage_product_", "")
    
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await query.edit_message_text("❌ Product not found.")
            return
        
        from utils.db_utils import count_unused_location_photos
        unused_photos = await count_unused_location_photos(session, product_id)
        
        stock_status = "🔴 LOW STOCK" if product.stock < 5 else "🟢 In Stock"
        
        text = (
            f"📦 **Product Management**\n\n"
            f"**Name:** {product.name}\n"
            f"**Price:** ${product.price}\n"
            f"**Stock:** {product.stock} ({stock_status})\n"
            f"**Category:** {product.category or 'N/A'}\n"
            f"**Location Photos:** {unused_photos} available\n"
            f"**Description:** {product.description or 'No description'}\n"
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

@require_admin_auth
async def enhanced_order_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced order management interface"""
    query = update.callback_query
    await query.answer()
    
    async with SessionLocal() as session:
        orders = await get_orders(session, limit=20)
        
        if not orders:
            await query.edit_message_text(
                "📋 **No Orders Found**\n\nNo orders have been placed yet.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin_orders")
                ]]),
                parse_mode="Markdown"
            )
            return
        
        # Group orders by status
        pending_orders = [o for o in orders if o.status == "pending"]
        completed_orders = [o for o in orders if o.status == "completed"]
        cancelled_orders = [o for o in orders if o.status == "cancelled"]
        
        text = (
            f"📋 **Order Management**\n\n"
            f"📊 **Summary:**\n"
            f"⏳ Pending: {len(pending_orders)}\n"
            f"✅ Completed: {len(completed_orders)}\n"
            f"❌ Cancelled: {len(cancelled_orders)}\n\n"
            f"Select orders to manage:"
        )
        
        keyboard = []
        
        # Show pending orders first
        if pending_orders:
            keyboard.append([InlineKeyboardButton("⏳ Pending Orders", callback_data="orders_show_pending")])
        if completed_orders:
            keyboard.append([InlineKeyboardButton("✅ Completed Orders", callback_data="orders_show_completed")])
        if cancelled_orders:
            keyboard.append([InlineKeyboardButton("❌ Cancelled Orders", callback_data="orders_show_cancelled")])
        
        keyboard.extend([
            [InlineKeyboardButton("🔍 Search Orders", callback_data="orders_search"),
             InlineKeyboardButton("📊 Export Data", callback_data="orders_export_new")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_orders")]
        ])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

@require_admin_auth
async def show_orders_by_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show orders filtered by status"""
    query = update.callback_query
    await query.answer()
    
    status_map = {
        "orders_show_pending": "pending",
        "orders_show_completed": "completed", 
        "orders_show_cancelled": "cancelled"
    }
    
    status = status_map.get(query.data)
    if not status:
        return
    
    async with SessionLocal() as session:
        orders = await get_orders(session, limit=50)
        filtered_orders = [o for o in orders if o.status == status]
        
        status_emoji = {"pending": "⏳", "completed": "✅", "cancelled": "❌"}
        status_name = {"pending": "Pending", "completed": "Completed", "cancelled": "Cancelled"}
        
        text = f"{status_emoji[status]} **{status_name[status]} Orders** ({len(filtered_orders)})\n\n"
        
        keyboard = []
        
        for order in filtered_orders[:10]:  # Show first 10
            order_date = order.created_at.strftime("%m/%d %H:%M")
            button_text = f"{order.product_name} - User {order.user_id} ({order_date})"
            keyboard.append([InlineKeyboardButton(
                button_text[:60] + "..." if len(button_text) > 60 else button_text,
                callback_data=f"manage_order_{order.id}"
            )])
        
        if len(filtered_orders) > 10:
            keyboard.append([InlineKeyboardButton(f"... and {len(filtered_orders) - 10} more", callback_data=f"orders_show_{status}_all")])
        
        keyboard.append([
            InlineKeyboardButton("🔄 Refresh", callback_data=f"orders_show_{status}"),
            InlineKeyboardButton("🔙 Back", callback_data="orders_view_all")
        ])
        
        if not filtered_orders:
            text += f"No {status} orders found."
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

@require_admin_auth
async def manage_single_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage a specific order"""
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.replace("manage_order_", "")
    
    async with SessionLocal() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await query.edit_message_text("❌ Order not found.")
            return
        
        order_date = order.created_at.strftime("%Y-%m-%d %H:%M:%S")
        status_emoji = {"pending": "⏳", "completed": "✅", "cancelled": "❌"}
        
        text = (
            f"📋 **Order Details**\n\n"
            f"**Order ID:** `{order.id}`\n"
            f"**User ID:** {order.user_id}\n"
            f"**Product:** {order.product_name}\n"
            f"**Quantity:** {order.quantity}\n"
            f"**Status:** {status_emoji.get(order.status, '')} {order.status.title()}\n"
            f"**Date:** {order_date}\n"
        )
        
        keyboard = []
        
        # Status change buttons
        if order.status == "pending":
            keyboard.extend([
                [InlineKeyboardButton("✅ Mark Completed", callback_data=f"complete_order_{order_id}"),
                 InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_order_{order_id}")],
            ])
        elif order.status == "completed":
            keyboard.append([InlineKeyboardButton("🔄 Mark Pending", callback_data=f"pending_order_{order_id}")])
        elif order.status == "cancelled":
            keyboard.append([InlineKeyboardButton("🔄 Mark Pending", callback_data=f"pending_order_{order_id}")])
        
        keyboard.extend([
            [InlineKeyboardButton("👤 View User", callback_data=f"view_user_{order.user_id}"),
             InlineKeyboardButton("📦 View Product", callback_data=f"view_product_{order.product_id}")],
            [InlineKeyboardButton("🔙 Back to Orders", callback_data="orders_view_all")]
        ])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

@require_admin_auth
async def quick_order_status_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quickly change order status"""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split("_")
    new_status = data_parts[0]  # complete, cancel, pending
    order_id = "_".join(data_parts[2:])  # handle UUID with underscores
    
    async with SessionLocal() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await query.edit_message_text("❌ Order not found.")
            return
        
        old_status = order.status
        
        # Update order status
        if new_status == "complete":
            if old_status == "completed":
                await query.edit_message_text("❌ Order is already completed.")
                return
            
            # Complete the order and deliver photos
            result = await fulfill_order_and_deliver_photos(session, order, context)
            if result == "no_photos":
                await query.edit_message_text(
                    f"⚠️ **Order Completed - No Photos Available**\n\n"
                    f"Order {order.id[:8]}... has been marked as completed, but no location photos were available for this product.\n\n"
                    f"The user has been notified that the order is ready for pickup.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Orders", callback_data="orders_view_all")
                    ]]),
                    parse_mode="Markdown"
                )
                return
            elif result == "success":
                await query.edit_message_text(
                    f"✅ **Order Completed Successfully**\n\n"
                    f"Order {order.id[:8]}... has been completed and the pickup location photo has been sent to the user.\n\n"
                    f"The user has been notified about their order completion.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Orders", callback_data="orders_view_all")
                    ]]),
                    parse_mode="Markdown"
                )
                return
        
        elif new_status == "cancel":
            if old_status == "cancelled":
                await query.edit_message_text("❌ Order is already cancelled.")
                return
            result = await update_order_status(session, order_id, "cancelled")
        
        elif new_status == "pending":
            result = await update_order_status(session, order_id, "pending")
        
        if result:
            status_emoji = {"pending": "⏳", "completed": "✅", "cancelled": "❌"}
            await query.edit_message_text(
                f"{status_emoji.get(new_status, '')} **Order Status Updated**\n\n"
                f"Order {order.id[:8]}... has been marked as {new_status}.\n\n"
                f"The user will be automatically notified of this change.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Orders", callback_data="orders_view_all")
                ]]),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ Failed to update order status.")

# Enhanced management callback handler
async def enhanced_management_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle enhanced management callbacks"""
    query = update.callback_query
    data = query.data
    
    if data == "product_list":
        await enhanced_product_list(update, context)
    elif data.startswith("manage_product_"):
        await manage_single_product(update, context)
    elif data == "orders_view_all":
        await enhanced_order_management(update, context)
    elif data in ["orders_show_pending", "orders_show_completed", "orders_show_cancelled"]:
        await show_orders_by_status(update, context)
    elif data.startswith("manage_order_"):
        await manage_single_order(update, context)
    elif data.startswith(("complete_order_", "cancel_order_", "pending_order_")):
        await quick_order_status_change(update, context)