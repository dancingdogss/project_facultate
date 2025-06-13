# 🚀 Bot Command Reference

---

## 👤 User Commands

| Command | Usage | Description |
|---------|-------|-------------|
| **/start** | `/start` | Start the bot, show the main menu, and your balance. |
| **/categories** | `/categories` | List all product categories. |
| **/search** | `/search <keyword>` | Search for products by name or description.<br>_Example:_ `/search Spliff` |
| **/profile** | `/profile` | Show your profile: join date, order count, and balance. |
| **/balance** | `/balance` | Show your current coin balance. |
| **/deposit_ltc** | `/deposit_ltc` | Get a Litecoin deposit address (demo/testing). |
| **/myorders** | `/myorders` | Show your order history. |

**Inline Buttons:**
- 🛒 **Order**: Start the order process for a product.
- ℹ️ **Details**: Show detailed info for a product.
- 🔙 **Back to Menu**: Return to the main menu.
- 🔙 **Back to Categories**: Return to category selection.
- 🔙 **Back to Filters**: Return to order filter selection.

---

## 🛠️ Admin Commands

| Command | Usage | Description |
|---------|-------|-------------|
| **/addproduct** | `/addproduct` | Start a guided flow to add a new product. |
| **/removeproduct** | `/removeproduct` | Start a guided flow to remove a product by name. |
| **/removeproductid** | `/removeproductid <product_id>` | Remove a product by its ID. |
| **/removecategory** | `/removecategory <category>` | Remove all products in a category. |
| **/editproduct** | `/editproduct` | Start a guided flow to edit a product. |
| **/productlist** | `/productlist` | List all products with their IDs, names, prices, stock, and categories. |
| **/addproductphoto** | `/addproductphoto` | Start a guided flow to set the main presentation photo for a product. |
| **/addproductphoto_bulk** | `/addproductphoto_bulk` | Bulk upload presentation photos for a product. Send multiple photos, then `/done`. |
| **/addlocationphoto** | `/addlocationphoto` | Bulk upload location (delivery) photos for a product. Send multiple photos, then `/done`. |
| **/done** | `/done` | Finish a bulk photo upload session. |
| **/showlocationphotos** | `/showlocationphotos <product_name>` | Show all available (not yet delivered) location photos for a product. |
| **/allorders** | `/allorders [category]` | Show all orders for all users. Optionally filter by category.<br>_Example:_ `/allorders Cox` |
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
| **/users** | `/users` | List all users in the database. |

---

## 📦 Product Example: Spliff

- **Add Spliff product:**  
  Start `/addproduct` and follow the prompts.
- **Add a presentation photo:**  
  `/addproductphoto` and follow the prompts.
- **Bulk add presentation photos:**  
  `/addproductphoto_bulk` (send multiple photos, then `/done`)
- **Bulk add location photos:**  
  `/addlocationphoto` (send multiple photos, then `/done`)
- **Show available location photos:**  
  `/showlocationphotos Spliff`

---

## 🖼️ Photo & Delivery Management

- **Location Photos:**  
  Bulk upload with `/addlocationphoto`. Each order receives a unique, unused location photo if available. If a user orders more units than available photos, they receive as many as possible and the order remains pending for the rest until more photos are added.

- **Presentation Photos:**  
  Bulk upload with `/addproductphoto_bulk`. The last photo sent is used as the main image.

- **Delivered Photos Archive:**  
  Every delivered location photo is logged in the `deliveredphoto` table and can also be saved to the `delivered_photos` folder with the pattern:  
  ```
  <product_name>_<order_id>_<user_id>_<date-time>.jpg
  ```

- **Show Available Location Photos:**  
  `/showlocationphotos <product_name>` (admin only): Shows all available (not yet delivered) location photos for the product.

---

## 🗄️ Database Structure (Key Tables)

- **products:** `id`, `name`, `price`, `stock`, `description`, `category`, `image`
- **locationphoto:** `id`, `product_id`, `file_id`, `caption`, `is_delivered`, `order_id`
- **deliveredphoto:** `id`, `file_id`, `product_id`, `order_id`, `user_id`, `product_name`, `caption`, `delivered_at`
- **orders:** `id`, `user_id`, `product_id`, `product_name`, `quantity`, `status`, `created_at`
- **users:** `id`, `join_date`, `balance`

---

## 📝 Notes

- All commands are case-insensitive for product names.
- Only admins (IDs in `ADMIN_IDS`) can use admin commands.
- All data is persistent in SQLite.
- The bot uses async handlers and the latest python-telegram-bot API.
- Inline buttons are used for navigation and order flow.
- When a new user joins, the admin is notified automatically.
- Orders can be filtered by category using `/allorders <category>`.
- Orders with more units than available location photos are partially fulfilled and remain pending for the rest.

---

> _For any questions or to add more features, contact your bot developer!_