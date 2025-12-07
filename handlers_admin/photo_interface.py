from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from handlers_admin.auth import require_admin_auth
from db import SessionLocal
from utils.db_utils import get_all_products, get_location_photos_by_product, get_product_by_id, add_location_photo, count_unused_location_photos
import uuid

# Conversation states
AWAITING_LOCATION_PHOTOS = 1

@require_admin_auth
async def handle_product_selected_for_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle product selection for photo operations"""
    query = update.callback_query
    await query.answer()
    
    product_id = query.data.replace("product_selected_", "")
    action = context.user_data.get("photo_action")
    
    async with SessionLocal() as session:
        product = await get_product_by_id(session, product_id)
        if not product:
            await query.edit_message_text("❌ Product not found.")
            return
        
        if action == "photo_show_location":
            await show_location_photos_interactive(query, session, product)
        elif action == "photo_add_location":
            await start_add_location_photos_interactive(query, session, product, context)

async def show_location_photos_interactive(query, session, product):
    """Show location photos with interactive interface"""
    photos = await get_location_photos_by_product(session, product.id)
    unused_photos = [p for p in photos if not p.is_delivered]
    used_photos = [p for p in photos if p.is_delivered]
    
    text = f"📸 **Location Photos for {product.name}**\n\n"
    text += f"📊 **Summary:**\n"
    text += f"• Total photos: {len(photos)}\n"
    text += f"• Available (unused): {len(unused_photos)}\n"
    text += f"• Used (delivered): {len(used_photos)}\n\n"
    
    if unused_photos:
        text += "🟢 **Available Photos:**\n"
        for i, photo in enumerate(unused_photos[:5], 1):  # Show first 5
            caption = photo.caption[:30] + "..." if photo.caption and len(photo.caption) > 30 else photo.caption or "No caption"
            text += f"{i}. {caption}\n"
        
        if len(unused_photos) > 5:
            text += f"... and {len(unused_photos) - 5} more\n"
    else:
        text += "❌ No available photos for this product.\n"
    
    keyboard = []
    
    if unused_photos:
        # Add buttons to view photos
        photo_buttons = []
        for i, photo in enumerate(unused_photos[:6]):  # Max 6 buttons per row
            photo_buttons.append(InlineKeyboardButton(f"📸 {i+1}", callback_data=f"view_photo_{photo.id}"))
        
        # Split into rows of 3
        for i in range(0, len(photo_buttons), 3):
            keyboard.append(photo_buttons[i:i+3])
    
    keyboard.append([
        InlineKeyboardButton("➕ Add More Photos", callback_data=f"photo_add_more_{product.id}"),
        InlineKeyboardButton("🔄 Refresh", callback_data=f"photo_refresh_{product.id}")
    ])
    keyboard.append([InlineKeyboardButton("🔙 Back to Photo Management", callback_data="admin_photos")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def start_add_location_photos_interactive(query, session, product, context):
    """Start interactive location photo addition"""
    context.user_data["selected_product_id"] = product.id
    context.user_data["selected_product_name"] = product.name
    context.user_data["photo_count"] = 0
    
    unused_count = await count_unused_location_photos(session, product.id)
    
    text = (
        f"📸 **Add Location Photos**\n\n"
        f"**Product:** {product.name}\n"
        f"**Current unused photos:** {unused_count}\n\n"
        f"📝 **Instructions:**\n"
        f"• Send photos one by one or multiple at once\n"
        f"• Each photo should show a pickup location\n"
        f"• Add captions to describe the location\n"
        f"• Use /done when finished\n\n"
        f"🏁 **Start sending your location photos now!**"
    )
    
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data="admin_photos")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return AWAITING_LOCATION_PHOTOS

@require_admin_auth
async def receive_location_photos_interactive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and save location photos interactively"""
    if not update.message.photo:
        await update.message.reply_text("❌ Please send a photo or use /done to finish.")
        return AWAITING_LOCATION_PHOTOS
    
    product_id = context.user_data.get("selected_product_id")
    product_name = context.user_data.get("selected_product_name")
    
    if not product_id:
        await update.message.reply_text("❌ Session expired. Please start again.")
        return ConversationHandler.END
    
    # Get the largest photo
    photo = update.message.photo[-1]
    caption = update.message.caption or ""
    
    async with SessionLocal() as session:
        # Save photo to database
        await add_location_photo(session, product_id, photo.file_id, caption)
        
        # Update counter
        context.user_data["photo_count"] = context.user_data.get("photo_count", 0) + 1
        count = context.user_data["photo_count"]
        
        # Get updated total
        unused_count = await count_unused_location_photos(session, product_id)
    
    # Send confirmation with inline keyboard
    keyboard = [
        [InlineKeyboardButton("✅ Done Adding", callback_data=f"done_adding_photos_{product_id}"),
         InlineKeyboardButton("🔍 View Photos", callback_data=f"view_added_photos_{product_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="admin_photos")]
    ]
    
    await update.message.reply_text(
        f"✅ **Photo {count} saved!**\n\n"
        f"📸 Photos added this session: {count}\n"
        f"📊 Total unused photos for {product_name}: {unused_count}\n\n"
        f"Continue sending photos or click Done when finished.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return AWAITING_LOCATION_PHOTOS

@require_admin_auth
async def done_adding_photos_interactive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish adding photos and show summary"""
    query = update.callback_query
    await query.answer()
    
    product_id = context.user_data.get("selected_product_id")
    product_name = context.user_data.get("selected_product_name")
    count = context.user_data.get("photo_count", 0)
    
    async with SessionLocal() as session:
        unused_count = await count_unused_location_photos(session, product_id)
    
    text = (
        f"🎉 **Photo Upload Complete!**\n\n"
        f"**Product:** {product_name}\n"
        f"**Photos added:** {count}\n"
        f"**Total unused photos:** {unused_count}\n\n"
        f"✅ All photos have been saved successfully!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔍 View All Photos", callback_data=f"product_selected_{product_id}"),
         InlineKeyboardButton("➕ Add More", callback_data=f"photo_add_more_{product_id}")],
        [InlineKeyboardButton("🔙 Back to Photo Management", callback_data="admin_photos")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END

# Enhanced photo management callback handler
async def enhanced_photo_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle enhanced photo management callbacks"""
    query = update.callback_query
    data = query.data
    
    if data.startswith("product_selected_"):
        await handle_product_selected_for_photos(update, context)
    elif data.startswith("photo_add_more_"):
        product_id = data.replace("photo_add_more_", "")
        async with SessionLocal() as session:
            product = await get_product_by_id(session, product_id)
            if product:
                context.user_data["photo_action"] = "photo_add_location" 
                await start_add_location_photos_interactive(query, session, product, context)
    elif data.startswith("photo_refresh_"):
        product_id = data.replace("photo_refresh_", "")
        async with SessionLocal() as session:
            product = await get_product_by_id(session, product_id)
            if product:
                await show_location_photos_interactive(query, session, product)
    elif data.startswith("done_adding_photos_"):
        await done_adding_photos_interactive(update, context)
    elif data.startswith("view_photo_"):
        await view_single_photo(update, context)

async def view_single_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View a single location photo"""
    query = update.callback_query
    await query.answer()
    
    photo_id = query.data.replace("view_photo_", "")
    
    async with SessionLocal() as session:
        from sqlalchemy import select
        from db import LocationPhoto, Product
        
        result = await session.execute(
            select(LocationPhoto, Product)
            .join(Product)
            .where(LocationPhoto.id == photo_id)
        )
        row = result.first()
        
        if not row:
            await query.edit_message_text("❌ Photo not found.")
            return
        
        photo, product = row
        
        caption = (
            f"📸 **Location Photo**\n\n"
            f"**Product:** {product.name}\n"
            f"**Status:** {'🔴 Used' if photo.is_delivered else '🟢 Available'}\n"
            f"**Caption:** {photo.caption or 'No caption'}\n"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=f"product_selected_{product.id}")]]
        
        try:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=photo.file_id,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            await query.delete_message()
        except Exception as e:
            await query.edit_message_text(f"❌ Could not load photo: {e}")

# Conversation handler for interactive photo management
interactive_photo_conv = ConversationHandler(
    entry_points=[],  # We'll trigger this through callbacks
    states={
        AWAITING_LOCATION_PHOTOS: [
            MessageHandler(filters.PHOTO, receive_location_photos_interactive),
            CallbackQueryHandler(done_adding_photos_interactive, pattern="^done_adding_photos_"),
            CallbackQueryHandler(enhanced_photo_callback_handler),
        ],
    },
    fallbacks=[CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^admin_photos$")],
    per_chat=True,
    per_user=True,
)