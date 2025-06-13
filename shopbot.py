import sys
import asyncio

if sys.platform.startswith("win") and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# If running in Jupyter, VS Code interactive, or similar, allow nested event loops:
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
    profits_cmd, export_profits, add_location_start, add_location_receive_photo,
    add_location_set_product, ADD_LOCATION_WAIT_PHOTO,
    ADD_LOCATION_WAIT_PRODUCT, add_location_receive_product
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ConversationHandler
)
from handlers_admin.products import (
    add_location_start, add_location_set_product, add_location_receive_photo,
    ADD_LOCATION_WAIT_PRODUCT, ADD_LOCATION_WAIT_PHOTO
)


from telegram import Update
from telegram.ext import ContextTypes

from db import init_db


async def main():
    app = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_order, pattern="^order_")],
        states={
            ORDER_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_quantity)],
            ORDER_CONFIRM: [
                CallbackQueryHandler(confirm_order, pattern="^confirm_order$"),
                CallbackQueryHandler(cancel_confirm, pattern="^cancel_order$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_order),
                   CallbackQueryHandler(handle_back_buttons, pattern="^back_to_"),],
    )
    add_location_conv = ConversationHandler(
        entry_points=[CommandHandler("addstocklocation", add_location_start)],
        states={
            ADD_LOCATION_WAIT_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_location_set_product)],
            ADD_LOCATION_WAIT_PHOTO: [MessageHandler(filters.PHOTO, add_location_receive_photo)],
        },
        fallbacks=[],
    )

    app.add_handler(add_location_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.add_handler(CallbackQueryHandler(product_details, pattern="^details_"))
    app.add_handler(CommandHandler("profile", profile_cmd))
    # Admin
    app.add_handler(CommandHandler("addproduct", add_product))
    app.add_handler(CommandHandler("removeproduct", remove_product))
    app.add_handler(CommandHandler("editproduct", edit_product))
    app.add_handler(CommandHandler("productlist", product_list))
    app.add_handler(CommandHandler("exportorders", export_orders))
    app.add_handler(CommandHandler("allorders", all_orders))
    app.add_handler(CommandHandler("setorderstatus", set_order_status))
    app.add_handler(CommandHandler("deliveries", deliveries_cmd))
    app.add_handler(CommandHandler("removedelivery", removedelivery_cmd))
    app.add_handler(CommandHandler("exportdeliveries", export_deliveries))
    app.add_handler(CommandHandler("findorder", findorder_cmd))
    app.add_handler(CallbackQueryHandler(filter_orders_callback, pattern="^filter_orders_"))
    app.add_handler(CommandHandler("profits", profits_cmd))
    app.add_handler(CommandHandler("exportprofits", export_profits))
    
    # Balance
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("addcoins", addcoins_cmd))
    app.add_handler(CommandHandler("setcoins", setcoins_cmd))
    app.add_handler(CommandHandler("topusers", topusers_cmd))
    app.add_handler(CommandHandler("deposit_ltc", deposit_ltc))
    app.add_handler(CallbackQueryHandler(check_balance, pattern="^check_balance_"))
    app.add_handler(CallbackQueryHandler(simulate_deposit, pattern="^simulate_deposit$"))
    app.add_handler(CommandHandler("categories", categories_cmd))
    app.add_handler(CallbackQueryHandler(show_category, pattern="^cat_"))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("dashboard", dashboard_cmd))
    app.add_handler(CommandHandler("myorders", myorders_cmd))
    app.add_handler(CallbackQueryHandler(back_to_orders_filters, pattern="^back_to_orders_filters$"))
    app.add_handler(CallbackQueryHandler(handle_back_buttons, pattern="^back_to_"))

    print("Bot running... Press CTRL+C to stop.")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
