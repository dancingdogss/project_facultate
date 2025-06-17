import asyncio
import os
from telegram import Bot
from db import SessionLocal
from sqlalchemy.future import select
from db import DeliveredPhoto, Order, Product

BOT_TOKEN = "7091591495:AAE6XrbI0a7g5_i9zS6vWi3_zY_U3HLnwUA"  # <-- your bot token
SAVE_FOLDER = "delivered_photos"  # Folder to save images

async def main():
    bot = Bot(token=BOT_TOKEN)
    os.makedirs(SAVE_FOLDER, exist_ok=True)

    async with SessionLocal() as session:
        # Get all delivered photos
        result = await session.execute(select(DeliveredPhoto))
        photos = result.scalars().all()

        for photo in photos:
            # Get order and product info for naming
            order_result = await session.execute(select(Order).where(Order.id == photo.order_id))
            order = order_result.scalar_one_or_none()
            product_result = await session.execute(select(Product).where(Product.id == photo.product_id))
            product = product_result.scalar_one_or_none()

            if not order or not product:
                print(f"Skipping photo {photo.id}: missing order or product.")
                continue

            # Build filename
            dt_str = photo.delivered_at.strftime("%Y%m%d_%H%M%S")
            filename = f"{product.name}_{order.id}_{order.user_id}_{order.quantity}_{dt_str}.png"
            filepath = os.path.join(SAVE_FOLDER, filename)

            # Download the photo from Telegram
            try:
                file = await bot.get_file(photo.file_id)
                await file.download_to_drive(filepath)
                print(f"Saved: {filepath}")
            except Exception as e:
                print(f"Failed to download photo {photo.id}: {e}")

    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())