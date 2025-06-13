import os
from datetime import datetime

async def save_delivered_photo_to_folder(bot, file_id, product_name, order_id, user_id):
    folder = "delivered_photos"
    os.makedirs(folder, exist_ok=True)
    dt_str = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{product_name}_{order_id}_{user_id}_{dt_str}.jpg"
    path = os.path.join(folder, filename)
    file = await bot.get_file(file_id)
    await file.download_to_drive(path)
    return path