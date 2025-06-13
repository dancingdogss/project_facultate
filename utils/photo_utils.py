import os
from telegram import Bot
from db import SessionLocal, Order, Product
from sqlalchemy.future import select

BOT_TOKEN = "7091591495:AAE6XrbI0a7g5_i9zS6vWi3_zY_U3HLnwUA"
SAVE_FOLDER = "delivered_photos"

# Ensure the folder exists once at import
os.makedirs(SAVE_FOLDER, exist_ok=True)

async def save_delivered_photo_to_folder(photo):
    """
    Downloads a delivered photo from Telegram and saves it locally with a descriptive filename.
    """
    print(f"Saving delivered photo {photo.id}...")  # Debug print

    bot = Bot(token=BOT_TOKEN)

    async with SessionLocal() as session:
        # Get order and product info for naming
        order_result = await session.execute(select(Order).where(Order.id == photo.order_id))
        order = order_result.scalar_one_or_none()
        product_result = await session.execute(select(Product).where(Product.id == photo.product_id))
        product = product_result.scalar_one_or_none()

        if not order or not product:
            print(f"Skipping photo {photo.id}: missing order or product.")
            return

        # Use delivered_at if available, else current time
        dt = getattr(photo, "delivered_at", None)
        from datetime import datetime
        dt_str = (dt or datetime.utcnow()).strftime("%Y%m%d_%H%M%S")

        filename = f"{product.name}_{order.id}_{order.user_id}_{order.quantity}_{dt_str}.png"
        filepath = os.path.join(SAVE_FOLDER, filename)

        try:
            file = await bot.get_file(photo.file_id)
            await file.download_to_drive(filepath)
            print(f"Saved: {filepath}")
        except Exception as e:
            print(f"Failed to download photo {photo.id}: {e}")