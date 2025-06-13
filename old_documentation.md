=========================================================
                 DOCUMENTATION
=========================================================

---------------------------------------------------------
USER FEATURES
---------------------------------------------------------
- View Products:
    Browse products by category (Cox, Klein, Shrooms). See price, stock, and order or view details (with images).
    Use "Back to Categories" and "Back to Menu" buttons for easy navigation.

- Order Products:
    Place an order by selecting a product and quantity. The bot checks stock and user balance before confirming.
    If the product has a pickup location, the order is instantly completed and the user receives the location info.

- My Orders:
    View your order history, including product name, quantity, order status, order date/time, and order ID.
    Filter orders by status. Use "Back to Filters" and "Back to Menu" for navigation.

- My Balance:
    Check your current coin balance.

- Profile:
    View your profile info, join date, order count, and balance.

- Deposit LTC:
    Get a Litecoin deposit address (placeholder). Balance can be updated by admin or via simulate deposit.

- Help:
    Get usage instructions.

- Categories:
    /categories – List product categories and browse by category.

- Search:
    /search <keyword> – Search for products by name or description.

---------------------------------------------------------
ADMIN FEATURES
---------------------------------------------------------
- Add Product:
    /addproduct Name | Price | ImageURL_or_FileID | Stock | [Description] | [Category]
    Example: /addproduct Magic Potion | 50 | https://example.com/image.jpg | 10 | Restores health | Cox

- Remove Product:
    /removeproduct <product_id>
    Example: /removeproduct 123e4567-e89b-12d3-a456-426614174000

- Edit Product:
    /editproduct <product_id> <field> <new_value>
    Fields: name, price, image, stock, description, category

- Product List:
    /productlist – List all products with their IDs.

- Export Orders:
    /exportorders – Export all orders as a CSV file.

- All Orders:
    /allorders – View all orders for all users, grouped by status, with order IDs.

- Set Order Status:
    /setorderstatus <order_id> <status>
    Example: /setorderstatus 8e1b2c3d-4f5a-678b-9c0d-1e2f3a4b5c6d completed
    Notifies the user of the status change. If set to "completed", the user receives the pickup location photo and caption (if set for the product). If set to "cancelled", the user is notified and stock is restored.

- Add Stock Location:
    /addstocklocation
    Admins can set a pickup location photo and caption for a product. The flow:
      1. Admin sends /addstocklocation
      2. Bot asks for product name
      3. Admin sends product name as text
      4. Bot asks for a photo with a caption (the pickup location info)
      5. Admin sends the photo and caption
      6. Bot saves this info to the product
    When an order for this product is marked as "completed", the user receives this photo and caption.

- Deliveries Log:
    /deliveries – View completed deliveries, including Stock ID (order ID).
    /exportdeliveries – Export all deliveries as a CSV file.
    /removedelivery <stock_id> – Remove a delivery log by Stock ID.

- Balance Management:
    /balance – Check your own balance.
    /addcoins <user_id> <amount> – Add coins to a user.
    /setcoins <user_id> <amount> – Set a user’s balance.
    /topusers – Show top users by coin balance.

- Dashboard:
    /dashboard – View sales stats, top products, and low-stock alerts.

- Profits:
    /profits – View recent profits.
    /exportprofits – Export profits as CSV.

---------------------------------------------------------
DATA STORAGE
---------------------------------------------------------
- products.json:
    List of products with fields: id, name, price, image, stock, description, category,
    location_image (Telegram file_id for pickup location), location_caption (pickup info).

- orders.json:
    User orders, keyed by user ID. Each order includes order_id, name, quantity, order_status, and created_at (date/time).

- balances.json:
    User coin balances, keyed by user ID.

- first_join.json:
    User join dates.

- deposit_addresses.json:
    User Litecoin deposit addresses (placeholder).

- deliveries.json:
    List of completed deliveries with user_id, product_name, stock_id (order_id), delivered_at, and location_caption.

- profits.json:
    List of profit entries with user_id, product, quantity, amount, stock_id, datetime.

---------------------------------------------------------
CODE STRUCTURE
---------------------------------------------------------
- shopbot.py:
    Main entry point. Imports and registers all handlers, starts the bot.

- handlers_user/
    - menu.py: User menu, profile, and navigation handlers.
    - orders.py: User order flow, order history, and filtering.
    - products.py: Product browsing, categories, details, and search.
    - balance.py: Balance, deposit, and related actions.
    - __init__.py: Exports all user handlers.

- handlers_admin/
    - orders.py: Admin order management, deliveries, and exports.
    - products.py: Admin product management and stock location.
    - analytics.py: Profits, dashboard, top users, and balance management.
    - __init__.py: Exports all admin handlers.

- models.py:
    Data access functions: load_json(filename, default), save_json(filename, data).

- config.py:
    Configuration constants: ADMIN_IDS, TOKEN, DEFAULT_START_COINS, main_menu.

---------------------------------------------------------
USER EXPERIENCE & NAVIGATION
---------------------------------------------------------
- Users can always return to the main menu or categories using "Back to Menu" and "Back to Categories" buttons.
- If a user presses these buttons during an order, the order flow is cancelled and further input is not treated as part of the order.
- Navigation is consistent and available in all product and order views.
- Modular code structure for easy maintenance and future features.

---------------------------------------------------------
TECHNICAL NOTES
---------------------------------------------------------
- All data is persistent and stored in JSON files.
- Only users in ADMIN_IDS can use admin commands.
- Error handling is provided for invalid input and unavailable actions.
- The bot uses async handlers and the latest python-telegram-bot API.
- Modular code structure for easy maintenance and future features.

=========================================================