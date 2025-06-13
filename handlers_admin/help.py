from telegram import Update
from telegram.ext import ContextTypes

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """
📚 *Admin Command Reference*

*Product Management:*
/addproduct <name> <price> <stock> <category> - Add a new product
/removeproduct <product_id> - Remove product
/editproduct <id> <field> <value> - Edit product
/productlist - List all products
/bulkaddproducts - Import products from CSV (attach file)
/categories - Manage product categories

*Order Management:*
/allorders - List all orders
/setorderstatus <order_id> <status> - Update order status
/findorder <order_id> - Find order by ID
/exportorders - Export orders as CSV
/orderstats - Show order statistics

*User Management:*
/searchuser <search_term> - Search users
/setcoins <user_id> <amount> - Set user balance
/addcoins <user_id> <amount> - Add coins to user
/userstats - Show user statistics

*Analytics:*
/profits - Show recent profits
/exportprofits - Export profits as CSV
/dashboard - Show shop dashboard
/topusers - List users with highest balance

*Delivery Management:*
/deliveries - List all deliveries
/removedelivery <id> - Remove a delivery
"""
    await update.message.reply_text(msg, parse_mode="Markdown")