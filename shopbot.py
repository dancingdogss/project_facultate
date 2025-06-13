from config import TOKEN
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters
)
from handlers_user.menu import start, handle_menu, profile_cmd, deposit_ltc, categories_cmd, handle_back_buttons
from handlers_admin.products import (
    product_list,
    add_product_cmd, add_product_name, add_product_price, add_product_stock,
    add_product_category, add_product_description, cancel_add_product,
    remove_product_cmd, remove_product_name, remove_product_by_id_cmd, remove_category_cmd,
    edit_product_cmd, edit_product_name, edit_product_field, edit_product_value,
    add_product_photo_cmd, receive_product_photo, save_product_photo, locationphotos_cmd,
    add_location_photo_cmd, receive_location_photo_bulk, save_location_photo, done_adding_location_photos,
    show_location_photos_cmd, send_location_photos,
    ADD_NAME, ADD_PRICE, ADD_STOCK, ADD_CATEGORY, ADD_DESCRIPTION,
    REMOVE_NAME, EDIT_NAME, EDIT_FIELD, EDIT_VALUE,
    PHOTO_PRODUCT_NAME, PHOTO_RECEIVE,
    LOCATION_PRODUCT_NAME, LOCATION_RECEIVE, LOCATION_DONE,
    SHOW_LOCATION_PHOTOS
)
from handlers_admin.orders import (
    all_orders, set_order_status, export_orders, deliveries_cmd, findorder_cmd, export_deliveries, removedelivery_cmd
)
from handlers_admin.analytics import (
    profits_cmd, export_profits, addcoins_cmd, setcoins_cmd, topusers_cmd, dashboard_cmd, users_cmd
)
from handlers_user.orders import (
    handle_order, receive_quantity, confirm_order, cancel_order,
    myorders_cmd, filter_orders_callback, back_to_orders_filters, simulate_deposit,
    ORDER_QUANTITY, ORDER_CONFIRM
)
from handlers_user.products import (
    show_category_products, product_details_callback, back_to_categories_callback, back_to_menu_callback
)
from handlers_user.balance import check_balance, balance_cmd
from handlers_user.search import search_cmd

from db import init_db
import sys
import asyncio

if sys.platform.startswith("win") and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    await init_db()
    app = Application.builder().token(TOKEN).build()

    # --- Conversation Handlers (register these FIRST) ---

    add_product_conv = ConversationHandler(
        entry_points=[CommandHandler("addproduct", add_product_cmd)],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_name)],
            ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price)],
            ADD_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_stock)],
            ADD_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_category)],
            ADD_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_description)],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_product)],
    )
    app.add_handler(add_product_conv)

    remove_product_conv = ConversationHandler(
        entry_points=[CommandHandler("removeproduct", remove_product_cmd)],
        states={
            REMOVE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_product_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_product)],
    )
    app.add_handler(remove_product_conv)

    edit_product_conv = ConversationHandler(
        entry_points=[CommandHandler("editproduct", edit_product_cmd)],
        states={
            EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_name)],
            EDIT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_field)],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_product)],
    )
    app.add_handler(edit_product_conv)

    add_location_photo_conv = ConversationHandler(
        entry_points=[CommandHandler("addlocationphoto", add_location_photo_cmd)],
        states={
            LOCATION_PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_location_photo_bulk)],
            LOCATION_RECEIVE: [
                MessageHandler(filters.PHOTO, save_location_photo),
                CommandHandler("done", done_adding_location_photos)
            ],
        },
        fallbacks=[CommandHandler("cancel", done_adding_location_photos)],
    )
    app.add_handler(add_location_photo_conv)

    # --- Order Conversation Handler ---
    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_order, pattern="^order_")],
        states={
            ORDER_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_quantity)],
            ORDER_CONFIRM: [
                CallbackQueryHandler(confirm_order, pattern="^confirm_order$"),
                CallbackQueryHandler(cancel_order, pattern="^cancel_order$")
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_order, pattern="^cancel_order$")],
    )
    app.add_handler(order_conv)

    # --- Command Handlers ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("productlist", product_list))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("allorders", all_orders))
    app.add_handler(CommandHandler("setorderstatus", set_order_status))
    app.add_handler(CommandHandler("exportorders", export_orders))
    app.add_handler(CommandHandler("deliveries", deliveries_cmd))
    app.add_handler(CommandHandler("findorder", findorder_cmd))
    app.add_handler(CommandHandler("exportdeliveries", export_deliveries))
    app.add_handler(CommandHandler("removedelivery", removedelivery_cmd))
    app.add_handler(CommandHandler("removeproductid", remove_product_by_id_cmd))
    app.add_handler(CommandHandler("removecategory", remove_category_cmd))
    app.add_handler(CommandHandler("profits", profits_cmd))
    app.add_handler(CommandHandler("exportprofits", export_profits))
    app.add_handler(CommandHandler("addcoins", addcoins_cmd))
    app.add_handler(CommandHandler("setcoins", setcoins_cmd))
    app.add_handler(CommandHandler("topusers", topusers_cmd))
    app.add_handler(CommandHandler("dashboard", dashboard_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("myorders", myorders_cmd))
    app.add_handler(CommandHandler("categories", categories_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("deposit_ltc", deposit_ltc))
    app.add_handler(CommandHandler("locationphotos", locationphotos_cmd))

    # --- CallbackQuery Handlers ---
    app.add_handler(CallbackQueryHandler(product_details_callback, pattern="^details_"))
    app.add_handler(CallbackQueryHandler(back_to_categories_callback, pattern="^back_to_categories$"))
    app.add_handler(CallbackQueryHandler(back_to_menu_callback, pattern="^back_to_menu$"))

    # --- Fallback: Main Menu Handler ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

    print("Bot running... Press CTRL+C to stop.")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())