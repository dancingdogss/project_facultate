from config import TOKEN
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters
)
from handlers_admin.products import (
    product_list,
    add_product_cmd, add_product_name, add_product_price, add_product_stock,
    add_product_category, add_product_description, cancel_add_product,
    remove_product_cmd, remove_product_id,
    edit_product_cmd, edit_product_id, edit_product_field, edit_product_value,
    add_product_photo_cmd, receive_product_photo, save_product_photo,
    add_location_photo_cmd, receive_location_photo_bulk, save_location_photo_bulk, done_adding_location_photos,
    show_location_photos_cmd, send_location_photos, lowstock_cmd,
    ADD_NAME, ADD_PRICE, ADD_STOCK, ADD_CATEGORY, ADD_DESCRIPTION,
    EDIT_FIELD, EDIT_ID, EDIT_VALUE, REMOVE_ID,
    PHOTO_PRODUCT_ID, PHOTO_RECEIVE,
    LOCATION_PRODUCT_ID, LOCATION_RECEIVE,
    SHOW_LOCATION_PHOTOS,
)
from handlers_admin.orders import (
    all_orders, export_orders, filter_orders_callback, show_orders, deliveries_cmd, findorder_cmd, export_deliveries, removedelivery_cmd,
    set_order_status_cmd, set_order_status_id, set_order_status_status,
    SET_ORDER_ID, SET_ORDER_STATUS,
)
from handlers_admin.analytics import (
    profits_cmd, export_profits, addcoins_cmd, setcoins_cmd, topusers_cmd, dashboard_cmd
)
from handlers_user.menu import start, handle_menu, profile_cmd, deposit_ltc, categories_cmd, handle_back_buttons
from handlers_user.orders import (
    handle_order, receive_quantity, confirm_order, cancel_order, orderstatus_cmd, myorders_cmd, back_to_orders_filters, simulate_deposit,
    ORDER_QUANTITY, ORDER_CONFIRM
)
from handlers_user.products import (
    show_category_products, categories_cmd, product_details_callback, back_to_categories_callback, back_to_menu_callback
)
from handlers_user.balance import check_balance, balance_cmd
from handlers_user.search import search_cmd

from db import init_db
import sys
import asyncio

if sys.platform.startswith("win") and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# --- Combined handler for filter input and menu ---
async def filter_or_menu(update, context):
    # Check if we're in the /allorders filter flow
    if context.user_data.get("awaiting_filter_value"):
        print("filter_value_input logic running")
        filter_type = context.user_data.get("filter_type")
        value = update.message.text.strip()
        await show_orders(update, context, filter_type, value)
        context.user_data.pop("awaiting_filter_value", None)
        context.user_data.pop("filter_type", None)
    else:
        print("handle_menu logic running")
        await handle_menu(update, context)

async def main():
    await init_db()
    app = Application.builder().token(TOKEN).build()

    # --- Add Product Conversation Handler ---
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

    # --- Edit Product Conversation Handler ---
    edit_product_conv = ConversationHandler(
        entry_points=[CommandHandler("editproduct", edit_product_cmd)],
        states={
            EDIT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_id)],
            EDIT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_field)],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_value)],
        },
        fallbacks=[],
    )
    app.add_handler(edit_product_conv)

    # --- Remove Product Conversation Handler ---
    remove_product_conv = ConversationHandler(
        entry_points=[CommandHandler("removeproduct", remove_product_cmd)],
        states={
            REMOVE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_product_id)],
        },
        fallbacks=[],
    )
    app.add_handler(remove_product_conv)

    # --- Add Product Photo Conversation Handler ---
    add_product_photo_conv = ConversationHandler(
        entry_points=[CommandHandler("addproductphoto", add_product_photo_cmd)],
        states={
            PHOTO_PRODUCT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_product_photo)],
            PHOTO_RECEIVE: [MessageHandler(filters.PHOTO, save_product_photo)],
        },
        fallbacks=[],
    )
    app.add_handler(add_product_photo_conv)

    # --- Add Location Photos Conversation Handler ---
    add_location_photo_conv = ConversationHandler(
        entry_points=[CommandHandler("addlocationphoto", add_location_photo_cmd)],
        states={
            LOCATION_PRODUCT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_location_photo_bulk)],
            LOCATION_RECEIVE: [
                MessageHandler(filters.PHOTO, save_location_photo_bulk),
                CommandHandler("done", done_adding_location_photos),
            ],
        },
        fallbacks=[CommandHandler("done", done_adding_location_photos)],
    )
    app.add_handler(add_location_photo_conv)

    # --- Show Location Photos Conversation Handler ---
    show_location_photos_conv = ConversationHandler(
        entry_points=[CommandHandler("showlocationphotos", show_location_photos_cmd)],
        states={
            SHOW_LOCATION_PHOTOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_location_photos)],
        },
        fallbacks=[],
    )
    app.add_handler(show_location_photos_conv)

    # --- Set Order Status Conversation Handler ---
    set_order_status_conv = ConversationHandler(
        entry_points=[CommandHandler("setorderstatus", set_order_status_cmd)],
        states={
            SET_ORDER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_order_status_id)],
            SET_ORDER_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_order_status_status)],
        },
        fallbacks=[],
    )
    app.add_handler(set_order_status_conv)

    # --- Order Conversation Handler (User) ---
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

    # --- Register Admin Product Commands ---
    app.add_handler(CommandHandler("productlist", product_list))

    # --- Register Admin Order Commands ---
    app.add_handler(CommandHandler("allorders", all_orders))
    app.add_handler(CommandHandler("exportorders", export_orders))
    app.add_handler(CommandHandler("deliveries", deliveries_cmd))
    app.add_handler(CommandHandler("findorder", findorder_cmd))
    app.add_handler(CommandHandler("exportdeliveries", export_deliveries))
    app.add_handler(CommandHandler("removedelivery", removedelivery_cmd))
    app.add_handler(CommandHandler("lowstock", lowstock_cmd))

    # --- Register Admin Analytics Commands ---
    app.add_handler(CommandHandler("profits", profits_cmd))
    app.add_handler(CommandHandler("exportprofits", export_profits))
    app.add_handler(CommandHandler("addcoins", addcoins_cmd))
    app.add_handler(CommandHandler("setcoins", setcoins_cmd))
    app.add_handler(CommandHandler("topusers", topusers_cmd))
    app.add_handler(CommandHandler("dashboard", dashboard_cmd))

    # --- Register User Commands ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("myorders", myorders_cmd))
    app.add_handler(CommandHandler("orderstatus", orderstatus_cmd))
    app.add_handler(CommandHandler("categories", categories_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("deposit_ltc", deposit_ltc))

    # --- Register Menu and Product Navigation ---
    app.add_handler(CallbackQueryHandler(product_details_callback, pattern="^details_"))
    app.add_handler(CallbackQueryHandler(back_to_categories_callback, pattern="^back_to_categories$"))
    app.add_handler(CallbackQueryHandler(back_to_menu_callback, pattern="^back_to_menu$"))

    # --- Register All Orders Filter Handlers ---
    app.add_handler(CallbackQueryHandler(filter_orders_callback, pattern="^filter_"))
    # --- Combined handler for both filter input and menu ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_or_menu))

    print("Bot running... Press CTRL+C to stop.")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())