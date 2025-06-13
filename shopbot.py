import sys
import asyncio

if sys.platform.startswith("win") and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

from config import TOKEN
from handlers_user import (
    start, handle_menu, handle_order, receive_quantity, confirm_order, cancel_confirm, cancel_order,
    product_details, profile_cmd, deposit_ltc, check_balance, balance_cmd, categories_cmd, show_category, search_cmd, ORDER_QUANTITY, ORDER_CONFIRM,
    handle_back_buttons, filter_orders_callback, myorders_cmd, back_to_orders_filters, simulate_deposit
)
from handlers_admin import (
    add_product, remove_product, edit_product, product_list, export_orders, all_orders,
    set_order_status, addcoins_cmd, setcoins_cmd, topusers_cmd, dashboard_cmd,
    deliveries_cmd, findorder_cmd, export_deliveries, removedelivery_cmd,
    profits_cmd, export_profits
)
from handlers_admin.products import (
    add_product_cmd, remove_product_cmd, edit_product_cmd, product_list,
    add_product_photo, receive_product_photo, ADD_PRODUCT_PHOTO,
    add_location_photo_cmd, receive_location_photo_bulk, done_adding_location_photos, ADD_LOCATION_PHOTO_BULK,
    show_location_photos
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ConversationHandler
)
from db import init_db

async def main():
    await init_db()  # Initialize the database

    app = Application.builder().token(TOKEN).build()

    # --- User Order Conversation ---
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_order, pattern="^order_")],
        states={
            ORDER_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_quantity)],
            ORDER_CONFIRM: [
                CallbackQueryHandler(confirm_order, pattern="^confirm_order$"),
                CallbackQueryHandler(cancel_confirm, pattern="^cancel_order$")
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_order),
            CallbackQueryHandler(handle_back_buttons, pattern="^back_to_"),
        ],
    )

    # --- Admin: Add Product Photo Conversation ---
    add_product_photo_conv = ConversationHandler(
        entry_points=[CommandHandler("addproductphoto", add_product_photo)],
        states={
            ADD_PRODUCT_PHOTO: [MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, receive_product_photo)],
        },
        fallbacks=[],
    )

    # --- Admin: Bulk Add Location Photo Conversation ---
    add_location_photo_bulk_conv = ConversationHandler(
        entry_points=[CommandHandler("addlocationphoto", add_location_photo_cmd)],
        states={
            ADD_LOCATION_PHOTO_BULK: [
                MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, receive_location_photo_bulk),
                CommandHandler("done", done_adding_location_photos),
            ],
        },
        fallbacks=[CommandHandler("cancel", done_adding_location_photos)],
    )

    # --- Register Handlers ---
    # User
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.add_handler(CallbackQueryHandler(product_details, pattern="^details_"))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("myorders", myorders_cmd))
    app.add_handler(CallbackQueryHandler(filter_orders_callback, pattern="^filter_orders_"))
    app.add_handler(CallbackQueryHandler(back_to_orders_filters, pattern="^back_to_orders_filters$"))
    app.add_handler(CallbackQueryHandler(handle_back_buttons, pattern="^back_to_"))
    app.add_handler(CommandHandler("categories", categories_cmd))
    app.add_handler(CallbackQueryHandler(show_category, pattern="^cat_"))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("deposit_ltc", deposit_ltc))
    app.add_handler(CallbackQueryHandler(check_balance, pattern="^check_balance_"))
    app.add_handler(CallbackQueryHandler(simulate_deposit, pattern="^simulate_deposit$"))

    # Admin
    app.add_handler(CommandHandler("addproduct", add_product_cmd))
    app.add_handler(CommandHandler("removeproduct", remove_product_cmd))
    app.add_handler(CommandHandler("editproduct", edit_product_cmd))
    app.add_handler(CommandHandler("productlist", product_list))
    app.add_handler(add_product_photo_conv)
    app.add_handler(add_location_photo_bulk_conv)
    app.add_handler(CommandHandler("showlocationphotos", show_location_photos))
    app.add_handler(CommandHandler("exportorders", export_orders))
    app.add_handler(CommandHandler("allorders", all_orders))
    app.add_handler(CommandHandler("setorderstatus", set_order_status))
    app.add_handler(CommandHandler("deliveries", deliveries_cmd))
    app.add_handler(CommandHandler("removedelivery", removedelivery_cmd))
    app.add_handler(CommandHandler("exportdeliveries", export_deliveries))
    app.add_handler(CommandHandler("findorder", findorder_cmd))
    app.add_handler(CommandHandler("profits", profits_cmd))
    app.add_handler(CommandHandler("exportprofits", export_profits))
    app.add_handler(CommandHandler("addcoins", addcoins_cmd))
    app.add_handler(CommandHandler("setcoins", setcoins_cmd))
    app.add_handler(CommandHandler("topusers", topusers_cmd))
    app.add_handler(CommandHandler("dashboard", dashboard_cmd))

    print("Bot running... Press CTRL+C to stop.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())