# 🚀 Bot Command Reference

---

## ✅ Fixed & Working Commands (2025-06-22)

- **/removeproduct** — Remove a product by its ID (UUID).
- **/editproduct** — Edit a product by its ID (UUID).
- **/addproductphoto** — Add a presentation photo for a product by ID.
- **/addlocationphoto** — Bulk upload location photos for a product by ID (supports /done to finish).
- **/showlocationphotos** — Show all available (not yet delivered) location photos for a product by ID.
- **/setorderstatus** — Admin can set order status to completed/canceled; delivers photos or refunds as needed.
- **/addcoins** — Add coins to a user's balance.
- **/setcoins** — Set a user's balance.
- **/exportorders** — Export all orders as CSV.
- **/topusers** — Show top users by coin balance.
- **/dashboard** — Show sales stats, top products, and low-stock alerts.
- **/profits** — Show recent profits.
- **/exportprofits** — Export profits as CSV.
- **/allorders** — Interactive admin interface to filter orders by User, Order ID, Product, or Date, with grouped and copy-friendly output.
- **Product Stock Alerts** — Admins are notified when product stock drops below a threshold.
- **Order Status Notifications** — Users are notified automatically when their order status changes.
- **Order Filtering & Search** — Admins can filter orders by user, product, date, or status; users can search their own order history.
- **Main Menu Buttons** — All main menu buttons and flows work seamlessly with the new order filtering logic.

All of the above have been tested and are working as intended.




## ✅ Fixed & Working Commands (2025-06-18)

- **/removeproduct** — Remove a product by its ID (UUID).  
- **/editproduct** — Edit a product by its ID (UUID).  
- **/addproductphoto** — Add a presentation photo for a product by ID.  
- **/addlocationphoto** — Bulk upload location photos for a product by ID (supports /done to finish).  
- **/showlocationphotos** — Show all available (not yet delivered) location photos for a product by ID.  
- **/setorderstatus** — Admin can set order status to completed/canceled; delivers photos or refunds as needed.  
- **/addcoins** — Add coins to a user's balance.  
- **/setcoins** — Set a user's balance.  
- **/exportorders** — Export all orders as CSV.  
- **/topusers** — Show top users by coin balance.  
- **/dashboard** — Show sales stats, top products, and low-stock alerts.  
- **/profits** — Show recent profits.  
- **/exportprofits** — Export profits as CSV.  
- **/allorders** — Interactive admin interface to filter orders by User, Order ID, Product, or Date, with grouped and copy-friendly output.  
- **Product Stock Alerts** — Admins are notified when product stock drops below a threshold.  
- **Order Status Notifications** — Users are notified automatically when their order status changes.  
- **Order Filtering & Search** — Admins can filter orders by user, product, date, or status; users can search their own order history.  
- **Main Menu Buttons** — All main menu buttons and flows work seamlessly with the new order filtering logic.

All of the above have been tested and are working as intended.

---

## 🧪 Still To Test / Review

- **/addproductphoto_bulk** — Bulk upload presentation photos for a product.
- **/deliveries** — Show completed deliveries.
- **/exportdeliveries** — Export all deliveries as CSV.
- **/removedelivery** — Remove a delivery log by Stock ID.

---

## 👤 User Commands

| Command | Usage | Description |
|---------|-------|-------------|
| **/start** | `/start` | Start the bot and show the main menu. |
| **/categories** | `/categories` | List all product categories. |
| **/search** | `/search <keyword>` | Search for products by name or description.<br>_Example:_ `/search Spliff` |
| **/profile** | `/profile` | Show your profile: join date, order count, and balance. |
| **/balance** | `/balance` | Show your current coin balance. |
| **/deposit_ltc** | `/deposit_ltc` | Get a Litecoin deposit address (demo/testing). |
| **/myorders** | `/myorders` | Show your order history. Supports keyword filtering. |
| **/orderstatus** | `/orderstatus <order_id>` | Show the status of a specific order. |

---

## 🛠️ Admin Commands

| Command | Usage | Description |
|---------|-------|-------------|
| **/addproduct** | `/addproduct <name> <price> <stock> <category>` | Add a new product.<br>_Example:_ `/addproduct Spliff 25 50 Spliff` |
| **/removeproduct** | `/removeproduct <product_id>` | Remove a product by its ID. |
| **/editproduct** | `/editproduct <product_id> <field> <new_value>` | Edit a product field (`name`, `price`, `stock`, `description`, `category`, `image`).<br>_Example:_ `/editproduct <id> price 30` |
| **/productlist** | `/productlist` | List all products with their IDs, names, prices, stock, and categories. |
| **/addproductphoto** | `/addproductphoto <product_id>` | Set the main presentation photo for a product.<br>_Then send a photo._ |
| **/addproductphoto_bulk** | `/addproductphoto_bulk <product_id>` | Bulk upload presentation photos for a product.<br>_Send multiple photos, then `/done`._ |
| **/addlocationphoto** | `/addlocationphoto <product_id>` | Bulk upload location (delivery) photos for a product.<br>_Send multiple photos, then `/done`._ |
| **/done** | `/done` | Finish a bulk photo upload session. |
| **/showlocationphotos** | `/showlocationphotos <product_id>` | Show all available (not yet delivered) location photos for a product. |
| **/allorders** | `/allorders` | Interactive filter: view orders by User, Order ID, Product, or Date. Results are grouped and copy-friendly. |
| **/exportorders** | `/exportorders` | Export all orders as a CSV file. |
| **/setorderstatus** | `/setorderstatus <order_id> <status>` | Change the status of an order (`completed`, `cancelled`, etc.).<br>_Example:_ `/setorderstatus <id> completed` |
| **/deliveries** | `/deliveries` | Show completed deliveries. |
| **/exportdeliveries** | `/exportdeliveries` | Export all deliveries as a CSV file. |
| **/removedelivery** | `/removedelivery <stock_id>` | Remove a delivery log by Stock ID. |
| **/addcoins** | `/addcoins <user_id> <amount>` | Add coins to a user's balance.<br>_Example:_ `/addcoins 5501799605 100` |
| **/setcoins** | `/setcoins <user_id> <amount>` | Set a user's balance.<br>_Example:_ `/setcoins 5501799605 500` |
| **/topusers** | `/topusers` | Show the top users by coin balance. |
| **/dashboard** | `/dashboard` | Show sales stats, top products, and low-stock alerts. |
| **/profits** | `/profits` | Show recent profits. |
| **/exportprofits** | `/exportprofits` | Export profits as a CSV file. |

---

## 📝 Notes

- All commands are case-insensitive for product names.
- Only admins (IDs in `ADMIN_IDS`) can use admin commands.
- All data is persistent in SQLite.
- The bot uses async handlers and the latest python-telegram-bot API.
- Inline buttons are used for navigation and order flow.
- The `location_img_count` column in the `products` table is always kept in sync with the number of unused (not delivered) location photos for each product.
- Every time a location photo is added, delivered, or removed, the count is recalculated and updated in the database.
- The `/productlist` command and admin views always reflect the true number of available location photos.
- **Order filtering and main menu now work seamlessly together.**
- **Admins receive automatic low stock alerts.**
- **Users are notified of order status changes.**

---

> _For any questions or to add more features, contact your bot developer!_