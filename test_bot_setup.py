"""
Test script to verify the bot structure and admin interface
"""

import asyncio
from telegram.ext import ApplicationBuilder
from config import TOKEN as BOT_TOKEN

async def test_bot_setup():
    """Test bot token and basic setup"""
    try:
        # Create application
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Try to get bot info
        bot_info = await application.bot.get_me()
        print(f"✅ Bot connected successfully!")
        print(f"Bot name: {bot_info.first_name}")
        print(f"Bot username: @{bot_info.username}")
        print(f"Bot ID: {bot_info.id}")
        
        # Check if we can import all handlers
        from handlers_admin.unified_interface import unified_admin_callback_handler
        from handlers_admin.interface import admin_panel
        from handlers_user.orders import create_order
        print("✅ All handlers imported successfully!")
        
        await application.stop()
        
    except Exception as e:
        print(f"❌ Bot setup failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot_setup())